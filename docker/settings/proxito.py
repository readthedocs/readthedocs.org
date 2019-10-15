from .docker import DockerBaseSettings


class ProxitoDevSettings(DockerBaseSettings):
    ROOT_URLCONF = 'readthedocs.proxito.urls'

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
