from rest_framework.routers import APIRootView
from rest_framework.routers import DefaultRouter
from rest_framework_extensions.routers import NestedRouterMixin


class DocsAPIRootView(APIRootView):
    # Overridden only to add documentation for BrowsableAPIRenderer.

    # noqa
    """
    Each request requires an `Authorization` HTTP header with `Token <your-token>`,
    find the token in [your account](/accounts/tokens/).

    Read the full documentation at <https://docs.readthedocs.io/page/api/v3.html>.
    """

    def get_view_name(self):
        return "Read the Docs API v3"


class DefaultRouterWithNesting(NestedRouterMixin, DefaultRouter):
    APIRootView = DocsAPIRootView
    root_view_name = "api-v3-root"
