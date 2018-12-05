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

from readthedocs.builds.models import Version
from readthedocs.core.utils import trigger_build


class VersionForm(forms.ModelForm):

    class Meta(object):
        model = Version
        fields = ['active', 'privacy_level', 'tags']

    def clean_active(self):
        active = self.cleaned_data['active']
        if self._is_default_version() and not active:
            msg = _(
                '{version} is the default version of the project, '
                'it should be active.'
            )
            raise forms.ValidationError(
                msg.format(version=self.instance.verbose_name)
            )
        return active

    def _is_default_version(self):
        project = self.instance.project
        return project.default_version == self.instance.slug

    def save(self, commit=True):
        obj = super(VersionForm, self).save(commit=commit)
        if obj.active and not obj.built and not obj.uploaded:
            trigger_build(project=obj.project, version=obj)
        return obj
