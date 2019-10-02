"""Django forms for the builds app."""

from django import forms
from django.utils.translation import ugettext_lazy as _

from readthedocs.builds.models import Version
from readthedocs.builds.version_slug import (
    VERSION_OK_CHARS,
    VERSION_TEST_PATTERN,
    VersionSlugify,
)
from readthedocs.core.mixins import HideProtectedLevelMixin
from readthedocs.core.utils import trigger_build


class VersionForm(HideProtectedLevelMixin, forms.ModelForm):

    class Meta:
        model = Version
        fields = ['slug', 'active', 'privacy_level']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].help_text = _('Warning: changing the slug will break existing URLs')

        if self.instance.pk and self.instance.machine:
            self.fields['slug'].disabled = True

    def clean_slug(self):
        slugifier = VersionSlugify(
            ok_chars=VERSION_OK_CHARS,
            test_pattern=VERSION_TEST_PATTERN,
        )
        original_slug = self.cleaned_data.get('slug')

        slug = slugifier.slugify(original_slug, check_pattern=False)
        if not slugifier.is_valid(slug):
            msg = _('The slug "{slug}" is not valid.')
            raise forms.ValidationError(msg.format(slug=original_slug))

        duplicated = (
            Version.objects
            .filter(project=self.instance.project, slug=slug)
            .exclude(pk=self.instance.pk)
            .exists()
        )
        if duplicated:
            msg = _('The slug "{slug}" is already in use.')
            raise forms.ValidationError(msg.format(slug=slug))
        return slug

    def clean_active(self):
        active = self.cleaned_data['active']
        if self._is_default_version() and not active:
            msg = _(
                '{version} is the default version of the project, '
                'it should be active.',
            )
            raise forms.ValidationError(
                msg.format(version=self.instance.verbose_name),
            )
        return active

    def _is_default_version(self):
        project = self.instance.project
        return project.default_version == self.instance.slug

    def save(self, commit=True):
        obj = super().save(commit=commit)
        if obj.active and not obj.built and not obj.uploaded:
            trigger_build(project=obj.project, version=obj)
        return obj
