from unittest import mock

from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.contrib.auth.models import User
from django.core.exceptions import NON_FIELD_ERRORS
from django.test import TestCase
from django.test.utils import override_settings
from django_dynamic_fixture import get

from readthedocs.builds.constants import EXTERNAL, LATEST, LATEST_VERBOSE_NAME, STABLE, TAG, BRANCH
from readthedocs.builds.models import Version
from readthedocs.core.forms import RichValidationError
from readthedocs.oauth.models import RemoteRepository, RemoteRepositoryRelation
from readthedocs.organizations.models import Organization, Team
from readthedocs.projects.constants import (
    ADDONS_FLYOUT_SORTING_CALVER,
    ADDONS_FLYOUT_SORTING_CUSTOM_PATTERN,
    MULTIPLE_VERSIONS_WITH_TRANSLATIONS,
    MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS,
    PRIVATE,
    PUBLIC,
    SINGLE_VERSION_WITHOUT_TRANSLATIONS,
    SPHINX,
)
from readthedocs.projects.forms import (
    AddonsConfigForm,
    EmailHookForm,
    EnvironmentVariableForm,
    ProjectAutomaticForm,
    ProjectBasicsForm,
    ProjectManualForm,
    TranslationForm,
    UpdateProjectForm,
    WebHookForm,
)
from readthedocs.projects.models import (
    EnvironmentVariable,
    Feature,
    Project,
    WebHookEvent,
)
from readthedocs.projects.validators import MAX_SIZE_ENV_VARS_PER_PROJECT


class TestProjectForms(TestCase):
    def test_import_repo_url(self):
        """Validate different type of repository URLs on importing a Project."""

        common_urls = [
            # Invalid
            ("./path/to/relative/folder", False),
            ("../../path/to/relative/folder", False),
            ("../../path/to/@/folder", False),
            ("/path/to/local/folder", False),
            ("/path/to/@/folder", False),
            ("file:///path/to/local/folder", False),
            ("file:///path/to/@/folder", False),
            ("github.com/humitos/foo", False),
            ("https://github.com/|/foo", False),
            ("git://github.com/&&/foo", False),
            # Valid
            ("git://github.com/humitos/foo", True),
            ("http://github.com/humitos/foo", True),
            ("https://github.com/humitos/foo", True),
            ("http://gitlab.com/humitos/foo", True),
            ("http://bitbucket.com/humitos/foo", True),
            ("ftp://ftpserver.com/humitos/foo", True),
            ("ftps://ftpserver.com/humitos/foo", True),
            ("lp:zaraza", True),
        ]

        public_urls = [
            ("git@github.com:humitos/foo", False),
            ("ssh://git@github.com/humitos/foo", False),
            ("ssh+git://github.com/humitos/foo", False),
            ("strangeuser@bitbucket.org:strangeuser/readthedocs.git", False),
            ("user@one-ssh.domain.com:22/_ssh/docs", False),
        ] + common_urls

        private_urls = [
            ("git@github.com:humitos/foo", True),
            ("ssh://git@github.com/humitos/foo", True),
            ("ssh+git://github.com/humitos/foo", True),
            ("strangeuser@bitbucket.org:strangeuser/readthedocs.git", True),
            ("user@one-ssh.domain.com:22/_ssh/docs", True),
        ] + common_urls

        with override_settings(ALLOW_PRIVATE_REPOS=False):
            for url, valid in public_urls:
                initial = {
                    "name": "foo",
                    "repo_type": "git",
                    "repo": url,
                    "language": "en",
                }
                form = ProjectBasicsForm(initial)
                self.assertEqual(form.is_valid(), valid, msg=url)

        with override_settings(ALLOW_PRIVATE_REPOS=True):
            for url, valid in private_urls:
                initial = {
                    "name": "foo",
                    "repo_type": "git",
                    "repo": url,
                    "language": "en",
                }
                form = ProjectBasicsForm(initial)
                self.assertEqual(form.is_valid(), valid, msg=url)

    def test_empty_slug(self):
        initial = {
            "name": "''",
            "repo_type": "git",
            "repo": "https://github.com/user/repository",
            "language": "en",
        }
        form = ProjectBasicsForm(initial)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_length_of_tags(self):
        project = get(Project)
        data = {
            "name": "Project",
            "repo": "https://github.com/readthedocs/readthedocs.org/",
            "repo_type": project.repo_type,
            "default_version": LATEST,
            "versioning_scheme": project.versioning_scheme,
            "documentation_type": "sphinx",
            "language": "en",
        }
        data["tags"] = "{},{}".format("a" * 50, "b" * 99)
        form = UpdateProjectForm(data, instance=project)
        self.assertTrue(form.is_valid())

        data["tags"] = "{},{}".format("a" * 90, "b" * 100)
        form = UpdateProjectForm(data, instance=project)
        self.assertTrue(form.is_valid())

        data["tags"] = "{},{}".format("a" * 99, "b" * 101)
        form = UpdateProjectForm(data, instance=project)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error("tags"))
        error_msg = "Length of each tag must be less than or equal to 100 characters."
        self.assertDictEqual(form.errors, {"tags": [error_msg]})

    def test_strip_repo_url(self):
        form = ProjectBasicsForm(
            {
                "name": "foo",
                "repo_type": "git",
                "repo": "https://github.com/rtfd/readthedocs.org/",
                "language": "en",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["repo"], "https://github.com/rtfd/readthedocs.org"
        )


class TestProjectAdvancedForm(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, privacy_level=PUBLIC, users=[self.user])
        get(
            Version,
            project=self.project,
            slug="public-1",
            active=True,
            privacy_level=PUBLIC,
            identifier="public-1",
            verbose_name="public-1",
        )
        get(
            Version,
            project=self.project,
            slug="public-2",
            active=True,
            privacy_level=PUBLIC,
            identifier="public-2",
            verbose_name="public-2",
        )
        get(
            Version,
            project=self.project,
            slug="public-3",
            active=False,
            privacy_level=PUBLIC,
            identifier="public-3",
            verbose_name="public-3",
        )
        get(
            Version,
            project=self.project,
            slug="public-4",
            active=False,
            privacy_level=PUBLIC,
            identifier="public/4",
            verbose_name="public/4",
        )
        get(
            Version,
            project=self.project,
            slug="private",
            active=True,
            privacy_level=PRIVATE,
            identifier="private",
            verbose_name="private",
        )

    def test_list_only_active_versions_on_default_version(self):
        form = UpdateProjectForm(instance=self.project)
        # This version is created automatically by the project on save
        self.assertTrue(self.project.versions.filter(slug=LATEST).exists())
        self.assertEqual(
            {slug for slug, _ in form.fields["default_version"].widget.choices},
            {"latest", "public-1", "public-2", "private"},
        )

    def test_default_version_field_if_no_active_version(self):
        project_1 = get(Project)
        project_1.versions.filter(active=True).update(active=False)

        # No active versions of project exists
        self.assertFalse(project_1.versions.filter(active=True).exists())

        form = UpdateProjectForm(instance=project_1)
        self.assertTrue(form.fields["default_version"].widget.attrs["readonly"])
        self.assertEqual(form.fields["default_version"].initial, "latest")

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_cant_update_privacy_level(self):
        form = UpdateProjectForm(
            {
                "name": "Project",
                "repo": "https://github.com/readthedocs/readthedocs.org/",
                "repo_type": self.project.repo_type,
                "default_version": LATEST,
                "language": self.project.language,
                "versioning_scheme": self.project.versioning_scheme,
                "documentation_type": SPHINX,
                "privacy_level": PRIVATE,
                "versioning_scheme": MULTIPLE_VERSIONS_WITH_TRANSLATIONS,
            },
            instance=self.project,
        )
        # The form is valid, but the field is ignored
        self.assertTrue(form.is_valid())
        self.assertEqual(self.project.privacy_level, PUBLIC)

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_can_update_privacy_level(self):
        form = UpdateProjectForm(
            {
                "name": "Project",
                "repo": "https://github.com/readthedocs/readthedocs.org/",
                "repo_type": self.project.repo_type,
                "default_version": LATEST,
                "versioning_scheme": self.project.versioning_scheme,
                "language": self.project.language,
                "documentation_type": SPHINX,
                "privacy_level": PRIVATE,
                "external_builds_privacy_level": PRIVATE,
                "versioning_scheme": MULTIPLE_VERSIONS_WITH_TRANSLATIONS,
            },
            instance=self.project,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(self.project.privacy_level, PRIVATE)

    @mock.patch("readthedocs.projects.forms.trigger_build")
    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_custom_readthedocs_yaml(self, trigger_build):
        custom_readthedocs_yaml_path = "folder/.readthedocs.yaml"
        form = UpdateProjectForm(
            {
                "name": "Project",
                "repo": "https://github.com/readthedocs/readthedocs.org/",
                "repo_type": self.project.repo_type,
                "default_version": LATEST,
                "language": self.project.language,
                "versioning_scheme": self.project.versioning_scheme,
                "documentation_type": SPHINX,
                "privacy_level": PRIVATE,
                "readthedocs_yaml_path": custom_readthedocs_yaml_path,
                "versioning_scheme": MULTIPLE_VERSIONS_WITH_TRANSLATIONS,
            },
            instance=self.project,
        )
        # The form is valid, but the field is ignored
        self.assertTrue(form.is_valid())
        self.assertEqual(self.project.privacy_level, PUBLIC)
        project = form.save()
        self.assertEqual(project.readthedocs_yaml_path, custom_readthedocs_yaml_path)

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    @mock.patch("readthedocs.projects.forms.trigger_build")
    def test_trigger_build_on_save(self, trigger_build):
        latest_version = self.project.get_latest_version()
        default_branch = get(
            Version,
            project=self.project,
            slug="main",
            active=True,
            type=BRANCH,
            verbose_name="main",
            identifier="main",
        )
        self.project.default_branch = default_branch.verbose_name
        self.project.save()

        data = {
            "name": "Project",
            "repo": "https://github.com/readthedocs/readthedocs.org/",
            "repo_type": self.project.repo_type,
            "default_version": LATEST,
            "versioning_scheme": self.project.versioning_scheme,
            "language": "en",
        }
        form = UpdateProjectForm(data, instance=self.project)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(trigger_build.call_count, 2)
        trigger_build.assert_has_calls(
            [
                mock.call(
                    project=self.project,
                    version=default_branch,
                ),
                mock.call(
                    project=self.project,
                    version=latest_version,
                ),
            ]
        )

        latest_version.active = False
        latest_version.save()

        trigger_build.reset_mock()
        form.save()
        trigger_build.assert_called_once_with(
            project=self.project,
            version=default_branch,
        )

    @mock.patch("readthedocs.projects.forms.trigger_build", mock.MagicMock())
    def test_set_remote_repository(self):
        data = {
            "name": "Project",
            "repo": "https://github.com/readthedocs/readthedocs.org",
            "repo_type": self.project.repo_type,
            "default_version": LATEST,
            "language": self.project.language,
            "versioning_scheme": self.project.versioning_scheme,
        }

        remote_repository = get(
            RemoteRepository,
            full_name="rtfd/template",
            clone_url="https://github.com/rtfd/template",
            html_url="https://github.com/rtfd/template",
            ssh_url="git@github.com:rtfd/template.git",
            private=False,
        )
        self.assertNotEqual(remote_repository.clone_url, data["repo"])

        # No remote repository attached.
        form = UpdateProjectForm(data, instance=self.project, user=self.user)
        self.assertTrue(form.is_valid())
        form.save()
        self.project.refresh_from_db()
        self.assertIsNone(self.project.remote_repository)
        self.assertEqual(self.project.repo, data["repo"])

        # Since there is no remote repository attached, the repo field should be enabled.
        form = UpdateProjectForm(data, instance=self.project, user=self.user)
        self.assertFalse(form.fields["repo"].disabled)

        # Remote repository attached, but it doesn't belong to the user.
        data["remote_repository"] = remote_repository.pk
        form = UpdateProjectForm(data, instance=self.project, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("remote_repository", form.errors)

        # Remote repository attached, it belongs to the user now.
        remote_repository_rel = get(
            RemoteRepositoryRelation,
            remote_repository=remote_repository,
            user=self.user,
            admin=True,
        )
        data["remote_repository"] = remote_repository.pk
        form = UpdateProjectForm(data, instance=self.project, user=self.user)
        self.assertTrue(form.is_valid())
        form.save()
        self.project.refresh_from_db()
        self.assertEqual(self.project.remote_repository, remote_repository)
        self.assertEqual(self.project.repo, remote_repository.clone_url)

        # Since a remote repository is attached, the repo field should be disabled.
        form = UpdateProjectForm(data, instance=self.project, user=self.user)
        self.assertTrue(form.fields["repo"].disabled)

        # This project has the don't sync with remote repository feature enabled,
        # so the repo field should be enabled.
        feature = get(Feature, feature_id=Feature.DONT_SYNC_WITH_REMOTE_REPO)
        self.project.feature_set.add(feature)
        form = UpdateProjectForm(data, instance=self.project, user=self.user)
        self.assertFalse(form.fields["repo"].disabled)
        self.project.feature_set.remove(feature)

        # The project has the remote repository attached.
        # And the user doesn't have access to it anymore, but still can use it.
        self.project.remote_repository = remote_repository
        self.project.save()
        remote_repository_rel.delete()
        data["remote_repository"] = remote_repository.pk
        form = UpdateProjectForm(data, instance=self.project, user=self.user)
        self.assertTrue(form.is_valid())


class TestProjectAdvancedFormDefaultBranch(TestCase):
    def setUp(self):
        self.project = get(
            Project,
            repo="https://github.com/readthedocs/readthedocs.org/",
        )
        user_created_stable_version = get(
            Version,
            project=self.project,
            slug="stable",
            active=True,
            privacy_level=PUBLIC,
            identifier="ab96cbff71a8f40a4340aaf9d12e6c10",
            verbose_name="stable",
        )
        get(
            Version,
            project=self.project,
            slug="public-1",
            active=True,
            privacy_level=PUBLIC,
            identifier="public-1",
            verbose_name="public-1",
        )
        get(
            Version,
            project=self.project,
            slug="private",
            active=True,
            privacy_level=PRIVATE,
            identifier="private",
            verbose_name="private",
        )

    def test_list_only_non_auto_generated_versions_in_default_branch_choices(self):
        form = UpdateProjectForm(instance=self.project)
        # This version is created automatically by the project on save
        latest = self.project.versions.filter(slug=LATEST)
        self.assertTrue(latest.exists())
        # show only the versions that are not auto generated as choices
        self.assertEqual(
            {
                identifier
                for identifier, _ in form.fields["default_branch"].widget.choices
            },
            {
                None,
                "stable",
                "public-1",
                "private",
            },
        )
        # Auto generated version `latest` should not be among the choices
        self.assertNotIn(
            latest.first().verbose_name,
            [
                identifier
                for identifier, _ in form.fields["default_branch"].widget.choices
            ],
        )

    def test_list_user_created_latest_and_stable_versions_in_default_branch_choices(
        self,
    ):
        self.project.versions.filter(slug=LATEST).first().delete()
        user_created_latest_version = get(
            Version,
            project=self.project,
            slug="latest",
            active=True,
            privacy_level=PUBLIC,
            identifier="ab96cbff71a8f40a4240aaf9d12e6c10",
            verbose_name="latest",
        )
        form = UpdateProjectForm(instance=self.project)
        # This version is created by the user
        latest = self.project.versions.filter(slug=LATEST)
        # This version is created by the user
        stable = self.project.versions.filter(slug=STABLE)

        self.assertIn(
            latest.first().verbose_name,
            [
                identifier
                for identifier, _ in form.fields["default_branch"].widget.choices
            ],
        )
        self.assertIn(
            stable.first().verbose_name,
            [
                identifier
                for identifier, _ in form.fields["default_branch"].widget.choices
            ],
        )

    def test_external_version_not_in_default_branch_choices(self):
        external_version = get(
            Version,
            identifier="pr-version",
            verbose_name="pr-version",
            slug="pr-9999",
            project=self.project,
            active=True,
            type=EXTERNAL,
            privacy_level=PUBLIC,
        )
        form = UpdateProjectForm(instance=self.project)

        self.assertNotIn(
            external_version.verbose_name,
            [
                identifier
                for identifier, _ in form.fields["default_branch"].widget.choices
            ],
        )

    @mock.patch("readthedocs.projects.forms.trigger_build")
    def test_change_default_branch_from_tag_to_branch_and_vice_versa(self, trigger_build):
        branch = get(
            Version,
            project=self.project,
            slug="branch",
            type=BRANCH,
            verbose_name="branch",
            identifier="branch",
        )
        tag = get(
            Version,
            project=self.project,
            slug="tag",
            type=TAG,
            verbose_name="tag",
            identifier="1234abcd",
        )

        data = {
            "name": self.project.name,
            "repo": self.project.repo,
            "repo_type": self.project.repo_type,
            "default_version": LATEST,
            "versioning_scheme": self.project.versioning_scheme,
            "language": self.project.language,
            "default_branch": branch.verbose_name,
            "privacy_level": self.project.privacy_level,
            "external_builds_privacy_level": self.project.external_builds_privacy_level,
        }
        form = UpdateProjectForm(data, instance=self.project)
        assert form.is_valid()
        form.save()

        self.project.refresh_from_db()
        latest = self.project.get_latest_version()
        assert latest.slug == LATEST
        assert latest.verbose_name == LATEST_VERBOSE_NAME
        assert latest.identifier == branch.verbose_name
        assert latest.type == BRANCH

        data["default_branch"] = tag.verbose_name
        form = UpdateProjectForm(data, instance=self.project)
        assert form.is_valid()
        form.save()

        self.project.refresh_from_db()
        latest = self.project.get_latest_version()
        assert latest.slug == LATEST
        assert latest.verbose_name == LATEST_VERBOSE_NAME
        assert latest.identifier == tag.verbose_name
        assert latest.type == TAG


@override_settings(RTD_ALLOW_ORGANIZATIONS=False)
class TestProjectPrevalidationForms(TestCase):
    def setUp(self):
        # User with connection
        # User without connection
        self.user_github = get(User)
        self.social_github = get(
            SocialAccount, user=self.user_github, provider=GitHubProvider.id
        )
        self.user_email = get(User)

    def test_form_prevalidation_email_user(self):
        form_auto = ProjectAutomaticForm(user=self.user_email)
        form_manual = ProjectManualForm(user=self.user_email)

        # Test validation errors directly
        self.assertRaises(RichValidationError, form_auto.clean_prevalidation)
        form_manual.clean_prevalidation()

        # Test downstream
        self.assertFalse(form_auto.is_valid())
        self.assertEqual(form_auto.errors, {NON_FIELD_ERRORS: mock.ANY})
        self.assertTrue(form_manual.is_valid())
        self.assertEqual(form_manual.errors, {})

    def test_form_prevalidation_github_user(self):
        form_auto = ProjectAutomaticForm(user=self.user_github)
        form_manual = ProjectManualForm(user=self.user_github)

        # Test validation errors directly
        form_auto.clean_prevalidation()
        form_manual.clean_prevalidation()

        # Test downstream
        self.assertTrue(form_auto.is_valid())
        self.assertEqual(form_auto.errors, {})
        self.assertTrue(form_manual.is_valid())
        self.assertEqual(form_manual.errors, {})


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class TestProjectPrevalidationFormsWithOrganizations(TestCase):
    def setUp(self):
        self.user_owner = get(User)
        self.social_owner = get(
            SocialAccount, user=self.user_owner, provider=GitHubProvider.id
        )
        self.user_admin = get(User)
        self.social_admin = get(
            SocialAccount, user=self.user_admin, provider=GitHubProvider.id
        )
        self.user_readonly = get(User)
        self.social_readonly = get(
            SocialAccount, user=self.user_readonly, provider=GitHubProvider.id
        )

        self.organization = get(
            Organization,
            owners=[self.user_owner],
            projects=[],
        )
        self.team_admin = get(
            Team,
            access="admin",
            organization=self.organization,
            members=[self.user_admin],
        )
        self.team_readonly = get(
            Team,
            access="readonly",
            organization=self.organization,
            members=[self.user_readonly],
        )

    def test_form_prevalidation_readonly_user(self):
        form_auto = ProjectAutomaticForm(user=self.user_readonly)
        form_manual = ProjectManualForm(user=self.user_readonly)

        # Test validation errors directly
        self.assertRaises(RichValidationError, form_auto.clean_prevalidation)
        self.assertRaises(RichValidationError, form_manual.clean_prevalidation)

        # Test downstream
        self.assertFalse(form_auto.is_valid())
        self.assertEqual(form_auto.errors, {NON_FIELD_ERRORS: mock.ANY})
        self.assertFalse(form_manual.is_valid())
        self.assertEqual(form_manual.errors, {NON_FIELD_ERRORS: mock.ANY})

    def test_form_prevalidation_admin_user(self):
        form_auto = ProjectAutomaticForm(user=self.user_admin)
        form_manual = ProjectManualForm(user=self.user_admin)

        # Test validation errors directly
        form_auto.clean_prevalidation()
        form_manual.clean_prevalidation()

        # Test downstream
        self.assertTrue(form_auto.is_valid())
        self.assertEqual(form_auto.errors, {})
        self.assertTrue(form_manual.is_valid())
        self.assertEqual(form_manual.errors, {})

    def test_form_prevalidation_owner_user(self):
        form_auto = ProjectAutomaticForm(user=self.user_owner)
        form_manual = ProjectManualForm(user=self.user_owner)

        # Test validation errors directly
        form_auto.clean_prevalidation()
        form_manual.clean_prevalidation()

        # Test downstream
        self.assertTrue(form_auto.is_valid())
        self.assertEqual(form_auto.errors, {})
        self.assertTrue(form_manual.is_valid())
        self.assertEqual(form_manual.errors, {})


class TestTranslationForms(TestCase):
    def setUp(self):
        self.user_a = get(User)
        self.project_a_es = self.get_project(lang="es", users=[self.user_a])
        self.project_b_en = self.get_project(lang="en", users=[self.user_a])
        self.project_c_br = self.get_project(lang="br", users=[self.user_a])
        self.project_d_ar = self.get_project(lang="ar", users=[self.user_a])
        self.project_e_en = self.get_project(lang="en", users=[self.user_a])

        self.user_b = get(User)
        self.project_f_ar = self.get_project(lang="ar", users=[self.user_b])
        self.project_g_ga = self.get_project(lang="ga", users=[self.user_b])

        self.project_s_fr = self.get_project(
            lang="fr",
            users=[self.user_b, self.user_a],
        )

    def get_project(self, lang, users, **kwargs):
        return get(
            Project, language=lang, users=users, main_language_project=None, **kwargs
        )

    def test_list_only_owner_projects(self):
        form = TranslationForm(
            {"project": self.project_b_en.slug},
            parent=self.project_a_es,
            user=self.user_a,
        )
        self.assertTrue(form.is_valid())
        expected_projects = [
            self.project_b_en,
            self.project_c_br,
            self.project_d_ar,
            self.project_e_en,
            self.project_s_fr,
        ]
        self.assertEqual(
            {proj_slug for proj_slug, _ in form.fields["project"].choices},
            {project.slug for project in expected_projects},
        )

        form = TranslationForm(
            {"project": self.project_g_ga.slug},
            parent=self.project_f_ar,
            user=self.user_b,
        )
        self.assertTrue(form.is_valid())
        expected_projects = [
            self.project_g_ga,
            self.project_s_fr,
        ]
        self.assertEqual(
            {proj_slug for proj_slug, _ in form.fields["project"].choices},
            {project.slug for project in expected_projects},
        )

    def test_excludes_existing_translations(self):
        self.project_a_es.translations.add(self.project_b_en)
        self.project_a_es.translations.add(self.project_c_br)
        self.project_a_es.save()

        form = TranslationForm(
            {"project": self.project_d_ar.slug},
            parent=self.project_a_es,
            user=self.user_a,
        )
        self.assertTrue(form.is_valid())
        expected_projects = [
            self.project_d_ar,
            self.project_e_en,
            self.project_s_fr,
        ]
        self.assertEqual(
            {proj_slug for proj_slug, _ in form.fields["project"].choices},
            {project.slug for project in expected_projects},
        )

    def test_user_cant_add_other_user_project(self):
        form = TranslationForm(
            {"project": self.project_f_ar.slug},
            parent=self.project_b_en,
            user=self.user_a,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Select a valid choice",
            "".join(form.errors["project"]),
        )
        self.assertNotIn(
            self.project_f_ar,
            [proj_slug for proj_slug, _ in form.fields["project"].choices],
        )

    def test_user_cant_add_project_with_same_lang(self):
        form = TranslationForm(
            {"project": self.project_b_en.slug},
            parent=self.project_e_en,
            user=self.user_a,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Both projects can not have the same language (English).",
            "".join(form.errors["project"]),
        )

    def test_user_cant_add_project_with_same_lang_of_other_translation(self):
        self.project_a_es.translations.add(self.project_b_en)
        self.project_a_es.save()

        form = TranslationForm(
            {"project": self.project_e_en.slug},
            parent=self.project_a_es,
            user=self.user_a,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "This project already has a translation for English.",
            "".join(form.errors["project"]),
        )

    def test_no_nesting_translation(self):
        self.project_a_es.translations.add(self.project_b_en)
        self.project_a_es.save()

        form = TranslationForm(
            {"project": self.project_b_en.slug},
            parent=self.project_c_br,
            user=self.user_a,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Select a valid choice",
            "".join(form.errors["project"]),
        )

    def test_no_nesting_translation_case_2(self):
        self.project_a_es.translations.add(self.project_b_en)
        self.project_a_es.save()

        form = TranslationForm(
            {"project": self.project_a_es.slug},
            parent=self.project_c_br,
            user=self.user_a,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "A project with existing translations can not",
            "".join(form.errors["project"]),
        )

    def test_not_already_translation(self):
        self.project_a_es.translations.add(self.project_b_en)
        self.project_a_es.save()

        form = TranslationForm(
            {"project": self.project_c_br.slug},
            parent=self.project_b_en,
            user=self.user_a,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "is already a translation",
            "".join(form.errors["project"]),
        )

    def test_cant_change_language_to_translation_lang(self):
        self.project_a_es.translations.add(self.project_b_en)
        self.project_a_es.translations.add(self.project_c_br)
        self.project_a_es.save()

        # Parent project tries to change lang
        form = UpdateProjectForm(
            {
                "name": "Project",
                "repo": "https://github.com/readthedocs/readthedocs.org/",
                "repo_type": self.project_a_es.repo_type,
                "versioning_scheme": self.project_a_es.versioning_scheme,
                "documentation_type": "sphinx",
                "language": "en",
            },
            instance=self.project_a_es,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'There is already a "en" translation',
            "".join(form.errors["language"]),
        )

        # Translation tries to change lang
        form = UpdateProjectForm(
            {
                "name": "Project",
                "repo": "https://github.com/readthedocs/readthedocs.org/",
                "repo_type": self.project_b_en.repo_type,
                "versioning_scheme": self.project_b_en.versioning_scheme,
                "documentation_type": "sphinx",
                "language": "es",
            },
            instance=self.project_b_en,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'There is already a "es" translation',
            "".join(form.errors["language"]),
        )

        # Translation tries to change lang
        # to the same as its sibling
        form = UpdateProjectForm(
            {
                "name": "Project",
                "repo": "https://github.com/readthedocs/readthedocs.org/",
                "repo_type": self.project_b_en.repo_type,
                "versioning_scheme": self.project_b_en.versioning_scheme,
                "documentation_type": "sphinx",
                "language": "br",
            },
            instance=self.project_b_en,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'There is already a "br" translation',
            "".join(form.errors["language"]),
        )

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_can_change_language_to_self_lang(self):
        self.project_a_es.translations.add(self.project_b_en)
        self.project_a_es.translations.add(self.project_c_br)
        self.project_a_es.save()

        # Parent project tries to change lang
        form = UpdateProjectForm(
            {
                "repo": "https://github.com/test/test",
                "repo_type": self.project_a_es.repo_type,
                "name": self.project_a_es.name,
                "default_version": LATEST,
                "versioning_scheme": self.project_b_en.versioning_scheme,
                "documentation_type": "sphinx",
                "language": "es",
            },
            instance=self.project_a_es,
        )
        self.assertTrue(form.is_valid())

        # Translation tries to change lang
        form = UpdateProjectForm(
            {
                "repo": "https://github.com/test/test",
                "repo_type": self.project_b_en.repo_type,
                "name": self.project_b_en.name,
                "default_version": LATEST,
                "versioning_scheme": self.project_b_en.versioning_scheme,
                "documentation_type": "sphinx",
                "language": "en",
            },
            instance=self.project_b_en,
        )
        self.assertTrue(form.is_valid())

    def test_cant_add_translations_to_multiple_versions_without_translations_project(
        self,
    ):
        self.project_a_es.versioning_scheme = MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS
        self.project_a_es.save()

        form = TranslationForm(
            {"project": self.project_b_en.slug},
            parent=self.project_a_es,
            user=self.user_a,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "This project is configured with a versioning scheme that doesn't support translations.",
            "".join(form.errors["__all__"]),
        )

    def test_cant_add_translations_to_single_version_without_translations_project(self):
        self.project_a_es.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.project_a_es.save()

        form = TranslationForm(
            {"project": self.project_b_en.slug},
            parent=self.project_a_es,
            user=self.user_a,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "This project is configured with a versioning scheme that doesn't support translations.",
            "".join(form.errors["__all__"]),
        )


class TestWebhookForm(TestCase):
    def setUp(self):
        self.project = get(Project)

    def test_webhookform(self):
        self.assertEqual(self.project.webhook_notifications.all().count(), 0)

        data = {
            "url": "http://www.example.com/",
            "payload": "{}",
            "events": [WebHookEvent.objects.get(name=WebHookEvent.BUILD_FAILED).id],
        }
        form = WebHookForm(data=data, project=self.project)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(self.project.webhook_notifications.all().count(), 1)

        data = {
            "url": "https://www.example.com/",
            "payload": "{}",
            "events": [WebHookEvent.objects.get(name=WebHookEvent.BUILD_PASSED).id],
        }
        form = WebHookForm(data=data, project=self.project)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(self.project.webhook_notifications.all().count(), 2)

    def test_wrong_inputs_in_webhookform(self):
        self.assertEqual(self.project.webhook_notifications.all().count(), 0)

        data = {
            "url": "",
            "payload": "{}",
            "events": [WebHookEvent.objects.get(name=WebHookEvent.BUILD_FAILED).id],
        }
        form = WebHookForm(data=data, project=self.project)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {"url": ["This field is required."]})
        self.assertEqual(self.project.webhook_notifications.all().count(), 0)

        data = {
            "url": "wrong-url",
            "payload": "{}",
            "events": [WebHookEvent.objects.get(name=WebHookEvent.BUILD_FAILED).id],
        }
        form = WebHookForm(data=data, project=self.project)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {"url": ["Enter a valid URL."]})
        self.assertEqual(self.project.webhook_notifications.all().count(), 0)

        data = {
            "url": "https://example.com/webhook/",
            "payload": "{wrong json object}",
            "events": [WebHookEvent.objects.get(name=WebHookEvent.BUILD_FAILED).id],
        }
        form = WebHookForm(data=data, project=self.project)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(
            form.errors, {"payload": ["The payload must be a valid JSON object."]}
        )
        self.assertEqual(self.project.webhook_notifications.all().count(), 0)

        data = {
            "url": "https://example.com/webhook/",
            "payload": "{}",
            "events": [],
        }
        form = WebHookForm(data=data, project=self.project)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {"events": ["This field is required."]})
        self.assertEqual(self.project.webhook_notifications.all().count(), 0)


class TestNotificationForm(TestCase):
    def setUp(self):
        self.project = get(Project)

    def test_emailhookform(self):
        self.assertEqual(self.project.emailhook_notifications.all().count(), 0)

        data = {"email": "test@email.com"}
        form = EmailHookForm(data=data, project=self.project)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(self.project.emailhook_notifications.all().count(), 1)

    def test_wrong_inputs_in_emailhookform(self):
        self.assertEqual(self.project.emailhook_notifications.all().count(), 0)

        data = {"email": "wrong_email@"}
        form = EmailHookForm(data=data, project=self.project)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {"email": ["Enter a valid email address."]})
        self.assertEqual(self.project.emailhook_notifications.all().count(), 0)

        data = {"email": ""}
        form = EmailHookForm(data=data, project=self.project)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {"email": ["This field is required."]})
        self.assertEqual(self.project.emailhook_notifications.all().count(), 0)


class TestProjectEnvironmentVariablesForm(TestCase):
    def setUp(self):
        self.project = get(Project)

    def test_use_invalid_names(self):
        data = {
            "name": "VARIABLE WITH SPACES",
            "value": "string here",
        }
        form = EnvironmentVariableForm(data, project=self.project)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Variable name can't contain spaces",
            form.errors["name"],
        )

        data = {
            "name": "READTHEDOCS__INVALID",
            "value": "string here",
        }
        form = EnvironmentVariableForm(data, project=self.project)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Variable name can't start with READTHEDOCS",
            form.errors["name"],
        )

        data = {
            "name": "INVALID_CHAR*",
            "value": "string here",
        }
        form = EnvironmentVariableForm(data, project=self.project)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Only letters, numbers and underscore are allowed",
            form.errors["name"],
        )

        data = {
            "name": "__INVALID",
            "value": "string here",
        }
        form = EnvironmentVariableForm(data, project=self.project)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Variable name can't start with __ (double underscore)",
            form.errors["name"],
        )

        get(EnvironmentVariable, name="EXISTENT_VAR", project=self.project)
        data = {
            "name": "EXISTENT_VAR",
            "value": "string here",
        }
        form = EnvironmentVariableForm(data, project=self.project)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "There is already a variable with this name for this project",
            form.errors["name"],
        )

    def test_create(self):
        data = {
            "name": "MYTOKEN",
            "value": "string here",
        }
        form = EnvironmentVariableForm(data, project=self.project)
        form.save()

        self.assertEqual(EnvironmentVariable.objects.count(), 1)
        self.assertEqual(EnvironmentVariable.objects.latest().name, "MYTOKEN")
        self.assertEqual(EnvironmentVariable.objects.latest().value, "'string here'")

        data = {
            "name": "ESCAPED",
            "value": r"string escaped here: #$\1[]{}\|",
        }
        form = EnvironmentVariableForm(data, project=self.project)
        form.save()

        self.assertEqual(EnvironmentVariable.objects.count(), 2)
        self.assertEqual(EnvironmentVariable.objects.latest().name, "ESCAPED")
        self.assertEqual(
            EnvironmentVariable.objects.latest().value,
            r"'string escaped here: #$\1[]{}\|'",
        )

    def test_create_env_variable_with_long_value(self):
        data = {
            "name": "MYTOKEN",
            "value": "a" * (48000 + 1),
        }
        form = EnvironmentVariableForm(data, project=self.project)
        assert not form.is_valid()
        assert form.errors["value"] == [
            "Ensure this value has at most 48000 characters (it has 48001)."
        ]

    def test_create_env_variable_over_total_project_size(self):
        size = 2000
        for i in range((MAX_SIZE_ENV_VARS_PER_PROJECT - size) // size):
            get(
                EnvironmentVariable,
                project=self.project,
                name=f"ENVVAR{i}",
                value="a" * size,
                public=False,
            )

        form = EnvironmentVariableForm(
            {"name": "A", "value": "a" * (size // 2)}, project=self.project
        )
        assert form.is_valid()
        form.save()

        form = EnvironmentVariableForm(
            {"name": "B", "value": "a" * size}, project=self.project
        )
        assert not form.is_valid()
        assert form.errors["__all__"] == [
            "The total size of all environment variables in the project cannot exceed 256 KB."
        ]


class TestAddonsConfigForm(TestCase):
    def setUp(self):
        self.project = get(Project)

    def test_addonsconfig_form(self):
        data = {
            "enabled": True,
            "options_root_selector": "main",
            "analytics_enabled": False,
            "doc_diff_enabled": False,
            "filetreediff_enabled": True,
            # Empty lines, lines with trailing spaces or lines full of spaces are ignored
            "filetreediff_ignored_files": "user/index.html\n     \n\n\n   changelog.html    \n/normalized.html",
            "flyout_enabled": True,
            "flyout_sorting": ADDONS_FLYOUT_SORTING_CALVER,
            "flyout_sorting_latest_stable_at_beginning": True,
            "flyout_sorting_custom_pattern": None,
            "flyout_position": "bottom-left",
            "hotkeys_enabled": False,
            "search_enabled": False,
            "linkpreviews_enabled": True,
            "notifications_enabled": True,
            "notifications_show_on_latest": True,
            "notifications_show_on_non_stable": True,
            "notifications_show_on_external": True,
        }
        form = AddonsConfigForm(data=data, project=self.project)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(self.project.addons.enabled, True)
        self.assertEqual(self.project.addons.options_root_selector, "main")
        self.assertEqual(self.project.addons.analytics_enabled, False)
        self.assertEqual(self.project.addons.doc_diff_enabled, False)
        self.assertEqual(self.project.addons.filetreediff_enabled, True)
        self.assertEqual(
            self.project.addons.filetreediff_ignored_files,
            [
                "user/index.html",
                "changelog.html",
                "normalized.html",
            ],
        )
        self.assertEqual(self.project.addons.notifications_enabled, True)
        self.assertEqual(self.project.addons.notifications_show_on_latest, True)
        self.assertEqual(self.project.addons.notifications_show_on_non_stable, True)
        self.assertEqual(self.project.addons.notifications_show_on_external, True)
        self.assertEqual(self.project.addons.flyout_enabled, True)
        self.assertEqual(
            self.project.addons.flyout_sorting,
            ADDONS_FLYOUT_SORTING_CALVER,
        )
        self.assertEqual(
            self.project.addons.flyout_sorting_latest_stable_at_beginning,
            True,
        )
        self.assertEqual(self.project.addons.flyout_sorting_custom_pattern, None)
        self.assertEqual(self.project.addons.flyout_position, "bottom-left")
        self.assertEqual(self.project.addons.hotkeys_enabled, False)
        self.assertEqual(self.project.addons.search_enabled, False)
        self.assertEqual(self.project.addons.linkpreviews_enabled, True)
        self.assertEqual(self.project.addons.notifications_enabled, True)
        self.assertEqual(self.project.addons.notifications_show_on_latest, True)
        self.assertEqual(self.project.addons.notifications_show_on_non_stable, True)
        self.assertEqual(self.project.addons.notifications_show_on_external, True)

    def test_addonsconfig_form_invalid_sorting_custom_pattern(self):
        data = {
            "enabled": True,
            "analytics_enabled": False,
            "doc_diff_enabled": False,
            "flyout_enabled": True,
            "flyout_sorting": ADDONS_FLYOUT_SORTING_CUSTOM_PATTERN,
            "flyout_sorting_latest_stable_at_beginning": True,
            "flyout_sorting_custom_pattern": None,
            "hotkeys_enabled": False,
            "search_enabled": False,
            "notifications_enabled": True,
            "notifications_show_on_latest": True,
            "notifications_show_on_non_stable": True,
            "notifications_show_on_external": True,
        }
        form = AddonsConfigForm(data=data, project=self.project)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            "The flyout sorting custom pattern is required when selecting a custom pattern.",
            form.errors["__all__"][0],
        )
