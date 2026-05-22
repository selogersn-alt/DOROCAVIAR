from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.views import View
from django.db.models import Q, F
from django.contrib import messages
from .models import Video, Category, Photo, Comment, VideoHistory
from .forms import VideoUploadForm, PhotoUploadForm
from apps.users.models import User

class VideoListView(ListView):
    model = Video
    template_name = 'index.html'
    context_object_name = 'videos'
    paginate_by = 12

    def get(self, request, *args, **kwargs):
        if request.GET.get('ajax'):
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            return render(request, 'videos/video_list_fragment.html', context)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        from .recommendations import get_recommended_videos
        return get_recommended_videos(self.request, limit=120)

class VideoDetailView(DetailView):
    model = Video
    template_name = 'videos/video_detail.html'
    context_object_name = 'video'

    def get_object(self):
        obj = super().get_object()
        Video.objects.filter(pk=obj.pk).update(views_count=F('views_count') + 1)
        obj.refresh_from_db(fields=['views_count'])
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video = self.object
        
        # Historique
        if self.request.user.is_authenticated:
            from .models import VideoHistory
            VideoHistory.objects.update_or_create(
                user=self.request.user, 
                video=video
            )
        else:
            # Invité / Anonyme : Historique en session
            guest_viewed = self.request.session.get('guest_viewed_videos', [])
            if video.id not in guest_viewed:
                guest_viewed.append(video.id)
                self.request.session['guest_viewed_videos'] = guest_viewed
            
            # Intérêts basés sur les catégories pour l'invité
            if video.category_id:
                interests = self.request.session.get('guest_interests', {})
                interests[str(video.category_id)] = interests.get(str(video.category_id), 0) + 1
                self.request.session['guest_interests'] = interests
            
        # Recommandations intelligentes adaptées excluant la vidéo en cours
        from .recommendations import get_recommended_videos
        all_recs = get_recommended_videos(self.request, limit=15)
        context['related_videos'] = [v for v in all_recs if v.id != video.id][:10]
        
        # Statut relationnel pour le Chat en direct
        uploader = video.uploader
        friendship_status = 'NONE'
        friend_request_id = None
        
        if self.request.user.is_authenticated and uploader and uploader != self.request.user:
            from apps.users.models import FriendRequest
            # 1. Vérifier si déjà amis
            if self.request.user.friends.filter(id=uploader.id).exists():
                friendship_status = 'ACCEPTED'
            else:
                # 2. Vérifier demande envoyée par moi
                req_sent = FriendRequest.objects.filter(sender=self.request.user, receiver=uploader).first()
                if req_sent:
                    friendship_status = 'PENDING_SENT' if req_sent.status == 'PENDING' else req_sent.status
                    friend_request_id = req_sent.id
                else:
                    # 3. Vérifier demande reçue
                    req_recv = FriendRequest.objects.filter(sender=uploader, receiver=self.request.user).first()
                    if req_recv:
                        friendship_status = 'PENDING_RECEIVED' if req_recv.status == 'PENDING' else req_recv.status
                        friend_request_id = req_recv.id
                        
        context['friendship_status'] = friendship_status
        context['friend_request_id'] = friend_request_id
        
        return context
class LibraryView(LoginRequiredMixin, TemplateView):
    template_name = 'videos/library.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['history'] = VideoHistory.objects.filter(user=user).select_related('video', 'video__category')[:12]
        context['favorites'] = user.favorites.all().select_related('category')[:12]
        context['my_videos'] = Video.objects.filter(uploader=user).select_related('category')[:12]
        return context

class CategoryListView(ListView):
    model = Category
    template_name = 'videos/category_list.html'
    context_object_name = 'categories'

class CategoryDetailView(DetailView):
    model = Category
    template_name = 'videos/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # On récupère les vidéos de cette catégorie (avec pagination si on veut)
        context['videos'] = self.object.videos.filter(is_published=True)[:24]
        return context

class TrendingListView(ListView):
    model = Video
    template_name = 'index.html' # On réutilise le template index
    context_object_name = 'videos'
    paginate_by = 12

    def get_queryset(self):
        # Les vidéos les plus vues avec optimisation
        return Video.objects.filter(is_published=True).select_related('category', 'uploader').order_by('-views_count')

class SearchView(ListView):
    model = Video
    template_name = 'index.html'
    context_object_name = 'videos'
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Video.objects.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) |
                Q(tags__name__icontains=query)
            ).distinct()
        return Video.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q')
        # On peut aussi suggérer des créateurs
        query = self.request.GET.get('q')
        if query:
            context['suggested_users'] = User.objects.filter(username__icontains=query)[:5]
        return context

def search_suggestions_view(request):
    query = request.GET.get('q', '')
    suggestions = []
    if len(query) > 1:
        videos = Video.objects.filter(title__icontains=query, is_published=True)[:8]
        for v in videos:
            suggestions.append({
                'title': v.title,
                'url': v.get_absolute_url()
            })
    return JsonResponse({'suggestions': suggestions})

class PhotoListView(ListView):
    model = Photo
    template_name = 'photos/photo_list.html'
    context_object_name = 'photos'
    paginate_by = 24

    def get_queryset(self):
        return Photo.objects.filter(is_published=True).select_related('uploader')

class PhotoDetailView(DetailView):
    model = Photo
    template_name = 'photos/photo_detail.html'
    context_object_name = 'photo'
# --- PUBLICATION MEMBRES ---

class VideoCreateView(LoginRequiredMixin, CreateView):
    model = Video
    form_class = VideoUploadForm
    template_name = 'videos/video_form.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.uploader = self.request.user
        form.instance.is_published = True  # Publication automatique comme demandé
        self.object = form.save()
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'redirect_url': self.object.get_absolute_url()
            })
            
        messages.success(self.request, "Votre vidéo a été publiée avec succès !")
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'errors': form.errors
            }, status=400)
        return super().form_invalid(form)

class PhotoCreateView(LoginRequiredMixin, CreateView):
    model = Photo
    form_class = PhotoUploadForm
    template_name = 'videos/photo_form.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.uploader = self.request.user
        messages.success(self.request, "Votre photo a été publiée avec succès !")
        return super().form_valid(form)

class AddCommentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # 1. Honeypot anti-spam check
        if request.POST.get('website_confirm'):
            return HttpResponse("Spam détecté.", status=400)

        content = request.POST.get('content')
        if not content:
            if request.headers.get('HX-Request'):
                return HttpResponse("Le commentaire ne peut pas être vide.", status=400)
            messages.error(request, "Le commentaire ne peut pas être vide.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # 2. Link & keyword spam filter
        from .forms import check_spam
        spam_error = check_spam(content)
        if spam_error:
            if request.headers.get('HX-Request'):
                return HttpResponse(spam_error, status=400)
            messages.error(request, spam_error)
            return redirect(request.META.get('HTTP_REFERER', '/'))
            
        video_id = request.POST.get('video_id')
        photo_id = request.POST.get('photo_id')
        
        if video_id:
            video = get_object_or_404(Video, id=video_id)
            comment = Comment.objects.create(author=request.user, video=video, content=content)
            if request.headers.get('HX-Request'):
                return render(request, 'videos/comment_single_fragment.html', {'comment': comment})
        elif photo_id:
            photo = get_object_or_404(Photo, id=photo_id)
            comment = Comment.objects.create(author=request.user, photo=photo, content=content)
            if request.headers.get('HX-Request'):
                return render(request, 'videos/comment_single_fragment.html', {'comment': comment})
            
        messages.success(request, "Commentaire publié avec succès !")
        return redirect(request.META.get('HTTP_REFERER', '/'))

def like_video_view(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    if request.user.is_authenticated:
        if video.likes.filter(id=request.user.id).exists():
            video.likes.remove(request.user)
            liked = False
        else:
            video.likes.add(request.user)
            liked = True
    else:
        video.anonymous_likes_count = F('anonymous_likes_count') + 1
        video.save(update_fields=['anonymous_likes_count'])
        video.refresh_from_db(fields=['anonymous_likes_count'])
        liked = True
    return JsonResponse({'liked': liked, 'count': video.total_likes})

@login_required
def like_photo_view(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)
    if photo.likes.filter(id=request.user.id).exists():
        photo.likes.remove(request.user)
        liked = False
    else:
        photo.likes.add(request.user)
        liked = True
    return JsonResponse({'liked': liked, 'count': photo.likes.count()})


class ShortsListView(ListView):
    """Interface mobile-first pour les vidéos verticales type TikTok."""
    model = Video
    template_name = 'videos/shorts_list.html'
    context_object_name = 'shorts'

    def get_queryset(self):
        return Video.objects.filter(is_published=True, is_short=True).order_by('?')

def like_video_ajax(request, video_id):
    """Action de like asynchrone pour les vidéos."""
    video = get_object_or_404(Video, id=video_id)
    liked = False
    if request.user.is_authenticated:
        if request.user in video.likes.all():
            video.likes.remove(request.user)
        else:
            video.likes.add(request.user)
            liked = True
    else:
        video.anonymous_likes_count = F('anonymous_likes_count') + 1
        video.save(update_fields=['anonymous_likes_count'])
        video.refresh_from_db(fields=['anonymous_likes_count'])
        liked = True
    return JsonResponse({'liked': liked, 'count': video.total_likes})
