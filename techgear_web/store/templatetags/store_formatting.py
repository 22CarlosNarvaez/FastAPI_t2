from decimal import Decimal, ROUND_HALF_UP

from django import template

register = template.Library()


@register.filter
def cop(value):
    pesos = Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return f"${format(pesos, ',').replace(',', '.')}"
