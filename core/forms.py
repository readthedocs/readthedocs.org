from django.forms import ModelForm
from django.forms.fields import CharField
from models import UserProfile
from django.contrib.auth.models import User

class UserProfileForm(ModelForm):
    first_name = CharField(label='First name', required=False)
    last_name = CharField(label='Last name', required=False)

    class Meta:
        model = UserProfile
        # Don't allow users edit someone else's user page,
        # or to whitelist themselves
        exclude = ('user', 'whitelisted',)

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
