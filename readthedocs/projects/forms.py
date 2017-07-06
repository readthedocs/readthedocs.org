"""Project forms"""

from __future__ import absolute_import

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
from readthedocs.core.utils import trigger_build, slugify
from readthedocs.integrations.models import Integration
from readthedocs.oauth.models import RemoteRepository
from readthedocs.projects import constants
from readthedocs.projects.exceptions import ProjectSpamError
from readthedocs.projects.models import (
    Project, ProjectRelationship, EmailHook, WebHook, Domain)
from readthedocs.redirects.models import Redirect


class ProjectForm(forms.ModelForm):

    """Project form

    :param user: If provided, add this user as a project user on save
    """

    required_css_class = "required"

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

    """Mixin to trigger build on form save

    This should be replaced with signals instead of calling trigger_build
    explicitly.
    """

    def save(self, commit=True):
        """Trigger build on commit save"""
        project = super(ProjectTriggerBuildMixin, self).save(commit)
        if commit:
            trigger_build(project=project)
        return project


class ProjectBackendForm(forms.Form):

    """Get the import backend"""

    backend = forms.CharField()


class ProjectBasicsForm(ProjectForm):

    """Form for basic project fields"""

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
                label=_('Edit advanced project options')
            )
        self.fields['repo'].widget.attrs['placeholder'] = self.placehold_repo()
        self.fields['repo'].widget.attrs['required'] = True

    def save(self, commit=True):
        """Add remote repository relationship to the project instance"""
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
                    _('Invalid project name, a project already exists with that name'))
        return name

    def clean_repo(self):
        repo = self.cleaned_data.get('repo', '').strip()
        pvt_repos = getattr(settings, 'ALLOW_PRIVATE_REPOS', False)
        if '&&' in repo or '|' in repo:
            raise forms.ValidationError(_(u'Invalid character in repo name'))
        elif '@' in repo and not pvt_repos:
            raise forms.ValidationError(
                _(u'It looks like you entered a private repo - please use the '
                  u'public (http:// or git://) clone url'))
        return repo

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
            raise forms.ValidationError(_(u'Repository invalid'))

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

    """Additional project information form"""

    class Meta(object):
        model = Project
        fields = (
            'description',
            'documentation_type',
            'language',
            'programming_language',
            'project_url',
            'tags',
        )

    description = forms.CharField(
        validators=[ClassifierValidator(raises=ProjectSpamError)],
        required=False,
        widget=forms.Textarea
    )


class ProjectAdvancedForm(ProjectTriggerBuildMixin, ProjectForm):

    """Advanced project option form"""

    python_interpreter = forms.ChoiceField(
        choices=constants.PYTHON_CHOICES, initial='python',
        help_text=_("(Beta) The Python interpreter used to create the virtual "
                    "environment."))

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
                  'conf.py in it.'))
        return filename


class UpdateProjectForm(ProjectTriggerBuildMixin, ProjectBasicsForm,
                        ProjectExtraForm):

    class Meta(object):
        model = Project
        fields = (
            # Basics
            'name', 'repo', 'repo_type',
            # Extra
            # 'allow_comments',
            # 'comment_moderation',
            'description',
            'documentation_type',
            'language', 'programming_language',
            'project_url',
            'tags',
        )


class ProjectRelationshipForm(forms.ModelForm):

    """Form to add/update project relationships"""

    parent = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta(object):
        model = ProjectRelationship
        exclude = []

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project')
        self.user = kwargs.pop('user')
        super(ProjectRelationshipForm, self).__init__(*args, **kwargs)
        # Don't display the update form with an editable child, as it will be
        # filtered out from the queryset anyways.
        if hasattr(self, 'instance') and self.instance.pk is not None:
            self.fields['child'].disabled = True
        else:
            self.fields['child'].queryset = self.get_subproject_queryset()

    def clean_parent(self):
        if self.project.superprojects.exists():
            # This validation error is mostly for testing, users shouldn't see
            # this in normal circumstances
            raise forms.ValidationError(_("Subproject nesting is not supported"))
        return self.project

    def get_subproject_queryset(self):
        """Return scrubbed subproject choice queryset

        This removes projects that are either already a subproject of another
        project, or are a superproject, as neither case is supported.
        """
        queryset = (Project.objects.for_admin_user(self.user)
                    .exclude(subprojects__isnull=False)
                    .exclude(superprojects__isnull=False))
        return queryset


class DualCheckboxWidget(forms.CheckboxInput):

    """Checkbox with link to the version's built documentation"""

    def __init__(self, version, attrs=None, check_test=bool):
        super(DualCheckboxWidget, self).__init__(attrs, check_test)
        self.version = version

    def render(self, name, value, attrs=None):
        checkbox = super(DualCheckboxWidget, self).render(name, value, attrs)
        icon = self.render_icon()
        return mark_safe(u'%s%s' % (checkbox, icon))

    def render_icon(self):
        context = {
            'MEDIA_URL': settings.MEDIA_URL,
            'built': self.version.built,
            'uploaded': self.version.uploaded,
            'url': self.version.get_absolute_url()
        }
        return render_to_string('projects/includes/icon_built.html', context)


class BaseVersionsForm(forms.Form):

    """Form for versions page"""

    def save(self):
        versions = self.project.versions.all()
        for version in versions:
            self.save_version(version)
        default_version = self.cleaned_data.get('default-version', None)
        if default_version:
            self.project.default_version = default_version
            self.project.save()

    def save_version(self, version):
        """Save version if there has been a change, trigger a rebuild"""
        new_value = self.cleaned_data.get('version-%s' % version.slug, None)
        privacy_level = self.cleaned_data.get('privacy-%s' % version.slug,
                                              None)
        if ((new_value is None or
             new_value == version.active) and (
                 privacy_level is None or
                 privacy_level == version.privacy_level)):
            return
        version.active = new_value
        version.privacy_level = privacy_level
        version.save()
        if version.active and not version.built and not version.uploaded:
            trigger_build(project=self.project, version=version)


def build_versions_form(project):
    """Versions form with a list of versions and version privacy levels"""
    attrs = {
        'project': project,
    }
    versions_qs = project.versions.all()  # Admin page, so show all versions
    active = versions_qs.filter(active=True)
    if active.exists():
        choices = [(version.slug, version.verbose_name) for version in active]
        attrs['default-version'] = forms.ChoiceField(
            label=_("Default Version"),
            choices=choices,
            initial=project.get_default_version(),
        )
    for version in versions_qs:
        field_name = 'version-%s' % version.slug
        privacy_name = 'privacy-%s' % version.slug
        if version.type == TAG:
            label = "%s (%s)" % (version.verbose_name, version.identifier[:8])
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
            label="privacy",
            choices=constants.PRIVACY_CHOICES,
            initial=version.privacy_level,
        )
    return type('VersionsForm', (BaseVersionsForm,), attrs)


class BaseUploadHTMLForm(forms.Form):
    content = forms.FileField(label=_("Zip file of HTML"))
    overwrite = forms.BooleanField(required=False,
                                   label=_("Overwrite existing HTML?"))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(BaseUploadHTMLForm, self).__init__(*args, **kwargs)

    def clean(self):
        version_slug = self.cleaned_data['version']
        filename = self.request.FILES['content']
        version = self.project.versions.get(slug=version_slug)

        # Validation
        if version.active and not self.cleaned_data.get('overwrite', False):
            raise forms.ValidationError(_("That version is already active!"))
        if not filename.name.endswith('zip'):
            raise forms.ValidationError(_("Must upload a zip file."))

        return self.cleaned_data


def build_upload_html_form(project):
    """Upload HTML form with list of versions to upload HTML for"""
    attrs = {
        'project': project,
    }
    active = project.versions.public()
    if active.exists():
        choices = []
        choices += [(version.slug, version.verbose_name) for version in active]
        attrs['version'] = forms.ChoiceField(
            label=_("Version of the project you are uploading HTML for"),
            choices=choices,
        )
    return type('UploadHTMLForm', (BaseUploadHTMLForm,), attrs)


class UserForm(forms.Form):

    """Project user association form"""

    user = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(UserForm, self).__init__(*args, **kwargs)

    def clean_user(self):
        name = self.cleaned_data['user']
        user_qs = User.objects.filter(username=name)
        if not user_qs.exists():
            raise forms.ValidationError(_("User %(name)s does not exist") %
                                        {'name': name})
        self.user = user_qs[0]
        return name

    def save(self):
        self.project.users.add(self.user)
        # Force update of permissions
        assign('view_project', self.user, self.project)
        return self.user


class EmailHookForm(forms.Form):

    """Project email notification form"""

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

    """Project webhook form"""

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


class TranslationForm(forms.Form):

    """Project translation form"""

    project = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop('parent', None)
        super(TranslationForm, self).__init__(*args, **kwargs)

    def clean_project(self):
        translation_name = self.cleaned_data['project']
        translation_qs = Project.objects.filter(slug=translation_name)
        if not translation_qs.exists():
            raise forms.ValidationError((_("Project %(name)s does not exist")
                                         % {'name': translation_name}))
        if translation_qs.first().language == self.parent.language:
            err = ("Both projects have a language of `%s`. "
                   "Please choose one with another language" % self.parent.language)
            raise forms.ValidationError(_(err))

        self.translation = translation_qs.first()
        return translation_name

    def save(self):
        project = self.parent.translations.add(self.translation)
        # Run symlinking and other sync logic to make sure we are in a good state.
        self.parent.save()
        return project


class RedirectForm(forms.ModelForm):

    """Form for project redirects"""

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


class DomainForm(forms.ModelForm):

    """Form to configure a custom domain name for a project."""

    project = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta(object):
        model = Domain
        exclude = ['machine', 'cname', 'count', 'https']

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(DomainForm, self).__init__(*args, **kwargs)

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
        if canonical and Domain.objects.filter(
            project=self.project, canonical=True
        ).exclude(domain=self.cleaned_data['domain']).exists():
            raise forms.ValidationError(_(u'Only 1 Domain can be canonical at a time.'))
        return canonical


class IntegrationForm(forms.ModelForm):

    """Form to add an integration

    This limits the choices of the integration type to webhook integration types
    """

    project = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta(object):
        model = Integration
        exclude = ['provider_data', 'exchanges']

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(IntegrationForm, self).__init__(*args, **kwargs)
        # Alter the integration type choices to only provider webhooks
        self.fields['integration_type'].choices = Integration.WEBHOOK_INTEGRATIONS

    def clean_project(self):
        return self.project

    def save(self, commit=True):
        self.instance = Integration.objects.subclass(self.instance)
        return super(IntegrationForm, self).save(commit)


class ProjectAdvertisingForm(forms.ModelForm):

    """Project promotion opt-out form"""

    class Meta(object):
        model = Project
        fields = ['allow_promos']

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(ProjectAdvertisingForm, self).__init__(*args, **kwargs)
