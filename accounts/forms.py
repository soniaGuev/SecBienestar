from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, UserProfile
from persona.models import (
    Persona, PersonaEstudiante, PersonaDocente,
    PersonaNoDocente, Dependencia, Carrera, Area, PersonaIngresante, PersonaEgresado
)
from allauth.account.forms import SignupForm


# ========== FORMULARIO PARA ALLAUTH ==========
class CustomSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=30,
        label='Nombre',
        widget=forms.TextInput(attrs={
            'placeholder': 'Nombre',
            'class': 'form-control'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        label='Apellido',
        widget=forms.TextInput(attrs={
            'placeholder': 'Apellido',
            'class': 'form-control'
        })
    )

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        return user


# ========== FORMULARIOS EXISTENTES ==========
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name',)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('nombre', 'apellido', 'bio', 'avatar')


# ========== FORMULARIOS PARA ROLES ==========
class RolSelectionForm(forms.Form):
    """Formulario para seleccionar el rol por primera vez"""
    ROLES_CHOICES = [
        ('ingresante', 'Ingresante'),
        ('estudiante', 'Estudiante'),
        ('egresado', 'Egresado'),
        ('docente', 'Docente'),
        ('no_docente', 'Personal No Docente'),
    ]

    rol = forms.ChoiceField(
        choices=ROLES_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="¿Cuál es tu rol en la universidad?"
    )


class PersonaBaseForm(forms.ModelForm):
    """Formulario base con campos comunes para todos los roles"""
    # Campo adicional para email (solo lectura)
    email = forms.EmailField(
        label='Correo Electrónico',
        disabled=True,
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control bg-light',
            'readonly': 'readonly'
        })
    )

    email_personal = forms.EmailField(
        label='Correo Electrónico Personal',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: correo@correo.com'
        })
    )

    class Meta:
        model = Persona
        fields = [
            'nombre', 'apellido', 'tipo_documento', 'documento',
            'genero', 'nacionalidad', 'sede', 'telefono',
            'contacto_emergencia_nombre', 'contacto_emergencia_telefono',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre legal'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido legal'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 12345678'}),
            'genero': forms.Select(attrs={'class': 'form-select'}),
            'nacionalidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Argentina'}),
            'sede': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: +54 261 1234567'}),
            'contacto_emergencia_nombre': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'contacto_emergencia_telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'email_personal': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ej: correo@correo.com'}),
        }

    def __init__(self, *args, **kwargs):
        # Extraer el email del usuario si se pasa como argumento
        user_email = kwargs.pop('user_email', None)
        super().__init__(*args, **kwargs)

        # Pre-llenar el email
        if user_email:
            self.fields['email'].initial = user_email

        if self.instance and self.instance.pk:
            if self.instance.documento.startswith('TEMP_'):
                self.fields['documento'].initial = ''
                self.initial['documento'] = ''


class PersonaIdentidadPercibidaForm(forms.ModelForm):
    """Formulario separado para identidad percibida"""

    class Meta:
        model = Persona
        fields = ['nombre_percibido', 'ddjj_identidad']
        widgets = {
            'nombre_percibido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre con el que te identificas'
            }),
            'ddjj_identidad': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }
        labels = {
            'nombre_percibido': 'Nombre Percibido',
            'ddjj_identidad': 'Declaración Jurada de Identidad Percibida',
        }
        help_texts = {
            'nombre_percibido': 'Nombre con el que te sientes identificado/a',
            'ddjj_identidad': 'Declaración jurada firmada (PDF, JPG o PNG - máx. 5MB)',
        }

class IngresantePerfilForm(forms.ModelForm):
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

class EstudiantePerfilForm(forms.ModelForm):
    """Formulario específico para completar perfil de Estudiante"""

    # Campo para DDJJ de celiaquía (condicional)
    ddjj_celiaco = forms.FileField(
        required=False,
        label='Declaración Jurada de Celiaquía',
        help_text='Requerido solo si seleccionaste menú celíaco',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png',
            'id': 'id_ddjj_celiaco'
        })
    )

    class Meta:
        model = PersonaEstudiante
        fields = [
            'dependencia', 'carrera', 'anio_ingreso',
            'numero_legajo', 'estado_academico', 'preferencia_menu',
            'certificado_regular',
            'fecha_vencimiento_certificado',
            'carta_aceptacion',
            'fecha_vencimiento_carta',
        ]
        widgets = {
            'dependencia': forms.Select(attrs={'class': 'form-select'}),
            'carrera': forms.Select(attrs={'class': 'form-select'}),
            'anio_ingreso': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: 2024', 'min': '1950', 'max': '2030'}),
            'numero_legajo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de legajo'}),
            'estado_academico': forms.Select(attrs={'class': 'form-select'}),
            'preferencia_menu': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_preferencia_menu',
                'onchange': 'toggleDdjjCeliaco()'
            }),
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
        }
        help_texts = {
            'preferencia_menu': 'Selecciona tu preferencia alimentaria. Si eres celíaco deberás adjuntar declaración jurada.',
            'certificado_regular': 'Certificado de alumno regular vigente (PDF, JPG o PNG)',
            'carta_aceptacion': 'Solo para estudiantes extranjeros: Carta de aceptación de la universidad',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Hacer campos opcionales por defecto
        self.fields['certificado_regular'].required = False
        self.fields['fecha_vencimiento_certificado'].required = False
        self.fields['carta_aceptacion'].required = False
        self.fields['fecha_vencimiento_carta'].required = False

        # Filtrar carreras según dependencia
        if 'dependencia' in self.data:
            try:
                dependencia_id = int(self.data.get('dependencia'))
                self.fields['carrera'].queryset = Carrera.objects.filter(
                    dependencia_id=dependencia_id, activa=True
                ).order_by('nombre')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['carrera'].queryset = self.fields['carrera'].queryset.filter(
                dependencia=self.instance.dependencia
            )

        if not self.instance.pk:
            self.fields['carrera'].queryset = Carrera.objects.filter(activa=True).order_by('nombre')

    def clean(self):
        print(f"DEBUG: self.instance.pk = {self.instance.pk if self.instance else 'No instance'}")
        if self.instance and self.instance.pk:
            print(f"DEBUG: tiene persona? {hasattr(self.instance, 'persona')}")

        cleaned_data = super().clean()
        preferencia_menu = cleaned_data.get('preferencia_menu')
        ddjj_celiaco = cleaned_data.get('ddjj_celiaco')

        # Validar que si es celíaco, debe tener DDJJ
        if preferencia_menu and 'celiaco' in preferencia_menu.lower():
            if not ddjj_celiaco:
                # Solo validar si NO existe una instancia previa con archivo
                if not (self.instance and self.instance.pk):
                    self.add_error('ddjj_celiaco', 'Debes adjuntar la declaración jurada si seleccionas menú celíaco.')

        return cleaned_data

class EgresadoPerfilForm(forms.ModelForm):
    class Meta:
        model = PersonaEgresado
        fields = ['certificado_egreso']
        widgets = {
            'certificado_egreso': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }


class DocentePerfilForm(forms.ModelForm):
    """Formulario específico para completar perfil de Docente"""

    class Meta:
        model = PersonaDocente
        fields = [
            'numero_legajo', 'categoria_docente',
            'fecha_ingreso_docencia', 'dependencia',
            'probatoria_laboral_docente',
        ]
        widgets = {
            'numero_legajo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de legajo'}),
            'categoria_docente': forms.Select(attrs={'class': 'form-select'}),
            'fecha_ingreso_docencia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'dependencia': forms.Select(attrs={'class': 'form-select'}),
            'probatoria_laboral_docente': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }


class NoDocentePerfilForm(forms.ModelForm):
    """Formulario específico para completar perfil de No Docente"""

    class Meta:
        model = PersonaNoDocente
        fields = [
            'numero_legajo', 'cargo', 'fecha_ingreso_laboral',
            'fecha_finalizacion_laboral', 'tipo_contrato', 'area_principal',
            'probatoria_laboral',
        ]
        widgets = {
            'numero_legajo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de legajo'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cargo que desempeña'}),
            'fecha_ingreso_laboral': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_finalizacion_laboral': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo_contrato': forms.Select(attrs={'class': 'form-select'}),
            'area_principal': forms.Select(attrs={'class': 'form-select'}),
            'probatoria_laboral': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }
        help_texts = {
            'probatoria_laboral': 'Contrato laboral, bono de sueldo o factura (PDF, JPG o PNG)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['probatoria_laboral'].required = False


class PersonaEditableForm(forms.ModelForm):
    """Formulario con solo los campos que el usuario puede editar"""

    class Meta:
        model = Persona
        fields = [
            'nombre_percibido',
            'ddjj_identidad',
            'telefono',
            'correo_personal',
            'contacto_emergencia_nombre',
            'contacto_emergencia_telefono',
        ]
        widgets = {
            'nombre_percibido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre con el que te identificas'
            }),
            'ddjj_identidad': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+54 261 1234567'
            }),
            'correo_personal': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'contacto_emergencia_nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo'
            }),
            'contacto_emergencia_telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de emergencia'
            }),
        }
        labels = {
            'nombre_percibido': 'Nombre Percibido',
            'ddjj_identidad': 'Declaración Jurada de Identidad',
            'telefono': 'Teléfono',
            'correo_personal': 'Correo Personal',
            'contacto_emergencia_nombre': 'Contacto de Emergencia',
            'contacto_emergencia_telefono': 'Teléfono de Emergencia',
        }


class EstudiantePreferenciaMenuForm(forms.ModelForm):
    """Formulario para cambiar preferencia de menú (una vez al año)"""

    class Meta:
        model = PersonaEstudiante
        fields = ['preferencia_menu']
        widgets = {
            'preferencia_menu': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'preferencia_menu': 'Preferencia de Menú',
        }
        help_texts = {
            'preferencia_menu': 'Solo puedes cambiar esta preferencia una vez al año.',
        }
