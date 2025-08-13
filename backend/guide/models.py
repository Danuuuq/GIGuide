from uuid import uuid4
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F, Q
from django.utils.text import slugify

from giguide.variables import ModelConfig


class BaseModel(models.Model):
    """Базовый класс для всех моделей портала."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    position = models.PositiveIntegerField(default=1, help_text='Порядок отображения')
    is_active = models.BooleanField(default=True, help_text='Активен ли объект')

    class Meta:
        abstract = True
        ordering = ['position', 'id']

    # === НАСТРОЙКА ОБЛАСТИ ПОРЯДКА ===
    def position_scope_filter(self) -> dict:
        """
        Верни фильтр области, в пределах которой позиции уникальны и «сдвигаются».
        По умолчанию — вся таблица (как для Product).
        Переопредели в наследниках: {'product': self.product} / {'subcategory': self.subcategory} / {'qa': self.qa}.
        """
        return {}

    # === ОСНОВНАЯ ЛОГИКА ПОЗИЦИЙ (вставка/перемещение) ===
    def _ensure_position_on_create(self):
        scope = self.position_scope_filter()
        with transaction.atomic():
            # если позиция не задана — ставим в конец
            if not self.position or self.position < 1:
                last = self.__class__.objects.select_for_update().filter(**scope).order_by('-position').first()
                self.position = (last.position + 1) if last else 1
                return

            # если позиция задана — сдвигаем всех, у кого position >= нашей
            self.__class__.objects.select_for_update().filter(
                Q(**scope) & Q(position__gte=self.position)
            ).update(position=F('position') + 1)

    def _ensure_position_on_update(self, old_position: int):
        """Пересчёт при изменении позиции существующей записи."""
        new_position = self.position or 1
        if new_position == old_position:
            return

        scope = self.position_scope_filter()
        with transaction.atomic():
            # заблокируем ряд в нашей области
            self.__class__.objects.select_for_update().filter(**scope)

            if new_position < 1:
                new_position = 1

            # вычислим границы
            if new_position > old_position:
                # сдвинуть вверх: окна (old+1 .. new) -=1
                self.__class__.objects.filter(
                    Q(**scope) & Q(position__gt=old_position) & Q(position__lte=new_position)
                ).update(position=F('position') - 1)
            else:
                # сдвинуть вниз: окна (new .. old-1) +=1
                self.__class__.objects.filter(
                    Q(**scope) & Q(position__gte=new_position) & Q(position__lt=old_position)
                ).update(position=F('position') + 1)

            self.position = new_position

    def save(self, *args, **kwargs):
        is_create = self._state.adding
        if is_create:
            self._ensure_position_on_create()
            return super().save(*args, **kwargs)

        # update: проверяем смену позиции
        old = self.__class__.objects.only('position').get(pk=self.pk)
        if old.position != (self.position or 1):
            self._ensure_position_on_update(old.position)
        return super().save(*args, **kwargs)


class Product(BaseModel):
    name = models.CharField(max_length=ModelConfig.MAX_LENGTH_NAME)
    slug = models.SlugField(max_length=ModelConfig.MAX_LENGTH_SLUG)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Subcategory(BaseModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='subcategories',
    )
    name = models.CharField(max_length=ModelConfig.MAX_LENGTH_NAME)
    slug = models.SlugField(max_length=ModelConfig.MAX_LENGTH_SLUG)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'slug'],
                name='uq_subcategory_product_slug',
            ),
        ]

    def __str__(self):
        return f'{self.product.name} / {self.name}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def position_scope_filter(self) -> dict:
        return {'product': self.product}


class QAStatus(models.TextChoices):
    DRAFT = 'draft', 'Черновик'
    PUBLISHED = 'published', 'Опубликовано'
    ARCHIVED = 'archived', 'Архив'


class QAItem(BaseModel):
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.CASCADE,
        related_name='qa_items',
    )
    question = models.TextField()
    status = models.CharField(
        max_length=ModelConfig.MAX_LENGTH_STATUS,
        choices=QAStatus.choices,
        default=QAStatus.DRAFT,
        db_index=True,
    )

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(
                fields=['subcategory', 'position'],
                name='idx_qaitems_subcat_pos',
            ),
        ]

    def __str__(self):
        return self.question[:ModelConfig.MAX_SHORT_QUESTION]

    def position_scope_filter(self) -> dict:
        return {'subcategory': self.subcategory}


class BlockKind(models.TextChoices):
    HEADING = 'heading', 'Заголовок'
    TEXT = 'text', 'Текст'
    IMAGE = 'image', 'Картинка'
    GIF = 'gif', 'GIF'
    VIDEO = 'video', 'Видео'


class HeadingLevel(models.IntegerChoices):
    H2 = 2, 'H2'
    H3 = 3, 'H3'
    H4 = 4, 'H4'


def qa_media_upload_to(instance: 'QABlock', filename: str) -> str:
    stem = Path(filename).stem
    ext = Path(filename).suffix.lower()
    safe = slugify(stem) or 'file'
    return f'qa/{instance.qa_id}/{uuid4().hex}_{safe}{ext}'


class QABlock(BaseModel):
    qa = models.ForeignKey(
        QAItem,
        on_delete=models.CASCADE,
        related_name='blocks',
    )
    kind = models.CharField(
        max_length=ModelConfig.MAX_LENGTH_KIND,
        choices=BlockKind.choices,
    )

    # --- Заголовок ---
    heading_text = models.CharField(
        max_length=ModelConfig.MAX_LENGTH_HEADING,
        blank=True,
        null=True,
        help_text='Текст заголовка без Markdown',
    )
    heading_level = models.PositiveSmallIntegerField(
        choices=HeadingLevel.choices,
        default=HeadingLevel.H2,
        blank=True,
        null=True,
    )
    heading_anchor = models.SlugField(
        max_length=ModelConfig.MAX_LENGTH_HEADING_ANCHOR,
        blank=True,
        null=True,
        help_text='Якорь для ссылок/TOC (автогенерация)',
    )

    # --- Текст ---
    text_md = models.TextField(
        blank=True,
        null=True,
        help_text='Markdown для текстовых блоков',
    )

    # --- Медиа ---
    media_file = models.FileField(
        upload_to=qa_media_upload_to,
        blank=True,
        null=True,
        help_text='Загруженный файл (изображение/GIF/видео)',
    )
    media_url = models.URLField(
        blank=True,
        null=True,
        help_text='Внешняя ссылка на медиа',
    )
    alt_text = models.CharField(
        max_length=ModelConfig.MAX_LENGTH_ALT_TEXT,
        blank=True,
        null=True,
    )
    caption = models.CharField(
        max_length=ModelConfig.MAX_LENGTH_CAPTION,
        blank=True,
        null=True,
    )

    class Meta(BaseModel.Meta):
        constraints = [
            # Позиция уникальна в рамках ответа
            models.UniqueConstraint(
                fields=['qa', 'position'],
                name='uq_qablock_qa_position',
            ),
            # Для текстового блока обязателен text_md
            models.CheckConstraint(
                name='ck_qablock_text_requires_text',
                check=Q(
                    kind=BlockKind.TEXT,
                    text_md__isnull=False,
                ) | ~Q(kind=BlockKind.TEXT),
            ),
            # Для медиаблока обязателен media_file или media_url
            models.CheckConstraint(
                name='ck_qablock_media_requires_file_or_url',
                check=(
                    ~Q(kind__in=[
                        BlockKind.IMAGE,
                        BlockKind.GIF,
                        BlockKind.VIDEO,
                    ]) |
                    Q(media_file__isnull=False) | Q(media_url__isnull=False)
                ),
            ),
            # Для заголовка обязателен heading_text
            models.CheckConstraint(
                name='ck_qablock_heading_requires_text',
                check=Q(
                    kind=BlockKind.HEADING,
                    heading_text__isnull=False,
                ) | ~Q(kind=BlockKind.HEADING),
            ),
        ]
        indexes = [
            models.Index(
                fields=['qa', 'position'],
                name='idx_qablocks_qa_pos',
            ),
        ]

    def __str__(self):
        if self.kind == BlockKind.HEADING and self.heading_text:
            return (
                f'{self.qa_id}#{self.position} '
                f'(H{self.heading_level} '
                f'{self.heading_text[:ModelConfig.MAX_LENGTH_SHORT_QABLOCK]})')
        if self.kind == BlockKind.TEXT and self.text_md:
            return (
                f'{self.qa_id}#{self.position} '
                f'(text {self.text_md[:ModelConfig.MAX_LENGTH_SHORT_QABLOCK]})')
        return f'{self.qa_id}#{self.position} ({self.kind})'

    def position_scope_filter(self) -> dict:
        return {'qa': self.qa}

    @property
    def media_link(self) -> str | None:
        if self.media_file:
            try:
                return self.media_file.url
            except ValueError:
                return None
        return self.media_url

    def clean(self):
        """
        Условная валидация по типу блока.
        """

        # нормализуем пустые строки
        for attr in ('text_md', 'media_url', 'heading_text', 'heading_anchor'):
            if getattr(self, attr) == '':
                setattr(self, attr, None)

        if self.kind == BlockKind.HEADING:
            if not self.heading_text:
                raise ValidationError('Для заголовка заполните heading_text.')
            # заголовок не должен требовать медиа/текста
            return

        if self.kind == BlockKind.TEXT:
            if not self.text_md:
                raise ValidationError('Для текстового блока заполните text_md.')
            return

        if self.kind in (BlockKind.IMAGE, BlockKind.GIF, BlockKind.VIDEO):
            if not self.media_file and not self.media_url:
                raise ValidationError('Для медиа-блока укажите media_file или media_url.')

    def save(self, *args, **kwargs):
        # автогенерация якоря для заголовка (если не задан)
        if self.kind == BlockKind.HEADING and self.heading_text and not self.heading_anchor:
            base = slugify(self.heading_text) or f'h{self.heading_level}-{self.position}'
            self.heading_anchor = base[:220]
        super().save(*args, **kwargs)


class LinkPlacement(models.TextChoices):
    HEADER = 'header', 'Шапка'
    FOOTER = 'footer', 'Футер'
    SOCIAL = 'social', 'Соцсети'


class NavLink(BaseModel):
    """Внешние ссылки для навигации (шапка/футер/соц.блок)."""
    placement = models.CharField(
        max_length=12,
        choices=LinkPlacement.choices,
        default=LinkPlacement.HEADER,
        db_index=True,
        help_text='Где показывать ссылку',
    )
    label = models.CharField(max_length=120, help_text='Текст ссылки')
    url = models.URLField(help_text='Только http(s) ссылки')
    icon_name = models.CharField(
        max_length=64, blank=True, null=True,
        help_text='Имя иконки из набора фронта (например, "github", "telegram")'
    )

    open_in_new_tab = models.BooleanField(default=True)
    rel_nofollow = models.BooleanField(default=False)
    rel_sponsored = models.BooleanField(default=False)
    rel_noopener = models.BooleanField(default=True)
    rel_noreferrer = models.BooleanField(default=True)

    class Meta(BaseModel.Meta):
        constraints = [
            # Необязательно, но удобно: уникальная метка в пределах placement
            models.UniqueConstraint(
                fields=['placement', 'label'],
                name='uq_navlink_placement_label'
            ),
        ]
        indexes = [
            models.Index(fields=['placement', 'position'], name='idx_navlink_place_pos'),
        ]

    def __str__(self):
        return f'[{self.placement}] {self.label} → {self.url}'

    # Позиции считаем отдельно в рамках одной зоны (шапка/футер/соц)
    def position_scope_filter(self) -> dict:
        return {'placement': self.placement}

    # Базовая защита: разрешаем только http/https
    def clean(self):
        super().clean()
        if not (self.url.startswith('http://') or self.url.startswith('https://')):
            raise ValidationError({'url': 'Разрешены только http(s) ссылки.'})

    # Готовые атрибуты для фронта/шаблона
    @property
    def html_target(self) -> str:
        return '_blank' if self.open_in_new_tab else '_self'

    @property
    def html_rel(self) -> str:
        parts = []
        if self.rel_noopener:
            parts.append('noopener')
        if self.rel_noreferrer:
            parts.append('noreferrer')
        if self.rel_nofollow:
            parts.append('nofollow')
        if self.rel_sponsored:
            parts.append('sponsored')
        return ' '.join(parts) if parts else ''
