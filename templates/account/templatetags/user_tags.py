from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """Verifica si el usuario pertenece a un grupo específico."""
    return user.groups.filter(name=group_name).exists()