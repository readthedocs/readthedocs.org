import itertools

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django_dynamic_fixture import get
from rest_framework.authtoken.models import Token

from readthedocs.audit.models import AuditLog
from readthedocs.organizations.models import Organization, Team
from readthedocs.projects.models import Project


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=False,
)
class ProfileViewsTest(TestCase):
    def setUp(self):
        self.user = get(User)
        self.user.set_password("test")
        self.user.save()
        self.client.login(username=self.user.username, password="test")

    def test_edit_profile(self):
        resp = self.client.get(
            reverse("profiles_profile_edit"),
        )
        self.assertTrue(resp.status_code, 200)
        resp = self.client.post(
            reverse("profiles_profile_edit"),
            data={
                "first_name": "Read",
                "last_name": "Docs",
                "homepage": "readthedocs.org",
            },
        )
        self.assertTrue(resp.status_code, 200)
        self.assertEqual(resp["Location"], "/accounts/edit/")

        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, "Read")
        self.assertEqual(self.user.last_name, "Docs")
        self.assertEqual(self.user.profile.homepage, "readthedocs.org")

    def test_edit_profile_with_invalid_values(self):
        resp = self.client.get(
            reverse("profiles_profile_edit"),
        )
        self.assertTrue(resp.status_code, 200)

        resp = self.client.post(
            reverse("profiles_profile_edit"),
            data={
                "first_name": "a" * 31,
                "last_name": "b" * 31,
                "homepage": "c" * 101,
            },
        )

        FORM_ERROR_FORMAT = "Ensure this value has at most {} characters (it has {})."

        self.assertFormError(
            resp.context.get('form'),
            field="first_name",
            errors=FORM_ERROR_FORMAT.format(30, 31),
        )
        self.assertFormError(
            resp.context.get('form'),
            field="last_name",
            errors=FORM_ERROR_FORMAT.format(30, 31),
        )
        self.assertFormError(
            resp.context.get('form'),
            field="homepage",
            errors=FORM_ERROR_FORMAT.format(100, 101),
        )

    def test_delete_account(self):
        resp = self.client.get(
            reverse("delete_account"),
        )
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(
            reverse("delete_account"),
            data={
                "username": self.user.username,
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("homepage"))

        self.assertFalse(
            User.objects.filter(username=self.user.username).exists(),
        )

    def test_profile_detail(self):
        resp = self.client.get(
            reverse("profiles_profile_detail", args=(self.user.username,)),
        )
        self.assertTrue(resp.status_code, 200)

    def test_profile_detail_logout(self):
        self.client.logout()
        resp = self.client.get(
            reverse("profiles_profile_detail", args=(self.user.username,)),
        )
        self.assertTrue(resp.status_code, 200)

    def test_profile_detail_not_found(self):
        resp = self.client.get(
            reverse("profiles_profile_detail", args=("not-found",)),
        )
        self.assertTrue(resp.status_code, 404)

    def test_account_advertising(self):
        resp = self.client.get(
            reverse("account_advertising"),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.user.profile.allow_ads)
        resp = self.client.post(
            reverse("account_advertising"),
            data={"allow_ads": False},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("account_advertising"))
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.allow_ads)

    def test_list_api_tokens(self):
        resp = self.client.get(reverse("profiles_tokens"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "You currently have no API tokens.")

        token = Token.objects.create(user=self.user)
        resp = self.client.get(reverse("profiles_tokens"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, token.key)

    def test_create_api_token(self):
        self.assertEqual(Token.objects.filter(user=self.user).count(), 0)

        resp = self.client.get(reverse("profiles_tokens_create"))
        self.assertEqual(resp.status_code, 405)  # GET not allowed

        resp = self.client.post(reverse("profiles_tokens_create"))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Token.objects.filter(user=self.user).count(), 1)

    def test_delete_api_token(self):
        Token.objects.create(user=self.user)
        self.assertEqual(Token.objects.filter(user=self.user).count(), 1)

        resp = self.client.post(reverse("profiles_tokens_delete"))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Token.objects.filter(user=self.user).count(), 0)

    def test_list_security_logs(self):
        project = get(Project, users=[self.user], slug="project")
        another_project = get(Project, users=[self.user], slug="another-project")
        another_user = get(User)

        actions = [
            AuditLog.AUTHN,
            AuditLog.AUTHN_FAILURE,
            AuditLog.LOGOUT,
            AuditLog.PAGEVIEW,
        ]
        ips = [
            "10.10.10.1",
            "10.10.10.2",
        ]
        users = [self.user, another_user]
        AuditLog.objects.all().delete()
        for action, ip, user in itertools.product(actions, ips, users):
            get(
                AuditLog,
                user=user,
                action=action,
                ip=ip,
            )
            get(
                AuditLog,
                user=user,
                action=action,
                project=project,
                ip=ip,
            )
            get(
                AuditLog,
                user=user,
                action=action,
                project=another_project,
                ip=ip,
            )

        self.assertEqual(AuditLog.objects.count(), 48)

        queryset = AuditLog.objects.filter(
            log_user_id=self.user.pk,
            action__in=[AuditLog.AUTHN, AuditLog.AUTHN_FAILURE, AuditLog.LOGOUT],
        )

        # Show logs from the current user
        # and for authn/authn_failure/logout events only.
        resp = self.client.get(reverse("profiles_security_log"))
        self.assertEqual(resp.status_code, 200)
        auditlogs = resp.context_data["object_list"]
        self.assertQuerySetEqual(auditlogs, queryset)

        # Show logs filtered by project.
        resp = self.client.get(reverse("profiles_security_log") + "?project=project")
        self.assertEqual(resp.status_code, 200)
        auditlogs = resp.context_data["object_list"]
        self.assertQuerySetEqual(auditlogs, queryset.filter(log_project_slug="project"))

        # Show logs filtered by IP.
        ip = "10.10.10.2"
        resp = self.client.get(reverse("profiles_security_log") + f"?ip={ip}")
        self.assertEqual(resp.status_code, 200)
        auditlogs = resp.context_data["object_list"]
        self.assertQuerySetEqual(auditlogs, queryset.filter(ip=ip))

        # Show logs filtered by action.
        resp = self.client.get(
            reverse("profiles_security_log") + "?action=authentication"
        )
        self.assertEqual(resp.status_code, 200)
        auditlogs = resp.context_data["object_list"]
        self.assertQuerySetEqual(auditlogs, queryset.filter(action=AuditLog.AUTHN))

        # Show logs filtered by action.
        resp = self.client.get(
            reverse("profiles_security_log") + "?action=authentication-failure"
        )
        self.assertEqual(resp.status_code, 200)
        auditlogs = resp.context_data["object_list"]
        self.assertQuerySetEqual(
            auditlogs, queryset.filter(action=AuditLog.AUTHN_FAILURE)
        )

        # Show logs filtered by invalid values.
        for filter in ["ip", "project"]:
            resp = self.client.get(
                reverse("profiles_security_log") + f"?{filter}=invalid"
            )
            self.assertEqual(resp.status_code, 200)
            auditlogs = resp.context_data["object_list"]
            self.assertEqual(auditlogs.count(), 0, filter)

        # If action isn't a valid value, the filter is just ignored.
        resp = self.client.get(reverse("profiles_security_log") + "?action=invalid")
        self.assertEqual(resp.status_code, 200)
        auditlogs = resp.context_data["object_list"]
        self.assertQuerySetEqual(auditlogs, queryset)


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
)
class ProfileViewsWithOrganizationsTest(ProfileViewsTest):
    def setUp(self):
        super().setUp()
        self.owner = get(User, username="owner")
        self.team_mate = get(User, username="teammate")
        self.member_from_another_team = get(User, username="member_from_another_team")
        self.org = get(Organization, owners=[self.owner])

        self.team = get(
            Team,
            organization=self.org,
            name="admin",
            access="admin",
            projects=[],
        )
        self.org.add_member(
            self.user,
            self.team,
        )
        self.org.add_member(
            self.team_mate,
            self.team,
        )
        self.team2 = get(
            Team,
            organization=self.org,
            name="another-team",
            access="readonly",
            projects=[],
        )
        self.org.add_member(
            self.team_mate,
            self.team2,
        )
        self.org.add_member(
            self.member_from_another_team,
            self.team2,
        )

        self.another_owner = get(User, username="another_owner")
        self.another_user = get(User, username="another_user")
        self.another_org = get(Organization, owners=[self.another_owner])
        self.another_team = get(
            Team,
            organization=self.another_org,
            name="admin",
            access="admin",
            projects=[],
        )
        self.another_org.add_member(
            self.another_user,
            self.another_team,
        )

    def test_user_can_see_the_profile(self):
        self.client.force_login(self.user)
        url = reverse(
            "profiles_profile_detail", kwargs={"username": self.user.username}
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_unrelated_user_can_not_see_the_profile(self):
        url = reverse(
            "profiles_profile_detail", kwargs={"username": self.user.username}
        )
        self.client.force_login(self.another_user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        self.client.force_login(self.member_from_another_team)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        self.client.force_login(self.another_owner)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_related_user_can_see_the_profile(self):
        url = reverse(
            "profiles_profile_detail", kwargs={"username": self.user.username}
        )
        self.client.force_login(self.owner)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        self.client.force_login(self.team_mate)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        url = reverse(
            "profiles_profile_detail", kwargs={"username": self.owner.username}
        )
        self.client.force_login(self.user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        self.client.force_login(self.member_from_another_team)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_user_without_orgs_can_see_their_own_profile(self):
        new_user = get(User)
        self.client.force_login(new_user)
        url = reverse("profiles_profile_detail", kwargs={"username": new_user.username})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
