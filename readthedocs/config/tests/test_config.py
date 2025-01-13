import os
import re
import textwrap
from collections import OrderedDict
from contextlib import nullcontext as does_not_raise

import pytest
from django.conf import settings
from django.test import override_settings
from pytest import raises

from readthedocs.config import ALL, PIP, SETUPTOOLS, BuildConfigV2, load
from readthedocs.config.config import CONFIG_FILENAME_REGEX
from readthedocs.config.exceptions import ConfigError, ConfigValidationError
from readthedocs.config.models import (
    BuildJobs,
    BuildJobsBuildTypes,
    BuildWithOs,
    PythonInstall,
    PythonInstallRequirements,
)

from .utils import apply_fs


def get_build_config(config, source_file="readthedocs.yml", validate=False, **kwargs):
    # I'm adding these defaults here to avoid modifying all the config file from all the tests
    final_config = {
        "version": "2",
        "build": {
            "os": "ubuntu-22.04",
            "tools": {
                "python": "3",
            },
        },
    }
    final_config.update(config)

    build_config = BuildConfigV2(
        final_config,
        source_file=source_file,
        **kwargs,
    )
    if validate:
        build_config.validate()

    return build_config


@pytest.mark.parametrize(
    "files",
    [
        {"readthedocs.ymlmore": ""},
        {"first": {"readthedocs.yml": ""}},
        {"startreadthedocs.yml": ""},
        {"second": {"confuser.txt": "content"}},
        {"noroot": {"readthedocs.ymlmore": ""}},
        {"third": {"readthedocs.yml": "content", "Makefile": ""}},
        {"noroot": {"startreadthedocs.yml": ""}},
        {"fourth": {"samplefile.yaml": "content"}},
        {"readthebots.yaml": ""},
        {"fifth": {"confuser.txt": "", "readthedocs.yml": "content"}},
    ],
)
def test_load_no_config_file(tmpdir, files):
    apply_fs(tmpdir, files)
    base = str(tmpdir)
    with raises(ConfigError) as e:
        with override_settings(DOCROOT=tmpdir):
            load(base, {})
    assert e.value.message_id == ConfigError.DEFAULT_PATH_NOT_FOUND


def test_load_empty_config_file(tmpdir):
    apply_fs(
        tmpdir,
        {
            "readthedocs.yml": "",
        },
    )
    base = str(tmpdir)
    with raises(ConfigError):
        with override_settings(DOCROOT=tmpdir):
            load(base, {})


def test_load_version2(tmpdir):
    apply_fs(
        tmpdir,
        {
            "readthedocs.yml": textwrap.dedent(
                """
            version: 2
            build:
              os: "ubuntu-22.04"
              tools:
                python: "3"
        """
            ),
        },
    )
    base = str(tmpdir)
    with override_settings(DOCROOT=tmpdir):
        build = load(base, {})
    assert isinstance(build, BuildConfigV2)


def test_load_unknow_version(tmpdir):
    apply_fs(
        tmpdir,
        {
            "readthedocs.yml": textwrap.dedent(
                """
            version: 9
        """
            ),
        },
    )
    base = str(tmpdir)
    with raises(ConfigError) as excinfo:
        with override_settings(DOCROOT=tmpdir):
            load(base, {})
    assert excinfo.value.message_id == ConfigError.INVALID_VERSION


def test_load_raise_exception_invalid_syntax(tmpdir):
    apply_fs(
        tmpdir,
        {
            "readthedocs.yml": textwrap.dedent(
                """
                version: 2
                python:
                  install:
                    - method: pip
                      path: .
                        # bad indentation here
                        extra_requirements:
                          - build
            """
            ),
        },
    )
    base = str(tmpdir)
    with raises(ConfigError) as excinfo:
        with override_settings(DOCROOT=tmpdir):
            load(base, {})
    assert excinfo.value.message_id == ConfigError.SYNTAX_INVALID


def test_load_non_default_filename(tmpdir):
    """
    Load a config file name with a non-default name.

    Verifies that we can load a custom config path and that an existing default config file is
    correctly ignored.

    Note: Our CharField validator for readthedocs_yaml_path currently ONLY allows a file to be
    called .readthedocs.yaml.
    This test just verifies that the loader doesn't care since we support different file names
    in the backend.
    """
    non_default_filename = "myconfig.yaml"
    apply_fs(
        tmpdir,
        {
            non_default_filename: textwrap.dedent(
                """
                version: 2
                build:
                  os: "ubuntu-22.04"
                  tools:
                    python: "3"
                """
            ),
            ".readthedocs.yaml": "illegal syntax but should not load",
        },
    )
    base = str(tmpdir)
    with override_settings(DOCROOT=tmpdir):
        build = load(base, readthedocs_yaml_path="myconfig.yaml")
    assert isinstance(build, BuildConfigV2)
    assert build.source_file == os.path.join(base, non_default_filename)


def test_load_non_yaml_extension(tmpdir):
    """
    Load a config file name from non-default path.

    In this version, we verify that we can handle non-yaml extensions
    because we allow the user to do that.

    See docstring of test_load_non_default_filename.
    """
    non_default_filename = ".readthedocs.skrammel"
    apply_fs(
        tmpdir,
        {
            "subdir": {
                non_default_filename: textwrap.dedent(
                    """
                    version: 2
                    build:
                      os: "ubuntu-22.04"
                      tools:
                        python: "3"
                    """
                ),
            },
            ".readthedocs.yaml": "illegal syntax but should not load",
        },
    )
    base = str(tmpdir)
    with override_settings(DOCROOT=tmpdir):
        build = load(base, readthedocs_yaml_path="subdir/.readthedocs.skrammel")
    assert isinstance(build, BuildConfigV2)
    assert build.source_file == os.path.join(base, "subdir/.readthedocs.skrammel")


@pytest.mark.parametrize(
    "correct_config_filename",
    [
        prefix + "readthedocs." + extension
        for prefix in {"", "."}
        for extension in {"yml", "yaml"}
    ],
)
def test_config_filenames_regex(correct_config_filename):
    assert re.match(CONFIG_FILENAME_REGEX, correct_config_filename)


class TestBuildConfigV2:
    def test_version(self):
        build = get_build_config({})
        assert build.version == "2"

    def test_formats_check_valid(self):
        build = get_build_config({"formats": ["htmlzip", "pdf", "epub"]})
        build.validate()
        assert build.formats == ["htmlzip", "pdf", "epub"]

    @pytest.mark.parametrize("value", [3, "invalid", {"other": "value"}])
    def test_formats_check_invalid_value(self, value):
        build = get_build_config({"formats": value})
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_LIST
        assert excinfo.value.format_values.get("key") == "formats"

    def test_formats_check_invalid_type(self):
        build = get_build_config(
            {"formats": ["htmlzip", "invalid", "epub"]},
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_CHOICE
        assert excinfo.value.format_values.get("key") == "formats"

    def test_formats_default_value(self):
        build = get_build_config({})
        build.validate()
        assert build.formats == []

    # TODO: remove/adapt all these tests that use "defaults".
    # I'm removing them from the code since we don't need them anymore.
    def test_formats_overrides_default_values(self):
        build = get_build_config(
            {},
        )
        build.validate()
        assert build.formats == []

    def test_formats_priority_over_defaults(self):
        build = get_build_config(
            {"formats": []},
        )
        build.validate()
        assert build.formats == []

        build = get_build_config(
            {"formats": ["pdf"]},
        )
        build.validate()
        assert build.formats == ["pdf"]

    def test_formats_allow_empty(self):
        build = get_build_config({"formats": []})
        build.validate()
        assert build.formats == []

    def test_formats_allow_all_keyword(self):
        build = get_build_config({"formats": "all"})
        build.validate()
        assert build.formats == ["htmlzip", "pdf", "epub"]

    def test_conda_check_valid(self, tmpdir):
        apply_fs(tmpdir, {"environment.yml": ""})
        build = get_build_config(
            {"conda": {"environment": "environment.yml"}},
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        build.validate()
        assert build.conda.environment == "environment.yml"

    def test_conda_key_required_for_conda_mamba(self):
        build = get_build_config(
            {
                "build": {
                    "os": "ubuntu-22.04",
                    "tools": {
                        "python": "miniconda3-4.7",
                    },
                },
            }
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigError.CONDA_KEY_REQUIRED
        assert excinfo.value.format_values.get("key") == "conda"

    def test_conda_key_not_required_for_conda_mamba_when_build_commands(self):
        build = get_build_config(
            {
                "build": {
                    "os": "ubuntu-22.04",
                    "tools": {
                        "python": "mambaforge-22.9",
                    },
                    "commands": [
                        "mamba env create --file environment.yml",
                    ],
                },
            }
        )
        with does_not_raise(ConfigError):
            build.validate()

    @pytest.mark.parametrize("value", [3, [], "invalid"])
    def test_conda_check_invalid_value(self, value):
        build = get_build_config({"conda": value})
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_DICT
        assert excinfo.value.format_values.get("key") == "conda"

    @pytest.mark.parametrize("value", [3, [], {}])
    def test_conda_check_invalid_file_value(self, value):
        build = get_build_config({"conda": {"file": value}})
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.VALUE_NOT_FOUND
        assert excinfo.value.format_values.get("key") == "conda.environment"

    def test_conda_check_file_required(self):
        build = get_build_config({"conda": {"no-file": "other"}})
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.VALUE_NOT_FOUND
        assert excinfo.value.format_values.get("key") == "conda.environment"

    @pytest.mark.parametrize("value", [3, [], "invalid"])
    def test_build_check_invalid_type(self, value):
        build = get_build_config({"build": value})
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_DICT
        assert excinfo.value.format_values.get("key") == "build"

    @pytest.mark.parametrize("value", [3, [], {}])
    def test_build_image_check_invalid_type(self, value):
        build = get_build_config({"build": {"image": value}})
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.VALUE_NOT_FOUND
        assert excinfo.value.format_values.get("key") == "build.os"

    @pytest.mark.parametrize("value", ["", None, "latest"])
    def test_new_build_config_invalid_os(self, value):
        build = get_build_config(
            {
                "build": {
                    "os": value,
                    "tools": {"python": "3"},
                },
            },
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_CHOICE
        assert excinfo.value.format_values.get("key") == "build.os"

    @pytest.mark.parametrize(
        "value", ["", None, "python", ["python", "nodejs"], {}, {"cobol": "99"}]
    )
    def test_new_build_config_invalid_tools(self, value):
        build = get_build_config(
            {
                "build": {
                    "os": "ubuntu-20.04",
                    "tools": value,
                },
            },
        )
        with raises(ConfigError) as excinfo:
            build.validate()

        # TODO: split this test to check specific errors now we have better messages
        assert excinfo.value.message_id in (
            ConfigError.NOT_BUILD_TOOLS_OR_COMMANDS,
            ConfigValidationError.INVALID_DICT,
            ConfigValidationError.VALUE_NOT_FOUND,
            ConfigValidationError.INVALID_CHOICE,
        )
        assert excinfo.value.format_values.get("key") in ("build.tools", "build")

    def test_new_build_config_invalid_tools_version(self):
        build = get_build_config(
            {
                "build": {
                    "os": "ubuntu-20.04",
                    "tools": {"python": "2.6"},
                },
            },
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_CHOICE
        assert excinfo.value.format_values.get("key") == "build.tools.python"
        assert excinfo.value.format_values.get("choices") == ", ".join(
            settings.RTD_DOCKER_BUILD_SETTINGS["tools"]["python"].keys()
        )

    def test_new_build_config(self):
        build = get_build_config(
            {
                "build": {
                    "os": "ubuntu-20.04",
                    "tools": {"python": "3.9"},
                },
            },
        )
        build.validate()
        assert isinstance(build.build, BuildWithOs)
        assert build.build.os == "ubuntu-20.04"
        assert build.build.tools["python"].version == "3.9"
        full_version = settings.RTD_DOCKER_BUILD_SETTINGS["tools"]["python"]["3.9"]
        assert build.build.tools["python"].full_version == full_version
        assert build.python_interpreter == "python"

    def test_new_build_config_conflict_with_build_image(self):
        build = get_build_config(
            {
                "build": {
                    "image": "latest",
                    "os": "ubuntu-20.04",
                    "tools": {"python": "3.9"},
                },
            },
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigError.INVALID_KEY_NAME
        assert excinfo.value.format_values.get("key") == "build.image"

    def test_new_build_config_conflict_with_build_python_version(self):
        build = get_build_config(
            {
                "build": {
                    "os": "ubuntu-20.04",
                    "tools": {"python": "3.8"},
                },
                "python": {"version": "3.8"},
            },
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigError.INVALID_KEY_NAME
        assert excinfo.value.format_values.get("key") == "python.version"

    def test_commands_build_config_tools_and_commands_valid(self):
        """
        Test that build.tools and build.commands are valid together.
        """
        build = get_build_config(
            {
                "build": {
                    "os": "ubuntu-20.04",
                    "tools": {"python": "3.8"},
                    "commands": ["pip install pelican", "pelican content"],
                },
            },
        )
        build.validate()
        assert isinstance(build.build, BuildWithOs)
        assert build.build.commands == ["pip install pelican", "pelican content"]

    def test_build_jobs_without_build_os_is_invalid(self):
        """
        build.jobs can't be used without build.os
        """
        build = get_build_config(
            {
                "build": {
                    "tools": {"python": "3.8"},
                    "jobs": {
                        "pre_checkout": ["echo pre_checkout"],
                    },
                },
            },
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.VALUE_NOT_FOUND
        assert excinfo.value.format_values.get("key") == "build.os"

    def test_commands_build_config_invalid_command(self):
        build = get_build_config(
            {
                "build": {
                    "os": "ubuntu-20.04",
                    "tools": {"python": "3.8"},
                    "commands": "command as string",
                },
            },
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_LIST
        assert excinfo.value.format_values.get("key") == "build.commands"

    def test_commands_build_config_invalid_no_os(self):
        build = get_build_config(
            {
                "build": {
                    "commands": ["pip install pelican", "pelican content"],
                },
            },
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.VALUE_NOT_FOUND
        assert excinfo.value.format_values.get("key") == "build.os"

    def test_commands_build_config_valid(self):
        """It's valid to build with just build.os and build.commands."""
        build = get_build_config(
            {
                "build": {
                    "os": "ubuntu-22.04",
                    "commands": ["echo 'hello world' > _readthedocs/html/index.html"],
                },
            },
        )
        build.validate()
        assert isinstance(build.build, BuildWithOs)
        assert build.build.commands == [
            "echo 'hello world' > _readthedocs/html/index.html"
        ]

    @pytest.mark.parametrize("value", ["", None, "pre_invalid"])
    def test_jobs_build_config_invalid_jobs(self, value):
        build = get_build_config(
            {
                "build": {
                    "os": "ubuntu-20.04",
                    "tools": {"python": "3.8"},
                    "jobs": {value: ["echo 1234", "git fetch --unshallow"]},
                },
            },
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_CHOICE
        assert excinfo.value.format_values.get("key") == "build.jobs"

    @pytest.mark.parametrize("value", ["", None, "echo 123", 42])
    def test_jobs_build_config_invalid_job_commands(self, value):
        build = get_build_config(
            {
                "build": {
                    "os": "ubuntu-20.04",
                    "tools": {"python": "3.8"},
                    "jobs": {
                        "pre_install": value,
                    },
                },
            },
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_LIST
        assert excinfo.value.format_values.get("key") == "build.jobs.pre_install"

    def test_jobs_build_config(self):
        build = get_build_config(
            {
                "build": {
                    "os": "ubuntu-20.04",
                    "tools": {"python": "3.8"},
                    "jobs": {
                        "pre_checkout": ["echo pre_checkout"],
                        "post_checkout": ["echo post_checkout"],
                        "pre_system_dependencies": ["echo pre_system_dependencies"],
                        "post_system_dependencies": ["echo post_system_dependencies"],
                        "pre_create_environment": ["echo pre_create_environment"],
                        "post_create_environment": ["echo post_create_environment"],
                        "pre_install": ["echo pre_install", "echo `date`"],
                        "post_install": ["echo post_install"],
                        "pre_build": [
                            "echo pre_build",
                            'sed -i -e "s|{VERSION}|${READTHEDOCS_VERSION_NAME}|g"',
                        ],
                        "post_build": ["echo post_build"],
                    },
                },
            },
        )
        build.validate()
        assert isinstance(build.build, BuildWithOs)
        assert isinstance(build.build.jobs, BuildJobs)
        assert build.build.jobs.pre_checkout == ["echo pre_checkout"]
        assert build.build.jobs.post_checkout == ["echo post_checkout"]
        assert build.build.jobs.pre_system_dependencies == [
            "echo pre_system_dependencies"
        ]
        assert build.build.jobs.post_system_dependencies == [
            "echo post_system_dependencies"
        ]
        assert build.build.jobs.pre_create_environment == [
            "echo pre_create_environment"
        ]
        assert build.build.jobs.create_environment is None
        assert build.build.jobs.post_create_environment == [
            "echo post_create_environment"
        ]
        assert build.build.jobs.pre_install == ["echo pre_install", "echo `date`"]
        assert build.build.jobs.install is None
        assert build.build.jobs.post_install == ["echo post_install"]
        assert build.build.jobs.pre_build == [
            "echo pre_build",
            'sed -i -e "s|{VERSION}|${READTHEDOCS_VERSION_NAME}|g"',
        ]
        assert build.build.jobs.build == BuildJobsBuildTypes()
        assert build.build.jobs.post_build == ["echo post_build"]

    def test_build_jobs_partial_override(self):
        build = get_build_config(
            {
                "formats": ["pdf", "htmlzip", "epub"],
                "build": {
                    "os": "ubuntu-20.04",
                    "tools": {"python": "3"},
                    "jobs": {
                        "create_environment": ["echo make_environment"],
                        "install": ["echo install"],
                        "build": {
                            "html": ["echo build html"],
                            "pdf": ["echo build pdf"],
                            "epub": ["echo build epub"],
                            "htmlzip": ["echo build htmlzip"],
                        },
                    },
                },
            },
        )
        build.validate()
        assert isinstance(build.build, BuildWithOs)
        assert isinstance(build.build.jobs, BuildJobs)
        assert build.build.jobs.create_environment == ["echo make_environment"]
        assert build.build.jobs.install == ["echo install"]
        assert build.build.jobs.build.html == ["echo build html"]
        assert build.build.jobs.build.pdf == ["echo build pdf"]
        assert build.build.jobs.build.epub == ["echo build epub"]
        assert build.build.jobs.build.htmlzip == ["echo build htmlzip"]

    def test_build_jobs_build_should_match_formats(self):
        build = get_build_config(
            {
                "formats": ["pdf"],
                "build": {
                    "os": "ubuntu-24.04",
                    "tools": {"python": "3"},
                    "jobs": {
                        "build": {
                            "epub": ["echo build epub"],
                        },
                    },
                },
            },
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert (
            excinfo.value.message_id
            == ConfigError.BUILD_JOBS_BUILD_TYPE_MISSING_IN_FORMATS
        )

    def test_build_jobs_build_defaults(self):
        build = get_build_config(
            {
                "build": {
                    "os": "ubuntu-24.04",
                    "tools": {"python": "3"},
                    "jobs": {
                        "build": {
                            "html": ["echo build html"],
                        },
                    },
                },
            },
        )
        build.validate()
        assert build.build.jobs.build.html == ["echo build html"]
        assert build.build.jobs.build.pdf is None
        assert build.build.jobs.build.htmlzip is None
        assert build.build.jobs.build.epub is None

    def test_build_jobs_partial_override_empty_commands(self):
        build = get_build_config(
            {
                "formats": ["pdf"],
                "build": {
                    "os": "ubuntu-24.04",
                    "tools": {"python": "3"},
                    "jobs": {
                        "create_environment": [],
                        "install": [],
                        "build": {
                            "html": [],
                            "pdf": [],
                        },
                    },
                },
            },
        )
        build.validate()
        assert isinstance(build.build, BuildWithOs)
        assert isinstance(build.build.jobs, BuildJobs)
        assert build.build.jobs.create_environment == []
        assert build.build.jobs.install == []
        assert build.build.jobs.build.html == []
        assert build.build.jobs.build.pdf == []
        assert build.build.jobs.build.epub == None
        assert build.build.jobs.build.htmlzip == None

    @pytest.mark.parametrize(
        "value",
        [
            [],
            ["cmatrix"],
            ["Mysql", "cmatrix", "postgresql-dev"],
        ],
    )
    def test_build_apt_packages_check_valid(self, value):
        build = get_build_config(
            {
                "build": {
                    "os": "ubuntu-22.04",
                    "tools": {"python": "3"},
                    "apt_packages": value,
                }
            }
        )
        build.validate()

        assert build.build.apt_packages == value

    @pytest.mark.parametrize(
        "value",
        [3, "string", {}],
    )
    def test_build_apt_packages_invalid_type(self, value):
        build = get_build_config(
            {
                "build": {
                    "os": "ubuntu-22.04",
                    "tools": {"python": "3"},
                    "apt_packages": value,
                }
            }
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_LIST
        assert excinfo.value.format_values.get("key") == "build.apt_packages"

    @pytest.mark.parametrize(
        "error_index, value",
        [
            (0, ["/", "cmatrix"]),
            (1, ["cmatrix", "-q"]),
            (1, ["cmatrix", " -q"]),
            (1, ["cmatrix", "\\-q"]),
            (1, ["cmatrix", "--quiet"]),
            (1, ["cmatrix", " --quiet"]),
            (2, ["cmatrix", "quiet", "./package.deb"]),
            (2, ["cmatrix", "quiet", " ./package.deb "]),
            (2, ["cmatrix", "quiet", "/home/user/package.deb"]),
            (2, ["cmatrix", "quiet", " /home/user/package.deb"]),
            (2, ["cmatrix", "quiet", "../package.deb"]),
            (2, ["cmatrix", "quiet", " ../package.deb"]),
            (1, ["one", "$two"]),
            (1, ["one", "non-ascíí"]),
            # We don't allow regex for now.
            (1, ["mysql", "cmatrix$"]),
            (0, ["^mysql-*", "cmatrix$"]),
            # We don't allow specifying versions for now.
            (0, ["postgresql=1.2.3"]),
            # We don't allow specifying distributions for now.
            (0, ["cmatrix/bionic"]),
        ],
    )
    def test_build_apt_packages_invalid_value(self, error_index, value):
        build = get_build_config(
            {
                "build": {
                    "os": "ubuntu-22.04",
                    "tools": {"python": "3"},
                    "apt_packages": value,
                }
            }
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id in (
            ConfigError.APT_INVALID_PACKAGE_NAME,
            ConfigError.APT_INVALID_PACKAGE_NAME_PREFIX,
        )
        assert (
            excinfo.value.format_values.get("key")
            == f"build.apt_packages.{error_index}"
        )

    @pytest.mark.parametrize("value", [3, [], "invalid"])
    def test_python_check_invalid_types(self, value):
        build = get_build_config({"python": value})
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_DICT
        assert excinfo.value.format_values.get("key") == "python"

    @pytest.mark.parametrize("value", [[], {}, "3", "3.10"])
    def test_python_version_check_invalid_types(self, value):
        build = get_build_config({"python": {"version": value}})
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigError.INVALID_KEY_NAME
        assert excinfo.value.format_values.get("key") == "python.version"

    def test_python_install_default_value(self):
        build = get_build_config({})
        build.validate()
        install = build.python.install
        assert len(install) == 0

    def test_python_install_check_default(self, tmpdir):
        build = get_build_config(
            {
                "python": {
                    "install": [
                        {
                            "path": ".",
                        }
                    ],
                },
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert isinstance(install[0], PythonInstall)
        assert install[0].path == "."
        assert install[0].method == PIP
        assert install[0].extra_requirements == []

    @pytest.mark.parametrize("value", ["invalid", "apt"])
    def test_python_install_method_check_invalid(self, value, tmpdir):
        build = get_build_config(
            {
                "python": {
                    "install": [
                        {
                            "path": ".",
                            "method": value,
                        }
                    ],
                },
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_CHOICE
        assert excinfo.value.format_values.get("key") == "python.install.0.method"

    def test_python_install_requirements_check_valid(self, tmpdir):
        apply_fs(tmpdir, {"requirements.txt": ""})
        build = get_build_config(
            {
                "python": {
                    "install": [{"requirements": "requirements.txt"}],
                },
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert isinstance(install[0], PythonInstallRequirements)
        assert install[0].requirements == "requirements.txt"

    def test_python_install_requirements_does_not_allow_null(self, tmpdir):
        build = get_build_config(
            {
                "python": {
                    "install": [
                        {
                            "path": ".",
                            "requirements": None,
                        }
                    ],
                },
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_STRING
        assert excinfo.value.format_values.get("key") == "python.install.0.requirements"

    def test_python_install_requirements_error_msg(self, tmpdir):
        build = get_build_config(
            {
                "python": {
                    "install": [
                        {
                            "path": ".",
                            "requirements": None,
                        }
                    ],
                },
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        with raises(ConfigError) as excinfo:
            build.validate()

        assert str(excinfo.value) == "Build user exception"
        # assert registry.get()
        #     == 'Invalid configuration option "python.install[0].requirements": expected string'

    def test_python_install_requirements_does_not_allow_empty_string(self, tmpdir):
        build = get_build_config(
            {
                "python": {
                    "install": [
                        {
                            "path": ".",
                            "requirements": "",
                        }
                    ],
                },
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_PATH
        assert excinfo.value.format_values.get("key") == "python.install.0.requirements"

    @pytest.mark.parametrize("value", [3, [], {}])
    def test_python_install_requirements_check_invalid_types(self, value, tmpdir):
        build = get_build_config(
            {
                "python": {
                    "install": [
                        {
                            "path": ".",
                            "requirements": value,
                        }
                    ],
                },
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_STRING
        assert excinfo.value.format_values.get("key") == "python.install.0.requirements"

    def test_python_install_path_is_required(self, tmpdir):
        build = get_build_config(
            {
                "python": {
                    "install": [
                        {
                            "method": "pip",
                        }
                    ],
                },
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigError.PIP_PATH_OR_REQUIREMENT_REQUIRED
        assert excinfo.value.format_values.get("key") == "python.install.0"

    def test_python_install_pip_check_valid(self, tmpdir):
        build = get_build_config(
            {
                "python": {
                    "install": [
                        {
                            "path": ".",
                            "method": "pip",
                        }
                    ],
                },
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert install[0].path == "."
        assert install[0].method == PIP

    def test_python_install_setuptools_check_valid(self, tmpdir):
        build = get_build_config(
            {
                "python": {
                    "install": [
                        {
                            "path": ".",
                            "method": "setuptools",
                        }
                    ],
                },
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert install[0].path == "."
        assert install[0].method == SETUPTOOLS

    def test_python_install_allow_empty_list(self):
        build = get_build_config(
            {"python": {"install": []}},
        )
        build.validate()
        assert build.python.install == []

    def test_python_install_default(self):
        build = get_build_config({"python": {}})
        build.validate()
        assert build.python.install == []

    @pytest.mark.parametrize("value", [2, "string", {}])
    def test_python_install_check_invalid_type(self, value):
        build = get_build_config(
            {"python": {"install": value}},
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_LIST
        assert excinfo.value.format_values.get("key") == "python.install"

    def test_python_install_extra_requirements_and_pip(self, tmpdir):
        build = get_build_config(
            {
                "python": {
                    "install": [
                        {
                            "path": ".",
                            "method": "pip",
                            "extra_requirements": ["docs", "tests"],
                        }
                    ],
                },
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert install[0].extra_requirements == ["docs", "tests"]

    def test_python_install_extra_requirements_and_setuptools(self, tmpdir):
        build = get_build_config(
            {
                "python": {
                    "install": [
                        {
                            "path": ".",
                            "method": "setuptools",
                            "extra_requirements": ["docs", "tests"],
                        }
                    ],
                }
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigError.USE_PIP_FOR_EXTRA_REQUIREMENTS

    @pytest.mark.parametrize("value", [2, "invalid", {}, "", None])
    def test_python_install_extra_requirements_check_type(self, value, tmpdir):
        build = get_build_config(
            {
                "python": {
                    "install": [
                        {
                            "path": ".",
                            "method": "pip",
                            "extra_requirements": value,
                        }
                    ],
                },
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_LIST
        assert (
            excinfo.value.format_values.get("key")
            == "python.install.0.extra_requirements"
        )

    def test_python_install_extra_requirements_allow_empty(self, tmpdir):
        build = get_build_config(
            {
                "python": {
                    "install": [
                        {
                            "path": ".",
                            "method": "pip",
                            "extra_requirements": [],
                        }
                    ],
                },
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert install[0].extra_requirements == []

    def test_python_install_several_respects_order(self, tmpdir):
        apply_fs(
            tmpdir,
            {
                "one": {},
                "two": {},
                "three.txt": "",
            },
        )
        build = get_build_config(
            {
                "python": {
                    "install": [
                        {
                            "path": "one",
                            "method": "pip",
                            "extra_requirements": [],
                        },
                        {
                            "path": "two",
                            "method": "setuptools",
                        },
                        {
                            "requirements": "three.txt",
                        },
                    ],
                },
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 3

        assert install[0].path == "one"
        assert install[0].method == PIP
        assert install[0].extra_requirements == []

        assert install[1].path == "two"
        assert install[1].method == SETUPTOOLS

        assert install[2].requirements == "three.txt"

    @pytest.mark.parametrize("value", [[], True, 0, "invalid"])
    def test_sphinx_validate_type(self, value):
        build = get_build_config({"sphinx": value})
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_DICT
        assert excinfo.value.format_values.get("key") == "sphinx"

    def test_sphinx_is_default_doc_type(self):
        build = get_build_config({})
        build.validate()
        assert build.sphinx is not None
        assert build.mkdocs is None
        assert build.doctype == "sphinx"

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("html", "sphinx"),
            ("htmldir", "sphinx_htmldir"),
            ("dirhtml", "sphinx_htmldir"),
            ("singlehtml", "sphinx_singlehtml"),
        ],
    )
    def test_sphinx_builder_check_valid(self, value, expected):
        build = get_build_config(
            {"sphinx": {"builder": value}},
        )
        build.validate()
        assert build.sphinx.builder == expected
        assert build.doctype == expected

    @pytest.mark.parametrize("value", [[], True, 0, "invalid"])
    def test_sphinx_builder_check_invalid(self, value):
        build = get_build_config({"sphinx": {"builder": value}})
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_CHOICE
        assert excinfo.value.format_values.get("key") == "sphinx.builder"

    def test_sphinx_builder_default(self):
        build = get_build_config({})
        build.validate()
        build.sphinx.builder == "sphinx"

    def test_sphinx_builder_ignores_default(self):
        build = get_build_config(
            {},
        )
        build.validate()
        build.sphinx.builder == "sphinx"

    def test_sphinx_configuration_check_valid(self, tmpdir):
        apply_fs(tmpdir, {"conf.py": ""})
        build = get_build_config(
            {"sphinx": {"configuration": "conf.py"}},
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        build.validate()
        assert build.sphinx.configuration == "conf.py"

    def test_sphinx_cant_be_used_with_mkdocs(self, tmpdir):
        apply_fs(tmpdir, {"conf.py": ""})
        build = get_build_config(
            {
                "sphinx": {"configuration": "conf.py"},
                "mkdocs": {},
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigError.SPHINX_MKDOCS_CONFIG_TOGETHER

    def test_sphinx_configuration_allow_null(self):
        build = get_build_config(
            {"sphinx": {"configuration": None}},
        )
        build.validate()
        assert build.sphinx.configuration is None

    def test_sphinx_configuration_check_default(self):
        build = get_build_config({})
        build.validate()
        assert build.sphinx.configuration is None

    @pytest.mark.parametrize("value", [[], True, 0, {}])
    def test_sphinx_configuration_validate_type(self, value):
        build = get_build_config(
            {"sphinx": {"configuration": value}},
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_STRING
        assert excinfo.value.format_values.get("key") == "sphinx.configuration"

    @pytest.mark.parametrize("value", [True, False])
    def test_sphinx_fail_on_warning_check_valid(self, value):
        build = get_build_config({"sphinx": {"fail_on_warning": value}})
        build.validate()
        assert build.sphinx.fail_on_warning is value

    @pytest.mark.parametrize("value", [[], "invalid", 5])
    def test_sphinx_fail_on_warning_check_invalid(self, value):
        build = get_build_config({"sphinx": {"fail_on_warning": value}})
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_BOOL
        assert excinfo.value.format_values.get("key") == "sphinx.fail_on_warning"

    def test_sphinx_fail_on_warning_check_default(self):
        build = get_build_config({})
        build.validate()
        assert build.sphinx.fail_on_warning is False

    @pytest.mark.parametrize("value", [[], True, 0, "invalid"])
    def test_mkdocs_validate_type(self, value):
        build = get_build_config({"mkdocs": value})
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_DICT
        assert excinfo.value.format_values.get("key") == "mkdocs"

    def test_mkdocs_default(self):
        build = get_build_config({})
        build.validate()
        assert build.mkdocs is None

    def test_mkdocs_configuration_check_valid(self, tmpdir):
        apply_fs(tmpdir, {"mkdocs.yml": ""})
        build = get_build_config(
            {"mkdocs": {"configuration": "mkdocs.yml"}},
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        build.validate()
        assert build.mkdocs.configuration == "mkdocs.yml"
        assert build.doctype == "mkdocs"
        assert build.sphinx is None

    def test_mkdocs_configuration_allow_null(self):
        build = get_build_config(
            {"mkdocs": {"configuration": None}},
        )
        build.validate()
        assert build.mkdocs.configuration is None

    def test_mkdocs_configuration_check_default(self):
        build = get_build_config(
            {"mkdocs": {}},
        )
        build.validate()
        assert build.mkdocs.configuration is None

    @pytest.mark.parametrize("value", [[], True, 0, {}])
    def test_mkdocs_configuration_validate_type(self, value):
        build = get_build_config(
            {"mkdocs": {"configuration": value}},
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_STRING
        assert excinfo.value.format_values.get("key") == "mkdocs.configuration"

    @pytest.mark.parametrize("value", [True, False])
    def test_mkdocs_fail_on_warning_check_valid(self, value):
        build = get_build_config(
            {"mkdocs": {"fail_on_warning": value}},
        )
        build.validate()
        assert build.mkdocs.fail_on_warning is value

    @pytest.mark.parametrize("value", [[], "invalid", 5])
    def test_mkdocs_fail_on_warning_check_invalid(self, value):
        build = get_build_config(
            {"mkdocs": {"fail_on_warning": value}},
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_BOOL
        assert excinfo.value.format_values.get("key") == "mkdocs.fail_on_warning"

    def test_mkdocs_fail_on_warning_check_default(self):
        build = get_build_config(
            {"mkdocs": {}},
        )
        build.validate()
        assert build.mkdocs.fail_on_warning is False

    def test_submodule_defaults(self):
        build = get_build_config({})
        build.validate()
        assert build.submodules.include == []
        assert build.submodules.exclude == ALL
        assert build.submodules.recursive is False

    @pytest.mark.parametrize("value", [[], "invalid", 0])
    def test_submodules_check_invalid_type(self, value):
        build = get_build_config({"submodules": value})
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_DICT
        assert excinfo.value.format_values.get("key") == "submodules"

    def test_submodules_include_check_valid(self):
        build = get_build_config(
            {
                "submodules": {
                    "include": ["one", "two"],
                },
            }
        )
        build.validate()
        assert build.submodules.include == ["one", "two"]
        assert build.submodules.exclude == []
        assert build.submodules.recursive is False

    @pytest.mark.parametrize("value", ["invalid", True, 0, {}])
    def test_submodules_include_check_invalid(self, value):
        build = get_build_config(
            {
                "submodules": {
                    "include": value,
                },
            }
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_LIST
        assert excinfo.value.format_values.get("key") == "submodules.include"

    def test_submodules_include_allows_all_keyword(self):
        build = get_build_config(
            {
                "submodules": {
                    "include": "all",
                },
            }
        )
        build.validate()
        assert build.submodules.include == ALL
        assert build.submodules.exclude == []
        assert build.submodules.recursive is False

    def test_submodules_exclude_check_valid(self):
        build = get_build_config(
            {
                "submodules": {
                    "exclude": ["one", "two"],
                },
            }
        )
        build.validate()
        assert build.submodules.include == []
        assert build.submodules.exclude == ["one", "two"]
        assert build.submodules.recursive is False

    @pytest.mark.parametrize("value", ["invalid", True, 0, {}])
    def test_submodules_exclude_check_invalid(self, value):
        build = get_build_config(
            {
                "submodules": {
                    "exclude": value,
                },
            }
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_LIST
        assert excinfo.value.format_values.get("key") == "submodules.exclude"

    def test_submodules_exclude_allows_all_keyword(self):
        build = get_build_config(
            {
                "submodules": {
                    "exclude": "all",
                },
            }
        )
        build.validate()
        assert build.submodules.include == []
        assert build.submodules.exclude == ALL
        assert build.submodules.recursive is False

    def test_submodules_cant_exclude_and_include(self):
        build = get_build_config(
            {
                "submodules": {
                    "include": ["two"],
                    "exclude": ["one"],
                },
            }
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert (
            excinfo.value.message_id == ConfigError.SUBMODULES_INCLUDE_EXCLUDE_TOGETHER
        )

    def test_submodules_can_exclude_include_be_empty(self):
        build = get_build_config(
            {
                "submodules": {
                    "exclude": "all",
                    "include": [],
                },
            }
        )
        build.validate()
        assert build.submodules.include == []
        assert build.submodules.exclude == ALL
        assert build.submodules.recursive is False

    @pytest.mark.parametrize("value", [True, False])
    def test_submodules_recursive_check_valid(self, value):
        build = get_build_config(
            {
                "submodules": {
                    "include": ["one", "two"],
                    "recursive": value,
                },
            }
        )
        build.validate()
        assert build.submodules.include == ["one", "two"]
        assert build.submodules.exclude == []
        assert build.submodules.recursive is value

    @pytest.mark.parametrize("value", [[], "invalid", 5])
    def test_submodules_recursive_check_invalid(self, value):
        build = get_build_config(
            {
                "submodules": {
                    "include": ["one", "two"],
                    "recursive": value,
                },
            }
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_BOOL
        assert excinfo.value.format_values.get("key") == "submodules.recursive"

    def test_submodules_recursive_explicit_default(self):
        build = get_build_config(
            {
                "submodules": {
                    "include": [],
                    "recursive": False,
                },
            }
        )
        build.validate()
        assert build.submodules.include == []
        assert build.submodules.exclude == ALL
        assert build.submodules.recursive is False

        build = get_build_config(
            {
                "submodules": {
                    "exclude": [],
                    "recursive": False,
                },
            }
        )
        build.validate()
        assert build.submodules.include == []
        assert build.submodules.exclude == []
        assert build.submodules.recursive is False

    @pytest.mark.parametrize("value", ["invalid", True, 0, []])
    def test_search_invalid_type(self, value):
        build = get_build_config(
            {
                "search": value,
            }
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id == ConfigValidationError.INVALID_DICT
        assert excinfo.value.format_values.get("key") == "search"

    @pytest.mark.parametrize(
        "value",
        [
            "invalid",
            True,
            0,
            [],
            {"foo/bar": 11},
            {"foo/bar": -11},
            {"foo/bar": 2.5},
            {"foo/bar": "bar"},
            {"/": 1},
            {"/foo/..": 1},
            {"..": 1},
            {"/foo/bar/../../../": 1},
            {10: "bar"},
            {10: 0},
        ],
    )
    def test_search_ranking_invalid_type(self, value):
        build = get_build_config(
            {
                "search": {"ranking": value},
            }
        )
        with raises(ConfigError) as excinfo:
            build.validate()

        # TODO: these test should be split to validate the exact ``message_id``
        assert excinfo.value.message_id in (
            ConfigValidationError.INVALID_DICT,
            ConfigValidationError.INVALID_CHOICE,
            ConfigValidationError.INVALID_PATH_PATTERN,
            ConfigValidationError.INVALID_STRING,
        )

        assert excinfo.value.format_values.get("key") == "search.ranking"

    @pytest.mark.parametrize("value", list(range(-10, 10 + 1)))
    def test_search_valid_ranking(self, value):
        build = get_build_config(
            {
                "search": {
                    "ranking": {
                        "foo/bar": value,
                        "bar/foo": value,
                    },
                },
            }
        )
        build.validate()
        assert build.search.ranking == {"foo/bar": value, "bar/foo": value}

    @pytest.mark.parametrize(
        "path, expected",
        [
            ("/foo/bar", "foo/bar"),
            ("///foo//bar", "foo/bar"),
            ("///foo//bar/", "foo/bar"),
            ("/foo/bar/../", "foo"),
            ("/foo*", "foo*"),
            ("/foo/bar/*", "foo/bar/*"),
            ("/foo/bar?/*", "foo/bar?/*"),
            ("foo/[bc]ar/*/", "foo/[bc]ar/*"),
            ("*", "*"),
            ("index.html", "index.html"),
        ],
    )
    def test_search_ranking_normilize_path(self, path, expected):
        build = get_build_config(
            {
                "search": {
                    "ranking": {
                        path: 1,
                    },
                },
            }
        )
        build.validate()
        assert build.search.ranking == {expected: 1}

    @pytest.mark.parametrize(
        "value",
        [
            "invalid",
            True,
            0,
            [2, 3],
            {"foo/bar": 11},
        ],
    )
    def test_search_ignore_invalid_type(self, value):
        build = get_build_config(
            {
                "search": {"ignore": value},
            }
        )
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id in (
            ConfigValidationError.INVALID_LIST,
            ConfigValidationError.INVALID_STRING,
        )
        assert excinfo.value.format_values.get("key") == "search.ignore"

    @pytest.mark.parametrize(
        "path, expected",
        [
            ("/foo/bar", "foo/bar"),
            ("///foo//bar", "foo/bar"),
            ("///foo//bar/", "foo/bar"),
            ("/foo/bar/../", "foo"),
            ("/foo*", "foo*"),
            ("/foo/bar/*", "foo/bar/*"),
            ("/foo/bar?/*", "foo/bar?/*"),
            ("foo/[bc]ar/*/", "foo/[bc]ar/*"),
            ("*", "*"),
            ("index.html", "index.html"),
        ],
    )
    def test_search_ignore_valid_type(self, path, expected):
        build = get_build_config(
            {
                "search": {
                    "ignore": [path],
                },
            }
        )
        build.validate()
        assert build.search.ignore == [expected]

    @pytest.mark.parametrize(
        "value,key",
        [
            ({"typo": "something"}, "typo"),
            (
                {
                    "pyton": {
                        "version": "another typo",
                    }
                },
                "pyton.version",
            ),
            (
                {
                    "build": {
                        "os": "ubuntu-22.04",
                        "tools": {"python": "3"},
                        "extra": "key",
                    }
                },
                "build.extra",
            ),
            (
                {
                    "python": {
                        "install": [
                            {
                                "path": ".",
                            },
                            {
                                "path": ".",
                                "method": "pip",
                                "invalid": "key",
                            },
                        ]
                    }
                },
                "python.install.1.invalid",
            ),
        ],
    )
    def test_strict_validation(self, value, key):
        build = get_build_config(value)
        with raises(ConfigError) as excinfo:
            build.validate()
        assert excinfo.value.message_id in (
            ConfigError.INVALID_KEY_NAME,
            ConfigValidationError.INVALID_BOOL,
        )
        assert excinfo.value.format_values.get("key") == key

    @pytest.mark.parametrize(
        "value,expected",
        [
            ({}, []),
            ({"one": 1}, ["one"]),
            ({"one": {"two": 3}}, ["one", "two"]),
            (OrderedDict([("one", 1), ("two", 2)]), ["one"]),
            (OrderedDict([("one", {"two": 2}), ("three", 3)]), ["one", "two"]),
        ],
    )
    def test_get_extra_key(self, value, expected):
        build = get_build_config({})
        assert build._get_extra_key(value) == expected

    def test_pop_config_single(self):
        build = get_build_config({})
        build.pop_config("version")
        build.pop_config("build")
        assert build._raw_config == {}

    def test_pop_config_nested(self):
        build = get_build_config({})
        build.pop_config("version")
        build.pop_config("build.os")
        build.pop_config("build.tools")
        assert build._raw_config == {}

    def test_pop_config_nested_with_residue(self):
        build = get_build_config({})
        build.pop_config("version")
        build.pop_config("build.tools")
        assert build._raw_config == {"build": {"os": "ubuntu-22.04"}}

    def test_pop_config_default_none(self):
        build = get_build_config({})
        assert build.pop_config("one.four") is None

    def test_pop_config_default(self):
        build = get_build_config({})
        assert build.pop_config("one.four", 4) == 4

    def test_pop_config_raise_exception(self):
        build = get_build_config({})
        with raises(ConfigValidationError) as excinfo:
            build.pop_config("build.invalid", raise_ex=True)
        assert excinfo.value.format_values.get("value") == "invalid"
        assert excinfo.value.message_id == ConfigValidationError.VALUE_NOT_FOUND

    def test_sphinx_without_explicit_configuration(self):
        data = {
            "sphinx": {},
        }
        get_build_config(data, validate=True)

        with raises(ConfigError) as excinfo:
            get_build_config(data, validate=True, deprecate_implicit_keys=True)

        assert excinfo.value.message_id == ConfigError.SPHINX_CONFIG_MISSING

        data["sphinx"]["configuration"] = "conf.py"
        get_build_config(data, validate=True, deprecate_implicit_keys=True)

    def test_mkdocs_without_explicit_configuration(self):
        data = {
            "mkdocs": {},
        }
        get_build_config(data, validate=True)

        with raises(ConfigError) as excinfo:
            get_build_config(data, validate=True, deprecate_implicit_keys=True)

        assert excinfo.value.message_id == ConfigError.MKDOCS_CONFIG_MISSING

        data["mkdocs"]["configuration"] = "mkdocs.yml"
        get_build_config(data, validate=True, deprecate_implicit_keys=True)

    def test_config_without_sphinx_key(self):
        data = {
            "build": {
                "os": "ubuntu-22.04",
                "tools": {
                    "python": "3",
                },
                "jobs": {},
            },
        }
        get_build_config(data, validate=True)

        with raises(ConfigError) as excinfo:
            get_build_config(data, validate=True, deprecate_implicit_keys=True)

        assert excinfo.value.message_id == ConfigError.SPHINX_CONFIG_MISSING

        # No exception should be raised when overriding any of the the new jobs.
        data_copy = data.copy()
        data_copy["build"]["jobs"]["create_environment"] = ["echo 'Hello World'"]
        get_build_config(data_copy, validate=True, deprecate_implicit_keys=True)

        data_copy = data.copy()
        data_copy["build"]["jobs"]["install"] = ["echo 'Hello World'"]
        get_build_config(data_copy, validate=True, deprecate_implicit_keys=True)

        data_copy = data.copy()
        data_copy["build"]["jobs"]["build"] = {"html": ["echo 'Hello World'"]}
        get_build_config(data_copy, validate=True, deprecate_implicit_keys=True)

    def test_sphinx_and_mkdocs_arent_required_when_using_build_commands(self):
        data = {
            "build": {
                "os": "ubuntu-22.04",
                "tools": {
                    "python": "3",
                },
                "commands": ["echo 'Hello World'"],
            },
        }
        get_build_config(data, validate=True, deprecate_implicit_keys=True)

    def test_as_dict_new_build_config(self, tmpdir):
        build = get_build_config(
            {
                "version": 2,
                "formats": ["pdf"],
                "build": {
                    "os": "ubuntu-20.04",
                    "tools": {
                        "python": "3.9",
                        "nodejs": "16",
                    },
                },
                "python": {
                    "install": [
                        {
                            "requirements": "requirements.txt",
                        }
                    ],
                },
            },
            source_file=str(tmpdir.join("readthedocs.yml")),
        )
        build.validate()
        expected_dict = {
            "version": "2",
            "formats": ["pdf"],
            "python": {
                "install": [
                    {
                        "requirements": "requirements.txt",
                    }
                ],
            },
            "build": {
                "os": "ubuntu-20.04",
                "tools": {
                    "python": {
                        "version": "3.9",
                        "full_version": settings.RTD_DOCKER_BUILD_SETTINGS["tools"][
                            "python"
                        ]["3.9"],
                    },
                    "nodejs": {
                        "version": "16",
                        "full_version": settings.RTD_DOCKER_BUILD_SETTINGS["tools"][
                            "nodejs"
                        ]["16"],
                    },
                },
                "commands": [],
                "jobs": {
                    "pre_checkout": [],
                    "post_checkout": [],
                    "pre_system_dependencies": [],
                    "post_system_dependencies": [],
                    "pre_create_environment": [],
                    "create_environment": None,
                    "post_create_environment": [],
                    "pre_install": [],
                    "install": None,
                    "post_install": [],
                    "pre_build": [],
                    "build": {
                        "html": None,
                        "pdf": None,
                        "epub": None,
                        "htmlzip": None,
                    },
                    "post_build": [],
                },
                "apt_packages": [],
            },
            "conda": None,
            "sphinx": {
                "builder": "sphinx",
                "configuration": None,
                "fail_on_warning": False,
            },
            "mkdocs": None,
            "doctype": "sphinx",
            "submodules": {
                "include": [],
                "exclude": ALL,
                "recursive": False,
            },
            "search": {
                "ranking": {},
                "ignore": [
                    "search.html",
                    "search/index.html",
                    "404.html",
                    "404/index.html",
                ],
            },
        }
        assert build.as_dict() == expected_dict
