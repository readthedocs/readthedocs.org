import logging
from haystack.forms import SearchForm
from haystack.query import SearchQuerySet

from django import forms
from django.forms.fields import CharField
from django.utils.translation import ugettext_lazy as _

from .models import UserProfile

log = logging.getLogger(__name__)


class UserProfileForm(forms.ModelForm):
    first_name = CharField(label=_('First name'), required=False)
    last_name = CharField(label=_('Last name'), required=False)

    class Meta:
        model = UserProfile
        # Don't allow users edit someone else's user page,
        fields = ['first_name', 'last_name', 'homepage']

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        try:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
        except:
            pass

    def save(self, *args, **kwargs):
        first_name = self.cleaned_data.pop('first_name', None)
        last_name = self.cleaned_data.pop('last_name', None)
        profile = super(UserProfileForm, self).save(*args, **kwargs)
        if kwargs.get('commit', True):
            user = profile.user
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        return profile


class FacetField(forms.MultipleChoiceField):

    """
    For filtering searches on a facet.

    Has validation for the format of facet values.
    """

    def valid_value(self, value):
        """
        Although this is a choice field, no choices need to be supplied.

        Instead, we just validate that the value is in the correct format
        for facet filtering (facet_name:value)
        """
        if ":" not in value:
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
            field, value = facet.split(":", 1)
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


class SendNotificationForm(forms.Form):

    """Send notification form

    Used for sending a notification to a list of users from admin pages

    Fields:

        _selected_action
            This is required for the admin intermediate form to submit

        source
            Source notification class to use, referenced by name

    :param notification_classes: List of notification sources to display
    :type notification_classes: list
    """

    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)

    source = forms.ChoiceField(label=_('Notification'), choices=[])

    def __init__(self, *args, **kwargs):
        self.notification_classes = kwargs.pop('notification_classes', [])
        super(SendNotificationForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [(cls.name, cls.name) for cls
                                         in self.notification_classes]

    def clean_source(self):
        """Get the source class from the class name"""
        source = self.cleaned_data['source']
        classes = dict((cls.name, cls) for cls in self.notification_classes)
        return classes.get(source, None)
