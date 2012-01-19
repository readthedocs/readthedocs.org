from django.utils import simplejson as json
import httplib2

SERVER_LIST = [
'http://djangopackages.com',
'http://plone.opencomparison.org',
'http://pyramid.opencomparison.org',
]

def import_project(project):
    for BASE_SERVER in SERVER_LIST:
        API_SERVER = '%s/api/v1/' % BASE_SERVER
        sucess = False
        URL = API_SERVER + "package/%s/" % project.slug
        h = httplib2.Http(timeout=5)
        try:
            print "Trying to import from %s" % API_SERVER
            resp, content = h.request(URL, "GET")
        except AttributeError:
            print "Socket error trying to pull from Open Comparison"
        if resp['status'] == '200':
            content_dict = json.loads(content)
            project.django_packages_url = BASE_SERVER + content_dict['absolute_url']
            project.save()
            return True
    return False

def import_crate(project):
    BASE_SERVER = 'http://crate.io'
    API_SERVER = '%s/api/v1/' % BASE_SERVER
    sucess = False
    URL = API_SERVER + "package/?name__iexact=%s" % project.slug
    h = httplib2.Http(timeout=5)
    try:
        print "Trying to import from %s" % API_SERVER
        resp, content = h.request(URL, "GET")
    except AttributeError:
        print "Socket error trying to pull from Create"
    if resp['status'] == '200':
        content_dict = json.loads(content)
        project.crate_url = BASE_SERVER + content_dict['objects'][0]['absolute_url']
        print project.crate_url
        project.save()
        return True
    return False

