from django.urls import path
from guide.views.home import HomeView
from guide.views.detail_view import QaDetailView
from guide.views.list_view import SubcategoriesListView, QaListView
from guide.views.system import RobotsView, SitemapView
from guide.views.search import SearchView

app_name = 'guide'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),

    path('<slug:product_slug>/', SubcategoriesListView.as_view(), name='product_list'),
    path('product/<slug:product_slug>/<slug:sub_slug>/', QaListView.as_view(), name='qa_list'),
    path(
        'product/<slug:product_slug>/<slug:sub_slug>/<int:qa_id>/',
        QaDetailView.as_view(),
        name='qa_detail'
    ),
    path('search/', SearchView.as_view(), name='search'),
    path('robots.txt', RobotsView.as_view(), name='robots'),
    path('sitemap.xml', SitemapView.as_view(), name='sitemap'),
]
