from django.urls import path

from readthedocs.invitations.views import RedeemInvitation
from readthedocs.invitations.views import RevokeInvitation


urlpatterns = [
    path("<invitation_token>/", RedeemInvitation.as_view(), name="invitations_redeem"),
    path(
        "<int:invitation_pk>/revoke/",
        RevokeInvitation.as_view(),
        name="invitations_revoke",
    ),
]
