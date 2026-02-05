from django.urls import path
from .views import dashboard_salud
from . import views

app_name = "salud"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", dashboard_salud, name="dashboard"),
]
