from rest_framework.renderers import BrowsableAPIRenderer


class BuildsBrowsableAPIRenderer(BrowsableAPIRenderer):
    """
    APIRenderer that does not render a raw/html form for POST.

    Builds endpoint accept the creation of a new Build object, but does not
    accept any data on body. So, we omit rendering the raw and html forms when
    browsing it.
    """

    def get_raw_data_form(self, data, view, method, request):
        if method == 'POST':
            return None
        return super().get_raw_data_form(data, view, method, request)

    def get_rendered_html_form(self, data, view, method, request):
        if method == 'POST':
            return None
        return super().get_rendered_html_form(data, view, method, request)
