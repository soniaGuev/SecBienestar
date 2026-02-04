from django.urls import path
from .views import dashboard_salud
from . import views

app_name = "salud"

urlpatterns = [
    path("", dashboard_salud, name="dashboard"),
    path("home/", views.home, name="home"),
]
