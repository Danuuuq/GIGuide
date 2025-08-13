from django.shortcuts import get_object_or_404

from guide.views.base import BaseView
from guide.models import QAItem
from guide.selectors.nav import menu_links_qs


class QaDetailView(BaseView):
    template_name = 'pages/qa_detail.html'

    def get(self, request, product_slug, sub_slug, qa_id):
        qa = get_object_or_404(
            QAItem,
            pk=qa_id,
            subcategory__slug=sub_slug,
            subcategory__product__slug=product_slug,
            is_active=True
        )

        blocks = qa.blocks.order_by('position', 'id')
        all_questions = qa.subcategory.qa_items.order_by('position', 'id')

        return self.render(
            request,
            qa=qa,
            product=qa.subcategory.product,
            subcategory=qa.subcategory,
            blocks=blocks,
            all_questions=all_questions,
            top_links=menu_links_qs(),
        )
