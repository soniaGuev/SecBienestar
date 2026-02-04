from django import forms
from .models import Persona, PersonaEstudiante, PersonaDocente, PersonaNoDocente, Observacion, PersonaIngresante, \
    PersonaEgresado


class PersonaForm(forms.ModelForm):
    """Formulario para editar datos básicos de Persona"""

    class Meta:
        model = Persona
        fields = [
            'nombre', 'apellido', 'nombre_percibido', 'tipo_documento', 'documento',
            'genero', 'nacionalidad', 'sede', 'telefono', 'correo', 'correo_personal',
            'contacto_emergencia_nombre', 'contacto_emergencia_telefono',
            'ddjj_identidad', 'nombre_percibido_validado', 'rol'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre legal'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'nombre_percibido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre percibido (opcional)'
            }),
            'tipo_documento': forms.Select(attrs={
                'class': 'form-select'
            }),
            'documento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de documento'
            }),
            'genero': forms.Select(attrs={
                'class': 'form-select'
            }),
            'nacionalidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nacionalidad'
            }),
            'sede': forms.Select(attrs={
                'class': 'form-select'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+54 9 ...'
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@institucional.edu.ar'
            }),
            'correo_personal': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@personal.com'
            }),
            'contacto_emergencia_nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del contacto'
            }),
            'contacto_emergencia_telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de contacto'
            }),
            'ddjj_identidad': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
            }),
            'nombre_percibido_validado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'rol': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'nombre': 'Nombre Legal',
            'apellido': 'Apellido',
            'nombre_percibido': 'Nombre Percibido',
            'tipo_documento': 'Tipo de Documento',
            'documento': 'Número de Documento',
            'genero': 'Identidad de Género',
            'nacionalidad': 'Nacionalidad',
            'sede': 'Sede',
            'telefono': 'Teléfono',
            'correo': 'Correo Institucional',
            'correo_personal': 'Correo Personal',
            'contacto_emergencia_nombre': 'Contacto de Emergencia - Nombre',
            'contacto_emergencia_telefono': 'Contacto de Emergencia - Teléfono',
            'ddjj_identidad': 'DDJJ de Identidad Percibida',
            'nombre_percibido_validado': '¿Nombre percibido validado?',
            'rol': 'Rol en el Sistema',
        }


class PersonaIngresanteForm(forms.ModelForm):
    class Meta:
        model = PersonaIngresante
        fields = ['certificado_ingreso', 'fecha_vencimiento']
        widgets = {
            'certificado_ingreso': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class PersonaEstudianteForm(forms.ModelForm):
    """Formulario para editar datos específicos de Estudiante"""

    class Meta:
        model = PersonaEstudiante
        fields = [
            'dependencia', 'carrera', 'anio_ingreso', 'numero_legajo',
            'estado_academico',
            'certificado_regular', 'fecha_vencimiento_certificado',
            'carta_aceptacion', 'fecha_vencimiento_carta', 'preferencia_menu', 'ddjj_celiaco',
            'fecha_vencimiento_ddjj_celiaco', 'celiaco_validado',
            'validado_como_regular', 'observaciones_validacion'
        ]
        widgets = {
            'dependencia': forms.Select(attrs={'class': 'form-select'}),
            'carrera': forms.Select(attrs={'class': 'form-select'}),
            'anio_ingreso': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1900',
                'max': '2100'
            }),
            'numero_legajo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de legajo'
            }),
            'estado_academico': forms.Select(attrs={'class': 'form-select'}),
            'certificado_regular': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'fecha_vencimiento_certificado': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'carta_aceptacion': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'fecha_vencimiento_carta': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'preferencia_menu': forms.Select(attrs={'class': 'form-select'}),
            'ddjj_celiaco': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'fecha_vencimiento_ddjj_celiaco': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'celiaco_validado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),

            'validado_como_regular': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'observaciones_validacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }


class PersonaEgresadoForm(forms.ModelForm):
    class Meta:
        model = PersonaEgresado
        fields = ['certificado_egreso']
        widgets = {
            'certificado_egreso': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }


class PersonaDocenteForm(forms.ModelForm):
    """Formulario para editar datos específicos de Docente"""

    class Meta:
        model = PersonaDocente
        fields = [
            'numero_legajo', 'categoria_docente',
            'fecha_ingreso_docencia', 'dependencia', 'probatoria_laboral_docente'
        ]
        widgets = {
            'numero_legajo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de legajo'
            }),
            'categoria_docente': forms.Select(attrs={'class': 'form-select'}),
            'fecha_ingreso_docencia': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'dependencia': forms.Select(attrs={'class': 'form-select'}),
            'probatoria_laboral_docente': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }


class PersonaNoDocenteForm(forms.ModelForm):
    """Formulario para editar datos específicos de No Docente"""

    class Meta:
        model = PersonaNoDocente
        fields = [
            'numero_legajo', 'cargo', 'fecha_ingreso_laboral',
            'fecha_finalizacion_laboral', 'tipo_contrato',
            'area_principal', 'probatoria_laboral'
        ]
        widgets = {
            'numero_legajo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de legajo'
            }),
            'cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cargo que desempeña'
            }),
            'fecha_ingreso_laboral': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_finalizacion_laboral': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'tipo_contrato': forms.Select(attrs={'class': 'form-select'}),
            'area_principal': forms.Select(attrs={'class': 'form-select'}),
            'probatoria_laboral': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }


class ObservacionForm(forms.ModelForm):
    """Formulario para agregar observaciones manuales"""

    class Meta:
        model = Observacion
        fields = ['observacion']
        widgets = {
            'observacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escriba aquí su observación...'
            }),
        }
        labels = {
            'observacion': 'Observación',
        }
