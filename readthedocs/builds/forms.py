"""Django forms for the builds app."""

from __future__ import absolute_import
from builtins import object
from django import forms
from django.utils.translation import ugettext_lazy as _, ugettext

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

    slug = forms.RegexField(
        '^{pattern}$'.format(pattern=VERSION_SLUG_REGEX),
        max_length=255,
        help_text=_("Used in this version's URL"),
    )

    class Meta(object):
        model = Version
        fields = ['slug', 'active', 'privacy_level', 'tags']

    def __init__(self, *args, **kwargs):
        super(VersionForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.slug in (LATEST, STABLE):
            self.fields['slug'].disabled = True
            self.fields['slug'].help_text += ugettext(' - read only for special versions')

    def clean_slug(self):
        slug = self.cleaned_data['slug']

        version = self.instance
        if version:
            if Version.objects.filter(project=version.project, slug=slug).exclude(
                    pk=version.pk).exists():
                raise forms.ValidationError(
                    _('There is already a version for this project with that slug'),
                )

        return slug

    def save(self, commit=True):
        obj = super(VersionForm, self).save(commit=commit)
        if obj.active and not obj.built and not obj.uploaded:
            trigger_build(project=obj.project, version=obj)
        return obj
