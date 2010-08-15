from django import template

register = template.Library()

@register.filter
def top_level_files(project):
    return project.files.filter(parent__isnull=True)

@register.filter
def annotated_tree(project, max_depth=99):
    annotated = []
    def walk_tree(qs, depth=1):
        for obj in qs:
            obj.depth = depth
            annotated.append(obj)
            if depth < max_depth:
                walk_tree(obj.children.order_by('ordering'), depth+1)
    walk_tree(project.files.filter(parent__isnull=True).order_by('ordering'))
    return annotated

@register.filter
def headline(headline_string):
    return '%s\n%s' % (headline_string, '=' * len(headline_string))
