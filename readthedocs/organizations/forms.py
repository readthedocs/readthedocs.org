"""Organization forms."""
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.core.validators import EmailValidator
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from readthedocs.core.history import SimpleHistoryModelForm
from readthedocs.core.permissions import AdminPermission
from readthedocs.core.utils import slugify
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.invitations.models import Invitation
from readthedocs.organizations.constants import ADMIN_ACCESS, READ_ONLY_ACCESS
from readthedocs.organizations.models import (
    Organization,
    OrganizationOwner,
    Team,
    TeamMember,
)


class OrganizationForm(SimpleHistoryModelForm):

    """
    Base organization form.

    :param user: User instance, responsible for ownership of Organization
    :type user: django.contrib.auth.models.User
    """

    # We use the organization slug + project name
    # to form the final project slug.
    # A valid project slug is 63 chars long.
    name = forms.CharField(max_length=32)

    class Meta:
        model = Organization
        fields = ['name', 'email', 'description', 'url']
        labels = {
            'name': _('Organization Name'),
            'email': _('Billing Email'),
        }

    # Don't use a URLField as a widget, the validation is too strict on FF
    url = forms.URLField(
        widget=forms.TextInput(attrs={'placeholder': 'http://'}),
        label=_('Site URL'),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        try:
            self.user = kwargs.pop('user')
        except KeyError:
            raise TypeError(
                'OrganizationForm expects a `user` keyword argument',
            )
        super().__init__(*args, **kwargs)

    def clean_name(self):
        """Raise exception on duplicate organization slug."""
        name = self.cleaned_data['name']

        # Skip slug validation on already created organizations.
        if self.instance.pk:
            return name

        potential_slug = slugify(name)
        if not potential_slug:
            raise forms.ValidationError(_('Invalid organization name: no slug generated'))
        if Organization.objects.filter(slug=potential_slug).exists():
            raise forms.ValidationError(
                _('Organization %(name)s already exists'),
                params={'name': name},
            )
        return name


class OrganizationSignupFormBase(OrganizationForm):

    """
    Simple organization creation form.

    This trims down the number of inputs required to create a new organization.
    This is used on the initial organization signup, to keep signup terse.

    :param user: User instance, responsible for ownership of Organization
    :type user: django.contrib.auth.models.User
    """

    class Meta:
        model = Organization
        fields = ['name', 'email']
        labels = {
            'name': _('Organization Name'),
            'email': _('Billing Email'),
        }

    url = None

    @staticmethod
    def _create_default_teams(organization):
        organization.teams.create(name='Admins', access=ADMIN_ACCESS)
        organization.teams.create(name='Read Only', access=READ_ONLY_ACCESS)

    def save(self, commit=True):
        org = super().save(commit)

        # If not committing, we can't save M2M fields
        if not commit:
            return org

        # Add default teams
        OrganizationOwner.objects.create(
            owner=self.user,
            organization=org,
        )
        self._create_default_teams(org)
        return org


class OrganizationSignupForm(SettingsOverrideObject):

    _default_class = OrganizationSignupFormBase


class OrganizationOwnerForm(forms.Form):

    """Form to manage owners of the organization."""

    username_or_email = forms.CharField(label=_("Email address or username"))

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean_username_or_email(self):
        """Lookup owner by username or email, detect collisions with existing owners."""
        username = self.cleaned_data["username_or_email"]
        user = User.objects.filter(
            Q(username=username)
            | Q(emailaddress__verified=True, emailaddress__email=username)
        ).first()
        if user is None:
            raise forms.ValidationError(
                _('User %(username)s does not exist'),
                params={'username': username},
            )
        if self.organization.owners.filter(pk=user.pk).exists():
            raise forms.ValidationError(
                _('User %(username)s is already an owner'),
                params={'username': username},
            )
        return user

    def save(self):
        invitation, _ = Invitation.objects.invite(
            from_user=self.request.user,
            to_user=self.cleaned_data["username_or_email"],
            obj=self.organization,
        )
        return invitation


class OrganizationTeamBasicFormBase(SimpleHistoryModelForm):

    """Form to manage teams."""

    class Meta:
        model = Team
        fields = ['name', 'access', 'organization']
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': _('Team already exists'),
            },
        }

    organization = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)

    def clean_organization(self):
        """Hard code organization return on form."""
        return self.organization


class OrganizationTeamBasicForm(SettingsOverrideObject):

    _default_class = OrganizationTeamBasicFormBase


class OrganizationTeamProjectForm(forms.ModelForm):

    """Form to manage access of teams to projects."""

    class Meta:
        model = Team
        fields = ['projects']

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.fields['projects'] = forms.ModelMultipleChoiceField(
            queryset=self.organization.projects,
            widget=forms.CheckboxSelectMultiple,
        )


class OrganizationTeamMemberForm(forms.Form):

    """Form to manage all members of the organization."""

    username_or_email = forms.CharField(label=_("Email address or username"))

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop("team", None)
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean_username_or_email(self):
        """
        Validate the user to invite to.

        We search for an existing user by username or email,
        if none is found, we try to validate if the input is an email,
        in that case we send an invitation to that email.
        """
        username = self.cleaned_data["username_or_email"]
        user = User.objects.filter(
            Q(username=username)
            | Q(emailaddress__verified=True, emailaddress__email=username)
        ).first()

        if user:
            return self.validate_member_user(user)

        # If it's a valid email,
        # then try sending an invitation to it.
        try:
            validator = EmailValidator(code='lookup not an email')
            validator(username)
            return username
        except ValidationError as error:
            if error.code != 'lookup not an email':
                raise

        raise forms.ValidationError(
            _("User %(username)s does not exist"), params={"username": username}
        )

    def validate_member_user(self, member):
        """Verify duplicate team member doesn't already exists."""
        if TeamMember.objects.filter(team=self.team, member=member).exists():
            raise forms.ValidationError(_('User is already a team member'),)
        return member

    def save(self):
        """Create an invitation only if the user isn't already a member."""
        user = self.cleaned_data["username_or_email"]
        if isinstance(user, User):
            # If the user is already a member or the organization
            # don't create an invitation.
            if (
                AdminPermission.members(self.team.organization)
                .filter(pk=user.pk)
                .exists()
            ):
                member = self.team.organization.add_member(user, self.team)
                member.send_add_notification(self.request)
                return user
            invitation, _ = Invitation.objects.invite(
                from_user=self.request.user,
                to_user=user,
                obj=self.team,
            )
            return invitation
        invitation, _ = Invitation.objects.invite(
            from_user=self.request.user,
            to_email=user,
            obj=self.team,
        )
        return invitation
