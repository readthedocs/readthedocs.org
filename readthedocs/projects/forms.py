"""Project forms."""

import json
from random import choice
from re import fullmatch
from urllib.parse import urlparse

import dns.name
import dns.resolver
from allauth.socialaccount.models import SocialAccount
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from readthedocs.builds.constants import INTERNAL
from readthedocs.core.forms import PrevalidatedForm
from readthedocs.core.forms import RichValidationError
from readthedocs.core.history import SimpleHistoryModelForm
from readthedocs.core.permissions import AdminPermission
from readthedocs.core.utils import slugify
from readthedocs.core.utils import trigger_build
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.integrations.models import Integration
from readthedocs.invitations.models import Invitation
from readthedocs.notifications.models import Notification
from readthedocs.oauth.models import RemoteRepository
from readthedocs.organizations.models import Team
from readthedocs.projects.constants import ADDONS_FLYOUT_SORTING_CUSTOM_PATTERN
from readthedocs.projects.models import AddonsConfig
from readthedocs.projects.models import Domain
from readthedocs.projects.models import EmailHook
from readthedocs.projects.models import EnvironmentVariable
from readthedocs.projects.models import Feature
from readthedocs.projects.models import Project
from readthedocs.projects.models import ProjectRelationship
from readthedocs.projects.models import WebHook
from readthedocs.projects.notifications import MESSAGE_PROJECT_SEARCH_INDEXING_DISABLED
from readthedocs.projects.tasks.search import index_project
from readthedocs.projects.templatetags.projects_tags import sort_version_aware
from readthedocs.redirects.models import Redirect


class ProjectForm(SimpleHistoryModelForm):
    """
    Project form.

    :param user: If provided, add this user as a project user on save
    """

    required_css_class = "required"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["repo"].widget.attrs["placeholder"] = self.placehold_repo()
        self.fields["repo"].widget.attrs["required"] = True

        # NOTE: we are not using the default ModelChoiceField widget
        # in order to use a list of choices instead of a queryset.
        # See _get_remote_repository_choices for more info.
        self.fields["remote_repository"] = forms.TypedChoiceField(
            choices=self._get_remote_repository_choices(),
            coerce=lambda x: RemoteRepository.objects.get(pk=x),
            required=False,
            empty_value=None,
            help_text=self.fields["remote_repository"].help_text,
            label=self.fields["remote_repository"].label,
        )

        # The clone URL will be set from the remote repository.
        if self.instance.remote_repository and not self.instance.has_feature(
            Feature.DONT_SYNC_WITH_REMOTE_REPO
        ):
            self.fields["repo"].disabled = True

    def _get_remote_repository_choices(self):
        """
        Get valid choices for the remote repository field.

        If there is a remote repo attached to the project,
        we add it to the queryset, since the current user
        might not have access to it.

        .. note::

           We are not including the current remote repo in the queryset
           using an "or" condition, that confuses the ORM/postgres and
           it results in a very slow query. Instead, we are using a list,
           and adding the current remote repo to it.
        """
        queryset = RemoteRepository.objects.for_project_linking(self.user)
        current_remote_repo = self.instance.remote_repository if self.instance.pk else None
        options = [
            (None, _("No connected repository")),
        ]
        if current_remote_repo and current_remote_repo not in queryset:
            options.append((current_remote_repo.pk, str(current_remote_repo)))

        options.extend((repo.pk, repo.clone_url) for repo in queryset)
        return options

    def save(self, commit=True):
        project = super().save(commit)
        if commit:
            if self.user and not project.users.filter(pk=self.user.pk).exists():
                project.users.add(self.user)
        return project

    def clean_name(self):
        name = self.cleaned_data.get("name", "")
        if not self.instance.pk:
            potential_slug = slugify(name)
            if Project.objects.filter(slug=potential_slug).exists():
                raise forms.ValidationError(
                    _("Invalid project name, a project already exists with that name"),
                )  # yapf: disable # noqa
            if not potential_slug:
                # Check the generated slug won't be empty
                raise forms.ValidationError(
                    _("Invalid project name"),
                )

        return name

    def clean_repo(self):
        repo = self.cleaned_data.get("repo", "")
        return repo.rstrip("/")

    def placehold_repo(self):
        return choice(
            [
                "https://bitbucket.org/cherrypy/cherrypy",
                "https://bitbucket.org/birkenfeld/sphinx",
                "https://bitbucket.org/hpk42/tox",
                "https://github.com/zzzeek/sqlalchemy.git",
                "https://github.com/django/django.git",
                "https://github.com/fabric/fabric.git",
                "https://github.com/ericholscher/django-kong.git",
            ]
        )


class ProjectTriggerBuildMixin:
    """
    Mixin to trigger build on form save.

    We trigger a build to LATEST version of the project, and the version
    that LATEST points to, since latest is just an alias.

    This should be replaced with signals instead of calling trigger_build
    explicitly.
    """

    def save(self, commit=True):
        """Trigger build on commit save."""
        project = super().save(commit)
        if commit:
            original_latest_version = project.get_original_latest_version()
            if original_latest_version and original_latest_version.active:
                trigger_build(project=project, version=original_latest_version)
            latest_version = project.get_latest_version()
            if latest_version and latest_version.active:
                trigger_build(project=project, version=latest_version)
        return project


class ProjectBackendForm(forms.Form):
    """Get the import backend."""

    backend = forms.CharField()


class ProjectPRBuildsMixin(PrevalidatedForm):
    """
    Mixin that provides a method to setup the external builds option.

    TODO: Remove this once we migrate to the new dashboard,
    and we don't need to support the old project settings form.
    """

    def has_supported_integration(self, integrations):
        supported_types = {Integration.GITHUB_WEBHOOK, Integration.GITLAB_WEBHOOK}
        for integration in integrations:
            if integration.integration_type in supported_types:
                return True
        return False

    def can_build_external_versions(self, integrations):
        """
        Check if external versions can be enabled for this project.

        A project can build external versions if:

        - They are using GitHub or GitLab.
        - The repository's webhook is setup to send pull request events.

        If the integration's provider data isn't set,
        it could mean that the user created the integration manually,
        and doesn't have an account connected.
        So we don't know for sure if the webhook is sending pull request events.
        """
        for integration in integrations:
            provider_data = integration.provider_data
            if integration.integration_type == Integration.GITHUB_WEBHOOK and (
                not provider_data or "pull_request" in provider_data.get("events", [])
            ):
                return True
            if integration.integration_type == Integration.GITLAB_WEBHOOK and (
                not provider_data or provider_data.get("merge_requests_events")
            ):
                return True
        return False

    def setup_external_builds_option(self):
        """Disable the external builds option if the project doesn't meet the requirements."""
        if (
            settings.ALLOW_PRIVATE_REPOS
            and self.instance.remote_repository
            and not self.instance.remote_repository.private
        ):
            self.fields["external_builds_privacy_level"].disabled = True
            # TODO use a proper error/warning instead of help text for error states
            help_text = _(
                "We have detected that this project is public, pull request previews are set to public."
            )
            self.fields["external_builds_privacy_level"].help_text = help_text

    def clean_prevalidation(self):
        """Disable the external builds option if the project doesn't meet the requirements."""
        # If the project is attached to a GitHub app integration,
        # it will always be able to build external versions.
        if self.instance.is_github_app_project:
            return

        integrations = list(self.instance.integrations.all())
        has_supported_integration = self.has_supported_integration(integrations)
        can_build_external_versions = self.can_build_external_versions(integrations)

        # External builds are supported for this project,
        # don't disable the option.
        if has_supported_integration and can_build_external_versions:
            return

        msg = None
        url = reverse("projects_integrations", args=[self.instance.slug])

        if not has_supported_integration:
            msg = _(
                "To build from pull requests you need a "
                f'GitHub or GitLab <a href="{url}">integration</a>.'
            )

        if has_supported_integration and not can_build_external_versions:
            # If there is only one integration, link directly to it.
            if len(integrations) == 1:
                url = reverse(
                    "projects_integrations_detail",
                    args=[self.instance.slug, integrations[0].pk],
                )
            msg = _(
                "To build from pull requests your repository's webhook "
                "needs to send pull request events. "
                f'Try to <a href="{url}">resync your integration</a>.'
            )

        if msg:
            # TODO use a proper error/warning instead of help text for error states
            field = self.fields["external_builds_enabled"]
            field.disabled = True
            field.help_text = f"{msg} {field.help_text}"
            # Don't raise an error on the Update form,
            # to keep backwards compat
            if not self.fields.get("name"):
                raise RichValidationError(
                    msg,
                    header=_("Pull request builds not supported"),
                )


class ProjectFormPrevalidateMixin:
    """Provides shared logic between the automatic and manual create forms."""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_prevalidation(self):
        # Shared conditionals between automatic and manual forms
        self.user_has_connected_account = SocialAccount.objects.filter(
            user=self.user,
        ).exists()
        self.user_is_nonowner_with_sso = None
        self.user_missing_admin_permission = None
        if settings.RTD_ALLOW_ORGANIZATIONS:
            # TODO there should be some way to initially select the organization
            # and maybe the team too. It's mostly safe to automatically select
            # the first organization, but explicit would be better. Reusing the
            # organization selection UI works, we only really need a query param
            # here.
            self.user_is_nonowner_with_sso = all(
                [
                    AdminPermission.has_sso_enabled(self.user),
                    AdminPermission.organizations(
                        user=self.user,
                        owner=False,
                    ).exists(),
                ]
            )

            # TODO this logic should be possible from AdminPermission
            # AdminPermssion.is_admin only inspects organization owners, so the
            # additional team check is necessary
            self.user_has_admin_permission = any(
                [
                    AdminPermission.organizations(
                        user=self.user,
                        owner=True,
                    ).exists(),
                    Team.objects.admin(self.user).exists(),
                ]
            )


class ProjectAutomaticForm(ProjectFormPrevalidateMixin, PrevalidatedForm):
    def clean_prevalidation(self):
        """
        Block user from using this form for important blocking states.

        We know before the user gets a chance to use this form that the user
        might not have the ability to add a project into their organization.
        These errors are raised before the user submits the form.
        """
        super().clean_prevalidation()
        if not self.user_has_connected_account:
            url = reverse("socialaccount_connections")
            raise RichValidationError(
                _(
                    f"You must first <a href='{url}'>add a connected service "
                    f"to your account</a> to enable automatic configuration of "
                    f"repositories."
                ),
                header=_("No connected services found"),
            )
        if settings.RTD_ALLOW_ORGANIZATIONS:
            if self.user_is_nonowner_with_sso:
                raise RichValidationError(
                    _(
                        "Only organization owners may create new projects "
                        "when single sign-on is enabled."
                    ),
                    header=_("Organization single sign-on enabled"),
                )
            if not self.user_has_admin_permission:
                raise RichValidationError(
                    _(
                        "You must be on a team with admin permissions "
                        "in order to add a new project to your organization."
                    ),
                    header=_("Admin permission required"),
                )


class ProjectManualForm(ProjectFormPrevalidateMixin, PrevalidatedForm):
    def clean_prevalidation(self):
        super().clean_prevalidation()
        if settings.RTD_ALLOW_ORGANIZATIONS:
            if self.user_is_nonowner_with_sso:
                raise RichValidationError(
                    _(
                        "Projects cannot be manually configured when "
                        "single sign-on is enabled for your organization."
                    ),
                    header=_("Organization single sign-on enabled"),
                )
            if not self.user_has_admin_permission:
                raise RichValidationError(
                    _(
                        "You must be on a team with admin permissions "
                        "in order to add a new project to your organization."
                    ),
                    header=_("Admin permission required"),
                )


class ProjectBasicsForm(ProjectForm):
    """Form used when importing a project."""

    class Meta:
        model = Project
        fields = ("name", "repo", "default_branch", "language", "remote_repository")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["repo"].widget.attrs["placeholder"] = self.placehold_repo()
        self.fields["repo"].widget.attrs["required"] = True
        # Make the repo field readonly if a remote repository is given,
        # since it will be derived from the remote repository.
        # In the form we already populate this field with the remote repository's clone URL.
        if self.initial.get("remote_repository"):
            self.fields["repo"].disabled = True
        self.fields["remote_repository"].widget = forms.HiddenInput()


class ProjectConfigForm(forms.Form):
    """Simple intermediate step to communicate about the .readthedocs.yaml file."""

    def __init__(self, *args, **kwargs):
        # Remove 'user' field since it's not expected by BaseForm.
        kwargs.pop("user")
        super().__init__(*args, **kwargs)


class UpdateProjectForm(
    ProjectTriggerBuildMixin,
    ProjectForm,
    ProjectPRBuildsMixin,
):
    """Main project settings form."""

    class Meta:
        model = Project
        fields = (
            # Basics and repo settings
            "name",
            "repo",
            "remote_repository",
            "language",
            "default_version",
            "privacy_level",
            "versioning_scheme",
            "default_branch",
            "readthedocs_yaml_path",
            "search_indexing_enabled",
            # Meta data
            "programming_language",
            "project_url",
            "description",
            "tags",
            # Booleans
            "external_builds_privacy_level",
            "external_builds_enabled",
            "show_version_warning",
        )

    # Make description smaller, only a CharField
    description = forms.CharField(
        required=False,
        max_length=150,
        help_text=_("Short description of this project"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.had_search_disabled = not self.instance.search_indexing_enabled

        # Remove empty choice from options.
        self.fields["versioning_scheme"].choices = [
            (key, value) for key, value in self.fields["versioning_scheme"].choices if key
        ]

        if self.instance.main_language_project:
            link = reverse(
                "projects_advanced",
                args=[self.instance.main_language_project.slug],
            )
            self.fields["versioning_scheme"].help_text = _(
                f'This setting is inherited from the <a href="{link}">parent translation</a>.',
            )
            self.fields["versioning_scheme"].disabled = True

        # Only show this field if search is disabled for the project.
        # We allow enabling it from the form, but not disabling it.
        if self.instance.search_indexing_enabled:
            self.fields.pop("search_indexing_enabled")

        # NOTE: we are deprecating this feature.
        # However, we will keep it available for projects that already using it.
        # Old projects not using it already or new projects won't be able to enable.
        if not self.instance.has_feature(Feature.ALLOW_VERSION_WARNING_BANNER):
            self.fields.pop("show_version_warning")

        if not settings.ALLOW_PRIVATE_REPOS:
            for field in ["privacy_level", "external_builds_privacy_level"]:
                self.fields.pop(field)

        default_choice = (None, "-" * 9)
        versions_choices = (
            self.instance.versions(manager=INTERNAL)
            .filter(machine=False)
            .values_list("verbose_name", flat=True)
        )

        self.fields["default_branch"].widget = forms.Select(
            choices=[default_choice] + list(zip(versions_choices, versions_choices)),
        )

        active_versions = self.get_all_active_versions()

        if active_versions:
            self.fields["default_version"].widget = forms.Select(
                choices=active_versions,
            )
        else:
            self.fields["default_version"].widget.attrs["readonly"] = True

        self.setup_external_builds_option()

    def clean_readthedocs_yaml_path(self):
        """
        Validate user input to help user.

        We also validate this path during the build process, so this validation step is
        only considered as helpful to a user, not a security measure.
        """
        filename = self.cleaned_data.get("readthedocs_yaml_path")
        filename = (filename or "").strip()
        return filename

    def get_all_active_versions(self):
        """
        Returns all active versions.

        Returns a smartly sorted list of tuples.
        First item of each tuple is the version's slug,
        and the second item is version's verbose_name.
        """
        version_qs = self.instance.all_active_versions()
        if version_qs.exists():
            version_qs = sort_version_aware(version_qs)
            all_versions = [(version.slug, version.verbose_name) for version in version_qs]
            return all_versions
        return None

    def clean_language(self):
        """Ensure that language isn't already active."""
        language = self.cleaned_data["language"]
        project = self.instance
        if project:
            msg = _(
                'There is already a "{lang}" translation for the {proj} project.',
            )
            if project.translations.filter(language=language).exists():
                raise forms.ValidationError(
                    msg.format(lang=language, proj=project.slug),
                )
            main_project = project.main_language_project
            if main_project:
                if main_project.language == language:
                    raise forms.ValidationError(
                        msg.format(lang=language, proj=main_project.slug),
                    )
                siblings = (
                    main_project.translations.filter(language=language)
                    .exclude(pk=project.pk)
                    .exists()
                )
                if siblings:
                    raise forms.ValidationError(
                        msg.format(lang=language, proj=main_project.slug),
                    )
        return language

    def clean_tags(self):
        tags = self.cleaned_data.get("tags", [])
        for tag in tags:
            if len(tag) > 100:
                raise forms.ValidationError(
                    _(
                        "Length of each tag must be less than or equal to 100 characters.",
                    ),
                )
        return tags

    def save(self, commit=True):
        instance = super().save(commit)
        # Trigger a reindex when enabling search from the form.
        if self.had_search_disabled and instance.search_indexing_enabled:
            index_project.delay(project_slug=instance.slug)
            Notification.objects.cancel(
                message_id=MESSAGE_PROJECT_SEARCH_INDEXING_DISABLED,
                attached_to=instance,
            )
        return instance


class ProjectRelationshipForm(forms.ModelForm):
    """Form to add/update project relationships."""

    parent = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = ProjectRelationship
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project")
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        # Don't display the update form with an editable child, as it will be
        # filtered out from the queryset anyways.
        if hasattr(self, "instance") and self.instance.pk is not None:
            self.fields["child"].queryset = Project.objects.filter(pk=self.instance.child.pk)
        else:
            self.fields["child"].queryset = self.project.get_subproject_candidates(self.user)

    def clean_parent(self):
        self.project.is_valid_as_superproject(forms.ValidationError)
        return self.project

    def clean_alias(self):
        alias = self.cleaned_data["alias"]
        subproject = self.project.subprojects.filter(alias=alias).exclude(id=self.instance.pk)

        if subproject.exists():
            raise forms.ValidationError(
                _("A subproject with this alias already exists"),
            )
        return alias


class ProjectPullRequestForm(forms.ModelForm, ProjectPRBuildsMixin):
    """Project pull requests configuration form."""

    class Meta:
        model = Project
        fields = [
            "external_builds_enabled",
            "external_builds_privacy_level",
            "show_build_overview_in_comment",
        ]

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

        self.setup_external_builds_option()

        if not self.instance.is_github_app_project:
            self.fields.pop("show_build_overview_in_comment")

        if not settings.ALLOW_PRIVATE_REPOS:
            self.fields.pop("external_builds_privacy_level")


class OnePerLineList(forms.Field):
    widget = forms.Textarea(
        attrs={
            "placeholder": "\n".join(
                [
                    "whatsnew.html",
                    "archive/*",
                    "tags/*",
                    "guides/getting-started.html",
                    "changelog.html",
                    "release/*",
                ]
            ),
        },
    )

    def to_python(self, value):
        """Convert a text area into a list of items (one per line)."""
        if not value:
            return []
        # Normalize paths and filter empty lines:
        #  - remove trailing spaces
        #  - skip empty lines
        #  - remove starting `/`
        result = []
        for line in value.splitlines():
            normalized = line.strip().lstrip("/")
            if normalized:
                result.append(normalized)
        return result

    def prepare_value(self, value):
        """Convert a list of items into a text area (one per line)."""
        if not value:
            return ""
        return "\n".join(value)


class AddonsConfigForm(forms.ModelForm):
    """Form to opt-in into new addons."""

    project = forms.CharField(widget=forms.HiddenInput(), required=False)
    filetreediff_ignored_files = OnePerLineList(required=False)

    class Meta:
        model = AddonsConfig
        fields = (
            "enabled",
            "project",
            "options_root_selector",
            "analytics_enabled",
            "doc_diff_enabled",
            "filetreediff_enabled",
            "filetreediff_ignored_files",
            "flyout_enabled",
            "flyout_sorting",
            "flyout_sorting_latest_stable_at_beginning",
            "flyout_sorting_custom_pattern",
            "flyout_position",
            "hotkeys_enabled",
            "search_enabled",
            "linkpreviews_enabled",
            "linkpreviews_selector",
            "notifications_enabled",
            "notifications_show_on_latest",
            "notifications_show_on_non_stable",
            "notifications_show_on_external",
        )
        labels = {
            "enabled": _("Enable Addons"),
            "doc_diff_enabled": _("Visual diff enabled"),
            "filetreediff_enabled": _("Enabled"),
            "filetreediff_ignored_files": _("Ignored files"),
            "notifications_show_on_external": _("Show a notification on builds from pull requests"),
            "notifications_show_on_non_stable": _("Show a notification on non-stable versions"),
            "notifications_show_on_latest": _("Show a notification on latest version"),
            "linkpreviews_enabled": _("Enabled"),
            "linkpreviews_selector": _("CSS link previews selector"),
            "options_root_selector": _("CSS main content selector"),
        }

        widgets = {
            "options_root_selector": forms.TextInput(attrs={"placeholder": "[role=main]"}),
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        kwargs["instance"] = self.project.addons
        super().__init__(*args, **kwargs)

        # Keep the ability to disable addons completely on Read the Docs for Business
        if not settings.RTD_ALLOW_ORGANIZATIONS:
            self.fields["enabled"].disabled = True

    def clean(self):
        if (
            self.cleaned_data["flyout_sorting"] == ADDONS_FLYOUT_SORTING_CUSTOM_PATTERN
            and not self.cleaned_data["flyout_sorting_custom_pattern"]
        ):
            raise forms.ValidationError(
                _("The flyout sorting custom pattern is required when selecting a custom pattern."),
            )
        return super().clean()

    def clean_project(self):
        return self.project


class UserForm(forms.Form):
    """Project owners form."""

    username_or_email = forms.CharField(label=_("Email address or username"))

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean_username_or_email(self):
        username = self.cleaned_data["username_or_email"]
        user = User.objects.filter(
            Q(username=username) | Q(emailaddress__verified=True, emailaddress__email=username)
        ).first()
        if not user:
            raise forms.ValidationError(
                _("User %(username)s does not exist"), params={"username": username}
            )
        if self.project.users.filter(pk=user.pk).exists():
            raise forms.ValidationError(
                _("User %(username)s is already a maintainer"),
                params={"username": username},
            )
        return user

    def save(self):
        invitation, _ = Invitation.objects.invite(
            from_user=self.request.user,
            to_user=self.cleaned_data["username_or_email"],
            obj=self.project,
        )
        return invitation


class EmailHookForm(forms.Form):
    """Project email notification form."""

    email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        self.email = EmailHook.objects.get_or_create(
            email=self.cleaned_data["email"],
            project=self.project,
        )[0]
        return self.email

    def save(self):
        self.project.emailhook_notifications.add(self.email)
        return self.project


class WebHookForm(forms.ModelForm):
    """Webhook form."""

    project = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = WebHook
        fields = ["project", "url", "events", "payload", "secret"]
        widgets = {
            "events": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            # Show secret in the detail form, but as readonly.
            self.fields["secret"].disabled = True
        else:
            # Don't show the secret in the creation form.
            self.fields.pop("secret")
            self.fields["payload"].initial = json.dumps(
                {
                    "event": "{{ event }}",
                    "name": "{{ project.name }}",
                    "slug": "{{ project.slug }}",
                    "version": "{{ version.slug }}",
                    "commit": "{{ build.commit }}",
                    "build": "{{ build.id }}",
                    "start_date": "{{ build.start_date }}",
                    "build_url": "{{ build.url }}",
                    "docs_url": "{{ build.docs_url }}",
                },
                indent=2,
            )

    def clean_project(self):
        return self.project

    def clean_payload(self):
        """Check if the payload is a valid json object and format it."""
        payload = self.cleaned_data["payload"]
        try:
            payload = json.loads(payload)
            payload = json.dumps(payload, indent=2)
        except Exception as exc:
            raise forms.ValidationError(_("The payload must be a valid JSON object.")) from exc
        return payload


class TranslationBaseForm(forms.Form):
    """Project translation form."""

    project = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop("parent", None)
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["project"].choices = self.get_choices()

    def get_choices(self):
        return [
            (
                project.slug,
                "{project} ({lang})".format(
                    project=project.slug,
                    lang=project.get_language_display(),
                ),
            )
            for project in self.get_translation_queryset().all()
        ]

    def clean(self):
        if not self.parent.supports_translations:
            raise forms.ValidationError(
                _(
                    "This project is configured with a versioning scheme that doesn't support translations."
                ),
            )
        return super().clean()

    def clean_project(self):
        """Ensures that selected project is valid as a translation."""

        translation_project_slug = self.cleaned_data["project"]

        # Ensure parent project isn't already itself a translation
        if self.parent.main_language_project is not None:
            msg = 'Project "{project}" is already a translation'
            raise forms.ValidationError(
                (_(msg).format(project=self.parent.slug)),
            )

        project_translation_qs = self.get_translation_queryset().filter(
            slug=translation_project_slug,
        )
        if not project_translation_qs.exists():
            msg = 'Project "{project}" does not exist.'
            raise forms.ValidationError(
                (_(msg).format(project=translation_project_slug)),
            )
        self.translation = project_translation_qs.first()
        if self.translation.language == self.parent.language:
            msg = "Both projects can not have the same language ({lang})."
            raise forms.ValidationError(
                _(msg).format(lang=self.parent.get_language_display()),
            )

        # yapf: disable
        exists_translation = (
            self.parent.translations
            .filter(language=self.translation.language)
            .exists()
        )
        # yapf: enable
        if exists_translation:
            msg = "This project already has a translation for {lang}."
            raise forms.ValidationError(
                _(msg).format(lang=self.translation.get_language_display()),
            )
        is_parent = self.translation.translations.exists()
        if is_parent:
            msg = "A project with existing translations can not be added as a project translation."
            raise forms.ValidationError(_(msg))
        return translation_project_slug

    def get_translation_queryset(self):
        queryset = (
            Project.objects.for_admin_user(self.user)
            .filter(main_language_project=None)
            .exclude(pk=self.parent.pk)
        )
        return queryset

    def save(self, commit=True):
        if commit:
            # Don't use ``self.parent.translations.add()`` here as this
            # triggers a problem with database routing and multiple databases.
            # Directly set the ``main_language_project`` instead of doing a
            # bulk update.
            self.translation.main_language_project = self.parent
            self.translation.save()
            # Run other sync logic to make sure we are in a good state.
            self.parent.save()
        return self.parent


class TranslationForm(SettingsOverrideObject):
    _default_class = TranslationBaseForm


class RedirectForm(forms.ModelForm):
    """Form for project redirects."""

    project = forms.CharField(widget=forms.HiddenInput(), required=False, disabled=True)

    class Meta:
        model = Redirect
        fields = [
            "project",
            "redirect_type",
            "from_url",
            "to_url",
            "http_status",
            "force",
            "enabled",
            "description",
        ]

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

        # Remove the nullable option from the form.
        self.fields["enabled"].widget = forms.CheckboxInput()
        self.fields["enabled"].empty_value = False

        # Remove the nullable option from the form.
        # TODO: remove after migration.
        self.fields["force"].widget = forms.CheckboxInput()
        self.fields["force"].empty_value = False

    def clean_project(self):
        return self.project


class DomainForm(forms.ModelForm):
    """Form to configure a custom domain name for a project."""

    project = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Domain
        fields = ["project", "domain", "canonical", "https"]

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

        # Disable domain manipulation on Update, but allow on Create
        if self.instance.pk:
            self.fields["domain"].disabled = True

        # Remove the https option at creation,
        # but show it if the domain is already marked as http only,
        # so users can upgrade.
        if not self.instance.pk or self.instance.https:
            self.fields.pop("https")

    def clean_project(self):
        return self.project

    def clean_domain(self):
        """Validates domain."""
        domain = self.cleaned_data["domain"].lower()
        parsed = self._safe_urlparse(domain)

        # Force the scheme to have a valid netloc.
        if not parsed.scheme:
            parsed = self._safe_urlparse(f"https://{domain}")

        domain_string = parsed.netloc.strip()
        if not domain_string:
            raise forms.ValidationError(f"{domain} is not a valid domain.")

        for invalid_domain in settings.RTD_RESTRICTED_DOMAINS:
            if invalid_domain and domain_string.endswith(invalid_domain):
                raise forms.ValidationError(f"{invalid_domain} is not a valid domain.")

        # Run this check only on domain creation.
        if not self.instance.pk:
            self._check_for_suspicious_cname(domain_string)

        return domain_string

    def _check_for_suspicious_cname(self, domain):
        """
        Check if a domain has a suspicious CNAME record.

        The domain is suspicious if:

        - Has a CNAME pointing to another CNAME.
          This prevents the subdomain from being hijacked if the last subdomain is on RTD,
          but the user didn't register the other subdomain.
          Example: doc.example.com -> docs.example.com -> readthedocs.io,
          We don't want to allow doc.example.com to be added.
        - Has a CNAME pointing to the APEX domain.
          This prevents a subdomain from being hijacked if the APEX domain is on RTD.
          A common case is `www` pointing to the APEX domain, but users didn't register the
          `www` subdomain, only the APEX domain.
          Example: www.example.com -> example.com -> readthedocs.io,
          we don't want to allow www.example.com to be added.
        """
        cname = self._get_cname(domain)
        # Doesn't have a CNAME record, we are good.
        if not cname:
            return

        # If the domain has a CNAME pointing to the APEX domain, that's not good.
        # This check isn't perfect, but it's a good enoug heuristic
        # to dectect CNAMES like www.example.com -> example.com.
        if f"{domain}.".endswith(f".{cname}"):
            raise forms.ValidationError(
                _(
                    "This domain has a CNAME record pointing to the APEX domain. "
                    "Please remove the CNAME before adding the domain.",
                ),
            )

        second_cname = self._get_cname(cname)
        # The domain has a CNAME pointing to another CNAME, That's not good.
        if second_cname:
            raise forms.ValidationError(
                _(
                    "This domain has a CNAME record pointing to another CNAME. "
                    "Please remove the CNAME before adding the domain.",
                ),
            )

    def _get_cname(self, domain):
        try:
            answers = dns.resolver.resolve(domain, "CNAME", lifetime=1)
            # dnspython doesn't recursively resolve CNAME records.
            # We always have one response or none.
            return str(answers[0].target)
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            return None
        except dns.resolver.LifetimeTimeout:
            raise forms.ValidationError(
                _("DNS resolution timed out. Make sure the domain is correct, or try again later."),
            )
        except dns.name.EmptyLabel:
            raise forms.ValidationError(
                _("The domain is not valid."),
            )

    def _safe_urlparse(self, url):
        """Wrapper around urlparse to throw ValueError exceptions as ValidationError."""
        try:
            return urlparse(url)
        except ValueError:
            raise forms.ValidationError("Invalid domain")

    def clean_canonical(self):
        canonical = self.cleaned_data["canonical"]
        pk = self.instance.pk
        has_canonical_domain = (
            Domain.objects.filter(project=self.project, canonical=True).exclude(pk=pk).exists()
        )
        if canonical and has_canonical_domain:
            raise forms.ValidationError(
                _("Only one domain can be canonical at a time."),
            )
        return canonical


class IntegrationForm(forms.ModelForm):
    """
    Form to add an integration.

    This limits the choices of the integration type to webhook integration types
    """

    project = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Integration
        fields = [
            "project",
            "integration_type",
        ]

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        # Alter the integration type choices to only provider webhooks
        self.fields[
            "integration_type"
        ].choices = Integration.WEBHOOK_INTEGRATIONS  # yapf: disable  # noqa

    def clean_project(self):
        return self.project

    def save(self, commit=True):
        self.instance = Integration.objects.subclass(self.instance)
        return super().save(commit)


class ProjectAdvertisingForm(forms.ModelForm):
    """Project promotion opt-out form."""

    class Meta:
        model = Project
        fields = ["allow_promos"]

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)


class FeatureForm(forms.ModelForm):
    """
    Project feature form for dynamic admin choices.

    This form converts the CharField into a ChoiceField on display. The
    underlying driver won't attempt to do validation on the choices, and so we
    can dynamically populate this list.
    """

    feature_id = forms.ChoiceField()

    class Meta:
        model = Feature
        fields = ["projects", "feature_id", "default_true", "future_default_true"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["feature_id"].choices = Feature.FEATURES


class EnvironmentVariableForm(forms.ModelForm):
    """
    Form to add an EnvironmentVariable to a Project.

    This limits the name of the variable.
    """

    project = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = EnvironmentVariable
        fields = ("name", "value", "public", "project")

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

        # Remove the nullable option from the form.
        # TODO: remove after migration.
        self.fields["public"].widget = forms.CheckboxInput()
        self.fields["public"].empty_value = False

    def clean_project(self):
        return self.project

    def clean_name(self):
        """Validate environment variable name chosen."""
        name = self.cleaned_data["name"]
        if name.startswith("__"):
            raise forms.ValidationError(
                _("Variable name can't start with __ (double underscore)"),
            )
        if name.startswith("READTHEDOCS"):
            raise forms.ValidationError(
                _("Variable name can't start with READTHEDOCS"),
            )
        if self.project.environmentvariable_set.filter(name=name).exists():
            raise forms.ValidationError(
                _(
                    "There is already a variable with this name for this project",
                ),
            )
        if " " in name:
            raise forms.ValidationError(
                _("Variable name can't contain spaces"),
            )
        if not fullmatch("[a-zA-Z0-9_]+", name):
            raise forms.ValidationError(
                _("Only letters, numbers and underscore are allowed"),
            )
        return name
