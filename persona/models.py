from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, EmailValidator
from datetime import date


class Dependencia(models.Model):
    """Unidad Académica"""
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        verbose_name = "Dependencia"
        verbose_name_plural = "Dependencias"

    def __str__(self):
        return self.nombre


class Carrera(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la carrera")
    dependencia = models.ForeignKey('Dependencia', on_delete=models.CASCADE, related_name='carreras')
    activa = models.BooleanField(default=True)
    plan_estudio = models.CharField(max_length=200, verbose_name="Plan de estudio")
    anio_programa = models.PositiveIntegerField(verbose_name="Año de Programa")

    class Meta:
        verbose_name = "Carrera"
        verbose_name_plural = "Carreras"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Area(models.Model):
    """Áreas de trabajo personal no docente"""
    nombre = models.CharField(max_length=200, verbose_name="Nombre del área")

    class Meta:
        verbose_name = "Área"
        verbose_name_plural = "Áreas"

    def __str__(self):
        return self.nombre


class Persona(models.Model):
    TIPOS_DOCUMENTO = [
        ('DNI', 'DNI'),
        ('PASAPORTE', 'Pasaporte'),
        ('EXTRANJERO', 'Documento Extranjero'),
        ('CUIL', 'CUIL'),
    ]

    GENERO = [
        ('femenino', 'Femenino'),
        ('masculino', 'Masculino'),
        ('no_binario', 'No Binario'),
        ('trans_femenino', 'Trans Femenino'),
        ('trans_masculino', 'Trans Masculino'),
        ('otro', 'Otro'),
        ('prefiero_no_decir', 'Prefiero no decir'),
    ]

    ROLES = [
        ('ingresante', 'Ingresante'),
        ('estudiante', 'Estudiante'),
        ('egresado', 'Egresado'),
        ('docente', 'Docente'),
        ('no_docente', 'No Docente'),
        ('admin_comedor', 'Administrador de Comedor'),
        ('admin', 'Administrador General'),
        ('auditor', 'Auditor'),
    ]

    SEDES = [
        ('central', 'Central'),
        ('san_rafael', 'San Rafael'),
        ('lujan_de_cuyo', 'Luján de Cuyo')
    ]

    nombre = models.CharField(max_length=100)
    nombre_percibido = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Nombre percibido"
    )
    apellido = models.CharField(max_length=100)
    tipo_documento = models.CharField(
        max_length=15,
        choices=TIPOS_DOCUMENTO,
        default='DNI',
        verbose_name="Tipo de documento"
    )
    documento = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(r'^[0-9]+$', 'Solo se permiten números')],
        verbose_name="Número de documento"
    )
    genero = models.CharField(
        max_length=20,
        choices=GENERO,
        verbose_name="Identidad de género",
        default='prefiero_no_decir'
    )
    nacionalidad = models.TextField()
    sede = models.CharField(choices=SEDES, max_length=25, default='central', verbose_name="Tipo de sede")
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.EmailField(
        validators=[EmailValidator()],
        unique=True
    )

    correo_personal = models.EmailField(validators=[EmailValidator()], null=True)

    ddjj_identidad = models.FileField(
        upload_to='ddjj_identidad/',
        blank=True,
        null=True,
        verbose_name="DDJJ de identidad percibida"
    )

    nombre_percibido_validado = models.BooleanField(
        default=False,
        verbose_name="Nombre percibido validado"
    )

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='persona')

    rol = models.CharField(max_length=20, choices=ROLES, default='', blank=True)

    contacto_emergencia_nombre = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Nombre de contacto de emergencia"
    )

    contacto_emergencia_telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono de contacto de emergencia"
    )

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        indexes = [
            models.Index(fields=['documento']),
            models.Index(fields=['rol']),
        ]

    def get_nombre_visible(self):
        """
        Retorna el nombre que debe verse en el sistema.
        Si existe nombre percibido y está validado → priorizarlo.
        Si no, usar el nombre legal.
        """
        if self.nombre_percibido and self.nombre_percibido_validado:
            return self.nombre_percibido
        return self.nombre  # nombre legal del documento

    @property
    def nombre_completo(self):
        """
        Nombre + apellido, priorizando nombre percibido si corresponde.
        """
        return f"{self.get_nombre_visible()} {self.apellido}"

    def __str__(self):
        return self.nombre_completo

    @property
    def perfil_completo(self):
        """Verifica si el perfil está completo"""
        return not self.documento.startswith('TEMP_')


class Beca(models.Model):
    tipo = models.CharField(max_length=100, verbose_name="Nombre de la Beca")
    activa = models.BooleanField(default=True)

    tiene_monto = models.BooleanField(
        default=False,
        verbose_name="¿Otorga monto monetario?",
        help_text="Si esta beca otorga un monto mensual/anual de dinero"
    )
    monto_sugerido = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Monto sugerido",
        help_text="Monto sugerido por defecto (puede modificarse por beneficiario)"
    )
    permite_comedor = models.BooleanField(
        default=False,
        verbose_name="¿Permite beneficio de comedor?",
        help_text="Si este tipo de beca puede tener beneficio de comedor asociado"
    )

    class Meta:
        verbose_name = "Beca"
        verbose_name_plural = "Becas"

    def __str__(self):
        return f'{self.tipo}'

    def clean(self):
        """Validación: si tiene_monto es True, debe tener un monto_sugerido"""
        if self.tiene_monto and not self.monto_sugerido:
            raise ValidationError({
                'monto_sugerido': 'Debe especificar un monto sugerido si la beca otorga dinero'
            })


class PersonaEstudiante(models.Model):
    ESTADOS_ACADEMICOS = [
        ('R', 'Regular'),
        ('L', 'Libre'),
        ('C', 'Condicional'),
        ('E', 'Egresado'),
        ('A', 'Abandono'),
    ]

    PREFERENCIA_MENU = [
        ('comun', 'Menú Común'),
        ('vegetariano', 'Menú Vegetariano'),
        ('celiaco_comun', 'Celiaco Comun'),
        ('celiaco_vegetariano', 'Celiaco Vegetariano'),
    ]

    persona = models.OneToOneField(Persona, on_delete=models.CASCADE, related_name='estudiante')
    dependencia = models.ForeignKey(Dependencia, on_delete=models.SET_NULL, null=True, related_name='estudiantes')
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, verbose_name="Carrera", related_name='estudiantes')
    anio_ingreso = models.PositiveIntegerField(verbose_name="Año de ingreso")
    numero_legajo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de legajo"
    )
    estado_academico = models.CharField(
        max_length=15,
        choices=ESTADOS_ACADEMICOS,
        default='REGULAR',
        verbose_name="Estado académico"
    )

    preferencia_menu = models.CharField(
        max_length=20,
        choices=PREFERENCIA_MENU,
        default='comun',
        verbose_name="Preferencia de menú",
        help_text="Tipo de menú preferido para el comedor"
    )

    fecha_ultima_modificacion_menu = models.DateField(
        null=True,
        blank=True,
        verbose_name="Última modificación de preferencia de menú"
    )

    ddjj_celiaco = models.FileField(
        upload_to='ddjj_celiaco/',
        blank=True,
        null=True,
        verbose_name="DDJJ o certificado médico de celíaco",
        help_text="Declaración jurada o certificado médico que acredite condición celíaca"
    )

    fecha_vencimiento_ddjj_celiaco = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fecha de vencimiento de DDJJ celíaco",
        help_text="Fecha hasta la cual es válida la documentación"
    )

    celiaco_validado = models.BooleanField(
        default=False,
        verbose_name="Condición celíaca validada",
        help_text="Indica si la documentación fue revisada y aprobada"
    )

    fecha_validacion_celiaco = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de validación celíaco"
    )

    validado_celiaco_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='celiaco_validados',
        verbose_name="Validado por (celíaco)"
    )

    certificado_regular = models.FileField(
        upload_to='certificados_alumno_regular/',
        blank=True,
        null=True,
        verbose_name="Certificado de alumno regular"
    )

    fecha_vencimiento_certificado = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fecha de vencimiento del certificado"
    )

    carta_aceptacion = models.FileField(
        upload_to='cartas_aceptacion/',
        blank=True,
        null=True,
        verbose_name="Carta de aceptación (solo extranjeros)"
    )

    fecha_vencimiento_carta = models.DateField(
        blank=True,
        null=True,
        verbose_name="Vigencia de carta de aceptación"
    )

    validado_como_regular = models.BooleanField(
        default=False,
        verbose_name="Validado como alumno regular"
    )
    fecha_validacion_regular = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de validación"
    )
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='estudiantes_validados',
        verbose_name="Validado por"
    )

    observaciones_validacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones de la validación"
    )


    class Meta:
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"
        indexes = [
            models.Index(fields=['numero_legajo']),
            models.Index(fields=['carrera']),
            models.Index(fields=['estado_academico']),
        ]

    def clean(self):
        """Validación personalizada"""
        super().clean()

        # Validar que si elige menú celíaco, debe tener DDJJ
        if 'celiaco' in self.preferencia_menu.lower():
            if not self.ddjj_celiaco:
                raise ValidationError({
                    'ddjj_celiaco': 'Debe cargar la DDJJ o certificado médico para menú celíaco.'
                })

        # Validación existente para extranjeros
        if self.persona_id and self.persona and self.persona.nacionalidad.lower() != "argentina":
            if not self.carta_aceptacion:
                raise ValidationError({
                    'carta_aceptacion': 'La carta de aceptación es obligatoria para estudiantes extranjeros.'
                })

    def __str__(self):
        return f"{self.persona.nombre_completo} - Legajo: {self.numero_legajo}"

    @property
    def ddjj_celiaco_vigente(self):
        """Verifica si la DDJJ de celíaco está vigente"""
        if not self.fecha_vencimiento_ddjj_celiaco:
            return None
        from datetime import date
        return self.fecha_vencimiento_ddjj_celiaco >= date.today()


class PersonaIngresante(models.Model):
    persona = models.OneToOneField(Persona, on_delete=models.CASCADE, related_name='ingresante')

    certificado_ingreso = models.FileField(
        upload_to='certificados_ingreso/',
        blank=True,
        null=True,
        verbose_name="Certificado de ingreso o inscripción"
    )

    fecha_vencimiento = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Ingresante: {self.persona.nombre_completo}"


class PersonaEgresado(models.Model):
    persona = models.OneToOneField(Persona, on_delete=models.CASCADE, related_name='egresado')

    certificado_egreso = models.FileField(
        upload_to='certificados_egreso/',
        blank=True,
        null=True,
        verbose_name="Certificado de egreso (opcional)"
    )

    # agregar validacion ,

    @property
    def es_invitado(self):
        return True

    def __str__(self):
        return f"Egresado: {self.persona.nombre_completo}"


class PersonaBeca(models.Model):
    ESTADOS_BECA = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('ACTIVA', 'Activa'),
        ('VENCIDA', 'Vencida'),
        ('SUSPENDIDA', 'Suspendida'),
        ('RECHAZADA', 'Rechazada'),
    ]

    persona_estudiante = models.ForeignKey(PersonaEstudiante, on_delete=models.CASCADE, related_name='becas', null=True,
                                           blank=True)
    persona_ingresante = models.ForeignKey(PersonaIngresante, on_delete=models.CASCADE, related_name='becas', null=True,
                                           blank=True)
    beca = models.ForeignKey(Beca, on_delete=models.CASCADE)
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name="Fecha de inicio")
    fecha_fin = models.DateField(null=True, blank=True, verbose_name="Fecha de fin")
    estado_beca = models.CharField(
        max_length=15,
        choices=ESTADOS_BECA,
        default='PENDIENTE',
        verbose_name="Estado de la beca"
    )
    fecha_aprobacion = models.DateTimeField(blank=True, null=True)

    monto_asignado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Monto asignado",
        help_text="Monto específico otorgado a este beneficiario"
    )

    class Meta:
        verbose_name = "Persona - Beca"
        verbose_name_plural = "Personas - Becas"
        unique_together = ['persona_estudiante', 'beca', 'fecha_inicio']

    def __str__(self):
        return f'{self.persona_estudiante.persona.nombre_completo} - {self.beca.tipo}'

    def clean(self):
        # Validación de fechas
        if self.fecha_fin and self.fecha_inicio and self.fecha_fin <= self.fecha_inicio:
            raise ValidationError({
                'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio'
            })

        if self.persona_estudiante and self.persona_ingresante:
            raise ValidationError("Solo puede asignar una persona (estudiante o ingresante)")

        # Validación: si la beca tiene_monto, debe asignarse un monto
        if self.beca and self.beca.tiene_monto and not self.monto_asignado:
            raise ValidationError({
                'monto_asignado': f'Esta beca ({self.beca.tipo}) requiere asignar un monto'
            })

        # Validación: si la beca NO tiene_monto, no debería tener monto_asignado
        if self.beca and not self.beca.tiene_monto and self.monto_asignado:
            raise ValidationError({
                'monto_asignado': f'Esta beca ({self.beca.tipo}) no contempla monto monetario'
            })

    @property
    def monto_a_pagar(self):
        """Retorna el monto a pagar si existe"""
        return self.monto_asignado if self.monto_asignado else 0

    @property
    def difiere_monto_sugerido(self):
        """Verifica si el monto asignado difiere del sugerido"""
        if self.beca and self.beca.monto_sugerido and self.monto_asignado:
            return self.monto_asignado != self.beca.monto_sugerido
        return False


class Observacion(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    persona_beca = models.ForeignKey(PersonaBeca, on_delete=models.SET_NULL, blank=True, null=True)
    observacion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    descripcion_cambio = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción del cambio realizado"
    )

    # AGREGAR ESTOS CAMPOS:
    tipo_accion = models.CharField(
        max_length=20,
        choices=[
            ('creacion', 'Creación'),
            ('modificacion', 'Modificación'),
            ('eliminacion', 'Eliminación'),
            ('observacion', 'Observación'),
        ],
        default='observacion',
        verbose_name="Tipo de acción"
    )

    datos_modificados = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Datos modificados (JSON)",
        help_text="Almacena qué campos se modificaron y sus valores"
    )

    class Meta:
        verbose_name = "Observación"
        verbose_name_plural = "Observaciones"
        ordering = ['-fecha']

    def __str__(self):
        return f'Observación de {self.persona.nombre_completo} - {self.fecha.strftime("%d/%m/%Y")}'


class PersonaDocente(models.Model):
    CATEGORIAS_DOCENTES = [
        ('TITULAR', 'Profesor Titular'),
        ('ASOCIADO', 'Profesor Asociado'),
        ('ADJUNTO', 'Profesor Adjunto'),
        ('JTP', 'Jefe de Trabajos Prácticos'),
        ('AYUDANTE_1', 'Ayudante de Primera'),
        ('AYUDANTE_2', 'Ayudante de Segunda'),
        ('AD_HONOREM', 'Ad Honorem'),
    ]

    persona = models.OneToOneField(
        Persona,
        on_delete=models.CASCADE,
        related_name='docente'
    )
    numero_legajo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de legajo"
    )
    categoria_docente = models.CharField(
        max_length=15,
        choices=CATEGORIAS_DOCENTES,
        verbose_name="Categoría docente"
    )
    fecha_ingreso_docencia = models.DateField(
        verbose_name="Fecha de ingreso a la docencia"
    )
    dependencia = models.ForeignKey(
        Dependencia,
        on_delete=models.SET_NULL,
        null=True,
        related_name='docentes'
    )

    probatoria_laboral_docente = models.FileField(
        upload_to='contrato_bono_sueldo_factura/',
        blank=True,
        null=True,
        verbose_name="Contrato laboral, bono de sueldo o factura"
    )

    class Meta:
        verbose_name = "Docente"
        verbose_name_plural = "Docentes"
        indexes = [
            models.Index(fields=['numero_legajo']),
            models.Index(fields=['categoria_docente']),
        ]

    def __str__(self):
        return f"{self.persona.nombre_completo} - {self.get_categoria_docente_display()}"


class PersonaNoDocente(models.Model):
    TIPOS_CONTRATO = {
        ('PLANTA_PERMANENTE', 'Planta Permanente'),
        ('CONTRATADO', 'Contratado'),
        ('BECARIO', 'Becario'),
        ('PASANTE', 'Pasante'),
    }

    persona = models.OneToOneField(
        Persona,
        on_delete=models.CASCADE,
        related_name='no_docente'
    )
    numero_legajo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de legajo"
    )

    cargo = models.CharField(
        max_length=200,
        verbose_name="Cargo"
    )
    fecha_ingreso_laboral = models.DateField(
        verbose_name="Fecha de ingreso laboral"
    )

    fecha_finalizacion_laboral = models.DateField(
        verbose_name="Fecha de finalización laboral"
    )

    tipo_contrato = models.CharField(
        max_length=20,
        choices=TIPOS_CONTRATO,
        verbose_name="Tipo de contrato"
    )
    area_principal = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        verbose_name="Área principal",
        related_name='no_docentes'
    )

    probatoria_laboral = models.FileField(
        upload_to='contrato_bono_sueldo_factura/',
        blank=True,
        null=True,
        verbose_name="Contrato laboral, bono de sueldo o factura"
    )

    def clean(self):
        if self.fecha_finalizacion_laboral <= self.fecha_ingreso_laboral:
            raise ValidationError({
                'fecha_finalizacion_laboral': 'La fecha de finalización debe ser posterior a la de ingreso.'
            })

    class Meta:
        verbose_name = "No Docente"
        verbose_name_plural = "No Docentes"
        indexes = [
            models.Index(fields=['numero_legajo']),
            models.Index(fields=['area_principal']),
            models.Index(fields=['tipo_contrato']),
        ]

    def __str__(self):
        return f"{self.persona.nombre_completo} - {self.cargo}"


