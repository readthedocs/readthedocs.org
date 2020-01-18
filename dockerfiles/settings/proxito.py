from .docker_compose import DockerBaseSettings


class ProxitoDevSettings(DockerBaseSettings):
    ROOT_URLCONF = 'readthedocs.proxito.urls'

    @property
    def MIDDLEWARE(self):  # noqa
        classes = list(super().MIDDLEWARE)
        classes.append('readthedocs.proxito.middleware.ProxitoMiddleware')
        classes.remove('django.middleware.locale.LocaleMiddleware')

        return tuple(classes)

ProxitoDevSettings.load_settings(__name__)
