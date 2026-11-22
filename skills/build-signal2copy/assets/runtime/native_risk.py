"""Documented supported-case native policy: no fixture margin defaults or client claims."""
import copy,re,threading,time
from datetime import datetime,timezone
from decimal import Decimal,ROUND_DOWN
from urllib.parse import urlsplit,parse_qs
from .exness_adapter import AdapterError,decimal,instant,identifier
DAYS={name:n for n,name in enumerate(('Mon','Tue','Wed','Thu','Fri','Sat','Sun'))}

def require(ok,message):
    if not ok:raise AdapterError(message)
def permits_order_type(conditions, requested):
    reported = conditions.get('order_types', [])
    if not isinstance(reported, list):
        return False
    if reported:
        return requested in reported
    # Exness can omit this list. Only the immediate market path is supported without it.
    return requested == 'market'

def weekly(value):
    match=re.fullmatch(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun), ([0-2][0-9]):([0-5][0-9]):([0-5][0-9])',value or '')
    require(match is not None and int(match[2])<=23,'Unsupported weekly boundary')
    return DAYS[match[1]]*86400+int(match[2])*3600+int(match[3])*60+int(match[4])
def contains(start,end,point):
    require(start!=end,'Equal session boundaries are ambiguous')
    return start<=point<end if start<end else point>=start or point<end

def session(conditions,at):
    sessions=conditions.get('trade_sessions');require(isinstance(sessions,list) and sessions,'Trading-session boundaries unavailable')
    point=at.weekday()*86400+at.hour*3600+at.minute*60+at.second;matched=[]
    for row in sessions:
        require(isinstance(row,dict) and row.get('trade_mode') in ('enabled','trading_disabled'),'Trading session mode unavailable')
        start=weekly(row.get('week_start_time'));end=weekly(row.get('week_end_time'))
        if contains(start,end,point):matched.append(row['trade_mode'])
    require(matched and set(matched)=={'enabled'},'Trading session closed or conflicting')

def effective_leverage(configured,hmr,symbol,at):
    base=decimal(configured);require(base>=2,'Unsupported configured leverage')
    require(isinstance(hmr,dict) and isinstance(hmr.get('periods'),list),'Synchronized account HMR baseline unavailable')
    point=at.weekday()*86400+at.hour*3600+at.minute*60+at.second;result=base
    for period in hmr['periods']:
        identifier(period.get('period_id'));instruments=period.get('instruments');require(isinstance(instruments,list) and instruments,'HMR instrument set unavailable')
        if symbol not in instruments:continue
        leverage=decimal(period.get('leverage'));require(leverage>0,'Invalid HMR leverage')
        if period.get('event_type')=='regular':
            try:start=datetime.strptime(period['start_time'],'%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc);end=datetime.strptime(period['end_time'],'%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            except (KeyError,ValueError,TypeError):raise AdapterError('Unsupported absolute UTC HMR boundary') from None
            require(start<end,'Invalid HMR interval');active=start<=at<end
        elif period.get('event_type')=='periodic':active=contains(weekly(period.get('start_time')),weekly(period.get('end_time')),point)
        else:raise AdapterError('Unsupported HMR schedule type')
        if active:result=min(result,leverage)
    return result

class QuotaLedger:
    def __init__(self):self.lock=threading.RLock();self.config={};self.sent={};self.initial={}
    def configure(self,account,value):
        limits=value.get('limits');require(isinstance(limits,dict) and isinstance(limits.get('rest'),dict),'Native quota configuration unavailable')
        rest=limits['rest'];self.window(rest.get('global_account_rate'));require(isinstance(rest.get('methods'),list),'Native method quotas unavailable')
        for method in rest['methods']:require(isinstance(method,dict) and isinstance(method.get('path'),str) and method.get('http_method') in ('GET','POST','PATCH','DELETE','PUT'),'Native method quota identity unavailable');self.window(method.get('rate_limit'))
        with self.lock:self.config[account]=copy.deepcopy(limits);self.initial.setdefault(account,time.monotonic())
    def window(self,value):
        require(isinstance(value,dict) and type(value.get('limit')) is int and value['limit']>0 and type(value.get('window_seconds')) in (int,float,Decimal) and value['window_seconds']>0,'Invalid native quota window');return value['limit'],float(value['window_seconds'])
    def match(self,template,path):
        pattern=re.escape(template);pattern=re.sub(r'\\\{[^}]+\\\}',r'[^/]+',pattern);pattern=re.sub(r':[A-Za-z_]+',r'[^/]+',pattern);return re.fullmatch(pattern,path) is not None
    def check(self,account,method,path,consume=False):
        with self.lock:
            clock=time.monotonic();rows=self.sent.setdefault(account,[]);config=self.config.get(account)
            if config is None:
                require(method=='GET','Native write quota configuration unavailable')
                if consume:rows.append((clock,method,path))
                return
            rest=config['rest'];global_limit,window=self.window(rest['global_account_rate']);matches=[m for m in rest['methods'] if m['http_method']==method and self.match(m['path'],path)];max_window=max([window]+[self.window(m['rate_limit'])[1] for m in rest['methods']]);rows[:]=[r for r in rows if r[0]>=clock-max_window]
            if method!='GET':require(clock-self.initial[account]>=max_window,'Native quota warm-up preserves unknown pre-restart capacity');require(len(matches)==1,'Exact native write method quota unavailable')
            require(sum(r[0]>clock-window for r in rows)<global_limit,'Native account REST quota waiting')
            if len(matches)==1:
                limit,period=self.window(matches[0]['rate_limit']);require(sum(r[0]>clock-period and r[1]==method and self.match(matches[0]['path'],r[2]) for r in rows)<limit,'Native operation REST quota waiting')
            if consume:rows.append((clock,method,path))
    def websocket(self,account):
        with self.lock:
            config=self.config.get(account,{}).get('websocket',{});global_limits=config.get('global_account_limits',{});require(type(global_limits.get('max_active_connections')) is int and global_limits['max_active_connections']>=5,'This managed-stream implementation requires five documented account connections')
            require(type(global_limits.get('max_inbound_message_bytes')) is int and global_limits['max_inbound_message_bytes']>=512,'Native inbound message budget unavailable')
            for key in ('connection_rate','inbound_message_rate'):
                item=global_limits.get(key,{});self.window(item);require(type(item.get('burst')) is int and item['burst']>=5,'Native account stream burst capacity unavailable')
            require(isinstance(config.get('endpoints'),list) and config['endpoints'],'Native stream endpoint quotas unavailable')


    def bucket(self,key,config,consume):
        limit,window=self.window(config);burst=config.get('burst');require(type(burst) is int and burst>0,'Native token bucket burst unavailable');clock=time.monotonic();buckets=getattr(self,'buckets',None)
        if buckets is None:self.buckets={};buckets=self.buckets
        tokens,at=buckets.get(key,(Decimal(burst),clock));tokens=min(Decimal(burst),tokens+Decimal(str(clock-at))*Decimal(limit)/Decimal(str(window)));require(tokens>=1,'Native stream quota waiting')
        buckets[key]=(tokens-(1 if consume else 0),clock)
    def ws_endpoint(self,account,path):
        config=self.config.get(account,{}).get('websocket',{});global_limits=config.get('global_account_limits');require(isinstance(global_limits,dict),'Native account stream limits unavailable');matches=[e for e in config.get('endpoints',[]) if self.match(e.get('path',''),path)];require(len(matches)==1,'Native stream endpoint quota unavailable');return global_limits,matches[0]
    def ws_open(self,account,path):
        with self.lock:
            self.websocket(account);global_limits,endpoint=self.ws_endpoint(account,path);active=getattr(self,'active',None)
            if active is None:self.active={};active=self.active
            require(active.get(account,0)<global_limits['max_active_connections'],'Native active connection cap reached')
            for label,limits in (('global',global_limits),('endpoint:'+path,endpoint)):self.bucket((account,label,'connect'),limits['connection_rate'],False)
            for label,limits in (('global',global_limits),('endpoint:'+path,endpoint)):self.bucket((account,label,'connect'),limits['connection_rate'],True)
            active[account]=active.get(account,0)+1

    def ws_close(self,account):
        with self.lock:
            if hasattr(self,'active'):self.active[account]=max(0,self.active.get(account,0)-1)
    def ws_send(self,account,path,text):
        import json
        with self.lock:
            global_limits,endpoint=self.ws_endpoint(account,path);require(len(text.encode())<=global_limits['max_inbound_message_bytes'],'Native subscription exceeds message limit');message=json.loads(text)
            configs=[((account,'global','inbound'),global_limits['inbound_message_rate']),((account,'endpoint:'+path,'inbound'),endpoint['inbound_message_rate'])]
            if isinstance(message.get('subscribe'),dict):
                event=message['subscribe'].get('event');limit=endpoint.get('subscription_operation_rate',{}).get(event);require(isinstance(limit,dict),'Native subscription operation quota unavailable');configs.append(((account,path,'subscribe:'+event),limit))
            for key,config in configs:self.bucket(key,config,False)
            for key,config in configs:self.bucket(key,config,True)

class SupportedPolicy:
    """Actual mandatory policy for supported fresh observations; no unconditional success flag."""
    simulation=False
    def stage(self):return True
    def evaluate(self,app,sub,source,target,source_state,target_state,signal,conditions,kind='open'):
        now=datetime.now(timezone.utc);entry=kind=='open'
        require(not app.state['frozen'] and not app.store.failed,'Owner or durability fence is closed')
        require(source.get('connected') and target.get('connected'),'Canonical account connection consent missing')
        consent=sub.get('consent') if entry or sub['status'] not in ('stopping','stopped') else sub.get('stop_consent') or sub.get('consent')
        require(isinstance(consent,dict) and consent.get('account')==target['id'] and consent.get('strategy')==sub['strategy'] and isinstance(consent.get('at'),str),'Bound explicit native trade/management consent missing')
        require(instant(consent['at'])<=now,'Native consent time is invalid')
        if entry:require(consent.get('scope_confirmed') is True,'Native initial scope consent missing')
        require(source['id']==app.state['strategies'][sub['strategy']]['source'] and target['id']==sub['account'],'Canonical strategy/account binding changed')
        if entry:require(sub['status']=='active' and app.state['strategies'][sub['strategy']]['published'],'Entry intent/publication does not authorize this effect')
        for account,state in ((source,source_state),(target,target_state)):
            require(account['id'] not in app.broker.quota_errors,'Native quota configuration malformed/stale')
            require(state.get('epoch')==account.get('epoch') and state.get('transactions_synchronized') and state.get('snapshot') is not None,'Native account transaction epoch is not synchronized')
            require(all(state.get('streams',{}).get(e,{}).get('connected') for e in ('transactions','ticks','account_state','instruments','hmr')),'Native stream connection unavailable')
            require(state.get('hmr_baseline') is True,'Native HMR baseline unavailable')
            require((now-instant(account['observation']['checked_at'])).total_seconds()<=30,'Native account configuration is stale')
            settings=account['observation']['details']['settings'];require(settings.get('trade_mode')=='enabled','Native account trading disabled');require(settings.get('account_status')=='active' or not entry and settings.get('account_status')=='close_only','Native account operation is restricted')
            snapshot=state['snapshot'];require(decimal(snapshot['account_state']['used_margin'])>=0,'Native used margin unavailable');decimal(snapshot['account_state']['equity'])
            if entry:require(decimal(snapshot['account_state']['equity'])>0,'Native entry equity must be positive')
        require(conditions.get('instrument')==signal['instrument'] and conditions.get('trade_mode')=='enabled','Native instrument identity/permission unavailable');session(conditions,now)
        if entry:
            require(target['observation']['details']['settings'].get('execution_mode')=='market' and conditions.get('exec_mode')=='market','Only documented native market execution mode is currently supported')
            requested = 'market' if signal.get('position_id') and not signal.get('order_type') else signal.get('order_type')
            require(permits_order_type(conditions, requested), 'Native entry order type is not permitted')
        tick=target_state.get('ticks',{}).get(signal['instrument']);require(tick is not None,'Native traded-symbol tick missing');age=(now-instant(tick['event_time'])).total_seconds();require(0<=age<=5 and 0<decimal(tick['bid'])<=decimal(tick['ask']),'Native original executable tick stale/future/invalid')
        require(type(conditions.get('point_digits')) is int and 0<=conditions['point_digits']<=12,'Native price precision unavailable')
        app.broker.quota.websocket(target['id']);app.broker.quota.websocket(source['id'])
        return {'tick':tick,'at':now.isoformat(),'source_version':source_state['transaction_version'],'target_version':target_state['transaction_version'],'supported_policy_passed':True}
    def authorize(self,*args,**kwargs):
        evidence=self.evaluate(*args,**kwargs);require(self.stage(),'Staging policy: production native writes remain disabled pending assembled acceptance');return evidence

class StagedPolicy(SupportedPolicy):
    def stage(self):return False
