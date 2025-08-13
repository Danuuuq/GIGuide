from __future__ import annotations
from django.db.models import QuerySet
from guide import models as m


def menu_links_qs() -> QuerySet[m.NavLink]:
    return m.NavLink.objects.filter(is_active=True).order_by('position')
