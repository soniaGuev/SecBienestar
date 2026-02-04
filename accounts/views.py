from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .forms import (RolSelectionForm, PersonaBaseForm, EstudiantePerfilForm, DocentePerfilForm,
                    NoDocentePerfilForm, PersonaIdentidadPercibidaForm, PersonaEditableForm,
                    EstudiantePreferenciaMenuForm, IngresantePerfilForm, EgresadoPerfilForm
                    )
from .models import CustomUser
from persona.models import Persona, PersonaEstudiante, PersonaDocente, PersonaNoDocente, PersonaEgresado, \
    PersonaIngresante
from django.core.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta
from functools import wraps


def perfil_completo_requerido(view_func):
    # Verifica si el usuario tiene el perfil completo. Si no lo tiene, redirige a completar el perfil.

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        # Staff puede acceder sin restricciones
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)

        try:
            persona = Persona.objects.get(usuario=request.user)

            # Verificar si necesita seleccionar rol
            if not persona.rol or persona.rol == '':
                messages.warning(request, 'Primero debes seleccionar tu rol.')
                return redirect('accounts:seleccionar_rol')

            # Verificar si tiene documento temporal
            if persona.documento.startswith('TEMP_'):
                messages.warning(request, 'Debes completar tu perfil para acceder.')
                return redirect('accounts:profile_complete')

            # Perfil completo, continuar
            return view_func(request, *args, **kwargs)

        except Persona.DoesNotExist:
            messages.error(request, 'No se encontró tu perfil. Contacta al administrador.')
            return redirect('accounts:seleccionar_rol')

    return wrapper


def home(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return render(request, 'home.html')

        try:
            persona = Persona.objects.get(usuario=request.user)

            # Si no tiene rol → seleccionar rol
            if not persona.rol or persona.rol == '':
                return redirect('accounts:seleccionar_rol')

            # Si tiene documento temporal → completar perfil
            if persona.documento.startswith('TEMP_'):
                return redirect('accounts:profile_complete')

            # Perfil completo → mostrar landing
            return render(request, 'bienestar_layout/landing.html')

        except Persona.DoesNotExist:
            messages.warning(request, 'Por favor completa tu perfil.')
            return redirect('accounts:seleccionar_rol')
    else:
        return render(request, 'bienestar_layout/landing.html')


def public_profile(request, username):
    user = get_object_or_404(CustomUser, username=username)
    userprofile = user.userprofile
    context = {'userprofile': userprofile}
    return render(request, 'account/public_profile.html', context)


@login_required
def signout(request):
    logout(request)
    return redirect('home')


@login_required
def seleccionar_rol(request):
    """Vista para que el usuario seleccione su rol por primera vez"""
    try:
        persona = Persona.objects.get(usuario=request.user)

        # Si tiene perfil completo → no puede cambiar rol, redirigir
        if persona.rol and persona.rol != '' and not persona.documento.startswith('TEMP_'):
            messages.warning(request, 'Ya tienes un perfil completo. No puedes cambiar tu rol.')
            return redirect('home')

    except Persona.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil. Contacta al administrador.')
        return redirect('home')

    if request.method == 'POST':
        form = RolSelectionForm(request.POST)
        if form.is_valid():
            rol_seleccionado = form.cleaned_data['rol']

            # Verificar si está cambiando el rol
            if persona.rol and persona.rol != '' and persona.rol != rol_seleccionado:
                messages.warning(request, 'Estás cambiando tu rol. Deberás completar nuevamente tu perfil.')

            persona.rol = rol_seleccionado
            persona.save()

            messages.success(request, f'Rol seleccionado: {persona.get_rol_display()}')
            return redirect('accounts:profile_complete')
    else:
        # Prellenar si ya tiene rol
        initial_data = {'rol': persona.rol} if persona.rol else {}
        form = RolSelectionForm(initial=initial_data)

    context = {
        'form': form,
        'persona': persona
    }
    return render(request, 'account/seleccionar_rol.html', context)


@login_required
def profile_complete(request):
    """
    Vista para completar el perfil según el rol del usuario
    """
    try:
        persona = Persona.objects.get(usuario=request.user)
    except Persona.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil. Contacta al administrador.')
        return redirect('home')

    if not persona.rol or persona.rol == '':
        messages.warning(request, 'Primero debes seleccionar tu rol.')
        return redirect('accounts:seleccionar_rol')

    if not persona.documento.startswith('TEMP_'):
        return redirect('home')

    rol = persona.rol

    if request.method == 'POST':
        # Formularios base
        form_base = PersonaBaseForm(request.POST, instance=persona, user_email=request.user.email)
        form_identidad = PersonaIdentidadPercibidaForm(request.POST, request.FILES, instance=persona)

        # Formulario específico según rol
        if rol == 'estudiante':
            try:
                perfil_estudiante = PersonaEstudiante.objects.get(persona=persona)
                form_especifico = EstudiantePerfilForm(request.POST, request.FILES, instance=perfil_estudiante)
            except PersonaEstudiante.DoesNotExist:
                perfil_temp = PersonaEstudiante(persona=persona)
                form_especifico = EstudiantePerfilForm(request.POST, request.FILES)

        elif rol == 'docente':
            try:
                perfil_docente = PersonaDocente.objects.get(persona=persona)
                form_especifico = DocentePerfilForm(request.POST, request.FILES, instance=perfil_docente)
            except PersonaDocente.DoesNotExist:
                perfil_temp = PersonaDocente(persona=persona)
                form_especifico = DocentePerfilForm(request.POST, request.FILES)

        elif rol == 'no_docente':
            try:
                perfil_no_docente = PersonaNoDocente.objects.get(persona=persona)
                form_especifico = NoDocentePerfilForm(request.POST, request.FILES, instance=perfil_no_docente)
            except PersonaNoDocente.DoesNotExist:
                perfil_temp = PersonaNoDocente(persona=persona)
                form_especifico = NoDocentePerfilForm(request.POST, request.FILES)

        elif rol == 'ingresante':
            try:
                perfil_ingresante = PersonaIngresante.objects.get(persona=persona)
                form_especifico = IngresantePerfilForm(request.POST, request.FILES, instance=perfil_ingresante)
            except PersonaIngresante.DoesNotExist:
                form_especifico = IngresantePerfilForm(request.POST, request.FILES)

        elif rol == 'egresado':
            try:
                perfil_egresado = PersonaEgresado.objects.get(persona=persona)
                form_especifico = EgresadoPerfilForm(request.POST, request.FILES, instance=perfil_egresado)
            except PersonaEgresado.DoesNotExist:
                form_especifico = EgresadoPerfilForm(request.POST, request.FILES)

        else:
            messages.error(request, 'Rol no reconocido.')
            return redirect('accounts:seleccionar_rol')

        # Validar todos los formularios
        if form_base.is_valid() and form_identidad.is_valid():
            try:
                with transaction.atomic():
                    # 1. Guardar datos base de Persona
                    persona_actualizada = form_base.save(commit=False)
                    persona_actualizada.correo = request.user.email
                    persona_actualizada.save()

                    # 2. Guardar identidad percibida
                    form_identidad.save()

                    # 3. AHORA validar el formulario específico (ya tiene persona asignada)
                    perfil_especifico = form_especifico.save(commit=False)
                    perfil_especifico.persona = persona_actualizada

                    # 4. Validar manualmente el perfil específico
                    try:
                        perfil_especifico.full_clean()
                    except ValidationError as e:
                        # Pasar los errores al formulario
                        for field, errors in e.message_dict.items():
                            for error in errors:
                                form_especifico.add_error(field, error)
                        raise ValidationError("Errores en el formulario específico")

                    # Para estudiantes: manejar DDJJ celíaco si existe
                    if rol == 'estudiante' and 'ddjj_celiaco' in request.FILES:
                        # Guardar el archivo si tu modelo lo soporta
                        # O crear un modelo adicional para almacenarlo
                        pass

                    perfil_especifico.save()

                    # IMPORTANTE: Si hay relaciones ManyToMany, guardarlas después
                    if hasattr(form_especifico, 'save_m2m'):
                        form_especifico.save_m2m()

                    messages.success(request, '¡Tu perfil ha sido completado exitosamente!')
                    return redirect('home')
            except Exception as e:
                messages.error(request, f'Error al guardar el perfil: {str(e)}')
        else:
            if not form_base.is_valid():
                messages.error(request, 'Hay errores en los datos personales.')
            if not form_identidad.is_valid():
                messages.error(request, 'Hay errores en la identidad percibida.')
            if not form_especifico.is_valid():
                messages.error(request, f'Hay errores en la información de {rol}.')
    else:
        # GET: Mostrar formularios
        form_base = PersonaBaseForm(instance=persona, user_email=request.user.email)
        form_identidad = PersonaIdentidadPercibidaForm(instance=persona)

        if rol == 'estudiante':
            try:
                perfil_estudiante = persona.estudiante
                form_especifico = EstudiantePerfilForm(instance=perfil_estudiante)
            except PersonaEstudiante.DoesNotExist:
                form_especifico = EstudiantePerfilForm()

        elif rol == 'docente':
            try:
                perfil_docente = persona.docente
                form_especifico = DocentePerfilForm(instance=perfil_docente)
            except PersonaDocente.DoesNotExist:
                form_especifico = DocentePerfilForm()

        elif rol == 'no_docente':
            try:
                perfil_no_docente = persona.no_docente
                form_especifico = NoDocentePerfilForm(instance=perfil_no_docente)
            except PersonaNoDocente.DoesNotExist:
                form_especifico = NoDocentePerfilForm()

        elif rol == 'ingresante':
            try:
                perfil_ingresante = PersonaIngresante.objects.get(persona=persona)
                form_especifico = IngresantePerfilForm(request.POST, request.FILES, instance=perfil_ingresante)
            except PersonaIngresante.DoesNotExist:
                form_especifico = IngresantePerfilForm(request.POST, request.FILES)

        elif rol == 'egresado':
            try:
                perfil_egresado = PersonaEgresado.objects.get(persona=persona)
                form_especifico = EgresadoPerfilForm(request.POST, request.FILES, instance=perfil_egresado)
            except PersonaEgresado.DoesNotExist:
                form_especifico = EgresadoPerfilForm(request.POST, request.FILES)

        else:
            messages.error(request, 'Rol no reconocido.')
            return redirect('accounts:seleccionar_rol')

    context = {
        'form_base': form_base,
        'form_identidad': form_identidad,
        'form_especifico': form_especifico,
        'persona': persona,
        'rol': rol,
        'rol_display': persona.get_rol_display()
    }
    return render(request, 'account/profile_complete.html', context)


@login_required
@perfil_completo_requerido  # Usar el nuevo decorador
def ver_perfil(request):
    """Vista para ver el perfil completo del usuario"""
    persona = Persona.objects.get(usuario=request.user)

    # Obtener el perfil específico según el rol
    perfil_especifico = None
    puede_cambiar_menu = False

    if persona.rol == 'estudiante':
        try:
            perfil_especifico = persona.estudiante
            estudiante = perfil_especifico

            # Calcular si puede cambiar menú
            if not estudiante.fecha_ultima_modificacion_menu:
                puede_cambiar_menu = True
            else:
                fecha_limite = (
                        estudiante.fecha_ultima_modificacion_menu
                        + relativedelta(years=1)
                )
                puede_cambiar_menu = date.today() >= fecha_limite
        except PersonaEstudiante.DoesNotExist:
            messages.error(request, 'No se encontró tu perfil de estudiante.')
            return redirect('home')

    elif persona.rol == 'docente':
        try:
            perfil_especifico = persona.docente
        except PersonaDocente.DoesNotExist:
            messages.error(request, 'No se encontró tu perfil de docente.')
            return redirect('home')

    elif persona.rol == 'no_docente':
        try:
            perfil_especifico = persona.no_docente
        except PersonaNoDocente.DoesNotExist:
            messages.error(request, 'No se encontró tu perfil de no docente.')
            return redirect('home')

    context = {
        'persona': persona,
        'perfil_especifico': perfil_especifico,
        'rol': persona.rol,
        'puede_cambiar_menu': puede_cambiar_menu,
    }
    return render(request, 'account/ver_perfil.html', context)


@login_required
def editar_perfil(request):
    """Vista para editar campos específicos del perfil"""
    try:
        persona = Persona.objects.get(usuario=request.user)
    except Persona.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil.')
        return redirect('home')

    if request.method == 'POST':
        form_editable = PersonaEditableForm(request.POST, request.FILES, instance=persona)

        if form_editable.is_valid():
            form_editable.save()
            messages.success(request, '¡Perfil actualizado correctamente!')
            return redirect('accounts:ver_perfil')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form_editable = PersonaEditableForm(instance=persona)

    context = {
        'form': form_editable,
        'persona': persona,
    }
    return render(request, 'account/editar_perfil.html', context)


@login_required
def cambiar_preferencia_menu(request):
    """Vista para cambiar la preferencia de menú (estudiantes)"""
    try:
        persona = Persona.objects.get(usuario=request.user)

        if persona.rol != 'estudiante':
            messages.error(request, 'Solo los estudiantes pueden cambiar la preferencia de menú.')
            return redirect('accounts:ver_perfil')

        estudiante = persona.estudiante

    except (Persona.DoesNotExist, PersonaEstudiante.DoesNotExist):
        messages.error(request, 'No se encontró tu perfil de estudiante.')
        return redirect('home')

    puede_cambiar = True
    if estudiante.fecha_ultima_modificacion_menu:
        fecha_limite = estudiante.fecha_ultima_modificacion_menu + relativedelta(years=1)
        if date.today() < fecha_limite:
            puede_cambiar = False
            dias_restantes = (fecha_limite - date.today()).days
            messages.warning(
                request,
                f'Solo puedes cambiar tu preferencia de menú una vez al año. '
                f'Podrás cambiarla nuevamente en {dias_restantes} días.'
            )
            return redirect('accounts:ver_perfil')

    # Verificar si puede cambiar (última modificación hace más de 1 año)
    # Puedes agregar un campo fecha_ultima_modificacion_menu en el modelo

    if request.method == 'POST':
        form = EstudiantePreferenciaMenuForm(request.POST, instance=estudiante)

        if form.is_valid():
            estudiante_actualizado = form.save(commit=False)
            estudiante_actualizado.fecha_ultima_modificacion_menu = date.today()
            estudiante_actualizado.save()
            messages.success(request, '¡Preferencia de menú actualizada correctamente!')
            return redirect('accounts:ver_perfil')
        else:
            messages.error(request, 'Hubo un error al actualizar la preferencia.')
    else:
        form = EstudiantePreferenciaMenuForm(instance=estudiante)

    context = {
        'form': form,
        'persona': persona,
        'estudiante': estudiante,
    }
    return render(request, 'account/cambiar_preferencia_menu.html', context)


# Mantener esta función si la usas en otro lado, sino elimínala
@login_required
def update_profile(request):
    """DEPRECADA - Redirigir a la nueva vista de perfil"""
    return redirect('accounts:ver_perfil')
