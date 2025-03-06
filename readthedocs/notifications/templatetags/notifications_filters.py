from django import template


register = template.Library()


@register.filter
def to_class_name(value):
    """Output the name of the class for the given object."""
    return value.__class__.__name__
