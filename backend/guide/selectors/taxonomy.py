from __future__ import annotations
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from guide import models as m

def categories_qs() -> QuerySet[m.Category]:
    return m.Product.objects.filter(is_active=True).order_by('position')

def category_by_slug_or_404(slug: str) -> m.Category:
    return get_object_or_404(m.Product, slug=slug, is_active=True)
