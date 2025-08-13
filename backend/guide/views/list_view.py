from __future__ import annotations
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from guide.views.base import BaseView
from guide.selectors.subcategories import subcategories_by_product_slug
from guide.selectors.qa import build_quick_faqs_for_product
from guide.models import Product, Subcategory, QAItem
from guide.selectors.nav import menu_links_qs


class SubcategoriesListView(BaseView):
    template_name = 'pages/list_subcategories.html'

    def get(self, request: HttpRequest, product_slug: str) -> HttpResponse:
        product = get_object_or_404(Product, slug=product_slug, is_active=True)
        subcategories = subcategories_by_product_slug(product_slug)
        quick_faqs = build_quick_faqs_for_product(product)

        return self.render(
            request,
            title=product.name,
            product=product,
            subcategories=subcategories,
            quick_faqs=quick_faqs,
            top_links=menu_links_qs(),
        )


class QaListView(BaseView):
    template_name = 'pages/list_qa.html'

    def get(self, request, product_slug: str, sub_slug: str):
        subcategory = get_object_or_404(
            Subcategory,
            slug=sub_slug,
            product__slug=product_slug,
            is_active=True
        )

        qas = QAItem.objects.filter(
            subcategory=subcategory,
            is_active=True
        ).order_by('position', 'id')

        return self.render(
            request,
            title=subcategory.name,
            subcategory=subcategory,
            qas=qas,
            product=subcategory.product,
            top_links=menu_links_qs(),
        )
