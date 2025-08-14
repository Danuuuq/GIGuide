from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from guide.views.base import BaseView
from guide.forms import (
    QAItemForm,
    QABlockFormSet,
    ProductForm,
    SubcategoryForm,
)
from guide.models import Product, Subcategory, QAItem
from guide.utils.slug import make_unique_slug


class SubcategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, BaseView):
    template_name = 'pages/subcategory_form.html'

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request, product_slug: str | None = None):
        product = None
        if product_slug:
            product = get_object_or_404(Product, slug=product_slug)
            form = SubcategoryForm(initial={'product': product})
        else:
            form = SubcategoryForm()
        return self.render(request, form=form, product=product)

    def post(self, request, product_slug: str | None = None):
        if product_slug:
            product = get_object_or_404(Product, slug=product_slug)
            form = SubcategoryForm(request.POST, product_fixed=True)
        else:
            product = None
            form = SubcategoryForm(request.POST)

        if not form.is_valid():
            return self.render(request, form=form, product=product)

        with transaction.atomic():
            sub: Subcategory = form.save(commit=False)

            if product:
                sub.product_id = product.id
            elif not sub.product_id:
                form.add_error(None, 'Не указан продукт.')
                return self.render(request, form=form, product=product)

            if not sub.slug:
                sub.slug = make_unique_slug(sub, sub.name)

            sub.save()

        return redirect(reverse(
            'guide:qa_list',
            kwargs={'product_slug': sub.product.slug, 'sub_slug': sub.slug}
        ))


class ProductCreateView(LoginRequiredMixin, UserPassesTestMixin, BaseView):
    template_name = 'pages/product_form.html'

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request):
        form = ProductForm()
        return self.render(request, form=form)

    def post(self, request):
        form = ProductForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                product: Product = form.save(commit=False)
                if not product.slug:
                    product.slug = make_unique_slug(product, product.name)
                product.save()

            return redirect(reverse('guide:product_list', kwargs={'product_slug': product.slug}))
        return self.render(request, form=form)


class QAItemCreateView(LoginRequiredMixin, UserPassesTestMixin, BaseView):
    """
    Создание QAItem (вопрос-ответ) с наборами QABlock.
    Требует URL с product_slug и sub_slug, чтобы зафиксировать подкатегорию.
    Шаблон должен рендерить { form } и { formset }.
    Обязательно: <form ... enctype="multipart/form-data"> для загрузки медиа.
    """
    template_name = 'pages/qa_item_form.html'

    def test_func(self):
        return self.request.user.is_staff

    def _get_subcategory(self, product_slug: str, sub_slug: str) -> Subcategory:
        product = get_object_or_404(Product, slug=product_slug)
        return get_object_or_404(Subcategory, product=product, slug=sub_slug)

    def get(self, request, product_slug: str, sub_slug: str):
        subcategory = self._get_subcategory(product_slug, sub_slug)

        form = QAItemForm(subcategory_fixed=True, initial={'subcategory': subcategory})
        formset = QABlockFormSet(prefix='blocks')

        return self.render(
            request,
            form=form,
            formset=formset,
            subcategory=subcategory,
        )

    def post(self, request, product_slug: str, sub_slug: str):
        subcategory = self._get_subcategory(product_slug, sub_slug)

        form = QAItemForm(request.POST, subcategory_fixed=True)
        formset = QABlockFormSet(request.POST, request.FILES, prefix='blocks')

        if not (form.is_valid() and formset.is_valid()):
            return self.render(
                request,
                form=form,
                formset=formset,
                subcategory=subcategory,
            )

        with transaction.atomic():
            qa: QAItem = form.save(commit=False)
            qa.subcategory_id = subcategory.id
            qa.save()
            ordered_forms = getattr(formset, 'ordered_forms', None) or formset.forms
            position = 1
            for f in ordered_forms:
                if f.cleaned_data.get('DELETE'):
                    continue
                block = f.save(commit=False)
                block.qa_id = qa.id
                block.position = position
                position += 1
                block.save()
        return redirect(reverse(
            'guide:qa_detail',
            kwargs={
                'product_slug': product_slug,
                'sub_slug': sub_slug,
                'qa_id': qa.id,
            }
        ))
