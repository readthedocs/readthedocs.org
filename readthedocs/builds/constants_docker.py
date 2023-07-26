"""
Define constants here to allow import them without any external dependency.

There are situations where we want to have access to these values without Django installed
(e.g. common/dockerfiles/tasks.py)

Note these constants where previously defined as Django settings in ``readthedocs/settings/base.py``.
"""

DOCKER_DEFAULT_IMAGE = "readthedocs/build"

# Adding a new tool/version to this setting requires:
#
# - a mapping between the expected version in the config file, to the full
# version installed via asdf (found via ``asdf list all <tool>``)
#
# - running the script ``./scripts/compile_version_upload.sh`` in
# development and production environments to compile and cache the new
# tool/version
#
# Note that when updating this options, you should also update the file:
# readthedocs/rtd_tests/fixtures/spec/v2/schema.json
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
            "3.8": "3.8.17",
            "3.9": "3.9.17",
            "3.10": "3.10.12",
            "3.11": "3.11.4",
            # Always point to the latest stable release.
            "3": "3.11.4",
            "miniconda3-4.7": "miniconda3-4.7.12",
            "mambaforge-4.10": "mambaforge-4.10.3-10",
            "mambaforge-22.9": "mambaforge-22.9.0-3",
        },
        "nodejs": {
            "14": "14.20.1",
            "16": "16.18.1",
            "18": "18.16.1",  # LTS
            "19": "19.0.1",
            "20": "20.3.1",
        },
        "rust": {
            "1.55": "1.55.0",
            "1.61": "1.61.0",
            "1.64": "1.64.0",
            "1.70": "1.70.0",
        },
        "golang": {
            "1.17": "1.17.13",
            "1.18": "1.18.10",
            "1.19": "1.19.10",
            "1.20": "1.20.5",
        },
    },
}
