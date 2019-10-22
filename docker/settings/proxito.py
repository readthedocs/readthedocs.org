from .docker_compose import DockerBaseSettings


class ProxitoDevSettings(DockerBaseSettings):
    ROOT_URLCONF = 'readthedocs.proxito.urls'

    CACHEOPS_TIMEOUT = 60 * 60
    CACHEOPS_OPS = {'get', 'fetch'}
    CACHEOPS = {
        # readthedocs.projects.*
        'projects.project': {
            'ops': CACHEOPS_OPS,
            'timeout': CACHEOPS_TIMEOUT,
        },
        'projects.projectrelationship': {
            'ops': CACHEOPS_OPS,
            'timeout': CACHEOPS_TIMEOUT,
        },
        'projects.domain': {
            'ops': CACHEOPS_OPS,
            'timeout': CACHEOPS_TIMEOUT,
        },

        # readthedocs.builds.*
        'builds.version': {
            'ops': CACHEOPS_OPS,
            'timeout': CACHEOPS_TIMEOUT,
        },
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
