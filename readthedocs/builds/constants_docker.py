"""
Define constants here to allow import them without any external dependency.

There are situations where we want to have access to these values without Django installed
(e.g. common/dockerfiles/tasks.py)

Note these constants where previously defined as Django settings in ``readthedocs/settings/base.py``.
"""

DOCKER_DEFAULT_IMAGE = "readthedocs/build"

# When adding a new tool/version to this setting, you should:
#
# - Add a mapping between the expected version in the config file, to the full
#   version installed via asdf (found via ``asdf list all <tool>``).
# - Run the script ``./scripts/compile_version_upload.sh`` in
#   development to compile and cache the new tool/version.
# - Update the CircleCI job on the ``readthedocs-docker-images`` repository with the new versions at
#   https://github.com/rtfd/readthedocs-docker-images/blob/d2760526abdfe27001946614b749abf8011b7f90/.circleci/config.yml#L38-L44.
# - Update the latest aliases for OS and tools (below this setting).
# - Update readthedocs/rtd_tests/fixtures/spec/v2/schema.json.
# - Update the documentation in ``docs/user/config-file/v2.rst``.
RTD_DOCKER_BUILD_SETTINGS = {
    # Mapping of build.os options to docker image.
    "os": {
        "ubuntu-20.04": f"{DOCKER_DEFAULT_IMAGE}:ubuntu-20.04",
        "ubuntu-22.04": f"{DOCKER_DEFAULT_IMAGE}:ubuntu-22.04",
        "ubuntu-24.04": f"{DOCKER_DEFAULT_IMAGE}:ubuntu-24.04",
    },
    # Mapping of build.tools options to specific versions.
    "tools": {
        "python": {
            "2.7": "2.7.18",
            "3.6": "3.6.15",
            "3.7": "3.7.17",
            "3.8": "3.8.20",
            "3.9": "3.9.22",
            "3.10": "3.10.17",
            "3.11": "3.11.12",
            "3.12": "3.12.10",
            "3.13": "3.13.3",
            "3.14": "3.14.0",
            "miniconda3-4.7": "miniconda3-4.7.12",
            "miniconda3-3.12-24.1": "miniconda3-3.12-24.1.2-0",
            "miniconda3-3.12-24.9": "miniconda3-3.12-24.9.2-0",
            "mambaforge-4.10": "mambaforge-4.10.3-10",
            "mambaforge-22.9": "mambaforge-22.9.0-3",
            "mambaforge-23.11": "mambaforge-23.11.0-0",
        },
        "nodejs": {
            "14": "14.21.3",
            "16": "16.20.2",
            "18": "18.20.8",
            "19": "19.9.0",
            "20": "20.19.1",
            "22": "22.21.1",  # LTS
            "23": "23.11.1",
            "24": "24.11.1",
        },
        "ruby": {
            "3.3": "3.3.10",
            "3.4": "3.4.7",
        },
        "rust": {
            "1.55": "1.55.0",
            "1.61": "1.61.0",
            "1.64": "1.64.0",
            "1.70": "1.70.0",
            "1.75": "1.75.0",
            "1.78": "1.78.0",
            "1.82": "1.82.0",
            "1.86": "1.86.0",
            "1.91": "1.91.1",
        },
        "golang": {
            "1.17": "1.17.13",
            "1.18": "1.18.10",
            "1.19": "1.19.13",
            "1.20": "1.20.14",
            "1.21": "1.21.13",
            "1.22": "1.22.12",
            "1.23": "1.23.12",
            "1.24": "1.24.10",
            "1.25": "1.25.4",
        },
    },
}

# Set latest aliases for OS and tools.
_OS = RTD_DOCKER_BUILD_SETTINGS["os"]
_TOOLS = RTD_DOCKER_BUILD_SETTINGS["tools"]

# TODO: point ``ubuntu-lts-latest`` to Ubuntu 24.04 LTS once we have tested it
# in production after some weeks
_OS["ubuntu-lts-latest"] = _OS["ubuntu-22.04"]

_TOOLS["python"]["3"] = _TOOLS["python"]["3.14"]
_TOOLS["python"]["latest"] = _TOOLS["python"]["3"]
_TOOLS["python"]["miniconda-latest"] = _TOOLS["python"]["miniconda3-3.12-24.9"]
_TOOLS["python"]["mambaforge-latest"] = _TOOLS["python"]["mambaforge-23.11"]
_TOOLS["nodejs"]["latest"] = _TOOLS["nodejs"]["24"]
_TOOLS["ruby"]["latest"] = _TOOLS["ruby"]["3.4"]
_TOOLS["rust"]["latest"] = _TOOLS["rust"]["1.91"]
_TOOLS["golang"]["latest"] = _TOOLS["golang"]["1.25"]
