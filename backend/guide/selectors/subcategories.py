from __future__ import annotations
from django.apps import apps
from django.db.models import QuerySet

m = apps.get_app_config('guide').models_module  # либо: from guide import models as m

def subcategories_by_product_slug(product_slug: str) -> QuerySet:
    Subcategory = m.Subcategory
    qs = Subcategory.objects.filter(is_active=True)

    # 1) Прямой FK: Subcategory.product -> Product.slug
    if hasattr(Subcategory, 'product'):
        return qs.filter(product__slug=product_slug).order_by('position', 'id') if hasattr(Subcategory, 'position') else qs.filter(product__slug=product_slug).order_by('id')

    # 2) Через категорию: Subcategory.category.product.slug
    if hasattr(Subcategory, 'category'):
        return qs.filter(category__product__slug=product_slug, category__is_active=True).order_by('position', 'id') if hasattr(Subcategory, 'position') else qs.filter(category__product__slug=product_slug, category__is_active=True).order_by('id')

    # 3) Иначе — пусто
    return Subcategory.objects.none()
