from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.oauth.models import RemoteRepository
from readthedocs.projects.models import Project


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
