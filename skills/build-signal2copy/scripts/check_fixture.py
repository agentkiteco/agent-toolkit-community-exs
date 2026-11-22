"""Loopback self-check of the bundled broker; never tests an application or real broker."""
import importlib.util
import json
from pathlib import Path
import secrets
import tempfile
import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('skill_fixture_v5', root / 'assets/sizing/broker.py')
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    with tempfile.TemporaryDirectory(prefix='signal2copy-fixture-check-') as temp:
        broker = fixture.Broker(Path(temp) / 'mutations.jsonl')
        token = secrets.token_urlsafe(24)
        handler = fixture.v4.v3.handler
        public = ThreadingHTTPServer(('127.0.0.1', 0), handler(broker))
        control = ThreadingHTTPServer(('127.0.0.1', 0), handler(broker, control=True, token=token))
        threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in (public, control)]
        for thread in threads:
            thread.start()

        def call(path, *, method='GET', body=None, account=None, key=None, operator=False, authorized=True):
            port = (control if operator else public).server_port
            headers = {}
            if account:
                headers['EXN-API-KEY'] = 'synthetic-' + account
            if key:
                headers['EXN-IDEMPOTENCY-KEY'] = key
            if operator and authorized:
                headers['Authorization'] = 'Bearer ' + token
            data = None if body is None else json.dumps(body).encode()
            if data is not None:
                headers['Content-Type'] = 'application/json'
            request = Request('http://127.0.0.1:' + str(port) + path, data=data, headers=headers, method=method)
            try:
                with urlopen(request, timeout=3) as response:
                    return response.status, json.load(response)
            except HTTPError as response:
                return response.code, json.load(response)

        try:
            assert call('/healthz')[1]['protocol'] == 5
            assert call('/v1/partner')[0] == 401
            assert call('/state', operator=True, authorized=False)[0] == 403
            assert call('/v1/trading/accounts/1111/details', account='2222')[0] == 401
            assert call('/v1/trading/accounts/2222/details', account='2222')[1]['settings']['currency'] == 'USD'
            assert call('/position', method='POST', operator=True,
                        body={'account':'1111', 'id':'91001', 'volume':'0.08', 'side':'buy'})[0] == 200
            body = {'instrument':'EURUSD', 'side':'buy', 'volume':'0.02'}
            path = '/v1/trading/accounts/2222/positions'
            status, ack = call(path, method='POST', body=body, account='2222', key='selfcheck-open-1')
            assert status == 202
            assert call(path, method='POST', body=body, account='2222', key='selfcheck-open-1')[1] == ack
            assert call(path, method='POST', body={**body, 'volume':'0.03'}, account='2222', key='selfcheck-open-1')[0] == 409
            snapshot = call('/v1/trading/accounts/2222/snapshot', account='2222')[1]
            assert len(snapshot['positions']) == 1 and snapshot['positions'][0]['volume'] == '0.02'
            assert call('/v1/trading/accounts/2222/operations/' + ack['operation_id'], account='2222')[1]['status'] == 'success'
            assert call('/fault', method='POST', operator=True,
                        body={'account':'2222', 'kind':'apply_then_503_hold', 'method':'POST'})[0] == 200
            assert call(path, method='POST', body=body, account='2222', key='selfcheck-open-2')[0] == 503
            assert len(call('/v1/trading/accounts/2222/snapshot', account='2222')[1]['positions']) == 2
            call('/release', method='POST', body={}, operator=True)
            print(json.dumps({'result':'passed', 'scope':'fixture-only loopback HTTP',
                              'checks':['protocol5','account/control authorization','source seed','market effect',
                                        'idempotent replay','conflicting request identity','exact operation status','applied-but-503 state'],
                              'generated_application_tested':False, 'real_broker_access':False}))
        finally:
            for server in (public, control):
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(timeout=3)


if __name__ == '__main__':
    main()
