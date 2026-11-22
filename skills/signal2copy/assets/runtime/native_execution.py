"""Unattended native-shaped execution with supported-case policy and shared durable app journal.
Read-only installations use StagedPolicy; explicitly configured new native-execution
installations use SupportedPolicy. Mode selection never skips per-effect gates.
"""
import copy,hashlib,json,secrets,time
from datetime import datetime,timedelta,timezone
from decimal import Decimal,ROUND_DOWN
from urllib.parse import urlsplit,parse_qs,urlencode
from .exness_adapter import ExnessAdapter,AdapterError,decimal,identifier,instant
from .native_risk import StagedPolicy,SupportedPolicy,effective_leverage,require
from .host import validate_host

def now():return datetime.now(timezone.utc).isoformat()
def token():return secrets.token_hex(16)
def price_equal(left,right):return left is right if left is None or right is None else decimal(left)==decimal(right)
def same_source_entity(before, after, kind):
    if before is None or after is None:
        return before is after
    identity = ('position_id',) if kind == 'position' else ('order_id', 'order_type')
    fields = (*identity, 'instrument', 'direction', 'state')
    if any(before.get(field) is None or before[field] != after.get(field) for field in fields):
        return False
    if instant(before.get('create_time')) != instant(after.get('create_time')):
        return False
    if decimal(before.get('volume')) != decimal(after.get('volume')):
        return False
    if kind == 'order':
        return (decimal(before.get('price')) == decimal(after.get('price'))
                and before.get('position_id') == after.get('position_id'))
    return all(
        before.get(field) is None or after.get(field) is None or price_equal(before[field], after[field])
        for field in ('initial_volume', 'open_price')
    )

class AppJournal:
    def __init__(self,engine):self.engine=engine
    def reserve(self,account,key,fingerprint):
        app=self.engine.app;require(not app.state['frozen'] and not app.store.failed,'Native journal fenced');c=app.state['commands'].get(key);require(c is not None and c['account']==account and c['status']=='prepared','Native request is already reserved or mismatched');require(c['fingerprint']==fingerprint,'Native immutable request fingerprint mismatch');c['status']='unknown';c['dispatch_at']=now();app.save('Native durable request reservation acknowledged')
    def update(self,account,key,status,operation=None):
        app=self.engine.app;c=app.state['commands'][key];require(c['account']==account,'Native result account mismatch');require(not operation or not c.get('operation') or c['operation']==operation,'Native operation rebinding rejected')
        if operation:c['operation']=operation
        before=(c.get('operation_status'),c['status'],c.get('operation'));c['operation_status']=status
        if status in ('pending','unknown'):c['status']='accepted' if operation else 'unknown'
        elif status=='not_sent':c['status']='not_sent'
        elif status in ('rejected','failed'):c['status']='rejected'
        # Operation confirmed alone never proves position/order ownership.
        if before!=(c.get('operation_status'),c['status'],c.get('operation')):app.save('Native exact journal result retained')
    def get(self,account,key):
        c=self.engine.app.state['commands'].get(key)
        if c is None or c['account']!=account:return None
        return {'fingerprint':c['fingerprint'],'status':c['status'],'operation_id':c.get('operation')}
class NativeEngine:
    def __init__(self,app,policy=None):
        validate_host(app)
        self.app=app;self.policy=policy or (SupportedPolicy() if app.mode=='native-execution' else StagedPolicy());self.journal=AppJournal(self);self.last_refresh={};self.adapters={}
        changed=False
        for sub in app.state['subscriptions'].values():
            if sub.get('native') and sub['status']=='active':
                sub['status']='paused';sub['initial_eligible']=[];sub['restart_hold']='Fresh native synchronization and explicit Resume required'
                for mapping in sub['mappings'].values():
                    if mapping['status']=='waiting':mapping['status']='cancelled_before_dispatch'
                changed=True
        if changed:app.save('Native restart retains owned management and explicit Pause')
    def frame(self,a):
        state=self.app.broker.sync_status(a);require(state.get('transactions_synchronized') and state.get('snapshot') is not None and state.get('epoch')==a['epoch'],'Fresh native transaction baseline required')
        require(isinstance(state.get('generations'),dict) and isinstance(state['generations'].get('_runtime'),str) and bool(state['generations']['_runtime']),'Native stream runtime identity missing')
        floating=state.get('account_state');require(isinstance(floating,dict) and 0<=(datetime.now(timezone.utc)-instant(floating.get('event_time'))).total_seconds()<=5,'Fresh native floating account state required');state['snapshot']['account_state']=copy.deepcopy(floating['values']);return state
    def refresh(self,a,force=False):
        if force or time.monotonic()-self.last_refresh.get(a['id'],0)>20:a['observation']=self.app.broker.observe(a);self.last_refresh[a['id']]=time.monotonic()
    def adapter(self,a):
        key=(a['id'],a['epoch'])
        if key not in self.adapters:self.adapters[key]=ExnessAdapter(self.app.broker.gateway,a['key'],a['private'],self.app.broker.send,allow_writes=True,journal=self.journal)
        return self.adapters[key]
    def start(self,session,b):
        require(self.policy.stage(),'Native production execution is disabled pending assembled supported-policy acceptance');app=self.app;require(session['role']=='investor' and b.get('confirmed') is True and b.get('scope_confirmed') is True,'Explicit native investor Start and initial scope confirmation required');account=session['identity'];require(not any(s['account']==account and s['status']!='stopped' for s in app.state['subscriptions'].values()),'Existing unfinished Subscription reserves this account');strategy=app.state['strategies'][b['strategy']];require(strategy['published'],'Strategy unpublished');source=app.account(strategy['source']);target=app.account(account);self.refresh(source,True);self.refresh(target,True);app.admission(target,source);sf=self.frame(source);tf=self.frame(target)
        for state in (sf,tf):require(state.get('hmr_baseline') and all(state.get('streams',{}).get(event,{}).get('connected') for event in ('transactions','ticks','account_state','instruments','hmr')),'Complete native read baselines required before Start')
        scope=b.get('scope','new');require(scope in ('new','current'),'Unknown initial native scope');settings=app.settings(b,decimal(tf['snapshot']['account_state']['equity']));sub={'id':token(),'strategy':strategy['id'],'account':account,'owner':account,'native':True,'sync_generations':{source['id']:copy.deepcopy(sf['generations']),target['id']:copy.deepcopy(tf['generations'])},'consent':{'account':account,'strategy':strategy['id'],'scope_confirmed':True,'at':now()},'status':'active','created_at':now(),'revision':0,'scope':scope,'activation_budget':str(min(decimal(tf['snapshot']['account_state']['equity']),Decimal('10000')).quantize(Decimal('.01'),rounding=ROUND_DOWN)),'seen':[] if scope=='current' else app.signal_ids(sf['snapshot']),'initial_eligible':app.signal_ids(sf['snapshot']) if scope=='current' else [],'baseline_orders':{o['order_id']:copy.deepcopy(o) for o in sf['snapshot']['orders'] if o.get('order_type') in ('limit','stop')},'mappings':{},'controls':dict.fromkeys(('max_entry_deviation_pct','max_trade_volume','max_positions','daily_loss_pct','max_signal_age_seconds'),None),'daily_auto_close':False,'daily':{},'reviews':[],**settings};app.state['subscriptions'][sub['id']]=sub;app.save('Native explicit subscription intent and activation boundary retained');return sub
    def lifecycle(self,sub,b):
        action=b.get('action');require(action in ('pause','resume','stop') and b.get('confirmed') is True,'Explicit native lifecycle confirmation required')
        if action=='resume':
            require(sub['status']=='paused' and self.policy.stage(),'Native Resume is unavailable');source=self.app.account(self.app.state['strategies'][sub['strategy']]['source']);target=self.app.account(sub['account']);self.refresh(source,True);self.refresh(target,True);self.app.admission(target,source);sf=self.frame(source);tf=self.frame(target);sub['sync_generations']={source['id']:copy.deepcopy(sf['generations']),target['id']:copy.deepcopy(tf['generations'])};require(self.app.state['strategies'][sub['strategy']]['published'],'Strategy unpublished');sub['seen']=list(set(sub['seen']+self.app.signal_ids(sf['snapshot'])));sub['baseline_orders'].update({o['order_id']:copy.deepcopy(o) for o in sf['snapshot']['orders'] if o.get('order_type') in ('limit','stop')});sub['status']='active';sub['consent']={'account':sub['account'],'strategy':sub['strategy'],'scope_confirmed':True,'at':now()};sub['resume_consent']={'at':now(),'revision':sub['revision']};sub.pop('restart_hold',None)
        elif action=='pause':
            require(sub['status']=='active','Only Active native subscriptions can Pause');sub['status']='paused';sub['initial_eligible']=[]
            for m in sub['mappings'].values():
                if m['status']=='waiting':m['status']='cancelled_before_dispatch'
        else:sub['status']='stopping';sub['stop_deadline']=time.time()+10;sub['stop_consent']={'account':sub['account'],'strategy':sub['strategy'],'at':now()}
        sub['revision']+=1;self.app.save('Native desired '+action+' persisted');return sub
    def condition(self,source,target,symbol):
        sc=self.app.broker.read(source,'instruments/'+symbol);tc=self.app.broker.read(target,'instruments/'+symbol)
        for key in ('instrument','base_currency','quote_currency','margin_currency','calc_mode','contract_size'):require(sc.get(key) is not None and sc[key]==tc.get(key),'Native contract mismatch or missing '+key)
        require(tc.get('calc_mode') in ('forex','forex_no_leverage','cfd','cfd_leverage'),'Unsupported native calculation mode');return tc
    def margin(self,target,tf,conditions,lots,side,price):
        rate,route=self.app.fx(target,conditions['margin_currency'],target['observation']['details']['settings']['currency'],purchase=True);mode=conditions['calc_mode'];contract=decimal(conditions['contract_size']);require(contract>0,'Native contract size must be positive')
        if mode in ('forex','cfd_leverage'):fraction=1/effective_leverage(target['observation']['details']['settings']['leverage'],tf['hmr'],conditions['instrument'],datetime.now(timezone.utc))
        else:fraction=decimal(conditions.get('margin_percent'));require(0<fraction<=1,'Native fixed margin fraction unavailable/unsupported')
        amount=lots*contract*rate*fraction
        if mode in ('cfd','cfd_leverage'):amount*=decimal(price)
        return amount,route
    def size(self,sub,signal,source,target,sf,tf,conditions,exclude=None):
        eq = decimal(sf['snapshot']['account_state']['equity'])
        require(eq > 0, 'Native source equity must be positive')
        lots = decimal(signal['volume'])
        rate, route = None, []
        if sub['mode'] == 'proportional':
            require(0 < decimal(sub['amount']) <= decimal(tf['snapshot']['account_state']['equity']), 'Native allocation exceeds current investor equity')
            rate, route = self.app.fx(target, target['observation']['details']['settings']['currency'], source['observation']['details']['settings']['currency'])
            raw = lots * decimal(sub['amount']) * rate / eq * decimal(sub['multiplier'])
        else:
            raw = lots
        step=decimal(conditions['volume_step']);low=decimal(conditions['volume_min']);high=decimal(conditions['volume_max']);require(0<low<=high and step>0 and low%step==0,'Native lot grid unavailable or unsupported');rounded=raw if sub['mode']=='one_to_one' else (raw/step).to_integral_value(rounding=ROUND_DOWN)*step;require(low<=rounded<=high and rounded%step==0,'Skipped: native requested lots incompatible with broker min/step/max')
        q=tf['ticks'][signal['instrument']];price=signal.get('price') or q['ask' if signal['direction']=='buy' else 'bid'];margin,margin_route=self.margin(target,tf,conditions,rounded,signal['direction'],price);reserve=Decimal(0)
        for old in self.app.state['subscriptions'].values():
            if old['account']!=sub['account']:continue
            for mapping in old['mappings'].values():
                if (old['id'],mapping['id'])==exclude:continue
                if not any(c['subscription']==old['id'] and c['mapping']==mapping['id'] and c['kind']=='open' and c['status'] in ('prepared','intent','accepted','unknown') for c in self.app.state['commands'].values()):continue
                require(mapping['source']['instrument']==signal['instrument'] and mapping.get('contract')=={k:conditions.get(k) for k in ('base_currency','quote_currency','margin_currency','calc_mode','contract_size')},'Unknown native entry risk cannot be bounded by this instrument/contract');current,_=self.margin(target,tf,conditions,decimal(mapping['requested_lots']),mapping['source']['direction'],price);reserve+=max(decimal(mapping['margin']),current)
        free=decimal(tf['snapshot']['account_state']['equity'])-decimal(tf['snapshot']['account_state']['used_margin']);require(margin+reserve<=free,'Native free margin cannot cover entry and uncertain reservations');return rounded,{'source_equity':str(eq),'fx_rate':str(rate) if rate is not None else None,'fx_route':route,'raw_lots':str(raw),'rounded_lots':str(rounded),'margin':str(margin),'uncertain_margin':str(reserve),'margin_fx_route':margin_route,'quote':q,'at':now()}
    def protection(self,snapshot,signal):
        related=[o for o in snapshot['orders'] if signal.get('position_id') is not None and o.get('order_type')=='sltp' and o.get('position_id')==signal.get('position_id')]
        require(len(related)<=1,'Ambiguous native source protection');values={k:(related[0].get(k) if related else signal.get(k)) for k in ('stop_loss_price','take_profit_price')}
        if related:
            require(related[0].get('state')=='placed','Native source protection is unresolved')
            for key in values:
                if key in signal:require(price_equal(signal[key],values[key]),'Native source position/order protection contradicts')
        return values
    def price_fields(self,body,conditions):
        digits=conditions['point_digits']
        for field in ('price','stop_loss_price','take_profit_price'):
            if body.get(field) is None:continue
            value=body[field];require(isinstance(value,str) and decimal(value)>0,'Native positive price string required');quantum=Decimal(1).scaleb(-digits);canonical=decimal(value).quantize(quantum);require(canonical==decimal(value),'Native price precision invalid');body[field]=format(canonical,'f')
    def related_unresolved(self,sub,m,exclude=None):
        parent=m.get('pending_parent',m['id']);related={parent}|{x['id'] for x in sub['mappings'].values() if x.get('pending_parent')==parent}
        return any(c['id']!=exclude and c['subscription']==sub['id'] and c['mapping'] in related and c['status'] in ('prepared','intent','unknown','accepted') for c in self.app.state['commands'].values())
    def effect(self,sub,m,kind,method,resource,body,sf,tf,conditions,query=None):
        app=self.app
        if self.related_unresolved(sub,m):return
        source=app.account(app.state['strategies'][sub['strategy']]['source']);target=app.account(sub['account']);self.price_fields(body or {},conditions);path='/v1/trading/accounts/'+target['id']+'/'+resource+('?' +urlencode(query) if query else '');raw=json.dumps(body,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode() if body is not None else b'';fingerprint=hashlib.sha256(method.encode()+b'\n'+path.encode()+b'\n'+raw).hexdigest();c={'id':token(),'subscription':sub['id'],'mapping':m['id'],'account':target['id'],'kind':kind,'method':method,'path':path,'body':body,'status':'prepared','created_at':now(),'fingerprint':fingerprint,'source_epoch':source['epoch'],'target_epoch':target['epoch']};app.state['commands'][c['id']]=c
        if kind=='close':
            current=next((p for p in tf['snapshot']['positions'] if p['position_id']==resource.rsplit('/',1)[1]),None);require(current is not None,'Native close target no longer exists');c['expected_remaining']=str(decimal(current['volume'])-decimal(query['volume'])) if query else '0'
        generations={'source':copy.deepcopy(sf.get('generations')),'target':copy.deepcopy(tf.get('generations'))};c['stream_generations']=generations
        app.save('Native immutable effect prepared')
        def dispatch_bound():
            require(not self.related_unresolved(sub,m,exclude=c['id']),'Native related pending group has an unresolved effect')
            # Bind this effect to its preparation, not the subscription's old Start frame.
            # Freshly verified owned cleanup can therefore proceed after a reconnect.
            for role,account in (('source',source),('target',target)):
                expected=generations[role];live=app.broker.sync_status(account)
                require(isinstance(expected,dict) and bool(expected) and live.get('generations')==expected,'Native '+role+' stream generation changed after preparation')
        def final():
            dispatch_bound()
            require(not app.state['frozen'] and not app.store.failed,'Native final owner/durability fence');current_sf=self.frame(source);current_tf=self.frame(target);require(current_sf['transaction_version']==sf['transaction_version'] and current_tf['transaction_version']==tf['transaction_version'],'Native transaction observation changed after preparation');current_conditions=self.condition(source,target,m['source']['instrument']);require(current_conditions==conditions,'Native conditions changed after preparation')
            for account in (source,target):account['observation']['details']=app.broker.read(account,'details')
            source_before = app.broker.read(source, 'snapshot')
            target_snapshot = app.broker.read(target, 'snapshot')
            target_at = now()
            source_snapshot = app.broker.read(source, 'snapshot')
            source_at = now()
            key = 'position_id' if m['type'] == 'position' else 'order_id'
            collection = 'positions' if m['type'] == 'position' else 'orders'
            source_id = m['source'][key]
            def selected(snapshot):
                return next((row for row in snapshot[collection] if row.get(key) == source_id), None)
            before, first, after = (selected(snapshot) for snapshot in (sf['snapshot'], source_before, source_snapshot))
            require(same_source_entity(first,after,m['type']), 'Native source changed during target observation')
            if sub['status'] not in ('stopping','stopped'):
                require(same_source_entity(before,after,m['type']), 'Native exact source changed after durable reservation')
            if kind in ('open', 'protection'):
                latest = self.protection(source_snapshot, after or m['source'])
                for snapshot, entity in ((sf['snapshot'], before), (source_before, first)):
                    levels = self.protection(snapshot, entity or m['source'])
                    require(all(price_equal(latest[key], levels[key]) for key in latest), 'Native source protection changed after reservation')
            for account, observed, frame in ((source, source_snapshot, sf), (target, target_snapshot, tf)):
                live = self.frame(account)
                require(live.get('transaction_version') == frame['transaction_version'], 'Native transaction observation changed during final reads')
                account['observation'].update(snapshot=copy.deepcopy(observed), checked_at=source_at if account is source else target_at)
            current_sf, current_tf = self.frame(source), self.frame(target)
            require(current_sf['transaction_version'] == sf['transaction_version'] and current_tf['transaction_version'] == tf['transaction_version'], 'Native transaction observation changed before dispatch')
            current_sf['snapshot']=source_snapshot;current_tf['snapshot']=target_snapshot;evidence=self.policy.authorize(app,sub,source,target,current_sf,current_tf,m['source'],conditions,kind)
            if kind=='open':
                require(sub['status']=='active','Native entries paused');lots,sizing=self.size(sub,m['source'],source,target,current_sf,current_tf,conditions,exclude=(sub['id'],m['id']));require(str(lots)==body['volume'],'Native sizing changed after durable reservation');require(0<=(datetime.now(timezone.utc)-instant(sizing['quote']['event_time'])).total_seconds()<=5,'Fresh final native tick expired before dispatch');status,reason=app.controls(sub,m['source'],current_tf['snapshot'],lots,sizing['quote'],exclude_command=c['id']);require(status is None,'Native final optional control: '+str(reason));c['final_sizing']=sizing
            else:
                owned=self.owned(sub,m,current_tf,kind)
                if kind=='close':
                    amount=decimal(query['volume']) if query else decimal(owned['volume']);require(decimal(owned['volume'])-amount==decimal(c['expected_remaining']),'Native owned close volume changed after reservation')
            if target['observation']['details']['settings'].get('account_status')=='close_only':require(method=='DELETE' or method=='POST' and (body or {}).get('type')=='sltp','Native close-only mode prohibits this modification')
            app.broker.quota.check(target['id'],method,urlsplit(path).path);c['final_check']=evidence
            # REST reads and final policy checks above may block while streams reconnect.
            dispatch_bound();return True
        try:
            ack=self.adapter(target).submit(target['id'],method,resource,body,c['id'],final,query=query);c['operation']=ack['operation_id'];c['status']='accepted';app.save('Native ACK retained; not a fill')
        except AdapterError as error:
            if c['status']=='prepared' or error.code=='LOCAL_QUOTA_NOT_SENT':c['status']='not_sent';m['status']='waiting' if kind=='open' else m['status']
            elif c['status'] not in ('not_sent','rejected'):c['status']='unknown';m['status']='unknown'
            if c['status']=='rejected':m['status']='rejected' if kind=='open' else 'review';m['reason']='Known native broker refusal; no automatic retry'
            elif c['status']=='not_sent' and kind=='open':m['status']='waiting';m['retry_after']=time.time()+1
            c['error']=str(error);app.save('Native dispatch/recovery evidence retained without resend')
    def owned(self,sub,m,tf,kind):
        collection=tf['snapshot']['positions' if m['type']=='position' else 'orders'];key='position_id' if m['type']=='position' else 'order_id';entity=next((p for p in collection if p.get(key)==m.get('target')),None);require(entity is not None and entity['instrument']==m['source']['instrument'] and entity['direction']==m['source']['direction'],'Exact native target ownership changed')
        if m['type']=='position':require(entity.get('state')=='open' and 0<decimal(entity['volume'])<=decimal(m['target_anchor']),'Native target semantic/volume anchor changed')
        else:require(entity.get('state')=='placed' and entity.get('order_type') in ('limit','stop'),'Native owned residual is not placed')
        return entity
    def reconcile(self,sub,sf,tf):
        app=self.app;target=app.account(sub['account'])
        for c in list(app.state['commands'].values()):
            if c['subscription']!=sub['id'] or c['status'] not in ('prepared','intent','unknown','accepted'):continue
            m=sub['mappings'][c['mapping']]
            if c['status']=='prepared':c['status']='not_sent';m['status']='waiting' if sub['status']=='active' else 'cancelled_before_dispatch';app.save('Native restored prepared effect proves no dispatch reservation');continue
            found=None
            for event in tf['events']:
                if c.get('operation'):
                    if event.get('operation_id')!=c['operation'] or event.get('client_request_id') not in (None,c['id']):continue
                elif event.get('client_request_id')!=c['id'] or not event.get('operation_id'):continue
                found=event;break
            if found is None:
                if c.get('operation') and time.time()>=c.get('next_operation_check',0):
                    previous=(c.get('operation_status'),c.get('entity_linkage_hold'),c.get('recovery_error'),c['status'])
                    try:self.adapter(target).operation(target['id'],c['operation'],c['id']);c['entity_linkage_hold']=True
                    except AdapterError as error:c['recovery_error']=str(error)
                    c['next_operation_check']=time.time()+min(30,c.get('poll_delay',1)*2);c['poll_delay']=min(30,c.get('poll_delay',1)*2)
                    if previous!=(c.get('operation_status'),c.get('entity_linkage_hold'),c.get('recovery_error'),c['status']):app.save('Native bounded status recovery; no guessed entity or resend')
                continue
            if c.get('operation') and c['operation']!=found['operation_id']:continue
            c['operation']=found['operation_id'];c['event']=copy.deepcopy(found)
            if found.get('status') in ('rejected','failed'):
                c['status']='rejected';c['error']='Native finalized '+found['status'];m['status']='rejected' if c['kind']=='open' else 'review';m['reason']='Known rejected native operation; inspect exact state before a new confirmed supported action';app.save('Native finalized refusal retained');continue
            if found.get('status')!='success':continue
            try:
                payload=found.get('payload',{});positions=payload.get('positions',[]);orders=payload.get('orders',[]);body=c.get('body') or {}
                if c['kind']=='open' and body.get('type') not in ('limit','stop'):
                    require(len(positions)==1,'Native market final result lacks a unique changed position');p=positions[0];identifier(p.get('position_id'));require(p.get('instrument')==body['instrument'] and p.get('direction')==body['side'] and p.get('state')=='open' and decimal(p.get('volume'))==decimal(body['volume']),'Native final open entity contradicts immutable request')
                    for deal in payload.get('deals',[]):require(deal.get('position_id') in (None,p['position_id']) and deal.get('instrument') in (None,body['instrument']) and deal.get('direction') in (None,body['side']),'Contradictory native open deal link')
                    expected={k:body.get(k) for k in ('stop_loss_price','take_profit_price')};protected=[o for o in orders if o.get('order_type')=='sltp' and o.get('position_id')==p['position_id']]
                    if any(v is not None for v in expected.values()):require(len(protected)==1 and protected[0].get('state')=='placed' and all(k in protected[0] and price_equal(protected[0][k],v) for k,v in expected.items()),'Atomic native protection ownership is not confirmed');m['protection_order']=protected[0]['order_id']
                    m.update(target=p['position_id'],target_anchor=p['volume'],status='confirmed',expected_protection=expected)
                elif c['kind']=='open':
                    candidates=[o for o in orders if o.get('order_type')==body['type']];require(len(candidates)==1,'Native pending placement lacks exact order evidence');o=candidates[0];identifier(o.get('order_id'));require(o.get('instrument')==body['instrument'] and o.get('direction')==body['side'] and o.get('state')=='placed' and decimal(o['volume'])==decimal(body['volume']) and decimal(o['price'])==decimal(body['price']),'Native pending result contradicts request');expected={k:body.get(k) for k in ('stop_loss_price','take_profit_price')}
                    if any(v is not None for v in expected.values()):
                        inline=all(k in o and price_equal(o[k],v) for k,v in expected.items());linked=[protection for protection in orders if protection.get('order_type')=='sltp' and o.get('position_id') is not None and protection.get('position_id')==o['position_id'] and all(k in protection and price_equal(protection[k],v) for k,v in expected.items())];require(inline or len(linked)==1,'Native pending protection result is incomplete/ambiguous')
                        if len(linked)==1:m['protection_order']=linked[0]['order_id']
                    m.update(target=o['order_id'],status='placed',target_anchor=body['volume'],expected_protection=expected)
                elif c['kind']=='close':
                    expected_id=c['path'].split('?',1)[0].rsplit('/',1)[1];p=next((p for p in positions if p.get('position_id')==expected_id),None);require(p is not None and p.get('instrument')==m['source']['instrument'] and p.get('direction')==m['source']['direction'],'Native close result lacks exact owned entity');remaining=decimal(p['volume']);require(remaining==decimal(c.get('expected_remaining','0')) and p.get('state')==('closed' if remaining==0 else 'open'),'Native close remaining-volume evidence contradicts command');m['last_remaining']=str(remaining);m['status']='closed' if remaining==0 else 'confirmed'
                elif c['kind']=='cancel':
                    o=next((o for o in orders if o.get('order_id')==m.get('target')),None);require(o is not None and o.get('state')=='cancelled','Native pending cancel lacks exact terminal order');m['status']='cancelled'
                elif c['kind']=='edit':
                    o=next((o for o in orders if o.get('order_id')==m.get('target')),None);require(o is not None and o.get('state')=='placed' and all(k in o and price_equal(o[k],v) for k,v in body.items()),'Native pending edit lacks exact requested values');m['status']='placed';m['expected_protection']={**m.get('expected_protection',{}),**{k:v for k,v in body.items() if k in ('stop_loss_price','take_profit_price')}}
                elif c['kind']=='protection':
                    expected_id=body.get('position_id',m['target']);candidates=[o for o in orders if o.get('order_type')=='sltp' and o.get('position_id')==expected_id];require(len(candidates)==1,'Native SLTP result lacks unique linked order');o=candidates[0]
                    if c['method']=='PATCH':require(o.get('order_id')==m.get('protection_order'),'Native SLTP order ownership changed')
                    expected={k:body[k] for k in ('stop_loss_price','take_profit_price') if k in body};require(all(k in o and price_equal(o[k],v) for k,v in expected.items()),'Native SLTP returned levels are incomplete or contradictory');require(o.get('state') in ('placed','cancelled'),'Native SLTP state unavailable');m['expected_protection']={**m.get('expected_protection',{}),**expected};m['protection_order']=o['order_id'] if o['state']=='placed' else None
                c['status']='confirmed';c['ownership_confirmed']=True;c.pop('entity_linkage_hold',None);app.save('Native exact correlated entity effect confirmed')
            except (AdapterError,KeyError,ValueError,TypeError) as error:c['entity_linkage_hold']=True;c['recovery_error']=str(error);app.save('Native operation retained with entity-linkage hold')
    def source_origin(self,position,sf,sub,source,mapping):
        if 'p:'+position['position_id'] in sub.get('initial_eligible',[]):return True
        for event in reversed(sf['events']):
            if event.get('status')!='success':continue
            payload=event.get('payload',{});deals=[d for d in payload.get('deals',[]) if d.get('type')=='open' and d.get('position_id')==position['position_id']]
            for deal in deals:
                order=next((o for o in payload.get('orders',[]) if o.get('order_id')==deal.get('order_id')),None)
                if not order:continue
                if order.get('order_type')!='market':return False
                require(order.get('position_id') in (None,position['position_id']) and deal.get('instrument')==position['instrument'] and deal.get('direction')==position['direction'] and order.get('instrument')==position['instrument'] and order.get('direction')==position['direction'],'Contradictory published native market lineage');return True
        # Corroborate a fresh source position when the event omitted linked entities.
        # Exact deal/order/position identity is required. An absent or pending order cannot qualify.
        created = instant(position['create_time'])
        recent = datetime.now(timezone.utc) - timedelta(seconds=2)
        if not instant(sub['created_at']) <= created < recent or (recent-created).total_seconds() > 60:
            return False
        if time.time() < mapping.get('next_lineage_read', 0):
            return False
        mapping['next_lineage_read'] = time.time() + 8
        evidence = self.app.broker.entry_history(source, (created-timedelta(seconds=2)).isoformat(), recent.isoformat())
        deals = [row['deal'] for row in evidence['deals'] if row['deal'].get('position_id') == position['position_id'] and row['deal'].get('type') == 'open']
        if len(deals) != 1:
            return False
        deal = deals[0]
        order_id = identifier(deal.get('order_id'))
        orders = [row['order'] for row in evidence['orders'] if row['order'].get('order_id') == order_id]
        if len(orders) != 1:
            return False
        order = orders[0]
        if order.get('order_type') != 'market' or order.get('state') != 'filled' or order.get('position_id') != position['position_id']:
            return False
        if any(row.get(key) != position.get(key) for row in (deal, order) for key in ('instrument', 'direction')):
            return False
        if not decimal(deal.get('volume')) == decimal(position.get('initial_volume') or position['volume']) == decimal(order.get('volume')):
            return False
        mapping['market_lineage'] = {'source': 'broker_history', 'deal_id': identifier(deal.get('deal_id')), 'order_id': order_id}
        return True
    def open(self,sub,signal,kind,source,target,sf,tf):
        app=self.app;sid=('p:' if kind=='position' else 'o:')+signal['position_id' if kind=='position' else 'order_id'];m=sub['mappings'].get(sid)
        if m and (m['status']!='waiting' or time.time()<m.get('retry_after',0)):return
        m=m or {'id':sid,'type':kind,'source':copy.deepcopy(signal),'source_anchor':signal['volume'],'status':'waiting'};sub['mappings'][sid]=m
        try:
            if kind=='position':require(self.source_origin(signal,sf,sub,source,m),'Published native source market lineage unavailable or related to pending entry')
            else:
                observed=any(e.get('status')=='success' and instant(e['event_time'])>=instant(sub['created_at']) and any(o.get('order_id')==signal['order_id'] and o.get('state')=='placed' for o in e.get('payload',{}).get('orders',[])) for e in sf['events']);require(observed,'Existing/earlier-executed native pending entry needs explicit unfilled-history support')
                require(not any(d.get('order_id')==signal['order_id'] and d.get('type')=='open' for e in sf['events'] for d in e.get('payload',{}).get('deals',[])),'Native source pending entry already executed; residual-volume semantics remain held')
            conditions=self.condition(source,target,signal['instrument']);self.policy.authorize(app,sub,source,target,sf,tf,signal,conditions,'open');lots,sizing=self.size(sub,signal,source,target,sf,tf,conditions);status,reason=app.controls(sub,signal,tf['snapshot'],lots,sizing['quote'])
            if status:m.update(status=status,reason=reason);app.save('Native optional entry decision');return
            body={'instrument':signal['instrument'],'side':signal['direction'],'volume':str(lots)}
            if kind=='order':body.update(type=signal['order_type'],price=signal['price'])
            body.update({field:value for field,value in self.protection(sf['snapshot'],signal).items() if value is not None});self.price_fields(body,conditions);m.update(source=copy.deepcopy(signal),sizing=sizing,requested_lots=str(lots),margin=sizing['margin'],contract={k:conditions[k] for k in ('base_currency','quote_currency','margin_currency','calc_mode','contract_size')},status='opening');self.effect(sub,m,'open','POST','positions' if kind=='position' else 'orders',body,sf,tf,conditions)
        except (AdapterError,KeyError,ValueError,TypeError) as error:
            m.update(status='skipped' if str(error).startswith('Skipped:') else 'waiting',reason=str(error),retry_after=time.time()+1);app.save('Native unsupported/unready candidate held with evidence')
    def recover_fills(self,sub,sf,tf,m):
        # Known unprotected pending IDs, including retained partial executions, fully fill offline.
        # Never infer ownership for an unknown placement or settle its command from history.
        if m.get('history_recovery',{}).get('status')=='recovered' or m['status'] in ('cancelled','closed','rejected') or self.related_unresolved(sub,m):return
        pairs=(('source',sf,m['source']['order_id'],m['source_anchor'],self.app.state['strategies'][sub['strategy']]['source']),('target',tf,m['target'],m['requested_lots'],sub['account']))
        if any(any(o['order_id']==oid for o in frame['snapshot']['orders']) for _,frame,oid,_,_ in pairs):return
        if all(sum((decimal(d['volume']) for d in m[side+'_deals'].values()),Decimal(0))==decimal(planned) for side,_,_,planned,_ in pairs):return
        state=m.setdefault('history_recovery',{})
        if time.time()<state.get('next_read',0):raise AdapterError(state.get('reason','Exact fill history recovery waiting'))
        state.update(status='reading',next_read=time.time()+30)
        try:
            require(not self.related_unresolved(sub,m),'Unknown related command still requires exact result evidence')
            require(not any(value is not None for value in m.get('expected_protection',{}).values()),'History-only protection linkage is not supported')
            start=m['source']['create_time'];end=now();recovered={};reads={}
            for side,frame,oid,planned,account in pairs:
                history=self.app.broker.fill_history(self.app.account(account),start,end);cached=m[side+'_deals'];deals=copy.deepcopy(cached);returned=set()
                for row in history['items']:
                    deal=row['deal']
                    require(deal.get('deal_id') not in cached or cached[deal['deal_id']]==deal,'Recovery history contradicts retained fill evidence')
                    if deal.get('order_id')!=oid or deal.get('type')!='open':continue
                    identifier(deal.get('deal_id'));identifier(deal.get('position_id'));require(deal.get('instrument')==m['source']['instrument'] and deal.get('direction')==m['source']['direction'] and decimal(deal['volume'])>0,'Recovery exact deal lineage/volume conflict')
                    require(deal['deal_id'] not in deals or deals[deal['deal_id']]==deal,'Recovery conflicting deal identity');deals[deal['deal_id']]=copy.deepcopy(deal);returned.add(deal['deal_id'])
                ids={d['position_id'] for d in deals.values()};total=sum((decimal(d['volume']) for d in deals.values()),Decimal(0))
                require(len(ids)==1 and total==decimal(planned),'Exact full-fill history unavailable; no inferred ownership or replacement')
                p=next((p for p in frame['snapshot']['positions'] if p['position_id']==next(iter(ids))),None)
                require(p is not None and p.get('state')=='open' and p.get('instrument')==m['source']['instrument'] and p.get('direction')==m['source']['direction'] and decimal(p['volume'])==total,'Recovered position no longer matches exact full-fill history')
                recovered[side]=deals;reads[side]={'account':account,'order_id':oid,'deal_ids':sorted(deals),'retained_deal_ids':sorted(cached),'returned_deal_ids':sorted(returned),'new_deal_ids':sorted(set(deals)-set(cached)),'from':start,'to':end,'pagination_complete':True}
            # All-or-nothing adoption. History stays history; no fabricated transaction event.
            for side,deals in recovered.items():m[side+'_deals']=deals
            state.update(status='recovered',reads=reads,at=now());state.pop('reason',None)
            if m.pop('history_hold',False):m.pop('native_hold',None);m.pop('review_required',None);m.pop('reason',None)
            self.app.save('Exact known pending full fills recovered from bounded positive history')
        except (AdapterError,KeyError,ValueError,TypeError) as error:
            state.update(status='held',reason=str(error));m['history_hold']=True;self.app.save('History recovery incomplete; ownership remains held without replay');raise
    def fills(self,sub,sf,tf):
        for mapping in list(sub['mappings'].values()):
            if mapping['type']!='order' or not mapping.get('target'):continue
            try:self.fills_one(sub,sf,tf,mapping)
            except (AdapterError,KeyError,ValueError,TypeError) as error:
                changed=mapping.get('reason')!=str(error);mapping.update(native_hold=True,review_required=True,reason=str(error))
                if changed:self.app.save('Native pending group evidence held; independent groups remain eligible')
    def fills_one(self,sub,sf,tf,m):
        app=self.app
        if m['type']!='order' or not m.get('target'):return
        source_order=m['source']['order_id'];before=json.dumps({'mapping':m,'child':sub['mappings'].get('fp:'+source_order)},sort_keys=True);m.setdefault('source_deals',{});m.setdefault('target_deals',{})
        for side,frame,order_id in (('source',sf,source_order),('target',tf,m['target'])):
            for event in frame['events']:
                if event.get('status')!='success':continue
                for deal in event.get('payload',{}).get('deals',[]):
                    if deal.get('type')!='open' or deal.get('order_id')!=order_id:continue
                    require(deal.get('instrument')==m['source']['instrument'] and deal.get('direction')==m['source']['direction'],'Native pending deal lineage conflict');identifier(deal.get('deal_id'));identifier(deal.get('position_id'));require(decimal(deal['volume'])>0,'Native fill volume unavailable');old=m[side+'_deals'].get(deal['deal_id']);require(old is None or old==deal,'Conflicting native fill deal identity');m[side+'_deals'][deal['deal_id']]=copy.deepcopy(deal)
        self.recover_fills(sub,sf,tf,m)
        spids={d['position_id'] for d in m['source_deals'].values()};tpids={d['position_id'] for d in m['target_deals'].values()}
        if not spids or not tpids:return
        require(len(spids)==len(tpids)==1,'Native multi-position/asymmetric pending fill topology held');source_id=next(iter(spids));target_id=next(iter(tpids));source_position=next((p for p in sf['snapshot']['positions'] if p['position_id']==source_id),None);target_position=next((p for p in tf['snapshot']['positions'] if p['position_id']==target_id),None)
        if not target_position:return
        source_total=sum(decimal(d['volume']) for d in m['source_deals'].values());target_total=sum(decimal(d['volume']) for d in m['target_deals'].values());source_active=any(o['order_id']==source_order and o.get('state')=='placed' for o in sf['snapshot']['orders']);target_active=any(o['order_id']==m['target'] and o.get('state')=='placed' for o in tf['snapshot']['orders']);child_id='fp:'+source_order;child=sub['mappings'].get(child_id)
        if child is None:
            source_signal=copy.deepcopy(source_position or {'position_id':source_id,'instrument':m['source']['instrument'],'direction':m['source']['direction'],'volume':str(source_total),'state':'open','create_time':m['source'].get('create_time')});child={'id':child_id,'type':'position','source':source_signal,'source_anchor':str(source_total),'target':target_id,'target_anchor':str(target_total),'status':'confirmed','pending_parent':m['id'],'expected_protection':copy.deepcopy(m.get('expected_protection',{k:m['source'].get(k) for k in ('stop_loss_price','take_profit_price')}))};sub['mappings'][child_id]=child
        else:
            require(child['target']==target_id and child['source']['position_id']==source_id,'Native pending fill position identity changed');child['source_anchor']=str(source_total);child['target_anchor']=str(target_total)
        # A fill establishes initial protection. Subsequent confirmed position changes supersede it.
        protection_changed = any(
            command['subscription'] == sub['id'] and command['mapping'] == child_id
            and command['kind'] == 'protection' and command['status'] == 'confirmed'
            for command in self.app.state['commands'].values()
        )
        if not protection_changed:
            for event in tf['events']:
                if not any(deal.get('order_id')==m['target'] and deal.get('position_id')==target_id and deal.get('type')=='open' for deal in event.get('payload',{}).get('deals',[])):continue
                protections=[order for order in event.get('payload',{}).get('orders',[]) if order.get('order_type')=='sltp' and order.get('position_id')==target_id and order.get('state')=='placed' and all(field in order and price_equal(order[field],value) for field,value in m.get('expected_protection',{}).items())]
                if len(protections)==1:child['protection_order']=protections[0]['order_id'];child['expected_protection']=copy.deepcopy(m['expected_protection'])
        m['filled_source']=source_id;m['filled_target']=target_id;m['executed_source_lots']=str(source_total);m['executed_target_lots']=str(target_total);m['source_residual_active']=source_active;m['target_residual_active']=target_active
        # Fill observation cannot undo an exact cancellation or an unresolved command.
        pending=any(c['subscription']==sub['id'] and c['mapping']==m['id'] and c['status'] in ('prepared','intent','unknown','accepted') for c in app.state['commands'].values())
        if m['status'] not in ('cancelled','closed','rejected') and not pending:m['status']='pending_fill' if source_active or target_active else 'filled'
        step=decimal(self.app.broker.read(self.app.account(sub['account']),'instruments/'+m['source']['instrument'])['volume_step']);expected=(source_total*decimal(m['requested_lots'])/decimal(m['source_anchor'])/step).to_integral_value(rounding=ROUND_DOWN)*step;child['asymmetric_fill']=target_total!=expected;child['pending_active']=source_active or target_active or child['asymmetric_fill']
        if child['asymmetric_fill']:child['reason']='Asymmetric exact pending fills held; no volume inference or market top-up'
        if sub['status']=='paused' and (source_active or target_active):child['pending_review']=True;child['reason']='Partially filled pending group held for review after Pause'
        if json.dumps({'mapping':m,'child':sub['mappings'].get('fp:'+source_order)},sort_keys=True)!=before:app.save('Native unique exact fill links/anchors retained; no market replacement')
    def manage(self,sub,source,target,sf,tf):
        app=self.app;ss=sf['snapshot'];ts=tf['snapshot'];source_positions={p['position_id']:p for p in ss['positions']};target_positions={p['position_id']:p for p in ts['positions']};source_orders={o['order_id']:o for o in ss['orders']};target_orders={o['order_id']:o for o in ts['orders']}
        for m in list(sub['mappings'].values()):
            if not m.get('target') or m['status'] in ('closed','cancelled','filled'):continue
            if m.get('native_hold') and sub['status'] not in ('stopping','stopped'):continue
            # A residual and its deal-linked child are one cleanup group. In particular,
            # Stop cannot close the child while cancellation of its parent is unknown.
            if self.related_unresolved(sub,m):continue
            if any(c['subscription']==sub['id'] and c['mapping']==m['id'] and c['status']=='rejected' and c['kind']!='open' and not c.get('retry_authorized') for c in app.state['commands'].values()):m.update(status='review',reason='Known rejected native management; fresh confirmed retry required');continue
            try:
                conditions=self.condition(source,target,m['source']['instrument']);self.policy.authorize(app,sub,source,target,sf,tf,m['source'],conditions,'management')
                if m['type']=='order':
                    so=source_orders.get(m['source']['order_id']);to=target_orders.get(m['target'])
                    cancelled=any(e.get('status')=='success' and any(o.get('order_id')==m['source']['order_id'] and o.get('state') in ('cancelled','rejected') for o in e.get('payload',{}).get('orders',[])) for e in sf['events'])
                    if to and (sub['status'] in ('paused','stopping','stopped') or not so and cancelled):self.effect(sub,m,'cancel','DELETE','orders/'+m['target'],None,sf,tf,conditions);continue
                    if to and so:
                        changed={k:so.get(k) for k in ('price','stop_loss_price','take_profit_price') if not price_equal(so.get(k),to.get(k))}
                        if changed:self.effect(sub,m,'edit','PATCH','orders/'+m['target'],changed,sf,tf,conditions)
                    continue
                tp=target_positions.get(m['target']);sp=source_positions.get(m['source']['position_id'])
                if tp is None:m.update(status='review',reason='Native owned position missing from current snapshot; no guessed close or replacement');continue
                self.owned(sub,m,tf,'management')
                if sub['status'] in ('stopping','stopped'):self.effect(sub,m,'close','DELETE','positions/'+m['target'],None,sf,tf,conditions);continue
                if m.get('pending_active') or m.get('pending_review'):continue
                if sp is None:
                    closed=any(e.get('status')=='success' and any(p.get('position_id')==m['source']['position_id'] and p.get('state')=='closed' and decimal(p.get('volume'))==0 for p in e.get('payload',{}).get('positions',[])) for e in sf['events']);require(closed,'Native source absence lacks exact close evidence');self.effect(sub,m,'close','DELETE','positions/'+m['target'],None,sf,tf,conditions);continue
                require(sp['instrument']==m['source']['instrument'] and sp['direction']==m['source']['direction'] and decimal(sp['volume'])<=decimal(m['source_anchor']),'Native source semantic/increased volume requires review');step=decimal(conditions['volume_step']);desired=(decimal(m['target_anchor'])*decimal(sp['volume'])/decimal(m['source_anchor'])/step).to_integral_value(rounding=ROUND_DOWN)*step;current=decimal(tp['volume'])
                if current<desired:m.update(status='review',reason='Manual native target reduction; no automatic top-up');continue
                if current>desired:
                    amount=current-desired;require(amount%step==0 and (desired==0 or desired>=decimal(conditions['volume_min'])),'Native partial close/remainder incompatible');self.effect(sub,m,'close','DELETE','positions/'+m['target'],None,sf,tf,conditions,query={'volume':str(amount)} if desired else None);continue
                expected=m.get('expected_protection',{});actual_orders=[o for o in ts['orders'] if o.get('order_type')=='sltp' and o.get('position_id')==m['target']];require(len(actual_orders)<=1,'Multiple native target protection orders require review');actual=actual_orders[0] if actual_orders else None
                if actual:require(actual.get('order_id')==m.get('protection_order'),'Native target protection is not owned by this copy')
                require(all(price_equal((actual or {}).get(k),expected.get(k)) for k in ('stop_loss_price','take_profit_price')) and all(k not in tp or price_equal(tp[k],expected.get(k)) for k in ('stop_loss_price','take_profit_price')),'Manual/contradictory native protection requires review');desired_protection=self.protection(ss,sp)
                if not all(price_equal(desired_protection.get(k),expected.get(k)) for k in ('stop_loss_price','take_profit_price')):
                    if actual:self.effect(sub,m,'protection','PATCH','orders/'+actual['order_id'],desired_protection,sf,tf,conditions)
                    elif any(v is not None for v in desired_protection.values()):self.effect(sub,m,'protection','POST','orders',{'type':'sltp','position_id':m['target'],**desired_protection},sf,tf,conditions)
            except (AdapterError,KeyError,ValueError,TypeError) as error:m['reason']=str(error);m['review_required']=True
    def tick(self):
        app=self.app
        if app.state['frozen'] or app.store.failed:return
        for sub in app.state['subscriptions'].values():
            if not sub.get('native') or sub['status']=='stopped' and not sub.get('follow_up'):continue
            if sub['status']=='stopping' and time.time()>sub['stop_deadline']:sub['status']='stopped';sub['follow_up']=True;app.save('Native bounded Stop retains follow-up while broker unavailable')
            try:
                source=app.account(app.state['strategies'][sub['strategy']]['source']);target=app.account(sub['account']);self.refresh(source);self.refresh(target);sf=self.frame(source);tf=self.frame(target)
                generations={source['id']:sf.get('generations'),target['id']:tf.get('generations')}
                if sub['status']=='active' and generations!=sub.get('sync_generations'):
                    sub['status']='paused';sub['initial_eligible']=[];sub['restart_hold']='Native stream generation changed; fresh readiness and explicit Resume required';sub['seen']=list(set(sub['seen']+app.signal_ids(sf['snapshot'])))
                    for mapping in sub['mappings'].values():
                        if mapping['status']=='waiting':mapping['status']='cancelled_before_dispatch'
                    app.save('Native stream generation change paused entries without replay')
                day=now()[:10];equity=decimal(tf['snapshot']['account_state']['equity']);daily=sub['daily']
                if daily.get('day')!=day:sub['daily']={'day':day,'start_equity':str(equity),'loss':'0'};app.save('Native original UTC-day whole-account equity baseline retained')
                else:daily['loss']=str(max(Decimal(0),decimal(daily['start_equity'])-equity))
                if sub['status'] in ('active','paused') and sub['daily_auto_close'] and sub['controls']['daily_loss_pct'] is not None and decimal(sub['daily']['loss'])>=decimal(sub.get('amount') or sub['activation_budget'])*decimal(sub['controls']['daily_loss_pct'])/100:
                    sub['status']='stopping';sub.setdefault('stop_deadline',time.time()+10);sub.setdefault('daily_stop',{'id':token(),'day':day,'at':now()});app.save('Native separately consented daily-loss desired Stop retained')
                self.reconcile(sub,sf,tf);self.fills(sub,sf,tf);self.manage(sub,source,target,sf,tf)
                if sub['status'] in ('stopping','stopped'):
                    active=[m for m in sub['mappings'].values() if m.get('target') and m['status'] not in ('closed','cancelled','filled')];unresolved=app.unresolved(sub)
                    if sub['status']=='stopped':
                        if sub.get('follow_up')!=bool(active or unresolved):sub['follow_up']=bool(active or unresolved);app.save('Native late stopped follow-up recomputed')
                    elif not active and not unresolved or time.time()>sub['stop_deadline']:sub['status']='stopped';sub['follow_up']=bool(active or unresolved);app.save('Native bounded Stop retained permanent exact follow-up')
                    continue
                ids=app.signal_ids(sf['snapshot'])
                if sub['status']=='active' and app.state['strategies'][sub['strategy']]['published']:
                    for order in sf['snapshot']['orders']:
                        sid='o:'+order['order_id']
                        if order.get('order_type') in ('limit','stop') and (sid not in sub['seen'] or sub['mappings'].get(sid,{}).get('status')=='waiting'):self.open(sub,order,'order',source,target,sf,tf)
                    linked={m.get('filled_source') for m in sub['mappings'].values() if m['type']=='order'}
                    for position in sf['snapshot']['positions']:
                        sid='p:'+position['position_id']
                        if position['position_id'] not in linked and (sid not in sub['seen'] or sub['mappings'].get(sid,{}).get('status')=='waiting'):self.open(sub,position,'position',source,target,sf,tf)
                seen=set(sub['seen'])|set(ids)
                if seen!=set(sub['seen']):sub['seen']=list(seen);app.save('Native source boundary consumed without paused replay')
                sub['monitor']={'at':now(),'source_version':sf['transaction_version'],'target_version':tf['transaction_version'],'native':True};app.error=None
            except Exception as error:app.error='Native execution held: '+str(error)
