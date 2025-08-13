# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # все публичные маршруты приложения
    path('', include(('guide.urls', 'guide'), namespace='guide')),
]

# раздача MEDIA в режиме DEBUG
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
