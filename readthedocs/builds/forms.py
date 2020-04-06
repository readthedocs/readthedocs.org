"""Django forms for the builds app."""

import re
import textwrap

from django import forms
from django.utils.translation import ugettext_lazy as _

from readthedocs.builds.constants import (
    ALL_VERSIONS,
    BRANCH,
    BRANCH_TEXT,
    TAG,
    TAG_TEXT,
)
from readthedocs.builds.models import RegexAutomationRule, Version
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

    match_arg = forms.CharField(
        label='Custom match',
        help_text=_(textwrap.dedent(
            """
            A regular expression to match the version.
            <a href="https://docs.readthedocs.io/page/automation-rules.html#user-defined-matches">
              Check the documentation for valid patterns.
            </a>
            """
        )),
        required=False,
    )

    class Meta:
        model = RegexAutomationRule
        fields = [
            'description',
            'predefined_match_arg',
            'match_arg',
            'version_type',
            'action',
        ]
        # Don't pollute the UI with help texts
        help_texts = {
            'version_type': '',
            'action': '',
        }
        labels = {
            'predefined_match_arg': 'Match',
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)

        # Only list supported types
        self.fields['version_type'].choices = [
            (None, '-' * 9),
            (BRANCH, BRANCH_TEXT),
            (TAG, TAG_TEXT),
        ]

        if not self.instance.pk:
            self.initial['predefined_match_arg'] = ALL_VERSIONS
        # Allow users to start from the pattern of the predefined match
        # if they want to use a custom one.
        if self.instance.pk and self.instance.predefined_match_arg:
            self.initial['match_arg'] = self.instance.get_match_arg()

    def clean_match_arg(self):
        """Check that a custom match was given if a predefined match wasn't used."""
        match_arg = self.cleaned_data['match_arg']
        predefined_match = self.cleaned_data['predefined_match_arg']
        if predefined_match:
            match_arg = ''
        if not predefined_match and not match_arg:
            raise forms.ValidationError(
                _('Custom match should not be empty.'),
            )

        try:
            re.compile(match_arg)
        except Exception:
            raise forms.ValidationError(
                _('Invalid Python regular expression.'),
            )
        return match_arg

    def save(self, commit=True):
        if self.instance.pk:
            rule = super().save(commit=commit)
        else:
            rule = RegexAutomationRule.objects.add_rule(
                project=self.project,
                description=self.cleaned_data['description'],
                match_arg=self.cleaned_data['match_arg'],
                predefined_match_arg=self.cleaned_data['predefined_match_arg'],
                version_type=self.cleaned_data['version_type'],
                action=self.cleaned_data['action'],
            )
        if not rule.description:
            rule.description = rule.get_description()
            rule.save()
        return rule
