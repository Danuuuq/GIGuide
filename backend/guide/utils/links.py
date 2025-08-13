from __future__ import annotations
from django.urls import NoReverseMatch, reverse


def product_url(slug: str) -> str:
    """Пытаемся сослаться на детальную страницу продукта, иначе глушилка."""
    try:
        return reverse('guide:product_detail', kwargs={'slug': slug})
    except NoReverseMatch:
        return '#'


def qa_item_url(qa_id: int, product_slug: str | None = None) -> str:
    """
    Предпочтительно: детальная страница вопроса.
    Запасной вариант: якорь на странице продукта (#q-<id>), если нет маршрута.
    Совсем запасной: '#'.
    """
    try:
        return reverse('guide:qa_detail', kwargs={'pk': qa_id})
    except NoReverseMatch:
        if product_slug:
            try:
                return reverse('guide:product_detail', kwargs={'slug': product_slug}) + f'#q-{qa_id}'
            except NoReverseMatch:
                pass
    return '#'
