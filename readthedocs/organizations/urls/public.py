from django.conf.urls import url
from django.views.generic.base import TemplateView

from readthedocsinc.organizations.views import public as views

urlpatterns = [
    url(
        r'^verify-email/$',
        TemplateView.as_view(template_name='organizations/verify_email.html'),
        name='organization_verify_email',
    ),
    url(
        r'^(?P<slug>[\w.-]+)/$',
        views.DetailOrganization.as_view(),
        name='organization_detail',
    ),
    # Teams
    url(
        r'^(?P<slug>[\w.-]+)/teams/(?P<team>[\w.-]+)/$',
        views.ListOrganizationTeamMembers.as_view(),
        name='organization_team_detail',
    ),
    url(
        r'^(?P<slug>[\w.-]+)/teams/$',
        views.ListOrganizationTeams.as_view(),
        name='organization_team_list',
    ),
    url(
        r'^invite/(?P<hash>[\w.-]+)/redeem/$',
        views.UpdateOrganizationTeamMember.as_view(),
        name='organization_invite_redeem',
    ),
    # Members
    url(
        r'^(?P<slug>[\w.-]+)/members/$',
        views.ListOrganizationMembers.as_view(),
        name='organization_members',
    ),
]
