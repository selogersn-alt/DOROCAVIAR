import csv
import io
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from .models import Category, Video, ImportSource

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'video_count')
    search_fields = ('name',)
    change_list_template = "admin/videos/category/change_list_import.html"

    def video_count(self, obj):
        return obj.videos.count()

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='category_import_csv'),
        ]
        return custom_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES.get("csv_file")
            if not csv_file:
                self.message_user(request, "Veuillez choisir un fichier.", messages.ERROR)
                return redirect("..")
            
            if not csv_file.name.endswith('.csv'):
                self.message_user(request, "Ce n'est pas un fichier CSV.", messages.ERROR)
                return redirect("..")

            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            reader = csv.reader(io_string, delimiter=',', quotechar='"')
            
            count = 0
            for row in reader:
                if not row: continue
                name = row[0]
                description = row[1] if len(row) > 1 else ""
                parent_slug = row[2].strip() if len(row) > 2 and row[2] else None
                
                parent = None
                if parent_slug:
                    parent = Category.objects.filter(slug=parent_slug).first()
                
                _, created = Category.objects.update_or_create(
                    name=name,
                    defaults={'description': description, 'parent': parent}
                )
                if created: count += 1
            
            self.message_user(request, f"Importation réussie : {count} nouvelles catégories créées.")
            return redirect("..")
            
        return render(request, "admin/videos/category/import_csv.html", {"title": "Importer Catégories"})

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'views_count', 'created_at', 'thumbnail_preview')
    list_filter = ('is_published', 'category', 'created_at')
    search_fields = ('title', 'description', 'tags__name')
    autocomplete_fields = ['category']
    date_hierarchy = 'created_at'
    change_list_template = "admin/videos/video/change_list_import.html"
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'tags')
        }),
        ('Video Source', {
            'fields': ('embed_url', 'source_url', 'thumbnail', 'thumbnail_file')
        }),
        ('Status & Stats', {
            'fields': ('is_published', 'views_count')
        }),
        ('SEO Meta Tags', {
            'classes': ('collapse',),
            'fields': ('meta_title', 'meta_description')
        }),
    )

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="100" style="border-radius: 5px;" />', obj.thumbnail)
        return "No Thumbnail"
    thumbnail_preview.short_description = 'Preview'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-videos/', self.admin_site.admin_view(self.import_videos), name='video_import_bulk'),
        ]
        return custom_urls + urls

    def import_videos(self, request):
        from apps.users.models import User
        
        if request.method == "POST":
            cat_id = request.POST.get("category")
            uploader_id = request.POST.get("uploader")
            bulk_urls = request.POST.get("bulk_urls", "")
            csv_file = request.FILES.get("csv_file")
            
            if not cat_id:
                self.message_user(request, "Veuillez choisir une catégorie.", messages.ERROR)
                return redirect("..")
                
            category = get_object_or_404(Category, id=cat_id)
            uploader = None
            if uploader_id:
                uploader = User.objects.filter(id=uploader_id).first()
                
            imported_count = 0
            
            # Traiter les URLs collées
            if bulk_urls.strip():
                lines = [line.strip() for line in bulk_urls.split('\n') if line.strip()]
                for line in lines:
                    embed_url, thumbnail_url, title = self._parse_video_url(line)
                    Video.objects.create(
                        title=title,
                        embed_url=embed_url,
                        thumbnail=thumbnail_url,
                        category=category,
                        uploader=uploader,
                        is_published=True
                    )
                    imported_count += 1
                    
            # Traiter le fichier CSV
            if csv_file:
                if csv_file.name.endswith('.csv'):
                    data_set = csv_file.read().decode('UTF-8')
                    io_string = io.StringIO(data_set)
                    reader = csv.reader(io_string, delimiter=',', quotechar='"')
                    for row in reader:
                        if not row:
                            continue
                        title = row[0].strip()
                        url = row[1].strip() if len(row) > 1 else ""
                        desc = row[2].strip() if len(row) > 2 else ""
                        
                        if url:
                            embed_url, thumbnail_url, fallback_title = self._parse_video_url(url)
                            if not title:
                                title = fallback_title
                                
                            Video.objects.create(
                                title=title,
                                description=desc,
                                embed_url=embed_url,
                                thumbnail=thumbnail_url,
                                category=category,
                                uploader=uploader,
                                is_published=True
                            )
                            imported_count += 1
                else:
                    self.message_user(request, "Le fichier fourni n'est pas un CSV valide.", messages.ERROR)

            self.message_user(request, f"Importation réussie : {imported_count} vidéos ont été créées avec succès.")
            return redirect("..")
            
        context = {
            "title": "Importer des vidéos en masse",
            "categories": Category.objects.all(),
            "users": User.objects.all(),
        }
        return render(request, "admin/videos/video/import_videos.html", context)

    def _parse_video_url(self, url):
        url = url.strip()
        title = f"Vidéo {url.split('/')[-1][:30]}"
        embed_url = url
        thumbnail_url = ""
        
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
                embed_url = f"https://www.youtube.com/embed/{video_id}"
                thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                title = f"YouTube {video_id}"
                
        elif "vimeo.com" in url:
            video_id = url.split("vimeo.com/")[-1].split("?")[0]
            if video_id.isdigit():
                embed_url = f"https://player.vimeo.com/video/{video_id}"
                title = f"Vimeo {video_id}"
                
        return embed_url, thumbnail_url, title

@admin.register(ImportSource)
class ImportSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_type', 'is_active', 'last_run')
    list_filter = ('source_type', 'is_active')
    actions = ['trigger_import']
    
    def trigger_import(self, request, queryset):
        # This will be connected to Celery tasks later
        self.message_user(request, "Import triggered for selected sources.")
    trigger_import.short_description = "Run import now"
