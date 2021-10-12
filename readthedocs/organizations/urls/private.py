"""URLs that require login."""
from django.conf.urls import url

from readthedocs.organizations.views import private as views

urlpatterns = [
    url(
        r'^$',
        views.ListOrganization.as_view(),
        name='organization_list',
    ),
    url(
        r'^create/$',
        views.CreateOrganizationSignup.as_view(),
        name='organization_create',
    ),
    url(
        r'^(?P<slug>[\w.-]+)/edit/$',
        views.EditOrganization.as_view(),
        name='organization_edit',
    ),
    url(
        r'^(?P<slug>[\w.-]+)/delete/$',
        views.DeleteOrganization.as_view(),
        name='organization_delete',
    ),
    # Owners
    url(
        r'^(?P<slug>[\w.-]+)/owners/(?P<owner>\d+)/delete/$',
        views.DeleteOrganizationOwner.as_view(),
        name='organization_owner_delete',
    ),
    url(
        r'^(?P<slug>[\w.-]+)/owners/add/$',
        views.AddOrganizationOwner.as_view(),
        name='organization_owner_add',
    ),
    url(
        r'^(?P<slug>[\w.-]+)/owners/$',
        views.EditOrganizationOwners.as_view(),
        name='organization_owners',
    ),
    # Teams
    url(
        r'^(?P<slug>[\w.-]+)/teams/add/$',
        views.AddOrganizationTeam.as_view(),
        name='organization_team_add',
    ),
    url(
        r'^(?P<slug>[\w.-]+)/teams/(?P<team>[\w.-]+)/edit/$',
        views.EditOrganizationTeam.as_view(),
        name='organization_team_edit',
    ),
    url(
        r'^(?P<slug>[\w.-]+)/teams/(?P<team>[\w.-]+)/projects/$',
        views.UpdateOrganizationTeamProject.as_view(),
        name='organization_team_project_edit',
    ),
    url(
        r'^(?P<slug>[\w.-]+)/teams/(?P<team>[\w.-]+)/delete/$',
        views.DeleteOrganizationTeam.as_view(),
        name='organization_team_delete',
    ),
    url(
        r'^(?P<slug>[\w.-]+)/teams/(?P<team>[\w.-]+)/members/invite/$',
        views.AddOrganizationTeamMember.as_view(),
        name='organization_team_member_add',
    ),
    url(
        r'^(?P<slug>[\w.-]+)/teams/(?P<team>[\w.-]+)/members/(?P<member>\d+)/revoke/$',
        views.DeleteOrganizationTeamMember.as_view(),
        name='organization_team_member_delete',
    ),
]
