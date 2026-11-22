"""Offline domain checks; no application, socket or broker access."""
from copy import deepcopy
from datetime import datetime,timezone,timedelta
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'assets'/'policies'))
from policy_controls import *
def emit_result(value):
 if '--output' in sys.argv:Path(sys.argv[sys.argv.index('--output')+1]).write_text(value)
ROOT=Path(__file__).resolve().parent
now='2026-11-18T16:00:00+00:00';old='2026-11-18T15:59:00+00:00';checks=[]
def check(label,value=True):
    assert value,label
    checks.append(label);print('PASS '+label,flush=True)
def denied(fn):
    try:fn()
    except PolicyError:return True
    return False
provider='provider-local';iid='9007199254740993';sid='9007199254740995'
def obs(account,**fields):return {'account_id':account,'verified':True,'verified_at':now,'currency':'USD','stream_id':'server.live.std','is_demo':False,**fields}
def ctx(**fields):return {'provider_id':provider,'investor_account':iid,'source_account':sid,'strategy_id':'strategy-one','transition':'start','now':now,**fields}
def change(policy,**values):return save_policy(policy,provider,policy['revision'],values,now)
def page(rows,count,**extra):return {'successful':True,'provider_id':provider,'checked_at':now,'query':{'client_account':[iid],'limit':100,'offset':0},'rows':rows,'totals':{'count':count},**extra}
p=new_policy(provider);check('four independent requirements defaultOFF',set(p['settings'])==set(POLICY_KEYS) and not any(p['settings'].values()))
original=deepcopy(p);check('ownership strictbooleans and revision conflicts preserve original',denied(lambda:save_policy(p,'other',0,{'real_accounts_only':True},now)) and denied(lambda:save_policy(p,provider,0,{'real_accounts_only':'true'},now)) and denied(lambda:save_policy(p,provider,1,{},now)) and p==original)
p=change(p,real_accounts_only=True);p=change(p,same_currency_only=False);check('omitted settings preserved and audit/revision recorded',p['settings']['real_accounts_only'] and p['revision']==2 and len(p['audit'])==2)
check('strict real false passes true blocks and missing/string/numeric stayspending',admission(p,ctx(),obs(iid),obs(sid))['allowed'] and admission(p,ctx(),obs(iid,is_demo=True),obs(sid))['status']=='block' and all(admission(p,ctx(),obs(iid,is_demo=x),obs(sid))['status']=='pending' for x in (None,'false',0,1)))
check('source and active management exempt while manual Resume rechecks current policy',admission(p,ctx(investor_account=sid),obs(sid,is_demo=True),obs(sid))['allowed'] and admission(p,ctx(transition='active_management'),obs(iid,is_demo=True),obs(sid))['allowed'] and not admission(p,ctx(transition='resume'),obs(iid,is_demo=True),obs(sid))['allowed'])
pc=change(new_policy(provider),same_currency_only=True,same_account_type_only=True)
check('currency cents and selected-source product code compare independently',admission(pc,ctx(),obs(iid,stream_id='a.trial.future9'),obs(sid,stream_id='different.live.future9'))['allowed'] and admission(pc,ctx(),obs(iid,currency='USC'),obs(sid))['status']=='block')
check('missing stale or wrong-bound source/type evidence stayspending',admission(pc,ctx(),obs(iid,stream_id=''),obs(sid))['status']=='pending' and admission(pc,ctx(),obs(iid),obs(sid,verified_at=old))['status']=='pending' and admission(pc,ctx(),obs(iid),obs('9007199254740997'))['status']=='pending')
check('pre-strategy connection ignores currency/type policy without disturbing login',admission(pc,ctx(transition='connection',strategy_id=None,source_account=None),obs(iid,currency='JPY'),None)['allowed'] and admission(pc,ctx(transition='login'),None,None)['allowed'])
proof=admission(pc,ctx(),obs(iid),obs(sid))['snapshot'];check('final admission validates exact current bound evidence',validate_admission(proof,pc,ctx(),obs(iid),obs(sid))['allowed'])
check('final revision strategy and changed evidence cannot reuse preview',denied(lambda:validate_admission(proof,change(pc,real_accounts_only=True),ctx(),obs(iid),obs(sid))) and denied(lambda:validate_admission(proof,pc,ctx(strategy_id='different'),obs(iid),obs(sid))) and denied(lambda:validate_admission(proof,pc,ctx(),obs(iid,currency='EUR'),obs(sid))))
check('partner enable requires separate consent and report-access proof',denied(lambda:change(new_policy(provider),partner_accounts_only=True)))
access={'provider_id':provider,'status':'verified_report_access','credential_ref':'vault-provider-reference','identity_fingerprint':'registered-pair-proof','checked_at':now}
pp=save_policy(new_policy(provider,'registered-pair-proof'),provider,0,{'partner_accounts_only':True},now,partner_access=access,verification_consent=True)
m=membership_evidence(provider,pp['revision'],iid,[page([{'client_account':iid}],1)],now)
check('exact full account attribution passes without clientUID/email',m['status']=='member' and admission(pp,ctx(),obs(iid),obs(sid),m)['allowed'] and 'rows' not in m)
wrong=membership_evidence(provider,1,iid,[page([{'client_account':'900719925474099'}],1)],now)
check('truncated or another account and ignored filters cannot prove membership',wrong['status']=='pending' and not admission(pp,ctx(),obs(iid),obs(sid),wrong)['allowed'])
absent=membership_evidence(provider,1,iid,[page([],0)],now);partial=membership_evidence(provider,1,iid,[page([],1)],now)
check('complete filtered absence is blocked while partial/error/stale stayspending',absent['status']=='absent' and admission(pp,ctx(),obs(iid),obs(sid),absent)['status']=='block' and partial['status']=='pending' and membership_evidence(provider,1,iid,[page([],0,successful=False)],now)['status']=='pending' and membership_evidence(provider,1,iid,[page([{'client_account':iid}],1,checked_at=old)],now)['status']=='pending')
check('membership never substitutes for fresh Trading authorization',admission(pp,ctx(),obs(iid,verified=False),obs(sid),m)['status']=='pending')
pp['partner_evidence']={'example':'retained'};off=change(pp,partner_accounts_only=False);check('disable removes verification/evidence without touching separate provider key vault',off['partner_verification'] is None and not off['partner_evidence'] and pp['partner_verification']['credential_ref']=='vault-provider-reference')
sub={'account':iid,'revision':0,'status':'paused','mode':'Proportional','amount':'12000','multiplier':'1','activation_risk_budget':'10000','advanced':new_advanced(),'commands':[],'mappings':[{'original_lots':'0.02'}]}
check('fiveAdvanced controls OFF/null with autoclosefalse',all(sub['advanced'][k] is None for k in ADVANCED_KEYS) and not sub['advanced']['auto_close_daily_loss'])
check('Advanced edit needs confirmation explicitvalue and ownership',denied(lambda:edit_advanced(sub,iid,0,{},now)) and denied(lambda:edit_advanced(sub,'other',0,{},now,confirmed=True)) and denied(lambda:edit_advanced(sub,iid,0,{'max_positions':{'enabled':True}},now,confirmed=True)))
check('unfinished outcome blocks edits without changing subscription',denied(lambda:edit_advanced({**sub,'commands':[{'status':'unknown'}]},iid,0,{},now,confirmed=True)))
a=edit_advanced(sub,iid,0,{'daily_loss_pct':{'enabled':True,'value':'5'},'max_trade_volume':{'enabled':True,'value':'1.25'}},now,confirmed=True)
check('Advanced save is atomic paused and retains original maps',a['status']=='paused' and a['mappings']==sub['mappings'] and a['advanced']['max_trade_volume']=='1.25' and sub['advanced']['daily_loss_pct'] is None)
check('daily automatic close requires separate explicit consent',denied(lambda:edit_advanced(a,iid,1,{},now,confirmed=True,auto_close={'enabled':True})))
a=edit_advanced(a,iid,1,{},now,confirmed=True,auto_close={'enabled':True,'consent':True});a=edit_advanced(a,iid,2,{'daily_loss_pct':{'enabled':False}},now,confirmed=True);check('disabling Daily loss also disables automatic close',a['advanced']['daily_loss_pct'] is None and not a['advanced']['auto_close_daily_loss'])
b=edit_copy_mode(sub,iid,0,'Proportional',now,'50000',confirmed=True,allocation='20000',multiplier='1.5');check('paused same-mode amount above10000 accepted within actualequity noresume/remap',b['amount']=='20000' and b['status']=='paused' and b['mappings']==sub['mappings'])
check('overequity or invalid precision saves no partial fields',denied(lambda:edit_copy_mode(sub,iid,0,'Proportional',now,'10000',confirmed=True,allocation='15000')) and denied(lambda:edit_copy_mode(sub,iid,0,'Proportional',now,'50000',confirmed=True,allocation='10.001')) and sub['amount']=='12000')
one=edit_copy_mode(sub,iid,0,'1:1',now,'50000',confirmed=True);check('1to1 preserves amount/riskbudget resets multiplier and rejects proportionalfields',one['amount']==sub['amount'] and one['activation_risk_budget']=='10000' and one['multiplier']=='1' and denied(lambda:edit_copy_mode(sub,iid,0,'1:1',now,'50000',confirmed=True,allocation='1000')))
controls=new_advanced();daily,_=daily_loss_update(None,'10000',now,'1000',controls,subscription_status='paused');controls.update(daily_loss_pct='5',auto_close_daily_loss=True);daily,result=daily_loss_update(daily,'9900',now,'1000',controls,subscription_status='paused');check('daily wholeaccount equity threshold can request normalStop whilepaused after enabling',result['threshold']=='50' and result['loss']=='100' and result['action']=='request_normal_stop')
daily,result=daily_loss_update(daily,'9800',now,'1000',controls,subscription_status='paused');check('daily desiredStop request does not repeat after persisted observation',result['action']=='block_entries' and daily['stop_requested'])
nextday,result=daily_loss_update(daily,'9800','2026-11-19T00:00:00Z','1000',controls,subscription_status='stopped');check('UTC newday baseline resets without requesting resume or a new stop',nextday['baseline_equity']=='9800' and result['action']=='none')
controls.update(max_entry_deviation_pct='0',max_trade_volume='0.10',max_positions=2,max_signal_age_seconds=30)
flags=advanced_entry_check(controls,side='buy',source_entry='1',bid='.98',ask='.99',lots='.11',positions_and_entries=2,signal_time='2026-11-18T15:59:00Z',now=now)
check('better entry allowed volume skipped manual-inclusive slotswait and oldsignalneedsfreshcheck',flags=={'entry_price':'pass','volume':'skip','positions':'wait','signal_age':'refresh_source'})
emit_result(json.dumps({'count':len(checks),'passed':checks,'network_access':False,'broker_writes':False,'scope':'Pure M3 policy/control domain; no app/API/native read integration'},indent=2)+'\n')
print('Completed '+str(len(checks))+' offline policy/control checks')
