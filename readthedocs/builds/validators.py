"""Validators for the builds app."""

from django import forms
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class VersionValidator:
    """
    Shared validation for ``Version`` fields.

    Forms enter through ``clean_<field>`` and API serializers through
    ``validate_<field>``. Both extract the data they need and delegate to a
    private ``_validate_<field>`` method that holds the shared logic and raises
    the error class given to it (``forms.ValidationError`` or
    ``serializers.ValidationError``).
    """

    def _validate_active(self, active, version, error_class):
        """The default version of a project must remain active."""
        if version and not active and version.project.default_version == version.slug:
            raise error_class(
                _("{version} is the default version of the project, it should be active.").format(
                    version=version.verbose_name,
                ),
            )
        return active

    def clean_active(self):
        return self._validate_active(
            self.cleaned_data["active"],
            version=self.instance,
            error_class=forms.ValidationError,
        )

    def validate_active(self, active):
        return self._validate_active(
            active,
            version=self.instance,
            error_class=serializers.ValidationError,
        )
