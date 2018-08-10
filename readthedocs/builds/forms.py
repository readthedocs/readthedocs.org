"""Django forms for the builds app."""

from __future__ import absolute_import
from builtins import object
from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

from .constants import STABLE, LATEST
from .models import VersionAlias, Version
from .version_slug import VERSION_SLUG_REGEX
from readthedocs.projects.models import Project
from readthedocs.core.utils import trigger_build


class AliasForm(forms.ModelForm):

    class Meta(object):
        model = VersionAlias
        fields = (
            'project',
            'from_slug',
            'to_slug',
            'largest',
        )

    def __init__(self, instance=None, *args, **kwargs):  # noqa
        super(AliasForm, self).__init__(instance=instance, *args, **kwargs)
        if instance:
            self.fields['project'].queryset = (Project.objects
                                               .filter(pk=instance.project.pk))


class VersionForm(forms.ModelForm):

    slug = forms.CharField(
        max_length=255,
        validators=[RegexValidator('^{pattern}$'.format(pattern=VERSION_SLUG_REGEX))],
        help_text=_("Used in this version's URL"),
    )

    class Meta(object):
        model = Version
        fields = ['slug', 'active', 'privacy_level', 'tags']

    def __init__(self, *args, **kwargs):
        super(VersionForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.slug in (LATEST, STABLE):
            self.fields['slug'].disabled = True
            self.fields['slug'].help_text += ' - it is read only for "{}"'.format(
                self.instance.slug)

    def save(self, commit=True):
        obj = super(VersionForm, self).save(commit=commit)
        if obj.active and not obj.built and not obj.uploaded:
            trigger_build(project=obj.project, version=obj)
        return obj
