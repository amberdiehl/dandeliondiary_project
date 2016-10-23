from django import template

register = template.Library()


# Returns dictionary value; usage: {{ mydict|get_item:item.NAME }}
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


# Returns array value adjusting index by -1 to assume template loop
@register.filter
def get_index(d, key):
    return d[key-1]
