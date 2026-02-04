from django.db import models
from django.utils import timezone
from persona.models import Persona


#PrestadorSalud
class PrestadorSalud(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Prestador de Salud"
        verbose_name_plural = "Prestadores de Salud"

    def __str__(self):
        return self.nombre

#Plan de Salud

class PlanSalud(models.Model):
    nombre = models.CharField(max_length=100)
    prestador = models.ForeignKey(
        PrestadorSalud,
        on_delete=models.PROTECT,
        related_name="planes"
    )
    precio_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    precio_anual = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Plan de Salud"
        verbose_name_plural = "Planes de Salud"

    def __str__(self):
        return f"{self.nombre} ({self.prestador.nombre})"

#Cobertura del Estudiante

class CoberturaSalud(models.Model):
    persona = models.OneToOneField(
        Persona,
        on_delete=models.CASCADE,
        related_name="cobertura_salud"
    )
    plan = models.ForeignKey(
        PlanSalud,
        on_delete=models.PROTECT
    )
    fecha_inicio = models.DateField(default=timezone.now)
    fecha_fin = models.DateField(null=True, blank=True)
    activa = models.BooleanField(default=True)
    numero_afiliado_externo = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Cobertura de Salud"
        verbose_name_plural = "Coberturas de Salud"

    def __str__(self):
        return f"{self.persona} - {self.plan}"

#Pagos de Salud
class PagoSalud(models.Model):
    TIPO_PAGO = (
        ("mensual", "Mensual"),
        ("anual", "Anual"),
    )

    ESTADO = (
        ("pendiente", "Pendiente"),
        ("pagado", "Pagado"),
        ("rechazado", "Rechazado"),
    )

    cobertura = models.ForeignKey(
        CoberturaSalud,
        on_delete=models.CASCADE,
        related_name="pagos"
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=10, choices=TIPO_PAGO)
    estado = models.CharField(max_length=10, choices=ESTADO, default="pendiente")
    referencia_pago = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_pago = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Pago de Salud"
        verbose_name_plural = "Pagos de Salud"

    def __str__(self):
        return f"{self.cobertura.persona} - {self.monto}"

#Registro de Integraciones Externas
class RegistroIntegracion(models.Model):
    prestador = models.ForeignKey(
        PrestadorSalud,
        on_delete=models.PROTECT
    )
    persona = models.ForeignKey(
        Persona,
        on_delete=models.CASCADE
    )
    endpoint = models.CharField(max_length=100)
    estado = models.CharField(max_length=50)
    mensaje = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Integración"
        verbose_name_plural = "Registros de Integración"

    def __str__(self):
        return f"{self.prestador} - {self.estado}"







