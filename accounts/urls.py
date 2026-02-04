from django.urls import path, include
from . import views

app_name = "accounts"

urlpatterns = [
    # Perfil
    path("profile/", views.ver_perfil, name='profile'),
    path("perfil/", views.ver_perfil, name='ver_perfil'),
    path("perfil/editar/", views.editar_perfil, name='editar_perfil'),
    path("perfil/cambiar-menu/", views.cambiar_preferencia_menu, name='cambiar_preferencia_menu'),

    # Público
    path("u/<str:username>/", views.public_profile, name='public-profile'),

    # Autenticación
    path('logout/', views.signout, name='logout'),

    # Onboarding
    path('seleccionar-rol/', views.seleccionar_rol, name='seleccionar_rol'),
    path('completar-perfil/', views.profile_complete, name='profile_complete'),
]
