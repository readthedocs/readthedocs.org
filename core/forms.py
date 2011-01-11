from django.forms import ModelForm
from models import UserProfile

class UserProfileForm (ModelForm):
    class Meta:
        model = UserProfile
        # Don't allow users edit someone else's user page,
        # or to whitelist themselves
        exclude = ('user', 'whitelisted',)
