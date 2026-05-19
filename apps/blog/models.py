from django.db import models
from django.conf import settings
from autoslug import AutoSlugField
from ckeditor.fields import RichTextField
from taggit.managers import TaggableManager

class BlogCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = AutoSlugField(populate_from='name', unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Categories de Blog"
        
    def __str__(self):
        return self.name

class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
    )
    
    title = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='title', unique=True)
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, related_name='posts')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    featured_image = models.ImageField(upload_to='blog/featured/', help_text="Image principale de l'article")
    content = RichTextField(config_name='default')
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    tags = TaggableManager(blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True, help_text="Titre pour les moteurs de recherche")
    meta_description = models.TextField(blank=True, help_text="Description pour les moteurs de recherche")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('blog:post_detail', kwargs={'slug': self.slug})
