from django.http.response import Http404


class ProxitoHttp404(Http404):
    def __init__(self, message, project_slug=None, project=None, subproject_slug=None):
        self.project_slug = project_slug
        self.project = project
        self.subproject_slug = subproject_slug
        super().__init__(message)
