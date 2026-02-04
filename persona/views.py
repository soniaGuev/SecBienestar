from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Prefetch
from comedor.decorators import admin_comedor_required, auditor_required
from .models import (
    Persona, PersonaEstudiante, PersonaDocente, PersonaNoDocente,
    Observacion, PersonaBeca, Dependencia, Carrera, Area
)
from .forms import (
    PersonaForm, PersonaEstudianteForm, PersonaDocenteForm,
    PersonaNoDocenteForm, ObservacionForm
)
import json
from datetime import datetime

@admin_comedor_required
def panel_persona(request):
    return render(request, 'persona/panel_persona.html')

def registrar_cambio(persona, usuario, cambios_dict, accion='modificacion', request=None):
    """
    Función auxiliar para registrar cambios en el modelo Observacion

    Args:
        persona: Instancia de Persona
        usuario: Usuario que realiza el cambio
        cambios_dict: Dict con formato {campo: {'anterior': valor, 'nuevo': valor}}
        accion: Tipo de acción realizada
        request: Request para obtener IP y user agent
    """
    if not cambios_dict:
        return

    # Crear descripción legible
    descripcion_partes = []
    for campo, valores in cambios_dict.items():
        descripcion_partes.append(
            f"{campo}: '{valores.get('anterior', 'N/A')}' → '{valores.get('nuevo', 'N/A')}'"
        )

    descripcion = "\n".join(descripcion_partes)

    observacion_texto = f"[{accion.upper()}] Cambios realizados por {usuario.get_full_name() or usuario.username}"

    Observacion.objects.create(
        persona=persona,
        observacion=observacion_texto,
        usuario=usuario,
        descripcion_cambio=descripcion,
        tipo_accion=accion,
        datos_modificados=cambios_dict
    )


@admin_comedor_required
def listar_personas(request):
    """Lista todas las personas del sistema con filtros"""

    # Filtros
    search_query = request.GET.get('search', '')
    rol_filter = request.GET.get('rol', '')
    sede_filter = request.GET.get('sede', '')

    # Query base
    personas = Persona.objects.select_related('usuario').all()

    # Aplicar búsqueda
    if search_query:
        personas = personas.filter(
            Q(nombre__icontains=search_query) |
            Q(apellido__icontains=search_query) |
            Q(nombre_percibido__icontains=search_query) |
            Q(documento__icontains=search_query) |
            Q(correo__icontains=search_query)
        )

    # Filtrar por rol
    if rol_filter:
        personas = personas.filter(rol=rol_filter)

    # Filtrar por sede
    if sede_filter:
        personas = personas.filter(sede=sede_filter)

    personas = personas.order_by('apellido', 'nombre')

    # Estadísticas
    total_personas = personas.count()
    por_rol = {}
    for rol_code, rol_name in Persona.ROLES:
        count = personas.filter(rol=rol_code).count()
        if count > 0:
            por_rol[rol_name] = count

    context = {
        'personas': personas,
        'search_query': search_query,
        'rol_filter': rol_filter,
        'sede_filter': sede_filter,
        'roles': Persona.ROLES,
        'sedes': Persona.SEDES,
        'total_personas': total_personas,
        'por_rol': por_rol,
    }

    return render(request, 'persona/listar_personas.html', context)


@admin_comedor_required
def detalle_persona(request, persona_id):
    """Muestra el detalle completo de una persona"""
    persona = get_object_or_404(
        Persona.objects.select_related('usuario'),
        pk=persona_id
    )

    # Obtener perfil específico según rol
    perfil_especifico = None
    if persona.rol == 'estudiante' and hasattr(persona, 'estudiante'):
        perfil_especifico = persona.estudiante
        becas = PersonaBeca.objects.filter(
            persona_estudiante=perfil_especifico
        ).select_related('beca').order_by('-fecha_inicio')
    elif persona.rol == 'docente' and hasattr(persona, 'docente'):
        perfil_especifico = persona.docente
        becas = None
    elif persona.rol == 'no_docente' and hasattr(persona, 'no_docente'):
        perfil_especifico = persona.no_docente
        becas = None
    else:
        becas = None

    # Obtener observaciones
    observaciones = Observacion.objects.filter(
        persona=persona
    ).select_related('usuario').order_by('-fecha')[:20]

    context = {
        'persona': persona,
        'perfil_especifico': perfil_especifico,
        'becas': becas,
        'observaciones': observaciones,
    }

    return render(request, 'persona/detalle_persona.html', context)


@admin_comedor_required
def editar_persona(request, persona_id):
    """Permite editar todos los datos de una persona"""
    persona = get_object_or_404(Persona, pk=persona_id)

    # Obtener perfil específico según rol
    perfil_especifico = None
    FormPerfilClass = None

    if persona.rol == 'estudiante' and hasattr(persona, 'estudiante'):
        perfil_especifico = persona.estudiante
        FormPerfilClass = PersonaEstudianteForm
    elif persona.rol == 'docente' and hasattr(persona, 'docente'):
        perfil_especifico = persona.docente
        FormPerfilClass = PersonaDocenteForm
    elif persona.rol == 'no_docente' and hasattr(persona, 'no_docente'):
        perfil_especifico = persona.no_docente
        FormPerfilClass = PersonaNoDocenteForm

    if request.method == 'POST':
        form_persona = PersonaForm(request.POST, request.FILES, instance=persona)
        form_perfil = FormPerfilClass(
            request.POST, request.FILES, instance=perfil_especifico
        ) if FormPerfilClass else None

        if form_persona.is_valid() and (form_perfil is None or form_perfil.is_valid()):
            try:
                with transaction.atomic():
                    cambios = {}

                    # Registrar cambios en Persona
                    for field in form_persona.changed_data:
                        valor_anterior = getattr(persona, field)
                        valor_nuevo = form_persona.cleaned_data[field]

                        # Convertir a string legible
                        if hasattr(valor_anterior, 'name'):  # FileField
                            valor_anterior = valor_anterior.name if valor_anterior else 'Sin archivo'
                        if hasattr(valor_nuevo, 'name'):
                            valor_nuevo = valor_nuevo.name if valor_nuevo else 'Sin archivo'

                        cambios[f"Persona.{field}"] = {
                            'anterior': str(valor_anterior) if valor_anterior else '',
                            'nuevo': str(valor_nuevo) if valor_nuevo else ''
                        }

                    persona = form_persona.save()

                    # Registrar cambios en perfil específico
                    if form_perfil and perfil_especifico:
                        for field in form_perfil.changed_data:
                            valor_anterior = getattr(perfil_especifico, field)
                            valor_nuevo = form_perfil.cleaned_data[field]

                            if hasattr(valor_anterior, 'name'):
                                valor_anterior = valor_anterior.name if valor_anterior else 'Sin archivo'
                            if hasattr(valor_nuevo, 'name'):
                                valor_nuevo = valor_nuevo.name if valor_nuevo else 'Sin archivo'

                            cambios[f"{persona.get_rol_display()}.{field}"] = {
                                'anterior': str(valor_anterior) if valor_anterior else '',
                                'nuevo': str(valor_nuevo) if valor_nuevo else ''
                            }

                        form_perfil.save()

                    # Registrar cambios en Observacion
                    if cambios:
                        registrar_cambio(
                            persona=persona,
                            usuario=request.user,
                            cambios_dict=cambios,
                            accion='modificacion',
                            request=request
                        )

                    messages.success(
                        request,
                        f'✓ Datos de {persona.nombre_completo} actualizados correctamente. '
                        f'Se registraron {len(cambios)} cambio(s).'
                    )
                    return redirect('detalle_persona', persona_id=persona.id)

            except Exception as e:
                messages.error(request, f'Error al guardar cambios: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        form_persona = PersonaForm(instance=persona)
        form_perfil = FormPerfilClass(instance=perfil_especifico) if FormPerfilClass else None

    context = {
        'persona': persona,
        'form_persona': form_persona,
        'form_perfil': form_perfil,
        'tiene_perfil': perfil_especifico is not None,
        'nombre_perfil': persona.get_rol_display() if persona.rol else 'Sin Rol',
    }

    return render(request, 'persona/editar_persona.html', context)


@admin_comedor_required
def eliminar_persona(request, persona_id):
    """Elimina una persona del sistema (con confirmación)"""
    persona = get_object_or_404(Persona, pk=persona_id)

    if request.method == 'POST':
        confirmar = request.POST.get('confirmar', '')

        if confirmar == 'ELIMINAR':
            try:
                with transaction.atomic():
                    # Registrar eliminación
                    cambios = {
                        'accion': {
                            'anterior': 'Persona existente',
                            'nuevo': 'Persona eliminada'
                        },
                        'datos': {
                            'anterior': f"{persona.nombre_completo} - {persona.documento}",
                            'nuevo': 'ELIMINADO'
                        }
                    }

                    registrar_cambio(
                        persona=persona,
                        usuario=request.user,
                        cambios_dict=cambios,
                        accion='eliminacion',
                        request=request
                    )

                    nombre_completo = persona.nombre_completo
                    persona.delete()

                    messages.success(
                        request,
                        f'✓ Persona {nombre_completo} eliminada correctamente'
                    )
                    return redirect('listar_personas')

            except Exception as e:
                messages.error(request, f'Error al eliminar persona: {str(e)}')
        else:
            messages.error(request, 'Debe escribir "ELIMINAR" para confirmar')

    context = {
        'persona': persona,
    }

    return render(request, 'persona/eliminar_persona.html', context)


@admin_comedor_required
def agregar_observacion(request, persona_id):
    """Agrega una observación manual a una persona"""
    persona = get_object_or_404(Persona, pk=persona_id)

    if request.method == 'POST':
        form = ObservacionForm(request.POST)
        if form.is_valid():
            observacion = form.save(commit=False)
            observacion.persona = persona
            observacion.usuario = request.user
            observacion.tipo_accion = 'observacion'
            observacion.save()

            messages.success(request, '✓ Observación agregada correctamente')
            return redirect('detalle_persona', persona_id=persona.id)
    else:
        form = ObservacionForm()

    context = {
        'persona': persona,
        'form': form,
    }

    return render(request, 'persona/agregar_observacion.html', context)


@auditor_required
def historial_completo(request, persona_id):
    """Vista exclusiva para auditores - historial completo de cambios"""
    persona = get_object_or_404(Persona, pk=persona_id)

    # Filtros
    tipo_filter = request.GET.get('tipo', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    observaciones = Observacion.objects.filter(
        persona=persona
    ).select_related('usuario')

    # Aplicar filtros
    if tipo_filter:
        observaciones = observaciones.filter(tipo_accion=tipo_filter)

    if fecha_desde:
        observaciones = observaciones.filter(fecha__gte=fecha_desde)

    if fecha_hasta:
        observaciones = observaciones.filter(fecha__lte=fecha_hasta)

    observaciones = observaciones.order_by('-fecha')

    # Estadísticas
    total_cambios = observaciones.count()
    por_tipo = {}
    for tipo_code, tipo_name in [
        ('creacion', 'Creación'),
        ('modificacion', 'Modificación'),
        ('eliminacion', 'Eliminación'),
        ('observacion', 'Observación'),
    ]:
        count = observaciones.filter(tipo_accion=tipo_code).count()
        if count > 0:
            por_tipo[tipo_name] = count

    context = {
        'persona': persona,
        'observaciones': observaciones,
        'tipo_filter': tipo_filter,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_cambios': total_cambios,
        'por_tipo': por_tipo,
    }

    return render(request, 'persona/historial_completo.html', context)


@auditor_required
def historial_general(request):
    """Vista para auditores - todos los cambios del sistema"""

    # Filtros
    search_query = request.GET.get('search', '')
    tipo_filter = request.GET.get('tipo', '')
    usuario_filter = request.GET.get('usuario', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    observaciones = Observacion.objects.select_related(
        'persona', 'usuario'
    ).all()

    # Aplicar filtros
    if search_query:
        observaciones = observaciones.filter(
            Q(persona__nombre__icontains=search_query) |
            Q(persona__apellido__icontains=search_query) |
            Q(persona__documento__icontains=search_query) |
            Q(observacion__icontains=search_query)
        )

    if tipo_filter:
        observaciones = observaciones.filter(tipo_accion=tipo_filter)

    if usuario_filter:
        observaciones = observaciones.filter(usuario_id=usuario_filter)

    if fecha_desde:
        observaciones = observaciones.filter(fecha__gte=fecha_desde)

    if fecha_hasta:
        observaciones = observaciones.filter(fecha__lte=fecha_hasta)

    observaciones = observaciones.order_by('-fecha')

    # Para el filtro de usuarios
    from django.contrib.auth import get_user_model
    User = get_user_model()
    usuarios = User.objects.filter(
        id__in=Observacion.objects.values_list('usuario_id', flat=True).distinct()
    ).order_by('username')

    context = {
        'observaciones': observaciones,
        'search_query': search_query,
        'tipo_filter': tipo_filter,
        'usuario_filter': usuario_filter,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'usuarios': usuarios,
    }

    return render(request, 'persona/historial_general.html', context)