"""Validate the application's native-engine integration before changing retained state."""
from inspect import signature
from .exness_adapter import AdapterError


def validate_host(app):
    missing = []
    calls = {
        'save': (('event',), {}),
        'account': (('account',), {}),
        'admission': ((None, None), {}),
        'settings': (({}, None), {}),
        'signal_ids': (({},), {}),
        'unresolved': (({},), {}),
        'fx': ((None, 'USD', 'USD'), {'purchase': True}),
        'controls': (({}, {}, {}, None, {}), {'exclude_command': None}),
    }
    for name, (args, kwargs) in calls.items():
        callback = getattr(app, name, None)
        try:
            if not callable(callback):
                raise TypeError()
            signature(callback).bind(*args, **kwargs)
        except (TypeError, ValueError):
            missing.append(name)
    mode = getattr(app, 'mode', None)
    if mode not in ('native-read-only', 'native-execution'):
        missing.append('sealed native mode')
    state = getattr(app, 'state', None)
    if not isinstance(state, dict):
        missing.append('state')
    else:
        if state.get('mode') != mode:
            missing.append('retained state.mode matching mode')
        if type(state.get('frozen')) is not bool:
            missing.append('state.frozen')
        for key in ('accounts', 'strategies', 'subscriptions', 'commands'):
            if not isinstance(state.get(key), dict):
                missing.append('state.' + key)
    if type(getattr(getattr(app, 'store', None), 'failed', None)) is not bool:
        missing.append('store.failed durability fence')
    broker = getattr(app, 'broker', None)
    for name in ('observe', 'read', 'sync_status', 'fill_history', 'send'):
        if not callable(getattr(broker, name, None)):
            missing.append('broker.' + name)
    if not isinstance(getattr(broker, 'gateway', None), str):
        missing.append('broker.gateway')
    if not isinstance(getattr(broker, 'quota_errors', None), dict):
        missing.append('broker.quota_errors')
    for name in ('check', 'websocket'):
        if not callable(getattr(getattr(broker, 'quota', None), name, None)):
            missing.append('broker.quota.' + name)
    if missing:
        raise AdapterError('Native runtime host integration missing: ' + ', '.join(missing))
