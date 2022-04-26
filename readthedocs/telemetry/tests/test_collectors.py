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
            Package: adduser
            Status: install ok installed
            Priority: important
            Section: admin
            Version: 3.118ubuntu2
            Depends: passwd, debconf (>= 0.5) | debconf-2.0
            Suggests: liblocale-gettext-perl, perl, ecryptfs-utils (>= 67-1)
            Conffiles:
            /etc/deluser.conf 773fb95e98a27947de4a95abb3d3f2a2
            Description: add and remove users and groups
            This package includes the 'adduser' and 'deluser' commands for creating
            and removing users.
            .
            - 'adduser' creates new users and groups and adds existing users to
                existing groups;
            - 'deluser' removes users and groups and removes users from a given
                group.
            .

            Package: apt
            Status: install ok installed
            Priority: important
            Section: admin
            Installed-Size: 4209
            Architecture: amd64
            Version: 2.0.6
            Replaces: apt-transport-https (<< 1.5~alpha4~), apt-utils (<< 1.3~exp2~)
            Provides: apt-transport-https (= 2.0.6)
            Depends: adduser, gpgv | gpgv2 | gpgv1, libapt-pkg6.0 (>= 2.0.6)

            Package: base-files
            Essential: yes
            Status: install ok installed
            Priority: required
            Section: admin
            Installed-Size: 392
            Architecture: amd64
            Multi-Arch: foreign
            Version: 11ubuntu5.5
            Replaces: base, dpkg (<= 1.15.0), miscutils
            Provides: base
            Depends: libc6 (>= 2.3.4), libcrypt1 (>= 1:4.4.10-10ubuntu3)
            Pre-Depends: awk
            Breaks: debian-security-support (<< 2019.04.25), initscripts (<< 2.88dsf-13.3)
            """
        )
        run.return_value = (0, out, "")
        self.assertEqual(
            self.collector._get_all_apt_packages(),
            [
                {
                    "name": "adduser",
                    "version": "3.118ubuntu2",
                },
                {
                    "name": "apt",
                    "version": "2.0.6",
                },
                {
                    "name": "base-files",
                    "version": "11ubuntu5.5",
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
