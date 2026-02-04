from django.urls import path
from .views import dashboard_salud
from . import views   # 👈 ESTA línea faltaba

app_name = "salud"

urlpatterns = [
    path("", dashboard_salud, name="dashboard"),
    path("", views.home, name="home"),
]
