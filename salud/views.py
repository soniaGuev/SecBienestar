from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from .models import (
    CoberturaSalud,
    TurnoSalud,
    AtencionSalud,
    RegistroIntegracion,
    AfiliacionSalud,
    IntegracionPrestadorSalud,
)

@login_required
def dashboard_salud(request):
    cobertura = (
        CoberturaSalud.objects
        .select_related("plan", "plan__prestador")
        .filter(persona=request.user.persona, activa=True)
        .first()
    )

    ultimo_pago = None
    if cobertura:
        ultimo_pago = cobertura.pagos.order_by("-fecha_creacion").first()

    turnos = (
        TurnoSalud.objects
        .select_related("prestador", "cobertura")
        .filter(persona=request.user.persona, fecha_hora__gte=timezone.now())
        .order_by("fecha_hora")[:5]
    )

    historial = (
        AtencionSalud.objects
        .select_related("prestador", "cobertura")
        .filter(persona=request.user.persona)
        .order_by("-fecha")[:5]
    )

    afiliacion = None
    if cobertura:
        afiliacion = (
            AfiliacionSalud.objects
            .select_related("prestador")
            .filter(persona=request.user.persona, prestador=cobertura.plan.prestador)
            .first()
        )
    if afiliacion is None:
        afiliacion = (
            AfiliacionSalud.objects
            .select_related("prestador")
            .filter(persona=request.user.persona)
            .order_by("-ultima_actualizacion")
            .first()
        )

    integracion = None
    if afiliacion:
        integracion = (
            IntegracionPrestadorSalud.objects
            .select_related("prestador")
            .filter(prestador=afiliacion.prestador)
            .first()
        )

    ultima_integracion = (
        RegistroIntegracion.objects
        .filter(persona=request.user.persona)
        .select_related("prestador")
        .order_by("-fecha")
        .first()
    )

    return render(
        request,
        "salud/dashboard.html",
        {
            "cobertura": cobertura,
            "ultimo_pago": ultimo_pago,
            "turnos": turnos,
            "historial": historial,
            "afiliacion": afiliacion,
            "integracion": integracion,
            "ultima_integracion": ultima_integracion,
        }
    )
def home(request):
    return render(request, "salud/home.html")
