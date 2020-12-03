"""Django forms for the builds app."""

import itertools
import re
import textwrap

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Fieldset, Layout
from django import forms
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from readthedocs.builds.constants import (
    ALL_VERSIONS,
    BRANCH,
    BRANCH_TEXT,
    EXTERNAL,
    EXTERNAL_TEXT,
    TAG,
    TAG_TEXT,
)
from readthedocs.builds.models import (
    RegexAutomationRule,
    Version,
    VersionAutomationRule,
)
from readthedocs.core.mixins import HideProtectedLevelMixin
from readthedocs.core.utils import trigger_build


class VersionForm(HideProtectedLevelMixin, forms.ModelForm):

    class Meta:
        model = Version
        states_fields = ['active', 'hidden']
        privacy_fields = ['privacy_level']
        fields = (
            *states_fields,
            *privacy_fields,
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        field_sets = [
            Fieldset(
                _('States'),
                HTML(render_to_string('projects/project_version_states_help_text.html')),
                *self.Meta.states_fields,
            ),
        ]

        if settings.ALLOW_PRIVATE_REPOS:
            field_sets.append(
                Fieldset(
                    _('Privacy'),
                    *self.Meta.privacy_fields,
                )
            )
        else:
            self.fields.pop('privacy_level')

        field_sets.append(
            HTML(render_to_string(
                'projects/project_version_submit.html',
                context={'version': self.instance},
            ))
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(*field_sets)

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
              Check the documentation
            </a>
            for valid patterns.
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
            'action_arg',
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
            (EXTERNAL, EXTERNAL_TEXT),
        ]

        # Remove privacy actions not available in community
        if not settings.ALLOW_PRIVATE_REPOS:
            invalid_actions = {
                VersionAutomationRule.MAKE_VERSION_PUBLIC_ACTION,
                VersionAutomationRule.MAKE_VERSION_PRIVATE_ACTION,
            }
            action_choices = self.fields['action'].choices
            self.fields['action'].choices = [
                action
                for action in action_choices
                if action[0] not in invalid_actions
            ]

        if not self.instance.pk:
            self.initial['predefined_match_arg'] = ALL_VERSIONS
        # Allow users to start from the pattern of the predefined match
        # if they want to use a custom one.
        if self.instance.pk and self.instance.predefined_match_arg:
            self.initial['match_arg'] = self.instance.get_match_arg()

    def clean_action(self):
        """Check the action is allowed for the type of version."""
        action = self.cleaned_data['action']
        version_type = self.cleaned_data['version_type']
        internal_allowed_actions = set(
            itertools.chain(
                VersionAutomationRule.allowed_actions_on_create.keys(),
                VersionAutomationRule.allowed_actions_on_delete.keys(),
            )
        )
        allowed_actions = {
            BRANCH: internal_allowed_actions,
            TAG: internal_allowed_actions,
            EXTERNAL: set(VersionAutomationRule.allowed_actions_on_external_versions.keys()),
        }
        if action not in allowed_actions.get(version_type, []):
            raise forms.ValidationError(
                _('Invalid action for this version type.'),
            )
        return action

    def clean_action_arg(self):
        """
        Validate the action argument.

        Currently only external versions accept this argument,
        and it's the pattern to match the base_branch.
        """
        action_arg = self.cleaned_data['action_arg']
        version_type = self.cleaned_data['version_type']
        if version_type == EXTERNAL:
            if not action_arg:
                action_arg = '.*'
            try:
                re.compile(action_arg)
                return action_arg
            except Exception:
                raise forms.ValidationError(
                    _('Invalid Python regular expression.'),
                )
        return ''

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
                action_arg=self.cleaned_data['action_arg'],
            )
        if not rule.description:
            rule.description = rule.get_description()
            rule.save()
        return rule
