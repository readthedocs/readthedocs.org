from textwrap import dedent
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.config import BuildConfigV2
from readthedocs.doc_builder.environments import DockerBuildEnvironment
from readthedocs.projects.models import Project
from readthedocs.telemetry.collectors import BuildDataCollector


@mock.patch.object(BuildDataCollector, "run")
class TestBuildDataCollector(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, slug="test", users=[self.user])
        self.version = self.project.versions.first()
        self.environment = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={"id": 1},
            config=self._get_build_config({}),
        )
        self.collector = BuildDataCollector(self.environment)

    def _get_build_config(self, config, env_config=None):
        config = BuildConfigV2(
            env_config=env_config or {},
            raw_config=config,
            source_file="readthedocs.yaml",
        )
        config.validate()
        return config

    def test_get_operating_system(self, run):
        run.return_value = (0, "Description:\tUbuntu 20.04.3 LTS", "")
        out = self.collector._get_operating_system()
        self.assertEqual(out, "Ubuntu 20.04.3 LTS")

    def test_get_python_version(self, run):
        run.return_value = (0, "Python 3.8.12", "")
        out = self.collector._get_python_version()
        self.assertEqual(out, "3.8.12")

    def test_get_all_conda_packages(self, run):
        out = dedent(
            """
            [
                {
                    "base_url": "https://conda.anaconda.org/conda-forge",
                    "build_number": 0,
                    "build_string": "py_0",
                    "channel": "conda-forge",
                    "dist_name": "alabaster-0.7.12-py_0",
                    "name": "alabaster",
                    "platform": "noarch",
                    "version": "0.7.12"
                },
                {
                    "base_url": "https://conda.anaconda.org/conda-forge",
                    "build_number": 0,
                    "build_string": "pyh9f0ad1d_0",
                    "channel": "conda-forge",
                    "dist_name": "asn1crypto-1.4.0-pyh9f0ad1d_0",
                    "name": "asn1crypto",
                    "platform": "noarch",
                    "version": "1.4.0"
                }
            ]
            """
        )
        run.return_value = (0, out, "")
        self.assertEqual(
            self.collector._get_all_conda_packages(),
            [
                {
                    "name": "alabaster",
                    "channel": "conda-forge",
                    "version": "0.7.12",
                },
                {
                    "name": "asn1crypto",
                    "channel": "conda-forge",
                    "version": "1.4.0",
                },
            ],
        )

    def test_get_user_pip_packages(self, run):
        out = dedent(
            """
            [
                {
                    "name": "requests-mock",
                    "version": "1.8.0"
                },
                {
                    "name": "requests-toolbelt",
                    "version": "0.9.1"
                },
                {
                    "name": "rstcheck",
                    "version": "3.3.1"
                }
            ]
            """
        )
        run.return_value = (0, out, "")
        self.assertEqual(
            self.collector._get_pip_packages(include_all=False),
            [
                {"name": "requests-mock", "version": "1.8.0"},
                {"name": "requests-toolbelt", "version": "0.9.1"},
                {"name": "rstcheck", "version": "3.3.1"},
            ],
        )

    def test_get_all_pip_packages(self, run):
        out = dedent(
            """
            [
                {
                    "name": "requests-mock",
                    "version": "1.8.0"
                },
                {
                    "name": "requests-toolbelt",
                    "version": "0.9.1"
                },
                {
                    "name": "rstcheck",
                    "version": "3.3.1"
                }
            ]
            """
        )
        run.return_value = (0, out, "")
        self.assertEqual(
            self.collector._get_pip_packages(include_all=True),
            [
                {"name": "requests-mock", "version": "1.8.0"},
                {"name": "requests-toolbelt", "version": "0.9.1"},
                {"name": "rstcheck", "version": "3.3.1"},
            ],
        )

    def test_get_all_apt_packages(self, run):
        out = dedent(
            """
            apt 1.6.14
            base-files 10.1ubuntu2.11
            base-passwd 3.5.44
            bash 4.4.18-2ubuntu1.2
            bsdutils 1:2.31.1-0.4ubuntu3.7
            coreutils 8.28-1ubuntu1
            """
        )
        run.return_value = (0, out, "")
        self.assertEqual(
            self.collector._get_all_apt_packages(),
            [
                {
                    "name": "apt",
                    "version": "1.6.14",
                },
                {
                    "name": "base-files",
                    "version": "10.1ubuntu2.11",
                },
                {
                    "name": "base-passwd",
                    "version": "3.5.44",
                },
                {
                    "name": "bash",
                    "version": "4.4.18-2ubuntu1.2",
                },
                {
                    "name": "bsdutils",
                    "version": "1:2.31.1-0.4ubuntu3.7",
                },
                {
                    "name": "coreutils",
                    "version": "8.28-1ubuntu1",
                },
            ],
        )

    def test_get_user_apt_packages(self, run):
        self.collector.config = self._get_build_config(
            {"build": {"apt_packages": ["cmake", "libclang"]}}
        )
        self.assertEqual(
            self.collector._get_user_apt_packages(),
            [
                {
                    "name": "cmake",
                    "version": "",
                },
                {"name": "libclang", "version": ""},
            ],
        )
