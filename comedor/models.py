from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import qrcode
from io import BytesIO
from django.core.files import File
import uuid
from decimal import Decimal
from persona.models import Beca


class BeneficioComedor(models.Model):
    """Define el tipo de beneficio que otorga cada beca para el comedor"""
    TIPO_BENEFICIO = [
        ('gratuito', 'Acceso Gratuito (100%)'),
        ('descuento', 'Descuento Porcentual'),
        ('ninguno', 'Sin Beneficio'),
    ]

    tipo_beca = models.ForeignKey(
        'persona.Beca',
        on_delete=models.CASCADE,
        related_name='beneficios',
        verbose_name='Beca asociada'
    )
    tipo_beneficio = models.CharField(
        max_length=20,
        choices=TIPO_BENEFICIO,
        default='ninguno'
    )
    porcentaje_descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Porcentaje de descuento",
        help_text="0-100. Para acceso gratuito usar 100%"
    )

    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Beneficio de Comedor"
        verbose_name_plural = "Beneficios de Comedor"
        ordering = ['tipo_beca']

    def __str__(self):
        if self.tipo_beneficio == 'gratuito' or self.porcentaje_descuento == 100:
            return f"{self.tipo_beca} - Gratuito"
        elif self.tipo_beneficio == 'descuento' and self.porcentaje_descuento > 0:
            return f"{self.tipo_beca} - {self.porcentaje_descuento}% descuento"
        return f"{self.tipo_beca} - Sin beneficio"

    def calcular_precio_final(self, precio_base):
        """Calcula el precio final después de aplicar el descuento"""
        if self.tipo_beneficio == 'gratuito' or self.porcentaje_descuento == 100:
            return Decimal('0.00')
        elif self.tipo_beneficio == 'descuento':
            descuento = precio_base * (self.porcentaje_descuento / 100)
            return precio_base - descuento
        return precio_base

    def calcular_descuento(self, precio_base):
        """Calcula el monto del descuento"""
        if self.tipo_beneficio == 'gratuito' or self.porcentaje_descuento == 100:
            return precio_base
        elif self.tipo_beneficio == 'descuento':
            return precio_base * (self.porcentaje_descuento / 100)
        return Decimal('0.00')


class TipoMenu(models.Model):
    TIPO_CHOICES = [
        ('comun', 'Menú Común'),
        ('vegetariano', 'Menú Vegetariano'),
        ('celiaco_comun', 'Celiaco Comun'),
        ('celiaco_vegetariano', 'Celiaco Vegetariano'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Tipos de Menú"

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"


class ConfiguracionMenu(models.Model):
    """Configuración única del menú que solo admin puede modificar"""
    menu_comun = models.ForeignKey(
        TipoMenu,
        on_delete=models.SET_NULL,
        null=True,
        related_name='config_comun'
    )
    menu_vegetariano = models.ForeignKey(
        TipoMenu,
        on_delete=models.SET_NULL,
        null=True,
        related_name='config_vegetariano'
    )
    menu_celiaco_comun = models.ForeignKey(
        TipoMenu,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='config_celiaco_comun',
        verbose_name="Menú Celíaco Común"
    )
    menu_celiaco_vegetariano = models.ForeignKey(
        TipoMenu,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='config_celiaco_vegetariano',
        verbose_name="Menú Celíaco Vegetariano"
    )

    requiere_formulario_celiaquia = models.BooleanField(default=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Configuración de Menú"
        verbose_name_plural = "Configuración de Menús"

    def save(self, *args, **kwargs):
        # Asegurar que solo exista una configuración
        if not self.pk and ConfiguracionMenu.objects.exists():
            raise ValueError('Solo puede existir una configuración de menú')
        return super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        """Obtener o crear la configuración única"""
        config, created = cls.objects.get_or_create(pk=1)
        return config


class Ticket(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Pago'),
        ('pagado', 'Pagado'),
        ('usado', 'Usado'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Cambiado aquí
        on_delete=models.CASCADE,
        related_name='tickets_comedor'
    )
    tipo_menu = models.ForeignKey(TipoMenu, on_delete=models.PROTECT)

    # Código único del ticket
    codigo = models.CharField(max_length=100, unique=True, editable=False)
    numero_ticket = models.CharField(max_length=20, unique=True, editable=False)

    # QR Code
    qr_code = models.ImageField(upload_to='comedor/qr/', blank=True, null=True)

    # Estado y seguimiento
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')

    # Precios
    precio_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio base del menú",
        default=0
    )
    descuento_aplicado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Descuento aplicado"
    )
    precio_pagado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio final pagado"
    )

    # Información de beneficio aplicado
    beneficio_aplicado = models.ForeignKey(
        BeneficioComedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets_beneficiados',
        verbose_name="Beneficio de beca aplicado"
    )
    beca_utilizada = models.ForeignKey(
        'persona.PersonaBeca',  # Referencia al modelo PersonaBeca
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets_comedor',
        verbose_name="Beca utilizada"
    )

    # Fechas
    fecha_compra = models.DateTimeField(auto_now_add=True)
    fecha_uso = models.DateTimeField(null=True, blank=True)
    fecha_valido_hasta = models.DateField(null=True, blank=True)

    compra = models.ForeignKey(
        'CompraTickets',
        on_delete=models.CASCADE,
        related_name='tickets',
        null=True,
        blank=True
    )

    # Celiaquía
    requiere_menu_celiaco = models.BooleanField(default=False)
    formulario_celiaquia = models.FileField(
        upload_to='comedor/formularios_celiaquia/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )

    class Meta:
        ordering = ['-fecha_compra']
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['estado']),
            models.Index(fields=['usuario', 'estado']),
        ]

    def __str__(self):
        return f"Ticket {self.numero_ticket} - {self.usuario.username}"

    def save(self, *args, **kwargs):
        # Generar código único si no existe
        if not self.codigo:
            self.codigo = str(uuid.uuid4())

        # Generar número de ticket si no existe
        if not self.numero_ticket:
            ultimo_numero = Ticket.objects.count() + 1
            self.numero_ticket = f"TCK-{ultimo_numero:06d}"

        super().save(*args, **kwargs)

        # Generar QR code si no existe
        if not self.qr_code:
            self.generar_qr()

    def generar_qr(self):
        """Genera el código QR para el ticket"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # Datos del QR: código del ticket
        qr.add_data(self.codigo)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Guardar en memoria
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Guardar en el modelo
        filename = f'ticket_{self.numero_ticket}.png'
        self.qr_code.save(filename, File(buffer), save=False)
        buffer.close()

        self.save(update_fields=['qr_code'])

    @property
    def es_gratuito(self):
        """Verifica si el ticket es gratuito por beneficio de beca"""
        return self.precio_pagado == 0 and self.beneficio_aplicado is not None

    @property
    def porcentaje_descuento_aplicado(self):
        """Calcula el porcentaje de descuento aplicado"""
        if self.precio_base > 0:
            return (self.descuento_aplicado / self.precio_base) * 100
        return 0



class CompraTickets(models.Model):
    """Agrupa múltiples tickets en una sola compra"""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Cambiado aquí
        on_delete=models.CASCADE,
        related_name='compras_comedor'
    )
    fecha_compra = models.DateTimeField(auto_now_add=True)
    cantidad_tickets = models.PositiveIntegerField(default=1)

    # Información financiera
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Subtotal (sin descuentos)"
    )
    total_descuentos = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total de descuentos aplicados"
    )
    total_pagado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total final pagado"
    )
    metodo_pago = models.CharField(max_length=50, blank=True)

    # Información de beneficios
    tickets_con_beneficio = models.PositiveIntegerField(
        default=0,
        verbose_name="Cantidad de tickets con beneficio de beca"
    )

    class Meta:
        ordering = ['-fecha_compra']
        verbose_name = "Compra de Tickets"
        verbose_name_plural = "Compras de Tickets"

    def __str__(self):
        return f"Compra {self.id} - {self.usuario.username} - {self.cantidad_tickets} tickets"

    def calcular_totales(self):
        """Calcula los totales basándose en los tickets asociados"""
        tickets = self.tickets.all()
        self.cantidad_tickets = tickets.count()
        self.subtotal = sum(ticket.precio_base for ticket in tickets)
        self.total_descuentos = sum(ticket.descuento_aplicado for ticket in tickets)
        self.total_pagado = sum(ticket.precio_pagado for ticket in tickets)
        self.tickets_con_beneficio = tickets.filter(beneficio_aplicado__isnull=False).count()
        self.save()

def validar_tamano_imagen(image):
        file_size = image.size
        limit_mb = 5
        if file_size > limit_mb * 1024 * 1024:
            image.error = ValidationError(f'El tamaño máximo de archivo es {limit_mb}MB')
            raise image.error

class ImagenCarrusel(models.Model):
        DIAS_SEMANA = [
            ('lunes', 'Lunes'),
            ('martes', 'Martes'),
            ('miercoles', 'Miércoles'),
            ('jueves', 'Jueves'),
            ('viernes', 'Viernes'),
        ]

        titulo = models.CharField(max_length=200, help_text="Título que aparecerá en el carrusel")
        descripcion = models.TextField(blank=True, null=True, help_text="Descripción de la comida del día")
        imagen = models.ImageField(
            upload_to='carrusel/%Y/%m/',
            validators=[
                FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
                validar_tamano_imagen
            ],
            help_text="Formatos permitidos: JPG, PNG, WEBP. Tamaño máximo: 5MB"
        )
        dia_semana = models.CharField(max_length=20, choices=DIAS_SEMANA, blank=True, null=True)
        activo = models.BooleanField(default=True, help_text="¿Mostrar en el carrusel?")
        orden = models.IntegerField(default=0, help_text="Orden de aparición (menor número = primero)")
        fecha_desde = models.DateField(blank=True, null=True, help_text="Fecha desde la que se mostrará")
        fecha_hasta = models.DateField(blank=True, null=True, help_text="Fecha hasta la que se mostrará")
        fecha_creacion = models.DateTimeField(auto_now_add=True)
        fecha_modificacion = models.DateTimeField(auto_now=True)
        usuario_creador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='imagenes_creadas')

        class Meta:
            ordering = ['orden', 'dia_semana']
            verbose_name = 'Imagen de Carrusel'
            verbose_name_plural = 'Imágenes de Carrusel'

        def __str__(self):
            dia = self.get_dia_semana_display() if self.dia_semana else "General"
            return f'{self.titulo} - {dia}'

        def clean(self):
            if self.fecha_desde and self.fecha_hasta:
                if self.fecha_desde > self.fecha_hasta:
                    raise ValidationError(
                        'La fecha de inicio no puede ser posterior a la fecha de fin'
                    )

class CertificadoCeliaco(models.Model):
    """Certificado médico de celiaquía para cualquier persona"""
    persona = models.OneToOneField(
        'persona.Persona',
        on_delete=models.CASCADE,
        related_name='certificado_celiaco',
        verbose_name="Persona"
    )
    archivo_certificado = models.FileField(
        upload_to='comedor/certificados_celiacos/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        verbose_name="Certificado Médico"
    )
    fecha_emision = models.DateField(verbose_name="Fecha de emisión del certificado")
    fecha_vencimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de vencimiento"
    )
    activo = models.BooleanField(default=True, verbose_name="¿Certificado vigente?")
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )
    fecha_carga = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    cargado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='certificados_celiacos_cargados',
        verbose_name="Cargado por"
    )

    class Meta:
        verbose_name = "Certificado de Celiaquía"
        verbose_name_plural = "Certificados de Celiaquía"
        ordering = ['-fecha_carga']

    def __str__(self):
        return f"Certificado celíaco - {self.persona.nombre_completo}"

    @property
    def esta_vigente(self):
        """Verifica si el certificado está vigente"""
        from datetime import date
        if not self.activo:
            return False
        if self.fecha_vencimiento:
            return date.today() <= self.fecha_vencimiento
        return True

    def clean(self):
        from datetime import date
        if self.fecha_vencimiento and self.fecha_emision:
            if self.fecha_vencimiento < self.fecha_emision:
                raise ValidationError(
                    'La fecha de vencimiento no puede ser anterior a la fecha de emisión'
                )