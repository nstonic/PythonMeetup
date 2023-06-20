from django.contrib import admin

from .models import User, Event, Speech


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'nickname', 'is_admin')


class OrganizerInline(admin.TabularInline):
    model = User.org_events.through
    extra = 1
    verbose_name_plural = 'Организаторы'


class ParticipantInlaine(admin.TabularInline):
    model = User.events.through
    extra = 1
    verbose_name_plural = 'Участники'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'started_at', 'get_organizer')
    fields = ('title', 'description', 'started_at')
    inlines = [OrganizerInline, ParticipantInlaine]


admin.site.register(Speech)