"""Invitation views."""

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DeleteView, DetailView

from readthedocs.core.mixins import PrivateViewMixin
from readthedocs.core.permissions import AdminPermission
from readthedocs.invitations.models import Invitation
from readthedocs.organizations.models import Organization, Team


class RevokeInvitation(PrivateViewMixin, UserPassesTestMixin, DeleteView):

    model = Invitation
    pk_url_kwarg = "invitation_pk"
    http_method_names = ["post"]

    def test_func(self):
        invitation = self.get_object()
        return invitation.can_revoke_invitation(self.request.user)

    def get_success_url(self):
        invitation = self.get_object()
        return invitation.get_origin_url()


class RedeemInvitation(DetailView):

    """
    Allow the user to accept or decline an invitation.

    The invitation is deleted once it has been accepted or declined.
    """

    model = Invitation
    slug_url_kwarg = "invitation_token"
    slug_field = "token"
    context_object_name = "invitation"

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        invitation = self.get_object()
        url = reverse("homepage")
        if request.POST.get("accept"):
            if invitation.expired:
                return HttpResponseBadRequest("Invitation has expired.")

            # If the invitation is attached to an email,
            # and the current user isn't logged-in we
            # redeem the invitation after the user has signed-up.
            if not request.user.is_authenticated and invitation.to_email:
                return self.redeem_at_sign_up(invitation)
            invitation.redeem(request.user)
            url = invitation.get_success_url()
        invitation.delete()
        return HttpResponseRedirect(url)

    def redeem_at_sign_up(self, invitation):
        """
        Mark the invitation to be redeemed after the user has signed-up.

        We redirect the user to the sign-up page,
        the invitation will be automatically redeemed
        after the user has signed-up (readthedocs.core.adapters.AccountAdapter.save_user).
        """
        self.request.session.update(
            {
                "invitation:pk": invitation.pk,
                # Auto-verify EmailAddress via django-allauth.
                "account_verified_email": invitation.to_email,
            }
        )
        url = reverse("account_signup")

        obj = invitation.object
        organization = None
        if isinstance(obj, Team):
            organization = obj.organization
        elif isinstance(obj, Organization):
            organization = obj
        if organization and AdminPermission.has_sso_enabled(organization):
            url += f"?organization={organization.slug}"
        return HttpResponseRedirect(url)
