"""Data collectors."""

import json

import structlog

log = structlog.get_logger(__name__)


class BuildDataCollector:

    """
    Build data collector.

    Collect data from a runnig build.
    """

    def __init__(self, environment):
        self.environment = environment
        self.build = self.environment.build
        self.project = self.environment.project
        self.version = self.environment.version
        self.config = self.environment.config

        log.bind(
            build_id=self.build["id"],
            project_slug=self.project.slug,
            version_slug=self.version.slug,
        )

    @staticmethod
    def _safe_json_loads(content, default=None):
        # pylint: disable=broad-except
        try:
            return json.loads(content)
        except Exception as exc:
            log.info(
                "Error while loading JSON content.",
                execption=str(exc),
            )
            return default

    def run(self, *args, **kwargs):
        build_cmd = self.environment.run(*args, record=False, **kwargs)
        return build_cmd.exit_code, build_cmd.output, build_cmd.error

    def collect(self):
        data = {}
        data["config"] = {
            "user": self.config.source_config,
        }
        data["packages"] = {
            "os": self._get_operating_system(),
            "pip": {
                "user": self._get_user_pip_packages(),
                "all": self._get_all_pip_packages(),
            },
            "conda": {
                "all": self._get_all_conda_packages(),
            },
            "apt": {
                "user": self._get_user_apt_packages(),
                "all": self._get_all_apt_packages(),
            },
        }
        return data

    def _get_all_conda_packages(self):
        """
        Get all the packages installed by the user using conda.

        This includes top level and transitive dependencies.
        The output of ``conda list`` is in the form of::

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
        code, stdout, _ = self.run(
            "conda", "list", "--json", "--name", self.version.slug
        )
        if code == 0 and stdout:
            packages = self._safe_json_loads(stdout, [])
            packages = [
                {
                    "name": package["name"],
                    "channel": package["channel"],
                    "version": package["version"],
                }
                for package in packages
            ]
            return packages
        return []

    def _get_user_pip_packages(self):
        """
        Get all the top level packages installed by the user using pip.

        The output of ``pip list`` is in the form of::

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
                },
                {
                    "name": "selectolax",
                    "version": "0.2.10"
                },
                {
                    "name": "slumber",
                    "version": "0.7.1"
                }
            ]
        """
        code, stdout, _ = self.run(
            "python",
            "-m",
            "pip",
            "list",
            "--pre",
            "--not-required",
            "--local",
            "--format",
            "json",
        )
        if code == 0 and stdout:
            return self._safe_json_loads(stdout, [])
        return []

    def _get_all_pip_packages(self):
        """
        Get all the packages installed by the user using pip.

        This includes top level and transitive dependencies.
        The output of ``pip list`` is in the form of::

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
                },
                {
                    "name": "selectolax",
                    "version": "0.2.10"
                },
                {
                    "name": "slumber",
                    "version": "0.7.1"
                }
            ]
        """
        code, stdout, _ = self.run(
            "python", "-m", "pip", "list", "--pre", "--local", "--format", "json"
        )
        if code == 0 and stdout:
            return self._safe_json_loads(stdout, [])
        return []

    def _get_operating_system(self):
        """
        Get the current operating system.

        The output of ``lsb_release --description`` is in the form of::

            Description:	Ubuntu 20.04.3 LTS
        """
        code, stdout, _ = self.run("lsb_release", "--description")
        stdout = stdout.strip()
        if code == 0 and stdout:
            prefix = "Description:"
            if stdout.startswith(prefix):
                # pep8 and blank don't agree on having a space before :.
                stdout = stdout[len(prefix) :].strip()  # noqa
            return stdout
        return ""

    def _get_all_apt_packages(self):
        """
        Get all installed apt packages and their versions.

        The output of ``dpkg --status`` is the form of::

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

        .. note:: Some lines have been removed for brevity.
        """

        def extract_value(key, line):
            if line.startswith(key):
                # pep8 and blank don't agree on having a space before :.
                return line[len(key) :].strip()  # noqa
            return ""

        code, stdout, _ = self.run("dpkg", "--status")
        stdout = stdout.strip()
        packages = []
        if code != 0 or not stdout:
            return packages

        for chunk in stdout.split("\n\n"):
            lines = chunk.split("\n")
            package = ""
            version = ""
            for line in lines:
                if not package:
                    package = extract_value("Package:", line)
                if not version:
                    version = extract_value("Version:", line)
                if package and version:
                    break
            # If the version wasn't recovered we
            # at least got the package name.
            if package:
                packages.append(
                    {
                        "name": package,
                        "version": version,
                    }
                )

        return packages

    def _get_user_apt_packages(self):
        return [
            {"name": package, "version": ""}
            for package in self.config.build.apt_packages
        ]
