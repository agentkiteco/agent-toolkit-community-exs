"""Safe JSON fallback for broker decimals at the application checkpoint boundary."""
from decimal import Decimal


def exact_json_decimal(value):
    """Keep the exact plain decimal text and reject unsupported objects."""
    if isinstance(value, Decimal) and value.is_finite():
        return format(value, 'f')
    raise TypeError('Unsupported JSON value type: ' + type(value).__name__)
