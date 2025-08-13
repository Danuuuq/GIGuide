from __future__ import annotations
from django.db import models
from django.apps import apps
from django.shortcuts import get_object_or_404

Page = apps.get_model('guide', 'Product')


def _has_field(model: type[models.Model], name: str) -> bool:
    try:
        model._meta.get_field(name)
        return True
    except Exception:
        return False


def base_page_qs() -> models.QuerySet[Page]:
    qs = Page.objects.filter(is_active=True)
    if _has_field(Page, 'created_at'):
        qs = qs.order_by('-created_at')
    elif _has_field(Page, 'position'):
        qs = qs.order_by('position', 'id')
    return qs


def latest_pages(limit: int = 8):
    return base_page_qs()[:limit]


def page_by_slug_or_404(slug: str) -> Page:
    return get_object_or_404(Page.objects.all(), slug=slug, is_active=True)


def pages_by_category_slug(slug: str):
    if _has_field(Page, 'category'):
        return base_page_qs().filter(category__slug=slug, category__is_active=True)
    return Page.objects.none()
