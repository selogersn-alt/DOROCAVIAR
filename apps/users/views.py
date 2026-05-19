from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, View
from django.db.models import Q, Sum
from django.contrib import messages
from django.urls import reverse_lazy
from django import forms
from .models import User, FriendRequest, PrivateMessage
from apps.videos.models import Video, Photo

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas")
        return cleaned_data

def register_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            messages.success(request, "Inscription réussie ! Bienvenue sur Dorocaviar.")
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'users/signup.html', {'form': form})

@login_required
def dashboard_view(request):
    # Statistiques privées
    uploaded_videos = Video.objects.filter(uploader=request.user).order_by('-created_at')
    uploaded_photos = Photo.objects.filter(uploader=request.user).order_by('-created_at')
    
    total_views_agg = uploaded_videos.aggregate(total=Sum('views_count'))['total']
    total_views = total_views_agg if total_views_agg else 0
    
    context = {
        'total_views': total_views,
        'follower_count': request.user.followers.count(),
        'friend_count': request.user.friends.count(),
        'recent_videos': uploaded_videos[:5],
        'recent_photos': uploaded_photos[:5],
    }
    return render(request, 'users/dashboard.html', context)

def public_profile_view(request, username):
    target_user = get_object_or_404(User, username=username)
    videos = Video.objects.filter(uploader=target_user, is_published=True).order_by('-created_at')
    photos = Photo.objects.filter(uploader=target_user).order_by('-created_at')
    
    is_friend = False
    has_pending_request = False
    
    if request.user.is_authenticated:
        is_friend = request.user.friends.filter(id=target_user.id).exists()
        has_pending_request = FriendRequest.objects.filter(
            sender=request.user, receiver=target_user, status='PENDING'
        ).exists()

    context = {
        'target_user': target_user,
        'videos': videos,
        'photos': photos,
        'is_friend': is_friend,
        'has_pending_request': has_pending_request,
        'is_own_profile': request.user == target_user if request.user.is_authenticated else False
    }
    return render(request, 'users/profile_public.html', context)
# --- MESSAGERIE ET RESEAU SOCIAL ---

class ChatListView(LoginRequiredMixin, ListView):
    template_name = 'users/chat_list.html'
    context_object_name = 'conversations'

    def get_queryset(self):
        # Récupère tous les utilisateurs avec qui j'ai un historique de messages
        user = self.request.user
        messages = PrivateMessage.objects.filter(Q(sender=user) | Q(recipient=user))
        user_ids = set()
        for msg in messages:
            if msg.sender == user:
                user_ids.add(msg.recipient.id)
            else:
                user_ids.add(msg.sender.id)
        return User.objects.filter(id__in=user_ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_requests'] = FriendRequest.objects.filter(receiver=self.request.user, status='PENDING')
        context['friends_list'] = self.request.user.friends.all()
        return context

class FriendsListView(LoginRequiredMixin, ListView):
    template_name = 'users/friends_list.html'
    context_object_name = 'friends'

    def get_queryset(self):
        return self.request.user.friends.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import FriendRequest
        context['pending_requests'] = FriendRequest.objects.filter(receiver=self.request.user, status='PENDING')
        context['pending_requests_count'] = context['pending_requests'].count()
        return context

class ChatDetailView(LoginRequiredMixin, View):
    def get(self, request, username):
        other_user = get_object_or_404(User, username=username)
        # Vérification si amis
        if not request.user.friends.filter(id=other_user.id).exists():
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == 'true':
                return JsonResponse({'error': 'Unauthorized'}, status=403)
            messages.error(request, "Vous devez être amis pour discuter en privé.")
            return redirect('chat_list')
        
        chat_messages = PrivateMessage.objects.filter(
            (Q(sender=request.user) & Q(recipient=other_user)) |
            (Q(sender=other_user) & Q(recipient=request.user))
        ).order_by('created_at')
        
        # Marquer comme lu
        chat_messages.filter(recipient=request.user, is_read=False).update(is_read=True)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == 'true':
            data = []
            for m in chat_messages:
                data.append({
                    'id': m.id,
                    'content': m.content,
                    'image': m.image.url if m.image else None,
                    'created_at': m.created_at.strftime('%H:%M'),
                    'sender_username': m.sender.username
                })
            return JsonResponse({'messages': data})
            
        return render(request, 'users/chat_detail.html', {
            'other_user': other_user,
            'chat_messages': chat_messages
        })

    def post(self, request, username):
        other_user = get_object_or_404(User, username=username)
        content = request.POST.get('content')
        image = request.FILES.get('image')
        
        if content or image:
            msg = PrivateMessage.objects.create(
                sender=request.user,
                recipient=other_user,
                content=content,
                image=image
            )
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == 'true':
                return JsonResponse({
                    'status': 'success',
                    'message': {
                        'id': msg.id,
                        'content': msg.content,
                        'image': msg.image.url if msg.image else None,
                        'created_at': msg.created_at.strftime('%H:%M'),
                        'sender_username': msg.sender.username
                    }
                })
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == 'true':
            return JsonResponse({'status': 'empty'})
            
        return redirect('chat_detail', username=username)

class AcceptFriendRequestView(LoginRequiredMixin, View):
    def post(self, request, request_id):
        friend_request = get_object_or_404(FriendRequest, id=request_id, receiver=request.user)
        friend_request.status = 'ACCEPTED'
        friend_request.save()
        
        # Ajouter à la liste d'amis réciproque
        request.user.friends.add(friend_request.sender)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == 'true':
            return JsonResponse({
                'status': 'success',
                'friendship_status': 'ACCEPTED',
                'friend_username': friend_request.sender.username
            })
            
        messages.success(request, f"Vous êtes maintenant ami avec {friend_request.sender.username}")
        return redirect('chat_list')

class SendFriendRequestView(LoginRequiredMixin, View):
    def post(self, request, username):
        receiver = get_object_or_404(User, username=username)
        if receiver == request.user:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == 'true':
                return JsonResponse({'error': 'Self request forbidden'}, status=400)
            messages.warning(request, "Vous ne pouvez pas vous ajouter vous-même.")
            return redirect('chat_list')
            
        obj, created = FriendRequest.objects.get_or_create(sender=request.user, receiver=receiver)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == 'true':
            return JsonResponse({
                'status': 'success',
                'friendship_status': 'PENDING_SENT',
                'friend_request_id': obj.id
            })
            
        messages.success(request, f"Demande d'ami envoyée à {username}")
        return redirect('chat_list')

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['profile_image', 'cover_image', 'bio']
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        return self.request.user

from .utils import create_notification

class FollowUserView(LoginRequiredMixin, View):
    def post(self, request, username):
        target_user = get_object_or_404(User, username=username)
        if target_user == request.user:
            return JsonResponse({'error': 'Self follow forbidden'}, status=400)
            
        if request.user in target_user.followers.all():
            target_user.followers.remove(request.user)
            action = 'unfollowed'
        else:
            target_user.followers.add(request.user)
            action = 'followed'
            # Créer notification
            create_notification(
                recipient=target_user,
                sender=request.user,
                notification_type='FOLLOW',
                text=f"{request.user.username} s'est abonné à votre chaîne.",
                link=f"/@{request.user.username}/"
            )
            
        return JsonResponse({'action': action, 'count': target_user.followers.count()})

@login_required
def notification_list_view(request):
    """Affiche toutes les notifications de l'utilisateur."""
    notifs = request.user.notifications.all()
    # Marquer tout comme lu
    notifs.update(is_read=True)
    return render(request, 'users/notifications.html', {'notifications': notifs})

@login_required
def notification_count_view(request):
    """Retourne le nombre total de notifications."""
    unread_messages = PrivateMessage.objects.filter(recipient=request.user, is_read=False).count()
    pending_friends = FriendRequest.objects.filter(receiver=request.user, status='PENDING').count()
    unread_notifs = request.user.notifications.filter(is_read=False).count()
    
    return JsonResponse({
        'total': unread_messages + pending_friends + unread_notifs,
        'messages': unread_messages,
        'friends': pending_friends,
        'notifications': unread_notifs
    })

@login_required
def chat_poll_view(request, username):
    """Vérifie s'il y a de nouveaux messages dans une conversation."""
    other_user = get_object_or_404(User, username=username)
    
    # Sécurité: seuls les amis peuvent poll
    if not request.user.friends.filter(id=other_user.id).exists():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    last_id = request.GET.get('last_id')
    messages_query = PrivateMessage.objects.filter(
        recipient=request.user, 
        sender=other_user
    )
    
    if last_id:
        messages_query = messages_query.filter(id__gt=last_id)
        
    # Marquer comme lu
    messages_query.update(is_read=True)
    
    data = []
    for m in messages_query:
        data.append({
            'id': m.id,
            'content': m.content,
            'image': m.image.url if m.image else None,
            'created_at': m.created_at.strftime('%H:%M'),
            'sender_username': m.sender.username
        })
        
    return JsonResponse({'messages': data})

from django.http import JsonResponse
