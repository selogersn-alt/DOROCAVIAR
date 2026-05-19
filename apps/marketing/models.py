from django.db import models
from autoslug import AutoSlugField
from apps.users.models import User
from apps.videos.models import Video, Photo

class PlatformSettings(models.Model):
    site_name = models.CharField(max_length=100, default="Dorocaviar")
    site_slogan = models.CharField(max_length=255, blank=True, help_text="Slogan sous le logo")
    
    # --- DESIGN (White-Label) ---
    primary_color = models.CharField(max_length=7, default="#E6007E", help_text="Couleur principale (ex: #E6007E)")
    secondary_color = models.CharField(max_length=7, default="#000000", help_text="Couleur secondaire")
    
    logo = models.ImageField(upload_to='branding/', blank=True, null=True)
    favicon = models.ImageField(upload_to='branding/', blank=True, null=True)
    
    # --- FONCTIONNALITÉS MODULAIRES ---
    enable_social = models.BooleanField(default=True, help_text="Activer Amis, Profils, Likes")
    enable_chat = models.BooleanField(default=True, help_text="Activer la messagerie privée")
    enable_member_upload = models.BooleanField(default=True, help_text="Permettre aux membres d'uploader")
    
    # --- MONÉTISATION (GHOST CLICKS) ---
    ad_clicks_before_video = models.PositiveIntegerField(default=0)
    AD_STRATEGY_CHOICES = (
        ('ALWAYS', 'Sur TOUTES les vidéos'),
        ('EVERY_3', 'Toutes les 3 vidéos uniquement'),
        ('DISABLED', 'Désactivé'),
    )
    video_ad_strategy = models.CharField(max_length=15, choices=AD_STRATEGY_CHOICES, default='DISABLED')
    invisible_ad_link = models.URLField(blank=True, null=True)
    invisible_ad_active = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Configuration Générale"
        verbose_name_plural = "Configuration Générale"
    
    def __str__(self):
        return "Global Platform Settings"

    def save(self, *args, **kwargs):
        self.pk = 1 # Force single instance
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class Advertisement(models.Model):
    AD_TYPES = (
        ('BANNER', 'Banner (Image/HTML)'),
        ('POPUNDER', 'Pop-under (JS)'),
        ('INTERSTITIAL', 'Interstitial / Overlay (JS)'),
    )
    POSITIONS = (
        ('GLOBAL_TOP', 'Global - Top Header'),
        ('GLOBAL_BOTTOM', 'Global - Bottom Footer'),
        ('SIDEBAR', 'Sidebar Column'),
        ('VIDEO_PLAYER_OVERLAY', 'Over the Video Player'),
        ('BACKGROUND', 'Background/Popunder script'),
    )
    title = models.CharField(max_length=100)
    ad_type = models.CharField(max_length=20, choices=AD_TYPES, default='BANNER')
    position = models.CharField(max_length=25, choices=POSITIONS)
    
    code = models.TextField(help_text="Code JS, Iframe ou HTML fourni par la régie publicitaire")
    image = models.ImageField(upload_to='ads/', null=True, blank=True, help_text="Optionnel: si vous uploadez votre propre bannière")
    link = models.URLField(blank=True, help_text="Optionnel: lien de redirection si vous utilisez l'image ci-dessus")
    
    frequency_cap = models.PositiveIntegerField(default=0, help_text="Limiter l'affichage: X vues par utilisateur (0 = toujours afficher)")
    weight = models.PositiveIntegerField(default=1, help_text="Priorité d'affichage (plus c'est élevé, plus ça s'affiche souvent)")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_ad_type_display()})"

class AffiliateLink(models.Model):
    name = models.CharField(max_length=255)
    original_url = models.URLField(help_text="Le vrai lien fourni par la plateforme d'affiliation")
    tracking_url = models.URLField(unique=True, help_text="L'URL propre sur votre site qui redirigera vers l'affiliation")
    clicks = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.clicks} clicks)"

class Page(models.Model):
    title = models.CharField(max_length=200)
    slug = AutoSlugField(populate_from='title', unique=True)
    content = models.TextField(help_text="Le contenu de la page (HTML ou Texte)")
    content_format = models.CharField(
        max_length=10, 
        choices=(('HTML', 'HTML brute'), ('TEXT', 'Texte brut (sauts de ligne automatiques)')), 
        default='HTML', 
        help_text="Détermine si le contenu est interprété comme du code HTML brut ou du texte brut."
    )
    is_published = models.BooleanField(default=True)
    
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    
    def __str__(self):
        return self.title

class MenuLink(models.Model):
    title = models.CharField(max_length=100)
    url = models.CharField(max_length=255, help_text="URL locale (ex: /trending/) ou absolue (ex: https://...)")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
        
    def __str__(self):
        return self.title

class Report(models.Model):
    REASON_CHOICES = (
        ('SPAM', 'Spam ou publicité'),
        ('INAPPROPRIATE', 'Contenu inapproprié / Adulte'),
        ('VIOLENCE', 'Violence ou haine'),
        ('COPYRIGHT', 'Atteinte aux droits d\'auteur'),
        ('OTHER', 'Autre raison'),
    )
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_submitted')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    message = models.TextField(blank=True, help_text="Détails supplémentaires sur le signalement")
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Signalement {self.reason} par {self.reporter.username}"
