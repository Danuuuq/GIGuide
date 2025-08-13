from __future__ import annotations
from django.db.models import QuerySet
from guide import models as m


def products_for_home(limit: int = 8) -> QuerySet[m.Product]:
    qs = m.Product.objects.filter(is_active=True)
    if hasattr(m.Product, 'position'):
        qs = qs.order_by('position', 'id')
    else:
        qs = qs.order_by('id')
    return qs[:limit]
