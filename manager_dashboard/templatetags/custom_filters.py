from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, None)

@register.filter
def get_value(dictionary, key):
    return dictionary.get(key, 0)

@register.filter
def sum_values(queryset, field):
    return sum(getattr(obj, field, 0) for obj in queryset)