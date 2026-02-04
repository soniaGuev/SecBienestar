from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
# from posts import urls
from accounts import views

urlpatterns = [
    # path("", views.update_profile, name='profile'),
    path("", views.home, name='home'),
    # admin
    path('admin/', admin.site.urls),
    path('captcha/', include('captcha.urls')),
    # allauth & accounts
    path('accounts/', include('allauth.urls')),
    path('accounts/', include("accounts.urls", namespace="accounts")),

    path('comedor/', include('comedor.urls')),

    path('persona/', include('persona.urls')),

    path("salud/", include("salud.urls")),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
