"""Community site-wide form overrides."""

import structlog
from allauth.account.forms import SignupForm
from core.models import UserProfile
from django import forms

log = structlog.get_logger(__name__)  # noqa


class SignupFormWithNewsletter(SignupForm):

    """Custom signup form that includes a checkbox to subscribe to a newsletter."""

    receive_newsletter = forms.BooleanField(
        required=False,
        label=(
            "Subscribe to our newsletter to get product updates."
        ),
    )

    field_order = [
        'email',
        'username',
        'password1',
        'password2',
        'receive_newsletter',
    ]

    def save(self, request):
        user = super().save(request)

        receive_newsletter = self.cleaned_data.get("receive_newsletter")
        profile = UserProfile.objects.get_or_create(user=user)
        profile.mailing_list = receive_newsletter
        profile.save()


        return user
