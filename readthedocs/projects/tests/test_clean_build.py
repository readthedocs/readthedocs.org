import os
import stat
from unittest import mock

import django_dynamic_fixture as fixture
import pytest
from django.core.exceptions import SuspiciousFileOperation

from readthedocs.projects.models import Project
from readthedocs.projects.tasks.utils import _remove_as_root
from readthedocs.projects.tasks.utils import clean_build
from readthedocs.projects.tasks.utils import retire_builder


@pytest.mark.django_db
class TestCleanBuild:
    @pytest.fixture(autouse=True)
    def setup(self, settings, tmp_path):
        settings.DOCROOT = str(tmp_path / "user_builds")
        self.docroot = settings.DOCROOT
        self.project = fixture.get(Project, slug="project")
        self.version = self.project.versions.get(slug="latest")
        self.other_project = fixture.get(Project, slug="other")

    def test_removes_all_the_files_of_the_project(self):
        doc_path = self.project.doc_path
        # Files from other versions, or outside the known directories.
        os.makedirs(os.path.join(doc_path, "checkouts", "latest"))
        os.makedirs(os.path.join(doc_path, "checkouts", "other-version"))
        os.makedirs(os.path.join(doc_path, "envs", "other-version"))
        os.makedirs(os.path.join(doc_path, "tools"))
        os.makedirs(os.path.join(doc_path, "planted"))
        os.makedirs(self.other_project.doc_path)

        assert clean_build(self.version) is True
        assert not os.path.lexists(doc_path)
        # Only one build runs at a time,
        # but the files of other projects are never mounted into this build.
        assert os.path.exists(self.other_project.doc_path)

    def test_removes_docroot(self):
        os.makedirs(os.path.join(self.project.doc_path, "checkouts", "latest"))
        os.makedirs(self.other_project.doc_path)

        assert clean_build() is True
        assert not os.path.lexists(self.docroot)

    @mock.patch("readthedocs.projects.tasks.utils._remove_as_root")
    def test_doesnt_remove_as_root_if_not_needed(self, remove_as_root):
        os.makedirs(os.path.join(self.project.doc_path, "checkouts", "latest"))
        assert clean_build(self.version) is True
        remove_as_root.assert_not_called()

    @mock.patch("readthedocs.projects.tasks.utils._remove_as_root")
    def test_removes_as_root_files_that_cant_be_removed(self, remove_as_root):
        locked_dir = os.path.join(self.project.doc_path, "checkouts", "latest", "locked")
        os.makedirs(locked_dir)
        with open(os.path.join(locked_dir, "file"), "w") as f:
            f.write("content")
        os.chmod(locked_dir, stat.S_IRUSR | stat.S_IXUSR)

        def remove(path):
            os.chmod(locked_dir, stat.S_IRWXU)

        remove_as_root.side_effect = remove
        assert clean_build(self.version) is True
        remove_as_root.assert_called_once_with(self.project.doc_path)
        assert not os.path.lexists(self.project.doc_path)

    @mock.patch("readthedocs.projects.tasks.utils._remove_as_root")
    def test_returns_false_if_files_are_left(self, remove_as_root):
        locked_dir = os.path.join(self.project.doc_path, "checkouts", "latest", "locked")
        os.makedirs(locked_dir)
        with open(os.path.join(locked_dir, "file"), "w") as f:
            f.write("content")
        os.chmod(locked_dir, stat.S_IRUSR | stat.S_IXUSR)

        assert clean_build(self.version) is False
        remove_as_root.assert_called_once_with(self.project.doc_path)
        os.chmod(locked_dir, stat.S_IRWXU)

    @mock.patch("readthedocs.projects.tasks.utils._remove_as_root")
    def test_removes_empty_directory_without_permissions(self, remove_as_root):
        # A build running as root can remove all the permissions
        # of the directory mounted into the container (e.g. ``chmod 700`` owned by root).
        doc_path = self.project.doc_path
        os.makedirs(doc_path)
        with open(os.path.join(doc_path, "file"), "w") as f:
            f.write("content")
        os.chmod(doc_path, 0)

        def remove(path):
            # The files are removed as root, but the directory is still without permissions.
            os.chmod(path, stat.S_IRWXU)
            os.remove(os.path.join(path, "file"))
            os.chmod(path, 0)

        remove_as_root.side_effect = remove
        assert clean_build(self.version) is True
        assert not os.path.lexists(doc_path)

    @mock.patch("readthedocs.projects.tasks.utils.APIClient")
    def test_doesnt_raise_if_doc_path_is_a_symlink(self, api_client, settings, tmp_path):
        settings.DOCKER_ENABLE = True
        settings.RTD_DOCKER_COMPOSE = False
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        (outside_dir / "file.txt").write_text("content")
        os.makedirs(self.docroot)
        os.symlink(outside_dir, self.project.doc_path)

        assert clean_build(self.version) is False
        api_client.assert_not_called()
        assert (outside_dir / "file.txt").exists()


class TestRemoveAsRoot:
    @pytest.fixture(autouse=True)
    def setup(self, settings, tmp_path):
        settings.DOCROOT = str(tmp_path / "user_builds")
        settings.DOCKER_ENABLE = True
        settings.RTD_DOCKER_COMPOSE = False
        settings.RTD_DOCKER_CLONE_IMAGE = "readthedocs/build:ubuntu-22.04"
        self.path = os.path.join(settings.DOCROOT, "project")
        os.makedirs(self.path)

    @mock.patch("readthedocs.projects.tasks.utils.APIClient")
    def test_remove_as_root(self, api_client):
        client = api_client.return_value
        client.create_container.return_value = {"Id": "abc"}
        _remove_as_root(self.path)

        client.create_container.assert_called_once_with(
            image="readthedocs/build:ubuntu-22.04",
            command=["find", "/cleanup", "-mindepth", "1", "-delete"],
            user="root",
            network_disabled=True,
            host_config=client.create_host_config.return_value,
        )
        client.create_host_config.assert_called_once_with(
            binds={self.path: {"bind": "/cleanup", "mode": "rw"}},
            network_mode="none",
        )
        client.start.assert_called_once()
        client.wait.assert_called_once()
        client.remove_container.assert_called_once_with(container={"Id": "abc"}, force=True)

    @mock.patch("readthedocs.projects.tasks.utils.APIClient")
    def test_removes_container_on_error(self, api_client):
        client = api_client.return_value
        client.create_container.return_value = {"Id": "abc"}
        client.wait.side_effect = Exception("Timeout")
        _remove_as_root(self.path)
        client.remove_container.assert_called_once_with(container={"Id": "abc"}, force=True)

    @mock.patch("readthedocs.projects.tasks.utils.APIClient")
    def test_doesnt_mount_symlinks(self, api_client, tmp_path):
        link = os.path.join(os.path.dirname(self.path), "link")
        os.symlink(tmp_path, link)
        with pytest.raises(SuspiciousFileOperation):
            _remove_as_root(link)
        api_client.assert_not_called()

    @mock.patch("readthedocs.projects.tasks.utils.APIClient")
    def test_doesnt_mount_paths_outside_docroot(self, api_client, tmp_path):
        with pytest.raises(Exception):
            _remove_as_root(str(tmp_path))
        api_client.assert_not_called()

    @mock.patch("readthedocs.projects.tasks.utils.APIClient")
    def test_skip_on_docker_compose(self, api_client, settings):
        settings.RTD_DOCKER_COMPOSE = True
        _remove_as_root(self.path)
        api_client.assert_not_called()


class TestRetireBuilder:
    @mock.patch("readthedocs.projects.tasks.utils.stop_consuming_tasks_and_terminate")
    def test_retire_builder(self, stop_consuming, settings):
        settings.RTD_DOCKER_COMPOSE = False
        stop_consuming.return_value = True
        assert retire_builder(build_id=1) is True
        stop_consuming.assert_called_once_with(build_id=1)

    @mock.patch("readthedocs.projects.tasks.utils.stop_consuming_tasks_and_terminate")
    def test_dont_retire_builder_in_development(self, stop_consuming, settings):
        settings.RTD_DOCKER_COMPOSE = True
        assert retire_builder(build_id=1) is False
        stop_consuming.assert_not_called()
