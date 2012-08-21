import logging
from django.utils import simplejson as json
import httplib2

log = logging.getLogger(__name__)

SERVER_LIST = [
'http://djangopackages.com',
'http://plone.opencomparison.org',
'http://pyramid.opencomparison.org',
]

def import_project(project):
    for BASE_SERVER in SERVER_LIST:
        API_SERVER = '%s/api/v1/' % BASE_SERVER
        success = False
        URL = API_SERVER + "package/%s/" % project.slug
        h = httplib2.Http(timeout=5)
        try:
            log.info("Trying to import from %s" % API_SERVER)
            resp, content = h.request(URL, "GET")
        except AttributeError:
            log.error("Socket error trying to pull from Open Comparison", exc_info=True)
        if resp['status'] == '200':
            content_dict = json.loads(content)
            project.django_packages_url = BASE_SERVER + content_dict['absolute_url']
            project.save()
            return True
    return False

def import_crate(project):
    BASE_SERVER = 'http://crate.io'
    API_SERVER = '%s/api/v1/' % BASE_SERVER
    success = False
    URL = API_SERVER + "package/?name__iexact=%s" % project.slug
    h = httplib2.Http(timeout=5)
    try:
        log.info("Trying to import from %s" % API_SERVER)
        resp, content = h.request(URL, "GET")
    except AttributeError:
        log.error("Socket error trying to pull from Crate.io", exc_info=True)
    if resp['status'] == '200':
        content_dict = json.loads(content)
        if content_dict['meta']['total_count'] != 0:
            project.crate_url = BASE_SERVER + content_dict['objects'][0]['absolute_url']
            log.debug('Crate URL: %s' % project.crate_url)
            project.save()
            return True
    return False

