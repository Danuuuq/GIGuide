from django.urls import path
from guide.views.home import HomeView
from guide.views.create_view import ProductCreateView, SubcategoryCreateView, QAItemCreateView
from guide.views.detail_view import QaDetailView
from django.views.generic import TemplateView
from guide.views.list_view import SubcategoriesListView, QaListView
from guide.views.system import RobotsView, SitemapView

from guide.views.search import SearchView
from guide.views.update_view import QAItemUpdateView

app_name = 'guide'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('search/', SearchView.as_view(), name='search'),
    path(
        'contacts/',
        TemplateView.as_view(template_name='static/contacts.html'),
        name='contacts'
    ),
    path('add-product/', ProductCreateView.as_view(), name='product_add'),
    path('<slug:product_slug>/', SubcategoriesListView.as_view(), name='product_list'),
    path(
        'product/<slug:product_slug>/add-subcategory/',
        SubcategoryCreateView.as_view(),
        name='subcategory_add'
    ),
    path('product/<slug:product_slug>/<slug:sub_slug>/', QaListView.as_view(), name='qa_list'),
    path(
        'product/<slug:product_slug>/<slug:sub_slug>/add-qa/',
        QAItemCreateView.as_view(),
        name='qa_add'
    ),
    path(
        'product/<slug:product_slug>/<slug:sub_slug>/<int:qa_id>/',
        QaDetailView.as_view(),
        name='qa_detail'
    ),
    path(
        '<slug:product_slug>/<slug:sub_slug>/<int:qa_id>/edit-qa/',
        QAItemUpdateView.as_view(),
        name='qa_edit'
    ),
    path('search/', SearchView.as_view(), name='search'),
    path('robots.txt', RobotsView.as_view(), name='robots'),
    path('sitemap.xml', SitemapView.as_view(), name='sitemap'),
]
