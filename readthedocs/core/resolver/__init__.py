from django.conf import settings
from django.utils.module_loading import import_by_path


Resolver = import_by_path(
    getattr(settings, 'RESOLVER_CLASS',
            'readthedocs.core.resolver.backend.Resolver'))


resolver = Resolver()
resolve_path = resolver.resolve_path
resolve_domain = resolver.resolve_domain
resolve = resolver.resolve
