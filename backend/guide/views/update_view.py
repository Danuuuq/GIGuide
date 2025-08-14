# views.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from guide.models import Product, Subcategory, QAItem, QABlock
from guide.forms import QAItemForm, QABlockFormSet
from .base import BaseView


class QAItemUpdateView(LoginRequiredMixin, UserPassesTestMixin, BaseView):
    template_name = 'pages/qa_item_form.html'  # используем тот же шаблон, что и при создании

    def test_func(self):
        return self.request.user.is_staff

    def _get_ctx(self, product_slug: str, sub_slug: str, qa_id: int):
        product = get_object_or_404(Product, slug=product_slug)
        subcategory = get_object_or_404(Subcategory, product=product, slug=sub_slug)
        qa = get_object_or_404(QAItem, pk=qa_id, subcategory=subcategory)
        return product, subcategory, qa

    def get(self, request, product_slug: str, sub_slug: str, qa_id: int):
        product, subcategory, qa = self._get_ctx(product_slug, sub_slug, qa_id)

        form = QAItemForm(instance=qa, subcategory_fixed=True)
        # покажем блоки в текущем порядке (по position)
        formset = QABlockFormSet(instance=qa, prefix='blocks')

        return self.render(
            request,
            form=form,
            formset=formset,
            subcategory=subcategory,
            product=product,
            qa=qa,
            is_edit=True,  # флаг для заголовка/кнопок в шаблоне
        )

    def post(self, request, product_slug: str, sub_slug: str, qa_id: int):
        product, subcategory, qa = self._get_ctx(product_slug, sub_slug, qa_id)

        form = QAItemForm(request.POST, instance=qa, subcategory_fixed=True)
        formset = QABlockFormSet(request.POST, request.FILES, instance=qa, prefix='blocks')

        if not (form.is_valid() and formset.is_valid()):
            return self.render(
                request,
                form=form,
                formset=formset,
                subcategory=subcategory,
                product=product,
                qa=qa,
                is_edit=True,
            )

        with transaction.atomic():
            qa = form.save(commit=False)
            # подкатегорию не даём менять из формы:
            qa.subcategory_id = subcategory.id
            qa.save()

            # Сохраняем блоки в DOM-порядке, пропуская удалённые
            position = 1
            # formset.forms уже идут в порядке индексов blocks-0, blocks-1, ...
            for f in formset.forms:
                if f.cleaned_data.get('DELETE'):
                    # удалим после цикла, чтобы не мешать другим связям
                    continue
                block = f.save(commit=False)
                block.qa_id = qa.id
                block.position = position
                position += 1
                block.save()  # важно: вызвать save() для автогенерации heading_anchor

            # Удаляем отмеченные на удаление
            for f in formset.forms:
                if f.cleaned_data.get('DELETE') and f.instance.pk:
                    f.instance.delete()

        return redirect(reverse('guide:qa_detail', kwargs={
            'product_slug': product.slug,
            'sub_slug': subcategory.slug,
            'qa_id': qa.id,
        }))
