from django import forms

from .models import LEVEL_CHOICES


class CardForm(forms.Form):

    last_4_digits = forms.CharField(
        required=True,
        min_length=4,
        max_length=4,
        widget=forms.HiddenInput()
    )

    stripe_token = forms.CharField(
        required=True,
        widget=forms.HiddenInput()
    )

    level = forms.ChoiceField(
        required=True,
        choices=LEVEL_CHOICES,
    )


class GoldProjectForm(forms.Form):
    project = forms.CharField(
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.projects = kwargs.pop('projects', None)
        super(GoldProjectForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(GoldProjectForm, self).clean()
        if self.projects.count() < self.user.num_supported_projects:
            return cleaned_data
        else:
            self.add_error(None, 'You already have the max number of supported projects.')
