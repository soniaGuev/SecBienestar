from django.urls import path
from . import views

urlpatterns = [
    # Gestión de personas (admin_comedor)
    path('admin/personas', views.panel_persona, name='panel_persona'),
    path('admin/personas/', views.listar_personas, name='listar_personas'),
    path('admin/personas/<int:persona_id>/', views.detalle_persona, name='detalle_persona'),
    path('admin/personas/<int:persona_id>/editar/', views.editar_persona, name='editar_persona'),
    path('admin/personas/<int:persona_id>/eliminar/', views.eliminar_persona, name='eliminar_persona'),
    path('admin/personas/<int:persona_id>/observacion/', views.agregar_observacion, name='agregar_observacion'),

    # Auditoría (solo auditor)
    path('auditor/personas/<int:persona_id>/historial/', views.historial_completo, name='historial_completo'),
    path('auditor/historial/', views.historial_general, name='historial_general'),
]