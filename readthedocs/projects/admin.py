# -*- coding: utf-8 -*-

"""Django administration interface for `projects.models`."""

from django.contrib import admin, messages
from django.contrib.admin.actions import delete_selected
from django.utils.translation import ugettext_lazy as _
from guardian.admin import GuardedModelAdmin

from readthedocs.builds.models import Version
from readthedocs.core.models import UserProfile
from readthedocs.core.utils import broadcast, trigger_build
from readthedocs.notifications.views import SendNotificationView
from readthedocs.redirects.models import Redirect
from readthedocs.search.utils import _indexing_helper

from .forms import FeatureForm
from .models import (
    Domain,
    EmailHook,
    EnvironmentVariable,
    Feature,
    HTMLFile,
    ImportedFile,
    Project,
    ProjectRelationship,
    WebHook,
)
from .notifications import (
    DeprecatedBuildWebhookNotification,
    DeprecatedGitHubWebhookNotification,
    ResourceUsageNotification,
)
from .tasks import remove_dirs


class ProjectSendNotificationView(SendNotificationView):
    notification_classes = [
        ResourceUsageNotification,
        DeprecatedBuildWebhookNotification,
        DeprecatedGitHubWebhookNotification,
    ]

    def get_object_recipients(self, obj):
        for owner in obj.users.all():
            yield owner


class ProjectRelationshipInline(admin.TabularInline):

    """Project inline relationship view for :py:class:`ProjectAdmin`."""

    model = ProjectRelationship
    fk_name = 'parent'
    raw_id_fields = ('child',)


class VersionInline(admin.TabularInline):

    """Version inline relationship view for :py:class:`ProjectAdmin`."""

    model = Version


class RedirectInline(admin.TabularInline):

    """Redirect inline relationship view for :py:class:`ProjectAdmin`."""

    model = Redirect


class DomainInline(admin.TabularInline):
    model = Domain


# Turning off to support Django 1.9's requirement
# to not import apps that aren't in INSTALLED_APPS on rtd.com
# class ImpressionInline(admin.TabularInline):
#     from readthedocs.donate.models import ProjectImpressions
#     model = ProjectImpressions
#     readonly_fields = (
#         'date',
#         'promo',
#         'offers',
#         'views',
#         'clicks',
#         'view_ratio',
#         'click_ratio',
#     )
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
    NOT_OWNER_BANNED = 'false'

    def lookups(self, request, model_admin):
        return (
            (self.OWNER_BANNED, _('Yes')),
            (self.NOT_OWNER_BANNED, _('No')),
        )

    def queryset(self, request, queryset):
        if self.value() == self.OWNER_BANNED:
            return queryset.filter(users__profile__banned=True)
        if self.value() == self.NOT_OWNER_BANNED:
            return queryset.filter(users__profile__banned=False)
        return queryset


class ProjectAdmin(GuardedModelAdmin):

    """Project model admin view."""

    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug', 'repo', 'repo_type', 'featured')
    list_filter = (
        'repo_type',
        'featured',
        'privacy_level',
        'documentation_type',
        'programming_language',
        'feature__feature_id',
        ProjectOwnerBannedFilter,
    )
    list_editable = ('featured',)
    search_fields = ('slug', 'repo')
    inlines = [
        ProjectRelationshipInline,
        RedirectInline,
        VersionInline,
        DomainInline,
    ]
    readonly_fields = ('feature_flags',)
    raw_id_fields = ('users', 'main_language_project')
    actions = [
        'send_owner_email',
        'ban_owner',
        'build_default_version',
        'reindex_active_versions',
        'wipe_all_versions',
    ]

    def feature_flags(self, obj):
        return ', '.join([str(f.get_feature_display()) for f in obj.features])

    def send_owner_email(self, request, queryset):
        view = ProjectSendNotificationView.as_view(
            action_name='send_owner_email',
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
                count = (
                    UserProfile.objects.filter(
                        user__projects=project,
                    ).update(banned=True)
                )  # yapf: disabled
                total += count
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'Project has multiple owners: {}'.format(project),
                )
        if total == 0:
            messages.add_message(request, messages.ERROR, 'No users banned')
        else:
            messages.add_message(
                request,
                messages.INFO,
                'Banned {} user(s)'.format(total),
            )

    ban_owner.short_description = 'Ban project owner'

    def delete_selected_and_artifacts(self, request, queryset):
        """
        Remove HTML/etc artifacts from application instances.

        Prior to the query delete, broadcast tasks to delete HTML artifacts from
        application instances.
        """
        if request.POST.get('post'):
            for project in queryset:
                broadcast(
                    type='app',
                    task=remove_dirs,
                    args=[(project.doc_path,)],
                )
        return delete_selected(self, request, queryset)

    def build_default_version(self, request, queryset):
        """Trigger a build for the project version."""
        total = 0
        for project in queryset:
            trigger_build(project=project)
            total += 1
        messages.add_message(
            request,
            messages.INFO,
            'Triggered builds for {} project(s).'.format(total),
        )

    build_default_version.short_description = 'Build default version'

    def reindex_active_versions(self, request, queryset):
        """Reindex all active versions of the selected projects to ES."""
        qs_iterator = queryset.iterator()
        for project in qs_iterator:
            version_qs = Version.objects.filter(project=project)
            active_versions = version_qs.filter(active=True)

            if not active_versions.exists():
                self.message_user(
                    request,
                    'No active versions of project {}'.format(project),
                    messages.ERROR
                )
            else:
                html_objs_qs = []
                for version in active_versions.iterator():
                    html_objs = HTMLFile.objects.filter(project=project, version=version)

                    if html_objs.exists():
                        html_objs_qs.append(html_objs)

                if html_objs_qs:
                    _indexing_helper(html_objs_qs, wipe=False)

                self.message_user(
                    request,
                    'Task initiated successfully for {}'.format(project),
                    messages.SUCCESS
                )

    reindex_active_versions.short_description = 'Reindex active versions to ES'

    def wipe_all_versions(self, request, queryset):
        """Wipe indexes of all versions of selected projects."""
        qs_iterator = queryset.iterator()
        for project in qs_iterator:
            version_qs = Version.objects.filter(project=project)
            if not version_qs.exists():
                self.message_user(
                    request,
                    'No active versions of project {}.'.format(project),
                    messages.ERROR
                )
            else:
                html_objs_qs = []
                for version in version_qs.iterator():
                    html_objs = HTMLFile.objects.filter(project=project, version=version)

                    if html_objs.exists():
                        html_objs_qs.append(html_objs)

                if html_objs_qs:
                    _indexing_helper(html_objs_qs, wipe=True)

                self.message_user(
                    request,
                    'Task initiated successfully for {}.'.format(project),
                    messages.SUCCESS
                )

    wipe_all_versions.short_description = 'Wipe all versions from ES'

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions['delete_selected'] = (
            self.__class__.delete_selected_and_artifacts,
            'delete_selected',
            delete_selected.short_description,
        )
        return actions


class ImportedFileAdmin(admin.ModelAdmin):

    """Admin view for :py:class:`ImportedFile`."""

    raw_id_fields = ('project', 'version')
    list_display = ('path', 'name', 'version')
    search_fields = ('project', 'path')


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
    raw_id_fields = ('projects',)

    def project_count(self, feature):
        return feature.projects.count()


class EnvironmentVariableAdmin(admin.ModelAdmin):
    model = EnvironmentVariable
    list_display = ('name', 'value', 'project', 'created')
    search_fields = ('name', 'project__slug')


admin.site.register(Project, ProjectAdmin)
admin.site.register(EnvironmentVariable, EnvironmentVariableAdmin)
admin.site.register(ImportedFile, ImportedFileAdmin)
admin.site.register(Domain, DomainAdmin)
admin.site.register(Feature, FeatureAdmin)
admin.site.register(EmailHook)
admin.site.register(WebHook)
admin.site.register(HTMLFile, ImportedFileAdmin)
