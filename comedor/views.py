from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from datetime import datetime, timedelta, date
from .models import Ticket, TipoMenu, CompraTickets, ConfiguracionMenu, BeneficioComedor, ImagenCarrusel, \
    CertificadoCeliaco
from .forms import CompraTicketForm, TipoMenuForm, BeneficioComedorForm, ImagenCarruselForm, CertificadoCeliacoForm, \
    BecaForm, ValidacionEstudianteForm
from .decorators import admin_comedor_required, auditor_required
from persona.models import PersonaBeca, Beca, PersonaEstudiante, Persona
from django.utils import timezone


def carrousel(request):
    return render(request, 'comedor/carrousel.html')

def panel_comedor(request):
    return render(request, 'comedor/panel_comedor.html')


@login_required
def comprar_tickets(request):
    from decimal import Decimal

    config = ConfiguracionMenu.get_config()

    beneficio_disponible = None
    beca_activa = None
    es_gratuito = False
    preferencia_usuario = None

    if hasattr(request.user, 'persona') and hasattr(request.user.persona, 'estudiante'):
        preferencia_usuario = request.user.persona.estudiante.preferencia_menu

        hoy = timezone.now().date()

        # Buscar becas activas del estudiante
        becas_activas = PersonaBeca.objects.filter(
            persona_estudiante=request.user.persona.estudiante,
            estado_beca='ACTIVA',
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        ).select_related('beca')

        # Buscar si alguna beca tiene beneficio de comedor
        for persona_beca in becas_activas:
            try:
                beneficio = BeneficioComedor.objects.get(
                    tipo_beca=persona_beca.beca,
                    activo=True
                )
                beneficio_disponible = beneficio
                beca_activa = persona_beca

                # Verificar si es 100% gratuito
                if beneficio.tipo_beneficio == 'gratuito' or beneficio.porcentaje_descuento == 100:
                    es_gratuito = True
                break
            except BeneficioComedor.DoesNotExist:
                continue

    # ============================================
    # CASO 1: BECA GRATUITA - GENERACIÓN DIRECTA
    # ============================================
    if es_gratuito and request.method == 'GET':
        # Redirigir a la vista de generación automática
        return redirect('generar_ticket_gratuito')

    # Si es POST con beca gratuita, procesar normalmente
    # (por si alguien accede directamente al POST)

    # ============================================
    # CASO 2: DESCUENTO PARCIAL O SIN BECA
    # ============================================
    if request.method == 'POST':
        form = CompraTicketForm(
            request.POST,
            request.FILES,
            usuario=request.user,
            tiene_beneficio=beneficio_disponible is not None
        )

        if form.is_valid():
            try:
                with transaction.atomic():

                    cantidad = 1

                    if not preferencia_usuario:
                        messages.error(request, 'No tienes una preferencia de menú configurada')
                        return redirect('comprar_tickets')

                    if preferencia_usuario == 'comun':
                        tipo_menu = config.menu_comun
                    elif preferencia_usuario == 'vegetariano':
                        tipo_menu = config.menu_vegetariano
                    elif preferencia_usuario == 'celiaco_comun':
                        tipo_menu = config.menu_celiaco_comun
                    elif preferencia_usuario == 'celiaco_vegetariano':
                        tipo_menu = config.menu_celiaco_vegetariano
                    else:
                        messages.error(request, 'Preferencia de menú no válida')
                        return redirect('comprar_tickets')

                    # Calcular precios con beneficio si aplica
                    precio_base = tipo_menu.precio

                    if beneficio_disponible:
                        precio_final = beneficio_disponible.calcular_precio_final(precio_base)
                        descuento = beneficio_disponible.calcular_descuento(precio_base)
                    else:
                        precio_final = precio_base
                        descuento = Decimal('0.00')

                    # Calcular totales
                    subtotal = precio_base * cantidad
                    total_descuentos = descuento * cantidad
                    total_pagado = precio_final * cantidad

                    # Crear la compra
                    compra = CompraTickets.objects.create(
                        usuario=request.user,
                        cantidad_tickets=cantidad,
                        subtotal=subtotal,
                        total_descuentos=total_descuentos,
                        total_pagado=total_pagado,
                        metodo_pago='efectivo' if total_pagado > 0 else 'beca_gratuita',
                        tickets_con_beneficio=cantidad if beneficio_disponible else 0
                    )

                    # Crear tickets
                    fecha_valido = datetime.now().date() + timedelta(days=30)

                    for i in range(cantidad):
                        Ticket.objects.create(
                            usuario=request.user,
                            tipo_menu=tipo_menu,
                            precio_base=precio_base,
                            descuento_aplicado=descuento,
                            precio_pagado=precio_final,
                            beneficio_aplicado=beneficio_disponible,
                            beca_utilizada=beca_activa,
                            requiere_menu_celiaco=preferencia_usuario.startswith('celiaco'),
                            estado='pagado',
                            compra=compra,
                            fecha_valido_hasta=fecha_valido
                        )

                # Mensaje de éxito personalizado según el beneficio
                if beneficio_disponible:
                    if precio_final == 0:
                        messages.success(
                            request,
                            f'¡Tickets generados exitosamente! Se crearon {cantidad} ticket(s) GRATUITOS '
                            f'por tu beca {beca_activa.beca.tipo}. '
                            f'Puedes ver tus códigos QR en "Mis Tickets".'
                        )
                    else:
                        messages.success(
                            request,
                            f'¡Compra exitosa! Se generaron {cantidad} ticket(s). '
                            f'Descuento aplicado: ${total_descuentos:.2f} ({beneficio_disponible.porcentaje_descuento}%). '
                            f'Total a pagar: ${total_pagado:.2f}'
                        )
                else:
                    messages.success(
                        request,
                        f'¡Compra exitosa! Se generaron {cantidad} ticket(s). Total: ${total_pagado:.2f}'
                    )
                return redirect('mis_tickets')

            except Exception as e:
                messages.error(request, f'Error al procesar la compra: {str(e)}')
                return redirect('comprar_tickets')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario')
    else:
        form = CompraTicketForm(
            usuario=request.user,
            tiene_beneficio=beneficio_disponible is not None
        )

    # Calcular precios con descuento para mostrar en el template
    menu_a_mostrar = None
    precio_final_menu = None

    if preferencia_usuario == 'comun':
        menu_a_mostrar = config.menu_comun
    elif preferencia_usuario == 'vegetariano':
        menu_a_mostrar = config.menu_vegetariano
    elif preferencia_usuario == 'celiaco_comun':
        menu_a_mostrar = config.menu_celiaco_comun
    elif preferencia_usuario == 'celiaco_vegetariano':
        menu_a_mostrar = config.menu_celiaco_vegetariano

    if menu_a_mostrar and menu_a_mostrar.activo:
        if beneficio_disponible:
            precio_final_menu = beneficio_disponible.calcular_precio_final(menu_a_mostrar.precio)
        else:
            precio_final_menu = menu_a_mostrar.precio

    print(f"DEBUG CONTEXT:")
    print(f"  - preferencia_usuario: {preferencia_usuario}")
    print(f"  - menu_a_mostrar: {menu_a_mostrar}")
    print(f"  - menu activo: {menu_a_mostrar.activo if menu_a_mostrar else 'N/A'}")
    print(f"  - precio_final_menu: {precio_final_menu}")

    context = {
        'form': form,
        'config': config,
        'menu_a_mostrar': menu_a_mostrar,
        'precio_final_menu': precio_final_menu,
        'beneficio_disponible': beneficio_disponible,
        'beca_activa': beca_activa,
        'preferencia_usuario': preferencia_usuario,
    }

    return render(request, 'comedor/comprar.html', context)


@login_required
def generar_ticket_gratuito(request):
    """
    Vista para generar tickets gratuitos automáticamente para usuarios con beca 100%
    """
    from decimal import Decimal

    config = ConfiguracionMenu.get_config()

    # Verificar que el usuario tenga una beca gratuita activa
    beneficio_disponible = None
    beca_activa = None
    es_gratuito = False

    if hasattr(request.user, 'persona') and hasattr(request.user.persona, 'estudiante'):
        hoy = timezone.now().date()
        estudiante = request.user.persona.estudiante

        becas_activas = PersonaBeca.objects.filter(
            persona_estudiante=estudiante,
            estado_beca='ACTIVA',
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        ).select_related('beca')

        for persona_beca in becas_activas:
            try:
                beneficio = BeneficioComedor.objects.get(
                    tipo_beca=persona_beca.beca,
                    activo=True
                )
                if beneficio.tipo_beneficio == 'gratuito' or beneficio.porcentaje_descuento == 100:
                    beneficio_disponible = beneficio
                    beca_activa = persona_beca
                    es_gratuito = True
                    break
            except BeneficioComedor.DoesNotExist:
                continue

    if not es_gratuito:
        messages.warning(request, 'No tienes una beca con acceso gratuito al comedor.')
        return redirect('comprar_tickets')

    # Obtener el menú según la preferencia del estudiante
    preferencia = estudiante.preferencia_menu

    if preferencia == 'comun':
        tipo_menu = config.menu_comun
    else:
        tipo_menu = config.menu_vegetariano

    if not tipo_menu or not tipo_menu.activo:
        messages.error(request, 'El menú configurado no está disponible. Por favor contacta al administrador.')
        return redirect('mis_tickets')

    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 1))
        requiere_celiaquia = request.POST.get('requiere_celiaquia') == 'on'
        formulario_celiaquia = request.FILES.get('formulario_celiaquia') if requiere_celiaquia else None

        # Validación: si requiere celiaquía, debe subir el formulario
        if requiere_celiaquia and config.requiere_formulario_celiaquia and not formulario_celiaquia:
            messages.error(request, 'Debes adjuntar el formulario de celiaquía si requieres menú apto celíaco.')
            return render(request, 'comedor/generar_gratuito.html', {
                'tipo_menu': tipo_menu,
                'beneficio_disponible': beneficio_disponible,
                'beca_activa': beca_activa,
                'estudiante': estudiante,
            })

        try:
            with transaction.atomic():
                precio_base = tipo_menu.precio
                precio_final = Decimal('0.00')
                descuento = precio_base

                # Crear la compra
                compra = CompraTickets.objects.create(
                    usuario=request.user,
                    cantidad_tickets=cantidad,
                    subtotal=precio_base * cantidad,
                    total_descuentos=descuento * cantidad,
                    total_pagado=Decimal('0.00'),
                    metodo_pago='beca_gratuita',
                    tickets_con_beneficio=cantidad
                )

                # Crear tickets
                fecha_valido = datetime.now().date() + timedelta(days=30)

                for i in range(cantidad):
                    Ticket.objects.create(
                        usuario=request.user,
                        tipo_menu=tipo_menu,
                        precio_base=precio_base,
                        descuento_aplicado=descuento,
                        precio_pagado=precio_final,
                        beneficio_aplicado=beneficio_disponible,
                        beca_utilizada=beca_activa,
                        requiere_menu_celiaco=requiere_celiaquia,
                        formulario_celiaquia=formulario_celiaquia if requiere_celiaquia else None,
                        estado='pagado',
                        compra=compra,
                        fecha_valido_hasta=fecha_valido
                    )

                messages.success(
                    request,
                    f'¡Tickets generados exitosamente! Se crearon {cantidad} ticket(s) GRATUITOS. '
                    f'Puedes ver tus códigos QR en "Mis Tickets".'
                )
                return redirect('mis_tickets')

        except Exception as e:
            messages.error(request, f'Error al generar tickets: {str(e)}')

    context = {
        'tipo_menu': tipo_menu,
        'beneficio_disponible': beneficio_disponible,
        'beca_activa': beca_activa,
        'estudiante': estudiante,
        'config': config,
    }

    return render(request, 'comedor/generar_gratuito.html', context)


@login_required
def mis_tickets(request):
    tickets = Ticket.objects.filter(usuario=request.user).order_by('-fecha_compra')

    context = {
        'tickets': tickets,
    }

    return render(request, 'comedor/mis_tickets.html', context)


@login_required
def detalle_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, usuario=request.user)

    context = {
        'ticket': ticket,
    }

    return render(request, 'comedor/detalle_ticket.html', context)


# Vista pública del carrusel
def carrousel_view(request):
    hoy = date.today()
    imagenes = ImagenCarrusel.objects.filter(
        activo=True
    ).filter(
        Q(fecha_desde__isnull=True) | Q(fecha_desde__lte=hoy)
    ).filter(
        Q(fecha_hasta__isnull=True) | Q(fecha_hasta__gte=hoy)
    ).order_by('orden', 'dia_semana')

    return render(request, 'comedor/carrousel.html', {'imagenes': imagenes})


def _build_actividades_context():
    tickets_pagados = Ticket.objects.filter(estado='pagado')

    menus_comunes = tickets_pagados.filter(tipo_menu__tipo='comun').count()
    menus_vegetarianos = tickets_pagados.filter(tipo_menu__tipo='vegetariano').count()
    menus_celiacos = tickets_pagados.filter(
        Q(tipo_menu__tipo='celiaco') | Q(requiere_menu_celiaco=True)
    ).count()

    descuentos_aplicados = tickets_pagados.filter(descuento_aplicado__gt=0)

    descuentos_becados = descuentos_aplicados.filter(
        beneficio_aplicado__isnull=False
    ).count()
    descuentos_no_docente = descuentos_aplicados.filter(
        usuario__persona__rol='no_docente'
    ).count()
    descuentos_estudiantes = descuentos_aplicados.filter(
        usuario__persona__rol='estudiante',
        beneficio_aplicado__isnull=True
    ).count()

    return {
        'menus_comunes': menus_comunes,
        'menus_vegetarianos': menus_vegetarianos,
        'menus_celiacos': menus_celiacos,
        'descuentos_becados': descuentos_becados,
        'descuentos_no_docente': descuentos_no_docente,
        'descuentos_estudiantes': descuentos_estudiantes,
    }


# Panel de administración - Dashboard
@admin_comedor_required
def panel_admin(request):
    # Estadísticas de imágenes
    total_imagenes = ImagenCarrusel.objects.count()
    imagenes_activas = ImagenCarrusel.objects.filter(activo=True).count()
    imagenes_inactivas = ImagenCarrusel.objects.filter(activo=False).count()

    # Estadísticas de menús
    total_menus = TipoMenu.objects.count()
    menus_activos = TipoMenu.objects.filter(activo=True).count()
    menus_inactivos = TipoMenu.objects.filter(activo=False).count()

    total_beneficios = BeneficioComedor.objects.count()
    beneficios_activos = BeneficioComedor.objects.filter(activo=True).count()
    beneficios_inactivos = BeneficioComedor.objects.filter(activo=False).count()
    beneficios_gratuitos = BeneficioComedor.objects.filter(
        activo=True,
        porcentaje_descuento=100
    ).count()

    # Actividades y compras
    tickets_pagados = Ticket.objects.filter(estado='pagado')

    menus_comunes = tickets_pagados.filter(tipo_menu__tipo='comun').count()
    menus_vegetarianos = tickets_pagados.filter(tipo_menu__tipo='vegetariano').count()
    menus_celiacos = tickets_pagados.filter(
        Q(tipo_menu__tipo='celiaco') | Q(requiere_menu_celiaco=True)
    ).count()

    descuentos_aplicados = tickets_pagados.filter(descuento_aplicado__gt=0)

    descuentos_becados = descuentos_aplicados.filter(
        beneficio_aplicado__isnull=False
    ).count()
    descuentos_no_docente = descuentos_aplicados.filter(
        usuario__persona__rol='no_docente'
    ).count()
    descuentos_estudiantes = descuentos_aplicados.filter(
        usuario__persona__rol='estudiante',
        beneficio_aplicado__isnull=True
    ).count()

    context = {
        'total_imagenes': total_imagenes,
        'imagenes_activas': imagenes_activas,
        'imagenes_inactivas': imagenes_inactivas,
        'total_menus': total_menus,
        'menus_activos': menus_activos,
        'menus_inactivos': menus_inactivos,
        'total_beneficios': total_beneficios,
        'beneficios_activos': beneficios_activos,
        'beneficios_inactivos': beneficios_inactivos,
        'beneficios_gratuitos': beneficios_gratuitos,
        'menus_comunes': menus_comunes,
        'menus_vegetarianos': menus_vegetarianos,
        'menus_celiacos': menus_celiacos,
        'descuentos_becados': descuentos_becados,
        'descuentos_no_docente': descuentos_no_docente,
        'descuentos_estudiantes': descuentos_estudiantes,
    }
    return render(request, 'comedor/admin/dashboard.html', context)


@auditor_required
def actividades_auditor(request):
    context = _build_actividades_context()
    return render(request, 'comedor/actividades_auditor.html', context)

# Listar imágenes del carrusel
@admin_comedor_required
def listar_imagenes(request):
    imagenes = ImagenCarrusel.objects.all().order_by('-fecha_modificacion')
    return render(request, 'comedor/admin/listar_imagenes.html', {'imagenes': imagenes})

# ==================== GESTIÓN DE IMÁGENES ====================

# Crear nueva imagen
@admin_comedor_required
def crear_imagen(request):
    if request.method == 'POST':
        form = ImagenCarruselForm(request.POST, request.FILES)
        if form.is_valid():
            imagen = form.save(commit=False)
            imagen.usuario_creador = request.user
            imagen.save()
            messages.success(request, 'Imagen agregada exitosamente al carrusel.')
            return redirect('listar_imagenes')
    else:
        form = ImagenCarruselForm()

    return render(request, 'comedor/admin/form_imagen.html', {
        'form': form,
        'titulo': 'Agregar Nueva Imagen',
        'boton': 'Agregar'
    })


# Editar imagen existente
@admin_comedor_required
def editar_imagen(request, pk):
    imagen = get_object_or_404(ImagenCarrusel, pk=pk)

    if request.method == 'POST':
        form = ImagenCarruselForm(request.POST, request.FILES, instance=imagen)
        if form.is_valid():
            form.save()
            messages.success(request, 'Imagen actualizada exitosamente.')
            return redirect('listar_imagenes')
    else:
        form = ImagenCarruselForm(instance=imagen)

    return render(request, 'comedor/admin/form_imagen.html', {
        'form': form,
        'imagen': imagen,
        'titulo': 'Editar Imagen',
        'boton': 'Guardar Cambios'
    })


# Eliminar imagen
@admin_comedor_required
def eliminar_imagen(request, pk):
    imagen = get_object_or_404(ImagenCarrusel, pk=pk)

    if request.method == 'POST':
        imagen.delete()
        messages.success(request, 'Imagen eliminada exitosamente.')
        return redirect('listar_imagenes')

    return render(request, 'comedor/admin/confirmar_eliminacion.html', {'imagen': imagen})


# Activar/Desactivar imagen (AJAX friendly)
@admin_comedor_required
def toggle_activo(request, pk):
    imagen = get_object_or_404(ImagenCarrusel, pk=pk)
    imagen.activo = not imagen.activo
    imagen.save()

    estado = "activada" if imagen.activo else "desactivada"
    messages.success(request, f'Imagen {estado} exitosamente.')
    return redirect('listar_imagenes')

# ==================== GESTIÓN DE MENÚS ====================

@admin_comedor_required
def listar_menus(request):
    menus = TipoMenu.objects.all().order_by('tipo', 'nombre')
    config = ConfiguracionMenu.get_config()  # Agregar esta línea

    return render(request, 'comedor/admin/listar_menus.html', {
        'menus': menus,
        'config': config  # Agregar esta línea
    })

@admin_comedor_required
def crear_menu(request):
    if request.method == 'POST':
        form = TipoMenuForm(request.POST)
        if form.is_valid():
            menu = form.save()

            # Auto-configurar el menú según su tipo
            config = ConfiguracionMenu.get_config()

            if menu.tipo == 'comun' and menu.activo:
                config.menu_comun = menu
                config.save()
                messages.success(request, f'✓ Menú creado y configurado como Menú Común disponible.')
            elif menu.tipo == 'vegetariano' and menu.activo:
                config.menu_vegetariano = menu
                config.save()
                messages.success(request, f'✓ Menú creado y configurado como Menú Vegetariano disponible.')
            else:
                messages.success(request, 'Menú creado exitosamente.')

            return redirect('listar_menus')
    else:
        form = TipoMenuForm()

    return render(request, 'comedor/admin/form_menu.html', {
        'form': form,
        'titulo': 'Crear Nuevo Menú',
        'boton': 'Crear Menú'
    })


@admin_comedor_required
def editar_menu(request, pk):
    menu = get_object_or_404(TipoMenu, pk=pk)

    if request.method == 'POST':
        form = TipoMenuForm(request.POST, instance=menu)
        if form.is_valid():
            menu = form.save()

            # Auto-configurar el menú según su tipo
            config = ConfiguracionMenu.get_config()

            if menu.tipo == 'comun' and menu.activo:
                config.menu_comun = menu
                config.save()
                messages.success(request, f'✓ Menú actualizado y configurado como Menú Común disponible.')
            elif menu.tipo == 'vegetariano' and menu.activo:
                config.menu_vegetariano = menu
                config.save()
                messages.success(request, f'✓ Menú actualizado y configurado como Menú Vegetariano disponible.')
            else:
                # Si se desactiva, verificar si era el menú configurado
                if menu.tipo == 'comun' and config.menu_comun == menu:
                    config.menu_comun = None
                    config.save()
                    messages.warning(request,
                                     'Menú actualizado. Como fue desactivado, ya no está disponible para compra.')
                elif menu.tipo == 'vegetariano' and config.menu_vegetariano == menu:
                    config.menu_vegetariano = None
                    config.save()
                    messages.warning(request,
                                     'Menú actualizado. Como fue desactivado, ya no está disponible para compra.')
                else:
                    messages.success(request, 'Menú actualizado exitosamente.')

            return redirect('listar_menus')
    else:
        form = TipoMenuForm(instance=menu)

    return render(request, 'comedor/admin/form_menu.html', {
        'form': form,
        'menu': menu,
        'titulo': 'Editar Menú',
        'boton': 'Guardar Cambios'
    })


@admin_comedor_required
def eliminar_menu(request, pk):
    menu = get_object_or_404(TipoMenu, pk=pk)

    if request.method == 'POST':
        try:
            menu.delete()
            messages.success(request, 'Menú eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'No se puede eliminar el menú: {str(e)}')
        return redirect('listar_menus')

    return render(request, 'comedor/admin/confirmar_eliminacion_menu.html', {'menu': menu})


@admin_comedor_required
def toggle_activo_menu(request, pk):
    menu = get_object_or_404(TipoMenu, pk=pk)
    menu.activo = not menu.activo
    menu.save()

    estado = "activado" if menu.activo else "desactivado"
    messages.success(request, f'Menú {estado} exitosamente.')
    return redirect('listar_menus')

# ==================== GESTIÓN DE BENEFICIOS  ====================

@admin_comedor_required
def listar_beneficios(request):
    beneficios = BeneficioComedor.objects.all().order_by('tipo_beca')
    return render(request, 'comedor/admin/listar_beneficios.html', {
        'beneficios': beneficios
    })


@admin_comedor_required
def crear_beneficio(request):
    from persona.models import Beca

    if request.method == 'POST':
        form = BeneficioComedorForm(request.POST)
        if form.is_valid():
            beneficio = form.save()
            messages.success(request, f'Beneficio para beca "{beneficio.tipo_beca}" creado exitosamente.')
            return redirect('listar_beneficios')
    else:
        form = BeneficioComedorForm()

    return render(request, 'comedor/admin/form_beneficio.html', {
        'form': form,
        'titulo': 'Crear Beneficio de Comedor',
        'boton': 'Crear Beneficio'
    })


@admin_comedor_required
def editar_beneficio(request, pk):
    beneficio = get_object_or_404(BeneficioComedor, pk=pk)

    if request.method == 'POST':
        form = BeneficioComedorForm(request.POST, instance=beneficio)
        if form.is_valid():
            beneficio = form.save()
            messages.success(request, f'Beneficio "{beneficio.tipo_beca}" actualizado exitosamente.')
            return redirect('listar_beneficios')
    else:
        form = BeneficioComedorForm(instance=beneficio)

    return render(request, 'comedor/admin/form_beneficio.html', {
        'form': form,
        'beneficio': beneficio,
        'titulo': 'Editar Beneficio de Comedor',
        'boton': 'Guardar Cambios'
    })


@admin_comedor_required
def eliminar_beneficio(request, pk):
    beneficio = get_object_or_404(BeneficioComedor, pk=pk)

    if request.method == 'POST':
        try:
            tipo_beca = beneficio.tipo_beca
            beneficio.delete()
            messages.success(request, f'Beneficio de beca "{tipo_beca}" eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'No se puede eliminar el beneficio: {str(e)}')
        return redirect('listar_beneficios')

    return render(request, 'comedor/admin/confirmar_eliminacion_beneficio.html', {
        'beneficio': beneficio
    })


@admin_comedor_required
def toggle_activo_beneficio(request, pk):
    beneficio = get_object_or_404(BeneficioComedor, pk=pk)
    beneficio.activo = not beneficio.activo
    beneficio.save()

    estado = "activado" if beneficio.activo else "desactivado"
    messages.success(request, f'Beneficio "{beneficio.tipo_beca}" {estado} exitosamente.')
    return redirect('listar_beneficios')

# ==================== GESTIÓN DE BENEFICIARIOS ====================

@admin_comedor_required
def listar_beneficiarios(request):
    """Lista todos los estudiantes con sus becas"""
    # Filtros
    search_query = request.GET.get('search', '')
    beca_filter = request.GET.get('beca', '')
    estado_filter = request.GET.get('estado', '')

    estudiantes = PersonaEstudiante.objects.select_related(
        'persona', 'carrera'
    ).prefetch_related('becas__beca').all()

    # Aplicar búsqueda
    if search_query:
        estudiantes = estudiantes.filter(
            Q(persona__nombre__icontains=search_query) |
            Q(persona__apellido__icontains=search_query) |
            Q(numero_legajo__icontains=search_query) |
            Q(persona__documento__icontains=search_query)
        )

    # Filtrar por tipo de beca
    if beca_filter:
        estudiantes = estudiantes.filter(becas__beca__id=beca_filter)

    # Filtrar por estado de beca
    if estado_filter:
        estudiantes = estudiantes.filter(becas__estado_beca=estado_filter)

    estudiantes = estudiantes.distinct().order_by('persona__apellido', 'persona__nombre')

    # Para los filtros
    tipos_beca = Beca.objects.filter(activa=True).values_list('id', 'tipo')
    estados_beca = PersonaBeca.ESTADOS_BECA

    context = {
        'estudiantes': estudiantes,
        'search_query': search_query,
        'tipos_beca': tipos_beca,
        'estados_beca': estados_beca,
        'beca_filter': beca_filter,
        'estado_filter': estado_filter,
    }

    return render(request, 'comedor/admin/listar_beneficiarios.html', context)


@admin_comedor_required
def detalle_beneficiario(request, estudiante_id):
    """Muestra detalle de un estudiante con todas sus becas"""
    estudiante = get_object_or_404(
        PersonaEstudiante.objects.select_related('persona', 'carrera', 'dependencia'),
        pk=estudiante_id
    )

    becas = PersonaBeca.objects.filter(
        persona_estudiante=estudiante
    ).select_related('beca').order_by('-fecha_inicio')

    # Becas activas con beneficio de comedor
    hoy = timezone.now().date()
    becas_activas_comedor = []

    for beca in becas:
        if beca.estado_beca == 'ACTIVA' and beca.fecha_inicio <= hoy <= beca.fecha_fin:
            try:
                beneficio = BeneficioComedor.objects.get(
                    tipo_beca=beca.beca,
                    activo=True
                )
                becas_activas_comedor.append({
                    'beca': beca,
                    'beneficio': beneficio
                })
            except BeneficioComedor.DoesNotExist:
                pass

    # Tickets comprados
    tickets = Ticket.objects.filter(
        usuario=estudiante.persona.usuario
    ).select_related('tipo_menu', 'beneficio_aplicado').order_by('-fecha_compra')[:10]

    context = {
        'estudiante': estudiante,
        'becas': becas,
        'becas_activas_comedor': becas_activas_comedor,
        'tickets': tickets,
    }

    return render(request, 'comedor/admin/detalle_beneficiario.html', context)


# Reemplazar la función asignar_beca existente

@admin_comedor_required
def asignar_beca(request, estudiante_id):
    """Asigna una nueva beca a un estudiante"""
    estudiante = get_object_or_404(PersonaEstudiante, pk=estudiante_id)
    persona = estudiante.persona

    # Obtener certificado celíaco si existe
    try:
        certificado = CertificadoCeliaco.objects.get(persona=persona)
    except CertificadoCeliaco.DoesNotExist:
        certificado = None

    from datetime import datetime

    if request.method == 'POST':
        # Verificar si se está validando el estudiante
        if 'validar_estudiante' in request.POST:
            validacion_form = ValidacionEstudianteForm(request.POST)
            if validacion_form.is_valid():
                if validacion_form.cleaned_data['validado']:
                    estudiante.validado_como_regular = True
                    estudiante.fecha_validacion_regular = timezone.now()
                    estudiante.validado_por = request.user
                    estudiante.observaciones_validacion = validacion_form.cleaned_data['observaciones']
                    estudiante.save()
                    messages.success(
                        request,
                        f'✓ Estudiante {persona.nombre_completo} validado como alumno regular correctamente'
                    )
                else:
                    messages.warning(request, 'Debe marcar la casilla para validar al estudiante')
                return redirect('asignar_beca', estudiante_id=estudiante.id)

        # Proceso normal de asignación de beca
        beca_id = request.POST.get('beca_id')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        estado_beca = request.POST.get('estado_beca', 'PENDIENTE')
        monto_asignado = request.POST.get('monto_asignado')
        requiere_certificado = request.POST.get('requiere_certificado_celiaco', 'no') == 'si'

        try:
            beca = get_object_or_404(Beca, pk=beca_id)

            if not beca.activa:
                messages.error(request, f'La beca "{beca.tipo}" no está activa.')
                return redirect('asignar_beca', estudiante_id=estudiante.id)

            # VALIDACIÓN: Si es beca de comedor, verificar que esté validado como regular
            if beca.tipo.lower() == 'comedor' and not estudiante.validado_como_regular:
                messages.error(
                    request,
                    '⚠ No se puede asignar beca de comedor. El estudiante debe estar validado como alumno regular primero.'
                )
                return redirect('asignar_beca', estudiante_id=estudiante.id)

            # Convertir fechas
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()

            persona_beca = PersonaBeca(
                persona_estudiante=estudiante,
                beca=beca,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado_beca=estado_beca
            )

            if beca.tiene_monto:
                persona_beca.monto_asignado = monto_asignado or beca.monto_sugerido

            if estado_beca in ['APROBADA', 'ACTIVA']:
                persona_beca.fecha_aprobacion = timezone.now()

            persona_beca.full_clean()
            persona_beca.save()

            # Certificado celíaco
            if beca.permite_comedor and requiere_certificado:
                certificado_form = CertificadoCeliacoForm(
                    request.POST,
                    request.FILES,
                    instance=certificado
                )

                if certificado_form.is_valid():
                    cert = certificado_form.save(commit=False)
                    cert.persona = persona
                    cert.cargado_por = request.user
                    cert.save()
                else:
                    persona_beca.delete()
                    messages.error(request, 'Error en el formulario de certificado celíaco')
                    return redirect('asignar_beca', estudiante_id=estudiante.id)

            messages.success(
                request,
                f'✓ Beca "{beca.tipo}" asignada exitosamente a {persona.nombre_completo}'
            )

            return redirect('detalle_beneficiario', estudiante_id=estudiante.id)

        except Exception as e:
            messages.error(request, f'Error al asignar beca: {str(e)}')

    else:
        certificado_form = CertificadoCeliacoForm(instance=certificado)
        validacion_form = ValidacionEstudianteForm()

    # GET: mostrar formulario
    becas_disponibles = Beca.objects.filter(activa=True).order_by('tipo')
    estados_beca = PersonaBeca.ESTADOS_BECA

    context = {
        'estudiante': estudiante,
        'becas_disponibles': becas_disponibles,
        'estados_beca': estados_beca,
        'certificado_form': certificado_form,
        'certificado': certificado,
        'validacion_form': validacion_form,
    }

    return render(request, 'comedor/admin/asignar_beca.html', context)


@admin_comedor_required
def editar_beca(request, beca_id):
    """Edita una beca existente y permite gestionar certificado celíaco y preferencia de menú"""
    persona_beca = get_object_or_404(PersonaBeca, pk=beca_id)
    estudiante = persona_beca.persona_estudiante
    persona = estudiante.persona

    # Obtener o preparar el certificado celíaco si existe
    try:
        certificado = CertificadoCeliaco.objects.get(persona=persona)
    except CertificadoCeliaco.DoesNotExist:
        certificado = None

    if request.method == 'POST':
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        estado_beca = request.POST.get('estado_beca')
        preferencia_menu = request.POST.get('preferencia_menu')  # *** NUEVO ***
        requiere_certificado = request.POST.get('requiere_certificado_celiaco', 'no') == 'si'

        # Solo procesar certificado si es beca de Comedor Y se marcó que requiere
        certificado_form = None
        if persona_beca.beca.tipo.lower() == 'comedor' and requiere_certificado:
            certificado_form = CertificadoCeliacoForm(
                request.POST,
                request.FILES,
                instance=certificado
            )

        try:
            # Actualizar la beca
            persona_beca.fecha_inicio = fecha_inicio
            persona_beca.fecha_fin = fecha_fin

            # Si se aprueba o activa, registrar fecha
            if estado_beca in ['APROBADA', 'ACTIVA'] and not persona_beca.fecha_aprobacion:
                persona_beca.fecha_aprobacion = timezone.now()

            persona_beca.estado_beca = estado_beca

            persona_beca.save()

            # Guardar certificado celíaco solo si se requirió
            if persona_beca.beca.tipo.lower() == 'comedor' and requiere_certificado:
                if certificado_form and certificado_form.is_valid():
                    if request.FILES.get('archivo_certificado') or certificado:
                        cert = certificado_form.save(commit=False)
                        cert.persona = persona
                        cert.cargado_por = request.user
                        cert.save()
                        messages.success(request, '✓ Beca y certificado celíaco actualizados exitosamente')
                    else:
                        messages.success(request, '✓ Beca actualizada exitosamente')
                elif certificado_form and not certificado_form.is_valid():
                    messages.error(request, 'Error en el formulario de certificado celíaco')
                    return redirect('editar_beca', beca_id=beca_id)
            else:
                messages.success(request, '✓ Beca actualizada exitosamente')

            return redirect('detalle_beneficiario', estudiante_id=estudiante.id)

        except Exception as e:
            messages.error(request, f'Error al actualizar: {str(e)}')

    else:
        certificado_form = CertificadoCeliacoForm(instance=certificado)

    estados_beca = PersonaBeca.ESTADOS_BECA

    context = {
        'persona_beca': persona_beca,
        'estudiante': estudiante,
        'estados_beca': estados_beca,
        'certificado_form': certificado_form,
        'certificado': certificado,
    }

    return render(request, 'comedor/admin/editar_beca.html', context)


@admin_comedor_required
def eliminar_beca(request, beca_id):
    """Elimina una beca de un estudiante"""
    persona_beca = get_object_or_404(PersonaBeca, pk=beca_id)
    estudiante_id = persona_beca.persona_estudiante.id

    if request.method == 'POST':
        try:
            persona_beca.delete()
            messages.success(request, 'Beca eliminada exitosamente')
        except Exception as e:
            messages.error(request, f'Error al eliminar beca: {str(e)}')

        return redirect('detalle_beneficiario', estudiante_id=estudiante_id)

    context = {
        'persona_beca': persona_beca,
    }

    return render(request, 'comedor/admin/confirmar_eliminacion_beca.html', context)


@admin_comedor_required
def buscar_estudiante(request):
    """Búsqueda de estudiantes para asignar becas"""
    search_query = request.GET.get('q', '')

    estudiantes = PersonaEstudiante.objects.select_related(
        'persona', 'carrera'
    ).filter(
        Q(persona__nombre__icontains=search_query) |
        Q(persona__apellido__icontains=search_query) |
        Q(numero_legajo__icontains=search_query) |
        Q(persona__documento__icontains=search_query)
    )[:20]  # Limitar resultados

    context = {
        'estudiantes': estudiantes,
        'search_query': search_query,
    }

    return render(request, 'comedor/admin/buscar_estudiante.html', context)


# ==================== GESTIÓN DE CATÁLOGO DE BECAS ====================

@admin_comedor_required
def listar_becas(request):
    """Lista el catálogo de becas disponibles"""
    becas = Beca.objects.all().order_by('tipo')

    # Estadísticas
    total_becas = becas.count()
    becas_activas = becas.filter(activa=True).count()
    becas_con_monto = becas.filter(tiene_monto=True).count()
    becas_con_comedor = becas.filter(permite_comedor=True).count()

    context = {
        'becas': becas,
        'total_becas': total_becas,
        'becas_activas': becas_activas,
        'becas_con_monto': becas_con_monto,
        'becas_con_comedor': becas_con_comedor,
    }

    return render(request, 'comedor/admin/listar_becas.html', context)


@admin_comedor_required
def crear_beca(request):
    """Crea una nueva beca en el catálogo"""
    if request.method == 'POST':
        form = BecaForm(request.POST)
        if form.is_valid():
            beca = form.save()
            messages.success(
                request,
                f'✓ Beca "{beca.tipo}" creada exitosamente.'
            )
            return redirect('listar_becas')
    else:
        form = BecaForm()

    context = {
        'form': form,
        'titulo': 'Crear Nueva Beca',
        'boton': 'Crear Beca'
    }

    return render(request, 'comedor/admin/form_beca.html', context)


@admin_comedor_required
def editar_beca_catalogo(request, pk):
    """Edita una beca del catálogo"""
    beca = get_object_or_404(Beca, pk=pk)

    if request.method == 'POST':
        form = BecaForm(request.POST, instance=beca)
        if form.is_valid():
            beca = form.save()
            messages.success(
                request,
                f'✓ Beca "{beca.tipo}" actualizada exitosamente.'
            )
            return redirect('listar_becas')
    else:
        form = BecaForm(instance=beca)

    context = {
        'form': form,
        'beca': beca,
        'titulo': f'Editar Beca: {beca.tipo}',
        'boton': 'Guardar Cambios'
    }

    return render(request, 'comedor/admin/form_beca.html', context)


@admin_comedor_required
def eliminar_beca_catalogo(request, pk):
    """Elimina una beca del catálogo"""
    beca = get_object_or_404(Beca, pk=pk)

    # Verificar si hay estudiantes con esta beca asignada
    asignaciones = PersonaBeca.objects.filter(beca=beca).count()

    if request.method == 'POST':
        if asignaciones > 0:
            messages.error(
                request,
                f'No se puede eliminar la beca "{beca.tipo}" porque tiene {asignaciones} asignación(es) activa(s).'
            )
            return redirect('listar_becas')

        try:
            tipo_beca = beca.tipo
            beca.delete()
            messages.success(request, f'Beca "{tipo_beca}" eliminada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar beca: {str(e)}')

        return redirect('listar_becas')

    context = {
        'beca': beca,
        'asignaciones': asignaciones,
    }

    return render(request, 'comedor/admin/confirmar_eliminacion_beca_catalogo.html', context)


@admin_comedor_required
def toggle_activo_beca(request, pk):
    """Activa/desactiva una beca del catálogo"""
    beca = get_object_or_404(Beca, pk=pk)
    beca.activa = not beca.activa
    beca.save()

    estado = "activada" if beca.activa else "desactivada"
    messages.success(request, f'Beca "{beca.tipo}" {estado} exitosamente.')
    return redirect('listar_becas')