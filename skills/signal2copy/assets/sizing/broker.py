"""Fixture v5: account-scoped currencies/equity, FX ticks and volume conditions."""
import argparse
import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from http.server import ThreadingHTTPServer
import importlib.util
import os
from pathlib import Path
import re
import threading

spec = importlib.util.spec_from_file_location('fills_broker_v4', Path(__file__).resolve().parents[1] / 'fills/broker.py')
v4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)


def decimal(value):
    number = Decimal(str(value))
    if not number.is_finite(): raise ValueError('Finite decimal required')
    return number


class Broker(v4.Broker):
    def __init__(self, log):
        super().__init__(log)
        self.configuration = {account: {'currency':'USD', 'balance':'10000', 'equity':'10000', 'used_margin':'0',
            'instruments':['EURUSD'], 'volume_min':'0.01', 'volume_step':'0.01', 'volume_max':'10'} for account in self.accounts}
        self.ticks = {account: {'EURUSD':{'bid':'1.1000','ask':'1.1001','age_seconds':0},
            'USDJPY':{'bid':'150','ask':'151','age_seconds':0},
            'GBPUSD':{'bid':'1.4','ask':'1.5','age_seconds':0}} for account in self.accounts}

    def control(self, action, body):
        with self.lock:
            if action == 'state':
                return {**super().control(action, body), 'configuration':copy.deepcopy(self.configuration), 'ticks':copy.deepcopy(self.ticks)}
            if action == 'configuration':
                account=body['account']; old=self.configuration[account]
                if set(body)-set(old)-{'account'}: raise ValueError('Unknown configuration field')
                updated={**old, **{k:v for k,v in body.items() if k!='account'}}
                if not re.fullmatch('[A-Z]{3}', updated['currency']): raise ValueError('Currency code required')
                if not updated['instruments'] or not isinstance(updated['instruments'],list) or not set(updated['instruments']) <= set(self.ticks[account]):
                    raise ValueError('Known instrument inventory required')
                for name in ['balance','equity','used_margin','volume_min','volume_step','volume_max']:
                    value=decimal(updated[name])
                    if value < 0 or name.startswith('volume_') and value <= 0: raise ValueError('Invalid numeric configuration')
                    updated[name]=str(value)
                if decimal(updated['volume_min'])>decimal(updated['volume_max']): raise ValueError('Invalid volume range')
                if any(decimal(updated[k]) % Decimal('.01') for k in ['volume_min','volume_step','volume_max']) or decimal(updated['volume_max'])>10:
                    raise ValueError('Fixture supports 0.01-compatible volume conditions up to 10 lots')
                self.configuration[account]=updated
                return copy.deepcopy(updated)
            if action == 'quote':
                account, instrument=body['account'],body['instrument']
                if set(body)-{'account','instrument','bid','ask','age_seconds'}: raise ValueError('Unknown quote field')
                old=self.ticks[account][instrument]; updated={**old,**{k:v for k,v in body.items() if k not in {'account','instrument'}}}
                bid,ask,age=map(decimal,[updated['bid'],updated['ask'],updated['age_seconds']])
                if not 0<bid<=ask or not -3600<=age<=700000: raise ValueError('Invalid quote')
                updated={'bid':str(bid),'ask':str(ask),'age_seconds':float(age)}
                self.ticks[account][instrument]=updated
                return copy.deepcopy(updated)
            return super().control(action,body)

    def _public(self, method, path, query, headers, body):
        if path=='/healthz' and method=='GET':
            return 200,{'service':'orbit-behavior-broker','protocol':5,'capabilities':['v4','account_configuration','scoped_fx_ticks']}
        opening=re.fullmatch(r'/v1/trading/accounts/(1111|2222)/(positions|orders)',path)
        if method=='POST' and opening and 'volume' in body and headers.get('EXN-API-KEY')=='synthetic-'+opening[1]:
            config=self.configuration[opening[1]]; volume=decimal(body['volume'])
            if not decimal(config['volume_min'])<=volume<=decimal(config['volume_max']) or (volume-decimal(config['volume_min'])) % decimal(config['volume_step']):
                raise ValueError('Volume violates account conditions')
        match=re.fullmatch(r'/v1/trading/accounts/(1111|2222)/(details|snapshot|instruments|quotes)(?:/([A-Z]+))?',path)
        if method=='GET' and match:
            account,resource,instrument=match.groups()
            if headers.get('EXN-API-KEY')!='synthetic-'+account: return 401,{'detail':'Synthetic account access denied'}
            config=self.configuration[account]
            if resource=='details' and instrument is None:
                code,value=super()._public(method,path,query,headers,body)
                return code,{**value,'settings':{**value['settings'],'currency':config['currency']}}
            if resource=='snapshot' and instrument is None:
                code,value=super()._public(method,path,query,headers,body)
                return code,{**value,'account_state':{k:config[k] for k in ['balance','equity','used_margin']}}
            if resource=='instruments' and instrument is None: return 200,{'instruments':copy.deepcopy(config['instruments'])}
            if instrument not in config['instruments']: return 404,{'detail':'Instrument not available on this account'}
            if resource=='instruments':
                return 200,{'instrument':instrument,'base_currency':instrument[:3],'quote_currency':instrument[3:],
                    'margin_currency':instrument[:3],'calc_mode':'forex','contract_size':'100000','margin_percent':'1',
                    'point_digits':3 if instrument.endswith('JPY') else 5,'trade_mode':'enabled',
                    **{k:config[k] for k in ['volume_min','volume_step','volume_max']}}
            if resource=='quotes':
                tick=self.ticks[account][instrument]
                return 200,{'instrument':instrument,'bid':tick['bid'],'ask':tick['ask'],
                    'event_time':(datetime.now(timezone.utc)-timedelta(seconds=tick['age_seconds'])).isoformat(),
                    'received_at':datetime.now(timezone.utc).isoformat()}
        return super()._public(method,path,query,headers,body)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,required=True); parser.add_argument('--control-port',type=int,required=True)
    parser.add_argument('--log',type=Path,required=True);args=parser.parse_args()
    broker=Broker(args.log)
    controls=ThreadingHTTPServer(('127.0.0.1',args.control_port),v4.v3.handler(broker,control=True,token=os.environ['ACCEPTANCE_CONTROL_TOKEN']))
    threading.Thread(target=controls.serve_forever,daemon=True).start()
    ThreadingHTTPServer(('127.0.0.1',args.port),v4.v3.handler(broker)).serve_forever()
