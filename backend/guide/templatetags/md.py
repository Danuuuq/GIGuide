from django import template
from django.utils.safestring import mark_safe
import markdown2
import bleach

register = template.Library()

# Разрешённые HTML-теги/атрибуты/схемы — безопасный минимальный набор
ALLOWED_TAGS = [
    'p', 'br', 'hr',
    'strong', 'b', 'em', 'i', 'u', 's', 'code', 'pre', 'kbd',
    'blockquote',
    'ul', 'ol', 'li',
    'h2', 'h3', 'h4',  # если кто-то в md поставит ## ###
    'a',
    'table', 'thead', 'tbody', 'tr', 'th', 'td'
]
ALLOWED_ATTRS = {
    'a': ['href', 'title', 'target', 'rel'],
    'th': ['align'], 'td': ['align']
}
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

# Настройки markdown2 — таблицы, зачёркивание, fenced code и т.д.
MD_EXTRAS = {
    'fenced-code-blocks': True,
    'tables': True,
    'strike': True,
    'smarty-pants': False,
    'cuddled-lists': True,
    'code-friendly': True,
    'break-on-newline': True,  # переносы как <br>
    'header-ids': False,       # якоря заголовков не нужны тут
}

@register.filter(name='markdown_safe')
def markdown_safe(text_md: str | None):
    """
    Рендерит markdown -> безопасный HTML.
    Использовать ТОЛЬКО для текстовых блоков QABlock.
    """
    if not text_md:
        return ''
    # 1) md -> html
    html = markdown2.markdown(text_md, extras=MD_EXTRAS)

    # 2) sanitize (убираем всё лишнее)
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )

    # 3) автоссылки + target/_blank + rel
    linked = bleach.linkify(
        cleaned,
        callbacks=[bleach.linkifier.DEFAULT_CALLBACKS[0]],  # стандартный nofollow и т.п.
        skip_tags=None, parse_email=True
    )
    # принудительно добавим target/rel для <a>, если вдруг не проставилось
    linked = linked.replace('<a ', '<a target="_blank" rel="noopener noreferrer" ')

    return mark_safe(linked)
