"""Native Exness boundary. Browser copying remains synthetic; writes are opt-in.
Official routes checked 2026-11-18. No automatic HTTP or mutation retries.
"""
import hashlib,json,re,sqlite3,time,uuid
from contextlib import nullcontext
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode,urlsplit
from urllib.request import Request,HTTPSHandler,HTTPRedirectHandler,ProxyHandler,build_opener
from exness_signing import headers,load_key

MAX_RESPONSE=2*1024*1024
USER_AGENT='Signal2Copy/0.1'
WS_SUBPROTOCOL='exness-ws-protocol'
class AdapterError(Exception):
 def __init__(self,message,status=None,code=None,unknown=False):
  super().__init__(message);self.status=status;self.code=code;self.unknown=unknown
class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None

def origin(value):
 try:u=urlsplit(value);port=u.port
 except (ValueError,TypeError):raise AdapterError('Invalid HTTPS origin') from None
 if u.scheme!='https' or not u.hostname or u.username or u.password or u.path not in ('','/') or u.query or u.fragment or port not in (None,443):raise AdapterError('HTTPS origin without path/query/credentials required')
 return 'https://'+u.hostname.lower()
def identifier(value):
 if not isinstance(value,str) or not re.fullmatch('[1-9][0-9]{0,19}',value) or int(value)>2**64-1:raise AdapterError('Positive uint64 decimal account/operation identifier required')
 return value
def instrument(value):
 if not isinstance(value,str) or not re.fullmatch('[A-Za-z0-9._-]{1,11}',value):raise AdapterError('Invalid instrument identifier')
 return value
def instant(value):
 try:d=datetime.fromisoformat(value.replace('Z','+00:00'))
 except (TypeError,ValueError,AttributeError):raise AdapterError('Timezone-aware ISO time required') from None
 if d.tzinfo is None:raise AdapterError('Timezone-aware ISO time required')
 return d.astimezone(timezone.utc)
def decimal(value):
 try:d=Decimal(str(value))
 except Exception:raise AdapterError('Invalid decimal value') from None
 if not d.is_finite():raise AdapterError('Finite decimal value required')
 return d

def https_send(method,url,signed,body):
 """No redirects, proxies or automatic retries. Errors never include body/headers."""
 request=Request(url,headers={'User-Agent':USER_AGENT,**signed,'Content-Type':'application/json'},data=body if method!='GET' else None,method=method)
 try:
  with build_opener(ProxyHandler({}),NoRedirect(),HTTPSHandler()).open(request,timeout=10) as r:
   raw=r.read(MAX_RESPONSE+1);status=r.status;response_headers=dict(r.headers)
 except HTTPError as e:
  status=e.code;response_headers=dict(e.headers);raw=e.read(MAX_RESPONSE+1)
 except (URLError,OSError,TimeoutError):raise AdapterError('Exness transport unavailable',unknown=method!='GET') from None
 if len(raw)>MAX_RESPONSE:raise AdapterError('Exness response exceeds size limit',unknown=method!='GET')
 try:value=json.loads(raw,parse_float=Decimal)
 except (ValueError,UnicodeError):raise AdapterError('Malformed Exness JSON response',status=status,unknown=method!='GET') from None
 return status,value,response_headers

class IntentJournal:
 """Separate durable command evidence; never stores signing credentials."""
 def __init__(self,path):
  p=Path(path);p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
  self.db=sqlite3.connect(p);p.chmod(0o600)
  self.db.execute('PRAGMA synchronous=FULL');self.db.execute('CREATE TABLE IF NOT EXISTS intents(account TEXT,key TEXT,fingerprint TEXT,status TEXT,operation TEXT,PRIMARY KEY(account,key))');self.db.commit()
 def reserve(self,account,key,fingerprint):
  try:self.db.execute('INSERT INTO intents VALUES(?,?,?,?,NULL)',(account,key,fingerprint,'unknown'));self.db.commit()
  except sqlite3.IntegrityError:raise AdapterError('Persisted request already exists; investigate without resending',unknown=True) from None
 def update(self,account,key,status,operation=None):
  bound=self.get(account,key)
  if bound is None:raise AdapterError('No persisted request identity to settle',unknown=True)
  if operation and bound['operation_id'] and operation!=bound['operation_id']:raise AdapterError('Operation conflicts with persisted acknowledgement binding',unknown=True)
  self.db.execute('UPDATE intents SET status=?,operation=COALESCE(?,operation) WHERE account=? AND key=?',(status,operation,account,key));self.db.commit()
 def get(self,account,key):
  row=self.db.execute('SELECT fingerprint,status,operation FROM intents WHERE account=? AND key=?',(account,key)).fetchone()
  return dict(zip(('fingerprint','status','operation_id'),row)) if row else None
 def close(self):self.db.close()

class ExnessAdapter:
 def __init__(self,gateway,api_key,private_key,send=https_send,*,allow_writes=False,journal=None,clock=time.monotonic):
  self.gateway=origin(gateway);self.api_key=api_key;self.key=load_key(private_key);self.send=send;self.allow_writes=allow_writes;self.journal=journal;self.clock=clock;self.routes={};self.blocked={}
 def _request(self,host,method,path,account,body=b'',request_id=''):
  if self.clock()<self.blocked.get(account,0):raise AdapterError('Account request capacity cooling down',status=429,code=3015)
  signed=headers(self.api_key,self.key,method,path,body,request_id)
  try:status,value,response_headers=self.send(method,host+path,signed,body)
  except AdapterError:raise
  except Exception:raise AdapterError('Exness transport unavailable',unknown=method!='GET') from None
  if not isinstance(value,dict):raise AdapterError('Exness response object required',unknown=method!='GET')
  if status==429 or value.get('code')==3015:
   retry=next((v for k,v in response_headers.items() if k.lower()=='retry-after'),value.get('retry_after'))
   try:seconds=max(1,min(float(retry),3600))
   except (TypeError,ValueError):seconds=60
   self.blocked[account]=self.clock()+seconds
  if not 200<=status<300:
   raise AdapterError('Exness request failed (HTTP '+str(status)+')',status,value.get('code'),unknown=method!='GET' and status not in {400,401,403,404,405,409,415,422,429})
  return value
 def discover(self,account):
  account=identifier(account)
  if account not in self.routes:
   data=self._request(self.gateway,'GET','/v1/trading/access-point?'+urlencode({'account_id':account}),account)
   self.routes[account]=origin(data.get('access_point'))
  return self.routes[account]
 def get(self,account,path,query=None):
  account=identifier(account)
  if not path.startswith('/') or '?' in path or '#' in path:raise AdapterError('Native path must exclude query/fragment')
  # Public helper cannot cross account boundaries or send signed data to an arbitrary host.
  if not re.fullmatch(r'/v1/(configuration|trading|history|market-data)/accounts/'+account+r'/(account|limits|snapshot|instruments(?:/[A-Za-z0-9._-]{1,11}/conditions)?|orders|deals|candles|operations/[1-9][0-9]{0,19})',path):raise AdapterError('Native path/account mismatch or unsupported route')
  return self._request(self.discover(account),'GET',path+('?' + urlencode(query) if query else ''),account)
 def account(self,account):
  value=self.get(account,'/v1/configuration/accounts/'+identifier(account)+'/account')
  if value.get('account_id')!=account:raise AdapterError('Returned account identity mismatch')
  if not isinstance(value.get('settings'),dict) or not isinstance(value['settings'].get('currency'),str):raise AdapterError('Account currency/settings missing')
  return value
 def snapshot(self,account):
  value=self.get(account,'/v1/trading/accounts/'+identifier(account)+'/snapshot');validate_snapshot(value);return value
 def limits(self,account):return self.get(account,'/v1/configuration/accounts/'+identifier(account)+'/limits')
 def instruments(self,account):return self.get(account,'/v1/configuration/accounts/'+identifier(account)+'/instruments')
 def conditions(self,account,symbol):return self.get(account,'/v1/configuration/accounts/'+identifier(account)+'/instruments/'+instrument(symbol)+'/conditions')
 def history(self,account,kind,from_time,to_time,*,limit=100,max_pages=20):
  if kind not in {'orders','deals'} or type(limit)!=int or not 1<=limit<=200 or type(max_pages)!=int or not 1<=max_pages<=100:raise AdapterError('Invalid bounded history request')
  if not instant(from_time)<instant(to_time)<=datetime.now(timezone.utc):raise AdapterError('Invalid historical time range')
  query={'from':from_time,'to':to_time,'limit':limit};items=[];seen=set()
  for _ in range(max_pages):
   page=self.get(account,'/v1/history/accounts/'+identifier(account)+'/'+kind,query)
   if not isinstance(page.get('items'),list):raise AdapterError('History items missing')
   items.extend(page['items']);cursor=page.get('next_cursor')
   if not cursor and not page.get('has_more',False):return {'items':items,'pagination_complete':True,'coverage':'Broker-returned records; retention/completeness not guaranteed'}
   if not isinstance(cursor,str) or not cursor or cursor in seen:raise AdapterError('Invalid/repeated history cursor; completeness unavailable')
   seen.add(cursor);query={'cursor':cursor,'limit':limit}
  raise AdapterError('History page bound reached; completeness unavailable')
 def candles(self,account,symbol,timeframe,from_time,to_time):
  if timeframe not in {'M1','D1'} or not instant(from_time)<instant(to_time)<=datetime.now(timezone.utc):raise AdapterError('Invalid bounded conversion-candle request')
  data=self.get(account,'/v1/market-data/accounts/'+identifier(account)+'/candles',{'instrument':instrument(symbol),'timeframe':timeframe,'from':from_time,'to':to_time,'price_type':'both'})
  result=[]
  if not isinstance(data.get('candles'),list):raise AdapterError('Bid/Ask candle collection missing')
  for row in data['candles']:
   at=instant(row.get('time'));bid=decimal(row.get('bid',{}).get('close'));ask=decimal(row.get('ask',{}).get('close'))
   if not instant(from_time)<=at<instant(to_time) or not 0<bid<=ask:raise AdapterError('Invalid original Bid/Ask candle')
   result.append({'open_time':at.isoformat(),'bid_close':str(bid),'ask_close':str(ask),'reference_only':True,'constituent_tick_time':None})
  return {'items':result,'native_price_type':'both'}
 def operation(self,account,operation_id,request_id=None):
  data=self.get(account,'/v1/trading/accounts/'+identifier(account)+'/operations/'+identifier(operation_id))
  if data.get('operation_id')!=operation_id or data.get('status') not in {'pending','confirmed','rejected','failed'} or request_id and data.get('client_request_id')!=request_id:raise AdapterError('Uncorrelated operation result',unknown=True)
  if request_id and self.journal:self.journal.update(account,request_id,data['status'],operation_id)
  return data
 def submit(self,account,method,resource,body,request_id,preflight,query=None):
  if not self.allow_writes or not self.journal:raise AdapterError('Real writes disabled; verified engine integration and durable journal required')
  account=identifier(account)
  if not re.fullmatch(r'(positions|orders)(/[1-9][0-9]{0,19})?',resource) or method not in {'POST','PATCH','DELETE'}:raise AdapterError('Unsupported native write shape')
  if method=='POST' and '/' in resource or method in {'PATCH','DELETE'} and '/' not in resource or method=='PATCH' and not resource.startswith('orders/'):raise AdapterError('Unsupported native write method')
  if not isinstance(request_id,str) or not re.fullmatch(r'[A-Za-z0-9._~\-]{5,128}',request_id):raise AdapterError('Native request identity must be5to128allowed characters')
  if method=='DELETE' and body is not None:raise AdapterError('Native DELETE body unsupported; partial close uses explicit volume query')
  if query:
   if method!='DELETE' or not resource.startswith('positions/') or set(query)!={'volume'} or not isinstance(query['volume'],str) or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?',query['volume']) or decimal(query['volume'])<=0:raise AdapterError('Only positive native position-close volume query is supported')
  host=self.discover(account);path='/v1/trading/accounts/'+account+'/'+resource+('?' +urlencode(query) if query else '')
  # Resolve routing before the caller's final ownership/permissions/fresh-state/RMS check.
  if preflight() is not True:raise AdapterError('Application preflight did not authorize this exact effect')
  raw=json.dumps(body,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode() if body is not None else b''
  fingerprint=hashlib.sha256(method.encode()+b'\n'+path.encode()+b'\n'+raw).hexdigest()
  self.journal.reserve(account,request_id,fingerprint)
  # Durable persistence may outlive quote/session/epoch validity. Re-evaluate after it.
  try:
   authorized=preflight() is True
  except Exception:
   self.journal.update(account,request_id,'not_sent');raise AdapterError('Final application preflight failed after durable reservation') from None
  if not authorized:
   self.journal.update(account,request_id,'not_sent');raise AdapterError('Final application preflight did not authorize this exact effect')
  try:
   ack=self._request(host,method,path,account,raw,request_id)
   if ack.get('client_request_id')!=request_id or not ack.get('operation_id'):raise AdapterError('Uncorrelated write acknowledgement',unknown=True)
   identifier(ack['operation_id']);self.journal.update(account,request_id,'pending',ack['operation_id']);return ack
  except AdapterError as e:
   if e.status in {400,401,403,404,405,409,422,429} and not e.unknown:self.journal.update(account,request_id,'rejected')
   raise
 def stream(self,account,event,instruments=None,connect=None):return NativeStream(self,account,event,instruments,connect)

def validate_snapshot(value):
 if not isinstance(value,dict) or not isinstance(value.get('positions'),list) or not isinstance(value.get('orders'),list) or not isinstance(value.get('account_state'),dict):raise AdapterError('Native snapshot shape invalid')
 for key in ('balance','equity','used_margin'):decimal(value['account_state'].get(key))

class NativeStream:
 """One bounded transport session; caller schedules reconnect/backoff. No replay claim."""
 def __init__(self,adapter,account,event,instruments,connect):
  if event not in {'transactions','account_state','instruments','hmr','ticks'}:raise AdapterError('Unsupported native subscription')
  self.adapter=adapter;self.account=identifier(account);self.event=event;self.instruments=[instrument(s) for s in (instruments or [])];self.connect=connect;self.socket=None;self.subscription_id=None;self.synchronized=False;self.snapshot=None;self.ticks={};self.results={};self.last_error=None
  if event in {'ticks','hmr'} and not self.instruments:raise AdapterError('Subscription instruments required')
 def open(self):
  self.close();host=self.adapter.discover(self.account);path='/v1/server-events/accounts/'+self.account+'/ws/'+('ticks' if self.event=='ticks' else 'events')
  if self.connect is None:
   from websockets.sync.client import connect
  else:connect=self.connect
  signed=headers(self.adapter.api_key,self.adapter.key,'GET',path)
  self.socket=connect('wss://'+urlsplit(host).netloc+path,additional_headers=signed,user_agent_header=USER_AGENT,subprotocols=[WS_SUBPROTOCOL],proxy=None,open_timeout=10,max_size=MAX_RESPONSE)
  subscription={'event':self.event}
  if self.instruments:subscription['instruments']=self.instruments
  self.subscription_id=str(uuid.uuid4())
  self.socket.send(json.dumps({'id':self.subscription_id,'subscribe':subscription},separators=(',',':')))
  return self
 def receive(self,timeout=10):
  if self.socket is None:raise AdapterError('Stream disconnected; resubscribe required')
  try:
   raw=self.socket.recv(timeout=timeout)
   with getattr(self,'state_lock',nullcontext()):
    value=json.loads(raw,parse_float=Decimal)
    if not isinstance(value,dict):raise AdapterError('Invalid native stream message')
    if 'code' in value:
     # A correlated control ACK is not a trading snapshot, tick or transaction.
     if set(value)=={'id','code'} and value['id']==self.subscription_id and value['code'] in ('200',200):return value
     raise AdapterError('Native subscription rejected or uncorrelated',code=value['code'])
    if self.event=='ticks':
     if 'instrument' not in value:return value
     symbol=instrument(value['instrument']);bid,ask=decimal(value.get('bid')),decimal(value.get('ask'));at=instant(value.get('timestamp'))
     if symbol not in self.instruments or not 0<bid<=ask or at>datetime.now(timezone.utc):raise AdapterError('Invalid account-scoped native tick')
     self.ticks[symbol]={'instrument':symbol,'bid':str(bid),'ask':str(ask),'event_time':at.isoformat(),'received_at':datetime.now(timezone.utc).isoformat()};self.synchronized=set(self.instruments)<=self.ticks.keys()
    elif value.get('event_type')=='trading_state_snapshot':
     validate_snapshot(value.get('payload'));self.snapshot=value['payload'];self.synchronized=True
    elif value.get('event_type')=='transaction_event':
     if not self.synchronized:raise AdapterError('Transaction before fresh subscription snapshot')
     if value.get('status') not in {'success','failed','rejected'}:raise AdapterError('Invalid transaction status')
     # Correlation evidence is retained raw, not invented from a similar snapshot position.
     key=(value.get('operation_id'),value.get('client_request_id'))
     correlated=bool(key[0] or key[1])
     if correlated and key in self.results and self.results[key]!=value:raise AdapterError('Conflicting finalized transaction identity')
     if value['status']=='success':
      payload=value.get('payload')
      if not isinstance(payload,dict):raise AdapterError('Transaction payload missing')
      for collection,id_key,terminal in [('positions','position_id',{'closed'}),('orders','order_id',{'filled','cancelled','rejected'})]:
       values={row[id_key]:row for row in self.snapshot[collection]}
       for row in payload.get(collection,[]):
        identifier(row.get(id_key))
        if row.get('state') in terminal:values.pop(row[id_key],None)
        else:values[row[id_key]]=row
       self.snapshot[collection]=list(values.values())
      if 'account_state' in payload:
       for field in ('balance','equity','used_margin'):decimal(payload['account_state'].get(field))
       self.snapshot['account_state']=payload['account_state']
     if correlated:self.results[key]=value
    callback=getattr(self,'on_message',None)
    if callback:callback(value)
    return value
  except TimeoutError:
   # A bounded recv timeout is an idle session, not a disconnect; tick age is checked by consumers.
   raise
  except Exception as e:
   disconnected=getattr(self,'on_disconnect',None)
   if disconnected:disconnected()
   self.close();self.last_error='Stream invalid/disconnected; snapshot rebuild required'
   if isinstance(e,AdapterError):raise
   raise AdapterError(self.last_error) from None
 def close(self):
  if self.socket is not None:
   try:self.socket.close()
   except Exception:pass
  self.socket=None;self.subscription_id=None;self.synchronized=False;self.snapshot=None;self.ticks={};self.results={}
