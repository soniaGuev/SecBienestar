from django.urls import path
from . import views

urlpatterns = [
    path('comprar/', views.comprar_tickets, name='comprar_tickets'),
    path('generar-gratuito/', views.generar_ticket_gratuito, name='generar_ticket_gratuito'),
    path('mis-tickets/', views.mis_tickets, name='mis_tickets'),
    path('ticket/<int:ticket_id>/', views.detalle_ticket, name='detalle_ticket'),

    path('actividades/', views.actividades_auditor, name='actividades_auditor'),

    # Vista pública
    path('carrousel/', views.carrousel_view, name='carrousel'),
    path('panel_comedor', views.panel_comedor, name='panel_comedor'),

    # Panel de administración
    path('admin/panel/', views.panel_admin, name='panel_admin'),
    path('admin/imagenes/', views.listar_imagenes, name='listar_imagenes'),
    path('admin/imagenes/nueva/', views.crear_imagen, name='crear_imagen'),
    path('admin/imagenes/<int:pk>/editar/', views.editar_imagen, name='editar_imagen'),
    path('admin/imagenes/<int:pk>/eliminar/', views.eliminar_imagen, name='eliminar_imagen'),
    path('admin/imagenes/<int:pk>/toggle/', views.toggle_activo, name='toggle_activo'),

    # Gestión de menús
    path('admin/menus/', views.listar_menus, name='listar_menus'),
    path('admin/menus/nuevo/', views.crear_menu, name='crear_menu'),
    path('admin/menus/<int:pk>/editar/', views.editar_menu, name='editar_menu'),
    path('admin/menus/<int:pk>/eliminar/', views.eliminar_menu, name='eliminar_menu'),
    path('admin/menus/<int:pk>/toggle/', views.toggle_activo_menu, name='toggle_activo_menu'),

    # Gestion de Beneficios

    path('admin/beneficios/', views.listar_beneficios, name='listar_beneficios'),
    path('admin/beneficios/crear/', views.crear_beneficio, name='crear_beneficio'),
    path('admin/beneficios/<int:pk>/editar/', views.editar_beneficio, name='editar_beneficio'),
    path('admin/beneficios/<int:pk>/eliminar/', views.eliminar_beneficio, name='eliminar_beneficio'),
    path('admin/beneficios/<int:pk>/toggle/', views.toggle_activo_beneficio, name='toggle_activo_beneficio'),

    # Gestión de Beneficiarios
    path('admin/beneficiarios/', views.listar_beneficiarios, name='listar_beneficiarios'),
    path('admin/beneficiarios/<int:estudiante_id>/', views.detalle_beneficiario, name='detalle_beneficiario'),
    path('admin/beneficiarios/<int:estudiante_id>/asignar-beca/', views.asignar_beca, name='asignar_beca'),
    path('admin/becas/<int:beca_id>/editar/', views.editar_beca, name='editar_beca'),
    path('admin/becas/<int:beca_id>/eliminar/', views.eliminar_beca, name='eliminar_beca'),
    path('admin/buscar-estudiante/', views.buscar_estudiante, name='buscar_estudiante'),

    # Gestión de Becas
    path('admin/becas-catalogo/', views.listar_becas, name='listar_becas'),
    path('admin/becas-catalogo/crear/', views.crear_beca, name='crear_beca_catalogo'),
    path('admin/becas-catalogo/<int:pk>/editar/', views.editar_beca_catalogo, name='editar_beca_catalogo'),
    path('admin/becas-catalogo/<int:pk>/eliminar/', views.eliminar_beca_catalogo, name='eliminar_beca_catalogo'),
    path('admin/becas-catalogo/<int:pk>/toggle/', views.toggle_activo_beca, name='toggle_activo_beca'),
]
