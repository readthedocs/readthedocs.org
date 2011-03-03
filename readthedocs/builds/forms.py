from django import forms
from django.conf import settings
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string

from builds.models import VersionAlias
from projects.models import Project, File


class AliasForm(forms.ModelForm):
    class Meta:
        model = VersionAlias

    def __init__(self, instance=None, *args, **kwargs):
        super(AliasForm, self).__init__(instance=instance, *args, **kwargs)
        if instance:
            self.fields['project'].queryset = Project.objects.filter(pk=instance.project.pk)
