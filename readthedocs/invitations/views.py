"""Invitation views."""

import structlog
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DeleteView
from django.views.generic import DetailView

from readthedocs.audit.models import AuditLog
from readthedocs.core.mixins import PrivateViewMixin
from readthedocs.core.permissions import AdminPermission
from readthedocs.invitations.models import Invitation
from readthedocs.organizations.models import Organization
from readthedocs.organizations.models import Team
from readthedocs.organizations.models import TeamInvite


log = structlog.get_logger(__name__)


class RevokeInvitation(PrivateViewMixin, UserPassesTestMixin, DeleteView):
    """
    Revoke invitation view.

    An invitation is revoked by simple deleting it.
    """

    model = Invitation
    pk_url_kwarg = "invitation_pk"
    http_method_names = ["post"]

    def form_valid(self, form):
        invitation = self.get_object()
        invitation.create_audit_log(
            action=AuditLog.INVITATION_REVOKED,
            request=self.request,
            user=self.request.user,
        )
        return super().form_valid(form)

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invitation = self.get_object()
        from_user = invitation.from_user
        context["requestor_name"] = from_user.get_full_name() or from_user.username
        context["requestor_url"] = reverse("profiles_profile_detail", args=[from_user.username])
        context["target_name"] = invitation.object_name
        context["target_type"] = invitation.object._meta.verbose_name
        return context

    def post(self, request, *args, **kwargs):
        """
        Accept or decline an invitation.

        To accept an invitation, the ``accept`` parameter must be
        in the request, otherwise we decline the invitation.
        """
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
            invitation.redeem(request.user, request=request)
            url = invitation.get_success_url()
        else:
            log.info(
                "Invitation declined",
                invitation_pk=invitation.pk,
                object_type=invitation.object_type,
                object_name=invitation.object_name,
                object_pk=invitation.object.pk,
            )
            invitation.create_audit_log(
                action=AuditLog.INVITATION_DECLINED,
                request=request,
                user=invitation.to_user,
            )
        invitation.delete()
        return HttpResponseRedirect(url)

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset=queryset)
        except Http404:
            # TODO: remove after the migration has completed.
            # To avoid blocking users from redeeming invitations while
            # the data migration is running, we migrate those on the fly.
            team_invite = get_object_or_404(
                TeamInvite.objects.filter(teammember__member__isnull=True),
                hash=self.kwargs[self.slug_url_kwarg],
            )
            invitation, _ = team_invite.migrate()
            team_invite.delete()
            return invitation

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
