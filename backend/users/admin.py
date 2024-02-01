from django.contrib import admin

from users.models import User, Follow


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'email', 'username', 'first_name', 'last_name', 'password',
        'is_superuser', 'is_active', 'date_joined',
    )
    list_filter = ('email', 'username',)
    search_fields = ('username',)
    list_display_links = ('username',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author',)
    search_fields = ('user',)
    list_display_links = ('user',)
