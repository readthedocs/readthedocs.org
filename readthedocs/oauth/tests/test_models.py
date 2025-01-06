from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.oauth.models import RemoteRepository
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
