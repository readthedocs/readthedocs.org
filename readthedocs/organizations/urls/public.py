"""URLs that don't require login."""

from django.urls import path
from django.urls import re_path

from readthedocs.organizations.views import public as views


urlpatterns = [
    path(
        "verify-email/",
        views.OrganizationTemplateView.as_view(template_name="organizations/verify_email.html"),
        name="organization_verify_email",
    ),
    re_path(
        r"^(?P<slug>[\w.-]+)/$",
        views.DetailOrganization.as_view(),
        name="organization_detail",
    ),
    # Teams
    re_path(
        r"^(?P<slug>[\w.-]+)/teams/(?P<team>[\w.-]+)/$",
        views.ListOrganizationTeamMembers.as_view(),
        name="organization_team_detail",
    ),
    re_path(
        r"^(?P<slug>[\w.-]+)/teams/$",
        views.ListOrganizationTeams.as_view(),
        name="organization_team_list",
    ),
    re_path(
        r"^invite/(?P<hash>[\w.-]+)/redeem/$",
        views.RedirectRedeemTeamInvitation.as_view(),
        name="organization_invite_redeem",
    ),
    # Members
    re_path(
        r"^(?P<slug>[\w.-]+)/members/$",
        views.ListOrganizationMembers.as_view(),
        name="organization_members",
    ),
]
