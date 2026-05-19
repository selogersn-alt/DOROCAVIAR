import random
from apps.videos.models import Category, Video
from apps.marketing.models import PlatformSettings, Advertisement, Page
from apps.users.models import User

def run():
    print("Initialisation des données de test...")

    # 1. Platform Settings
    settings, _ = PlatformSettings.objects.get_or_create(pk=1)
    settings.site_name = "MegaVids Affiliate"
    settings.ad_clicks_before_video = 1
    settings.save()
    
    # 2. Catégories & Sous-Catégories
    cat_tech, _ = Category.objects.get_or_create(name="Technologie", slug="tech")
    Category.objects.get_or_create(name="Smartphones", slug="smartphones", parent=cat_tech)
    Category.objects.get_or_create(name="Tutoriels", slug="tutoriels", parent=cat_tech)
    
    cat_game, _ = Category.objects.get_or_create(name="Gaming", slug="gaming")
    Category.objects.get_or_create(name="eSport", slug="esport", parent=cat_game)
    Category.objects.get_or_create(name="Walkthroughs", slug="walkthroughs", parent=cat_game)
    
    # 3. Vidéos fictives
    sample_videos = [
        {"title": "Découverte du dernier iPhone 16", "cat": "smartphones", "embed": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
        {"title": "Tutoriel Python De Base à Avancé", "cat": "tutoriels", "embed": "https://www.youtube.com/embed/rfscVS0vtbw"},
        {"title": "Finale Mondiale League of Legends", "cat": "esport", "embed": "https://www.youtube.com/embed/vzHrjOMfHPY"},
        {"title": "Gameplay Complet Elden Ring", "cat": "walkthroughs", "embed": "https://www.youtube.com/embed/E3Huy2cdih0"},
        {"title": "Setup Gaming Ultime 2026", "cat": "tech", "embed": "https://www.youtube.com/embed/jNQXAC9IVRw"},
    ]
    
    for v_data in sample_videos:
        cat = Category.objects.get(slug=v_data['cat'])
        Video.objects.get_or_create(
            title=v_data['title'],
            defaults={
                'slug': v_data['title'].lower().replace(" ", "-"),
                'description': f"Description simulée pour {v_data['title']}. Abonnez-vous pour plus de contenu.",
                'embed_url': v_data['embed'],
                'thumbnail': f"https://source.unsplash.com/random/800x450/?{v_data['cat']}",
                'category': cat,
                'views_count': random.randint(100, 50000),
                'meta_title': f"{v_data['title']} - Regarder en Ligne",
            }
        )

    # 4. Pages (Legal, About)
    Page.objects.get_or_create(title="Conditions d'Utilisation", defaults={'content': "<h1>Conditions</h1><p>Contenu légal fictif...</p>"})
    Page.objects.get_or_create(title="Contact", defaults={'content': "<h1>Contactez-nous</h1><p>Pour la publicité, envoyez un mail à ads@domain.com</p>"})
    
    # 5. Publicités de Test
    Advertisement.objects.get_or_create(
        title="Popunder Régie Pub X",
        defaults={
            'ad_type': 'POPUNDER',
            'position': 'BACKGROUND',
            'code': "<script>console.log('Script Popunder Chargé - Simulation ouverture de popup');</script>"
        }
    )
    Advertisement.objects.get_or_create(
        title="Bannière Top Global",
        defaults={
            'ad_type': 'BANNER',
            'position': 'GLOBAL_TOP',
            'code': '<div style="background:red; color:white; padding:20px; text-align:center;">ESPACE BANNIERE RESPONSIVE 728x90</div>'
        }
    )

    print("Données générées avec succès !")

if __name__ == '__main__':
    run()
