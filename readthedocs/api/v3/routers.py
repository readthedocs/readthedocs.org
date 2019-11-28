from rest_framework.routers import APIRootView, DefaultRouter
from rest_framework_extensions.routers import NestedRouterMixin


class DocsAPIRootView(APIRootView):

    # Overridden only to add documentation for BrowsableAPIRenderer.

    """
    Read the Docs APIv3 root endpoint.

    The API is browseable by sending the header ``Authorization: Token <token>`` on each request. You can find your Token at [https://readthedocs.org/accounts/tokens/](https://readthedocs.org/accounts/tokens/).

    Read its full documentation at [https://docs.readthedocs.io/page/api/v3.html](https://docs.readthedocs.io/page/api/v3.html).
    """  # noqa

    def get_view_name(self):
        return 'Read the Docs APIv3'


class DefaultRouterWithNesting(NestedRouterMixin, DefaultRouter):
    APIRootView = DocsAPIRootView
    root_view_name = 'api-v3-root'
