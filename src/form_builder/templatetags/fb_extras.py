from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def set_this_field_type(context, field):
    # Adds to context given field type variable
    # variable named "this_field_type"

    context["this_field_type"] = field.field.__class__.__name__
    return ''
