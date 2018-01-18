# -*- coding: utf-8 -*-
"""Forms for core app."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import logging
from builtins import object

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.forms.fields import CharField
from django.utils.translation import ugettext_lazy as _
from haystack.forms import SearchForm
from haystack.query import SearchQuerySet

from .models import UserProfile

log = logging.getLogger(__name__)


class UserProfileForm(forms.ModelForm):
    first_name = CharField(label=_('First name'), required=False)
    last_name = CharField(label=_('Last name'), required=False)

    class Meta(object):
        model = UserProfile
        # Don't allow users edit someone else's user page
        fields = ['first_name', 'last_name', 'homepage']
        if settings.USE_PROMOS:
            fields.append('allow_ads')

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        try:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
        except AttributeError:
            pass

    def save(self, commit=True):
        first_name = self.cleaned_data.pop('first_name', None)
        last_name = self.cleaned_data.pop('last_name', None)
        profile = super(UserProfileForm, self).save(commit=commit)
        if commit:
            user = profile.user
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        return profile


class UserDeleteForm(forms.ModelForm):
    username = CharField(
        label=_('Username'),
        help_text=_('Please type your username to confirm.'),
    )

    class Meta(object):
        model = User
        fields = ['username']

    def clean_username(self):
        data = self.cleaned_data['username']

        if self.instance.username != data:
            raise forms.ValidationError(_('Username does not match!'))

        return data


class FacetField(forms.MultipleChoiceField):

    """
    For filtering searches on a facet.

    Has validation for the format of facet values.
    """

    def valid_value(self, value):
        """
        Although this is a choice field, no choices need to be supplied.

        Instead, we just validate that the value is in the correct format for
        facet filtering (facet_name:value)
        """
        if ':' not in value:
            return False
        return True


class FacetedSearchForm(SearchForm):

    """
    Supports fetching faceted results with a corresponding query.

    `facets`
        A list of facet names for which to get facet counts
    `models`
        Limit the search to one or more models
    """

    selected_facets = FacetField(required=False)

    def __init__(self, *args, **kwargs):
        facets = kwargs.pop('facets', [])
        models = kwargs.pop('models', [])
        super(FacetedSearchForm, self).__init__(*args, **kwargs)

        for facet in facets:
            self.searchqueryset = self.searchqueryset.facet(facet)
        if models:
            self.searchqueryset = self.searchqueryset.models(*models)

    def clean_selected_facets(self):
        facets = self.cleaned_data['selected_facets']
        cleaned_facets = []
        clean = SearchQuerySet().query.clean
        for facet in facets:
            field, value = facet.split(':', 1)
            if not value:  # Ignore empty values
                continue
            value = clean(value)
            cleaned_facets.append(u'%s:"%s"' % (field, value))
        return cleaned_facets

    def search(self):
        sqs = super(FacetedSearchForm, self).search()
        for facet in self.cleaned_data['selected_facets']:
            sqs = sqs.narrow(facet)
        self.searchqueryset = sqs
        return sqs
