"""Recorded-evidence reports. No broker I/O, tariffs, currency conversion or trading."""
import copy,csv,hashlib,hmac,io,json,re
from datetime import datetime,timezone,timedelta
from decimal import Decimal,InvalidOperation

class ReportError(ValueError):pass
TRADING={'open','close','swap_fee','admin_fee'}
FIELDS=('account_id','deal_id','event_time','type','position_id','order_id','instrument','volume','price','profit_amount','profit_currency','commission','commission_currency','account_type','account_type_asof','account_type_verified')

def amount(value):
 if value is None:return None
 if not isinstance(value,str) or not re.fullmatch(r'[+-]?[0-9]+(?:\.[0-9]+)?',value):raise ReportError('Money/volume must be a plain decimal string')
 try:d=Decimal(value)
 except InvalidOperation:raise ReportError('Invalid decimal') from None
 if not d.is_finite():raise ReportError('Finite decimal required')
 return d

def stamp(value):
 try:d=datetime.fromisoformat(value.replace('Z','+00:00'))
 except (ValueError,AttributeError):raise ReportError('Original timezone-aware event time required') from None
 if d.tzinfo is None:raise ReportError('Original timezone-aware event time required')
 return d.astimezone(timezone.utc)

def identifier(value):
 if not isinstance(value,str) or not re.fullmatch(r'[1-9][0-9]{0,19}',value) or int(value)>2**64-1:raise ReportError('Canonical uint64 string identifier required')
 return value

def text_number(value):return str(value) if value is not None else None

def normalize_native(account_id,account_currency,items,*,source='rest',account_type=None,account_type_asof=None,account_type_verified=False):
 """Only the documented event_time/deal/commission/profit shape; no alias guessing.
 Scalar native commission is denominated in the explicitly verified account currency.
 Profit currency remains the native field; missing is unknown, never inferred.
 """
 identifier(account_id)
 if not isinstance(account_currency,str) or not account_currency:raise ReportError('Verified account currency required')
 rows=[]
 for item in items:
  if not isinstance(item,dict) or not isinstance(item.get('deal'),dict):raise ReportError('Native history item/deal required')
  d=item['deal'];identifier(d.get('deal_id'));stamp(item.get('event_time'))
  if not isinstance(d.get('type'),str):raise ReportError('Native deal type required')
  p=d.get('profit')
  if p is not None and not isinstance(p,dict):raise ReportError('Native profit structure required')
  p=p or {}
  row={'account_id':account_id,'deal_id':d['deal_id'],'event_time':item['event_time'],'type':d['type'],
       'position_id':d.get('position_id'),'order_id':d.get('order_id'),'instrument':d.get('instrument'),
       'volume':d.get('volume'),'price':d.get('price'),'profit_amount':p.get('amount'),'profit_currency':p.get('currency'),
       'commission':d.get('commission'),'commission_currency':account_currency,'account_type':account_type,
       'account_type_asof':account_type_asof,'account_type_verified':account_type_verified is True,
       'source':source,'raw':copy.deepcopy(item)}
  validate(row);rows.append(row)
 return rows

def validate(row):
 identifier(row.get('account_id'));identifier(row.get('deal_id'));stamp(row.get('event_time'))
 for field in ('position_id','order_id'):
  if row.get(field) is not None:identifier(row[field])
 for field in ('volume','price','profit_amount','commission'):amount(row.get(field))
 if row.get('volume') is not None and amount(row['volume'])<0:raise ReportError('Negative deal volume')
 if row.get('account_type_asof') is not None:stamp(row['account_type_asof'])
 if not isinstance(row.get('type'),str):raise ReportError('Deal type required')

def deduplicate(records):
 """Merge sparse complementary evidence; explicit contradictory values remain conflict.
 Return all retained versions; no mutation of input or last-write-wins rewriting.
 """
 unique={}
 for original in records:
  validate(original);key=(original['account_id'],original['deal_id']);version=copy.deepcopy(original)
  if key not in unique:
   unique[key]={**version,'versions':[version],'conflict_fields':[],'event_times':[version['event_time']]};continue
  saved=unique[key]
  if version not in saved['versions']:saved['versions'].append(version)
  if version['event_time'] not in saved['event_times']:saved['event_times'].append(version['event_time'])
  for field in FIELDS:
   old,new=saved.get(field),version.get(field)
   if old is None and new is not None:saved[field]=new
   elif old is not None and new is not None:
    equal=amount(old)==amount(new) if field in {'volume','price','profit_amount','commission'} else stamp(old)==stamp(new) if field in {'event_time','account_type_asof'} else old==new
    if not equal and field not in saved['conflict_fields']:saved['conflict_fields'].append(field)
  # An account type is verified only when nonconflicting evidence explicitly says so.
  if 'account_type_verified' in saved['conflict_fields']:saved['account_type_verified']=False
 return sorted(unique.values(),key=lambda r:(min(stamp(t) for t in r['event_times']),r['account_id'],r['deal_id']))

def _attribution(row,mappings,strategy_id=None,subscription_id=None):
 hits=[]
 for m in mappings:
  if not (m.get('ownership_confirmed') is True or m.get('status') in {'confirmed','closed'}) or m.get('account_id')!=row['account_id']:continue
  if not any(row.get(field) is not None and m.get(field)==row[field] for field in ('deal_id','order_id','position_id')):continue
  hits.append((m.get('strategy_id'),m.get('subscription_id')))
 if len(set(hits))>1:return 'ambiguous'
 if not hits:return None
 strategy,subscription=hits[0]
 if strategy_id is not None and strategy!=strategy_id:return None
 if subscription_id is not None and subscription!=subscription_id:return None
 return {'strategy_id':strategy,'subscription_id':subscription}

def _opening_basis(close,all_rows,currency):
 matches=[r for r in all_rows if r['account_id']==close['account_id'] and r.get('position_id') is not None and r.get('position_id')==close.get('position_id') and r['type']=='open']
 if not matches:return None
 for r in matches:
  fee=amount(r.get('commission'))
  if r['conflict_fields'] or r.get('account_type') not in {'Zero','Raw'} or r.get('account_type_verified') is not True or not r.get('account_type_asof') or stamp(r['account_type_asof'])>stamp(r['event_time']) or stamp(r['event_time'])>stamp(close['event_time']) or r.get('commission_currency')!=currency or fee is None or fee>=0:return None
 return {'kind':'included_at_opening','opening_deal_ids':[r['deal_id'] for r in matches],'raw_close_commission':None}

def build_report(records,*,account_id,currency,start,end,scope='whole-account',mappings=(),strategy_id=None,subscription_id=None,history_complete=False,page=1,page_size=50):
 """Native-currency saved-record report. Caller authenticates account/scope FIRST.
 Interval completeness and saved-component completeness remain separate.
 """
 identifier(account_id);begin,finish=stamp(start),stamp(end)
 if begin>=finish or not isinstance(currency,str) or not currency:raise ReportError('Valid half-open UTC period/currency required')
 if scope not in {'whole-account','copying'} or type(page)!=int or page<1 or type(page_size)!=int or not 1<=page_size<=200:raise ReportError('Invalid report scope/pagination')
 rows=deduplicate([r for r in records if r.get('account_id')==account_id]);selected=[];issues=[]
 sums={k:Decimal(0) for k in ('gross_close_profit','commissions','swap','admin','funding','null_compensation')}
 complete={k:True for k in sums}
 relevant_mapping=any(m.get('account_id')==account_id and (m.get('ownership_confirmed') is True or m.get('status') in {'confirmed','closed'}) and (strategy_id is None or m.get('strategy_id')==strategy_id) and (subscription_id is None or m.get('subscription_id')==subscription_id) for m in mappings)
 components_complete=True;ambiguous_unattributed=0
 for row in rows:
  if not any(begin<=stamp(t)<finish for t in row['event_times']):continue
  attribution=_attribution(row,mappings,strategy_id,subscription_id)
  if scope=='copying' and {'position_id','order_id'}&set(row['conflict_fields']):attribution='ambiguous'
  if scope=='copying':
   if attribution=='ambiguous':issues.append({'deal_id':row['deal_id'],'cause':'Ambiguous confirmed attribution'});components_complete=False;continue
   if not attribution:
    if relevant_mapping and row['type'] in {'swap_fee','admin_fee'} and not row.get('position_id') and not row.get('order_id'):
     ambiguous_unattributed+=1;components_complete=False;issues.append({'deal_id':row['deal_id'],'cause':'Fee has no exact copying attribution'})
    continue
  out={field:row.get(field) for field in FIELDS};out.update(versions=copy.deepcopy(row['versions']),conflict_fields=list(row['conflict_fields']),attribution=attribution,commission_raw=row.get('commission'),commission_effective=None,commission_basis=None,profit_effective=None,component_status='complete')
  bad=[];kind=row['type'];conflicted=bool(row['conflict_fields'])
  def known_profit(bucket):
   value=amount(row.get('profit_amount'))
   if {'type','event_time','profit_amount','profit_currency'}&set(row['conflict_fields']):complete[bucket]=False;bad.append('Conflicting '+bucket+' evidence');return
   if value is None or row.get('profit_currency')!=currency:complete[bucket]=False;bad.append('Missing or mismatched '+bucket+' currency/amount');return
   sums[bucket]+=value;out['profit_effective']=str(value)
  if conflicted:bad.append('Conflicting retained versions: '+','.join(row['conflict_fields']))
  if kind=='close':known_profit('gross_close_profit')
  elif kind=='open':
   value=amount(row.get('profit_amount'))
   # A missing opening profit is not silently invented. It does not normally form gross close P/L.
   if value is not None and (value!=0 or row.get('profit_currency')!=currency):bad.append('Unclassified opening profit or currency')
  elif kind=='swap_fee':known_profit('swap')
  elif kind=='admin_fee':known_profit('admin')
  elif kind=='balance':known_profit('funding')
  elif kind=='null_compensation':known_profit('null_compensation')
  else:bad.append('Unclassified financial deal type '+kind)
  if kind in TRADING:
   commission=amount(row.get('commission'))
   if {'type','event_time','commission','commission_currency'}&set(row['conflict_fields']):complete['commissions']=False;bad.append('Conflicting commission evidence')
   elif commission is not None:
    if row.get('commission_currency')!=currency:complete['commissions']=False;bad.append('Commission currency mismatch')
    else:sums['commissions']+=commission;out.update(commission_effective=str(commission),commission_basis='explicit')
   elif kind=='close':
    basis=_opening_basis(row,rows,currency)
    if basis:out.update(commission_effective='0',commission_basis=basis)
    else:complete['commissions']=False;bad.append('No close commission reported')
   elif kind=='open':complete['commissions']=False;bad.append('No opening commission reported')
  # Non-trading unknown funding/compensation does not make trading net unknown.
  if bad:
   out['component_status']='unavailable';out['issues']=bad
   issues.extend({'deal_id':row['deal_id'],'cause':x} for x in bad)
   if kind not in {'balance','null_compensation'}:components_complete=False
  for field in ('profit_amount','commission'):
   if row.get(field) is None:out[field+'_display']={'value':'0','label':'No amount reported / shown as 0','calculation_value':None}
  selected.append(out)
 has_trading=any(r['type'] in TRADING for r in selected)
 net=sums['gross_close_profit']+sums['commissions']+sums['swap']+sums['admin'] if components_complete and has_trading else None
 totals={k:(str(v) if complete[k] else None) for k,v in sums.items()};totals.update({'known_'+k:str(v) for k,v in sums.items()});totals['component_availability']=complete;totals['has_recorded_trading']=has_trading;totals.update(trading_net=text_number(net),net_realized=None,saved_components_complete=components_complete,net_realized_reason='Period cash net is distinct from closed-position realized net')
 # A cumulative result can be shown only from complete saved components, never as a return percentage.
 curve=[];running=Decimal(0)
 if components_complete:
  for r in selected:
   if r['type'] not in TRADING:continue
   change=Decimal(0)
   if r['type'] in {'close','swap_fee','admin_fee'}:change+=amount(r.get('profit_effective')) or Decimal(0)
   change+=amount(r.get('commission_effective')) or Decimal(0);running+=change;curve.append({'event_time':r['event_time'],'recorded_net':str(running)})
 offset=(page-1)*page_size
 return {'scope':scope,'account_id':account_id,'currency':currency,'period':{'from':begin.isoformat(),'to':finish.isoformat(),'boundary':'from inclusive / to exclusive'},'totals':totals,'coverage':{'history_complete':history_complete is True,'saved_components_complete':components_complete,'label':'Complete requested history reported by caller' if history_complete is True else 'Partial/unknown historical coverage','full_period_return_available':False},'issues':issues,'unattributed_fee_records':ambiguous_unattributed,'recorded_curve':curve,'records':selected[offset:offset+page_size],'pagination':{'page':page,'page_size':page_size,'unique_matching_records':len(selected),'has_more':offset+page_size<len(selected)}}

def provider_copying_reports(records,*,accounts,mappings,strategy_id,start,end,pseudonym_secret,coverage_by_account=None):
 """Aggregate projection only; no raw investor IDs/records or unrelated accounts.
 accounts={authorized investor account: verified currency}. No cross-currency sum.
 """
 if not isinstance(pseudonym_secret,bytes) or len(pseudonym_secret)<16:raise ReportError('Provider-scoped pseudonym secret required')
 projected=[];groups={};coverage_by_account=coverage_by_account or {}
 for account,currency in accounts.items():
  report=build_report(records,account_id=account,currency=currency,start=start,end=end,scope='copying',mappings=mappings,strategy_id=strategy_id,history_complete=coverage_by_account.get(account,False))
  if not report['pagination']['unique_matching_records'] and not report['issues']:continue
  label='Investor '+hmac.new(pseudonym_secret,(strategy_id+'\0'+account).encode(),hashlib.sha256).hexdigest()[:12]
  projected.append({'investor':label,'currency':currency,'totals':report['totals'],'coverage':report['coverage']})
  group=groups.setdefault(currency,{'currency':currency,'known_gross':Decimal(0),'known_commissions':Decimal(0),'known_swap':Decimal(0),'known_admin':Decimal(0),'complete':True,'history_complete':True,'investors':0})
  for src,dst in [('gross_close_profit','known_gross'),('commissions','known_commissions'),('swap','known_swap'),('admin','known_admin')]:group[dst]+=amount(report['totals']['known_'+src])
  group['complete']=group['complete'] and report['totals']['saved_components_complete'];group['history_complete']=group['history_complete'] and report['coverage']['history_complete'];group['investors']+=1
 result=[]
 for group in groups.values():
  net=sum((group[k] for k in ('known_gross','known_commissions','known_swap','known_admin')),Decimal(0)) if group['complete'] else None
  result.append({**{k:(str(v) if isinstance(v,Decimal) else v) for k,v in group.items()},'trading_net':text_number(net)})
 return {'strategy_id':strategy_id,'investors':projected,'by_currency':result,'methodology':'Exactly mapped recorded copied deals; no funding, manual exposure or cross-currency total'}

def _calendar_intervals(records,start,end):
 """Only observed UTC buckets; never fill absent days/months with invented zero."""
 begin,finish=stamp(start),stamp(end);days=set();months=set()
 for row in deduplicate(records):
  for value in row['event_times']:
   at=stamp(value)
   if begin<=at<finish:days.add(at.replace(hour=0,minute=0,second=0,microsecond=0));months.add(at.replace(day=1,hour=0,minute=0,second=0,microsecond=0))
 for kind,values in (('daily',days),('monthly',months)):
  for at in sorted(values):
   after=at+timedelta(days=1) if kind=='daily' else at.replace(year=at.year+1,month=1) if at.month==12 else at.replace(month=at.month+1)
   yield kind,at.strftime('%Y-%m-%d' if kind=='daily' else '%Y-%m'),max(at,begin).isoformat(),min(after,finish).isoformat()

def period_summaries(records,*,account_id,currency,start,end,scope='whole-account',mappings=(),strategy_id=None):
 """Same signed posted-component calculation as the overall report, per UTC bucket."""
 rows=[r for r in records if r.get('account_id')==account_id];result={'daily':[],'monthly':[]}
 for kind,label,begin,finish in _calendar_intervals(rows,start,end):
  report=build_report(rows,account_id=account_id,currency=currency,start=begin,end=finish,scope=scope,mappings=mappings,strategy_id=strategy_id,history_complete=False)
  if report['pagination']['unique_matching_records'] or report['issues']:result[kind].append({'period':label,'from':begin,'to':finish,'currency':currency,'totals':report['totals'],'coverage':report['coverage'],'issues':report['issues']})
 return result

def provider_period_summaries(records,*,accounts,mappings,strategy_id,start,end,pseudonym_secret):
 """Provider gets currency aggregates only; never raw account/deal-level periods."""
 rows=[r for r in records if r.get('account_id') in accounts];result={'daily':[],'monthly':[]}
 for kind,label,begin,finish in _calendar_intervals(rows,start,end):
  report=provider_copying_reports(rows,accounts=accounts,mappings=mappings,strategy_id=strategy_id,start=begin,end=finish,pseudonym_secret=pseudonym_secret)
  for group in report['by_currency']:result[kind].append({'period':label,'from':begin,'to':finish,**group})
 return result

def quality_rows(commands):
 rows=[]
 for c in commands:
  kind=c.get('kind');status=c.get('status');raw=c.get('target_volume');amount(raw);close=c.get('requested_close_volume');amount(close)
  if kind not in {'open','pending-open','close','partial-close','full-close','protection','pending-edit','pending-cancel'} or status not in {'checking','prepared','confirmed','unknown','rejected','skipped','failed'}:raise ReportError('Unsupported normalized operation kind/status')
  if c.get('request_id') is not None and not re.fullmatch(r'[A-Za-z0-9._~-]{5,128}',c['request_id']):raise ReportError('Invalid retained request identity')
  for value in (raw,close):
   if value is not None and amount(value)<=0:raise ReportError('Positive operation volume required')
  for position in c.get('confirmed_position_ids',[]):identifier(position)
  volume=None;volume_state='not_applicable'
  if kind in {'open','pending-open'}:volume=raw;volume_state='recorded' if raw is not None else 'not_recorded'
  elif kind in {'close','partial-close','full-close'}:
   volume=close;volume_state='recorded' if close is not None else 'not_recorded' if kind=='partial-close' else 'full_remaining'
  entry=None
  if kind!='open':entry_state='not_applicable'
  elif status in {'skipped','rejected'}:entry_state='not_executed'
  elif status!='confirmed':entry_state='not_confirmed'
  elif c.get('submitted_entry_evidence') is not True or len(set(c.get('confirmed_position_ids',[])))!=1:entry_state='not_recorded'
  elif c.get('average_entry_price') is None:entry_state='not_recorded'
  else:
   entry=c['average_entry_price']
   if amount(entry)<=0:raise ReportError('Positive confirmed entry average required')
   entry_state='recorded'
  rows.append({'request_id':c.get('request_id'),'kind':kind,'status':status,'target_volume_raw':raw,'requested_volume':volume,'requested_volume_state':volume_state,'entry_average':entry,'entry_average_state':entry_state,'dispatched':c.get('dispatched') is True})
 return rows

def quality_summary(commands):
 rows=quality_rows(commands);sent=[r for r in rows if r['dispatched']];confirmed=sum(r['status']=='confirmed' for r in sent)
 return {'recorded_operations':len(rows),'dispatched_operations':len(sent),'confirmed_dispatched':confirmed,'unknown_dispatched':sum(r['status']=='unknown' for r in sent),'rejected_dispatched':sum(r['status']=='rejected' for r in sent),'skipped_operations':sum(r['status']=='skipped' for r in rows),'confirmation_ratio':str(Decimal(confirmed)/len(sent)) if sent else None,'denominator':'Explicitly dispatched recorded operations only'}

def _csv(rows,fields):
 target=io.StringIO(newline='');writer=csv.DictWriter(target,fieldnames=fields,extrasaction='ignore');writer.writeheader()
 for row in rows:
  writer.writerow({k:('' if row.get(k) is None else json.dumps(row[k],sort_keys=True) if isinstance(row.get(k),(dict,list)) else row[k]) for k in fields})
 return target.getvalue()

def financial_csv(report):
 return _csv(report['records'],['account_id','deal_id','event_time','type','position_id','order_id','volume','price','profit_amount','profit_currency','commission_raw','commission_effective','commission_basis','commission_currency','component_status','conflict_fields','versions'])

def quality_csv(commands):
 return _csv(quality_rows(commands),['request_id','kind','status','target_volume_raw','requested_volume','requested_volume_state','entry_average','entry_average_state','dispatched'])
