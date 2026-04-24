"""Constants for subscriptions."""

from django.utils.translation import gettext_lazy as _


# Days after the subscription has ended to disable the organization
DISABLE_AFTER_DAYS = 30

TYPE_CNAME = "cname"
TYPE_CDN = "cdn"
TYPE_SSL = "ssl"
TYPE_SUPPORT = "support"

TYPE_PRIVATE_DOCS = "private_docs"
TYPE_EMBED_API = "embed_api"
TYPE_SEARCH_ANALYTICS = "search_analytics"
TYPE_PAGEVIEW_ANALYTICS = "pageviews_analytics"
TYPE_CONCURRENT_BUILDS = "concurrent_builds"
TYPE_SSO = "sso"
TYPE_CUSTOM_URL = "urls"
TYPE_AUDIT_LOGS = "audit-logs"
TYPE_AUDIT_PAGEVIEWS = "audit-pageviews"
TYPE_REDIRECTS_LIMIT = "redirects-limit"
TYPE_SSO_SAML = "sso-saml"

FEATURE_TYPES = (
    (TYPE_CNAME, _("Custom domain")),
    (TYPE_CDN, _("CDN for public documentation")),
    (TYPE_SSL, _("Custom SSL configuration")),
    (TYPE_SUPPORT, _("Support SLA")),
    (TYPE_PRIVATE_DOCS, _("Private documentation")),
    (TYPE_EMBED_API, _("Embed content via API")),
    (TYPE_SEARCH_ANALYTICS, _("Search analytics")),
    (TYPE_PAGEVIEW_ANALYTICS, _("Pageview analytics")),
    (TYPE_CONCURRENT_BUILDS, _("Concurrent builds")),
    (TYPE_SSO, _("Single sign on (SSO) with Google")),
    (TYPE_SSO_SAML, _("Single sign on (SSO) with SAML")),
    (TYPE_CUSTOM_URL, _("Custom URLs")),
    (TYPE_AUDIT_LOGS, _("Audit logs")),
    (TYPE_AUDIT_PAGEVIEWS, _("Audit logs for every page view")),
    (TYPE_REDIRECTS_LIMIT, _("Redirects limit")),
)
