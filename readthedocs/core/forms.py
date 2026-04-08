"""Forms for core app."""

from dataclasses import dataclass

import structlog
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import NON_FIELD_ERRORS
from django.forms.fields import CharField
from django.utils.translation import gettext_lazy as _

from readthedocs.core.history import set_change_reason

from .models import UserProfile


log = structlog.get_logger(__name__)


class UserProfileForm(forms.ModelForm):
    first_name = CharField(label=_("First name"), required=False, max_length=30)
    last_name = CharField(label=_("Last name"), required=False, max_length=30)

    class Meta:
        model = UserProfile
        # Don't allow users edit someone else's user page
        fields = ["first_name", "last_name", "homepage"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
        except AttributeError:
            pass

    def save(self, commit=True):
        first_name = self.cleaned_data.pop("first_name", None)
        last_name = self.cleaned_data.pop("last_name", None)
        profile = super().save(commit=commit)
        if commit:
            user = profile.user
            user.first_name = first_name
            user.last_name = last_name
            # SimpleHistoryModelForm isn't used here
            # because the model of this form is `UserProfile`, not `User`.
            set_change_reason(user, self.get_change_reason())
            user.save()
        return profile

    def get_change_reason(self):
        klass = self.__class__.__name__
        return f"origin=form class={klass}"


class UserDeleteForm(forms.ModelForm):
    username = CharField(
        label=_("Username"),
        help_text=_("Please type your username to confirm."),
    )

    class Meta:
        model = User
        fields = ["username"]

    def clean_username(self):
        data = self.cleaned_data["username"]

        if self.instance.username != data:
            raise forms.ValidationError(_("Username does not match!"))

        return data


class UserAdvertisingForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["allow_ads"]


class PrevalidatedForm(forms.Form):
    """
    Form class that allows raising form errors before form submission.

    The base ``Form`` does not support validation errors while the form is
    unbound (does not have ``data`` defined). There are cases in our UI where we
    want to show errors and/or disabled the form before the user has a chance to
    interact with the form -- for example, when a feature is unavailable or
    disabled for the user or organization.

    This provides the ``clean_prevalidation`` method, which acts much like the
    ``clean`` method. Any validation errors raised in this method surface as non
    field errors in the UI.
    """

    def __init__(self, *args, **kwargs):
        self._prevalidation_errors = None
        super().__init__(*args, **kwargs)

    def is_valid(self):
        # This differs from ``Form`` in that we don't care if the form is bound
        return not self.errors

    @property
    def is_disabled(self):
        return self._prevalidation_errors is not None

    def full_clean(self):
        """
        Extend full clean method with prevalidation cleaning.

        Where :py:method:`forms.Form.full_clean` bails out if there is no bound
        data on the form, this method always checks prevalidation no matter
        what. This gives errors before submission and after submission.
        """
        # Always call prevalidation, ``full_clean`` bails if the form is unbound
        self._clean_prevalidation()

        super().full_clean()

        # ``full_clean`` sets ``self._errors``, so we prepend prevalidation
        # errors after calling the parent ``full_clean``
        if self._prevalidation_errors is not None:
            non_field_errors = []
            non_field_errors.extend(self._prevalidation_errors)
            non_field_errors.extend(self._errors.get(NON_FIELD_ERRORS, []))
            self._errors[NON_FIELD_ERRORS] = non_field_errors

    def _clean_prevalidation(self):
        """
        Catch validation errors raised by the subclassed ``clean_validation()``.

        This wraps ``clean_prevalidation()`` using the same pattern that
        :py:method:`form.Form._clean_form` wraps :py:method:`clean`. Validation
        errors raised in the subclass method will be eventually added to the
        form error list but :py:method:`full_clean`.
        """
        try:
            self.clean_prevalidation()
        except forms.ValidationError as validation_error:
            self._prevalidation_errors = [validation_error]

    def clean_prevalidation(self):
        raise NotImplementedError()


class RichValidationError(forms.ValidationError):
    """
    Show non-field form errors as titled messages.

    This uses more of the FUI message specification to give a really clear,
    concise error message to the user. Without this class, non-field validation
    errors show at the top of the form with a title "Error", which isn't as
    helpful to users as something like "Connected service required".

    :param header str: Message header/title text
    :param message_class str: FUI CSS class to use on the message -- "info",
        etc. Default: "error".
    """

    def __init__(self, message, code=None, params=None, header=None, message_class=None):
        super().__init__(message, code, params)
        self.header = header
        self.message_class = message_class


@dataclass
class RichChoice:
    """
    Data class for rich content dropdowns.

    Instead of just value and text, :py:class:`RichSelect` displays multiple
    attributes in each item content display. Choices can be passed as an array,
    however with the default :py:class:`django.forms.fields.ChoiceField`
    you should still pass in a tuple of ``(value, RichChoice(...))`` as the
    tuple values are used in field validation:

        choices = [
            RichChoice(name="Foo", value="foo", ...),
            RichChoice(name="Bar", value="bar", ...),
        ]
        field = forms.ChoiceField(
            ...,
            widget=RichSelect(),
            choices=[(choice.value, choice) for choice in choices],
        )
    """

    #: Choice verbose text display
    text: str
    #: Choice input value
    value: str
    #: Right floated content for dropdown item
    description: str
    #: Optional image URL for item
    image_url: str = None
    #: Optional image alt text
    image_alt: str = None
    #: Error string to display next to text
    error: str = None
    #: Is choice disabled?
    disabled: bool = False


class RichSelect(forms.Select):
    """
    Rich content dropdown field widget type used for complex content.

    This class is mostly used for special casing in Crispy form templates, it
    doesn't do anything special. This widget type requires use of the
    :py:class:`RichChoice` data class. Usage might look something comparable to:

        choice = RichChoice(...)
        field = forms.ChoiceField(
            ...,
            widget=RichSelect(),
            choices=[(choice.value, choice)]
        )
    """


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
        if ":" not in value:
            return False
        return True


class SupportForm(forms.Form):
    name = forms.CharField()
    email = forms.EmailField()
    body = forms.CharField(
        label=_("Explanation of the issue"),
        help_text=_("Please provide as much detail as possible."),
        widget=forms.Textarea,
    )
    url = forms.URLField(
        label=_("URL"),
        help_text=_("Is there a specific page this happened?"),
        required=False,
    )
    attachment = forms.FileField(
        label=_("Screenshot or additional file"),
        help_text=_("Anything else that would help us solve this issue?"),
        required=False,
    )
    severity_level = forms.ChoiceField(
        choices=(
            ("low", _("Low")),
            ("medium", _("Medium")),
            ("high", _("High")),
        ),
        help_text=_("Please rate the severity of this event."),
        required=False,
    )
    subject = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, user):
        super().__init__()

        self.fields["name"].initial = user.get_full_name
        self.fields["email"].initial = user.email

        if settings.ALLOW_PRIVATE_REPOS:
            self.fields["subject"].initial = "Commercial Support Request"
        else:
            self.fields["subject"].initial = "Community Support Request"

            if not (user.gold.exists() or user.goldonce.exists()):
                self.fields["severity_level"].disabled = True
                self.fields["severity_level"].widget.attrs["readonly"] = True
                self.fields["severity_level"].help_text = _(
                    "This option is only enabled for Gold users."
                )
