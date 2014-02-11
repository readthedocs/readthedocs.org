from django import template

register = template.Library()

@register.simple_tag(name="doc_url")
def make_document_url(project, version=None, page=None):
  if project.main_language_project:
    return project.get_translation_url(version) + page
  else:
    return project.get_docs_url(version) + page
