from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.audit.models import AuditLog
from readthedocs.organizations.models import Organization, OrganizationOwner
from readthedocs.projects.models import Project


class TestAuditModels(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, users=[self.user])
        self.organization = get(Organization, projects=[self.project])
        get(OrganizationOwner, organization=self.organization, owner=self.user)
        self.auditlog = get(
            AuditLog,
            user=self.user,
            project=self.project,
            organization=self.organization,
        )

    def test_user_deletion(self):
        id = self.user.id
        username = self.user.username
        self.user.delete()
        self.auditlog.refresh_from_db()
        self.assertIsNone(self.auditlog.user)
        self.assertEqual(self.auditlog.log_user_id, id)
        self.assertEqual(self.auditlog.log_user_username, username)

    def test_project_deletion(self):
        id = self.project.id
        slug = self.project.slug
        self.project.delete()
        self.auditlog.refresh_from_db()
        self.assertIsNone(self.auditlog.project)
        self.assertEqual(self.auditlog.log_project_id, id)
        self.assertEqual(self.auditlog.log_project_slug, slug)

    def test_organization_deletion(self):
        id = self.organization.id
        slug = self.organization.slug
        self.organization.delete()
        self.auditlog.refresh_from_db()
        self.assertIsNone(self.auditlog.organization)
        self.assertEqual(self.auditlog.log_organization_id, id)
        self.assertEqual(self.auditlog.log_organization_slug, slug)

    def test_log_attached_to_user_only(self):
        log = get(
            AuditLog,
            user=self.user,
        )
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.log_user_id, self.user.id)
        self.assertEqual(log.log_user_username, self.user.username)

    def test_log_attached_to_project_with_organization_only(self):
        log = get(
            AuditLog,
            project=self.project,
        )
        self.assertEqual(log.project, self.project)
        self.assertEqual(log.log_project_id, self.project.id)
        self.assertEqual(log.log_project_slug, self.project.slug)
        self.assertEqual(log.organization, self.organization)
        self.assertEqual(log.log_organization_id, self.organization.id)
        self.assertEqual(log.log_organization_slug, self.organization.slug)

    def test_log_attached_to_organization_only(self):
        log = get(
            AuditLog,
            organization=self.organization,
        )
        self.assertEqual(log.organization, self.organization)
        self.assertEqual(log.log_organization_id, self.organization.id)
        self.assertEqual(log.log_organization_slug, self.organization.slug)

    def test_truncate_browser(self):
        text = "a" * 250
        log = get(
            AuditLog,
            user=self.user,
            browser=text,
        )
        self.assertEqual(log.browser, text)

        text = "a" * 300
        log = get(
            AuditLog,
            user=self.user,
            browser=text,
        )
        self.assertNotEqual(log.browser, text)
        self.assertTrue(log.browser.endswith(" - Truncated"))
