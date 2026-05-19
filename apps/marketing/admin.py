from django.contrib import admin
from .models import Advertisement, AffiliateLink, PlatformSettings, Page, Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reason', 'reporter', 'content_object', 'is_resolved', 'created_at')
    list_filter = ('reason', 'is_resolved', 'created_at')
    search_fields = ('reporter__username', 'message')
    actions = ['mark_as_resolved']

    def content_object(self, obj):
        if obj.video:
            return f"Vidéo: {obj.video.title}"
        if obj.photo:
            return f"Photo: {obj.photo.title}"
        return "N/A"
    content_object.short_description = 'Contenu signalé'

    def mark_as_resolved(self, request, queryset):
        queryset.update(is_resolved=True)
        self.message_user(request, "Les signalements sélectionnés ont été marqués comme résolus.")
    mark_as_resolved.short_description = "Marquer comme résolu"

@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Empêche de créer plus d'une configuration
        return not PlatformSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'ad_type', 'position', 'weight', 'frequency_cap', 'is_active')
    list_filter = ('ad_type', 'position', 'is_active')
    search_fields = ('title',)
    fieldsets = (
        ('Configuration Générale', {
            'fields': ('title', 'ad_type', 'position', 'is_active')
        }),
        ('Code Publicitaire (JS / Iframe)', {
            'fields': ('code',),
            'description': "Collez ici les tags Javascript (Popunder, bannières responsives) donnés par votre régie."
        }),
        ('Bannière Hébergée Localement', {
            'fields': ('image', 'link'),
            'description': "Utilisez ceci si vous uploadez vous-même l'image au lieu d'utiliser un code JS."
        }),
        ('Règles d\'Affichage', {
            'fields': ('weight', 'frequency_cap')
        }),
    )

@admin.register(AffiliateLink)
class AffiliateLinkAdmin(admin.ModelAdmin):
    list_display = ('name', 'tracking_url', 'clicks', 'created_at')
    search_fields = ('name', 'original_url')
    readonly_fields = ('clicks', 'created_at')
    
@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'content_format', 'is_published')
    list_filter = ('content_format', 'is_published')
    search_fields = ('title',)
    readonly_fields = ('slug',)
    fieldsets = (
        ('General', {'fields': ('title', 'content', 'content_format', 'is_published')}),
        ('SEO Meta Tags', {'fields': ('meta_title', 'meta_description'), 'classes': ('collapse',)}),
    )
