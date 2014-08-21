'''ACL views'''

from django.http import Http404

from acl.models import ProjectAccessToken
from core.views import redirect_project_slug


def token(request, token_id):
    '''View to activate session from URL token'''
    proj_token = ProjectAccessToken.get_validated_token(token_id)
    if proj_token is not None:
        request.session['access_token'] = token_id
        request.session.modified = True
        return redirect_project_slug(request, proj_token.project.slug)
    raise Http404('Access token does not exist')

