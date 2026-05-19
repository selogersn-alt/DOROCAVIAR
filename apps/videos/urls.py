from django.urls import path
from .views import (
    VideoListView, VideoDetailView, CategoryListView,
    CategoryDetailView, TrendingListView, SearchView,
    PhotoListView, PhotoDetailView, VideoCreateView, PhotoCreateView, AddCommentView,
    search_suggestions_view, like_video_view, like_photo_view, LibraryView,
    ShortsListView, like_video_ajax
)

urlpatterns = [
    path('', VideoListView.as_view(), name='home'),
    path('search/', SearchView.as_view(), name='search'),
    path('search/suggestions/', search_suggestions_view, name='search_suggestions'),
    path('trending/', TrendingListView.as_view(), name='trending_videos'),
    path('shorts/', ShortsListView.as_view(), name='shorts_list'),
    path('library/', LibraryView.as_view(), name='library'),
    path('like/video-ajax/<int:video_id>/', like_video_ajax, name='like_video_ajax'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('c/<slug:slug>/', CategoryDetailView.as_view(), name='category_detail'),
    
    # Upload & Interactions
    path('upload/video/', VideoCreateView.as_view(), name='video_upload'),
    path('upload/photo/', PhotoCreateView.as_view(), name='photo_upload'),
    path('comment/add/', AddCommentView.as_view(), name='add_comment'),
    path('like/video/<int:video_id>/', like_video_view, name='like_video'),
    path('like/photo/<int:photo_id>/', like_photo_view, name='like_photo'),
    
    # URL SEO très puissante pour Google : monsite.com/nom-de-la-categorie/nom-de-la-video/
    path('<slug:category_slug>/v/<slug:slug>/', VideoDetailView.as_view(), name='video_detail'),
    path('v/<slug:slug>/', VideoDetailView.as_view(), name='video_detail_no_cat'),
    
    # Photos
    path('photos/', PhotoListView.as_view(), name='photo_list'),
    path('<slug:category_slug>/p/<slug:slug>/', PhotoDetailView.as_view(), name='photo_detail'),
    path('p/<slug:slug>/', PhotoDetailView.as_view(), name='photo_detail_no_cat'),
]
