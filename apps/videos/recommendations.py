import re
from django.utils import timezone
from django.db.models import Q
from .models import Video

def get_recommended_videos(request, limit=24):
    """
    Algorithme de recommandation additif premium pour DORO CAVIAR.
    Calcule un score personnalisé pour chaque vidéo en combinant :
      - Compte & Historique (exclut/demote le contenu déjà vu, boost les catégories préférées & likées)
      - Navigateur (priorise les Shorts verticaux sur Mobile, les grands formats sur Desktop)
      - Réseau WiFi / Vitesse (priorise le léger/Shorts si connexion lente, la HD si connexion rapide)
      - Nouveau contenu (les vidéos non visionnées sont mises en avant)
      - Récence (les vidéos récentes obtiennent un boost naturel)
    """
    qs = Video.objects.filter(is_published=True).select_related('category', 'uploader').prefetch_related('tags')
    
    # 1. HISTORIQUE DE VISIONNAGE & PRÉFÉRENCES DE COMPTE
    viewed_ids = set()
    pref_categories = {}
    
    if request.user.is_authenticated:
        # Récupère l'historique utilisateur de la base de données
        history = request.user.video_history.all().select_related('video')
        for h in history:
            viewed_ids.add(h.video_id)
            if h.video.category_id:
                pref_categories[h.video.category_id] = pref_categories.get(h.video.category_id, 0) + 1
                
        # Récupère les likes de l'utilisateur pour pondérer davantage ses goûts
        liked_videos = Video.objects.filter(likes=request.user)
        for lv in liked_videos:
            if lv.category_id:
                pref_categories[lv.category_id] = pref_categories.get(lv.category_id, 0) + 2  # Poids double pour les likes !
    else:
        # Pour les invités, vérifie l'historique et les intérêts stockés en session
        guest_history = request.session.get('guest_viewed_videos', [])
        viewed_ids.update(guest_history)
        
        guest_interests = request.session.get('guest_interests', {})
        for cat_id, weight in guest_interests.items():
            try:
                pref_categories[int(cat_id)] = weight
            except ValueError:
                pass

    # 2. DÉTECTION DU NAVIGATEUR ET SUPPORT MOBILE
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    is_mobile = any(x in user_agent for x in ['iphone', 'android', 'mobile', 'phone', 'ipod', 'opera mini', 'blackberry'])
    
    # 3. DÉTECTION DU RÉSEAU (Reçu via Cookie de l'API Connection)
    network_quality = request.COOKIES.get('net_quality', 'fast')
    if request.GET.get('net_quality'):
        network_quality = request.GET.get('net_quality')
        
    # Notation et classement
    scored_videos = []
    for video in qs:
        score = 0
        
        # A. Nouveau contenu vs Contenu vu
        if video.id not in viewed_ids:
            score += 100  # Gros avantage pour découvrir du nouveau contenu !
        else:
            score -= 40   # Recule le contenu déjà vu
            
        # B. Préférences de compte/catégories
        if video.category_id in pref_categories:
            score += min(pref_categories[video.category_id] * 8, 40)
            
        # C. Adaptation au Navigateur (Mobile vs Desktop)
        if is_mobile:
            if video.is_short:
                score += 35  # Format vertical idéal sur mobile
        else:
            if not video.is_short:
                score += 25  # Format horizontal plus immersif sur grand écran
                
        # D. Vitesse Réseau (Wifi vs Data lente)
        if network_quality == 'slow':
            if video.is_short:
                score += 30  # Contenu plus léger à charger
        else:
            if not video.is_short:
                score += 15  # Contenu haute qualité apprécié sur connexion rapide
                
        # E. Récence
        days_old = (timezone.now() - video.created_at).days
        if days_old <= 3:
            score += 20
        elif days_old <= 10:
            score += 10
            
        scored_videos.append((score, video))
        
    # Tri descendant par score
    scored_videos.sort(key=lambda x: x[0], reverse=True)
    
    # Retourne la liste des vidéos ordonnées
    return [item[1] for item in scored_videos[:limit]]
