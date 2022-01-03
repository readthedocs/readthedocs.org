"""Django administration interface for `projects.models`."""

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.actions import delete_selected
from django.db.models import Sum
from django.forms import BaseInlineFormSet
from django.utils.translation import gettext_lazy as _

from readthedocs.builds.models import Version
from readthedocs.core.history import ExtraSimpleHistoryAdmin, set_change_reason
from readthedocs.core.utils import trigger_build
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
    HTTPHeader,
    ImportedFile,
    Project,
    ProjectRelationship,
    WebHook,
    WebHookEvent,
)
from .notifications import (
    DeprecatedBuildWebhookNotification,
    DeprecatedGitHubWebhookNotification,
    ResourceUsageNotification,
)
from .tag_utils import import_tags
from .tasks import clean_project_resources


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


class VersionInlineFormSet(BaseInlineFormSet):

    """Limit the number of versions displayed in the inline."""

    LIMIT = 200

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = self.queryset[:self.LIMIT]


class VersionInline(admin.TabularInline):

    """Version inline relationship view for :py:class:`ProjectAdmin`."""

    formset = VersionInlineFormSet
    model = Version

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("project")


class RedirectInline(admin.TabularInline):

    """Redirect inline relationship view for :py:class:`ProjectAdmin`."""

    model = Redirect


class DomainInline(admin.TabularInline):
    model = Domain


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


class ProjectSpamThreshold(admin.SimpleListFilter):

    """Filter for projects that are potentially SPAM."""

    title = 'Spam Threshold'
    parameter_name = 'spam_threshold'

    NOT_ENOUGH_SCORE = 'not_enough_score'
    DONT_SHOW_ADS = 'dont_show_ads'
    DENY_ON_ROBOTS = 'deny_on_robots'
    DONT_SERVE_DOCS = 'dont_serve_docs'
    DONT_SHOW_DASHBOARD = 'dont_show_dashboard'
    DELETE_PROJECT = 'delete_project'

    def lookups(self, request, model_admin):
        return (
            (
                self.NOT_ENOUGH_SCORE,
                _("Not spam (1-{})").format(
                    settings.RTD_SPAM_THRESHOLD_DONT_SHOW_ADS,
                ),
            ),
            (
                self.DONT_SHOW_ADS,
                _("Don't show Ads ({}-{})").format(
                    settings.RTD_SPAM_THRESHOLD_DONT_SHOW_ADS,
                    settings.RTD_SPAM_THRESHOLD_DENY_ON_ROBOTS,
                ),
            ),
            (
                self.DENY_ON_ROBOTS,
                _('Deny on robots ({}-{})').format(
                    settings.RTD_SPAM_THRESHOLD_DENY_ON_ROBOTS,
                    settings.RTD_SPAM_THRESHOLD_DONT_SHOW_DASHBOARD,
                ),
            ),
            (
                self.DONT_SHOW_DASHBOARD,
                _("Don't show dashboard ({}-{})").format(
                    settings.RTD_SPAM_THRESHOLD_DONT_SHOW_DASHBOARD,
                    settings.RTD_SPAM_THRESHOLD_DONT_SERVE_DOCS,
                ),
            ),
            (
                self.DONT_SERVE_DOCS,
                _("Don't serve docs ({}-{})").format(
                    settings.RTD_SPAM_THRESHOLD_DONT_SERVE_DOCS,
                    settings.RTD_SPAM_THRESHOLD_DELETE_PROJECT,
                ),
            ),
            (
                self.DELETE_PROJECT,
                _('Delete project (>={})').format(
                    settings.RTD_SPAM_THRESHOLD_DELETE_PROJECT,
                ),
            ),
        )

    def queryset(self, request, queryset):
        queryset = queryset.annotate(spam_score=Sum('spam_rules__value'))
        if self.value() == self.NOT_ENOUGH_SCORE:
            return queryset.filter(
                spam_score__gte=1,
                spam_score__lt=settings.RTD_SPAM_THRESHOLD_DONT_SHOW_ADS,
            )
        if self.value() == self.DONT_SHOW_ADS:
            return queryset.filter(
                spam_score__gte=settings.RTD_SPAM_THRESHOLD_DONT_SHOW_ADS,
                spam_score__lt=settings.RTD_SPAM_THRESHOLD_DENY_ON_ROBOTS,
            )
        if self.value() == self.DENY_ON_ROBOTS:
            return queryset.filter(
                spam_score__gte=settings.RTD_SPAM_THRESHOLD_DENY_ON_ROBOTS,
                spam_score__lt=settings.RTD_SPAM_THRESHOLD_DONT_SHOW_DASHBOARD,
            )
        if self.value() == self.DONT_SHOW_DASHBOARD:
            return queryset.filter(
                spam_score__gte=settings.RTD_SPAM_THRESHOLD_DONT_SHOW_DASHBOARD,
                spam_score__lt=settings.RTD_SPAM_THRESHOLD_DONT_SERVE_DOCS,
            )
        if self.value() == self.DONT_SERVE_DOCS:
            return queryset.filter(
                spam_score__gte=settings.RTD_SPAM_THRESHOLD_DONT_SERVE_DOCS,
                spam_score__lt=settings.RTD_SPAM_THRESHOLD_DELETE_PROJECT,
            )
        if self.value() == self.DELETE_PROJECT:
            return queryset.filter(
                spam_score__gte=settings.RTD_SPAM_THRESHOLD_DELETE_PROJECT,
            )
        return queryset


class ProjectAdmin(ExtraSimpleHistoryAdmin):

    """Project model admin view."""

    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug', 'repo')

    list_filter = tuple()
    if 'readthedocsext.spamfighting' in settings.INSTALLED_APPS:
        list_filter = list_filter + (ProjectSpamThreshold,)

    list_filter = list_filter + (
        ProjectOwnerBannedFilter,
        'is_spam',
        'feature__feature_id',
        'repo_type',
        'privacy_level',
        'programming_language',
        'documentation_type',
    )

    search_fields = ('slug', 'repo')
    inlines = [
        ProjectRelationshipInline,
        RedirectInline,
        VersionInline,
        DomainInline,
    ]
    readonly_fields = ('pub_date', 'feature_flags', 'matching_spam_rules')
    raw_id_fields = ('users', 'main_language_project', 'remote_repository')
    actions = [
        'send_owner_email',
        'ban_owner',
        'run_spam_rule_checks',
        'build_default_version',
        'reindex_active_versions',
        'wipe_all_versions',
        'import_tags_from_vcs',
    ]

    def matching_spam_rules(self, obj):
        result = []
        for spam_rule in obj.spam_rules.filter(enabled=True):
            result.append(f'{spam_rule.spam_rule_type} ({spam_rule.value})')
        return '\n'.join(result) or 'No matching spam rules'

    def feature_flags(self, obj):
        return '\n'.join([str(f.get_feature_display()) for f in obj.features])

    def send_owner_email(self, request, queryset):
        view = ProjectSendNotificationView.as_view(
            action_name='send_owner_email',
        )
        return view(request, queryset=queryset)

    send_owner_email.short_description = 'Notify project owners'

    def run_spam_rule_checks(self, request, queryset):
        """Run all the spam checks on this project."""
        if 'readthedocsext.spamfighting' not in settings.INSTALLED_APPS:
            messages.add_message(
                request,
                messages.ERROR,
                'Spam fighting Django application not installed',
            )
            return

        from readthedocsext.spamfighting.tasks import spam_rules_check  # noqa
        project_slugs = queryset.values_list('slug', flat=True)
        # NOTE: convert queryset to a simple list so Celery can serialize it
        spam_rules_check.delay(project_slugs=list(project_slugs))
        messages.add_message(
            request,
            messages.INFO,
            'Spam check task triggered for {} projects'.format(queryset.count()),
        )

    def ban_owner(self, request, queryset):
        """
        Ban project owner.

        This will only ban single owners, because a malicious user could add a
        user as a co-owner of the project. We don't want to induce and
        collateral damage when flagging users.
        """
        total = 0
        for project in queryset:
            if project.users.count() == 1:
                user = project.users.first()
                user.profile.banned = True
                set_change_reason(user.profile, self.get_change_reason())
                user.profile.save()
                total += 1
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
        """Remove HTML/etc artifacts from storage."""
        if request.POST.get('post'):
            for project in queryset:
                clean_project_resources(project)
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
            version_qs = Version.internal.filter(project=project)
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
            version_qs = Version.internal.filter(project=project)
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

    def import_tags_from_vcs(self, request, queryset):
        for project in queryset.iterator():
            tags = import_tags(project)
            if tags:
                self.message_user(
                    request,
                    'Imported tags for {}: {}'.format(project, tags),
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    'No tags found for {}'.format(project),
                    messages.WARNING
                )

    import_tags_from_vcs.short_description = 'Import tags from the version control API'

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
    list_display = ('path', 'version', 'build')
    list_select_related = ('project', 'version', 'version__project')
    search_fields = ('project__slug', 'version__slug', 'path', 'build')


class HTTPHeaderInline(admin.TabularInline):
    model = HTTPHeader


class DomainAdmin(admin.ModelAdmin):
    list_display = (
        'domain',
        'project',
        'canonical',
        'https',
        'count',
        'ssl_status',
        'created',
        'modified',
    )
    inlines = (HTTPHeaderInline,)
    search_fields = ('domain', 'project__slug')
    raw_id_fields = ('project',)
    list_filter = ('canonical', 'https', 'ssl_status')
    model = Domain


class HTTPHeaderAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'value',
        'domain_name',
        'project_slug',
    )
    raw_id_fields = ('domain',)
    search_fields = ('name', 'domain__name', 'project__slug')
    model = HTTPHeader

    def domain_name(self, http_header):
        return http_header.domain.domain

    def project_slug(self, http_header):
        return http_header.domain.project.slug


class FeatureAdmin(admin.ModelAdmin):
    model = Feature
    form = FeatureForm
    list_display = ('feature_id', 'project_count', 'default_true', 'future_default_true')
    search_fields = ('feature_id',)
    filter_horizontal = ('projects',)
    readonly_fields = ('add_date',)
    raw_id_fields = ('projects',)

    def project_count(self, feature):
        return feature.projects.count()


class EnvironmentVariableAdmin(admin.ModelAdmin):
    model = EnvironmentVariable
    list_display = ('name', 'value', 'public', 'project', 'created')
    search_fields = ('name', 'project__slug')


admin.site.register(Project, ProjectAdmin)
admin.site.register(EnvironmentVariable, EnvironmentVariableAdmin)
admin.site.register(ImportedFile, ImportedFileAdmin)
admin.site.register(HTTPHeader, HTTPHeaderAdmin)
admin.site.register(Domain, DomainAdmin)
admin.site.register(Feature, FeatureAdmin)
admin.site.register(EmailHook)
admin.site.register(WebHook)
admin.site.register(WebHookEvent)
admin.site.register(HTMLFile, ImportedFileAdmin)
