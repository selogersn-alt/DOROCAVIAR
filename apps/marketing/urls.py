from django.urls import path
from .views import custom_page_view, report_content_view, admin_stats_view, html_sitemap_view

urlpatterns = [
    path('page/<slug:slug>/', custom_page_view, name='custom_page'),
    path('report/', report_content_view, name='report_content'),
    path('admin/stats/', admin_stats_view, name='admin_stats'),
    path('sitemap/', html_sitemap_view, name='html_sitemap'),
]
