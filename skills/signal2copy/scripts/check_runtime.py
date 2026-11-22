"""One socket-free integration observation of the installed native runtime."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from decimal import Decimal


def check():
    spec = importlib.util.spec_from_file_location('runtime_installer', Path(__file__).with_name('install_runtime.py'))
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    checks = []

    def passed(label):
        checks.append(label)

    def denied(action, kind=Exception):
        try:
            action()
        except kind:
            return
        raise AssertionError('Expected refusal')

    # ponytail: isolated process check; no real sockets are permitted here.
    with tempfile.TemporaryDirectory(prefix='signal2copy-runtime-') as directory, patch('socket.socket', side_effect=AssertionError('Network forbidden')):
        app_dir = Path(directory)
        installer.install(app_dir)
        package = app_dir / 'signal2copy_runtime'
        manifest = json.loads((package / 'RUNTIME_MANIFEST.json').read_text())
        for name, value in manifest['files'].items():
            assert hashlib.sha256((package / name).read_bytes()).hexdigest() == value
        denied(lambda: installer.install(app_dir), FileExistsError)
        sys.path.insert(0, directory)
        import signal2copy_runtime as core
        from signal2copy_runtime.exness_adapter import AdapterError
        assert Path(core.__file__).parent == package
        assert all(Path(module.__file__).is_relative_to(package) for name, module in sys.modules.items()
                   if name.startswith('signal2copy_runtime.') and getattr(module, '__file__', None))
        passed('Fresh package imports and manifest match; repeat installation refuses overwrite')

        broker = core.NativeBroker('https://gateway.example.invalid', 'https://partner.example.invalid',
                                   send=lambda *args: (_ for _ in ()).throw(AssertionError('Transport forbidden')))

        class Host:
            def __init__(self):
                self.mode = 'native-read-only'
                self.store = SimpleNamespace(failed=False)
                self.broker = broker
                self.state = {'mode': self.mode, 'frozen': False, 'accounts': {}, 'strategies': {},
                              'subscriptions': {}, 'commands': {}}
                self.saved = []
                self.conversion = core.Conversion(SimpleNamespace(read=self.conversion_read))

            def save(self, event):
                self.saved.append(copy.deepcopy(self.state))

            def account(self, account):
                return self.state['accounts'][account]

            def admission(self, investor, source):
                raise AssertionError('Read-only check must not reach admission')

            def settings(self, body, equity):
                raise AssertionError('Read-only check must not reach settings')

            def signal_ids(self, snapshot):
                return ['p:' + p['position_id'] for p in snapshot['positions']]

            def unresolved(self, sub):
                return [c for c in self.state['commands'].values() if c['subscription'] == sub['id']
                        and c['status'] in ('prepared', 'intent', 'accepted', 'unknown')]

            def fx(self, account, source, target, purchase=False):
                return self.conversion.convert(account, source, target, purchase)

            def controls(self, sub, signal, snapshot, lots, quote, exclude_command=None):
                raise AssertionError('This check does not authorize execution')

            def conversion_read(self, account, resource):
                from datetime import datetime, timezone
                if resource == 'instruments':
                    return {'instruments': ['EURUSD']}
                if resource == 'instruments/EURUSD':
                    return {'instrument': 'EURUSD', 'base_currency': 'EUR', 'quote_currency': 'USD'}
                if resource == 'quotes/EURUSD':
                    at = datetime.now(timezone.utc).isoformat()
                    return {'bid': '1.1000', 'ask': '1.1001', 'event_time': at, 'received_at': at}
                raise AssertionError('Unexpected conversion read')

        host = Host()
        before = copy.deepcopy(host.state)
        host.controls = None
        denied(lambda: core.NativeEngine(host), AdapterError)
        assert host.state == before and not host.saved
        del host.controls
        core.validate_host(host)
        passed('Missing required host hook refuses construction before mutation')

        sub = {'id': 'subscription', 'native': True, 'status': 'active', 'initial_eligible': ['p:41'],
               'account': '2222', 'strategy': 'strategy', 'mappings': {}}
        host.state['subscriptions'][sub['id']] = sub
        body = {'instrument': 'EURUSD', 'side': 'buy', 'volume': '0.02'}
        command = {'id': 'retained-request', 'subscription': sub['id'], 'mapping': 'p:41', 'account': '2222',
                   'kind': 'open', 'status': 'unknown', 'fingerprint': 'immutable', 'body': body}
        host.state['commands'][command['id']] = command
        host.state['accounts']['2222'] = {'id': '2222', 'observation': {'details': {'settings': {'currency': 'USD', 'leverage': '100'}}}}
        sub['mappings']['p:41'] = {'id': 'p:41', 'status': 'unknown', 'type': 'position',
                                 'source': {'position_id': '41', 'instrument': 'EURUSD', 'direction': 'buy'}}
        engine = core.NativeEngine(host)
        assert sub['status'] == 'paused' and sub['initial_eligible'] == []
        assert host.saved[-1]['commands'][command['id']]['status'] == 'unknown'
        denied(lambda: engine.start({'role': 'investor'}, {}), AdapterError)
        denied(lambda: engine.journal.reserve('2222', command['id'], 'immutable'), AdapterError)
        engine.reconcile(sub, {}, {'events': []})
        assert command['status'] == 'unknown' and 'target' not in sub['mappings']['p:41']
        passed('Restart pauses entries; read-only Start and unknown resend are denied')

        event = {'client_request_id': 'other-request', 'operation_id': '91', 'status': 'success',
                 'payload': {'positions': [{'position_id': '51', 'instrument': 'EURUSD', 'direction': 'buy',
                                            'volume': '0.02', 'state': 'open'}]}}
        engine.reconcile(sub, {}, {'events': [event]})
        assert command['status'] == 'unknown'
        event['client_request_id'] = command['id']
        engine.reconcile(sub, {}, {'events': [event]})
        assert command['status'] == 'confirmed' and command['ownership_confirmed'] is True
        assert sub['mappings']['p:41']['target'] == '51'
        assert sub['status'] == 'paused'
        passed('Unrelated result cannot adopt ownership; exact late result binds without Resume')

        old = core.ManagedStreams(None, '2222', ['EURUSD'], 1)
        replacement = core.ManagedStreams(None, '2222', ['EURUSD'], 1)
        assert old.generations['_runtime'] != replacement.generations['_runtime']
        old_stream, new_stream = object(), object()
        old.streams['transactions'] = new_stream
        denied(lambda: old.accept('transactions', 1, {}, old_stream), AdapterError)
        assert old.version == 0
        passed('Replacement has a distinct incarnation and stale callback cannot change state')

        source = {'id': '1111', 'observation': {'details': {'settings': {'currency': 'USD'}}}}
        target = host.account('2222')
        host.state['subscriptions'] = {}
        calc = {'id': 'calculation', 'account': '2222', 'mode': 'proportional', 'amount': '2500',
                'multiplier': '1', 'mappings': {}}
        frame = {'snapshot': {'account_state': {'equity': '10000', 'used_margin': '0'}},
                 'hmr': {'periods': []}, 'ticks': {'EURUSD': {'bid': '1.1000', 'ask': '1.1001'}}}
        conditions = {'margin_currency': 'EUR', 'calc_mode': 'forex', 'contract_size': '100000',
                      'instrument': 'EURUSD', 'volume_step': '0.01', 'volume_min': '0.01', 'volume_max': '10'}
        signal = {'instrument': 'EURUSD', 'volume': '0.08', 'direction': 'buy'}
        lots, evidence = engine.size(calc, signal, source, target, frame, frame, conditions)
        assert lots == Decimal('0.02') and evidence['margin_fx_route'][0]['direction'] == 'purchase'
        calc['mode'] = 'one_to_one'
        assert engine.size(calc, signal, source, target, frame, frame, conditions)[0] == Decimal('0.08')
        signal['volume'] = '0.005'
        denied(lambda: engine.size(calc, signal, source, target, frame, frame, conditions), AdapterError)
        rate, route = host.fx(target, 'USD', 'EUR')
        assert rate == 1 / Decimal('1.1001') and route[0]['instrument'] == 'EURUSD'
        passed('Both sizing modes, minimum refusal and account-scoped bid/ask FX use installed core')
    return {'result': 'passed', 'checks': checks, 'network_access': False, 'real_keys': False,
            'scope': 'One installed-core integration observation; not an app, broker or cloud acceptance'}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
