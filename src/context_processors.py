from django.conf import settings

def variable_global(request):
    return {
        'REGISTRO': settings.REGISTRO,
        'NOMBRE': settings.NOMBRE,
        'LOGO': settings.LOGO,
        'LOGO_ANCHO': settings.LOGO_ANCHO,
        'LOGO_ALTO': settings.LOGO_ALTO,
        'BARRA': settings.BARRA,
        'BARRA_ALTO': settings.BARRA_ALTO,
        'DESCRIPCION': settings.DESCRIPCION,
    }

