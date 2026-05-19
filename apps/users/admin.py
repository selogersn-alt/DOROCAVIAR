from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('bio',)
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Profile Info', {'fields': ('bio', 'profile_image', 'favorites')}),
    )
    filter_horizontal = ('favorites',)
