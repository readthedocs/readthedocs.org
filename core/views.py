from projects.models import Project
#from projects.tasks import update_docs
import json
from django.http import HttpResponse


def github_build(request):
    obj = json.loads(request.POST['payload'])
    name = obj['repository']['name']
    url = obj['repository']['url']
    project = Project.objects.get(github_repo=url)
    #update_docs.delay(github_repo=url)
    return HttpResponse('Build Started')

