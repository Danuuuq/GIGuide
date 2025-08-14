from itertools import groupby

from django.db.models import Q, Prefetch
from django.http import HttpRequest, HttpResponse

from guide.views.base import BaseView
from guide.utils.pagination import paginate
from guide.selectors.nav import menu_links_qs
from guide.models import QAItem, QABlock
from giguide import settings


def _cf(s: str | None) -> str:
    return (s or '').casefold() 



class SearchView(BaseView):
    template_name = 'pages/search_results.html'
    per_page = 12

    def get(self, request: HttpRequest) -> HttpResponse:
        q = (request.GET.get('q') or '').strip()
        if len(q) < 1:
            return self.render(request, title='Поиск', q=q, groups=[], total=0, page_obj=None)

        q_cf = _cf(q)
        is_sqlite = 'sqlite' in settings.DATABASES['default']['ENGINE']

        db_qs = (
            QAItem.objects.filter(
                Q(question__icontains=q)
                | Q(blocks__heading_text__icontains=q)
                | Q(blocks__text_md__icontains=q)
                | Q(blocks__caption__icontains=q)
                | Q(blocks__alt_text__icontains=q)
            )
            .select_related('subcategory', 'subcategory__product')
            .distinct()
            .order_by('subcategory__product__name', 'subcategory__name', 'question')
        )

        if is_sqlite:
            base_qs = (
                QAItem.objects.all()
                .select_related('subcategory', 'subcategory__product')
                .prefetch_related(
                    Prefetch(
                        'blocks',
                        queryset=QABlock.objects.only(
                            'qa_id',
                            'heading_text',
                            'text_md',
                            'caption',
                            'alt_text'
                        )
                    )
                )
            )

            matched = []
            for qa in base_qs:
                if (
                    q_cf in _cf(qa.question)
                    or any(
                        q_cf in _cf(val)
                        for b in qa.blocks.all()
                        for val in (b.heading_text, b.text_md, b.caption, b.alt_text)
                    )
                ):
                    matched.append(qa)

            matched.sort(key=lambda x: (x.subcategory.product.name, x.subcategory.name, x.question))

            total = len(matched)
            page_obj = paginate(request, matched, per_page=self.per_page)
            items = list(page_obj.object_list)
        else:
            total = db_qs.count()
            page_obj = paginate(request, db_qs, per_page=self.per_page)
            items = list(page_obj.object_list)

        groups = []
        for (product, subcategory), chunk in groupby(items, key=lambda x: (x.subcategory.product, x.subcategory)):
            groups.append({'product': product, 'subcategory': subcategory, 'qas': list(chunk)})

        return self.render(
            request,
            title='Поиск',
            q=q,
            groups=groups,
            total=total,
            page_obj=page_obj,
            top_links=menu_links_qs(),
        )
