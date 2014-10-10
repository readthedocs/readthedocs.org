from django.conf import settings
from django.core.urlresolvers import reverse


def redirect_filename(project, filename=None):
    """
    Return a url for a page. Always use http for now,
    to avoid content warnings.
    """
    protocol = "http"
    # Handle explicit http redirects
    if filename.startswith(protocol):
        return filename
    version = project.get_default_version()
    lang = project.language
    use_subdomain = getattr(settings, 'USE_SUBDOMAIN', False)
    if use_subdomain:
        if project.single_version:
            return "%s://%s/%s" % (
                protocol,
                project.subdomain,
                filename,
            )
        else:
            return "%s://%s/%s/%s/%s" % (
                protocol,
                project.subdomain,
                lang,
                version,
                filename,
            )
    else:
        if project.single_version:
            return reverse('docs_detail', kwargs={
                'project_slug': project.slug,
                'filename': filename,
            })
        else:
            return reverse('docs_detail', kwargs={
                'project_slug': project.slug,
                'lang_slug': lang,
                'version_slug': version,
                'filename': filename,
            })
