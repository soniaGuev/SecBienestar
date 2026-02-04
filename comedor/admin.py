from django.contrib import admin
from .models import TipoMenu, ConfiguracionMenu, Ticket, CompraTickets, BeneficioComedor


@admin.register(BeneficioComedor)
class BeneficioComedorAdmin(admin.ModelAdmin):
    list_display = ['tipo_beca', 'tipo_beneficio', 'porcentaje_descuento', 'activo']
    list_filter = ['tipo_beneficio', 'activo']
    search_fields = ['tipo_beca']
    list_editable = ['porcentaje_descuento', 'activo']

    fieldsets = (
        ('Información de Beca', {
            'fields': ('tipo_beca',)
        }),
        ('Configuración de Beneficio', {
            'fields': ('tipo_beneficio', 'porcentaje_descuento')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )


@admin.register(TipoMenu)
class TipoMenuAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'precio']
    list_filter = ['tipo']
    search_fields = ['nombre', 'descripcion']


@admin.register(ConfiguracionMenu)
class ConfiguracionMenuAdmin(admin.ModelAdmin):
    list_display = ['menu_comun', 'menu_vegetariano', 'requiere_formulario_celiaquia', 'fecha_actualizacion']
    fieldsets = (
        ('Menús Disponibles', {
            'fields': ('menu_comun', 'menu_vegetariano')
        }),
        ('Configuración de Celiaquía', {
            'fields': ('requiere_formulario_celiaquia',)
        }),
    )

    def has_add_permission(self, request):
        # Solo permitir una configuración
        return not ConfiguracionMenu.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['numero_ticket', 'usuario', 'tipo_menu', 'estado', 'precio_base', 'descuento_aplicado', 'precio_pagado', 'beneficio_aplicado', 'fecha_compra']
    list_filter = ['estado', 'tipo_menu', 'requiere_menu_celiaco', 'fecha_compra', 'beneficio_aplicado']
    search_fields = ['numero_ticket', 'codigo', 'usuario__username']
    readonly_fields = ['codigo', 'numero_ticket', 'qr_code', 'fecha_compra', 'precio_base', 'descuento_aplicado', 'precio_pagado']

    fieldsets = (
        ('Información del Ticket', {
            'fields': ('numero_ticket', 'codigo', 'usuario', 'tipo_menu')
        }),
        ('Precios y Descuentos', {
            'fields': ('precio_base', 'descuento_aplicado', 'precio_pagado',
                      'beneficio_aplicado', 'beca_utilizada')
        }),
        ('Estado', {
            'fields': ('estado', 'fecha_compra', 'fecha_uso', 'fecha_valido_hasta')
        }),
        ('Celiaquía', {
            'fields': ('requiere_menu_celiaco', 'formulario_celiaquia')
        }),
        ('QR Code', {
            'fields': ('qr_code',)
        }),
    )


@admin.register(CompraTickets)
class CompraTicketsAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'cantidad_tickets', 'subtotal', 'total_descuentos', 'total_pagado', 'tickets_con_beneficio', 'fecha_compra']
    list_filter = ['fecha_compra']
    search_fields = ['usuario__username']
    readonly_fields = ['fecha_compra', 'subtotal', 'total_descuentos', 'tickets_con_beneficio']