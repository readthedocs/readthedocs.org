"""Django forms for the builds app."""

from django import forms
from django.utils.translation import ugettext_lazy as _

from readthedocs.builds.constants import BRANCH, BRANCH_TEXT, TAG, TAG_TEXT
from readthedocs.builds.models import (
    RegexAutomationRule,
    Version,
)
from readthedocs.core.mixins import HideProtectedLevelMixin
from readthedocs.core.utils import trigger_build


class VersionForm(HideProtectedLevelMixin, forms.ModelForm):

    class Meta:
        model = Version
        fields = ['active', 'privacy_level']

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


class RegexAutomationRuleForm(forms.ModelForm):

    match = forms.ChoiceField(
        label='Rule',
        choices=[
            (r'.*', 'All versions'),
            (r'^v?(\d+\.)(\d+\.)(\d)(-.+)?$', 'Semver versions'),
            (None, 'Custom'),
        ],
        required=False,
    )

    match_arg = forms.CharField(
        label='Custom rule',
        help_text=_('A Python regular expression'),
        required=False,
    )

    class Meta:
        model = RegexAutomationRule
        fields = ['description', 'match', 'match_arg', 'version_type', 'action']

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)

        self.fields['version_type'].choices = [
            (None, '-' * 9),
            (BRANCH, BRANCH_TEXT),
            (TAG, TAG_TEXT),
        ]

    def clean_match_arg(self):
        match_arg = self.cleaned_data['match_arg']
        match = self.cleaned_data['match']
        if match is not None:
            match_arg = match
        if not match_arg:
            raise forms.ValidationError(
                _('Custom match should not be empty.'),
            )
        return match_arg

    def clean_description(self):
        description = self.cleaned_data['description']
        if not description:
            description = self.instance.get_description()
        return description

    def save(self, commit=True):
        if self.instance.pk:
            return super().save(commit=commit)
        return RegexAutomationRule.objects.append_rule(
            project=self.project,
            description=self.cleaned_data['description'],
            match_arg=self.cleaned_data['match_arg'],
            version_type=self.cleaned_data['version_type'],
            action=self.cleaned_data['action'],
        )
