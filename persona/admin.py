from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin, TabularInline
from .models import (
    Dependencia, Carrera, Area, Persona, Beca,
    PersonaEstudiante, PersonaBeca, Observacion,
    PersonaDocente, PersonaNoDocente
)


# ============= INLINES =============

class PersonaEstudianteInline(TabularInline):
    model = PersonaEstudiante
    extra = 0
    fields = (
        'carrera',
        'numero_legajo',
        'anio_ingreso',
        'estado_academico',
        'preferencia_menu',
        'fecha_ultima_modificacion_menu'
    )
    readonly_fields = ('fecha_ultima_modificacion_menu',)
    verbose_name = "Información de Estudiante"
    verbose_name_plural = "Información de Estudiante"


class PersonaDocenteInline(TabularInline):
    model = PersonaDocente
    extra = 0
    fields = ('numero_legajo', 'categoria_docente', 'fecha_ingreso_docencia', 'dependencia')
    verbose_name = "Información de Docente"
    verbose_name_plural = "Información de Docente"


class PersonaNoDocenteInline(TabularInline):
    model = PersonaNoDocente
    extra = 0
    fields = ('numero_legajo', 'cargo', 'tipo_contrato', 'area_principal')
    verbose_name = "Información de No Docente"
    verbose_name_plural = "Información de No Docente"


class PersonaBecaInline(TabularInline):
    model = PersonaBeca
    extra = 0
    fields = (
        'beca',
        'fecha_inicio',
        'fecha_fin',
        'estado_beca',
        'monto_asignado',
    )
    verbose_name = "Beca Asignada"
    verbose_name_plural = "Becas Asignadas"


class ObservacionInline(TabularInline):
    model = Observacion
    extra = 0
    fields = ('observacion', 'fecha', 'usuario')
    readonly_fields = ('fecha', 'usuario')
    verbose_name = "Observación"
    verbose_name_plural = "Observaciones"


# ============= ADMIN MODELS =============

@admin.register(Dependencia)
class DependenciaAdmin(UnfoldModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(Carrera)
class CarreraAdmin(UnfoldModelAdmin):
    list_display = ('codigo', 'nombre', 'dependencia', 'activa')
    list_filter = ('dependencia', 'activa')
    search_fields = ('codigo', 'nombre')
    list_editable = ('activa',)


@admin.register(Area)
class AreaAdmin(UnfoldModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(Persona)
class PersonaAdmin(UnfoldModelAdmin):
    list_display = ('apellido', 'nombre', 'documento', 'rol', 'correo', 'sede', 'usuario')
    list_filter = ('rol', 'tipo_documento', 'sede', 'genero')
    search_fields = ('nombre', 'apellido', 'documento', 'correo', 'nombre_percibido')
    inlines = [ObservacionInline]

    fieldsets = (
        ('Información Personal', {
            'fields': (
                'nombre',
                'apellido',
                'nombre_percibido',
                'nombre_percibido_validado',
                'tipo_documento',
                'documento',
                'genero',
                'nacionalidad'
            )
        }),
        ('Contacto', {
            'fields': (
                'correo',
                'correo_personal',
                'telefono',
                'contacto_emergencia_nombre',
                'contacto_emergencia_telefono'
            )
        }),
        ('Institución', {
            'fields': ('rol', 'sede', 'usuario'),
            'description': 'Asociar persona con usuario del sistema y configurar sede'
        }),
        ('Documentación', {
            'fields': ('ddjj_identidad',),
            'description': 'DDJJ de identidad percibida - formatos permitidos: PDF, DOC, DOCX, JPG, PNG'
        }),
    )

    readonly_fields = []

    def get_inlines(self, request, obj=None):
        """Mostrar inlines según el rol de la persona"""
        if obj:
            if obj.rol == 'estudiante':
                return [PersonaEstudianteInline, ObservacionInline]
            elif obj.rol == 'docente':
                return [PersonaDocenteInline, ObservacionInline]
            elif obj.rol == 'no_docente':
                return [PersonaNoDocenteInline, ObservacionInline]
        return [ObservacionInline]

    def save_model(self, request, obj, form, change):
        """Guardar el modelo con lógica adicional si es necesario"""
        super().save_model(request, obj, form, change)

        # Si hay un archivo DDJJ y el nombre percibido aún no está validado
        if obj.ddjj_identidad and obj.nombre_percibido and not obj.nombre_percibido_validado:
            Observacion.objects.create(
                persona=obj,
                observacion=f"Se ha cargado DDJJ de identidad percibida. Pendiente de validación del nombre percibido: {obj.nombre_percibido}",
                usuario=request.user
            )

    def delete_model(self, request, obj):
        """Eliminar modelo y sus archivos asociados"""
        if obj.ddjj_identidad:
            obj.ddjj_identidad.delete(save=False)
        super().delete_model(request, obj)


@admin.register(Beca)
class BecaAdmin(UnfoldModelAdmin):
    list_display = ('tipo', 'activa')
    list_filter = ('tipo', 'activa')
    search_fields = ('tipo',)
    list_editable = ('activa',)


@admin.register(PersonaEstudiante)
class PersonaEstudianteAdmin(UnfoldModelAdmin):
    list_display = (
        'numero_legajo',
        'get_nombre_completo',
        'carrera',
        'estado_academico',
        'anio_ingreso',
        'preferencia_menu',
        'get_es_celiaco',
        'get_ddjj_celiaco_estado'
    )
    list_filter = (
        'carrera',
        'estado_academico',
        'dependencia',
        'preferencia_menu',
        'celiaco_validado'
    )
    search_fields = (
        'numero_legajo',
        'persona__nombre',
        'persona__apellido',
        'persona__documento'
    )
    inlines = [PersonaBecaInline]

    fieldsets = (
        ('Información del Estudiante', {
            'fields': ('persona', 'numero_legajo', 'anio_ingreso')
        }),
        ('Información Académica', {
            'fields': ('dependencia', 'carrera', 'estado_academico')
        }),
        ('Preferencias de Comedor', {
            'fields': (
                'preferencia_menu',
                'fecha_ultima_modificacion_menu'
            ),
            'description': 'Configuración de menú para el comedor universitario'
        }),
        ('Documentación de Condición Celíaca', {
            'fields': (
                'ddjj_celiaco',
                'fecha_vencimiento_ddjj_celiaco',
                'celiaco_validado',
                'fecha_validacion_celiaco',
                'validado_celiaco_por'
            ),
            'description': '⚠️ Obligatorio para estudiantes con menú celíaco. Cargar DDJJ o certificado médico.',
            'classes': ('collapse',),
        }),
        ('Documentación de Estudiante Regular', {
            'fields': (
                'certificado_regular',
                'fecha_vencimiento_certificado',
                'carta_aceptacion',
                'fecha_vencimiento_carta'
            ),
            'classes': ('collapse',),
        }),
        ('Validación de Regularidad', {
            'fields': (
                'validado_como_regular',
                'fecha_validacion_regular',
                'validado_por',
                'observaciones_validacion'
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = (
        'fecha_ultima_modificacion_menu',
        'fecha_validacion_regular',
        'fecha_validacion_celiaco'
    )

    def get_nombre_completo(self, obj):
        return obj.persona.nombre_completo

    get_nombre_completo.short_description = 'Nombre Completo'

    def get_es_celiaco(self, obj):
        """Indica visualmente si el estudiante requiere menú celíaco"""
        if 'celiaco' in obj.preferencia_menu.lower():
            return '🌾 Sí'
        return 'No'

    get_es_celiaco.short_description = 'Celíaco'

    def get_ddjj_celiaco_estado(self, obj):
        """Muestra el estado de la documentación celíaca"""
        if 'celiaco' not in obj.preferencia_menu.lower():
            return '-'

        if not obj.ddjj_celiaco:
            return '❌ Sin DDJJ'

        if obj.celiaco_validado:
            # Verificar si está vigente
            if obj.ddjj_celiaco_vigente is False:
                return '⚠️ Vencida'
            return '✅ Validada'

        return '⏳ Pendiente validación'

    get_ddjj_celiaco_estado.short_description = 'Estado DDJJ Celíaco'

    def save_model(self, request, obj, form, change):
        """Registrar cambios en preferencia de menú y validaciones"""
        from datetime import date, datetime

        # Si es una modificación y cambió la preferencia de menú
        if change and 'preferencia_menu' in form.changed_data:
            # Actualizar fecha de modificación
            obj.fecha_ultima_modificacion_menu = date.today()

            # Crear observación automática
            Observacion.objects.create(
                persona=obj.persona,
                observacion=f"Cambio de preferencia de menú a: {obj.get_preferencia_menu_display()}",
                usuario=request.user
            )

        # Si se valida la condición celíaca
        if change and 'celiaco_validado' in form.changed_data and obj.celiaco_validado:
            obj.fecha_validacion_celiaco = datetime.now()
            obj.validado_celiaco_por = request.user

            # Crear observación
            Observacion.objects.create(
                persona=obj.persona,
                observacion=f"Condición celíaca validada. Documentación aprobada.",
                usuario=request.user
            )

        # Si se carga DDJJ celíaco por primera vez
        if change and 'ddjj_celiaco' in form.changed_data and obj.ddjj_celiaco:
            Observacion.objects.create(
                persona=obj.persona,
                observacion=f"Se ha cargado DDJJ/certificado de condición celíaca. Pendiente de validación.",
                usuario=request.user
            )

        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """Eliminar archivos asociados al eliminar estudiante"""
        # Eliminar archivos si existen
        if obj.ddjj_celiaco:
            obj.ddjj_celiaco.delete(save=False)
        if obj.certificado_regular:
            obj.certificado_regular.delete(save=False)
        if obj.carta_aceptacion:
            obj.carta_aceptacion.delete(save=False)

        super().delete_model(request, obj)


@admin.register(PersonaBeca)
class PersonaBecaAdmin(UnfoldModelAdmin):
    list_display = (
        'get_estudiante',
        'beca',
        'fecha_inicio',
        'fecha_fin',
        'estado_beca',
        'monto_asignado',
    )

    list_filter = (
        'estado_beca',
        'beca__tipo',
        'fecha_inicio',
    )

    search_fields = (
        'persona_estudiante__persona__nombre',
        'persona_estudiante__persona__apellido',
        'persona_estudiante__numero_legajo'
    )

    date_hierarchy = 'fecha_inicio'

    fieldsets = (
        ('Asignación de Beca', {
            'fields': ('persona_estudiante', 'beca')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin', 'fecha_aprobacion')
        }),
        ('Estado', {
            'fields': ('estado_beca', 'preferencia_menu')
        }),
        ('Monto', {
            'fields': ('monto_asignado',),
        }),
    )

    readonly_fields = ('fecha_aprobacion',)

    def get_estudiante(self, obj):
        return obj.persona_estudiante.persona.nombre_completo

    get_estudiante.short_description = 'Estudiante'



@admin.register(Observacion)
class ObservacionAdmin(UnfoldModelAdmin):
    list_display = ('persona', 'get_observacion_preview', 'fecha', 'usuario')
    list_filter = ('fecha',)
    search_fields = ('persona__nombre', 'persona__apellido', 'observacion')
    readonly_fields = ('fecha',)
    date_hierarchy = 'fecha'

    fieldsets = (
        ('Información', {
            'fields': ('persona', 'persona_beca')
        }),
        ('Observación', {
            'fields': ('observacion',)
        }),
        ('Registro', {
            'fields': ('usuario', 'fecha'),
            'classes': ('collapse',)
        }),
    )

    def get_observacion_preview(self, obj):
        return obj.observacion[:50] + '...' if len(obj.observacion) > 50 else obj.observacion

    get_observacion_preview.short_description = 'Observación'

    def save_model(self, request, obj, form, change):
        if not change:  # Solo al crear
            obj.usuario = request.user
        super().save_model(request, obj, form, change)


@admin.register(PersonaDocente)
class PersonaDocenteAdmin(UnfoldModelAdmin):
    list_display = ('numero_legajo', 'get_nombre_completo', 'categoria_docente', 'dependencia')
    list_filter = ('categoria_docente', 'dependencia')
    search_fields = ('numero_legajo', 'persona__nombre', 'persona__apellido', 'persona__documento')

    fieldsets = (
        ('Información del Docente', {
            'fields': ('persona', 'numero_legajo', 'fecha_ingreso_docencia')
        }),
        ('Información Académica', {
            'fields': ('categoria_docente', 'dependencia')
        }),
    )

    def get_nombre_completo(self, obj):
        return obj.persona.nombre_completo

    get_nombre_completo.short_description = 'Nombre Completo'


@admin.register(PersonaNoDocente)
class PersonaNoDocenteAdmin(UnfoldModelAdmin):
    list_display = ('numero_legajo', 'get_nombre_completo', 'cargo', 'tipo_contrato', 'area_principal')
    list_filter = ('tipo_contrato', 'area_principal')
    search_fields = ('numero_legajo', 'persona__nombre', 'persona__apellido', 'cargo')

    fieldsets = (
        ('Información del No Docente', {
            'fields': ('persona', 'numero_legajo', 'fecha_ingreso_laboral')
        }),
        ('Información Laboral', {
            'fields': ('cargo', 'tipo_contrato', 'area_principal')
        }),
    )

    def get_nombre_completo(self, obj):
        return obj.persona.nombre_completo

    get_nombre_completo.short_description = 'Nombre Completo'