from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import CoberturaSalud

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

    return render(
        request,
        "salud/dashboard.html",
        {
            "cobertura": cobertura,
            "ultimo_pago": ultimo_pago
        }
    )
def home(request):
    return render(request, "salud/home.html")
