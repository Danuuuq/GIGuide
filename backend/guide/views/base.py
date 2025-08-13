from __future__ import annotations
from typing import Any, Dict
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

from guide.utils.context import common_context


class BaseView(View):
    template_name: str = ''
    extra_context: dict[str, Any] | None = None

    def get_template_names(self) -> list[str]:
        if not self.template_name:
            raise ValueError(f'{self.__class__.__name__}: template_name is required')
        return [self.template_name]

    def get_context_data(self, request: HttpRequest, **kwargs: Any) -> Dict[str, Any]:
        base = self.extra_context.copy() if self.extra_context else {}
        base.update(kwargs)
        return common_context(**base)

    def render(self, request: HttpRequest, **context: Any) -> HttpResponse:
        return render(request, self.get_template_names()[0], self.get_context_data(request, **context))
