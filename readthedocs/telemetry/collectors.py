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
        except Exception:
            log.info(
                "Error while loading JSON content.",
                exc_info=True,
            )
            return default

    def run(self, *args, **kwargs):
        build_cmd = self.environment.run(*args, record=False, demux=True, **kwargs)
        return build_cmd.exit_code, build_cmd.output, build_cmd.error

    def collect(self):
        """
        Collect all relevant data from the runnig build.

        Data that can be extracted from the database (project/organization)
        isn't collected here.
        """
        data = {}
        data["config"] = {"user": self.config.source_config}
        data["os"] = self._get_operating_system()
        data["python"] = self._get_python_version()

        user_apt_packages, all_apt_packages = self._get_apt_packages()
        data["packages"] = {
            "pip": {
                "user": self._get_pip_packages(include_all=False),
                "all": self._get_pip_packages(include_all=True),
            },
            "conda": {
                "all": self._get_all_conda_packages(),
            },
            "apt": {
                "user": user_apt_packages,
                "all": all_apt_packages,
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

    def _get_pip_packages(self, include_all=False):
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
        cmd = ["python", "-m", "pip", "list", "--pre", "--local", "--format", "json"]
        if not include_all:
            cmd.append("--not-required")
        code, stdout, _ = self.run(*cmd)
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
            parts = stdout.split("\t")
            if len(parts) == 2:
                return parts[1]
        return ""

    def _get_apt_packages(self):
        """
        Get the list of installed apt packages (global and from the user).

        The current source of user installed packages is the config file,
        but we have only the name, so we take the version from the list of all
        installed packages.
        """
        all_apt_packages = self._get_all_apt_packages()
        all_apt_packages_dict = {
            package["name"]: package["version"] for package in all_apt_packages
        }
        user_apt_packages = self._get_user_apt_packages()
        for package in user_apt_packages:
            package["version"] = all_apt_packages_dict.get(package["name"], "")
        return user_apt_packages, all_apt_packages

    def _get_all_apt_packages(self):
        """
        Get all installed apt packages and their versions.

        The output of ``dpkg-query --show`` is the form of::

            adduser 3.116ubuntu1
            apt 1.6.14
            base-files 10.1ubuntu2.11
            base-passwd 3.5.44
            bash 4.4.18-2ubuntu1.2
            bsdutils 1:2.31.1-0.4ubuntu3.7
            bzip2 1.0.6-8.1ubuntu0.2
            coreutils 8.28-1ubuntu1
            dash 0.5.8-2.10
            debconf 1.5.66ubuntu1
            debianutils 4.8.4
            diffutils 1:3.6-1
            dpkg 1.19.0.5ubuntu2.3
            e2fsprogs 1.44.1-1ubuntu1.3
            fdisk 2.31.1-0.4ubuntu3.7
            findutils 4.6.0+git+20170828-2
            gcc-8-base 8.4.0-1ubuntu1~18.04
            gpgv 2.2.4-1ubuntu1.4
            grep 3.1-2build1
            gzip 1.6-5ubuntu1.2
            hostname 3.20
        """
        code, stdout, _ = self.run(
            "dpkg-query", "--showformat", "${package} ${version}\\n", "--show"
        )
        stdout = stdout.strip()
        packages = []
        if code != 0 or not stdout:
            return packages

        for line in stdout.split("\n"):
            parts = line.split()
            if len(parts) == 2:
                package, version = parts
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

    def _get_python_version(self):
        """
        Get the python version currently used.

        The output of ``python --version`` is in the form of::

            Python 3.8.12
        """
        code, stdout, _ = self.run("python", "--version")
        stdout = stdout.strip()
        if code == 0 and stdout:
            parts = stdout.split()
            if len(parts) == 2:
                return parts[1]
        return ""
