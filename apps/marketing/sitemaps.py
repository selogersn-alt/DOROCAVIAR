from django.contrib.sitemaps import Sitemap
from apps.videos.models import Video, Category

class VideoSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Video.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        from django.urls import reverse
        return reverse('video_detail', args=[obj.slug])

class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        # We need to implement category view later
        return f"/category/{obj.slug}/"
