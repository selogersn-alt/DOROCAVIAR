from .models import PlatformSettings, Advertisement, Page, MenuLink

def platform_context(request):
    # Charge la configuration globale
    settings_obj = PlatformSettings.load()
    
    # Charge les publicités qui doivent s'afficher partout (Popunders, Bannières Top globales...)
    popunders = Advertisement.objects.filter(position='BACKGROUND', is_active=True).order_by('-weight')
    top_banners = Advertisement.objects.filter(position='GLOBAL_TOP', is_active=True).order_by('-weight')
    bottom_banners = Advertisement.objects.filter(position='GLOBAL_BOTTOM', is_active=True).order_by('-weight')
    overlay_ads = Advertisement.objects.filter(position='VIDEO_PLAYER_OVERLAY', is_active=True).order_by('-weight')
    
    return {
        'platform': settings_obj,
        'ads_popunders': popunders,
        'ads_top': top_banners,
        'ads_bottom': bottom_banners,
        'ads_overlay': overlay_ads,
        'header_links': MenuLink.objects.filter(is_active=True),
        'footer_pages': Page.objects.filter(is_published=True),
    }
