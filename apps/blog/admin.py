from django.contrib import admin
from .models import BlogCategory, Post

@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'content')
    # prepopulated_fields = {'slug': ('title',)} # Supprimé car AutoSlugField gère le slug automatiquement
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Contenu de l\'article', {
            'fields': ('title', 'category', 'author', 'featured_image', 'content', 'status', 'tags')
        }),
        ('Référencement (SEO)', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
        }),
    )
