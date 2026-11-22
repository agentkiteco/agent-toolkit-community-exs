"""Account-scoped conversion references. Executable ticks stay independently mandatory."""
from datetime import datetime,timezone,timedelta
from decimal import Decimal
import time
from urllib.parse import urlencode
FIAT=set('USD EUR GBP JPY CHF AUD NZD CAD SEK NOK DKK SGD HKD PLN CZK HUF TRY ZAR MXN CNH CNY BRL THB ILS AED SAR RON BGN INR KRW IDR MYR PHP TWD CLP COP PEN ISK RUB'.split())
def number(v):
    value=Decimal(str(v))
    if not value.is_finite():raise ValueError('Nonfinite conversion value')
    return value

def stamp(v):
    d=datetime.fromisoformat(v.replace('Z','+00:00'))
    if d.tzinfo is None:raise ValueError('Original conversion timestamp required')
    return d.astimezone(timezone.utc)
class Conversion:
    def __init__(self,broker):self.broker=broker;self.cache={}
    def reference(self,a,symbol):
        key=(a['id'],symbol);cached=self.cache.get(key)
        if cached and cached['expires']>time.monotonic():
            if 'error' in cached:raise ValueError(cached['error'])
            return cached['reference']
        now=datetime.now(timezone.utc);result=None
        try:
            for timeframe,window in (('M1',timedelta(hours=1)),('D1',timedelta(days=7))):
                start=(now-window).isoformat();end=now.isoformat()
                if hasattr(self.broker,'client'):data=self.broker.client(a).candles(a['id'],symbol,timeframe,start,end)
                else:data=self.broker.read(a,'candles/'+symbol+'?'+urlencode({'timeframe':timeframe,'from_time':start,'to_time':end}))
                if not isinstance(data.get('items'),list):raise ValueError('Conversion candle collection is malformed')
                valid=[]
                for row in data['items']:
                    try:
                        at=stamp(row['open_time']);bid=number(row['bid_close']);ask=number(row['ask_close']);age=(now-at).total_seconds()
                        if 0<=age<=min(7*86400,window.total_seconds()) and 0<bid<=ask:valid.append((at,bid,ask))
                    except (KeyError,ValueError,TypeError):continue
                if valid:
                    at,bid,ask=max(valid,key=lambda x:x[0]);result={'bid':str(bid),'ask':str(ask),'source':'broker_candle_close','reference_only':True,'timeframe':timeframe,'open_time':at.isoformat(),'constituent_tick_time':None};break
            self.cache[key]={'expires':time.monotonic()+60,'reference':result};return result
        except Exception as error:
            # Access/quota/transport failures never turn into an automatic D1 retry.
            message='Conversion reference unavailable: '+str(error);self.cache[key]={'expires':time.monotonic()+60,'error':message};raise ValueError(message) from None
    def path(self,edges,start,end,purchase):
        queue=[(start,Decimal(1),[],{start})]
        for currency,rate,route,visited in queue:
            if len(route)>=2:continue
            for base,quote,symbol,value in edges:
                if currency==base:target=quote;leg=number(value['ask' if purchase else 'bid'])
                elif currency==quote:target=base;leg=1/number(value['bid' if purchase else 'ask'])
                else:continue
                if target in visited:continue
                evidence={**value,'instrument':symbol,'from_currency':currency,'to_currency':target,'rate':str(leg),'direction':'purchase' if purchase else 'sell'}
                if target==end:return rate*leg,route+[evidence]
                queue.append((target,rate*leg,route+[evidence],visited|{target}))
        return None
    def tick_reference(self, quote):
        bid, ask = number(quote['bid']), number(quote['ask'])
        now = datetime.now(timezone.utc)
        age = (now - stamp(quote['event_time'])).total_seconds()
        if not 0 < bid <= ask or age < 0 or stamp(quote['received_at']) > now:
            raise ValueError('Invalid/future original conversion tick')
        return {'bid':str(bid),'ask':str(ask),'source':'broker_tick' if age<=5 else 'broker_original_last_tick','original_age_seconds':str(age),'reference_only':False,'event_time':quote['event_time'],'received_at':quote['received_at']}

    def live_direct(self, account, source, target, purchase):
        synchronized = getattr(self.broker, 'sync_status', None)
        if synchronized is None:
            return None
        for symbol, quote in synchronized(account).get('ticks', {}).items():
            try:
                reference = self.tick_reference(quote)
            except (KeyError, TypeError, ValueError, ArithmeticError):
                continue
            if reference['source'] != 'broker_tick':
                continue
            contract = self.broker.read(account, 'instruments/'+symbol)
            if contract.get('instrument') != symbol:
                raise ValueError('Conversion instrument identity mismatch')
            base, counter = contract.get('base_currency'), contract.get('quote_currency')
            if {base, counter} == {source, target}:
                return self.path([(base,counter,symbol,reference)],source,target,purchase)
        return None

    def convert(self,a,source,target,purchase=False):
        if source==target:return Decimal(1),[]
        if source not in FIAT or target not in FIAT:raise ValueError('Unsupported non-fiat currency conversion; cent currencies are distinct')
        direct = self.live_direct(a, source, target, purchase)
        if direct:
            return direct
        inventory=self.broker.read(a,'instruments')['instruments'];ticks=[];unavailable=[]
        for symbol in inventory:
            contract=self.broker.client(a).conditions(a['id'],symbol) if hasattr(self.broker,'client') else self.broker.read(a,'instruments/'+symbol)
            if contract.get('instrument')!=symbol:raise ValueError('Conversion instrument identity mismatch')
            base=contract.get('base_currency');quote=contract.get('quote_currency')
            if base not in FIAT or quote not in FIAT or base==quote:continue
            try:
                ticks.append((base,quote,symbol,self.tick_reference(self.broker.read(a,'quotes/'+symbol))))
            except Exception as error:
                if getattr(error,'status',None) in (0,401,403,429,500,502,503,504):raise
                unavailable.append((base,quote,symbol))
        result=self.path(ticks,source,target,purchase)
        if result:return result
        references=[];causes=[]
        for base,quote,symbol in unavailable:
            try:value=self.reference(a,symbol)
            except ValueError as error:causes.append(str(error));continue
            if value:references.append((base,quote,symbol,value))
        result=self.path(ticks+references,source,target,purchase)
        if result:return result
        raise ValueError('No account-scoped conversion route '+source+' → '+target+(' ('+'; '.join(causes[:2])+')' if causes else ''))
