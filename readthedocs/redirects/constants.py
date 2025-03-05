from django.utils.translation import gettext_lazy as _


HTTP_STATUS_CHOICES = (
    (302, _("302 - Temporary Redirect")),
    (301, _("301 - Permanent Redirect")),
)

PAGE_REDIRECT = "page"
EXACT_REDIRECT = "exact"
CLEAN_URL_TO_HTML_REDIRECT = "clean_url_to_html"
HTML_TO_CLEAN_URL_REDIRECT = "html_to_clean_url"

TYPE_CHOICES = (
    (PAGE_REDIRECT, _("Page Redirect")),
    (EXACT_REDIRECT, _("Exact Redirect")),
    (CLEAN_URL_TO_HTML_REDIRECT, _("Clean URL to HTML (file/ to file.html)")),
    (HTML_TO_CLEAN_URL_REDIRECT, _("HTML to clean URL (file.html to file/)")),
)
