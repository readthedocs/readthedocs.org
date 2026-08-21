import os
import shutil
from unittest import mock

from django.conf import settings

from readthedocs.api.v2.serializers import VersionAdminSerializer
from readthedocs.builds.constants import BUILD_STATE_TRIGGERED
from readthedocs.projects.constants import MKDOCS
from readthedocs.projects.tasks.builds import UpdateDocsTask


class BuildEnvironmentMocker:
    def __init__(self, project, version, build, requestsmock):
        self.project = project
        self.version = version
        self.build = build
        self.requestsmock = requestsmock

        self.patches = {}
        self.mocks = {}

    def start(self):
        self._mock_api()
        self._mock_environment()
        self._mock_git_repository()
        self._mock_artifact_builders()
        self._mock_storage()

        # Save the mock instances to be able to check them later from inside
        # each test case.
        for k, p in self.patches.items():
            self.mocks[k] = p.start()

    def stop(self):
        for k, m in self.patches.items():
            m.stop()

    def add_file_in_repo_checkout(self, path, content):
        """
        A quick way to emulate that a file is in the repo.

        Does not change git data.
        """
        destination = os.path.join(self.project_repository_path, path)
        open(destination, "w").write(content)
        return destination

    def _mock_artifact_builders(self):
        # TODO: save the mock instances to be able to check them later
        # self.patches['builder.localmedia.move'] = mock.patch(
        #     'readthedocs.doc_builder.backends.sphinx.LocalMediaBuilder.move',
        # )

        # TODO: would be good to patch just `.run` but doing that, we are
        # raising a `BuildAppError('No TeX files were found')`
        # currently on the `.build` method
        #
        # self.patches['builder.pdf.run'] = mock.patch(
        #     'readthedocs.doc_builder.backends.sphinx.PdfBuilder.run',
        # )
        # self.patches['builder.pdf.run'] = mock.patch(
        #     'readthedocs.doc_builder.backends.sphinx.PdfBuilder.build',
        # )

        self.patches["builder.pdf.PdfBuilder.pdf_file_name"] = mock.patch(
            "readthedocs.doc_builder.backends.sphinx.PdfBuilder.pdf_file_name",
            "project-slug.pdf",
        )

        self.patches["builder.pdf.LatexBuildCommand.run"] = mock.patch(
            "readthedocs.doc_builder.backends.sphinx.LatexBuildCommand.run",
            return_value=mock.MagicMock(output="stdout", successful=True),
        )
        # self.patches['builder.pdf.LatexBuildCommand.output'] = mock.patch(
        #     'readthedocs.doc_builder.backends.sphinx.LatexBuildCommand.output',
        # )
        self.patches["builder.pdf.glob"] = mock.patch(
            "readthedocs.doc_builder.backends.sphinx.glob",
            return_value=["output.file"],
        )

        self.patches["builder.pdf.os.path.getmtime"] = mock.patch(
            "readthedocs.doc_builder.backends.sphinx.os.path.getmtime",
            return_value=1,
        )
        # NOTE: this is a problem, because it does not execute
        # `run_command_class` which does other extra stuffs, like appending the
        # commands to `environment.commands` which is used later
        self.patches["environment.run_command_class"] = mock.patch(
            "readthedocs.projects.tasks.builds.LocalBuildEnvironment.run_command_class",
            return_value=mock.MagicMock(output="stdout", successful=True),
        )

        # TODO: find a way to not mock this one and mock `open()` used inside
        # it instead to make the mock more granularly and be able to execute
        # `get_final_doctype` normally.
        self.patches["builder.html.mkdocs.MkdocsHTML.get_final_doctype"] = mock.patch(
            "readthedocs.doc_builder.backends.mkdocs.MkdocsHTML.get_final_doctype",
            return_value=MKDOCS,
        )

        # NOTE: another approach would be to make these files are in the tmpdir
        # used for testing (see ``apply_fs`` util function)
        self.patches["builder.html.sphinx.HtmlBuilder.show_conf"] = mock.patch(
            "readthedocs.doc_builder.backends.sphinx.HtmlBuilder.show_conf",
        )

    def _mock_git_repository(self):
        self.patches["git.Backend.run"] = mock.patch(
            "readthedocs.vcs_support.backends.git.Backend.run",
            return_value=(0, "stdout", "stderr"),
        )

        # TODO: improve this
        self._counter = 0

        # The tmp project repository should be at a unique location, but we need
        # to hook into test setup and teardown such that we can clean up nicely.
        # This probably means that the tmp dir should be handed to the mocker from
        # outside.
        self.project_repository_path = "/tmp/readthedocs-tests/git-repository"
        shutil.rmtree(self.project_repository_path, ignore_errors=True)
        os.makedirs(self.project_repository_path)

        self.patches["models.Project.checkout_path"] = mock.patch(
            "readthedocs.projects.models.Project.checkout_path",
            return_value=self.project_repository_path,
        )

        self.patches["git.Backend.make_clean_working_dir"] = mock.patch(
            "readthedocs.vcs_support.backends.git.Backend.make_clean_working_dir",
        )

        # Make a the backend to return 3 submodules when asked
        self.patches["git.Backend.submodules"] = mock.patch(
            "readthedocs.vcs_support.backends.git.Backend.submodules",
            new_callable=mock.PropertyMock,
            return_value=[
                "one",
                "two",
                "three",
            ],
        )
        self.patches["git.Backend.has_ssh_key_with_write_access"] = mock.patch(
            "readthedocs.vcs_support.backends.git.Backend.has_ssh_key_with_write_access",
            return_value=False,
        )

    def _mock_environment(self):
        # NOTE: by mocking `.run` we are not calling `.run_command_class`,
        # where some magic happens (passing environment variables, for
        # example). So, there are some things we cannot check with this mock
        #
        # It would be good to find a way to mock `BuildCommand.run` instead
        self.patches["environment.run"] = mock.patch(
            "readthedocs.projects.tasks.builds.LocalBuildEnvironment.run",
            return_value=mock.MagicMock(successful=True),
        )

        # self.patches['environment.run'] = mock.patch(
        #     'readthedocs.doc_builder.environments.BuildCommand.run',
        #     return_value=mock.MagicMock(successful=True)
        # )

    def _mock_storage(self):
        self.patches["get_build_media_storage_class"] = mock.patch("readthedocs.projects.tasks.storage._get_build_media_storage_class")

    def _mock_api(self):
        headers = {"Content-Type": "application/json"}

        self.requestsmock.get(
            f"{settings.SLUMBER_API_HOST}/api/v2/version/{self.version.pk}/",
            json=lambda requests, context: VersionAdminSerializer(self.version).data,
            headers=headers,
        )

        self.requestsmock.patch(
            f"{settings.SLUMBER_API_HOST}/api/v2/version/{self.version.pk}/",
            status_code=201,
        )

        self.requestsmock.get(
            f"{settings.SLUMBER_API_HOST}/api/v2/build/{self.build.pk}/",
            json=lambda request, context: {
                "id": self.build.pk,
                "state": BUILD_STATE_TRIGGERED,
                "commit": self.build.commit,
                "task_executed_at": self.build.task_executed_at,
            },
            headers=headers,
        )

        self.requestsmock.post(
            f"{settings.SLUMBER_API_HOST}/api/v2/command/",
            status_code=201,
        )

        self.requestsmock.patch(
            f"{settings.SLUMBER_API_HOST}/api/v2/build/{self.build.pk}/",
            status_code=201,
        )

        self.requestsmock.post(
            f"{settings.SLUMBER_API_HOST}/api/v2/build/{self.build.pk}/reset/",
            status_code=201,
        )

        self.requestsmock.get(
            f"{settings.SLUMBER_API_HOST}/api/v2/build/concurrent/?project__slug={self.project.slug}",
            json=lambda request, context: {
                "limit_reached": False,
                "max_concurrent": settings.RTD_MAX_CONCURRENT_BUILDS,
                "concurrent": 0,
            },
            headers=headers,
        )

        self.requestsmock.get(
            f"{settings.SLUMBER_API_HOST}/api/v2/project/{self.project.pk}/active_versions/",
            json=lambda request, context: {
                "versions": [
                    {
                        "id": self.version.pk,
                        "slug": self.version.slug,
                    },
                ]
            },
            headers=headers,
        )

        self.requestsmock.post(
            f"{settings.SLUMBER_API_HOST}/api/v2/build/{self.build.pk}/credentials/storage/",
            status_code=201,
            json={
                "s3": {
                    "access_key_id": "some-access-key",
                    "secret_access_key": "some-secret-key",
                    "session_token": "some-session-token",
                    "bucket_name": "some-bucket-name",
                    "region_name": "us-east-1",
                }
            },
            headers=headers,
        )

        self.requestsmock.patch(
            f"{settings.SLUMBER_API_HOST}/api/v2/project/{self.project.pk}/",
            status_code=201,
        )

        self.requestsmock.post(
            f"{settings.SLUMBER_API_HOST}/api/v2/revoke/",
            status_code=204,
        )

        self.requestsmock.post(
            f"{settings.SLUMBER_API_HOST}/api/v2/notifications/",
            status_code=204,
        )
