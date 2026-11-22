"""Pending fixture v3: market/protection plus limit/stop lifecycle; stdlib only."""
import argparse
import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import threading
from urllib.parse import urlsplit, parse_qs


def now():
    return datetime.now(timezone.utc).isoformat()


class Broker:
    def __init__(self, log):
        self.lock = threading.RLock()
        self.log = log
        self.accounts = {key: {"positions": {}, "orders": {}, "events": [], "operations": {}, "keys": {}}
                         for key in ("1111", "2222")}
        self.requests = []
        self.next_id = 1000
        self.fault = None
        self.held = []
        self.changes = []
        self.order_history = {key: [] for key in self.accounts}
        self.history_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

    def identifier(self):
        self.next_id += 1
        return str(self.next_id)

    def emit(self, account, position=None, *, operation=None, key=None, closed=False, orders=None):
        event = {"id": self.identifier(), "event_type": "transaction_event", "event_time": now(),
                 "status": "success", "payload": {"positions": [copy.deepcopy(position)] if position else [], "orders": copy.deepcopy(orders or []), "deals": []}}
        if operation:
            event.update(operation_id=operation, client_request_id=key)
        if closed:
            event["payload"]["positions"][0] = {**position, "state": "closed", "volume": "0"}
        self.accounts[account]["events"].append(event)
        return event

    def position(self, body, identifier=None):
        volume = Decimal(str(body["volume"]))
        if not volume.is_finite() or volume <= 0 or volume > 10 or volume % Decimal('.01'):
            raise ValueError("Invalid synthetic broker volume")
        if body.get("side", "buy") not in {"buy", "sell"} or body.get("instrument", "EURUSD") != "EURUSD":
            raise ValueError("Unsupported synthetic instrument or side")
        return {"position_id": identifier or self.identifier(), "direction": body.get("side", "buy"),
                "instrument": "EURUSD", "state": "open", "create_time": now(),
                "volume": str(volume), "open_price": "1.1000"}

    def write_log(self, row):
        self.requests.append(row)
        with self.log.open("a") as output:
            output.write(json.dumps(row) + "\n")

    def protection(self, account, position_id, body):
        if set(body) - {"stop_loss_price", "take_profit_price", "comment", "position_id", "type"}:
            raise ValueError("Unsupported protective field")
        state = self.accounts[account]
        if position_id not in state["positions"]:
            raise ValueError("Protective position not found")
        old = next((o for o in state["orders"].values() if o["position_id"] == position_id), None)
        values = {name: old.get(name) if old else None for name in ("stop_loss_price", "take_profit_price")}
        for name in values:
            if name in body:
                value = body[name]
                if value is not None and (not Decimal(str(value)).is_finite() or Decimal(str(value)) <= 0):
                    raise ValueError("Protective price must be positive or null")
                values[name] = str(Decimal(str(value))) if value is not None else None
        if old is None and not any(v is not None for v in values.values()):
            raise ValueError("At least one protective price is required")
        position = state["positions"][position_id]
        order = {**(old or {"order_id": self.identifier(), "create_time": now()}),
                 "position_id": position_id, "order_type": "sltp", "instrument": position["instrument"],
                 "direction": position["direction"], "volume": position["volume"],
                 "state": "placed", "update_time": now(), **values}
        if all(v is None for v in values.values()):
            state["orders"].pop(order["order_id"], None)
            order["state"] = "cancelled"
        else:
            state["orders"][order["order_id"]] = order
        return order

    def pending_order(self, body, old=None, identifier=None):
        allowed = {"type", "instrument", "side", "volume", "price", "stop_loss_price", "take_profit_price", "comment"}
        if set(body) - allowed: raise ValueError("Unsupported pending field")
        if old is None:
            if body.get("type") not in {"limit", "stop"}: raise ValueError("Pending type required")
            position = self.position(body)
            order = {"order_id": identifier or self.identifier(), "order_type": body["type"], "state": "placed",
                "position_id": None,
                "instrument": position["instrument"], "direction": position["direction"], "volume": position["volume"],
                "create_time": now(), "stop_loss_price": None, "take_profit_price": None}
        else:
            if not body or set(body) - {"price", "stop_loss_price", "take_profit_price", "comment"}:
                raise ValueError("Only price/protection may change")
            order = copy.deepcopy(old)
        for field in ("price", "stop_loss_price", "take_profit_price"):
            if field not in body: continue
            value = body[field]
            if value is None and field != "price": order[field] = None; continue
            price = Decimal(str(value))
            if not price.is_finite() or price <= 0: raise ValueError("Price must be positive")
            order[field] = str(price)
        if "price" not in order: raise ValueError("Pending price required")
        order["update_time"] = now()
        return order

    def remember_order(self, account, order):
        self.order_history[account].append({"event_time": now(), "order": copy.deepcopy(order)})

    def reduce(self, account, position_id, amount):
        state = self.accounts[account]
        old = state["positions"][position_id]
        amount = Decimal(str(amount)) if amount is not None else Decimal(old["volume"])
        before = Decimal(old["volume"])
        if not amount.is_finite() or amount <= 0 or amount > before or amount % Decimal('.01'):
            raise ValueError("Invalid close volume")
        remaining = before - amount
        if remaining and remaining < Decimal('.01'):
            raise ValueError("Remaining volume below broker minimum")
        position = {**old, "volume": str(remaining), "state": "open" if remaining else "closed"}
        if remaining:
            state["positions"][position_id] = position
        else:
            del state["positions"][position_id]
        orders = []
        for oid, order in list(state["orders"].items()):
            if order["position_id"] != position_id:
                continue
            order = {**order, "volume": str(remaining), "update_time": now(), "state": "placed" if remaining else "cancelled"}
            orders.append(order)
            if remaining: state["orders"][oid] = order
            else: del state["orders"][oid]
        return position, orders

    def control(self, action, body):
        with self.lock:
            if action == "state":
                return {"accounts": copy.deepcopy(self.accounts), "requests": copy.deepcopy(self.requests),
                        "held_operations": copy.deepcopy(self.held), "changes": copy.deepcopy(self.changes),
                        "order_history": copy.deepcopy(self.order_history)}
            if action in {"order", "order-change", "order-cancel"}:
                account = body["account"]
                if account not in self.accounts: raise ValueError("Unknown account")
                state = self.accounts[account]
                oid = str(body.get("id") or self.identifier())
                if not oid.isdigit(): raise ValueError("Numeric order ID required")
                fields = {k: v for k, v in body.items() if k not in {"account", "id"}}
                if action == "order":
                    if oid in state["orders"]: raise ValueError("New order ID required")
                    order = self.pending_order(fields, identifier=oid)
                    self.next_id = max(self.next_id, int(oid)); state["orders"][oid] = order
                else:
                    old = state["orders"].get(oid)
                    if not old or old["order_type"] not in {"limit", "stop"}: raise ValueError("Active pending required")
                    if action == "order-change":
                        order = self.pending_order(fields, old); state["orders"][oid] = order
                    else:
                        if fields: raise ValueError("Cancel has no extra fields")
                        order = {**old, "state": "cancelled", "update_time": now()}; del state["orders"][oid]
                self.remember_order(account, order); self.emit(account, orders=[order])
                self.changes.append({"at": now(), "action": action, "body": copy.deepcopy(body)})
                return order
            if action == "change":
                account, pid = body["account"], str(body["id"])
                if account not in self.accounts or pid not in self.accounts[account]["positions"]:
                    raise ValueError("Unknown source/manual position")
                if set(body) - {"account", "id", "remaining_volume", "stop_loss_price", "take_profit_price"}:
                    raise ValueError("Unsupported change field")
                if "remaining_volume" in body:
                    before = Decimal(self.accounts[account]["positions"][pid]["volume"])
                    remaining = Decimal(str(body["remaining_volume"]))
                    if not remaining.is_finite() or remaining < 0 or remaining >= before:
                        raise ValueError("Change only reduces existing exposure")
                    if any(k in body for k in ("stop_loss_price", "take_profit_price")):
                        raise ValueError("Apply volume and protection changes separately")
                    position, orders = self.reduce(account, pid, before - remaining)
                else:
                    if not any(k in body for k in ("stop_loss_price", "take_profit_price")):
                        raise ValueError("Provide a volume or protection change")
                    orders = [self.protection(account, pid, {k: v for k, v in body.items() if k not in {"account", "id"}})]
                    position = self.accounts[account]["positions"][pid]
                self.emit(account, position, orders=orders)
                self.changes.append({"at": now(), "body": copy.deepcopy(body)})
                return {"changed": True}
            if action == "position":
                account = body["account"]
                if account not in self.accounts:
                    raise ValueError("Unknown synthetic account")
                identifier = str(body.get("id") or self.identifier())
                if not identifier.isdigit() or identifier in self.accounts[account]["positions"]:
                    raise ValueError("Use a new numeric synthetic position ID")
                self.next_id = max(self.next_id, int(identifier))
                position = self.position(body, identifier)
                self.accounts[account]["positions"][identifier] = position
                self.emit(account, position)
                return position
            if action == "fault":
                if body.get("kind") != "apply_then_503_hold":
                    raise ValueError("Unknown synthetic fault")
                if self.fault:
                    raise ValueError("A fault is already armed")
                if body["account"] not in self.accounts or body.get("method", "POST") not in {"POST", "PATCH", "DELETE"}:
                    raise ValueError("Invalid fault target")
                self.fault = {"account": body["account"], "kind": body["kind"], "method": body.get("method", "POST")}
                return {"armed": True}
            if action == "release":
                for account, operation, event in self.held:
                    self.accounts[account]["operations"][operation]["status"] = "success"
                    self.accounts[account]["events"].append(event)
                count = len(self.held)
                self.held.clear()
                return {"released": count}
            raise ValueError("Unknown control action")

    def public(self, method, path, query, headers, body):
        # Include denied/unsupported writes in evidence, not only accepted orders.
        with self.lock:
            before = len(self.requests)
            try:
                result = self._public(method, path, query, headers, body)
            except (ValueError, InvalidOperation, KeyError, TypeError):
                if method in {"POST", "DELETE", "PATCH", "PUT"} and len(self.requests) == before:
                    self.rejected_attempt(method, path, query, headers, body, 400)
                raise
            if method in {"POST", "DELETE", "PATCH", "PUT"} and len(self.requests) == before:
                self.rejected_attempt(method, path, query, headers, body, result[0])
            return result

    def rejected_attempt(self, method, path, query, headers, body, status):
        match = re.search(r"/accounts/([^/]+)", path)
        self.write_log({"sequence": len(self.requests) + 1, "at": now(),
            "account": match.group(1) if match else None, "method": method, "path": path,
            "body": body, "query": query, "request_id": headers.get("EXN-IDEMPOTENCY-KEY") or headers.get("Idempotency-Key"),
            "duplicate": False, "rejected_http_status": status})

    def _public(self, method, path, query, headers, body):
        if path == "/healthz" and method == "GET":
            return 200, {"service": "orbit-behavior-broker", "protocol": 3, "capabilities": ["market", "partial_close", "sltp", "limit", "stop", "order_history"]}
        if path == "/v1/partner" and method == "GET":
            return (200, {"verified": True}) if headers.get("EXN-API-KEY") == "synthetic-provider" else (401, {"detail": "Synthetic partner access denied"})
        match = re.fullmatch(r"/v1/trading/accounts/(1111|2222)/(details|snapshot|instruments|quotes|events|history|limits|positions|orders|operations)(?:/([A-Za-z0-9]+))?", path)
        if not match:
            return 404, {"detail": "Unknown synthetic route"}
        account, resource, identifier = match.groups()
        if resource in {"details", "snapshot", "events", "limits"} and identifier is not None:
            return 404, {"detail": "Unknown synthetic route"}
        if resource == "history" and identifier not in {None, "orders", "deals"}:
            return 404, {"detail": "Unknown history route"}
        if resource == "quotes" and identifier != "EURUSD":
            return 404, {"detail": "Unknown synthetic instrument"}
        if headers.get("EXN-API-KEY") != "synthetic-" + account:
            return 401, {"detail": "Synthetic account access denied"}
        with self.lock:
            state = self.accounts[account]
            if method == "GET":
                if resource == "details":
                    return 200, {"account_id": account, "create_date": "2026-01-01T00:00:00+00:00", "settings": {
                        "currency": "USD", "leverage": "100", "trade_mode": "enabled", "account_status": "active", "execution_mode": "market"}}
                if resource == "snapshot":
                    return 200, {"positions": list(state["positions"].values()), "orders": list(state["orders"].values()),
                                 "account_state": {"balance": "10000", "equity": "10000", "used_margin": "0"}}
                if resource == "instruments":
                    if not identifier:
                        return 200, {"instruments": ["EURUSD"]}
                    if identifier != "EURUSD":
                        return 404, {"detail": "Unknown instrument"}
                    return 200, {"instrument": "EURUSD", "base_currency": "EUR", "quote_currency": "USD", "margin_currency": "EUR",
                                 "calc_mode": "forex", "contract_size": "100000", "margin_percent": "1", "point_digits": 5,
                                 "volume_min": ".01", "volume_step": ".01", "volume_max": "10", "trade_mode": "enabled"}
                if resource == "quotes":
                    return 200, {"instrument": "EURUSD", "bid": "1.1000", "ask": "1.1001", "event_time": now(), "received_at": now()}
                if resource == "limits":
                    return 200, {"rest": {"global_account_rate": {"limit": 1000, "window_seconds": 1},
                        "methods": [{"api_operation_id": "getDealsHistory", "limits": {"history_age_days": 3650, "history_range_days": 365}}]},
                                 "events": {"transport": "http_cursor", "retention": "process_lifetime"}}
                if resource == "events":
                    after = int(query.get("after", ["0"])[0])
                    return 200, {"cursor": len(state["events"]), "events": state["events"][after:]}
                if resource == "history":
                    if identifier == "orders":
                        latest = {item["order"]["order_id"]: item for item in self.order_history[account]}
                        return 200, {"items": list(latest.values()), "has_more": False, "next_cursor": None}
                    if identifier == "deals":
                        return 200, {"items": [], "has_more": False, "next_cursor": None}
                    return 200, {"complete": True, "issue": None, "pages": 1, "coverage": "synthetic_window",
                        "from": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(), "to": now(), "items": [{
                        "event_time": self.history_at, "deal": {
                            "deal_id": "10", "position_id": "20", "type": "close", "direction": "buy", "instrument": "EURUSD",
                            "volume": ".01", "price": "1.1", "create_time": self.history_at,
                            "profit": {"amount": "0", "currency": "USD"}}}]}
                if resource == "operations":
                    return (200, state["operations"][identifier]) if identifier in state["operations"] else (404, {"detail": "Unknown operation"})
            allowed = (resource == "positions" and (method == "POST" and identifier is None or method == "DELETE" and identifier is not None)
                       or resource == "orders" and (method == "POST" and identifier is None or method in {"PATCH", "DELETE"} and identifier is not None))
            if not allowed:
                return 405, {"detail": "Unsupported synthetic operation"}
            key = headers.get("EXN-IDEMPOTENCY-KEY") or headers.get("Idempotency-Key")
            if not key or not 5 <= len(key) <= 128:
                return 400, {"detail": "Provide a request identity"}
            signature = json.dumps([method, path, query, body], sort_keys=True)
            duplicate = key in state["keys"]
            row = {"sequence": len(self.requests) + 1, "at": now(), "account": account, "method": method,
                   "path": path, "body": body, "query": query, "request_id": key, "duplicate": duplicate}
            self.write_log(row)  # Record every attempt, including idempotent replays.
            if duplicate:
                old = state["keys"][key]
                return (202, old["ack"]) if old["signature"] == signature else (409, {"detail": "Request identity reused with different payload"})
            orders = []
            if resource == "orders":
                if query:
                    raise ValueError("Order routes have no query parameters")
                old = state["orders"].get(identifier) if identifier else None
                if method == "POST" and body.get("type") in {"limit", "stop"}:
                    order = self.pending_order(body); state["orders"][order["order_id"]] = order
                    orders, position = [order], None; self.remember_order(account, order)
                elif method in {"PATCH", "DELETE"} and old and old["order_type"] in {"limit", "stop"}:
                    if method == "PATCH":
                        order = self.pending_order(body, old); state["orders"][identifier] = order
                    else:
                        if body: raise ValueError("Cancel has no body")
                        order = {**old, "state": "cancelled", "update_time": now()}; del state["orders"][identifier]
                    orders, position = [order], None; self.remember_order(account, order)
                elif method == "DELETE":
                    return 405, {"detail": "Only pending entries can be cancelled"}
                elif method == "POST":
                    if body.get("type") != "sltp" or "position_id" not in body:
                        raise ValueError("Only protective orders are supported")
                    pid = str(body["position_id"])
                    if any(o["position_id"] == pid for o in state["orders"].values()):
                        return 409, {"detail": "Protective order already exists"}
                else:
                    if identifier not in state["orders"]:
                        return 404, {"detail": "Protective order not found"}
                    if not body or set(body) - {"stop_loss_price", "take_profit_price", "comment"}:
                        raise ValueError("Unsupported protective patch")
                    pid = state["orders"][identifier]["position_id"]
                if not orders:
                    orders = [self.protection(account, pid, body)]
                    position = state["positions"][pid]
            elif method == "POST":
                if query:
                    raise ValueError("Open route has no query parameters")
                position = self.position(body)
                protection = {k: v for k, v in body.items() if k in {"stop_loss_price", "take_profit_price"}}
                for value in protection.values():
                    if value is not None and (not Decimal(str(value)).is_finite() or Decimal(str(value)) <= 0):
                        raise ValueError("Invalid opening protection")
                state["positions"][position["position_id"]] = position
                if any(v is not None for v in protection.values()):
                    orders = [self.protection(account, position["position_id"], protection)]
            else:
                if identifier not in state["positions"]:
                    return 404, {"detail": "Position not found"}
                if body or set(query) - {"volume"} or any(len(v) != 1 for v in query.values()):
                    raise ValueError("Close accepts only one optional volume query")
                position, orders = self.reduce(account, identifier, query.get("volume", [None])[0])
            operation = self.identifier()
            ack = {"operation_id": operation, "client_request_id": key, "status": "accepted"}
            state["operations"][operation] = {**ack, "status": "success"}
            event = self.emit(account, position, operation=operation, key=key, orders=orders)
            state["keys"][key] = {"signature": signature, "ack": ack}
            if self.fault and self.fault["account"] == account and method == self.fault["method"]:
                self.fault = None
                state["events"].pop()
                state["operations"][operation]["status"] = "pending"
                self.held.append((account, operation, event))
                return 503, {"code": 5000, "error_message": "SYNTHETIC_REPLY_LOST"}
            return 202, ack


def handler(broker, *, control=False, token=""):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def handle_request(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 <= length <= 65536:
                    raise ValueError("Request too large")
                body = json.loads(self.rfile.read(length)) if length else {}
                if not isinstance(body, dict):
                    raise ValueError("JSON body must be an object")
                url = urlsplit(self.path)
                if control:
                    if self.headers.get("Authorization") != "Bearer " + token:
                        code, result = 403, {"detail": "Control access denied"}
                    else:
                        code, result = 200, broker.control(url.path.strip("/"), body)
                else:
                    code, result = broker.public(self.command, url.path, parse_qs(url.query), self.headers, body)
            except (ValueError, InvalidOperation, KeyError, TypeError) as exc:
                code, result = 400, {"detail": "Invalid synthetic request", "error_type": type(exc).__name__}
            data = json.dumps(result).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = do_POST = do_DELETE = do_PATCH = do_PUT = handle_request
    return Handler


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--control-port", type=int, required=True)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()
    token = os.environ["ACCEPTANCE_CONTROL_TOKEN"]
    broker = Broker(args.log)
    controls = ThreadingHTTPServer(("127.0.0.1", args.control_port), handler(broker, control=True, token=token))
    threading.Thread(target=controls.serve_forever, daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", args.port), handler(broker)).serve_forever()
