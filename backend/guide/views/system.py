from __future__ import annotations
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator
from guide.views.base import BaseView


@method_decorator(require_GET, name='dispatch')
class RobotsView(BaseView):
    template_name = 'system/robots.txt'

    def get(self, request: HttpRequest) -> HttpResponse:
        resp = self.render(request)
        resp['Content-Type'] = 'text/plain; charset=utf-8'
        return resp


@method_decorator(require_GET, name='dispatch')
class SitemapView(BaseView):
    template_name = 'system/sitemap.xml'

    def get(self, request: HttpRequest) -> HttpResponse:
        resp = self.render(request)
        resp['Content-Type'] = 'application/xml; charset=utf-8'
        return resp
