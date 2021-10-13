from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django_dynamic_fixture import get

from readthedocs.organizations.models import Organization, Team, TeamInvite
from readthedocs.rtd_tests.tests.test_privacy_urls import URLAccessMixin


class OrganizationMixin(URLAccessMixin):

    def setUp(self):
        super().setUp()
        self.user = get(User)
        self.member = get(User)
        self.organization = get(Organization, owners=[self.user])
        self.org_owner = self.organization.owners.first()
        self.team = get(Team, organization=self.organization, members=[self.member])
        self.team_member = self.team.members.first()
        self.invite = get(TeamInvite, organization=self.organization, team=self.team)
        self.default_kwargs.update(
            {
                'slug': self.organization.slug,
                'team': self.team.slug,
                'hash': self.invite.hash,
                'owner': self.org_owner.pk,
                'member': self.team_member.pk,
            }
        )

    def get_url_path_ctx(self):
        return self.default_kwargs


@override_settings(RTD_ALLOW_ORGANIZATIONS=False)
class NoOrganizationsTest(OrganizationMixin, TestCase):
    
    default_status_code = 404

    def login(self):
        return self.client.force_login(self.user)

    def test_public_urls(self):
        from readthedocs.organizations.urls.public import urlpatterns
        self._test_url(urlpatterns)

    def test_private_urls(self):
        from readthedocs.organizations.urls.private import urlpatterns
        self._test_url(urlpatterns)


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class AuthUserOrganizationsTest(OrganizationMixin, TestCase):

    response_data = {
        # Places where we 302 on success.
        '/organizations/invite/{hash}/redeem/': {'status_code': 302},

        # 405's where we should be POST'ing
        '/organizations/{slug}/owners/{owner}/delete/': {'status_code': 405},
        '/organizations/{slug}/teams/{team}/members/{member}/revoke/': {'status_code': 405},
    }

    def login(self):
        self.client.force_login(self.user)

    def test_public_urls(self):
        from readthedocs.organizations.urls.public import urlpatterns
        self._test_url(urlpatterns)

    def test_private_urls(self):
        from readthedocs.organizations.urls.private import urlpatterns
        self._test_url(urlpatterns)
