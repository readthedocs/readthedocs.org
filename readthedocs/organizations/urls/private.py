"""URLs that require login."""

from django.urls import path
from django.urls import re_path

from readthedocs.core.views import PageNotFoundView
from readthedocs.organizations.views import private as views


urlpatterns = [
    path(
        "",
        views.ListOrganization.as_view(),
        name="organization_list",
    ),
    re_path(
        r"^choose/(?P<next_name>[\w.-]+)/$",
        views.ChooseOrganization.as_view(),
        name="organization_choose",
    ),
    path(
        "create/",
        views.CreateOrganizationSignup.as_view(),
        name="organization_create",
    ),
    re_path(
        r"^(?P<slug>[\w.-]+)/edit/$",
        views.EditOrganization.as_view(),
        name="organization_edit",
    ),
    re_path(
        r"^(?P<slug>[\w.-]+)/delete/$",
        views.DeleteOrganization.as_view(),
        name="organization_delete",
    ),
    re_path(
        r"^(?P<slug>[\w.-]+)/security-log/$",
        views.OrganizationSecurityLog.as_view(),
        name="organization_security_log",
    ),
    # Owners
    re_path(
        r"^(?P<slug>[\w.-]+)/owners/(?P<owner>\d+)/delete/$",
        views.DeleteOrganizationOwner.as_view(),
        name="organization_owner_delete",
    ),
    re_path(
        r"^(?P<slug>[\w.-]+)/owners/add/$",
        views.AddOrganizationOwner.as_view(),
        name="organization_owner_add",
    ),
    re_path(
        r"^(?P<slug>[\w.-]+)/owners/$",
        views.EditOrganizationOwners.as_view(),
        name="organization_owners",
    ),
    # Teams
    re_path(
        r"^(?P<slug>[\w.-]+)/teams/add/$",
        views.AddOrganizationTeam.as_view(),
        name="organization_team_add",
    ),
    re_path(
        r"^(?P<slug>[\w.-]+)/teams/(?P<team>[\w.-]+)/edit/$",
        views.EditOrganizationTeam.as_view(),
        name="organization_team_edit",
    ),
    re_path(
        r"^(?P<slug>[\w.-]+)/teams/(?P<team>[\w.-]+)/projects/$",
        views.UpdateOrganizationTeamProject.as_view(),
        name="organization_team_project_edit",
    ),
    re_path(
        r"^(?P<slug>[\w.-]+)/teams/(?P<team>[\w.-]+)/delete/$",
        views.DeleteOrganizationTeam.as_view(),
        name="organization_team_delete",
    ),
    re_path(
        r"^(?P<slug>[\w.-]+)/teams/(?P<team>[\w.-]+)/members/invite/$",
        views.AddOrganizationTeamMember.as_view(),
        name="organization_team_member_add",
    ),
    re_path(
        r"^(?P<slug>[\w.-]+)/teams/(?P<team>[\w.-]+)/members/(?P<member>\d+)/revoke/$",
        views.DeleteOrganizationTeamMember.as_view(),
        name="organization_team_member_delete",
    ),
    # Placeholder URL, so that we can test the new templates
    # with organizations enabled from our community codebase.
    # TODO: migrate this functionality from corporate to community.
    re_path(
        r"^(?P<slug>[\w.-]+)/authorization/$",
        PageNotFoundView.as_view(),
        name="organization_sso",
    ),
]
