"""Project forms."""
from random import choice
from re import fullmatch
from urllib.parse import urlparse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, HTML, Submit
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from textclassifier.validators import ClassifierValidator

from readthedocs.builds.constants import INTERNAL
from readthedocs.core.mixins import HideProtectedLevelMixin
from readthedocs.core.utils import slugify, trigger_build
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.integrations.models import Integration
from readthedocs.oauth.models import RemoteRepository
from readthedocs.projects.exceptions import ProjectSpamError
from readthedocs.projects.models import (
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


class ProjectForm(forms.ModelForm):

    """
    Project form.

    :param user: If provided, add this user as a project user on save
    """

    required_css_class = 'required'

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
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


class ProjectBasicsForm(ProjectForm):

    """Form for basic project fields."""

    class Meta:
        model = Project
        fields = ('name', 'repo', 'repo_type')

    remote_repository = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        show_advanced = kwargs.pop('show_advanced', False)
        super().__init__(*args, **kwargs)
        if show_advanced:
            self.fields['advanced'] = forms.BooleanField(
                required=False,
                label=_('Edit advanced project options'),
            )
        self.fields['repo'].widget.attrs['placeholder'] = self.placehold_repo()
        self.fields['repo'].widget.attrs['required'] = True

    def save(self, commit=True):
        """Add remote repository relationship to the project instance."""
        instance = super().save(commit)
        remote_repo = self.cleaned_data.get('remote_repository', None)
        if remote_repo:
            if commit:
                remote_repo.project = self.instance
                remote_repo.save()
            else:
                instance.remote_repository = remote_repo
        return instance

    def clean_name(self):
        name = self.cleaned_data.get('name', '')
        if not self.instance.pk:
            potential_slug = slugify(name)
            if Project.objects.filter(slug=potential_slug).exists():
                raise forms.ValidationError(
                    _('Invalid project name, a project already exists with that name'),
                )  # yapf: disable # noqa
            if not potential_slug:
                # Check the generated slug won't be empty
                raise forms.ValidationError(_('Invalid project name'),)

        return name

    def clean_repo(self):
        repo = self.cleaned_data.get('repo', '')
        return repo.rstrip('/')

    def clean_remote_repository(self):
        remote_repo = self.cleaned_data.get('remote_repository', None)
        if not remote_repo:
            return None
        try:
            return RemoteRepository.objects.get(
                pk=remote_repo,
                users=self.user,
            )
        except RemoteRepository.DoesNotExist:
            raise forms.ValidationError(_('Repository invalid'))

    def placehold_repo(self):
        return choice([
            'https://bitbucket.org/cherrypy/cherrypy',
            'https://bitbucket.org/birkenfeld/sphinx',
            'https://bitbucket.org/hpk42/tox',
            'https://github.com/zzzeek/sqlalchemy.git',
            'https://github.com/django/django.git',
            'https://github.com/fabric/fabric.git',
            'https://github.com/ericholscher/django-kong.git',
        ])


class ProjectExtraForm(ProjectForm):

    """Additional project information form."""

    class Meta:
        model = Project
        fields = (
            'description',
            'documentation_type',
            'language',
            'programming_language',
            'tags',
            'project_url',
        )

    description = forms.CharField(
        validators=[ClassifierValidator(raises=ProjectSpamError)],
        required=False,
        widget=forms.Textarea,
    )

    def clean_tags(self):
        tags = self.cleaned_data.get('tags', [])
        for tag in tags:
            if len(tag) > 100:
                raise forms.ValidationError(
                    _(
                        'Length of each tag must be less than or equal to 100 characters.',
                    ),
                )
        return tags


class ProjectAdvancedForm(HideProtectedLevelMixin, ProjectTriggerBuildMixin, ProjectForm):

    """Advanced project option form."""

    class Meta:
        model = Project
        per_project_settings = (
            'default_version',
            'default_branch',
            'privacy_level',
            'analytics_code',
            'show_version_warning',
            'single_version',
        )
        # These that can be set per-version using a config file.
        per_version_settings = (
            'documentation_type',
            'requirements_file',
            'python_interpreter',
            'install_project',
            'use_system_packages',
            'conf_py_file',
            'enable_pdf_build',
            'enable_epub_build',
        )
        fields = (
            *per_project_settings,
            *per_version_settings,
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        help_text = render_to_string(
            'projects/project_advanced_settings_helptext.html'
        )
        self.helper.layout = Layout(
            Fieldset(
                _("Global settings"),
                *self.Meta.per_project_settings,
            ),
            Fieldset(
                _("Default settings"),
                HTML(help_text),
                *self.Meta.per_version_settings,
            ),
        )
        self.helper.add_input(Submit('save', _('Save')))

        default_choice = (None, '-' * 9)
        versions_choices = self.instance.versions(manager=INTERNAL).filter(
            machine=False).values_list('verbose_name', flat=True)

        self.fields['default_branch'].widget = forms.Select(
            choices=[default_choice] + list(
                zip(versions_choices, versions_choices)
            ),
        )

        active_versions = self.get_all_active_versions()

        if active_versions:
            self.fields['default_version'].widget = forms.Select(
                choices=active_versions,
            )
        else:
            self.fields['default_version'].widget.attrs['readonly'] = True

    def clean_conf_py_file(self):
        filename = self.cleaned_data.get('conf_py_file', '').strip()
        if filename and 'conf.py' not in filename:
            raise forms.ValidationError(
                _(
                    'Your configuration file is invalid, make sure it contains '
                    'conf.py in it.',
                ),
            )  # yapf: disable
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


class UpdateProjectForm(
        ProjectTriggerBuildMixin,
        ProjectBasicsForm,
        ProjectExtraForm,
):

    class Meta:
        model = Project
        fields = (
            # Basics
            'name',
            'repo',
            'repo_type',
            # Extra
            'description',
            'language',
            'programming_language',
            'project_url',
            'tags',
        )

    def clean_language(self):
        language = self.cleaned_data['language']
        project = self.instance
        if project:
            msg = _(
                'There is already a "{lang}" translation '
                'for the {proj} project.',
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
                    main_project.translations
                    .filter(language=language)
                    .exclude(pk=project.pk)
                    .exists()
                )
                if siblings:
                    raise forms.ValidationError(
                        msg.format(lang=language, proj=main_project.slug),
                    )
        return language


class ProjectRelationshipBaseForm(forms.ModelForm):

    """Form to add/update project relationships."""

    parent = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = ProjectRelationship
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project')
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        # Don't display the update form with an editable child, as it will be
        # filtered out from the queryset anyways.
        if hasattr(self, 'instance') and self.instance.pk is not None:
            self.fields['child'].queryset = Project.objects.filter(pk=self.instance.child.pk)
        else:
            self.fields['child'].queryset = self.get_subproject_queryset()

    def clean_parent(self):
        if self.project.superprojects.exists():
            # This validation error is mostly for testing, users shouldn't see
            # this in normal circumstances
            raise forms.ValidationError(
                _('Subproject nesting is not supported'),
            )
        return self.project

    def clean_child(self):
        child = self.cleaned_data['child']
        if child == self.project:
            raise forms.ValidationError(
                _('A project can not be a subproject of itself'),
            )
        return child

    def clean_alias(self):
        alias = self.cleaned_data['alias']
        subproject = self.project.subprojects.filter(
            alias=alias).exclude(id=self.instance.pk)

        if subproject.exists():
            raise forms.ValidationError(
                _('A subproject with this alias already exists'),
            )
        return alias

    def get_subproject_queryset(self):
        """
        Return scrubbed subproject choice queryset.

        This removes projects that are either already a subproject of another
        project, or are a superproject, as neither case is supported.
        """
        queryset = (
            Project.objects.for_admin_user(self.user)
            .exclude(subprojects__isnull=False)
            .exclude(superprojects__isnull=False)
            .exclude(pk=self.project.pk)
        )
        return queryset


class ProjectRelationshipForm(SettingsOverrideObject):
    _default_class = ProjectRelationshipBaseForm


class UserForm(forms.Form):

    """Project user association form."""

    user = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)

    def clean_user(self):
        name = self.cleaned_data['user']
        user_qs = User.objects.filter(username=name)
        if not user_qs.exists():
            raise forms.ValidationError(
                _('User {name} does not exist').format(name=name),
            )
        self.user = user_qs[0]
        return name

    def save(self):
        self.project.users.add(self.user)
        return self.user


class EmailHookForm(forms.Form):

    """Project email notification form."""

    email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        self.email = EmailHook.objects.get_or_create(
            email=self.cleaned_data['email'],
            project=self.project,
        )[0]
        return self.email

    def save(self):
        self.project.emailhook_notifications.add(self.email)
        return self.project


class WebHookForm(forms.ModelForm):

    """Project webhook form."""

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        self.webhook = WebHook.objects.get_or_create(
            url=self.cleaned_data['url'],
            project=self.project,
        )[0]
        self.project.webhook_notifications.add(self.webhook)
        return self.project

    def clean_url(self):
        url = self.cleaned_data.get('url')
        if not url:
            raise forms.ValidationError(
                _('This field is required.')
            )
        return url

    class Meta:
        model = WebHook
        fields = ['url']


class TranslationBaseForm(forms.Form):

    """Project translation form."""

    project = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop('parent', None)
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['project'].choices = self.get_choices()

    def get_choices(self):
        return [(
            project.slug,
            '{project} ({lang})'.format(
                project=project.slug,
                lang=project.get_language_display(),
            ),
        ) for project in self.get_translation_queryset().all()]

    def clean_project(self):
        translation_project_slug = self.cleaned_data['project']

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
            msg = ('Both projects can not have the same language ({lang}).')
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
            msg = ('This project already has a translation for {lang}.')
            raise forms.ValidationError(
                _(msg).format(lang=self.translation.get_language_display()),
            )
        is_parent = self.translation.translations.exists()
        if is_parent:
            msg = (
                'A project with existing translations '
                'can not be added as a project translation.'
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
            # triggeres a problem with database routing and multiple databases.
            # Directly set the ``main_language_project`` instead of doing a
            # bulk update.
            self.translation.main_language_project = self.parent
            self.translation.save()
            # Run symlinking and other sync logic to make sure we are in a good
            # state.
            self.parent.save()
        return self.parent


class TranslationForm(SettingsOverrideObject):
    _default_class = TranslationBaseForm


class RedirectForm(forms.ModelForm):

    """Form for project redirects."""

    class Meta:
        model = Redirect
        fields = ['redirect_type', 'from_url', 'to_url']

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)

    def save(self, **_):  # pylint: disable=arguments-differ
        # TODO this should respect the unused argument `commit`. It's not clear
        # why this needs to be a call to `create`, instead of relying on the
        # super `save()` call.
        redirect = Redirect.objects.create(
            project=self.project,
            redirect_type=self.cleaned_data['redirect_type'],
            from_url=self.cleaned_data['from_url'],
            to_url=self.cleaned_data['to_url'],
        )
        return redirect


class DomainBaseForm(forms.ModelForm):

    """Form to configure a custom domain name for a project."""

    project = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Domain
        exclude = ['machine', 'cname', 'count']  # pylint: disable=modelform-uses-exclude
        error_messages = {
            'domain':  {
                'unique': (
                    'This domain is already configured. '
                    'Please choose another.'
                ),
            }
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)

        # Disable domain manipulation on Update, but allow on Create
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['domain'].disabled = True

    def clean_project(self):
        return self.project

    def clean_domain(self):
        parsed = urlparse(self.cleaned_data['domain'])
        if parsed.scheme or parsed.netloc:
            domain_string = parsed.netloc
        else:
            domain_string = parsed.path

        return domain_string

    def clean_canonical(self):
        canonical = self.cleaned_data['canonical']
        _id = self.initial.get('id')
        if canonical and Domain.objects.filter(project=self.project, canonical=True).exclude(pk=_id).exists():  # yapf: disabled  # noqa
            raise forms.ValidationError(
                _('Only 1 Domain can be canonical at a time.'),
            )
        return canonical


class DomainForm(SettingsOverrideObject):
    _default_class = DomainBaseForm


class IntegrationForm(forms.ModelForm):

    """
    Form to add an integration.

    This limits the choices of the integration type to webhook integration types
    """

    project = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Integration
        exclude = ['provider_data', 'exchanges', 'secret']  # pylint: disable=modelform-uses-exclude

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        # Alter the integration type choices to only provider webhooks
        self.fields['integration_type'].choices = Integration.WEBHOOK_INTEGRATIONS  # yapf: disable  # noqa

    def clean_project(self):
        return self.project

    def save(self, commit=True):
        self.instance = Integration.objects.subclass(self.instance)
        # We don't set the secret on the integration
        # when it's created via the form.
        self.instance.secret = None
        return super().save(commit)


class ProjectAdvertisingForm(forms.ModelForm):

    """Project promotion opt-out form."""

    class Meta:
        model = Project
        fields = ['allow_promos']

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
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
        fields = ['projects', 'feature_id', 'default_true']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['feature_id'].choices = Feature.FEATURES


class EnvironmentVariableForm(forms.ModelForm):

    """
    Form to add an EnvironmentVariable to a Project.

    This limits the name of the variable.
    """

    project = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = EnvironmentVariable
        fields = ('name', 'value', 'project')

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)

    def clean_project(self):
        return self.project

    def clean_name(self):
        name = self.cleaned_data['name']
        if name.startswith('__'):
            raise forms.ValidationError(
                _("Variable name can't start with __ (double underscore)"),
            )
        elif name.startswith('READTHEDOCS'):
            raise forms.ValidationError(
                _("Variable name can't start with READTHEDOCS"),
            )
        elif self.project.environmentvariable_set.filter(name=name).exists():
            raise forms.ValidationError(
                _(
                    'There is already a variable with this name for this project',
                ),
            )
        elif ' ' in name:
            raise forms.ValidationError(
                _("Variable name can't contain spaces"),
            )
        elif not fullmatch('[a-zA-Z0-9_]+', name):
            raise forms.ValidationError(
                _('Only letters, numbers and underscore are allowed'),
            )
        return name
