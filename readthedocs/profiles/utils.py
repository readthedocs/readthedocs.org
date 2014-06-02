"""
Utility functions for retrieving and generating forms for the
site-specific user profile model specified in the
``AUTH_PROFILE_MODULE`` setting.

"""

from django import forms
from django.conf import settings
from django.db.models import get_model

from django.contrib.auth.models import SiteProfileNotAvailable


def get_profile_model():
    """
    Return the model class for the currently-active user profile
    model, as defined by the ``AUTH_PROFILE_MODULE`` setting. If that
    setting is missing, raise
    ``django.contrib.auth.models.SiteProfileNotAvailable``.
    
    """
    if (not hasattr(settings, 'AUTH_PROFILE_MODULE')) or \
           (not settings.AUTH_PROFILE_MODULE):
        raise SiteProfileNotAvailable
    profile_mod = get_model(*settings.AUTH_PROFILE_MODULE.split('.'))
    if profile_mod is None:
        raise SiteProfileNotAvailable
    return profile_mod


def get_profile_form():
    """
    Return a form class (a subclass of the default ``ModelForm``)
    suitable for creating/editing instances of the site-specific user
    profile model, as defined by the ``AUTH_PROFILE_MODULE``
    setting. If that setting is missing, raise
    ``django.contrib.auth.models.SiteProfileNotAvailable``.
    
    """
    profile_mod = get_profile_model()
    class _ProfileForm(forms.ModelForm):
        class Meta:
            model = profile_mod
            exclude = ('user',) # User will be filled in by the view.
    return _ProfileForm
