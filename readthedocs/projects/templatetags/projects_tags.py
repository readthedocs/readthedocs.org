from django import template

from projects.constants import HEADING_MARKUP

register = template.Library()

@register.filter
def top_level_files(project):
    """
    Given a project, return only the top-level files -
    useful for generating table-of-contents, etc
    """
    return project.files.filter(parent__isnull=True)

@register.filter
def annotated_tree(queryset, max_depth=99):
    """
    Given a queryset of files, return a list of files sorted
    depth-first by the ordering provided.  Used in table of contents
    and in the project manage view.
    """
    annotated = []
    
    def walk_tree(qs, depth=1):
        for obj in qs:
            annotated.append(obj)
            if depth < max_depth:
                walk_tree(obj.children.order_by('ordering'), depth+1)
    
    walk_tree(queryset.order_by('ordering'))
    return annotated

@register.filter
def file_heading(file_obj):
    """
    Take a string, and depending on the depth, render it with the
    appropriate underlining
    """
    underline = '='
    for depth, markup in HEADING_MARKUP:
        if file_obj.depth == depth:
            underline = markup
            break
    return heading(file_obj.heading, underline)

@register.filter
def heading(heading_string, underline='='):
    """
    Takes a raw string and underlines it with the given underline char
    """
    return '%s\n%s' % (heading_string, underline * len(heading_string))

@register.filter
def sort_version_aware(versions):
    """
    Takes a list of versions objects and sort them caring about version schemes
    """
    from distutils2.version import NormalizedVersion
    from readthedocs.projects.utils import mkversion
    fallback = NormalizedVersion('99999999.0', error_on_huge_major_num=False)
    return sorted(versions, key=lambda v:(mkversion(v) or fallback), reverse=True)
