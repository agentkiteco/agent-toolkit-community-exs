"""Pure admission and control rules. Callers supply authenticated observations, not browser claims.
No network, credential storage, subscription activation or broker writes occur here.
"""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re

POLICY_KEYS = ('real_accounts_only', 'partner_accounts_only', 'same_currency_only', 'same_account_type_only')
ADVANCED_KEYS = ('max_entry_deviation_pct', 'max_trade_volume', 'max_positions', 'daily_loss_pct', 'max_signal_age_seconds')
_MISSING = object()

class PolicyError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def number(value):
    if isinstance(value, (bool, float)):
        raise PolicyError('Use an exact decimal string or integer')
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise PolicyError('A finite decimal value is required') from None
    if not result.is_finite():
        raise PolicyError('A finite decimal value is required')
    return result


def stamp(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (AttributeError, TypeError, ValueError):
        raise PolicyError('Timezone-aware original observation time required') from None
    if result.tzinfo is None:
        raise PolicyError('Timezone-aware original observation time required')
    return result.astimezone(timezone.utc)


def fresh(value, now, seconds=30):
    try:
        age = (stamp(now) - stamp(value)).total_seconds()
        return 0 <= age <= seconds
    except PolicyError:
        return False


def account_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[1-9][0-9]{0,19}', value) or int(value) > 2**64 - 1:
        raise PolicyError('Full canonical uint64 account string required')
    return value


def product_code(stream_id):
    """Owner-confirmed stream extension: final DOT-delimited code, case preserved."""
    if not isinstance(stream_id, str) or stream_id != stream_id.strip() or not stream_id:
        return None
    parts = stream_id.split('.')
    if any(not part or re.search(r'\s', part) for part in parts):
        return None
    return parts[-1]


def new_policy(owner, registered_identity=None):
    return {'owner': owner, 'registered_identity': registered_identity, 'revision': 0, 'settings': dict.fromkeys(POLICY_KEYS, False),
            'partner_verification': None, 'partner_evidence': {}, 'audit': []}


def save_policy(current, actor, expected_revision, patch, now, *, partner_access=None, verification_consent=False):
    """Atomic pure transform; caller commits under the same policy-revision lock after I/O."""
    if actor != current['owner']:
        raise PolicyError('Only this provider can change its account requirements', 403)
    if type(expected_revision) is not int or expected_revision != current['revision']:
        raise PolicyError('Account requirements changed; reload before saving', 409)
    if not isinstance(patch, dict) or set(patch) - set(POLICY_KEYS) or any(type(v) is not bool for v in patch.values()):
        raise PolicyError('Account requirements must be known strict booleans')
    result = deepcopy(current)
    before = deepcopy(result['settings'])
    result['settings'].update(patch)
    enabling = result['settings']['partner_accounts_only'] and not before['partner_accounts_only']
    if enabling:
        proof = partner_access or {}
        if verification_consent is not True or proof.get('provider_id') != current['owner'] or proof.get('status') != 'verified_report_access' or not proof.get('credential_ref') or not result.get('registered_identity') or proof.get('identity_fingerprint') != result['registered_identity'] or not fresh(proof.get('checked_at'), now):
            raise PolicyError('Consent and fresh report-access verification using registered provider credentials are required', 409)
        result['partner_verification'] = {k: proof[k] for k in ('credential_ref', 'identity_fingerprint', 'checked_at')}
    if not result['settings']['partner_accounts_only']:
        result['partner_verification'] = None
        result['partner_evidence'] = {}
    result['revision'] += 1
    result['audit'].append({'at': now, 'actor': actor, 'before': before, 'after': deepcopy(result['settings'])})
    return result


def membership_evidence(provider_id, policy_revision, selected_account, pages, now):
    """Consume TRUSTED request/response envelopes, not a native API alias.

    Each envelope has successful, provider_id, checked_at, query.client_account=[id],
    query.limit, query.offset, rows=[{client_account: str}], totals.count.
    I/O adapter extracts native row collection using the current official schema.
    Results contain no partner directory, email, client UID, API or signing key.
    """
    selected_account = account_id(selected_account)
    result = {'provider_id': provider_id, 'policy_revision': policy_revision,
              'account_id': selected_account, 'checked_at': None, 'attempted_at': now, 'status': 'pending', 'reason': 'Report verification pending'}
    if not isinstance(pages, list) or not pages:
        return result
    expected_offset = 0
    expected_limit = None
    expected_count = None
    observed = 0
    matching = False
    times = []
    for page in pages:
        if not isinstance(page, dict) or page.get('successful') is not True or page.get('provider_id') != provider_id or not fresh(page.get('checked_at'), now):
            return {**result, 'reason': 'Provider report unavailable or stale'}
        query = page.get('query', {})
        limit, offset = query.get('limit'), query.get('offset')
        if query.get('client_account') != [selected_account] or type(limit) is not int or not 1 <= limit <= 1000 or type(offset) is not int or offset != expected_offset:
            return {**result, 'reason': 'Exact selected-account filter or pagination could not be verified'}
        if expected_limit is not None and limit != expected_limit:
            return {**result, 'reason': 'Report request changed during pagination'}
        expected_limit = limit
        rows = page.get('rows')
        count = page.get('totals', {}).get('count')
        if not isinstance(rows, list) or len(rows) > limit or type(count) is not int or count < 0 or count < offset + len(rows):
            return {**result, 'reason': 'Malformed or incomplete filtered report'}
        if expected_count is not None and count != expected_count:
            return {**result, 'reason': 'Report changed during pagination'}
        expected_count = count
        for row in rows:
            if not isinstance(row, dict) or row.get('client_account') != selected_account:
                return {**result, 'reason': 'Report did not honor the exact account filter'}
            matching = True
        times.append(page['checked_at'])
        observed += len(rows)
        expected_offset += limit
    # Preserve the oldest actual response time rather than refreshing evidence to now.
    result['checked_at'] = min(times, key=stamp)
    if matching:
        return {**result, 'status': 'member', 'reason': 'Exact selected trading account is attributed to this provider'}
    if expected_count == 0 and observed == 0 and len(pages) == 1:
        return {**result, 'status': 'absent', 'reason': 'Complete exact-account report contains no selected account'}
    return {**result, 'reason': 'Filtered absence is not complete'}


def _verified(row, expected, now):
    try: account_id(expected)
    except PolicyError: return False
    return (isinstance(row, dict) and row.get('account_id') == expected and row.get('verified') is True
            and fresh(row.get('verified_at'), now))


def _fingerprint(investor, source, membership):
    raw = json.dumps({'investor': investor, 'source': source, 'membership': membership},
                     sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def admission(policy, context, investor, source=None, membership=None):
    """Pure admission. Context/observations must be server-derived and authenticated.

    context: provider_id, investor_account, source_account, strategy_id, transition, now.
    Native observations: account_id, verified=True, verified_at, raw is_demo/currency/stream_id.
    is_demo and stream_id interpretation is owner-confirmed, not a new API schema claim.
    """
    if context['provider_id'] != policy['owner']:
        raise PolicyError('Provider policy context mismatch', 403)
    transition = context['transition']
    if transition not in {'login', 'connection', 'readiness', 'start', 'legacy_start', 'resume', 'active_management', 'entry'}:
        raise PolicyError('Unknown admission boundary')
    selected = account_id(context['investor_account'])
    source_id = context.get('source_account')
    now = context['now']
    checks = {}
    if selected == source_id or transition in {'login', 'active_management', 'entry'}:
        return {'allowed': True, 'status': 'exempt', 'checks': {}, 'policy_revision': policy['revision'], 'reason': 'No new restricted admission transition'}
    applicable = ['real_accounts_only', 'partner_accounts_only']
    if transition != 'connection':
        applicable += ['same_currency_only', 'same_account_type_only']
    for name in applicable:
        if not policy['settings'][name]:
            continue
        status, reason = 'pending', 'Refresh verified account data'
        if name == 'partner_accounts_only':
            proof = membership or {}
            if (_verified(investor, selected, now) and proof.get('provider_id') == policy['owner'] and proof.get('policy_revision') == policy['revision']
                    and proof.get('account_id') == selected and fresh(proof.get('checked_at'), now)):
                if proof.get('status') == 'member': status, reason = 'pass', 'Selected account linked to provider partnership'
                elif proof.get('status') == 'absent': status, reason = 'block', 'Selected account is not linked to provider partnership'
            if not policy.get('partner_verification') or policy['partner_verification'].get('identity_fingerprint') != policy.get('registered_identity'):

                status, reason = 'pending', 'Provider report access must be verified'
        elif _verified(investor, selected, now):
            if name == 'real_accounts_only':
                if investor.get('is_demo') is False: status, reason = 'pass', 'Real account verified'
                elif investor.get('is_demo') is True: status, reason = 'block', 'Real trading account required'
                else: reason = 'Account type not verified; refresh Trading details'
            elif _verified(source, source_id, now):
                if name == 'same_currency_only':
                    left, right = investor.get('currency'), source.get('currency')
                    if isinstance(left, str) and left and left == left.strip() and not re.search(r'\s', left) and isinstance(right, str) and right and right == right.strip() and not re.search(r'\s', right):
                        status, reason = ('pass', 'Account currencies match') if left == right else ('block', 'Same account currency as the selected strategy required')
                else:
                    left, right = product_code(investor.get('stream_id')), product_code(source.get('stream_id'))
                    if left and right:
                        status, reason = ('pass', 'Account product codes match') if left == right else ('block', 'Same account type as the selected strategy required')
                    else: reason = 'Account product type not verified; refresh Trading details'
        checks[name] = {'status': status, 'reason': reason}
    status = 'block' if any(c['status'] == 'block' for c in checks.values()) else 'pending' if any(c['status'] == 'pending' for c in checks.values()) else 'pass'
    result = {'allowed': status == 'pass', 'status': status, 'checks': checks, 'policy_revision': policy['revision']}
    if result['allowed']:
        result['snapshot'] = {k: context.get(k) for k in ('provider_id', 'investor_account', 'source_account', 'strategy_id', 'transition')}
        result['snapshot'].update(policy_revision=policy['revision'], checked_at=now,
                                  evidence_fingerprint=_fingerprint(investor, source, membership))
    return result


def validate_admission(snapshot, policy, context, investor, source=None, membership=None):
    if not isinstance(snapshot, dict) or snapshot.get('policy_revision') != policy['revision'] or not fresh(snapshot.get('checked_at'), context['now']):
        raise PolicyError('Admission changed or expired; run checks again', 409)
    for name in ('provider_id', 'investor_account', 'source_account', 'strategy_id', 'transition'):
        if snapshot.get(name) != context.get(name):
            raise PolicyError('Admission binding changed; run checks again', 409)
    result = admission(policy, context, investor, source, membership)
    if not result['allowed'] or snapshot.get('evidence_fingerprint') != _fingerprint(investor, source, membership):
        raise PolicyError('Admission evidence changed; run checks again', 409)
    return result


def new_advanced():
    return {**dict.fromkeys(ADVANCED_KEYS), 'auto_close_daily_loss': False}


def _editable(subscription, actor, revision, confirmed):
    if actor != subscription['account']:
        raise PolicyError('Subscription belongs to another account', 403)
    if type(revision) is not int or revision != subscription.get('revision', 0):
        raise PolicyError('Subscription changed; reload before confirming', 409)
    if confirmed is not True:
        raise PolicyError('Explicit confirmation is required')
    if subscription.get('recovery_blocked') or any(c.get('status') in {'checking', 'prepared', 'unknown', 'pending', 'dispatched'} for c in subscription.get('commands', [])):
        raise PolicyError('Resolve unfinished operation evidence before editing', 409)
    if subscription['status'] not in {'active', 'paused'}:
        raise PolicyError('Only active or paused subscription controls can be edited', 409)


def edit_advanced(subscription, actor, revision, patch, now, *, confirmed=False, auto_close=None):
    _editable(subscription, actor, revision, confirmed)
    if not isinstance(patch, dict) or set(patch) - set(ADVANCED_KEYS):
        raise PolicyError('Unknown Advanced control')
    result = deepcopy(subscription)
    before = deepcopy(result.get('advanced', new_advanced()))
    controls = deepcopy(before)
    ranges = {'max_entry_deviation_pct': (Decimal(0), None), 'max_trade_volume': (Decimal('.01'), Decimal(2)),
              'max_positions': (Decimal(1), Decimal(10)), 'daily_loss_pct': (Decimal('.01'), Decimal(20)),
              'max_signal_age_seconds': (Decimal(10), Decimal(300))}
    for name, field in patch.items():
        if not isinstance(field, dict) or set(field) - {'enabled', 'value'} or type(field.get('enabled')) is not bool:
            raise PolicyError('Each edited control requires an explicit enabled boolean')
        if field['enabled']:
            if 'value' not in field:
                raise PolicyError('Enabled control requires an explicit value')
            value = number(field['value']); low, high = ranges[name]
            if value < low or high is not None and value > high or name in {'max_positions', 'max_signal_age_seconds'} and value != value.to_integral_value():
                raise PolicyError('Advanced value outside supported range')
            controls[name] = int(value) if name in {'max_positions', 'max_signal_age_seconds'} else str(value)
        else:
            controls[name] = None
    if controls['daily_loss_pct'] is None:
        controls['auto_close_daily_loss'] = False
    if auto_close is not None:
        if not isinstance(auto_close, dict) or set(auto_close) - {'enabled', 'consent'} or type(auto_close.get('enabled')) is not bool:
            raise PolicyError('Daily-loss automatic close needs an explicit boolean')
        if auto_close['enabled'] and (controls['daily_loss_pct'] is None or auto_close.get('consent') is not True):
            raise PolicyError('Daily loss and separate automatic-close consent are required')
        controls['auto_close_daily_loss'] = auto_close['enabled']
    result['advanced'] = controls
    result['revision'] = result.get('revision', 0) + 1
    result.setdefault('audit', []).append({'at': now, 'actor': actor, 'kind': 'advanced', 'before': before, 'after': deepcopy(controls)})
    return result


def _allocation(value):
    text = str(value)
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]{1,2})?', text) or sum(c.isdigit() for c in text) > 16 or number(text) <= 0:
        raise PolicyError('Allocation requires positive plain decimal, at most16digits/two decimals')
    return number(text)


def edit_copy_mode(subscription, actor, revision, mode, now, verified_equity, *, confirmed=False, allocation=_MISSING, multiplier=_MISSING):
    _editable(subscription, actor, revision, confirmed)
    if subscription['status'] != 'paused':
        raise PolicyError('Pause before changing copying mode', 409)
    if mode not in {'Proportional', '1:1'}:
        raise PolicyError('Unsupported copying mode')
    result = deepcopy(subscription)
    before = {key: result.get(key) for key in ('mode', 'amount', 'multiplier')}
    if mode == '1:1':
        if allocation is not _MISSING or multiplier is not _MISSING:
            raise PolicyError('Do not supply Proportional-only fields for1:1')
        result.update(mode='1:1', multiplier='1')
    else:
        amount = _allocation(subscription['amount'] if allocation is _MISSING else allocation)
        multiple = number(subscription.get('multiplier', '1') if multiplier is _MISSING else multiplier)
        if not Decimal('.01') <= multiple <= 2:
            raise PolicyError('Multiplier must be0.01to2')
        if amount > number(verified_equity):
            raise PolicyError('Sizing amount exceeds verified investor equity')
        result.update(mode=mode, amount=str(amount), multiplier=str(multiple))
    result['revision'] = result.get('revision', 0) + 1
    result.setdefault('audit', []).append({'at': now, 'actor': actor, 'kind': 'copy_mode', 'before': before,
                                         'after': {k: result[k] for k in ('mode', 'amount', 'multiplier')}})
    return result


def daily_loss_update(daily, equity, now, risk_budget, controls, *, subscription_status):
    """Return updated observation and a desired action; NEVER issues Stop/close.
    Call even with limit disabled so enabling later can notice today's existing loss.
    Caller persists returned baseline/stop_requested before idempotent normal Stop enqueue.
    """
    value = number(equity); budget = number(risk_budget)
    if budget <= 0: raise PolicyError('Positive saved risk budget required')
    day = stamp(now).date().isoformat()
    state = deepcopy(daily) if daily and daily.get('day') == day else {'day': day, 'baseline_equity': str(value), 'stop_requested': False}
    loss = max(Decimal(0), number(state['baseline_equity']) - value)
    limit = controls.get('daily_loss_pct')
    output = {'loss': str(loss), 'threshold': None, 'blocked': False, 'action': 'none'}
    if limit is not None:
        threshold = budget * number(limit) / 100
        if threshold <= 0: raise PolicyError('Positive daily-loss threshold required')
        output.update(threshold=str(threshold), blocked=loss >= threshold)
        if output['blocked'] and subscription_status in {'active', 'paused'}:
            output['action'] = 'block_entries'
            if controls.get('auto_close_daily_loss') is True and not state['stop_requested']:
                output['action'] = 'request_normal_stop'; state['stop_requested'] = True
    return state, output


def advanced_entry_check(controls, *, side, source_entry, bid, ask, lots, positions_and_entries, signal_time, now, pending=False):
    """Bounded entry-only checks; caller supplies fresh verified market/account context."""
    checks = {}
    if controls.get('max_entry_deviation_pct') is not None and not pending:
        base, buy, sell = number(source_entry), number(ask), number(bid)
        if base <= 0 or not 0 < sell <= buy or side not in {'buy', 'sell'}:
            raise PolicyError('Valid source entry and current Bid/Ask required')
        worse = max(Decimal(0), (buy - base) / base * 100 if side == 'buy' else (base - sell) / base * 100)
        checks['entry_price'] = 'wait' if worse > number(controls['max_entry_deviation_pct']) else 'pass'
    if controls.get('max_trade_volume') is not None:
        checks['volume'] = 'skip' if number(lots) > number(controls['max_trade_volume']) else 'pass'
    if controls.get('max_positions') is not None:
        if type(positions_and_entries) is not int or positions_and_entries < 0:raise PolicyError('Verified total exposure-slot count required')
        checks['positions'] = 'wait' if positions_and_entries >= controls['max_positions'] else 'pass'
    if controls.get('max_signal_age_seconds') is not None:
        age = (stamp(now) - stamp(signal_time)).total_seconds()
        if age < 0:raise PolicyError('Source signal time cannot be future')
        checks['signal_age'] = 'refresh_source' if age > controls['max_signal_age_seconds'] else 'pass'
    return checks
