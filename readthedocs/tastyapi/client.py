import logging
from django.conf import settings
from django.utils import simplejson as json
import requests

log = logging.getLogger(__name__)

SERVER_LIST = [
    'http://djangopackages.com',
    'http://plone.opencomparison.org',
    'http://pyramid.opencomparison.org',
]


def import_project(project):
    if not settings.IMPORT_EXTERNAL_DATA:
        log.debug('importing of external data is disabled')
        return False
    for BASE_SERVER in SERVER_LIST:
        API_SERVER = '%s/api/v1/' % BASE_SERVER
        URL = API_SERVER + "package/%s/" % project.slug
        try:
            log.info("Trying to import from %s" % API_SERVER)
            resp = requests.get(URL)
        except AttributeError:
            log.error("Socket error trying to pull from Open Comparison",
                      exc_info=True)
        if resp.status_code == 200:
            content_dict = json.loads(resp.content)
            project.django_packages_url = (BASE_SERVER +
                                           content_dict['absolute_url'])
            project.save()
            return True
    return False


def import_crate(project):
    if not settings.IMPORT_EXTERNAL_DATA:
        log.debug('importing of external data is disabled')
        return False
    BASE_SERVER = 'http://crate.io'
    API_SERVER = '%s/api/v1/' % BASE_SERVER
    URL = API_SERVER + "package/?name__iexact=%s" % project.slug
    try:
        log.info("Trying to import from %s" % API_SERVER)
        resp = requests.get(URL)
    except AttributeError:
        log.error("Socket error trying to pull from Crate.io", exc_info=True)
    if resp.status_code == 200:
        content_dict = json.loads(resp.content)
        if content_dict['meta']['total_count'] != 0:
            project.crate_url = (BASE_SERVER +
                                 content_dict['objects'][0]['absolute_url'])
            log.debug('Crate URL: %s' % project.crate_url)
            project.save()
            return True
    return False
