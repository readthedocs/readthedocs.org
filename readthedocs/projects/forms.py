"""Project forms."""
import json
from random import choice
from re import fullmatch
from urllib.parse import urlparse

from allauth.socialaccount.models import SocialAccount
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from readthedocs.builds.constants import INTERNAL
from readthedocs.core.forms import PrevalidatedForm, RichValidationError
from readthedocs.core.history import SimpleHistoryModelForm
from readthedocs.core.permissions import AdminPermission
from readthedocs.core.utils import slugify, trigger_build
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.integrations.models import Integration
from readthedocs.invitations.models import Invitation
from readthedocs.oauth.models import RemoteRepository
from readthedocs.organizations.models import Team
from readthedocs.projects.models import (
    AddonsConfig,
    Domain,
    EmailHook,
    EnvironmentVariable,
    Feature,
    Project,
    ProjectRelationship,
    WebHook,
)
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

    def save(self, commit=True):
        project = super().save(commit)
        if commit:
            if self.user and not project.users.filter(pk=self.user.pk).exists():
                project.users.add(self.user)
        return project


class ProjectTriggerBuildMixin:

    """
    Mixin to trigger build on form save.

    This should be replaced with signals instead of calling trigger_build
    explicitly.
    """

    def save(self, commit=True):
        """Trigger build on commit save."""
        project = super().save(commit)
        if commit:
            trigger_build(project=project)
        return project


class ProjectBackendForm(forms.Form):

    """Get the import backend."""

    backend = forms.CharField()


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
        fields = ("name", "repo", "default_branch", "language")

    remote_repository = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["repo"].widget.attrs["placeholder"] = self.placehold_repo()
        self.fields["repo"].widget.attrs["required"] = True

    def save(self, commit=True):
        """Add remote repository relationship to the project instance."""
        instance = super().save(commit)
        remote_repo = self.cleaned_data.get("remote_repository", None)
        if remote_repo:
            if commit:
                remote_repo.projects.add(self.instance)
                remote_repo.save()
            else:
                instance.remote_repository = remote_repo
        return instance

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

    def clean_remote_repository(self):
        remote_repo = self.cleaned_data.get("remote_repository", None)
        if not remote_repo:
            return None
        try:
            return RemoteRepository.objects.get(
                pk=remote_repo,
                users=self.user,
            )
        except RemoteRepository.DoesNotExist as exc:
            raise forms.ValidationError(_("Repository invalid")) from exc

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


class ProjectConfigForm(forms.Form):

    """Simple intermediate step to communicate about the .readthedocs.yaml file."""

    def __init__(self, *args, **kwargs):
        # Remove 'user' field since it's not expected by BaseForm.
        kwargs.pop("user")
        super().__init__(*args, **kwargs)


class UpdateProjectForm(
    ProjectTriggerBuildMixin,
    ProjectBasicsForm,
):

    """Main project settings form."""

    class Meta:
        model = Project
        fields = (
            # Basics and repo settings
            "name",
            "repo",
            "repo_type",
            "default_branch",
            "language",
            "description",
            # Project related settings
            "default_version",
            "privacy_level",
            "versioning_scheme",
            "external_builds_enabled",
            "external_builds_privacy_level",
            "readthedocs_yaml_path",
            "analytics_code",
            "analytics_disabled",
            "show_version_warning",
            # Meta data
            "programming_language",
            "project_url",
            "tags",
        )

    description = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.Textarea,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the nullable option from the form
        self.fields["analytics_disabled"].widget = forms.CheckboxInput()
        self.fields["analytics_disabled"].empty_value = False

        # Remove empty choice from options.
        self.fields["versioning_scheme"].choices = [
            (key, value)
            for key, value in self.fields["versioning_scheme"].choices
            if key
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

    def setup_external_builds_option(self):
        """Disable the external builds option if the project doesn't meet the requirements."""
        if settings.ALLOW_PRIVATE_REPOS and self.instance.remote_repository:
            self.fields["external_builds_privacy_level"].disabled = True
            if self.instance.remote_repository.private:
                help_text = _(
                    "We have detected that this project is private, pull request previews are set to private."
                )
            else:
                help_text = _(
                    "We have detected that this project is public, pull request previews are set to public."
                )
            self.fields["external_builds_privacy_level"].help_text = help_text

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
            field = self.fields["external_builds_enabled"]
            field.disabled = True
            field.help_text = f"{msg} {field.help_text}"

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
            all_versions = [
                (version.slug, version.verbose_name) for version in version_qs
            ]
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
            self.fields["child"].queryset = Project.objects.filter(
                pk=self.instance.child.pk
            )
        else:
            self.fields["child"].queryset = self.project.get_subproject_candidates(
                self.user
            )

    def clean_parent(self):
        self.project.is_valid_as_superproject(forms.ValidationError)
        return self.project

    def clean_alias(self):
        alias = self.cleaned_data["alias"]
        subproject = self.project.subprojects.filter(alias=alias).exclude(
            id=self.instance.pk
        )

        if subproject.exists():
            raise forms.ValidationError(
                _("A subproject with this alias already exists"),
            )
        return alias


class AddonsConfigForm(forms.ModelForm):

    """Form to opt-in into new beta addons."""

    project = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = AddonsConfig
        fields = (
            "enabled",
            "project",
            "analytics_enabled",
            "doc_diff_enabled",
            "external_version_warning_enabled",
            "flyout_enabled",
            "hotkeys_enabled",
            "search_enabled",
            "stable_latest_version_warning_enabled",
        )
        labels = {
            "enabled": _("Enable Addons"),
            "external_version_warning_enabled": _(
                "Show a notification on builds from pull requests"
            ),
            "stable_latest_version_warning_enabled": _(
                "Show a notification on non-stable and latest versions"
            ),
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        addons, created = AddonsConfig.objects.get_or_create(project=self.project)
        if created:
            addons.enabled = False
            addons.save()

        kwargs["instance"] = addons
        super().__init__(*args, **kwargs)

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
            Q(username=username)
            | Q(emailaddress__verified=True, emailaddress__email=username)
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
            raise forms.ValidationError(
                _("The payload must be a valid JSON object.")
            ) from exc
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
            msg = (
                "A project with existing translations "
                "can not be added as a project translation."
            )
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
        parsed = urlparse(domain)

        # Force the scheme to have a valid netloc.
        if not parsed.scheme:
            parsed = urlparse(f"https://{domain}")

        if not parsed.netloc:
            raise forms.ValidationError(f"{domain} is not a valid domain.")

        domain_string = parsed.netloc

        # Don't allow internal domains to be added, we have:
        # - Dashboard domain
        # - Public domain (from where documentation pages are served)
        # - External version domain (from where PR previews are served)
        for invalid_domain in [
            settings.PRODUCTION_DOMAIN,
            settings.PUBLIC_DOMAIN,
            settings.RTD_EXTERNAL_VERSION_DOMAIN,
        ]:
            if invalid_domain and domain_string.endswith(invalid_domain):
                raise forms.ValidationError(f"{invalid_domain} is not a valid domain.")

        return domain_string

    def clean_canonical(self):
        canonical = self.cleaned_data["canonical"]
        pk = self.instance.pk
        has_canonical_domain = (
            Domain.objects.filter(project=self.project, canonical=True)
            .exclude(pk=pk)
            .exists()
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
