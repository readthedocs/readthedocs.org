"""Django forms for the builds app."""

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Fieldset
from crispy_forms.layout import Layout
from django import forms
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from readthedocs.builds.models import Version


class VersionForm(forms.ModelForm):
    project = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Version
        states_fields = ["active", "hidden"]
        privacy_fields = ["privacy_level"]
        fields = (
            "project",
            "slug",
            *states_fields,
            *privacy_fields,
        )

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project")
        super().__init__(*args, **kwargs)

        field_sets = [
            Fieldset(
                _("States"),
                HTML(render_to_string("projects/project_version_states_help_text.html")),
                *self.Meta.states_fields,
            ),
        ]

        if settings.ALLOW_PRIVATE_REPOS:
            field_sets.append(
                Fieldset(
                    _("Privacy"),
                    *self.Meta.privacy_fields,
                )
            )
        else:
            self.fields.pop("privacy_level")

        field_sets.append(
            HTML(
                render_to_string(
                    "projects/project_version_submit.html",
                    context={"version": self.instance},
                )
            )
        )

        # Don't allow changing the slug of machine created versions
        # (stable/latest), as we rely on the slug to identify them.
        if self.instance and self.instance.machine:
            self.fields["slug"].disabled = True

        self.helper = FormHelper()
        self.helper.layout = Layout(*field_sets)
        # We need to know if the version was active before the update.
        # We use this value in the save method.
        self._was_active = self.instance.active if self.instance else False
        self._previous_slug = self.instance.slug if self.instance else None

    def clean_active(self):
        active = self.cleaned_data["active"]
        if self._is_default_version() and not active:
            msg = _(
                "{version} is the default version of the project, it should be active.",
            )
            raise forms.ValidationError(
                msg.format(version=self.instance.verbose_name),
            )
        return active

    def _is_default_version(self):
        project = self.instance.project
        return project.default_version == self.instance.slug

    def clean_project(self):
        return self.project

    def save(self, commit=True):
        obj = super().save(commit=commit)
        obj.post_save(was_active=self._was_active, previous_slug=self._previous_slug)
        return obj
