from django.contrib import admin
from django.utils.html import format_html

from .models import User, Event, Speech


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'nickname', 'is_admin')


class OrganizerInline(admin.TabularInline):
    model = User.org_events.through
    extra = 1
    verbose_name_plural = 'Организаторы'


class SpeechInline(admin.TabularInline):
    model = Speech
    extra = 1
    fields = ['title', 'speaker', 'started_at', 'finished_at']
    verbose_name_plural = 'Выступления'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'started_at', 'get_organizer')
    readonly_fields = ['get_image_preview']
    fields = ('get_image_preview', 'image', 'title', 'description', 'started_at', 'finished_at')
    inlines = [SpeechInline, OrganizerInline]

    def get_image_preview(self, obj):
        img = obj.image
        if not img:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=img.url)

    get_image_preview.short_description = 'Привью логотипа'


admin.site.register(Speech)
