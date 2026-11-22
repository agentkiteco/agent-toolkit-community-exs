"""Offline recorded-report checks. No sockets, account credentials, broker or cloud."""
import copy,csv,io,json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'assets'/'reporting'))
from recorded_reports import *
def emit_result(value):
 if '--output' in sys.argv:Path(sys.argv[sys.argv.index('--output')+1]).write_text(value)
ROOT=Path(__file__).resolve().parent;checks=[]
START='2026-11-01T00:00:00Z';END='2026-12-01T00:00:00Z'
def check(name,condition=True):
 assert condition,name
 checks.append(name);print('PASS '+name,flush=True)
def row(id,kind='close',profit='100',commission='-1',*,account='1001',currency='USD',position='5001',at='2026-11-05T12:00:00Z'):
 deal={'deal_id':id,'type':kind,'position_id':position,'order_id':str(int(id)+10000),'volume':'0.10','price':'1.12345','create_time':at}
 if profit is not None:deal['profit']={'amount':profit,'currency':currency}
 if commission is not None:deal['commission']=commission
 return normalize_native(account,currency,[{'event_time':at,'deal':deal}])[0]
def report(rows,**kw):return build_report(rows,account_id=kw.pop('account_id','1001'),currency=kw.pop('currency','USD'),start=START,end=END,**kw)
def denied(fn):
 try:fn()
 except ReportError:return True
 return False
try:
 r=row('1',profit='10000000000000000.12345678');check('native monetary precision remains decimal strings',r['profit_amount']=='10000000000000000.12345678')
 opening=row('2','open','0','-2');close=row('3');swap=row('4','swap_fee','-3',None);admin=row('5','admin_fee','-4',None);fund=row('6','balance','1000',None,position=None);comp=row('7','null_compensation','5',None,position=None)
 result=report([opening,close,swap,admin,fund,comp]);check('signed posted net includes opening close swap admin and excludes funding compensation',result['totals']['trading_net']=='90' and result['totals']['funding']=='1000' and result['totals']['null_compensation']=='5')
 check('opening fee on an unclosed position is a current period cost',report([opening])['totals']['trading_net']=='-2')
 missingfund=row('8','balance',None,None,position=None);r=report([close,missingfund]);check('unknown funding remains unknown separately without inventing trading fees',r['totals']['trading_net']=='99' and r['totals']['funding'] is None)
 missing=row('9',commission=None);r=report([missing]);check('missing commission display zero never makes complete net zero-filled',r['totals']['trading_net'] is None and r['records'][0]['commission_display']['calculation_value'] is None and r['records'][0]['commission_display']['value']=='0')
 r=report([row('10',profit=None)]);check('missing close profit is unavailable with known subtotal separate',r['totals']['gross_close_profit'] is None and r['totals']['known_gross_close_profit']=='0' and r['totals']['trading_net'] is None)
 check('unclassified financial deal withholds net',report([row('11','dividend','10',None)])['totals']['trading_net'] is None)
 duplicate=copy.deepcopy(close);duplicate['source']='websocket';before=copy.deepcopy([close,duplicate]);r=report([close,duplicate]);check('account deal identity deduplicates REST WS without modifying originals',r['pagination']['unique_matching_records']==1 and r['totals']['trading_net']=='99' and [close,duplicate]==before)
 sparse=copy.deepcopy(close);sparse['commission']=None;r=report([sparse,close]);check('sparse unknown and explicit fee merge without fabricating a second charge',r['totals']['trading_net']=='99' and len(r['records'][0]['versions'])==2)
 conflict=copy.deepcopy(close);conflict['commission']='-2';r=report([close,conflict]);check('conflicting fees withhold net but retain known gross and all versions',r['totals']['trading_net'] is None and r['totals']['known_gross_close_profit']=='100' and r['totals']['commissions'] is None and len(r['records'][0]['versions'])==2)
 equivalent=copy.deepcopy(close);equivalent['commission']='-1.00';equivalent['event_time']='2026-11-05T12:00:00+00:00';r=report([close,equivalent]);check('equivalent decimal and UTC formatting does not create a financial conflict',not r['records'][0]['conflict_fields'] and r['totals']['trading_net']=='99')
 shifted=copy.deepcopy(close);shifted['event_time']='2026-10-31T23:59:59Z';r=report([shifted,close]);check('conflicting posting times do not silently drop in-period evidence',r['pagination']['unique_matching_records']==1 and r['totals']['trading_net'] is None)
 r=report([close,duplicate,opening],page_size=1);check('dedup precedes result pagination and totals',r['pagination']['unique_matching_records']==2 and r['pagination']['has_more'] and r['totals']['trading_net']=='97')
 oldopen=row('12','open','0','-2',at='2026-10-05T12:00:00Z');oldopen.update(account_type='Raw',account_type_asof='2026-09-01T00:00:00Z',account_type_verified=True)
 omitted=row('13',profit='50',commission=None);r=report([oldopen,omitted]);check('dated Raw opening evidence resolves missing close fee without recharging outside-period fee',r['totals']['trading_net']=='50' and r['records'][0]['commission_effective']=='0' and r['records'][0]['commission_raw'] is None)
 currentopen=copy.deepcopy(oldopen);currentopen['event_time']='2026-11-02T12:00:00Z';part1=row('14',profit='30',commission=None);part2=row('15',profit='20',commission=None);r=report([currentopen,part1,part2]);check('multiple partial closes never repeat recorded opening fee',r['totals']['trading_net']=='48' and r['totals']['commissions']=='-2')
 variants=[]
 for edit in ({'account_id':'2001'},{'commission_currency':'JPY'},{'event_time':'2026-11-10T12:00:00Z'},{'account_type_verified':False}):
  altered=copy.deepcopy(oldopen);altered.update(edit);variants.append(report([altered,omitted])['totals']['trading_net'] is None)
 check('included-opening inference rejects wrong account currency late or unverified evidence',all(variants))
 explicit=copy.deepcopy(omitted);explicit['commission']='-1';check('explicit close commission wins over included-at-opening inference',report([oldopen,explicit])['totals']['trading_net']=='49')
 mapping={'account_id':'1001','position_id':'5001','status':'closed','strategy_id':'strategy-a','subscription_id':'sub-a'};manual=row('16',profit='50',commission='0',position='5999')
 r=report([opening,close,manual],scope='copying',mappings=[mapping],strategy_id='strategy-a');check('closed confirmed mappings attribute copies while manual exposure is excluded',r['totals']['trading_net']=='97' and r['pagination']['unique_matching_records']==2)
 unknown={**mapping,'status':'unknown'};check('unconfirmed mapping never adopts matching account exposure',report([close],scope='copying',mappings=[unknown])['totals']['trading_net'] is None)
 ambiguous={**mapping,'subscription_id':'sub-b'};r=report([close],scope='copying',mappings=[mapping,ambiguous]);check('conflicting exact attribution cannot create a complete copied result',r['totals']['trading_net'] is None and r['issues'])
 second=row('17',profit='1000',commission='-10',account='2001',currency='JPY',position='6001');maps=[mapping,{'account_id':'2001','position_id':'6001','status':'confirmed','strategy_id':'strategy-a','subscription_id':'sub-jpy'}]
 r=provider_copying_reports([close,second,manual],accounts={'1001':'USD','2001':'JPY'},mappings=maps,strategy_id='strategy-a',start=START,end=END,pseudonym_secret=b'provider-scoped-secret-123')
 check('provider copying output anonymizes investors and separates currencies',len(r['by_currency'])==2 and all('account_id' not in x and x['investor'].startswith('Investor ') for x in r['investors']) and {x['currency']:x['trading_net'] for x in r['by_currency']}=={'USD':'99','JPY':'990'})
 unlinkedfee=row('18','swap_fee','-3',None,position=None);unlinkedfee['order_id']=None;r=report([close,unlinkedfee],scope='copying',mappings=[mapping]);check('unattributed trading fee holds copied net rather than assuming unrelated manual cost',r['totals']['trading_net'] is None and r['unattributed_fee_records']==1)
 empty=report([]);check('no saved trading records does not invent a zero-period result',empty['totals']['trading_net'] is None and not empty['totals']['has_recorded_trading'] and not empty['coverage']['full_period_return_available'])
 commands=[{'request_id':'open-01','kind':'open','status':'confirmed','target_volume':'0.02','confirmed_position_ids':['7001'],'submitted_entry_evidence':True,'average_entry_price':'1.1234','dispatched':True}, {'request_id':'close-01','kind':'partial-close','status':'confirmed','target_volume':'0.02','requested_close_volume':'0.01','dispatched':True}, {'request_id':'protect-01','kind':'protection','status':'confirmed','target_volume':'0.02','dispatched':True}, {'request_id':'pending-01','kind':'pending-open','status':'confirmed','target_volume':'0.02','dispatched':True}, {'request_id':'full-01','kind':'full-close','status':'confirmed','dispatched':True}]
 q=quality_rows(commands);check('quality volume describes actual operation without invented protection or full-close lots',q[1]['requested_volume']=='0.01' and q[2]['requested_volume'] is None and q[4]['requested_volume_state']=='full_remaining' and q[3]['entry_average_state']=='not_applicable')
 q=quality_rows([{**commands[0],'status':'unknown'},{**commands[0],'status':'rejected'},{**commands[0],'submitted_entry_evidence':False}]);check('entry average distinguishes not confirmed not executed and not recorded', [x['entry_average_state'] for x in q]==['not_confirmed','not_executed','not_recorded'])
 q=quality_rows(commands);check('only exact confirmed single-position entry exposes an entry average',q[0]['entry_average']=='1.1234' and all(x['entry_average'] is None for x in q[1:]))
 csvrows=list(csv.DictReader(io.StringIO(financial_csv(report([oldopen,omitted])))));check('CSV preserves raw missing commission blank versus effective zero and basis',csvrows[0]['commission_raw']=='' and csvrows[0]['commission_effective']=='0' and 'included_at_opening' in csvrows[0]['commission_basis'])
 csvq=list(csv.DictReader(io.StringIO(quality_csv(commands))));check('quality CSV leaves unavailable numerics blank and retains raw target volume',csvq[2]['requested_volume']=='' and csvq[2]['target_volume_raw']=='0.02' and csvq[3]['entry_average']=='')
 summ=quality_summary([commands[0],{**commands[0],'status':'unknown'},{**commands[0],'status':'rejected'},{**commands[0],'status':'skipped','dispatched':False}]);check('copy quality denominator is explicitly dispatched operations with no fake empty ratio',summ['dispatched_operations']==3 and summ['confirmation_ratio']==str(Decimal(1)/3) and quality_summary([])['confirmation_ratio'] is None)
 bad=copy.deepcopy(close);bad['profit_amount']=1.1;check('non-string money and negative operation volume are rejected',denied(lambda:report([bad])) and denied(lambda:quality_rows([{**commands[0],'target_volume':'-1'}])))
 posting=row('19',profit='10',commission='0');posting['raw']['deal']['create_time']='2026-10-01T00:00:00Z';atend=row('20',profit='99',commission='0',at=END);check('posting event time and half-open period govern money inclusion',report([posting,atend])['totals']['trading_net']=='10')
 r=report([missing],history_complete=True);check('requested-history completion cannot override unknown fee or imply full-period return',r['coverage']['history_complete'] and not r['coverage']['saved_components_complete'] and not r['coverage']['full_period_return_available'])
 cent=copy.deepcopy(close);cent['profit_currency']='USDc';check('cent and ordinary currency never silently combine',report([cent])['totals']['trading_net'] is None)
finally:
 emit_result(json.dumps({'count':len(checks),'passed':checks,'network_access':False,'app_integration':False,'scope':'Offline normalized recorded-report/calculation/CSV helpers only; parent executes'},indent=2))
