from django import forms
from django.forms import inlineformset_factory

from .models import (
    QAItem,
    QABlock,
    BlockKind,
    HeadingLevel,
    Product,
    Subcategory,
)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'slug', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'если пусто — сгенерируется автоматически'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False


class SubcategoryForm(forms.ModelForm):
    class Meta:
        model = Subcategory
        fields = ['name', 'slug', 'product', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'product': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, product_fixed=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False
        if product_fixed:
            self.fields.pop('product', None)


class QAItemForm(forms.ModelForm):
    class Meta:
        model = QAItem
        fields = ['subcategory', 'question', 'status']
        widgets = {
            'question': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'subcategory': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, subcategory_fixed: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        if subcategory_fixed:
            self.fields.pop('subcategory', None)


class QABlockForm(forms.ModelForm):
    class Meta:
        model = QABlock
        fields = [
            'kind',
            'heading_text', 'heading_level', 'heading_anchor',
            'text_md',
            'media_file', 'media_url', 'alt_text', 'caption',
        ]
        widgets = {
            'kind': forms.Select(attrs={'class': 'form-select'}),
            'heading_text': forms.TextInput(attrs={'class': 'form-control'}),
            'heading_level': forms.Select(attrs={'class': 'form-select'}),
            'heading_anchor': forms.TextInput(attrs={'class': 'form-control'}),
            'text_md': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'media_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'media_url': forms.URLInput(attrs={'class': 'form-control'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        for f in ('text_md', 'media_url', 'heading_text', 'heading_anchor', 'alt_text', 'caption'):
            if cleaned.get(f) == '':
                cleaned[f] = None
                self.cleaned_data[f] = None

        kind = cleaned.get('kind')

        if kind == BlockKind.HEADING:
            if not cleaned.get('heading_text'):
                self.add_error('heading_text', 'Для заголовка заполните heading_text.')
        elif kind == BlockKind.TEXT:
            if not cleaned.get('text_md'):
                self.add_error('text_md', 'Для текстового блока заполните text_md.')
        elif kind in (BlockKind.IMAGE, BlockKind.GIF, BlockKind.VIDEO):
            if not cleaned.get('media_file') and not cleaned.get('media_url'):
                self.add_error('media_file', 'Укажите media_file или media_url.')
                self.add_error('media_url', 'Укажите media_url или media_file.')

        return cleaned


QABlockFormSet = inlineformset_factory(
    parent_model=QAItem,
    model=QABlock,
    form=QABlockForm,
    fields=[
        'kind',
        'heading_text', 'heading_level', 'heading_anchor',
        'text_md',
        'media_file', 'media_url', 'alt_text', 'caption',
    ],
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
