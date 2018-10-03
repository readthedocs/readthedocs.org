"""Django forms for the builds app."""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from builtins import object
from django import forms
from django.utils.translation import ugettext_lazy as _

from readthedocs.builds.models import Version, VersionAlias
from readthedocs.core.utils import trigger_build
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import Project


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

    class Meta(object):
        model = Version
        fields = ['active', 'privacy_level', 'tags']

    def clean_active(self):
        active = self.cleaned_data['active']
        if self._is_default_version and not active:
            msg = (
                '{} is the default version of the project, '
                'it should be active.'
            )
            raise forms.ValidationError(
                _(msg.format(self.instance.verbose_name))
            )
        return active

    def clean_privacy_level(self):
        privacy_level = self.cleaned_data['privacy_level']
        if self._is_default_version and privacy_level != PUBLIC:
            msg = (
                '{} is the default version of the project, '
                'it should be public.'
            )
            raise forms.ValidationError(
                _(msg.format(self.instance.verbose_name))
            )
        return privacy_level

    def _is_default_version(self):
        project = self.instance.project
        return project.default_version == self.instance.slug

    def save(self, commit=True):
        obj = super(VersionForm, self).save(commit=commit)
        if obj.active and not obj.built and not obj.uploaded:
            trigger_build(project=obj.project, version=obj)
        return obj
