from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django import template

register = template.Library()


@register.filter
def cop(value):
    try:
        decimal_value = Decimal(str(value))
        if not decimal_value.is_finite() or decimal_value < 0:
            return "Precio no disponible"
        pesos = decimal_value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return "Precio no disponible"
    return f"${format(pesos, ',').replace(',', '.')}"
