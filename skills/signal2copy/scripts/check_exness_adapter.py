"""Offline exact-wire tests: generated keys and injected I/O, never network."""
import base64,hashlib,json,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'assets'))
from exness_adapter import ExnessAdapter,AdapterError,IntentJournal,origin
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from unittest.mock import patch
checks=[]
def check(name,ok=True):
 assert ok,name
 checks.append(name);print('PASS '+name,flush=True)
def denied(fn):
 try:fn()
 except AdapterError:return True
 return False
seed=Ed25519PrivateKey.generate();private=seed.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption()).hex();public=seed.public_key()
def b64(value):return base64.urlsafe_b64decode(value+'='*((-len(value))%4))
class Wire:
 def __init__(self):self.calls=[];self.responses=[]
 def __call__(self,method,url,h,body):
  data=b64(h['EXN-DATA']);public.verify(b64(h['EXN-SIGN']),data);p=json.loads(data)
  from urllib.parse import urlsplit
  u=urlsplit(url);path=u.path+('?' +u.query if u.query else '')
  assert p['path']==path and p['method']==method and p['body_hash']==base64.urlsafe_b64encode(hashlib.sha256(body).digest()).decode().rstrip('=')
  assert p['idempotency_key']==h['EXN-IDEMPOTENCY-KEY'] and p['timestamp']==int(h['EXN-TIMESTAMP'])
  self.calls.append((method,url,h,body));return self.responses.pop(0)
def answer(value,status=200,headers=None):return status,value,headers or {}
def make(w):return ExnessAdapter('https://gateway.example','dummy-api',private,send=w)
account={'account_id':'123456','settings':{'currency':'USD','trade_mode':'enabled','account_status':'active'}}
snapshot={'positions':[],'orders':[],'account_state':{'balance':'10000','equity':'10000','used_margin':'0'}}
w=Wire();c=make(w);w.responses=[answer({'access_point':'https://ap.example'}),answer(account),answer(snapshot),answer({'limits':{}})];assert c.account('123456')==account;assert c.snapshot('123456')==snapshot;c.limits('123456');check('discovery and account-native signedGETs use exact path/header/body bytes',len(w.calls)==4 and all(x[2]['EXN-IDEMPOTENCY-KEY']=='' and x[3]==b'' for x in w.calls));check('per-account access-point cache avoids rediscovery',sum('/access-point?' in x[1] for x in w.calls)==1)
check('path traversal and account crossing denied before I/O',denied(lambda:c.get('123456','/v1/configuration/accounts/999999/account')) and denied(lambda:c.get('123456','/v1/configuration/accounts/123456/../../../accounts/999999/account')))
check('origins reject nonHTTPS credential/query/path injection',all(denied(lambda x=x:origin(x)) for x in ['http://ap.example','https://user:pass@ap.example','https://ap.example/x','https://ap.example?key=x']))
w.responses=[answer({'items':[{'deal':{'deal_id':'1'}}],'next_cursor':'opaque+/= ?', 'has_more':True}),answer({'items':[{'deal':{'deal_id':'2'}}],'has_more':False})];data=c.history('123456','deals','2026-11-17T00:00:00Z','2026-11-18T00:00:00Z');check('opaque cursor only combines with limit and exact encoded signature',len(data['items'])==2 and 'from=' not in w.calls[-1][1] and 'cursor=opaque%2B%2F%3D+%3F' in w.calls[-1][1])
w.responses=[answer({'items':[],'next_cursor':'same'}),answer({'items':[],'next_cursor':'same'})];check('repeated history cursor cannot yield false completeness',denied(lambda:c.history('123456','orders','2026-11-17T00:00:00Z','2026-11-18T00:00:00Z')))
w.responses=[answer({'candles':[{'time':'2026-11-17T00:00:00Z','bid':{'close':1.1},'ask':{'close':1.2}}]})];data=c.candles('123456','EURUSD','D1','2026-11-17T00:00:00Z','2026-11-18T00:00:00Z');check('native bidask candle maps original time without executable tick fiction',data['items'][0]['open_time']=='2026-11-17T00:00:00+00:00' and data['items'][0]['constituent_tick_time'] is None and 'price_type=both' in w.calls[-1][1])
prior=len(w.calls);check('real writes disabled before network by default',denied(lambda:c.submit('123456','POST','positions',{'volume':'0.01'},'one-1',lambda:True)) and len(w.calls)==prior)
with tempfile.TemporaryDirectory() as folder:
 journal=IntentJournal(Path(folder)/'journal.sqlite3');c.allow_writes=True;c.journal=journal
 w.responses=[answer({'operation_id':'789','client_request_id':'one-1'})];ack=c.submit('123456','POST','positions',{'instrument':'EURUSD','side':'buy','volume':'0.01'},'one-1',lambda:True);check('mutation exact bytes and stable identity persist before ACKpending',journal.get('123456','one-1')['status']=='pending' and ack['operation_id']=='789')
 check('same persisted request cannot be resent after ACK',denied(lambda:c.submit('123456','POST','positions',{},'one-1',lambda:True)))
 w.responses=[answer({'operation_id':'790','client_request_id':'one-1','status':'confirmed'})];check('matching request cannot rebind to another operation after ACK',denied(lambda:c.operation('123456','790','one-1')) and journal.get('123456','one-1')['status']=='pending' and journal.get('123456','one-1')['operation_id']=='789')
 w.responses=[answer({'operation_id':'789','client_request_id':'wrong','status':'confirmed'})];check('unrelated operation cannot settle command',denied(lambda:c.operation('123456','789','one-1')) and journal.get('123456','one-1')['status']=='pending')
 w.responses=[answer({'operation_id':'789','client_request_id':'one-1','status':'confirmed'})];c.operation('123456','789','one-1');check('exact operation evidence settles native confirmed status',journal.get('123456','one-1')['status']=='confirmed')
 def lost(*args):raise TimeoutError()
 c.send=lost;check('lost mutation response stays unknown with no auto-retry',denied(lambda:c.submit('123456','POST','positions',{'volume':'0.01'},'lost-1',lambda:True)) and journal.get('123456','lost-1')['status']=='unknown');journal.close()
 journal=IntentJournal(Path(folder)/'journal.sqlite3');c.journal=journal;check('unknown survives journal reopen and cannot resend',denied(lambda:c.submit('123456','POST','positions',{},'lost-1',lambda:True)));journal.close()
w=Wire();c=make(w);c.routes['123456']='https://ap.example';w.responses=[answer({'code':3015},429,{'Retry-After':'120'})];check('quota response surfaced without automatic retry',denied(lambda:c.limits('123456')) and len(w.calls)==1);check('same account cooldown denies another I/O',denied(lambda:c.snapshot('123456')) and len(w.calls)==1)
w=Wire();c=make(w);clock=[0];c.clock=lambda:clock[0]
w.responses=[answer({'code':1003,'retry_after':9},429)]
check('Gateway body retry delay applies to discovery',denied(lambda:c.discover('123456')) and len(w.calls)==1)
clock[0]=8
check('Discovery stays held before the declared delay',denied(lambda:c.discover('123456')) and len(w.calls)==1)
clock[0]=9;w.responses=[answer({'access_point':'https://ap.example'})]
check('Discovery resumes when the declared cooldown ends',c.discover('123456')=='https://ap.example' and len(w.calls)==2)

class Socket:
 def __init__(self,messages):self.messages=messages;self.sent=[];self.closed=False
 def send(self,text):self.sent.append(json.loads(text))
 def recv(self,timeout):
  item=self.messages.pop(0)
  if isinstance(item,Exception):raise item
  return json.dumps(item)
 def close(self):self.closed=True
w=Wire();c=make(w);c.routes['123456']='https://ap.example'
sock=Socket([{'event_type':'trading_state_snapshot','payload':snapshot},{'event_type':'transaction_event','operation_id':'789','client_request_id':'one-1','status':'success','payload':{'positions':[{'position_id':'321','state':'open','volume':'0.01'}]}},OSError()])
def connect(url,**kwargs):
 assert kwargs['user_agent_header']=='Signal2Copy/0.1'
 assert kwargs['subprotocols']==['exness-ws-protocol']
 h=kwargs['additional_headers'];p=json.loads(b64(h['EXN-DATA']));assert p['method']=='GET' and p['path']=='/v1/server-events/accounts/123456/ws/events';public.verify(b64(h['EXN-SIGN']),b64(h['EXN-DATA']));return sock
stream=c.stream('123456','transactions',connect=connect).open();stream.receive();check('signedWS GET and native subscription await snapshot',stream.synchronized and sock.sent[0]['subscribe']=={'event':'transactions'});stream.receive();check('transaction deltas update current state without treating delta as full snapshot',len(stream.snapshot['positions'])==1 and len(stream.results)==1);check('disconnect invalidates stream state and prevents stale synchronization',denied(lambda:stream.receive()) and not stream.synchronized and stream.snapshot is None and not stream.results)
sock=Socket([{'event_type':'transaction_event','operation_id':'1','status':'success','payload':{}}]);stream=c.stream('123456','transactions',connect=connect).open();check('transaction before fresh subscription snapshot fails closed',denied(lambda:stream.receive()) and not stream.synchronized)
now=datetime.now(timezone.utc).isoformat();sock=Socket([{'instrument':'EURUSD','bid':1.1,'ask':1.2,'timestamp':now}]);
def tick_connect(url,**kw):
 assert url.endswith('/v1/server-events/accounts/123456/ws/ticks') and json.loads(b64(kw['additional_headers']['EXN-DATA']))['path'].endswith('/ws/ticks');return sock
stream=c.stream('123456','ticks',['EURUSD'],tick_connect).open();stream.receive();check('separate native ticks preserve original timestamp and decimal values',stream.ticks['EURUSD']['event_time']==now and sock.sent[0]['subscribe']=={'event':'ticks','instruments':['EURUSD']} and stream.ticks['EURUSD']['bid']=='1.1');stream.close()
sock=Socket([{'event_type':'trading_state_snapshot','payload':snapshot},{'event_type':'transaction_event','status':'success','payload':{'account_state':{'balance':'10001','equity':'10001','used_margin':'0'}}}]);stream=c.stream('123456','transactions',connect=connect).open();stream.receive();stream.receive();check('uncorrelated system balance delta updates state without settling any request',stream.snapshot['account_state']['balance']=='10001' and not stream.results);stream.close()
with tempfile.TemporaryDirectory() as folder:
 journal=IntentJournal(Path(folder)/'journal.sqlite3');w=Wire();c=make(w);c.routes['123456']='https://ap.example';c.allow_writes=True;c.journal=journal
 before=len(w.calls);check('invalid native idempotency identity rejected before I/O',denied(lambda:c.submit('123456','POST','positions',{},'bad',lambda:True)) and len(w.calls)==before)
 check('DELETE body cannot silently become full close',denied(lambda:c.submit('123456','DELETE','positions/321',{'volume':'0.01'},'close-1',lambda:True)) and len(w.calls)==before)
 w.responses=[answer({'operation_id':'790','client_request_id':'close-2'})];c.submit('123456','DELETE','positions/321',None,'close-2',lambda:True,query={'volume':'0.01'});check('partial close volume is exact signed native query with empty body',w.calls[-1][1].endswith('/positions/321?volume=0.01') and w.calls[-1][3]==b'');journal.close()
with tempfile.TemporaryDirectory() as folder:
 class SlowJournal(IntentJournal):
  def reserve(self,*args):super().reserve(*args);generation[0]+=1
 generation=[1];journal=SlowJournal(Path(folder)/'journal.sqlite3');w=Wire();c=make(w);c.routes['123456']='https://ap.example';c.allow_writes=True;c.journal=journal
 check('post-durable generation change vetoes dispatch and records not_sent',denied(lambda:c.submit('123456','POST','positions',{'volume':'0.01'},'fence-1',lambda:generation[0]==1)) and not w.calls and journal.get('123456','fence-1')['status']=='not_sent');journal.close()
sock=Socket([{'event_type':'trading_state_snapshot','payload':snapshot},TimeoutError()]);stream=c.stream('123456','transactions',connect=connect).open();stream.receive()
try:stream.receive()
except TimeoutError:pass
else:raise AssertionError('Expected idle receive timeout')
check('normal quiet-stream timeout preserves subscription baseline',stream.synchronized and stream.snapshot is not None and not sock.closed);stream.close()
sock=Socket([]);stream=c.stream('123456','transactions',connect=connect).open();sock.messages=[{'id':sock.sent[0]['id'],'code':'200'},{'event_type':'trading_state_snapshot','payload':snapshot}]
stream.receive();assert not stream.synchronized and stream.snapshot is None
stream.receive();check('correlated subscription200 ACK waits for actual native trading baseline',stream.synchronized);stream.close()
sock=Socket([{'id':'another-subscription','code':'200'}]);stream=c.stream('123456','transactions',connect=connect).open();check('uncorrelated subscription200 cannot establish or retain synchronization',denied(lambda:stream.receive()) and not stream.synchronized and sock.closed)
class HttpResponse:
 status=200;headers={}
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def read(self,size):return b'{}'
class HttpOpener:
 def open(self,request,timeout):
  assert request.get_header('User-agent')=='Signal2Copy/0.1' and request.get_header('Exn-api-key')=='transport-dummy'
  assert request.method=='GET' and request.data is None
  return HttpResponse()
from exness_adapter import https_send
with patch('exness_adapter.build_opener',return_value=HttpOpener()):
 check('actual HTTPS transport adds explicit product User-Agent without altering signed headers',https_send('GET','https://ap.example/test',{'EXN-API-KEY':'transport-dummy'},b'')[0]==200)
summary={'count':len(checks),'passed':checks,'network_access':False,'live_broker':False,'scope':'Injected native HTTP/WS with generated keys; actual TLS/authentication untested by this offline check'}
if '--output' in sys.argv:
 output=Path(sys.argv[sys.argv.index('--output')+1]);output.write_text(json.dumps(summary,indent=2)+'\n')
print('Completed '+str(len(checks))+' offline native checks',flush=True)
