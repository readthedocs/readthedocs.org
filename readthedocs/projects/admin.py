"""Django administration interface for `projects.models`"""

from __future__ import absolute_import
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.actions import delete_selected
from django.utils.translation import ugettext_lazy as _
from guardian.admin import GuardedModelAdmin

from readthedocs.core.models import UserProfile
from readthedocs.core.utils import broadcast
from readthedocs.builds.models import Version
from readthedocs.redirects.models import Redirect
from readthedocs.notifications.views import SendNotificationView

from .forms import FeatureForm
from .models import (Project, ImportedFile, Feature,
                     ProjectRelationship, EmailHook, WebHook, Domain)
from .notifications import ResourceUsageNotification
from .tasks import remove_dir


class ProjectSendNotificationView(SendNotificationView):
    notification_classes = [ResourceUsageNotification]

    def get_object_recipients(self, obj):
        for owner in obj.users.all():
            yield owner


class ProjectRelationshipInline(admin.TabularInline):

    """Project inline relationship view for :py:class:`ProjectAdmin`"""

    model = ProjectRelationship
    fk_name = 'parent'
    raw_id_fields = ('child',)


class VersionInline(admin.TabularInline):

    """Version inline relationship view for :py:class:`ProjectAdmin`"""

    model = Version


class RedirectInline(admin.TabularInline):

    """Redirect inline relationship view for :py:class:`ProjectAdmin`"""

    model = Redirect


class DomainInline(admin.TabularInline):
    model = Domain


# Turning off to support Django 1.9's requirement
# to not import apps that aren't in INSTALLED_APPS on rtd.com
# class ImpressionInline(admin.TabularInline):
#     from readthedocs.donate.models import ProjectImpressions
#     model = ProjectImpressions
#     readonly_fields = ('date', 'promo', 'offers', 'views', 'clicks', 'view_ratio', 'click_ratio')
#     extra = 0
#     can_delete = False
#     max_num = 15

#     def view_ratio(self, instance):
#         return instance.view_ratio * 100

#     def click_ratio(self, instance):
#         return instance.click_ratio * 100


class ProjectOwnerBannedFilter(admin.SimpleListFilter):

    """
    Filter for projects with banned owners.

    There are problems adding `users__profile__banned` to the `list_filter`
    attribute, so we'll create a basic filter to capture banned owners.
    """

    title = 'project owner banned'
    parameter_name = 'project_owner_banned'

    OWNER_BANNED = 'true'

    def lookups(self, request, model_admin):
        return (
            (self.OWNER_BANNED, _('Yes')),
        )

    def queryset(self, request, queryset):
        if self.value() == self.OWNER_BANNED:
            return queryset.filter(users__profile__banned=True)
        return queryset


class ProjectAdmin(GuardedModelAdmin):

    """Project model admin view."""

    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug', 'repo', 'repo_type', 'featured', 'theme')
    list_filter = ('repo_type', 'featured', 'privacy_level',
                   'documentation_type', 'programming_language',
                   ProjectOwnerBannedFilter)
    list_editable = ('featured',)
    search_fields = ('slug', 'repo')
    inlines = [ProjectRelationshipInline, RedirectInline,
               VersionInline, DomainInline]
    readonly_fields = ('feature_flags',)
    raw_id_fields = ('users', 'main_language_project')
    actions = ['send_owner_email', 'ban_owner']

    def feature_flags(self, obj):
        return ', '.join([str(f.get_feature_display()) for f in obj.features])

    def send_owner_email(self, request, queryset):
        view = ProjectSendNotificationView.as_view(
            action_name='send_owner_email'
        )
        return view(request, queryset=queryset)

    send_owner_email.short_description = 'Notify project owners'

    def ban_owner(self, request, queryset):
        """
        Ban project owner.

        This will only ban single owners, because a malicious user could add a
        user as a co-owner of the project. We don't want to induce and
        collatoral damage when flagging users.
        """
        total = 0
        for project in queryset:
            if project.users.count() == 1:
                count = (UserProfile.objects
                         .filter(user__projects=project)
                         .update(banned=True))
                total += count
            else:
                messages.add_message(request, messages.ERROR,
                                     'Project has multiple owners: {0}'.format(project))
        if total == 0:
            messages.add_message(request, messages.ERROR, 'No users banned')
        else:
            messages.add_message(request, messages.INFO,
                                 'Banned {0} user(s)'.format(total))

    ban_owner.short_description = 'Ban project owner'

    def delete_selected_and_artifacts(self, request, queryset):
        """
        Remove HTML/etc artifacts from application instances.

        Prior to the query delete, broadcast tasks to delete HTML artifacts from
        application instances.
        """
        if request.POST.get('post'):
            for project in queryset:
                broadcast(type='app', task=remove_dir, args=[project.doc_path])
        return delete_selected(self, request, queryset)

    def get_actions(self, request):
        actions = super(ProjectAdmin, self).get_actions(request)
        actions['delete_selected'] = (
            self.__class__.delete_selected_and_artifacts,
            'delete_selected',
            delete_selected.short_description
        )
        return actions


class ImportedFileAdmin(admin.ModelAdmin):

    """Admin view for :py:class:`ImportedFile`"""

    list_display = ('path', 'name', 'version')


class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'project', 'https', 'count')
    search_fields = ('domain', 'project__slug')
    raw_id_fields = ('project',)
    list_filter = ('canonical', 'https')
    model = Domain


class FeatureAdmin(admin.ModelAdmin):
    model = Feature
    form = FeatureForm
    list_display = ('feature_id', 'project_count', 'default_true')
    search_fields = ('feature_id',)
    filter_horizontal = ('projects',)
    readonly_fields = ('add_date',)

    def project_count(self, feature):
        return feature.projects.count()


admin.site.register(Project, ProjectAdmin)
admin.site.register(ImportedFile, ImportedFileAdmin)
admin.site.register(Domain, DomainAdmin)
admin.site.register(Feature, FeatureAdmin)
admin.site.register(EmailHook)
admin.site.register(WebHook)
