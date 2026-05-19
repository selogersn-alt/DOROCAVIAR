from django.urls import path
from .views import custom_page_view, report_content_view, admin_stats_view, html_sitemap_view
from .views_premium import (
    premium_page_view, create_checkout_session_view,
    premium_success_view, premium_cancel_view, stripe_webhook_view
)

urlpatterns = [
    path('page/<slug:slug>/', custom_page_view, name='custom_page'),
    path('report/', report_content_view, name='report_content'),
    path('admin/stats/', admin_stats_view, name='admin_stats'),
    path('sitemap/', html_sitemap_view, name='html_sitemap'),
    
    # Premium Stripe VIP
    path('premium/', premium_page_view, name='premium_page'),
    path('premium/checkout/', create_checkout_session_view, name='premium_checkout'),
    path('premium/success/', premium_success_view, name='premium_success'),
    path('premium/cancel/', premium_cancel_view, name='premium_cancel'),
    path('premium/webhook/', stripe_webhook_view, name='stripe_webhook'),
]
