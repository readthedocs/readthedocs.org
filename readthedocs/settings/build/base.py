# pylint: disable=missing-docstring

import sys


class CommunityBuildSettingsMixin:

    @classmethod
    def override_settings(cls, module_name):
        """
        Override and manipulate settings after local_settings was loaded.

        The settings defined in this class either override the anything that
        was set for the setting in local_settings module, or uses the
        local_settings settings as input (and therefore can't be set as a class
        property in this class).
        """
        self = cls()
        module = sys.modules[module_name]
        setattr(module, 'DATABASES', self.DATABASES)
        setattr(module, 'DONT_HIT_DB', self.DONT_HIT_DB)

        # Because we likely don't have a ``DOCKER_USE_DEV_IMAGES`` setting until
        # we load the local_settings file, we can't conditionally check for
        # truthiness of this setting in this class as a property. That is, this
        # class doesn't have knowledge of the setting value in local_settings.
        # After local_settings is loaded, we can inspect the module and adjust
        # the names of the Docker images.
        if getattr(module, 'DOCKER_USE_DEV_IMAGES', False):
            # Remap docker image setting keys
            docker_image_settings = {
                key.replace('readthedocs/build:', 'readthedocs/build-dev:'): settings
                for (key, settings)
                in getattr(module, 'DOCKER_IMAGE_SETTINGS', {}).items()
            }
            setattr(module, 'DOCKER_IMAGE_SETTINGS', docker_image_settings)
            # Replace default image name as well
            docker_image = getattr(module, 'DOCKER_IMAGE')
            setattr(
                module,
                'DOCKER_IMAGE',
                docker_image.replace(
                    'readthedocs/build:',
                    'readthedocs/build-dev:',
                ),
            )

    DATABASES = {
        'default': {},
    }

    DONT_HIT_DB = True
