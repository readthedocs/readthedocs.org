from .docker_compose import DockerBaseSettings


class ProxitoDevSettings(DockerBaseSettings):
    ROOT_URLCONF = 'readthedocs.proxito.urls'

    # El Proxito does not have django-debug-toolbar installed
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: False,
    }

    @property
    def MIDDLEWARE(self):  # noqa
        classes = list(super().MIDDLEWARE)
        index = classes.index(
            'readthedocs.core.middleware.SubdomainMiddleware'
        )
        # Use our new middleware instead of the old one
        classes[index] = 'readthedocs.proxito.middleware.ProxitoMiddleware'
        classes.remove('readthedocs.core.middleware.SingleVersionMiddleware')
        classes.remove('django.middleware.locale.LocaleMiddleware')

        return tuple(classes)

ProxitoDevSettings.load_settings(__name__)
