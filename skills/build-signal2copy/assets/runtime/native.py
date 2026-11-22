"""Native signed reads/managed synchronization. Only the journaled engine authorizes writes."""
import copy,hashlib,json,secrets,threading,time
from datetime import datetime,timezone,timedelta
from decimal import Decimal
from urllib.parse import urlencode,urlsplit,parse_qs
from cryptography.hazmat.primitives import serialization
from .exness_adapter import ExnessAdapter,AdapterError,https_send,origin,identifier,instrument,decimal,instant
from .exness_signing import headers,load_key
from .native_risk import QuotaLedger


def now():return datetime.now(timezone.utc).isoformat()
def identity(api_key,private):
    key=load_key(private);public=key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    return hashlib.sha256(api_key.encode()+b'\0'+public).hexdigest()

class Partnership:
    def __init__(self,base,api_key,private,send=https_send):
        self.base=origin(base);self.api_key=api_key;self.key=load_key(private);self.send=send;self.blocked_until=0
    def get(self,path):
        if time.monotonic()<self.blocked_until:raise AdapterError('Partnership request capacity cooling down',429)
        signed=headers(self.api_key,self.key,'GET',path);signed.pop('EXN-IDEMPOTENCY-KEY',None)
        status,value,response_headers=self.send('GET',self.base+path,signed,b'')
        if status==429:
            retry=next((v for k,v in response_headers.items() if k.lower()=='retry-after'),'60')
            try:delay=max(1,min(float(retry),3600))
            except (ValueError,TypeError):delay=60
            self.blocked_until=time.monotonic()+delay
        if status!=200:raise AdapterError('Partnership read failed (HTTP '+str(status)+')',status,value.get('code') if isinstance(value,dict) else None)
        if not isinstance(value,dict):raise AdapterError('Malformed Partnership success response')
        return value
    def verify(self):
        value=self.get('/v1/partnership/partner/default-link')
        if not all(isinstance(value.get(k),str) and value[k] for k in ('full_default_link','domain','code','path','url')):raise AdapterError('Malformed default-link capability response')
        for field in ('full_default_link','url'):
            u=urlsplit(value[field])
            if u.scheme!='https' or not u.hostname or u.username or u.password:raise AdapterError('Malformed default-link URL')
        return {'verified':True,'checked_at':now()}
    def verify_report_access(self):
        value=self.get('/v1/partnership/reports/clients/accounts?'+urlencode({'limit':1,'offset':0,'ordering':'client_account'}))
        if not isinstance(value.get('data'),list) or len(value['data'])>1 or type(value.get('totals',{}).get('count')) is not int or value['totals']['count']<len(value['data']):raise AdapterError('Malformed Partnership report-access response')
        for row in value['data']:
            if not isinstance(row,dict):raise AdapterError('Malformed Partnership report-access row')
            identifier(row.get('client_account'))
        return True
    def account_report(self,selected):
        identifier(selected);pages=[];offset=0;limit=200;total=None
        for _ in range(20):
            query={'client_account':[selected],'limit':limit,'offset':offset,'ordering':'client_account'}
            value=self.get('/v1/partnership/reports/clients/accounts?'+urlencode(query,doseq=True));rows=value.get('data');count=value.get('totals',{}).get('count')
            if not isinstance(rows,list) or type(count) is not int or count<0 or len(rows)>limit or count<offset+len(rows) or total is not None and total!=count:raise AdapterError('Malformed or changing exact-account report')
            if any(not isinstance(row,dict) or row.get('client_account')!=selected for row in rows):raise AdapterError('Partnership report did not honor selected-account filter')
            pages.append({'successful':True,'provider_id':'provider','checked_at':now(),'query':query,'rows':[{'client_account':r['client_account']} for r in rows],'totals':{'count':count}})
            total=count
            if offset+len(rows)>=count:return pages
            if len(rows)!=limit:raise AdapterError('Truncated exact-account report')
            offset+=limit
        raise AdapterError('Exact-account report page bound exceeded')

class NativeBroker:
    """Facade matches the application read surface only. No fixture fallback or native writes."""
    def __init__(self,gateway,partnership,send=https_send,connect=None):
        self.gateway=origin(gateway);self.partnership=origin(partnership);self.transport=send;self.send=self.send_checked;self.connector=connect;self.connect=self.connect_checked;self.clients={};self.partners={};self.runtime={};self.lock=threading.RLock();self.quota=QuotaLedger();self.quota_errors={}
    def partner(self,key,private):
        canonical=identity(key,private)
        if canonical not in self.partners:self.partners[canonical]=Partnership(self.partnership,key,private,self.transport)
        return self.partners[canonical]
    def send_checked(self,method,url,signed,body):
        import re
        u=urlsplit(url);match=re.search(r'/accounts/([0-9]+)(?:/|$)',u.path);account=match[1] if match else None
        if u.path=='/v1/trading/access-point':account=parse_qs(u.query).get('account_id',[None])[0]
        if account:
            try:self.quota.check(account,method,u.path,consume=True)
            except AdapterError as error:raise AdapterError(str(error),429,'LOCAL_QUOTA_NOT_SENT') from None
        result=self.transport(method,url,signed,body)
        if account and u.path.endswith('/limits') and result[0]==200:
            try:self.quota.configure(account,result[1]);self.quota_errors.pop(account,None)
            except AdapterError as error:self.quota_errors[account]=str(error)
        return result
    def connect_checked(self,url,**kwargs):
        import re
        u=urlsplit(url);match=re.search(r'/accounts/([0-9]+)/',u.path);require_account=match[1] if match else None
        if not require_account:raise AdapterError('Native stream account binding missing')
        self.quota.ws_open(require_account,u.path)
        try:
            if self.connector:socket=self.connector(url,**kwargs)
            else:
                from websockets.sync.client import connect
                socket=connect(url,**kwargs)
            return QuotaSocket(socket,self.quota,require_account,u.path)
        except Exception:self.quota.ws_close(require_account);raise
    def client(self,a):
        key=(a['id'],identity(a['key'],a['private']))
        if key not in self.clients:self.clients[key]=ExnessAdapter(self.gateway,a['key'],a['private'],self.send,allow_writes=False)
        return self.clients[key]
    def observe(self,a):
        client=self.client(a);details=client.account(a['id']);snapshot=client.snapshot(a['id']);limits=client.limits(a['id']);inventory=client.instruments(a['id']);symbols=inventory.get('instruments')
        if not isinstance(symbols,list) or any(not isinstance(s,str) for s in symbols):raise AdapterError('Native instrument inventory unavailable')
        for k in ('balance','equity','used_margin'):decimal(snapshot['account_state'].get(k))
        return {'details':details,'snapshot':snapshot,'history':{'items':[],'coverage':'Not read; use explicit Read history','complete':False},'limits':limits,'inventory':symbols,'checked_at':now(),'native':True}
    def read(self,a,resource):
        client=self.client(a);account=a['id'];base=resource.split('?',1)[0]
        if base=='details':return client.account(account)
        if base=='snapshot':return client.snapshot(account)
        if base=='limits':return client.limits(account)
        if base=='instruments':return client.instruments(account)
        if base.startswith('instruments/'):
            symbol=instrument(base.split('/',1)[1]);value=client.conditions(account,symbol)
            if value.get('instrument')!=symbol:raise AdapterError('Native condition instrument mismatch')
            low,step,high=(decimal(value.get(k)) for k in ('volume_min','volume_step','volume_max'))
            if not 0<low<=high or step<=0:raise AdapterError('Native volume conditions unavailable')
            return value
        if base.startswith('quotes/'):
            symbol=base.split('/',1)[1];runtime=self.runtime.get(account);tick=runtime.safe()['ticks'].get(symbol) if runtime else None
            if not tick:raise AdapterError('Native original-time tick synchronization unavailable')
            return tick
        if base in ('history','history/deals'):raise AdapterError('Native history requires an explicit bounded interval via Read history')
        raise AdapterError('Unsupported native read resource')
    def request(self,*args,**kwargs):raise AdapterError('Native writes disabled; complete execution/RMS/recovery acceptance required')
    def history(self,a,start,end):return self.client(a).history(a['id'],'deals',start,end,limit=200,max_pages=100)
    def entry_history(self, account, start, end):
        client = self.client(account)
        return {
            kind: client.history(account['id'], kind, start, end, limit=20, max_pages=1)['items']
            for kind in ('deals', 'orders')
        }
    def fill_history(self,a,start,end):
        # A small recovery read, not an unbounded scan or a retention guarantee.
        client=self.client(a);limits=client.limits(a['id']);begin=instant(start);finish=instant(end);present=datetime.now(timezone.utc)
        methods=limits.get('limits',{}).get('rest',{}).get('methods',[])
        entries=[m for m in methods if m.get('api_operation_id')=='getDealsHistory' and m.get('http_method')=='GET' and m.get('path')=='/v1/history/accounts/{account_id}/deals']
        if len(entries)!=1:raise AdapterError('Recovery deal-history limits unavailable')
        bounds=entries[0].get('limits',{});age=decimal(bounds.get('history_age_days'));span=decimal(bounds.get('history_range_days'))
        if not age>0 or not span>0 or not begin<finish<=present or Decimal(str((present-begin).total_seconds()))>age*86400 or Decimal(str((finish-begin).total_seconds()))>span*86400:raise AdapterError('Recovery interval exceeds returned deal-history limits')
        history=client.history(a['id'],'deals',start,end,limit=200,max_pages=4)
        if history.get('pagination_complete') is not True:raise AdapterError('Recovery history pagination incomplete')
        previous=None
        for row in history['items']:
            at=instant(row.get('event_time'))
            if not begin<=at<finish or previous is not None and at<previous or not isinstance(row.get('deal'),dict):raise AdapterError('Recovery history range/order/record invalid')
            previous=at
        return history
    def sync(self,a,symbols):
        with self.lock:
            # Restored accounts have observations, but this process has no quota ledger.
            # Authenticate a fresh limits read; invalid new evidence must not reuse stale limits.
            client=self.client(a);limits=client.limits(a['id']);self.quota.configure(a['id'],limits);self.quota.websocket(a['id'])
            if a['id'] in self.runtime:self.runtime[a['id']].close()
            runtime=ManagedStreams(client,a['id'],symbols,a.get('epoch',0),self.connect);self.runtime[a['id']]=runtime;runtime.start();return runtime.safe()
    def close_account(self,account):
        with self.lock:
            if account in self.runtime:self.runtime.pop(account).close()
            for key in list(self.clients):
                if key[0]==account:self.clients.pop(key)
    def sync_status(self,a):
        runtime=self.runtime.get(a['id']);return runtime.safe() if runtime else {'account':a['id'],'epoch':a.get('epoch',0),'transactions_synchronized':False,'execution_enabled':False,'reason':'Read streams have not been started'}

class QuotaSocket:
    def __init__(self,socket,quota,account,path):self.socket=socket;self.quota=quota;self.account=account;self.path=path;self.closed=False
    def send(self,text):self.quota.ws_send(self.account,self.path,text);return self.socket.send(text)
    def recv(self,**kwargs):return self.socket.recv(**kwargs)
    def close(self):
        if self.closed:return
        self.closed=True
        try:self.socket.close()
        finally:self.quota.ws_close(self.account)

class ManagedStreams:
    """Epoch fenced workers. Quiet timeout preserves a session; no durable replay claim."""
    def __init__(self,client,account,symbols,epoch,connect=None):
        self.client=client;self.account=account;self.symbols=[instrument(s) for s in symbols];self.epoch=epoch;self.connect=connect;self.stop=threading.Event();self.lock=threading.RLock();self.streams={};self.status={};self.hmr={};self.hmr_baseline=False;self.account_state=None;self.conditions={};self.version=0;self.events=[];self.hmr_periods={};self.generations={'_runtime':secrets.token_hex(16)}
    def start(self):
        for event in ('transactions','ticks','account_state','instruments','hmr'):threading.Thread(target=self.worker,args=(event,self.epoch),daemon=True).start()
    def worker(self,event,epoch):
        backoff=1
        while not self.stop.is_set():
            stream=None
            try:
                stream=self.client.stream(self.account,event,self.symbols if event!='transactions' and event!='account_state' else None,self.connect);stream.state_lock=self.lock;stream.on_message=lambda value,current=stream:self.accept(event,epoch,value,current);stream.on_disconnect=lambda current=stream:self.disconnected(event,epoch,current)
                with self.lock:
                    if self.stop.is_set() or self.epoch!=epoch:stream.close();return
                    # Invalidate the old binding before discovery/open can block.
                    self.streams[event]=stream;self.generations[event]=self.generations.get(event,0)+1;self.status[event]={'connected':False,'at':now(),'error':'Waiting for a fresh connection and baseline'}
                stream.open()
                with self.lock:
                    if self.stop.is_set() or self.epoch!=epoch:stream.close();return
                    self.status[event]={'connected':True,'at':now(),'error':None}
                while not self.stop.is_set():
                    try:stream.receive(timeout=.1);backoff=1
                    except TimeoutError:continue
            except Exception:
                self.disconnected(event,epoch,stream)
            finally:
                if stream:stream.close()
            self.stop.wait(backoff);backoff=min(30,backoff*2)
    def accept(self,event,epoch,value,stream):
        if self.epoch!=epoch or self.stop.is_set() or self.streams.get(event) is not stream:raise AdapterError('Stale native stream session or epoch')
        self.apply(event,value);self.status[event]={'connected':True,'at':now(),'error':None}
    def disconnected(self,event,epoch,stream):
        with self.lock:
            if self.epoch==epoch and not self.stop.is_set() and self.streams.get(event) is stream:
                self.streams.pop(event,None);self.generations[event]=self.generations.get(event,0)+1
                self.status[event]={'connected':False,'at':now(),'error':'Native stream lost; fresh baseline required'}
                if event=='hmr':self.hmr_baseline=False;self.hmr={};self.hmr_periods={}
                if event=='account_state':self.account_state=None
                if event=='instruments':self.conditions={}
    def apply(self,event,value):
        kind=value.get('event_type');payload=value.get('payload')
        if event=='transactions' and kind in ('trading_state_snapshot','transaction_event'):
            self.version+=1
            if kind=='transaction_event':self.events.append(copy.deepcopy(value));self.events=self.events[-4096:]
        if event=='account_state' and kind=='account_state_event':
            if not isinstance(payload,dict):raise AdapterError('Native floating state payload missing')
            state=payload.get('account_state')
            if not isinstance(state,dict):raise AdapterError('Native account_state structure missing')
            for name in ('balance','equity','used_margin'):decimal(state.get(name))
            self.account_state={'values':copy.deepcopy(state),'event_time':value.get('event_time'),'received_at':now()}
        elif event=='instruments' and kind=='instrument_event':
            if not isinstance(payload,dict) or payload.get('instrument') not in self.symbols:raise AdapterError('Native instrument update unavailable')
            if value.get('action')=='del':self.conditions.pop(payload['instrument'],None)
            elif value.get('action') in ('new','upd'):self.conditions[payload['instrument']]=copy.deepcopy(payload)
            else:raise AdapterError('Native instrument lifecycle action missing')
        elif event=='hmr' and kind in ('hmr_snapshot','hmr_update'):
            periods=value.get('periods') if kind=='hmr_snapshot' else value.get('upserted_periods');removed=[] if kind=='hmr_snapshot' else value.get('removed_period_ids')
            if not isinstance(periods,list) or not isinstance(removed,list) or kind=='hmr_update' and not self.hmr_baseline:raise AdapterError('Native HMR baseline/update structure missing')
            parsed={}
            for period in periods:
                if not isinstance(period,dict) or period.get('event_type') not in ('regular','periodic') or not isinstance(period.get('instruments'),list) or not period['instruments']:raise AdapterError('Native HMR period unavailable')
                identifier(period.get('period_id'))
                if decimal(period.get('leverage'))<=0 or not isinstance(period.get('start_time'),str) or not isinstance(period.get('end_time'),str):raise AdapterError('Native HMR period limits unavailable')
                parsed[period['period_id']]=copy.deepcopy(period)
            if kind=='hmr_snapshot':self.hmr_periods=parsed
            else:
                self.hmr_periods.update(parsed)
                for period_id in removed:identifier(period_id);self.hmr_periods.pop(period_id,None)
            self.hmr={'periods':copy.deepcopy(list(self.hmr_periods.values())),'received_at':now()};self.hmr_baseline=True
    def safe(self):
        with self.lock:
            transactions=self.streams.get('transactions');ticks=self.streams.get('ticks');connected=all(self.status.get(e,{}).get('connected') for e in ('transactions','ticks','account_state','instruments','hmr'))
            return {'account':self.account,'epoch':self.epoch,'streams':copy.deepcopy(self.status),'generations':copy.deepcopy(self.generations),'transactions_synchronized':bool(transactions and transactions.synchronized),'transaction_version':self.version,'snapshot':copy.deepcopy(transactions.snapshot) if transactions and transactions.synchronized else None,'events':copy.deepcopy(self.events),'ticks':copy.deepcopy(ticks.ticks) if ticks else {},'account_state':copy.deepcopy(self.account_state),'condition_updates':copy.deepcopy(self.conditions),'hmr_baseline':self.hmr_baseline,'hmr':copy.deepcopy(self.hmr),'streams_connected':connected,'execution_enabled':False,'reason':'Native reads/streams do not authorize production orders; full RMS, sessions, exact ownership/recovery and dispatch acceptance remain required'}
    def close(self):
        self.stop.set()
        with self.lock:
            self.epoch+=1
            for stream in self.streams.values():stream.close()
            self.streams.clear();self.status.clear();self.hmr_baseline=False
