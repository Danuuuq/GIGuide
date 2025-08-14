from django.utils.text import slugify as dj_slugify
from unidecode import unidecode

def make_unique_slug(instance, value: str, field_name: str = 'slug') -> str:
    Model = instance.__class__
    base = dj_slugify(unidecode(value)) or 'item'
    max_len = getattr(Model._meta.get_field(field_name), 'max_length', None)
    if max_len:
        base = base[:max_len]

    slug = base
    i = 2
    while Model.objects.filter(**{field_name: slug}).exists():
        suffix = f'-{i}'
        cut = (max_len - len(suffix)) if max_len else None
        slug = f'{base[:cut]}{suffix}'
        i += 1
    return slug
