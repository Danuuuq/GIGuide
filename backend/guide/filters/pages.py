from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from django.db.models import Q


@dataclass(slots=True)
class PageFilters:
    q: Optional[str] = None
    category: Optional[str] = None  # slug

    @classmethod
    def from_request(cls, request) -> 'PageFilters':
        return cls(
            q=(request.GET.get('q') or '').strip() or None,
            category=(request.GET.get('category') or '').strip() or None,
        )


def apply_page_filters(qs, f: PageFilters):
    if f.q:
        qs = qs.filter(
            Q(title__icontains=f.q) |
            Q(content__icontains=f.q)
        )
    if f.category:
        qs = qs.filter(category__slug=f.category, category__is_active=True)
    return qs.distinct()
