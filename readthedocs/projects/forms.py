from random import choice

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from guardian.shortcuts import assign

from core.utils import trigger_build
from redirects.models import Redirect
from projects import constants
from projects.models import Project, EmailHook, WebHook


class ProjectForm(forms.ModelForm):
    required_css_class = "required"

    def clean_name(self):
        name = self.cleaned_data.get('name', '')
        if not self.instance.pk:
            potential_slug = slugify(name)
            if Project.objects.filter(slug=potential_slug).count():
                raise forms.ValidationError(
                    _('A project with that name exists already!')
                )

        return name

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

    def placehold_canonical_url(self):
        return choice([
            'http://docs.fabfile.org',
            'http://example.readthedocs.org',
        ])


class ImportProjectForm(ProjectForm):

    class Meta:
        model = Project
        fields = (
            # Important
            'name', 'repo', 'repo_type',
            # Not as important
            'description',
            'documentation_type',
            'language', 'programming_language',
            'project_url',
            'canonical_url',
            'tags',
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ImportProjectForm, self).__init__(*args, **kwargs)
        placeholders = {
            'repo': self.placehold_repo(),
            'canonical_url': self.placehold_canonical_url(),
        }
        for (field, value) in placeholders.items():
            self.fields[field].widget.attrs['placeholder'] = value

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

    def save(self, *args, **kwargs):
        # save the project
        project = super(ImportProjectForm, self).save(*args, **kwargs)

        if kwargs.get('commit', True):
            # kick off the celery job
            trigger_build(project=project)

        return project


class AdvancedProjectForm(ProjectForm):
    python_interpreter = forms.ChoiceField(
        choices=constants.PYTHON_CHOICES, initial='python',
        help_text=_("(Beta) The Python interpreter used to create the virtual "
                    "environment."))

    class Meta:
        model = Project
        fields = (
            # Standard build edits
            'use_virtualenv',
            'requirements_file',
            'single_version',
            'conf_py_file',
            'default_branch',
            'default_version',
            # Privacy
            'privacy_level',
            # 'version_privacy_level',
            # Python specific
            'use_system_packages',
            'python_interpreter',
            # Fringe
            'analytics_code',
            # Version Support
            'num_major', 'num_minor', 'num_point',
        )

    def clean_conf_py_file(self):
        file = self.cleaned_data.get('conf_py_file', '').strip()
        if file and not 'conf.py' in file:
            raise forms.ValidationError(
                _('Your configuration file is invalid, make sure it contains '
                  'conf.py in it.'))
        return file

    def save(self, *args, **kwargs):
        # save the project
        project = super(AdvancedProjectForm, self).save(*args, **kwargs)

        # kick off the celery job
        trigger_build(project=project)

        return project


class DualCheckboxWidget(forms.CheckboxInput):

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

    def save(self):
        versions = self.project.versions.public()
        for version in versions:
            self.save_version(version)
        default_version = self.cleaned_data.get('default-version', None)
        if default_version:
            self.project.default_version = default_version
            self.project.save()

    def save_version(self, version):
        new_value = self.cleaned_data.get('version-%s' % version.slug, None)
        privacy_level = self.cleaned_data.get('privacy-%s' % version.slug,
                                              None)
        if ((new_value is None or
             new_value == version.active)
            and (privacy_level is None or
                 privacy_level == version.privacy_level)):
            return
        version.active = new_value
        version.privacy_level = privacy_level
        version.save()
        if version.active and not version.built and not version.uploaded:
            trigger_build(project=self.project, version=version)


def build_versions_form(project):
    attrs = {
        'project': project,
    }
    versions_qs = project.versions.all() # Admin page, so show all versions
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
        if version.type == 'tag':
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
        file = self.request.FILES['content']
        version = self.project.versions.get(slug=version_slug)

        # Validation
        if version.active and not self.cleaned_data.get('overwrite', False):
            raise forms.ValidationError(_("That version is already active!"))
        if not file.name.endswith('zip'):
            raise forms.ValidationError(_("Must upload a zip file."))

        return self.cleaned_data


def build_upload_html_form(project):
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


class SubprojectForm(forms.Form):
    subproject = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop('parent', None)
        super(SubprojectForm, self).__init__(*args, **kwargs)

    def clean_subproject(self):
        subproject_name = self.cleaned_data['subproject']
        subproject_qs = Project.objects.filter(slug=subproject_name)
        if not subproject_qs.exists():
            raise forms.ValidationError((_("Project %(name)s does not exist")
                                         % {'name': subproject_name}))
        self.subproject = subproject_qs[0]
        return subproject_name

    def save(self):
        relationship = self.parent.add_subproject(self.subproject)
        return relationship


class UserForm(forms.Form):
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
    project = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop('parent', None)
        super(TranslationForm, self).__init__(*args, **kwargs)

    def clean_project(self):
        subproject_name = self.cleaned_data['project']
        subproject_qs = Project.objects.filter(slug=subproject_name)
        if not subproject_qs.exists():
            raise forms.ValidationError((_("Project %(name)s does not exist")
                                         % {'name': subproject_name}))
        self.subproject = subproject_qs[0]
        return subproject_name

    def save(self):
        project = self.parent.translations.add(self.subproject)
        return project


class RedirectForm(forms.ModelForm):

    class Meta:
        model = Redirect
        fields = ['redirect_type', 'from_url', 'to_url']

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(RedirectForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        redirect = Redirect.objects.create(
            project=self.project,
            redirect_type=self.cleaned_data['redirect_type'],
            from_url=self.cleaned_data['from_url'],
            to_url=self.cleaned_data['to_url'],
        )
        return redirect

