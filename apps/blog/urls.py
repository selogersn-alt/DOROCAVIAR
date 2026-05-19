from django.urls import path
from .views import PostListView, PostDetailView, CategoryPostListView

app_name = 'blog'

urlpatterns = [
    path('', PostListView.as_view(), name='post_list'),
    path('category/<slug:slug>/', CategoryPostListView.as_view(), name='category_post_list'),
    path('<slug:slug>/', PostDetailView.as_view(), name='post_detail'),
]
