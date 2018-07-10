# -*- coding: utf-8 -*-
"""Forms used for SSH key management."""
from __future__ import division, print_function, unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from .keys import is_valid_private_key


class SSHKeyFileUploadForm(forms.Form):

    """Form to upload a private SSH key from user's computer."""

    private_key = forms.FileField(
        help_text=_('Upload an additional private key file to use while cloning or installing dependencies'),  # noqa
    )

    def clean_private_key(self):
        """Check the ``private_key`` uploaded is a valid key."""
        data = self.cleaned_data['private_key'].read().decode('utf8')
        if not is_valid_private_key(data):
            raise forms.ValidationError(
                _("We couldn't load the private key file. Please, be sure it's valid."),
            )
        return data
