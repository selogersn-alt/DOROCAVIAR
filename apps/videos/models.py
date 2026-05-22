from django.db import models
from django.utils.text import slugify
from autoslug import AutoSlugField
from taggit.managers import TaggableManager
from apps.users.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = AutoSlugField(populate_from='name', unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    affiliate_link = models.URLField(blank=True, null=True, help_text="Lien d'affiliation spécifique pour cette catégorie (utilisé pour les clics invisibles).")
    
    class Meta:
        verbose_name_plural = "Categories"
        
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

class Video(models.Model):
    title = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='title', unique=True)
    description = models.TextField(blank=True)
    thumbnail = models.URLField(max_length=500, blank=True)
    thumbnail_file = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    video_file = models.FileField(upload_to='videos/', null=True, blank=True, help_text="Uploader un fichier vidéo direct")
    embed_url = models.TextField(blank=True, null=True, help_text="Coller un lien ou le code d'intégration iframe complet")
    source_url = models.URLField(max_length=500, blank=True)
    
    is_short = models.BooleanField(default=False, help_text="Format vertical (9:16) type Reels/TikTok")
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='videos')
    tags = TaggableManager(blank=True)
    
    # SYSTEME SOCIAL ET UGC (Contenu Généré par les Utilisateurs)
    uploader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_videos')
    likes = models.ManyToManyField(User, related_name='liked_videos', blank=True)
    anonymous_likes_count = models.PositiveIntegerField(default=0)
    
    @property
    def total_likes(self):
        return self.likes.count() + self.anonymous_likes_count
        
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)
    
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        if self.category:
            return reverse('video_detail', kwargs={'category_slug': self.category.slug, 'slug': self.slug})
        return reverse('video_detail_no_cat', kwargs={'slug': self.slug})

    @staticmethod
    def convert_url_to_embed(url):
        """
        Convertit une URL de page vidéo en URL d'intégration (embed) valide.
        Supporte YouTube, Vimeo, Dailymotion, XVideos, XHamster, Pornhub, RedTube, etc.
        Retourne l'URL d'embed propre ou None si non reconnu.
        """
        if not url:
            return None
        url = url.strip()

        # Déjà un iframe HTML -> on ne touche pas
        if url.startswith("<"):
            return url

        from urllib.parse import urlparse, parse_qs

        # --- YouTube ---
        if "youtube.com/watch" in url:
            parsed = urlparse(url)
            video_id = parse_qs(parsed.query).get('v', [None])[0]
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}"
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[-1].split("?")[0]
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}"
        elif "youtube.com/embed/" in url:
            return url  # Déjà bon

        # --- Vimeo ---
        elif "vimeo.com" in url and "player.vimeo.com" not in url:
            video_id = url.split("vimeo.com/")[-1].split("?")[0]
            if video_id.isdigit():
                return f"https://player.vimeo.com/video/{video_id}"

        # --- Dailymotion ---
        elif "dailymotion.com/video/" in url:
            video_id = url.split("/video/")[-1].split("_")[0].split("?")[0]
            if video_id:
                return f"https://www.dailymotion.com/embed/video/{video_id}"
        elif "dailymotion.com/embed" in url:
            return url

        # --- XVideos ---
        elif "xvideos.com" in url:
            # Format: /video.XXXXXXX/slug -> embedframe/XXXXXXX
            import re
            # Essayer d'extraire l'ID depuis video.XXXXXXX
            match = re.search(r'/video\.([a-z0-9]+)/', url)
            if match:
                video_id = match.group(1)
                return f"https://www.xvideos.com/embedframe/{video_id}"
            # Déjà une URL embed
            if "embedframe" in url:
                return url

        # --- XHamster ---
        elif "xhamster.com" in url:
            # Format: /videos/slug-XXXXXXX -> /xembed.php?video=XXXXXXX
            import re
            match = re.search(r'-(\d+)$', url.rstrip('/').split('?')[0])
            if match:
                video_id = match.group(1)
                return f"https://xhamster.com/xembed.php?video={video_id}"
            if "xembed" in url:
                return url

        # --- Pornhub ---
        elif "pornhub.com" in url:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            video_id = params.get('viewkey', [None])[0]
            if video_id:
                return f"https://www.pornhub.com/embed/{video_id}"
            if "/embed/" in url:
                return url

        # --- RedTube ---
        elif "redtube.com" in url:
            import re
            match = re.search(r'redtube\.com/(\d+)', url)
            if match:
                video_id = match.group(1)
                return f"https://embed.redtube.com/?id={video_id}&bgcolor=000000"

        # --- Tube8 ---
        elif "tube8.com" in url:
            import re
            match = re.search(r'tube8\.com/[^/]+/[^/]+/(\d+)', url)
            if match:
                video_id = match.group(1)
                return f"https://www.tube8.com/embed/{video_id}/"

        # URL non reconnue - retourner None pour signaler qu'on ne sait pas intégrer
        return None

    @property
    def get_embed_url(self):
        """Retourne l'URL d'embed prête à l'emploi pour le template."""
        if self.video_file:
            return None  # On utilise le player <video> natif
        if not self.embed_url:
            return None
        converted = self.convert_url_to_embed(self.embed_url)
        return converted or self.embed_url  # Fallback sur l'URL brute

    def save(self, *args, **kwargs):
        if not self.meta_title:
            self.meta_title = self.title

        # Convertir l'embed_url en URL d'intégration propre pour toutes les plateformes
        if self.embed_url and not self.embed_url.strip().startswith("<"):
            converted = self.convert_url_to_embed(self.embed_url)
            if converted:
                self.embed_url = converted

                # Auto-miniature YouTube
                if "youtube.com/embed/" in self.embed_url and not self.thumbnail:
                    video_id = self.embed_url.split("/embed/")[-1].split("?")[0]
                    self.thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

        # Mettre à jour l'URL textuelle de la miniature si on a une miniature sous forme de fichier local/distant
        if self.thumbnail_file and (not self.thumbnail or self.thumbnail != self.thumbnail_file.url):
            self.thumbnail = self.thumbnail_file.url

        super().save(*args, **kwargs)

class Photo(models.Model):
    title = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='title', unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='photos/')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='photos')
    
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_photos')
    likes = models.ManyToManyField(User, related_name='liked_photos', blank=True)
    
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        if self.category:
            return reverse('photo_detail', kwargs={'category_slug': self.category.slug, 'slug': self.slug})
        return reverse('photo_detail_no_cat', kwargs={'slug': self.slug})

class Comment(models.Model):
    video = models.ForeignKey(Video, related_name='comments', on_delete=models.CASCADE, null=True, blank=True)
    photo = models.ForeignKey(Photo, related_name='comments', on_delete=models.CASCADE, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class ImportSource(models.Model):
    SOURCE_TYPES = (
        ('API', 'External API'),
        ('SCRAPE', 'Web Scraping'),
    )
    name = models.CharField(max_length=100)
    source_type = models.CharField(max_length=10, choices=SOURCE_TYPES)
    base_url = models.URLField()
    config = models.JSONField(help_text="Configuration for the importer (selectors, API keys, etc.)")
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.source_type})"
class VideoHistory(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='video_history')
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-viewed_at']
        unique_together = ('user', 'video')

    def __str__(self):
        return f"{self.user.username} a vu {self.video.title}"

@receiver(post_save, sender=Video)
def trigger_video_processing(sender, instance, created, **kwargs):
    """Déclenche le traitement vidéo après l'enregistrement."""
    if getattr(instance, '_ffmpeg_processed', False):
        return
    if instance.video_file:
        # Importer ici pour éviter les imports circulaires
        from .tasks import process_uploaded_video_task
        import threading
        # Exécuter dans un thread séparé après la validation de la transaction SQL
        # pour éviter de bloquer l'interface et de dépendre de Celery/Redis
        transaction.on_commit(lambda: threading.Thread(target=process_uploaded_video_task, args=(instance.id,)).start())
