from __future__ import annotations
from django.http import HttpRequest, HttpResponse
from guide.views.base import BaseView
from guide.utils.pagination import paginate
from guide.filters.pages import PageFilters, apply_page_filters
from guide.selectors.pages import base_page_qs


class SearchView(BaseView):
    template_name = 'search/results.html'   # можешь временно поставить 'pages/list.html'
    per_page = 12

    def get(self, request: HttpRequest) -> HttpResponse:
        filters = PageFilters.from_request(request)
        qs = base_page_qs()

        # если запрос пустой — ничего не ищем, показываем “введите запрос”
        if not filters.q:
            return self.render(
                request,
                title='Поиск',
                filters=filters,
                page_obj=None,
                pages=[],
            )

        qs = apply_page_filters(qs, filters)
        page_obj = paginate(request, qs, per_page=self.per_page)
        return self.render(
            request,
            title='Поиск',
            filters=filters,
            page_obj=page_obj,
            pages=page_obj.object_list,
        )
