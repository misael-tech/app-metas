from decimal import Decimal

from django import template

register = template.Library()


def _br(v):
    return f"{Decimal(v or 0):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


@register.filter
def moeda(v):
    return "R$ " + _br(v)


@register.filter
def perc(v):
    return _br(v) + "%"
