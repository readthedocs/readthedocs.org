"""HTML forms for sending notifications."""
from __future__ import absolute_import
from django import forms
from django.utils.translation import ugettext_lazy as _


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
