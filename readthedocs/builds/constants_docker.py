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
#   development and production environments to compile and cache the new
#   tool/version.
# - Update the latest aliases for OS and tools (below this setting).
# - Update readthedocs/rtd_tests/fixtures/spec/v2/schema.json.
# - Update the documentation in ``docs/user/config-file/v2.rst``.
RTD_DOCKER_BUILD_SETTINGS = {
    # Mapping of build.os options to docker image.
    "os": {
        "ubuntu-20.04": f"{DOCKER_DEFAULT_IMAGE}:ubuntu-20.04",
        "ubuntu-22.04": f"{DOCKER_DEFAULT_IMAGE}:ubuntu-22.04",
    },
    # Mapping of build.tools options to specific versions.
    "tools": {
        "python": {
            "2.7": "2.7.18",
            "3.6": "3.6.15",
            "3.7": "3.7.17",
            "3.8": "3.8.18",
            "3.9": "3.9.18",
            "3.10": "3.10.13",
            "3.11": "3.11.6",
            "3.12": "3.12.0",
            "miniconda3-4.7": "miniconda3-4.7.12",
            "mambaforge-4.10": "mambaforge-4.10.3-10",
            "mambaforge-22.9": "mambaforge-22.9.0-3",
        },
        "nodejs": {
            "14": "14.20.1",
            "16": "16.18.1",
            "18": "18.16.1",
            "19": "19.0.1",
            "20": "20.11.0",  # LTS
        },
        "rust": {
            "1.55": "1.55.0",
            "1.61": "1.61.0",
            "1.64": "1.64.0",
            "1.70": "1.70.0",
            "1.75": "1.75.0",
        },
        "golang": {
            "1.17": "1.17.13",
            "1.18": "1.18.10",
            "1.19": "1.19.10",
            "1.20": "1.20.5",
            "1.21": "1.21.6",
        },
    },
}

# Set latest aliases for OS and tools.
RTD_DOCKER_BUILD_SETTINGS["os"]["ubuntu-latest-lts"] = RTD_DOCKER_BUILD_SETTINGS["os"]["ubuntu-20.04"]
RTD_DOCKER_BUILD_SETTINGS["tools"]["python"]["3"] = RTD_DOCKER_BUILD_SETTINGS["tools"]["python"]["3.12"]
RTD_DOCKER_BUILD_SETTINGS["tools"]["python"]["latest"] = RTD_DOCKER_BUILD_SETTINGS["tools"]["python"]["3"]
RTD_DOCKER_BUILD_SETTINGS["tools"]["python"]["miniconda-latest"] = RTD_DOCKER_BUILD_SETTINGS["tools"]["python"]["miniconda3-4.7"]
RTD_DOCKER_BUILD_SETTINGS["tools"]["python"]["mambaforge-latest"] = RTD_DOCKER_BUILD_SETTINGS["tools"]["python"]["mambaforge-22.9"]
RTD_DOCKER_BUILD_SETTINGS["tools"]["nodejs"]["latest"] = RTD_DOCKER_BUILD_SETTINGS["tools"]["nodejs"]["20"]
RTD_DOCKER_BUILD_SETTINGS["tools"]["rust"]["latest"] = RTD_DOCKER_BUILD_SETTINGS["tools"]["rust"]["1.75"]
RTD_DOCKER_BUILD_SETTINGS["tools"]["golang"]["latest"] = RTD_DOCKER_BUILD_SETTINGS["tools"]["golang"]["1.21"]
