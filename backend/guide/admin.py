from django.contrib import admin

from .models import (
    Product,
    Subcategory,
    QAItem,
    QABlock,
    NavLink
)

admin.site.register(Product)
admin.site.register(Subcategory)
admin.site.register(QAItem)
admin.site.register(QABlock)
admin.site.register(NavLink)
