from django import template

register = template.Library()


@register.filter
def get_widget_class(ob):
    return ob.__class__.__name__
