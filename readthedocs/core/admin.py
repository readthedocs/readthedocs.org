# -*- coding: utf-8 -*-

"""Django admin interface for core models."""

from datetime import timedelta

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from messages_extends.admin import MessageAdmin
from messages_extends.models import Message
from rest_framework.authtoken.admin import TokenAdmin

from readthedocs.core.models import UserProfile
from readthedocs.projects.models import Project


# Monkeypatch raw_id_fields onto the TokenAdmin
# https://www.django-rest-framework.org/api-guide/authentication/#with-django-admin
TokenAdmin.raw_id_fields = ['user']


class UserProjectInline(admin.TabularInline):
    model = Project.users.through
    verbose_name = 'User project'
    verbose_name_plural = 'User projects'
    extra = 1
    raw_id_fields = ('project',)


class UserProjectFilter(admin.SimpleListFilter):

    """Filter users based on project properties."""

    parameter_name = 'project_state'
    title = _('user projects')

    PROJECT_ACTIVE = 'active'
    PROJECT_BUILT = 'built'
    PROJECT_RECENT = 'recent'

    def lookups(self, request, model_admin):
        return (
            (self.PROJECT_ACTIVE, _('has active project')),
            (self.PROJECT_BUILT, _('has built project')),
            (self.PROJECT_RECENT, _('has project with recent builds')),
        )

    def queryset(self, request, queryset):
        """
        Add filters to queryset filter.

        ``PROJECT_ACTIVE`` and ``PROJECT_BUILT`` look for versions on projects,
        ``PROJECT_RECENT`` looks for projects with builds in the last year
        """
        if self.value() == self.PROJECT_ACTIVE:
            return queryset.filter(projects__versions__active=True)
        if self.value() == self.PROJECT_BUILT:
            return queryset.filter(projects__versions__built=True)
        if self.value() == self.PROJECT_RECENT:
            recent_date = timezone.now() - timedelta(days=365)
            return queryset.filter(projects__builds__date__gt=recent_date)


class UserAdminExtra(UserAdmin):

    """Admin configuration for User."""

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_banned',
    )
    list_filter = (UserProjectFilter,) + UserAdmin.list_filter
    actions = ['ban_user']
    inlines = [UserProjectInline]

    def is_banned(self, obj):
        return hasattr(obj, 'profile') and obj.profile.banned

    is_banned.short_description = 'Banned'
    is_banned.boolean = True

    def ban_user(self, request, queryset):
        users = []
        for profile in UserProfile.objects.filter(user__in=queryset):
            profile.banned = True
            profile.save()
            users.append(profile.user.username)
        self.message_user(request, 'Banned users: %s' % ', '.join(users))

    ban_user.short_description = 'Ban user'


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'homepage')
    search_fields = ('user__username', 'homepage')
    raw_id_fields = ('user',)


class MessageAdminExtra(MessageAdmin):
    list_display = [
        'user',
        'organizations',
        'message',
        'created',
        'read',
    ]
    list_filter = [
        'read',
    ]
    search_fields = [
        'user__username',
        'message',
        'user__organizationowner__organization__slug',
    ]

    def organizations(self, obj):
        return ', '.join(
            organization.slug
            for organization in obj.user.owner_organizations.all()
        )


admin.site.unregister(User)
admin.site.register(User, UserAdminExtra)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.unregister(Message)
admin.site.register(Message, MessageAdminExtra)
