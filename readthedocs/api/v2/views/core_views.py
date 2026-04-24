"""Utility endpoints relating to canonical urls, embedded content, etc."""

from django.shortcuts import get_object_or_404
from rest_framework import decorators
from rest_framework import permissions
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.api.v2.permissions import HasBuildAPIKey
from readthedocs.builds.constants import LATEST
from readthedocs.core.templatetags.core_tags import make_document_url
from readthedocs.projects.models import Project


class RevokeBuildAPIKeyView(APIView):
    """
    Revoke a build API key.

    This is done by hitting the /api/v2/revoke/ endpoint with a POST request,
    while using the API key to be revoked as the authorization key.
    """

    http_method_names = ["post"]
    permission_classes = [HasBuildAPIKey]
    renderer_classes = [JSONRenderer]

    def post(self, request, *args, **kwargs):
        build_api_key = request.build_api_key
        build_api_key.revoked = True
        build_api_key.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@decorators.api_view(["GET"])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer,))
def docurl(request):
    """
    Get the url that a slug resolves to.

    Example::

        GET https://readthedocs.org/api/v2/docurl/?
          project=requests&
          version=latest&
          doc=index&
          path=index.html
    """
    project = request.GET.get("project")
    version = request.GET.get("version", LATEST)
    doc = request.GET.get("doc", "index")
    path = request.GET.get("path", "")
    if project is None:
        return Response(
            {"error": "Need project and doc"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    project = get_object_or_404(Project, slug=project)
    version = get_object_or_404(
        project.versions.public(request.user, only_active=False),
        slug=version,
    )
    return Response(
        {
            "url": make_document_url(
                project=project,
                version=version.slug,
                page=doc,
                path=path,
            ),
        }
    )
