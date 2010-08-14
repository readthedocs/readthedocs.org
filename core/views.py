from projects.models import Project
from projects.tasks import update_docs
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_view_exempt

@csrf_view_exempt
def github_build(request):
    #import ipdb; ipdb.set_trace()
    obj = json.loads(request.POST['payload'])
    name = obj['repository']['name']
    url = obj['repository']['url']
    project = Project.objects.get(github_repo=url)
    update_docs.delay(github_repo=url)
    return HttpResponse('Build Started')

