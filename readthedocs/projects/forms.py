# -*- coding: utf-8 -*-
"""Project forms."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from random import choice

from builtins import object
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from future.backports.urllib.parse import urlparse
from guardian.shortcuts import assign
from textclassifier.validators import ClassifierValidator

from readthedocs.builds.constants import TAG
from readthedocs.core.utils import slugify, trigger_build
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.integrations.models import Integration
from readthedocs.oauth.models import RemoteRepository
from readthedocs.projects import constants
from readthedocs.projects.exceptions import ProjectSpamError
from readthedocs.projects.models import (
    Domain, EmailHook, Feature, Project, ProjectRelationship, WebHook)
from readthedocs.redirects.models import Redirect


class ProjectForm(forms.ModelForm):

    """
    Project form.

    :param user: If provided, add this user as a project user on save
    """

    required_css_class = 'required'

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ProjectForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        project = super(ProjectForm, self).save(commit)
        if commit:
            if self.user and not project.users.filter(pk=self.user.pk).exists():
                project.users.add(self.user)
        return project


class ProjectTriggerBuildMixin(object):

    """
    Mixin to trigger build on form save.

    This should be replaced with signals instead of calling trigger_build
    explicitly.
    """

    def save(self, commit=True):
        """Trigger build on commit save."""
        project = super(ProjectTriggerBuildMixin, self).save(commit)
        if commit:
            trigger_build(project=project)
        return project


class ProjectBackendForm(forms.Form):

    """Get the import backend."""

    backend = forms.CharField()


class ProjectBasicsForm(ProjectForm):

    """Form for basic project fields."""

    class Meta(object):
        model = Project
        fields = ('name', 'repo', 'repo_type')

    remote_repository = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        show_advanced = kwargs.pop('show_advanced', False)
        super(ProjectBasicsForm, self).__init__(*args, **kwargs)
        if show_advanced:
            self.fields['advanced'] = forms.BooleanField(
                required=False,
                label=_('Edit advanced project options'),
            )
        self.fields['repo'].widget.attrs['placeholder'] = self.placehold_repo()
        self.fields['repo'].widget.attrs['required'] = True

    def save(self, commit=True):
        """Add remote repository relationship to the project instance."""
        instance = super(ProjectBasicsForm, self).save(commit)
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
                    _('Invalid project name, a project already exists with that name'))  # yapf: disable # noqa
        return name

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

    class Meta(object):
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


class ProjectAdvancedForm(ProjectTriggerBuildMixin, ProjectForm):

    """Advanced project option form."""

    python_interpreter = forms.ChoiceField(
        choices=constants.PYTHON_CHOICES,
        initial='python',
        help_text=_('The Python interpreter used to create the virtual '
                    'environment.'),
    )

    class Meta(object):
        model = Project
        fields = (
            # Standard build edits
            'install_project',
            'requirements_file',
            'single_version',
            'conf_py_file',
            'default_branch',
            'default_version',
            'show_version_warning',
            'enable_pdf_build',
            'enable_epub_build',
            # Privacy
            'privacy_level',
            # 'version_privacy_level',
            # Python specific
            'use_system_packages',
            'python_interpreter',
            # Fringe
            'analytics_code',
            # Version Support
            # 'num_major', 'num_minor', 'num_point',
        )

    def clean_conf_py_file(self):
        filename = self.cleaned_data.get('conf_py_file', '').strip()
        if filename and 'conf.py' not in filename:
            raise forms.ValidationError(
                _('Your configuration file is invalid, make sure it contains '
                  'conf.py in it.'))  # yapf: disable
        return filename


class UpdateProjectForm(ProjectTriggerBuildMixin, ProjectBasicsForm,
                        ProjectExtraForm):
    class Meta(object):
        model = Project
        fields = (
            # Basics
            'name',
            'repo',
            'repo_type',
            # Extra
            'description',
            'documentation_type',
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
                'for the {proj} project.'
            )
            if project.translations.filter(language=language).exists():
                raise forms.ValidationError(
                    msg.format(lang=language, proj=project.slug)
                )
            main_project = project.main_language_project
            if main_project:
                if main_project.language == language:
                    raise forms.ValidationError(
                        msg.format(lang=language, proj=main_project.slug)
                    )
                siblings = (
                    main_project.translations
                    .filter(language=language)
                    .exclude(pk=project.pk)
                    .exists()
                )
                if siblings:
                    raise forms.ValidationError(
                        msg.format(lang=language, proj=main_project.slug)
                    )
        return language


class ProjectRelationshipBaseForm(forms.ModelForm):

    """Form to add/update project relationships."""

    parent = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta(object):
        model = ProjectRelationship
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project')
        self.user = kwargs.pop('user')
        super(ProjectRelationshipBaseForm, self).__init__(*args, **kwargs)
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
                _('Subproject nesting is not supported'))
        return self.project

    def clean_child(self):
        child = self.cleaned_data['child']
        if child == self.project:
            raise forms.ValidationError(
                _('A project can not be a subproject of itself'))
        return child

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
            .exclude(pk=self.project.pk))
        return queryset


class ProjectRelationshipForm(SettingsOverrideObject):
    _default_class = ProjectRelationshipBaseForm


class DualCheckboxWidget(forms.CheckboxInput):

    """Checkbox with link to the version's built documentation."""

    def __init__(self, version, attrs=None, check_test=bool):
        super(DualCheckboxWidget, self).__init__(attrs, check_test)
        self.version = version

    def render(self, name, value, attrs=None):
        checkbox = super(DualCheckboxWidget, self).render(name, value, attrs)
        icon = self.render_icon()
        return mark_safe('{}{}'.format(checkbox, icon))

    def render_icon(self):
        context = {
            'MEDIA_URL': settings.MEDIA_URL,
            'built': self.version.built,
            'uploaded': self.version.uploaded,
            'url': self.version.get_absolute_url(),
        }
        return render_to_string('projects/includes/icon_built.html', context)


class BaseVersionsForm(forms.Form):

    """Form for versions page."""

    def save(self):
        versions = self.project.versions.all()
        for version in versions:
            self.save_version(version)
        default_version = self.cleaned_data.get('default-version', None)
        if default_version:
            self.project.default_version = default_version
            self.project.save()

    def save_version(self, version):
        """Save version if there has been a change, trigger a rebuild."""
        new_value = self.cleaned_data.get(
            'version-{}'.format(version.slug),
            None,
        )
        privacy_level = self.cleaned_data.get(
            'privacy-{}'.format(version.slug),
            None,
        )
        if ((new_value is None or new_value == version.active) and
                (privacy_level is None or privacy_level == version.privacy_level)):  # yapf: disable  # noqa
            return
        version.active = new_value
        version.privacy_level = privacy_level
        version.save()
        if version.active and not version.built and not version.uploaded:
            trigger_build(project=self.project, version=version)


def build_versions_form(project):
    """Versions form with a list of versions and version privacy levels."""
    attrs = {
        'project': project,
    }
    versions_qs = project.versions.all()  # Admin page, so show all versions
    active = versions_qs.filter(active=True)
    if active.exists():
        choices = [(version.slug, version.verbose_name) for version in active]
        attrs['default-version'] = forms.ChoiceField(
            label=_('Default Version'),
            choices=choices,
            initial=project.get_default_version(),
        )
    for version in versions_qs:
        field_name = 'version-{}'.format(version.slug)
        privacy_name = 'privacy-{}'.format(version.slug)
        if version.type == TAG:
            label = '{} ({})'.format(
                version.verbose_name,
                version.identifier[:8],
            )
        else:
            label = version.verbose_name
        attrs[field_name] = forms.BooleanField(
            label=label,
            widget=DualCheckboxWidget(version),
            initial=version.active,
            required=False,
        )
        attrs[privacy_name] = forms.ChoiceField(
            # This isn't a real label, but just a slug for the template
            label='privacy',
            choices=constants.PRIVACY_CHOICES,
            initial=version.privacy_level,
        )
    return type(str('VersionsForm'), (BaseVersionsForm,), attrs)


class BaseUploadHTMLForm(forms.Form):
    content = forms.FileField(label=_('Zip file of HTML'))
    overwrite = forms.BooleanField(required=False,
                                   label=_('Overwrite existing HTML?'))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(BaseUploadHTMLForm, self).__init__(*args, **kwargs)

    def clean(self):
        version_slug = self.cleaned_data['version']
        filename = self.request.FILES['content']
        version = self.project.versions.get(slug=version_slug)

        # Validation
        if version.active and not self.cleaned_data.get('overwrite', False):
            raise forms.ValidationError(_('That version is already active!'))
        if not filename.name.endswith('zip'):
            raise forms.ValidationError(_('Must upload a zip file.'))

        return self.cleaned_data


def build_upload_html_form(project):
    """Upload HTML form with list of versions to upload HTML for."""
    attrs = {
        'project': project,
    }
    active = project.versions.public()
    if active.exists():
        choices = []
        choices += [(version.slug, version.verbose_name) for version in active]
        attrs['version'] = forms.ChoiceField(
            label=_('Version of the project you are uploading HTML for'),
            choices=choices,
        )
    return type('UploadHTMLForm', (BaseUploadHTMLForm,), attrs)


class UserForm(forms.Form):

    """Project user association form."""

    user = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(UserForm, self).__init__(*args, **kwargs)

    def clean_user(self):
        name = self.cleaned_data['user']
        user_qs = User.objects.filter(username=name)
        if not user_qs.exists():
            raise forms.ValidationError(
                _('User {name} does not exist').format(name=name))
        self.user = user_qs[0]
        return name

    def save(self):
        self.project.users.add(self.user)
        # Force update of permissions
        assign('view_project', self.user, self.project)
        return self.user


class EmailHookForm(forms.Form):

    """Project email notification form."""

    email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(EmailHookForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        self.email = EmailHook.objects.get_or_create(
            email=self.cleaned_data['email'], project=self.project)[0]
        return self.email

    def save(self):
        self.project.emailhook_notifications.add(self.email)
        return self.project


class WebHookForm(forms.Form):

    """Project webhook form."""

    url = forms.URLField()

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(WebHookForm, self).__init__(*args, **kwargs)

    def clean_url(self):
        self.webhook = WebHook.objects.get_or_create(
            url=self.cleaned_data['url'], project=self.project)[0]
        return self.webhook

    def save(self):
        self.project.webhook_notifications.add(self.webhook)
        return self.project


class TranslationBaseForm(forms.Form):

    """Project translation form."""

    project = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop('parent', None)
        self.user = kwargs.pop('user')
        super(TranslationBaseForm, self).__init__(*args, **kwargs)
        self.fields['project'].choices = self.get_choices()

    def get_choices(self):
        return [
            (project.slug, '{project} ({lang})'.format(
                project=project.slug, lang=project.get_language_display()))
            for project in self.get_translation_queryset().all()
        ]

    def clean_project(self):
        translation_project_slug = self.cleaned_data['project']

        # Ensure parent project isn't already itself a translation
        if self.parent.main_language_project is not None:
            msg = 'Project "{project}" is already a translation'
            raise forms.ValidationError(
                (_(msg).format(project=self.parent.slug))
            )

        project_translation_qs = self.get_translation_queryset().filter(
            slug=translation_project_slug
        )
        if not project_translation_qs.exists():
            msg = 'Project "{project}" does not exist.'
            raise forms.ValidationError(
                (_(msg).format(project=translation_project_slug))
            )
        self.translation = project_translation_qs.first()
        if self.translation.language == self.parent.language:
            msg = (
                'Both projects can not have the same language ({lang}).'
            )
            raise forms.ValidationError(
                _(msg).format(lang=self.parent.get_language_display())
            )
        exists_translation = (
            self.parent.translations
            .filter(language=self.translation.language)
            .exists()
        )
        if exists_translation:
            msg = (
                'This project already has a translation for {lang}.'
            )
            raise forms.ValidationError(
                _(msg).format(lang=self.translation.get_language_display())
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

    def save(self):
        project = self.parent.translations.add(self.translation)
        # Run symlinking and other sync logic to make sure we are in a good
        # state.
        self.parent.save()
        return project


class TranslationForm(SettingsOverrideObject):
    _default_class = TranslationBaseForm


class RedirectForm(forms.ModelForm):

    """Form for project redirects."""

    class Meta(object):
        model = Redirect
        fields = ['redirect_type', 'from_url', 'to_url']

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(RedirectForm, self).__init__(*args, **kwargs)

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

    class Meta(object):
        model = Domain
        exclude = ['machine', 'cname', 'count']  # pylint: disable=modelform-uses-exclude

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(DomainBaseForm, self).__init__(*args, **kwargs)

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
        if canonical and Domain.objects.filter(
                project=self.project, canonical=True
        ).exclude(pk=_id).exists():
            raise forms.ValidationError(
                _('Only 1 Domain can be canonical at a time.'))
        return canonical


class DomainForm(SettingsOverrideObject):
    _default_class = DomainBaseForm


class IntegrationForm(forms.ModelForm):

    """
    Form to add an integration.

    This limits the choices of the integration type to webhook integration types
    """

    project = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta(object):
        model = Integration
        exclude = ['provider_data', 'exchanges']  # pylint: disable=modelform-uses-exclude

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(IntegrationForm, self).__init__(*args, **kwargs)
        # Alter the integration type choices to only provider webhooks
        self.fields['integration_type'].choices = Integration.WEBHOOK_INTEGRATIONS  # yapf: disable  # noqa

    def clean_project(self):
        return self.project

    def save(self, commit=True):
        self.instance = Integration.objects.subclass(self.instance)
        return super(IntegrationForm, self).save(commit)


class ProjectAdvertisingForm(forms.ModelForm):

    """Project promotion opt-out form."""

    class Meta(object):
        model = Project
        fields = ['allow_promos']

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(ProjectAdvertisingForm, self).__init__(*args, **kwargs)


class FeatureForm(forms.ModelForm):

    """
    Project feature form for dynamic admin choices.

    This form converts the CharField into a ChoiceField on display. The
    underlying driver won't attempt to do validation on the choices, and so we
    can dynamically populate this list.
    """

    feature_id = forms.ChoiceField()

    class Meta(object):
        model = Feature
        fields = ['projects', 'feature_id', 'default_true']

    def __init__(self, *args, **kwargs):
        super(FeatureForm, self).__init__(*args, **kwargs)
        self.fields['feature_id'].choices = Feature.FEATURES
