from __future__ import annotations
from django.http import HttpRequest, HttpResponse
from guide.views.base import BaseView
from guide.selectors.products import products_for_home
from guide.selectors.qa import quick_faq_groups
from guide.selectors.nav import menu_links_qs


class HomeView(BaseView):
    template_name = 'pages/home.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        return self.render(
            request,
            title='Главная — Портал ИТ Газпром Инвест',
            products=products_for_home(limit=12),
            quick_faqs=quick_faq_groups(max_products=12, per_product=4),
            top_links=menu_links_qs(),
        )
