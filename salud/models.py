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

    @property
    def esta_vigente(self):
        if not self.activa:
            return False
        if self.fecha_fin and self.fecha_fin < timezone.now().date():
            return False
        return True

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


class IntegracionPrestadorSalud(models.Model):
    TIPOS_AUTH = (
        ("api_key", "API Key"),
        ("bearer", "Bearer Token"),
        ("oauth2", "OAuth2"),
    )

    prestador = models.OneToOneField(
        PrestadorSalud,
        on_delete=models.CASCADE,
        related_name="integracion"
    )
    base_url = models.URLField(max_length=200)
    auth_tipo = models.CharField(max_length=20, choices=TIPOS_AUTH)
    token_url = models.URLField(max_length=200, blank=True)
    client_id = models.CharField(max_length=120, blank=True)
    client_secret = models.CharField(max_length=120, blank=True)
    scope = models.CharField(max_length=200, blank=True)
    api_key_header = models.CharField(max_length=50, blank=True)
    api_key_value = models.CharField(max_length=120, blank=True)
    timeout_segundos = models.PositiveIntegerField(default=10)
    activo = models.BooleanField(default=True)
    ultima_sincronizacion = models.DateTimeField(blank=True, null=True)
    ultimo_estado = models.CharField(max_length=50, blank=True)
    ultimo_mensaje = models.TextField(blank=True)

    class Meta:
        verbose_name = "Integración de Prestador"
        verbose_name_plural = "Integraciones de Prestadores"

    def __str__(self):
        return f"{self.prestador.nombre} ({self.get_auth_tipo_display()})"


class AfiliacionSalud(models.Model):
    ESTADOS = (
        ("activa", "Activa"),
        ("suspendida", "Suspendida"),
        ("baja", "Baja"),
        ("pendiente", "Pendiente"),
    )

    persona = models.ForeignKey(
        Persona,
        on_delete=models.CASCADE,
        related_name="afiliaciones_salud"
    )
    prestador = models.ForeignKey(
        PrestadorSalud,
        on_delete=models.PROTECT,
        related_name="afiliaciones"
    )
    numero_afiliado = models.CharField(max_length=80, blank=True)
    plan_nombre = models.CharField(max_length=120, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADOS, default="pendiente")
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    payload = models.JSONField(blank=True, null=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "Afiliación de Salud"
        verbose_name_plural = "Afiliaciones de Salud"
        unique_together = ("persona", "prestador")

    def __str__(self):
        return f"{self.persona} - {self.prestador.nombre}"


class TurnoSalud(models.Model):
    ESTADOS = (
        ("pendiente", "Pendiente"),
        ("confirmado", "Confirmado"),
        ("cancelado", "Cancelado"),
        ("atendido", "Atendido"),
    )

    FUENTE = (
        ("integracion", "Integración"),
        ("manual", "Manual"),
    )

    persona = models.ForeignKey(
        Persona,
        on_delete=models.CASCADE,
        related_name="turnos_salud"
    )
    prestador = models.ForeignKey(
        PrestadorSalud,
        on_delete=models.PROTECT,
        related_name="turnos"
    )
    cobertura = models.ForeignKey(
        CoberturaSalud,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="turnos"
    )
    fecha_hora = models.DateTimeField()
    especialidad = models.CharField(max_length=100)
    profesional = models.CharField(max_length=100, blank=True)
    ubicacion = models.CharField(max_length=150, blank=True)
    motivo = models.CharField(max_length=150, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADOS, default="pendiente")
    fuente = models.CharField(max_length=15, choices=FUENTE, default="integracion")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Turno de Salud"
        verbose_name_plural = "Turnos de Salud"
        ordering = ["fecha_hora"]

    def __str__(self):
        return f"{self.persona} - {self.especialidad} ({self.fecha_hora:%d/%m/%Y %H:%M})"


class AtencionSalud(models.Model):
    FUENTE = (
        ("integracion", "Integración"),
        ("manual", "Manual"),
    )

    persona = models.ForeignKey(
        Persona,
        on_delete=models.CASCADE,
        related_name="atenciones_salud"
    )
    prestador = models.ForeignKey(
        PrestadorSalud,
        on_delete=models.PROTECT,
        related_name="atenciones"
    )
    cobertura = models.ForeignKey(
        CoberturaSalud,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="atenciones"
    )
    turno = models.ForeignKey(
        "TurnoSalud",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="atenciones"
    )
    fecha = models.DateField(default=timezone.now)
    especialidad = models.CharField(max_length=100)
    profesional = models.CharField(max_length=100, blank=True)
    diagnostico = models.CharField(max_length=200, blank=True)
    tratamiento = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    fuente = models.CharField(max_length=15, choices=FUENTE, default="integracion")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Atención de Salud"
        verbose_name_plural = "Atenciones de Salud"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.persona} - {self.especialidad} ({self.fecha:%d/%m/%Y})"





