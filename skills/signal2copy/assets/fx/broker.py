"""Synthetic fixture v6 wrapper: explicit contract metadata, candles and read faults.
No real broker schema/signatures or matching engine are modeled.
"""
import argparse,copy,importlib.util,json,os,re,threading,time
from datetime import datetime,timedelta,timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
spec=importlib.util.spec_from_file_location('sizing_v5',Path(__file__).resolve().parents[1]/'sizing/broker.py');v5=importlib.util.module_from_spec(spec);spec.loader.exec_module(v5)
class Broker(v5.Broker):
 def __init__(self,log):
  super().__init__(log);self.contracts={a:{} for a in self.accounts};self.candles={a:{} for a in self.accounts};self.reads=[];self.read_faults={};self.read_delays={};self.fixed_quotes={}
 def control(self,action,body):
  with self.lock:
   if action=='state':return {**super().control(action,body),'fx_reads':copy.deepcopy(self.reads)}
   if action=='fx-fixed-quote':
    result=super().control('quote',body)
    at=datetime.now(timezone.utc)
    self.fixed_quotes[(body['account'],body['instrument'])]={'event_time':(at-timedelta(seconds=float(body.get('age_seconds',0)))).isoformat(),'received_at':at.isoformat()}
    return result
   if action=='fx-contract':
    a,symbol=body['account'],body['instrument'];self.contracts[a][symbol]={k:v for k,v in body.items() if k not in {'account','instrument'}}
    self.ticks[a].setdefault(symbol,{'bid':'1','ask':'1','age_seconds':0})
    return {'configured':True}
   if action=='fx-candles':
    a,symbol,tf=body['account'],body['instrument'],body['timeframe']
    if tf not in {'M1','D1'}:raise ValueError('Synthetic timeframe must be M1 or D1')
    # Fixed original open times; repeated reads never refresh candle age.
    now=datetime.now(timezone.utc);items=[]
    for item in body['items']:
     item=dict(item)
     if 'age_seconds' in item:item['open_time']=(now-timedelta(seconds=float(item.pop('age_seconds')))).isoformat()
     items.append(item)
    self.candles[a][symbol,tf]=items;return {'configured':len(items)}
   if action=='fx-read-delay':
    seconds=float(body['seconds'])
    if not 0<=seconds<=2.7:raise ValueError('One-shot synthetic read delay must be0to2.7seconds')
    self.read_delays[(body['account'],body['resource'])]=seconds;return {'configured':True}
   if action=='fx-read-fault':
    self.read_faults[(body['account'],body['resource'])]=int(body['status']);return {'configured':True}
   return super().control(action,body)
 def _public(self,method,path,query,headers,body):
  match=re.fullmatch(r'/v1/trading/accounts/(1111|2222)/(instruments|quotes|candles)(?:/([A-Z]+))?',path)
  if method=='GET' and match:
   account,resource,instrument=match.groups()
   if headers.get('EXN-API-KEY')!='synthetic-'+account:return 401,{'detail':'Synthetic account access denied'}
   if instrument is not None and instrument not in self.configuration[account]['instruments']:return 404,{'detail':'Instrument not available on this account'}
   self.reads.append({'account':account,'resource':resource,'instrument':instrument,'query':query})
   delay=self.read_delays.pop((account,resource+'/'+str(instrument)),0)
   if delay:time.sleep(delay)
   status=self.read_faults.get((account,resource+'/'+str(instrument)),200)
   if status!=200:return status,{'detail':'Synthetic configured read fault'}
   if resource=='quotes' and (account,instrument) in self.fixed_quotes:
    code,value=super()._public(method,path,query,headers,body)
    return code,{**value,**self.fixed_quotes[(account,instrument)]}
   if resource=='instruments' and instrument:
    values=self.contracts[account].get(instrument,{})
    return 200,{'instrument':instrument,'base_currency':values.get('base_currency',instrument[:3]),'quote_currency':values.get('quote_currency',instrument[3:]),'margin_currency':values.get('margin_currency',values.get('base_currency',instrument[:3])),'calc_mode':'forex','contract_size':'100000','margin_percent':'1','point_digits':5,'trade_mode':'enabled',**{k:self.configuration[account][k] for k in ('volume_min','volume_step','volume_max')},**values}
   if resource=='candles' and instrument:
    tf=query.get('timeframe',[''])[0]
    if tf not in {'M1','D1'}:return 400,{'detail':'Synthetic timeframe required'}
    return 200,{'items':copy.deepcopy(self.candles[account].get((instrument,tf),[]))}
  return super()._public(method,path,query,headers,body)
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,required=True);parser.add_argument('--control-port',type=int,required=True);parser.add_argument('--log',type=Path,required=True);args=parser.parse_args()
 broker=Broker(args.log);controls=ThreadingHTTPServer(('127.0.0.1',args.control_port),v5.v4.v3.handler(broker,control=True,token=os.environ['ACCEPTANCE_CONTROL_TOKEN']));threading.Thread(target=controls.serve_forever,daemon=True).start();ThreadingHTTPServer(('127.0.0.1',args.port),v5.v4.v3.handler(broker)).serve_forever()
