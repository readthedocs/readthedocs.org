"""Organization forms."""

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.core.validators import EmailValidator
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from readthedocs.core.utils import slugify
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.organizations.constants import ADMIN_ACCESS, READ_ONLY_ACCESS
from readthedocs.organizations.models import (
    Organization,
    OrganizationOwner,
    Team,
    TeamInvite,
    TeamMember,
)


class OrganizationForm(forms.ModelForm):

    """
    Base organization form.

    :param user: User instance, responsible for ownership of Organization
    :type user: django.contrib.auth.models.User
    """

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
        """Raise exception on duplicate organization."""
        name = self.cleaned_data['name']
        if self.instance and self.instance.name and name == self.instance.name:
            return name
        if Organization.objects.filter(slug=slugify(name)).exists():
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

        # If not commiting, we can't save M2M fields
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


class OrganizationOwnerForm(forms.ModelForm):

    """Form to manage owners of the organization."""

    class Meta:
        model = OrganizationOwner
        fields = ['owner']

    owner = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)

    def clean_owner(self):
        """Lookup owner by username, detect collisions with existing owners."""
        username = self.cleaned_data['owner']
        owner = User.objects.filter(username=username).first()
        if owner is None:
            raise forms.ValidationError(
                _('User %(username)s does not exist'),
                params={'username': username},
            )
        if self.organization.owners.filter(username=username).exists():
            raise forms.ValidationError(
                _('User %(username)s is already an owner'),
                params={'username': username},
            )
        return owner


class OrganizationTeamBasicFormBase(forms.ModelForm):

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


class OrganizationTeamMemberForm(forms.ModelForm):

    """Form to manage all members of the organization."""

    class Meta:
        model = TeamMember
        fields = []

    member = forms.CharField(label=_('Email address or username'))

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop('team', None)
        super().__init__(*args, **kwargs)

    def clean_member(self):
        """
        Get member or invite from field.

        If input is email, try to look up a user using that email address, if
        that doesn't return a user, then consider this a fresh invite.  If the
        input is not an email, treat it as a user name and lookup a user.  Throw
        a validation error if the username doesn't not exist.

        Return a User instance, or a TeamInvite instance, depending on the above
        conditions.
        """
        lookup = self.cleaned_data['member']

        # Look up user emails first, see if a verified user can be added
        try:
            validator = EmailValidator(code='lookup not an email')
            validator(lookup)

            member = (
                User.objects.filter(
                    emailaddress__verified=True,
                    emailaddress__email=lookup,
                    is_active=True,
                ).first()
            )
            if member is not None:
                return self.validate_member_user(member)

            invite = TeamInvite(
                organization=self.team.organization,
                team=self.team,
                email=lookup,
            )

            return self.validate_member_invite(invite)
        except ValidationError as error:
            if error.code != 'lookup not an email':
                raise

        # Not an email, attempt username lookup
        try:
            member = User.objects.get(username=lookup, is_active=True)
            return self.validate_member_user(member)
        except User.DoesNotExist:
            raise forms.ValidationError('User not found')

    def validate_member_user(self, member):
        """Verify duplicate team member doesn't already exists."""
        if TeamMember.objects.filter(team=self.team, member=member).exists():
            raise forms.ValidationError(_('User is already a team member'),)
        return member

    def validate_member_invite(self, invite):
        """
        Verify team member and team invite don't already exist.

        Query searches for duplicate :py:cls:`TeamMember` instances, and also
        for existing :py:cls:`TeamInvite` instances, sharing the team and email
        address of the given ``invite``

        :param invite: :py:cls:`TeamInvite` instance
        """
        queryset = TeamMember.objects.filter(
            Q(
                team=self.team,
                invite__team=self.team,
                invite__email=invite.email,
            ),
        )
        if queryset.exists():
            raise forms.ValidationError(
                _('An invitation was already sent to this email'),
            )
        return invite

    def clean(self):
        """
        Treat an invite email as an invite in the member field.

        This will drop an invite object as the invite field if the member field
        returned a TeamInvite instance
        """
        data = super().clean()

        if not self.is_valid():
            return data

        self.instance.team = self.team
        member = data['member']

        if isinstance(member, User):
            self.instance.invite = None
            self.instance.member = member
        elif isinstance(member, TeamInvite):
            member.save()
            self.instance.member = None
            self.instance.invite = member

        self._validate_unique = True
        return data
