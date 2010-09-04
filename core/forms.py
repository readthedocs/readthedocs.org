from django.db import models
from django import forms
from models import UserProfile

class UserProfileForm (forms.ModelForm):
    class Meta:
        model = UserProfile
        # Don't allow users edit someone else's user page,
        # or to whitelist themselves
        exclude = ('user', 'whitelisted',)
        fields = ('first_name', 'last_name', 'email', 'homepage')

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        # Add email, first and last name from User instance
        # to the form, so the user can edit them
        try:
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
        except User.DoesNotExist:
            pass

    # Include form fields
    email = forms.EmailField(label='Email', required=False, help_text='')
    first_name = forms.CharField(label='First name', required=False, help_text='')
    last_name = forms.CharField(label='Last name', required=False, help_text='')

    def save(self, *args, **kwargs):
        """
        Save the user profile, as well as User data like email and name.
        """
        user = self.instance.user
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        profile = super(UserProfileForm, self).save(*args, **kwargs)
        return profile

