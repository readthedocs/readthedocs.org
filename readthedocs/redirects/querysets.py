"""Queryset for the redirects app."""

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects.querysets import RelatedProjectQuerySet


class RedirectQuerySetBase(RelatedProjectQuerySet):

    """Redirects take into account their own privacy_level setting."""

    use_for_related_fields = True

    def get_redirect_path_with_status(self, path, language=None, version_slug=None):
        for redirect in self.select_related('project'):
            new_path = redirect.get_redirect_path(
                path=path,
                language=language,
                version_slug=version_slug,
            )
            if new_path:
                return new_path, redirect.http_status
        return (None, None)


class RedirectQuerySet(SettingsOverrideObject):
    _default_class = RedirectQuerySetBase
