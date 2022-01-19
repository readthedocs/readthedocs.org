import shutil
import os
import tempfile
from collections import namedtuple

import requests_mock
from unittest import mock

from django.conf import settings


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

        for k, p in self.patches.items():
            self.mocks[k] = p.start()

    def stop(self):
        for k, m in self.mocks.items():
            m.stop()

    def _mock_artifact_builders(self):
        # TODO: save the mock instances to be able to check them later
        # self.patches['builder.localmedia.move'] = mock.patch(
        #     'readthedocs.doc_builder.backends.sphinx.LocalMediaBuilder.move',
        # )

        # TODO: would be good to patch just `.run` but doing that, we are
        # raising a `BuildEnvironmentError('No TeX files were found')`
        # currently on the `.build` method
        #
        # self.patches['builder.pdf.run'] = mock.patch(
        #     'readthedocs.doc_builder.backends.sphinx.PdfBuilder.run',
        # )
        # self.patches['builder.pdf.run'] = mock.patch(
        #     'readthedocs.doc_builder.backends.sphinx.PdfBuilder.build',
        # )

        self.patches['builder.pdf.LatexBuildCommand.run'] = mock.patch(
            'readthedocs.doc_builder.backends.sphinx.LatexBuildCommand.run',
            return_value=mock.MagicMock(output='stdout', successful=True)
        )
        # self.patches['builder.pdf.LatexBuildCommand.output'] = mock.patch(
        #     'readthedocs.doc_builder.backends.sphinx.LatexBuildCommand.output',
        # )
        self.patches['builder.pdf.glob'] = mock.patch(
            'readthedocs.doc_builder.backends.sphinx.glob',
            return_value=['output.file'],
        )

        self.patches['builder.pdf.os.path.getmtime'] = mock.patch(
            'readthedocs.doc_builder.backends.sphinx.os.path.getmtime',
            return_value=1,
        )
        # NOTE: this is a problem, because it does not execute
        # `run_command_class` which does other extra stuffs, like appending the
        # commands to `environment.commands` which is used later
        self.patches['environment.run_command_class'] = mock.patch(
            'readthedocs.projects.tasks.builds.LocalBuildEnvironment.run_command_class',
            return_value=mock.MagicMock(output='stdout', successful=True)
        )

    def _mock_git_repository(self):
        self.patches['git.Backend.run'] = mock.patch(
            'readthedocs.vcs_support.backends.git.Backend.run',
            return_value=(0, 'stdout', 'stderr'),
        )

        # TODO: improve this
        self._counter = 0
        self.project_repository_path = '/tmp/readthedocs-tests/git-repository'
        shutil.rmtree(self.project_repository_path)
        os.makedirs(self.project_repository_path)
        mock.patch('readthedocs.projects.models.Project.checkout_path', return_value=self.project_repository_path).start()

        def _repo_exists_side_effect(*args, **kwargs):
            if self._counter == 0:
                # TODO: create a miniamal git repository nicely or mock `git.Repo` if possible
                os.system(f'cd {self.project_repository_path} && git init')
                self._counter += 1
                return False

            self._counter += 1
            return True


        self.patches['git.Backend.make_clean_working_dir'] = mock.patch(
            'readthedocs.vcs_support.backends.git.Backend.make_clean_working_dir',
        )
        self.patches['git.Backend.repo_exists'] = mock.patch(
            'readthedocs.vcs_support.backends.git.Backend.repo_exists',
            side_effect=_repo_exists_side_effect,
        )

    def _mock_environment(self):
        self.patches['environment.run'] = mock.patch(
            'readthedocs.projects.tasks.builds.LocalBuildEnvironment.run',
            return_value=mock.MagicMock(successful=True)
        )

    def _mock_api(self):
        headers = {'Content-Type': 'application/json'}

        self.requestsmock.get(
            f'{settings.SLUMBER_API_HOST}/api/v2/version/{self.version.pk}/',
            json={
                'pk': self.version.pk,
                'slug': self.version.slug,
                'project': {
                    'id': self.project.pk,
                    'slug': self.project.slug,
                    'language': self.project.language,
                    'repo_type': self.project.repo_type,
                },
                'downloads': [],
            },
            headers=headers,
        )

        self.requestsmock.patch(
            f'{settings.SLUMBER_API_HOST}/api/v2/version/{self.version.pk}/',
            status_code=201,
        )

        self.requestsmock.get(
            f'{settings.SLUMBER_API_HOST}/api/v2/build/{self.build.pk}/',
            json={
                'id': self.build.pk,
            },
            headers=headers,
        )

        self.requestsmock.post(
            f'{settings.SLUMBER_API_HOST}/api/v2/command/',
            status_code=201,
        )

        self.requestsmock.patch(
            f'{settings.SLUMBER_API_HOST}/api/v2/build/{self.build.pk}/',
            status_code=201,
        )

        self.requestsmock.get(
            f'{settings.SLUMBER_API_HOST}/api/v2/build/concurrent/?project__slug={self.project.slug}',
            json={
                'limit_reached': False,
                'max_concurrent': settings.RTD_MAX_CONCURRENT_BUILDS,
                'concurrent': 0,
            },
            headers=headers,
        )

        self.requestsmock.get(
            f'{settings.SLUMBER_API_HOST}/api/v2/project/{self.project.pk}/active_versions/',
            json={
                'versions': [
                    {
                        'id': self.version.pk,
                        'slug': self.version.slug,
                    },
                ]
            },
            headers=headers,
        )

        self.requestsmock.patch(
            f'{settings.SLUMBER_API_HOST}/api/v2/project/{self.project.pk}/',
            status_code=201,
        )
