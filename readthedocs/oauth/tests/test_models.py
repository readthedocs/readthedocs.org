from django.core.exceptions import ValidationError
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.oauth.models import RemoteRepository
from readthedocs.oauth.validators import CloneURLValidator
from readthedocs.oauth.validators import SshURLValidator
from readthedocs.projects.models import Feature, Project


class TestsModels(TestCase):
    def test_post_save_signal(self):
        clone_url_a = "https://github.com/readthedocs/test-builds"
        clone_url_b = "https://github.com/readthedocs/readthedocs.org"
        remote_repo = get(
            RemoteRepository,
            clone_url=clone_url_a,
        )
        project = get(
            Project,
            repo=clone_url_b,
            remote_repository=remote_repo,
        )

        # The project uses the clone url from the remote repository.
        assert project.repo == clone_url_a
        assert remote_repo.clone_url == clone_url_a

        remote_repo.clone_url = clone_url_b
        remote_repo.save()
        project.refresh_from_db()
        # The project clone URL is updated when the remote repository clone URL changes.
        assert project.repo == clone_url_b

        # The project URL is not updated when the feature is set to not sync with the remote repository.
        feature = get(Feature, feature_id=Feature.DONT_SYNC_WITH_REMOTE_REPO)
        project.feature_set.add(feature)
        remote_repo.clone_url = clone_url_a
        remote_repo.save()
        project.refresh_from_db()
        assert project.repo == clone_url_b


class TestSshURLValidator(TestCase):
    def setUp(self):
        self.validator = SshURLValidator()

    def test_valid_git_user_format(self):
        """SSH URL in git user format is accepted."""
        self.validator("git@github.com:readthedocs/test-builds.git")

    def test_valid_ssh_scheme(self):
        """SSH URL with ssh:// scheme is accepted."""
        self.validator("ssh://git@github.com/readthedocs/test-builds.git")

    def test_invalid_https_url(self):
        """HTTPS URL is rejected by SshURLValidator."""
        with self.assertRaises(ValidationError):
            self.validator("https://github.com/readthedocs/test-builds.git")

    def test_invalid_random_string(self):
        """Random string is rejected."""
        with self.assertRaises(ValidationError):
            self.validator("not-a-url")


class TestCloneURLValidator(TestCase):
    def setUp(self):
        self.validator = CloneURLValidator()

    def test_valid_https_url(self):
        """HTTPS clone URL is accepted."""
        self.validator("https://github.com/readthedocs/test-builds.git")

    def test_valid_http_url(self):
        """HTTP clone URL is accepted."""
        self.validator("http://github.com/readthedocs/test-builds.git")

    def test_valid_git_scheme(self):
        """git:// clone URL is accepted."""
        self.validator("git://github.com/readthedocs/test-builds.git")

    def test_valid_ssh_scheme(self):
        """ssh:// clone URL is accepted."""
        self.validator("ssh://git@github.com/readthedocs/test-builds.git")

    def test_valid_git_user_format(self):
        """SSH URL in git user format is accepted as a clone URL."""
        self.validator("git@github.com:readthedocs/test-builds.git")

    def test_invalid_random_string(self):
        """Random string is rejected."""
        with self.assertRaises(ValidationError):
            self.validator("not-a-url")


class TestRemoteRepositoryAdminValidation(TestCase):
    def test_ssh_url_git_user_format_accepted(self):
        """RemoteRepository full_clean accepts git user SSH URL in ssh_url field."""
        repo = get(
            RemoteRepository,
            ssh_url="git@github.com:readthedocs/test-builds.git",
            clone_url="https://github.com/readthedocs/test-builds.git",
        )
        # Should not raise ValidationError
        repo.full_clean()

    def test_clone_url_git_user_format_accepted(self):
        """RemoteRepository full_clean accepts git user SSH URL in clone_url field."""
        repo = get(
            RemoteRepository,
            clone_url="git@github.com:readthedocs/test-builds.git",
            ssh_url="git@github.com:readthedocs/test-builds.git",
        )
        # Should not raise ValidationError
        repo.full_clean()

    def test_clone_url_https_accepted(self):
        """RemoteRepository full_clean accepts HTTPS URL in clone_url field."""
        repo = get(
            RemoteRepository,
            clone_url="https://github.com/readthedocs/test-builds.git",
            ssh_url="",
        )
        # Should not raise ValidationError
        repo.full_clean()
