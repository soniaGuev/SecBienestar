# decorators.py (crear este archivo en tu app comedor)
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def admin_comedor_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Permitir acceso a staff o roles administrativos del comedor
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Verificar si el usuario tiene el rol necesario
        if hasattr(request.user, 'persona'):
            if request.user.persona.rol in ['admin_comedor', 'admin']:
                return view_func(request, *args, **kwargs)

        # Si no tiene permiso, redirigir
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')  # Cambia 'home' por tu vista principal

    return wrapper

# AUDITOR
def auditor_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        if hasattr(request.user, 'persona'):
            if request.user.persona.rol == 'auditor':
                return view_func(request, *args, **kwargs)
        else:
            # Permitir usuarios de staff sin perfil enlazado que actúan como auditores
            if request.user.is_staff:
                return view_func(request, *args, **kwargs)

        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')

    return wrapper