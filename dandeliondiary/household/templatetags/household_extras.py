from django import template

register = template.Library()


@register.filter
def get_index(d, key):
    return d[key-1]


@register.filter
def get_widget_class(ob):
    return ob.__class__.__name__


# Not currently used but returns dictionary value; usage: {{ mydict|get_item:item.NAME }}
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
