from django.db import models
from django.utils.text import slugify
from autoslug import AutoSlugField
from taggit.managers import TaggableManager
from apps.users.models import User

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

    def save(self, *args, **kwargs):
        if not self.meta_title:
            self.meta_title = self.title
            
        # Formater l'url d'intégration si c'est YouTube ou Vimeo (et que ce n'est pas un code HTML d'iframe)
        if self.embed_url:
            url = self.embed_url.strip()
            if not url.startswith("<"):
                if "youtube.com/watch" in url or "youtu.be" in url or "youtube.com/embed" in url:
                    video_id = None
                    if "youtube.com/watch" in url:
                        from urllib.parse import urlparse, parse_qs
                        parsed = urlparse(url)
                        video_id = parse_qs(parsed.query).get('v', [None])[0]
                    elif "youtu.be/" in url:
                        video_id = url.split("youtu.be/")[-1].split("?")[0]
                    elif "youtube.com/embed/" in url:
                        video_id = url.split("youtube.com/embed/")[-1].split("?")[0]
                        
                    if video_id:
                        self.embed_url = f"https://www.youtube.com/embed/{video_id}"
                        if not self.thumbnail:
                            self.thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                            
                elif "vimeo.com" in url and "player.vimeo.com" not in url:
                    video_id = url.split("vimeo.com/")[-1].split("?")[0]
                    if video_id.isdigit():
                        self.embed_url = f"https://player.vimeo.com/video/{video_id}"
                    
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
