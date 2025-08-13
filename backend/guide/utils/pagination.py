from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpRequest


def paginate(request: HttpRequest, qs, per_page: int = 12, page_param: str = 'page'):
    page = request.GET.get(page_param) or 1
    paginator = Paginator(qs, per_page)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj
