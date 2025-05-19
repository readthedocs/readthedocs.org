"""An API to load config from a readthedocs.yml file."""

from readthedocs.config import load as load_config


def load_yaml_config(version, readthedocs_yaml_path=None):
    """
    Load a build configuration file (`.readthedocs.yaml`).

    This uses the configuration logic from `readthedocs-build`, which will keep
    parsing consistent between projects.

    :param readthedocs_yaml_path: Optionally, we are told which readthedocs_yaml_path to
                                  load instead of using defaults.
    """
    checkout_path = version.project.checkout_path(version.slug)

    # TODO: review this function since we are removing all the defaults for BuildConfigV2 as well.
    # NOTE: all the configuration done on the UI will make no effect at all from now on.

    # Get build image to set up the python version validation. Pass in the
    # build image python limitations to the loaded config so that the versions
    # can be rejected at validation

    config = load_config(
        path=checkout_path,
        readthedocs_yaml_path=readthedocs_yaml_path,
    )
    return config
