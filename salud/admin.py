from django.contrib import admin

from .models import (
    PrestadorSalud,
    PlanSalud,
    CoberturaSalud,
    PagoSalud,
    RegistroIntegracion,
    IntegracionPrestadorSalud,
    AfiliacionSalud,
    TurnoSalud,
    AtencionSalud,
)


@admin.register(PrestadorSalud)
class PrestadorSaludAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "activo")
    search_fields = ("nombre", "codigo")
    list_filter = ("activo",)


@admin.register(PlanSalud)
class PlanSaludAdmin(admin.ModelAdmin):
    list_display = ("nombre", "prestador", "precio_mensual", "precio_anual", "activo")
    search_fields = ("nombre", "prestador__nombre")
    list_filter = ("activo", "prestador")


@admin.register(CoberturaSalud)
class CoberturaSaludAdmin(admin.ModelAdmin):
    list_display = ("persona", "plan", "fecha_inicio", "fecha_fin", "activa", "esta_vigente")
    search_fields = ("persona__nombre", "persona__apellido", "plan__nombre")
    list_filter = ("activa", "plan__prestador")


@admin.register(PagoSalud)
class PagoSaludAdmin(admin.ModelAdmin):
    list_display = ("cobertura", "monto", "tipo", "estado", "fecha_creacion", "fecha_pago")
    list_filter = ("tipo", "estado")
    search_fields = ("cobertura__persona__nombre", "cobertura__persona__apellido")


@admin.register(RegistroIntegracion)
class RegistroIntegracionAdmin(admin.ModelAdmin):
    list_display = ("prestador", "persona", "estado", "endpoint", "fecha")
    list_filter = ("estado", "prestador")
    search_fields = ("prestador__nombre", "persona__nombre", "persona__apellido")


@admin.register(IntegracionPrestadorSalud)
class IntegracionPrestadorSaludAdmin(admin.ModelAdmin):
    list_display = ("prestador", "auth_tipo", "base_url", "activo", "ultima_sincronizacion")
    list_filter = ("auth_tipo", "activo")
    search_fields = ("prestador__nombre", "base_url")


@admin.register(AfiliacionSalud)
class AfiliacionSaludAdmin(admin.ModelAdmin):
    list_display = ("persona", "prestador", "numero_afiliado", "plan_nombre", "estado", "ultima_actualizacion")
    list_filter = ("estado", "prestador")
    search_fields = ("persona__nombre", "persona__apellido", "numero_afiliado", "plan_nombre")


@admin.register(TurnoSalud)
class TurnoSaludAdmin(admin.ModelAdmin):
    list_display = ("persona", "prestador", "especialidad", "fecha_hora", "estado", "fuente")
    list_filter = ("estado", "fuente", "prestador")
    search_fields = ("persona__nombre", "persona__apellido", "especialidad", "profesional")


@admin.register(AtencionSalud)
class AtencionSaludAdmin(admin.ModelAdmin):
    list_display = ("persona", "prestador", "especialidad", "fecha", "fuente")
    list_filter = ("fuente", "prestador")
    search_fields = ("persona__nombre", "persona__apellido", "especialidad", "profesional")
