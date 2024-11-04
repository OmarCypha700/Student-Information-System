from django import template

register = template.Library()

@register.filter
def format_number(value):
    """Formats the number with a 'K' suffix for thousands."""
    if value is None:
        return ''
    if value >= 1000:
        return f"{value / 1000:.1f}K"  # format to 1 decimal place
    return str(value)
