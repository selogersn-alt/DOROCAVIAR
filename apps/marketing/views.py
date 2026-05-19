from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count
from apps.videos.models import Video, Photo, Category
from apps.users.models import User
from .models import Page, Report, AffiliateLink

def custom_page_view(request, slug):
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, 'marketing/page.html', {'page': page})

@login_required
def report_content_view(request):
    if request.method == 'POST':
        reason = request.POST.get('reason')
        message = request.POST.get('message', '')
        video_id = request.POST.get('video_id')
        photo_id = request.POST.get('photo_id')
        
        report = Report(
            reporter=request.user,
            reason=reason,
            message=message
        )
        
        if video_id:
            report.video = get_object_or_404(Video, id=video_id)
        elif photo_id:
            report.photo = get_object_or_404(Photo, id=photo_id)
            
        report.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == 'true':
            from django.http import JsonResponse
            return JsonResponse({'status': 'success', 'message': 'Merci, votre signalement a été enregistré.'})
            
        messages.success(request, "Merci, votre signalement a été envoyé à l'équipe de modération.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    return redirect('/')

@staff_member_required
def admin_stats_view(request):
    """Tableau de bord de statistiques pour le Business Owner."""
    # Période de référence (Aujourd'hui)
    today = timezone.now().date()
    
    # 1. Chiffres Clés (KPIs)
    total_videos = Video.objects.count()
    total_users = User.objects.count()
    total_views = Video.objects.aggregate(total=Sum('views_count'))['total'] or 0
    total_clicks = AffiliateLink.objects.aggregate(total=Sum('clicks'))['total'] or 0
    pending_reports_count = Report.objects.filter(is_resolved=False).count()
    
    # 2. Performance des Catégories
    top_categories = Category.objects.annotate(
        video_count=Count('videos')
    ).order_by('-video_count')[:5]
    
    # 3. Derniers Signalements
    recent_reports = Report.objects.filter(is_resolved=False).order_by('-created_at')[:5]
    
    # 4. Liens d'Affiliation les plus performants
    top_links = AffiliateLink.objects.order_by('-clicks')[:5]
    
    context = {
        'total_videos': total_videos,
        'total_users': total_users,
        'total_views': total_views,
        'total_clicks': total_clicks,
        'pending_reports': pending_reports_count,
        'top_categories': top_categories,
        'recent_reports': recent_reports,
        'top_links': top_links,
        'new_users_today': User.objects.filter(date_joined__date=today).count(),
        'title': "Dorocaviar - Business Stats"
    }
    
    return render(request, 'admin/stats_dashboard.html', context)

from django.http import HttpResponse

def robots_txt_view(request):
    """Fichier robots.txt pour guider les moteurs de recherche."""
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Allow: /",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

def html_sitemap_view(request):
    """Plan du site visuel et premium pour l'utilisateur et le SEO."""
    categories = Category.objects.all().prefetch_related('videos')
    videos = Video.objects.filter(is_published=True).order_by('-created_at')[:100]
    pages = Page.objects.filter(is_published=True)
    return render(request, 'marketing/sitemap.html', {
        'categories': categories,
        'videos': videos,
        'pages': pages
    })
