from django import template

register = template.Library()

@register.simple_tag(name="doc_url")
def make_document_url(project, version=None, page=None):
  if project.main_language_project:
    base_url =  project.get_translation_url(version)
  else:
    base_url = project.get_docs_url(version)
  ending = "/" if project.documentation_type == "sphinx_htmldir" else ".html"
  return base_url + ((page + ending) if page != "index" else "")
