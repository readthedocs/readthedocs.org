from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from projects import constants
from projects.models import Project, EmailHook, WebHook
from projects.tasks import update_docs


class ProjectForm(forms.ModelForm):
    required_css_class = "required"

    def clean_name(self):
        name = self.cleaned_data.get('name', '')
        if not self.instance.pk:
            potential_slug = slugify(name)
            if Project.objects.filter(slug=potential_slug).count():
                raise forms.ValidationError(_('A project with that name exists already!'))

        return name


class ImportProjectForm(ProjectForm):
    repo = forms.CharField(required=True,
            help_text=_(u'URL for your code (hg or git). Ex. http://github.com/ericholscher/django-kong.git'))

    python_interpreter = forms.ChoiceField(
        choices=constants.PYTHON_CHOICES, initial='python',
        help_text=_("(Beta) The Python interpreter used to create the virtual environment."))
    
    class Meta:
        model = Project
        fields = (
            # Important
            'name', 'repo', 'repo_type', 'description',
            # Not as important
            'project_url', 'tags', 'default_branch', 'default_version', 'conf_py_file',
            # Privacy
            'privacy_level', 'version_privacy_level',
            # Python specific
            'use_virtualenv', 'use_system_packages', 'requirements_file',
            #'python_interpreter',
            # Fringe
            'analytics_code', 'documentation_type', 'tags'
        )

    def clean_repo(self):
        repo = self.cleaned_data.get('repo', '').strip()
        if '&&' in repo or '|' in repo:
            raise forms.ValidationError(_(u'Invalid character in repo name'))
        elif '@' in repo and not getattr(settings, 'ALLOW_PRIVATE_REPOS', False):
            raise forms.ValidationError(_(u'It looks like you entered a private repo - please use the public (http:// or git://) clone url'))
        return repo

    def clean_conf_py_file(self):
        file = self.cleaned_data.get('conf_py_file', '').strip()
        if file and not 'conf.py' in file:
            raise forms.ValidationError(_('Your configuration file is invalid, make sure it contains conf.py in it.'))
        return file

    def save(self, *args, **kwargs):
        # save the project
        project = super(ImportProjectForm, self).save(*args, **kwargs)

        # kick off the celery job
        update_docs.delay(pk=project.pk)

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
        versions = self.project.versions.all()
        for version in versions:
            self.save_version(version)
        default_version = self.cleaned_data.get('default-version', None)
        if default_version:
            self.project.default_version = default_version
            self.project.save()

    def save_version(self, version):
        new_value = self.cleaned_data.get('version-%s' % version.slug, None)
        privacy_level = self.cleaned_data.get('privacy-%s' % version.slug, None)
        if (new_value is None or new_value == version.active) and (privacy_level is None or privacy_level == version.privacy_level):
            return
        version.active = new_value
        version.privacy_level = privacy_level
        version.save()
        if version.active and not version.built and not version.uploaded:
            update_docs.delay(self.project.pk, record=True, version_pk=version.pk)


def build_versions_form(project):
    attrs = {
        'project': project,
    }
    versions_qs = project.versions.all()
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
        attrs[field_name] = forms.BooleanField(
            label=version.verbose_name,
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
    overwrite = forms.BooleanField(required=False, label=_("Overwrite existing HTML?"))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(BaseUploadHTMLForm, self).__init__(*args, **kwargs)

    def clean(self):
        version_slug = self.cleaned_data['version']
        file = self.request.FILES['content']
        version = self.project.versions.get(slug=version_slug)

        #Validation
        if version.active and not self.cleaned_data.get('overwrite', False):
            raise forms.ValidationError(_("That version is already active!"))
        if not file.name.endswith('zip'):
            raise forms.ValidationError(_("Must upload a zip file."))

        return self.cleaned_data


def build_upload_html_form(project):
    attrs = {
        'project': project,
    }
    active = project.versions.all()
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
        subproject_qs = Project.objects.filter(name=subproject_name)
        if not subproject_qs.exists():
            raise forms.ValidationError(_("Project %(name)s does not exist") % {'name': subproject_name})
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
        project = self.project.users.add(self.user)
        return self.user

class EmailHookForm(forms.Form):
    email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(EmailHookForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        self.email = EmailHook.objects.get_or_create(email=self.cleaned_data['email'], project=self.project)[0]
        return self.email

    def save(self):
        project = self.project.emailhook_notifications.add(self.email)
        return self.project
