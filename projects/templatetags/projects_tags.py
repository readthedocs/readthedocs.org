from django import template

from projects.constants import HEADING_MARKUP

register = template.Library()

@register.filter
def top_level_files(project):
    return project.files.filter(parent__isnull=True)

@register.filter
def annotated_tree(queryset, max_depth=99):
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
    underline = '='
    for depth, markup in HEADING_MARKUP:
        if file_obj.depth == depth:
            underline = markup
            break
    return heading(file_obj.heading, underline)

@register.filter
def heading(heading_string, underline='='):
    return '%s\n%s' % (heading_string, underline * len(heading_string))
