from random import sample

from dataclasses import dataclass
from typing import List, Dict, Tuple
from django.db import models
from django.urls import reverse

from guide import models as m
from guide.utils.links import product_url, qa_item_url


# --- вспомогательное определение "опубликованного" статуса ---
def _published_q_filter() -> dict:
    # Если есть QAStatus с нужными значениями — используем его
    status_field = 'status'
    if hasattr(m, 'QAStatus'):
        candidates = [getattr(m.QAStatus, name, None) for name in ('PUBLISHED', 'PUBLIC', 'ACTIVE')]
        values = [v for v in candidates if v]
        if values:
            return {f'{status_field}__in': values}
        # иначе хотя бы исключим DRAFT
        draft = getattr(m.QAStatus, 'DRAFT', None)
        if draft:
            return {f'{status_field}__ne': draft}  # обработаем ниже вручную
    # по умолчанию: исключаем 'DRAFT'
    return {f'{status_field}__ne': 'DRAFT'}


def _exclude_draft(qs: models.QuerySet) -> models.QuerySet:
    # безопасно исключим DRAFT, если поле существует
    try:
        return qs.exclude(status='DRAFT')
    except Exception:
        return qs


@dataclass(slots=True)
class QuickFaqItem:
    title: str
    url: str


@dataclass(slots=True)
class QuickFaqGroup:
    product_name: str
    product_url: str
    items: List[QuickFaqItem]


# --- утилита извлечения "родительского" продукта из QAItem ---
def _resolve_product_from_subcategory(subcategory) -> Tuple[str | None, str | None]:
    """
    Возвращает (product_name, product_slug) из связей subcategory.
    Поддерживает цепочки: subcategory.product ИЛИ subcategory.category.product.
    """
    if subcategory is None:
        return None, None

    # прямой FK: Subcategory.product
    prod = getattr(subcategory, 'product', None)
    if prod is not None:
        return getattr(prod, 'name', None), getattr(prod, 'slug', None)

    # цепочка через category: Subcategory.category.product
    category = getattr(subcategory, 'category', None)
    if category is not None:
        prod2 = getattr(category, 'product', None)
        if prod2 is not None:
            return getattr(prod2, 'name', None), getattr(prod2, 'slug', None)

    return None, None


def quick_faq_groups(
    max_products: int = 8,
    per_product: int = 4,
) -> list[QuickFaqGroup]:
    """
    Возвращает данные для блока 'Быстрые вопросы по продуктам':
    до max_products групп, в каждой до per_product вопросов.
    """
    qs = m.QAItem.objects.filter(is_active=True)
    pub = _published_q_filter()
    if f"status__ne" in pub:
        qs = _exclude_draft(qs)
    elif pub:
        qs = qs.filter(**pub)

    # Нам нужны связи до subcategory и, по возможности, product/category
    qs = qs.select_related('subcategory')

    groups: Dict[str, QuickFaqGroup] = {}
    # Пройдёмся по самым свежим/верхним по position
    if hasattr(m.QAItem, 'position'):
        qs = qs.order_by('position', 'id')
    elif hasattr(m.QAItem, 'updated_at'):
        qs = qs.order_by('-updated_at', '-id')
    else:
        qs = qs.order_by('-id')

    for qa in qs.iterator():
        sub = getattr(qa, 'subcategory', None)
        product_name, product_slug = _resolve_product_from_subcategory(sub)
        if not product_name or not product_slug:
            continue

        # инициализация группы
        grp = groups.get(product_slug)
        if grp is None:
            grp = QuickFaqGroup(
                product_name=product_name,
                product_url=reverse(
                    'guide:product_list',  # имя маршрута на страницу продукта
                    kwargs={'product_slug': product_slug}
                ),
                items=[],
            )
            groups[product_slug] = grp
            # если уже набрали нужное количество продуктов — позже остановимся

        # добавляем пункт, если в группе ещё есть место
        if len(grp.items) < per_product:
            title = getattr(qa, 'question', '').strip() or f'Вопрос #{qa.pk}'
            url = reverse(
                'guide:qa_detail',
                kwargs={
                    'product_slug': product_slug,
                    'sub_slug': sub.slug,
                    'qa_id': qa.pk
                }
            )
            grp.items.append(QuickFaqItem(title=title, url=url))

        # если уже есть достаточно продуктов И все по per_product — можно завершать
        if len(groups) >= max_products and all(len(g.items) >= per_product for g in groups.values()):
            break

    # упорядочим группы по product_name (или просто как есть)
    result = list(groups.values())
    result = result[:max_products]
    return result


def build_quick_faqs_for_product(
    product: m.Product,
    *,
    max_subcats: int = 12,
    max_items_per_card: int = 4,
) -> list[dict]:
    """
    Возвращает список карточек для горизонтальной ленты:
    каждая карточка соответствует подкатегории продукта и содержит
    несколько опубликованных вопросов из неё.
    """
    # Берём активные подкатегории продукта (в пределах лимита)
    subcats_qs = m.Subcategory.objects.filter(
        product=product, is_active=True
    ).order_by('position', 'id')
    subcats = list(subcats_qs[:max_subcats])

    cards: list[dict] = []
    for sub in subcats:
        qas_qs = m.QAItem.objects.filter(
            subcategory=sub, status=m.QAStatus.PUBLISHED, is_active=True
        ).order_by('position', 'id')

        qas = list(qas_qs[:max_items_per_card])
        if len(qas) > 1:
            qas = sample(qas, k=min(max_items_per_card, len(qas)))

        items = [{
            'title': qa.question,
            'url': reverse('guide:qa_detail', kwargs={
                'product_slug': product.slug,
                'sub_slug': sub.slug,
                'qa_id': qa.id,
            })
        } for qa in qas]

        cards.append({
            'product_name': sub.name,
            'product_url': reverse('guide:qa_list', kwargs={
                'product_slug': product.slug,
                'sub_slug': sub.slug,
            }),
            'items': items,
        })
    return cards
