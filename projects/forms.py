import os

from django import forms
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string

from projects import constants
from projects.models import Project, File
from projects.tasks import update_docs


class ProjectForm(forms.ModelForm):
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
        exclude = ('skip', 'user', 'slug', 'repo',
                   'docs_directory', 'status', 'repo_type')

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
        exclude = ('skip', 'theme', 'docs_directory', 'user', 'slug', 'version', 'copyright', 'status')

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
