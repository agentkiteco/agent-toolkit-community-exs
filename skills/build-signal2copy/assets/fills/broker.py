"""Fixture v4: explicit pending executions; extends the preserved v3 wire model."""
import argparse
import copy
from datetime import datetime
from decimal import Decimal
import importlib.util
import os
from pathlib import Path
import threading
from http.server import ThreadingHTTPServer

PARENT = Path(__file__).resolve().parents[1] / 'pending/broker.py'
spec = importlib.util.spec_from_file_location('pending_broker_v3', PARENT)
v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)


class Broker(v3.Broker):
    def __init__(self, log):
        super().__init__(log)
        self.deal_history = {account: [] for account in self.accounts}
        self.origins = {}
        self.hidden_links = []

    def fill(self, body):
        account, oid, pid = body['account'], str(body['id']), str(body['position_id'])
        state = self.accounts[account]
        old = state['orders'][oid]
        amount = Decimal(str(body['volume']))
        remaining = Decimal(old['volume']) - amount
        if old['order_type'] not in {'limit', 'stop'} or old['state'] != 'placed':
            raise ValueError('Active entry required')
        if not amount.is_finite() or amount <= 0 or remaining < 0 or amount % Decimal('.01'):
            raise ValueError('Invalid execution volume')
        if not pid.isdigit() or (old.get('position_id') and old['position_id'] != pid):
            raise ValueError('Invalid position linkage')
        origin = (account, pid)
        if origin in self.origins and self.origins[origin] != oid or pid in state['positions'] and origin not in self.origins:
            raise ValueError('Cannot merge unrelated positions')
        previous = state['positions'].get(pid)
        position = previous or self.position({'side': old['direction'], 'volume': str(amount)}, pid)
        position = {**position, 'volume': str(Decimal(previous['volume']) + amount) if previous else str(amount)}
        linked = body.get('publish_link', True)
        order = {**old, 'volume': str(remaining), 'state': 'placed' if remaining else 'filled',
                 'position_id': pid if linked else None, 'update_time': v3.now()}
        deal = {'deal_id': self.identifier(), 'order_id': oid, 'position_id': pid, 'type': 'open',
                'direction': old['direction'], 'instrument': old['instrument'], 'volume': str(amount),
                'price': old['price'], 'create_time': v3.now(), 'profit': {'amount': '0', 'currency': 'USD'}}
        self.origins[origin] = oid
        state['positions'][pid] = position
        self.next_id = max(self.next_id, int(pid))
        if remaining: state['orders'][oid] = order
        else: del state['orders'][oid]
        self.remember_order(account, order)
        event = self.emit(account, position, orders=[order])
        if linked:
            self.deal_history[account].append({'event_time': deal['create_time'], 'deal': copy.deepcopy(deal)})
            event['payload']['deals'] = [copy.deepcopy(deal)]
        else:
            self.hidden_links.append((account, oid, pid, copy.deepcopy(deal)))
        return copy.deepcopy(order)

    def reduce(self, account, position_id, amount):
        # v3 had no filled entries: only protective orders followed position size.
        # A linked residual entry has independent unexecuted volume.
        orders = self.accounts[account]['orders']
        residuals = {oid: order for oid, order in orders.items()
                     if order['order_type'] in {'limit', 'stop'} and order.get('position_id') == position_id}
        for oid in residuals: del orders[oid]
        try:
            return super().reduce(account, position_id, amount)
        finally:
            orders.update(residuals)

    def control(self, action, body):
        with self.lock:
            if action == 'state':
                return {**super().control(action, body), 'deal_history': copy.deepcopy(self.deal_history),
                        'hidden_links': copy.deepcopy(self.hidden_links)}
            if action == 'reserve':
                account, oid, pid = body['account'], str(body['id']), str(body['position_id'])
                old = self.accounts[account]['orders'][oid]
                if not pid.isdigit() or pid in self.accounts[account]['positions'] or old.get('position_id'):
                    raise ValueError('New reserved position ID required')
                order = {**old, 'position_id': pid, 'update_time': v3.now()}
                self.accounts[account]['orders'][oid] = order
                self.remember_order(account, order); self.emit(account, orders=[order])
                return order
            if action == 'fill':
                return self.fill(body)
            if action == 'fill-batch':
                # Roll back invalid operator batches; application sees both accounts after commit.
                names = ('accounts', 'order_history', 'deal_history', 'origins', 'hidden_links', 'next_id')
                before = {name: copy.deepcopy(getattr(self, name)) for name in names}
                try:
                    return {'orders': [self.fill(item) for item in body['fills']]}
                except (ValueError, KeyError, ArithmeticError, TypeError):
                    for name, value in before.items(): setattr(self, name, value)
                    raise
            if action == 'release-links':
                count = len(self.hidden_links)
                for account, oid, pid, deal in self.hidden_links:
                    latest = next(item['order'] for item in reversed(self.order_history[account]) if item['order']['order_id'] == oid)
                    order = {**latest, 'position_id': pid, 'update_time': v3.now()}
                    if oid in self.accounts[account]['orders']: self.accounts[account]['orders'][oid] = order
                    self.remember_order(account, order)
                    self.deal_history[account].append({'event_time': deal['create_time'], 'deal': deal})
                    event = self.emit(account, orders=[order]); event['payload']['deals'] = [copy.deepcopy(deal)]
                self.hidden_links.clear()
                return {'released': count}
            return super().control(action, body)

    def _public(self, method, path, query, headers, body):
        if path == '/healthz' and method == 'GET':
            return 200, {'service': 'orbit-behavior-broker', 'protocol': 4,
                         'capabilities': ['market', 'partial_close', 'sltp', 'limit', 'stop', 'order_history', 'explicit_fills', 'deal_history']}
        if path.endswith('/history/deals') and method == 'GET':
            # Keep parent authentication/route checks before supplying actual executions.
            code, data = super()._public(method, path, query, headers, body)
            if code != 200: return code, data
            account = path.split('/')[4]
            items = copy.deepcopy(self.deal_history[account])
            for name, lower in [('from_time', True), ('to_time', False)]:
                if name in query:
                    bound = datetime.fromisoformat(query[name][0])
                    items = [item for item in items if (datetime.fromisoformat(item['event_time']) >= bound if lower else datetime.fromisoformat(item['event_time']) <= bound)]
            if 'deal_type' in query: items = [item for item in items if item['deal']['type'] == query['deal_type'][0]]
            # ponytail: bounded experiment; reject overflow rather than claim complete truncated history.
            if len(items) > int(query.get('limit', ['200'])[0]): raise ValueError('Synthetic history page bound exceeded')
            return 200, {'items': items, 'has_more': False, 'next_cursor': None}
        return super()._public(method, path, query, headers, body)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--control-port', type=int, required=True)
    parser.add_argument('--log', type=Path, required=True)
    args = parser.parse_args()
    broker = Broker(args.log)
    controls = ThreadingHTTPServer(('127.0.0.1', args.control_port), v3.handler(broker, control=True, token=os.environ['ACCEPTANCE_CONTROL_TOKEN']))
    threading.Thread(target=controls.serve_forever, daemon=True).start()
    ThreadingHTTPServer(('127.0.0.1', args.port), v3.handler(broker)).serve_forever()
