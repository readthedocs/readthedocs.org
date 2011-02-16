from django.utils import simplejson as json
import httplib2

BASE_SERVER = 'http://djangopackages.com'
API_SERVER = '%s/api/v1/' % BASE_SERVER

def import_project(project):
    URL = API_SERVER + "package/%s/" % project.slug
    h = httplib2.Http(timeout=5)
    try:
        resp, content = h.request(URL, "GET")
    except AttributeError:
        print "Socket error trying to pull from Django Packages"
        return False
    if resp['status'] == '200':
        content_dict = json.loads(content)
        project.django_packages_url = BASE_SERVER + content_dict['absolute_url']
        project.save()
        return True
    return False
