from django import forms
from django.conf import settings
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string

from builds.models import VersionAlias
from projects.models import Project, File


class AliasForm(forms.ModelForm):
    class Meta:
        model = VersionAlias
