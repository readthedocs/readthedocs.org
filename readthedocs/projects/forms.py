from django import forms
from django.conf import settings
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from projects import constants
from projects.models import Project, File
from projects.tasks import update_docs


class ProjectForm(forms.ModelForm):
    required_css_class = "required"

    def clean_name(self):
        name = self.cleaned_data.get('name', '')
        if not self.instance.pk:
            potential_slug = slugify(name)
            if Project.objects.filter(slug=potential_slug).count():
                raise forms.ValidationError('A project with that name exists already!')

        return name


class CreateProjectForm(ProjectForm):
    class Meta:
        model = Project
        exclude = ('skip', 'user', 'slug', 'repo', 'featured',
                   'docs_directory', 'status', 'repo_type', 'default_version',)

    def save(self, *args, **kwargs):
        created = self.instance.pk is None

        # save the project
        project = super(CreateProjectForm, self).save(*args, **kwargs)

        if created:
            # create a couple sample files
            for i, (sample_file, template) in enumerate(constants.SAMPLE_FILES):
                file = File.objects.create(
                    project=project,
                    heading=sample_file,
                    content=render_to_string(template, {'project': project}),
                    ordering=i+1,
                )
                file.create_revision(old_content='', comment='')

        # kick off the celery job
        update_docs.delay(pk=project.pk)

        return project


class ImportProjectForm(ProjectForm):
    repo = forms.CharField(required=True,
        help_text='URL for your code (hg or git). Ex. http://github.com/ericholscher/django-kong.git')
    class Meta:
        model = Project
        fields = ('name', 'repo', 'repo_type', 'description', 'project_url', 'tags', 'default_branch')

    def clean_repo(self):
        repo = self.cleaned_data.get('repo', '').strip()
        if '&&' in repo or '|' in repo:
            raise forms.ValidationError('Invalid character in repo name')
        elif '@' in repo:
            raise forms.ValidationError('It looks like you entered a private repo - please use the public (http:// or git://) clone url')
        return repo

    def save(self, *args, **kwargs):
        # save the project
        project = super(ImportProjectForm, self).save(*args, **kwargs)

        # kick off the celery job
        update_docs.delay(pk=project.pk)

        return project


class FileForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={'class': 'editor'}),
        help_text='<small><a href="http://sphinx.pocoo.org/rest.html">reStructuredText Primer</a></small>')
    revision_comment = forms.CharField(max_length=255, required=False)

    class Meta:
        model = File
        exclude = ('project', 'slug', 'status')

    def __init__(self, instance=None, *args, **kwargs):
        file_qs = instance.project.files.all()
        if instance.pk:
            file_qs = file_qs.exclude(pk=instance.pk)
        self.base_fields['parent'].queryset = file_qs
        super(FileForm, self).__init__(instance=instance, *args, **kwargs)

    def save(self, *args, **kwargs):
        # grab the old content before saving
        old_content = self.initial.get('content', '')

        # save the file object
        file_obj = super(FileForm, self).save(*args, **kwargs)

        # create a new revision from the old content -> new
        file_obj.create_revision(
            old_content,
            self.cleaned_data.get('revision_comment', '')
        )

        update_docs.delay(file_obj.project.pk)

        return file_obj


class FileRevisionForm(forms.Form):
    revision = forms.ModelChoiceField(queryset=None)

    def __init__(self, file, *args, **kwargs):
        revision_qs = file.revisions.exclude(pk=file.current_revision.pk)
        self.base_fields['revision'].queryset = revision_qs
        super(FileRevisionForm, self).__init__(*args, **kwargs)


class DualCheckboxWidget(forms.CheckboxInput):
    def __init__(self, version, attrs=None, check_test=bool):
        super(DualCheckboxWidget, self).__init__(attrs, check_test)
        self.version = version

    def render(self, name, value, attrs=None):
        checkbox = super(DualCheckboxWidget, self).render(name, value, attrs)
        icon = self.render_icon()
        return u'%s%s' % (checkbox, icon)

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
        if new_value is None or new_value == version.active:
            return
        version.active = new_value
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
        choices = [('latest', 'latest')]
        choices += [(version.slug, version.verbose_name) for version in active]
        attrs['default-version'] = forms.ChoiceField(
            label="Choose the default version for this project",
            choices=choices,
            initial=project.get_default_version(),
        )
    for version in versions_qs:
        field_name = 'version-%s' % version.slug
        attrs[field_name] = forms.BooleanField(
            label=version.verbose_name,
            widget=DualCheckboxWidget(version),
            initial=version.active,
            required=False,
        )
    return type('VersionsForm', (BaseVersionsForm,), attrs)


class BaseUploadHTMLForm(forms.Form):
    content = forms.FileField(label="Zip file of HTML")
    overwrite = forms.BooleanField(required=False, label="Overwrite existing HTML?")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(BaseUploadHTMLForm, self).__init__(*args, **kwargs)

    def clean(self):
        version_slug = self.cleaned_data['version']
        file = self.request.FILES['content']
        version = self.project.versions.get(slug=version_slug)

        #Validation
        if version.active and not self.cleaned_data.get('overwrite', False):
            raise forms.ValidationError("That version is already active!")
        if not file.name.endswith('zip'):
            raise forms.ValidationError("Must upload a zip file.")

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
            label="Version of the project you are uploading HTML for",
            choices=choices,
        )
    return type('UploadHTMLForm', (BaseUploadHTMLForm,), attrs)
