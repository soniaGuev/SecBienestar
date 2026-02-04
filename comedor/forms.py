from django import forms
from .models import Ticket, TipoMenu, ConfiguracionMenu, BeneficioComedor, CertificadoCeliaco
from .models import ImagenCarrusel
from persona.models import Beca


class CompraTicketForm(forms.Form):
    def __init__(self, *args, **kwargs):
        usuario = kwargs.pop('usuario', None)
        tiene_beneficio = kwargs.pop('tiene_beneficio', False)
        super().__init__(*args, **kwargs)


class ImagenCarruselForm(forms.ModelForm):
    class Meta:
        model = ImagenCarrusel
        fields = ['titulo', 'descripcion', 'imagen', 'dia_semana', 'activo', 'orden', 'fecha_desde', 'fecha_hasta']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Menú del Lunes'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de las comidas del día...'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'dia_semana': forms.Select(attrs={
                'class': 'form-select'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'fecha_desde': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_hasta': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')

        if fecha_desde and fecha_hasta:
            if fecha_desde > fecha_hasta:
                raise forms.ValidationError('La fecha de inicio no puede ser posterior a la fecha de fin')

        return cleaned_data


class TipoMenuForm(forms.ModelForm):
    class Meta:
        model = TipoMenu
        fields = ['tipo', 'nombre', 'descripcion', 'precio', 'activo']
        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Menú Completo del Día'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción del menú (entrada, plato principal, postre, bebida...)'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'tipo': 'Tipo de Menú',
            'nombre': 'Nombre del Menú',
            'descripcion': 'Descripción',
            'precio': 'Precio ($)',
            'activo': '¿Menú disponible para compra?',
        }
        help_texts = {
            'tipo': 'Categoría del menú',
            'precio': 'Precio en pesos argentinos',
            'activo': 'Si está desactivado, no se podrá comprar este menú',
        }

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio and precio <= 0:
            raise forms.ValidationError('El precio debe ser mayor a 0')
        return precio


class BeneficioComedorForm(forms.ModelForm):
    class Meta:
        model = BeneficioComedor
        fields = ['tipo_beca', 'tipo_beneficio', 'porcentaje_descuento', 'activo']
        widgets = {
            'tipo_beca': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo_beneficio': forms.Select(attrs={
                'class': 'form-select'
            }),
            'porcentaje_descuento': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '0.00'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'tipo_beca': 'Tipo de Beca',
            'tipo_beneficio': 'Tipo de Beneficio',
            'porcentaje_descuento': 'Porcentaje de Descuento (%)',
            'activo': '¿Beneficio activo?',
        }
        help_texts = {
            'tipo_beca': 'Selecciona el tipo de beca a otorgar',
            'tipo_beneficio': 'Selecciona el tipo de beneficio a otorgar',
            'porcentaje_descuento': 'Ingresa un valor entre 0 y 100. Para acceso gratuito usa 100%',
            'activo': 'Si está desactivado, no se aplicará este beneficio',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Obtener las opciones de tipo de beca desde el modelo Beca
        self.fields['tipo_beca'].queryset = Beca.objects.filter(activa=True)
        self.fields['tipo_beca'].label_from_instance = lambda obj: f"{obj.tipo}"

    def clean(self):
        cleaned_data = super().clean()
        tipo_beneficio = cleaned_data.get('tipo_beneficio')
        porcentaje_descuento = cleaned_data.get('porcentaje_descuento')

        # Validación: si es gratuito, el porcentaje debe ser 100
        if tipo_beneficio == 'gratuito' and porcentaje_descuento != 100:
            cleaned_data['porcentaje_descuento'] = 100
            self.add_error('porcentaje_descuento',
                           'Para acceso gratuito, el porcentaje debe ser 100%')

        # Validación: si es descuento, el porcentaje debe ser mayor a 0
        if tipo_beneficio == 'descuento' and porcentaje_descuento <= 0:
            self.add_error('porcentaje_descuento',
                           'Para descuento, el porcentaje debe ser mayor a 0%')

        # Validación: si es ninguno, el porcentaje debe ser 0
        if tipo_beneficio == 'ninguno' and porcentaje_descuento != 0:
            cleaned_data['porcentaje_descuento'] = 0

        return cleaned_data

    def clean_porcentaje_descuento(self):
        porcentaje = self.cleaned_data.get('porcentaje_descuento')
        if porcentaje < 0 or porcentaje > 100:
            raise forms.ValidationError('El porcentaje debe estar entre 0 y 100')
        return porcentaje


class CertificadoCeliacoForm(forms.ModelForm):
    class Meta:
        model = CertificadoCeliaco
        fields = ['archivo_certificado', 'fecha_emision', 'fecha_vencimiento', 'observaciones', 'activo']
        widgets = {
            'archivo_certificado': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'fecha_emision': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),  # ← AGREGAR ESTE FORMATO
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),  # ← AGREGAR ESTE FORMATO
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales sobre el certificado...'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'archivo_certificado': 'Certificado Médico (PDF, JPG, PNG)',
            'fecha_emision': 'Fecha de Emisión *',
            'fecha_vencimiento': 'Fecha de Vencimiento (opcional)',
            'observaciones': 'Observaciones',
            'activo': '¿Certificado vigente?',
        }
        help_texts = {
            'archivo_certificado': 'Adjuntar certificado médico que acredite la condición celíaca',
            'fecha_vencimiento': 'Dejar en blanco si el certificado no vence',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar el formato de entrada para los campos de fecha
        self.fields['fecha_emision'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_vencimiento'].input_formats = ['%Y-%m-%d']

    def clean(self):
        cleaned_data = super().clean()
        fecha_emision = cleaned_data.get('fecha_emision')
        fecha_vencimiento = cleaned_data.get('fecha_vencimiento')

        if fecha_emision and fecha_vencimiento:
            if fecha_emision > fecha_vencimiento:
                raise forms.ValidationError(
                    'La fecha de emisión no puede ser posterior a la fecha de vencimiento'
                )

        return cleaned_data


class BecaForm(forms.ModelForm):
    class Meta:
        model = Beca
        fields = ['tipo', 'tiene_monto', 'monto_sugerido', 'permite_comedor', 'activa']
        widgets = {
            'tipo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Comedor, Transporte, etc.'
            }),
            'tiene_monto': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_tiene_monto'
            }),
            'monto_sugerido': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'permite_comedor': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'tipo': 'Tipo de Beca',
            'tiene_monto': '¿Otorga monto monetario?',
            'monto_sugerido': 'Monto Sugerido ($)',
            'permite_comedor': '¿Permite beneficio de comedor?',
            'activa': '¿Beca activa?',
        }
        help_texts = {
            'tiene_monto': 'Marca si esta beca otorga un monto mensual/anual de dinero',
            'monto_sugerido': 'Monto sugerido por defecto (puede modificarse por beneficiario)',
            'permite_comedor': 'Marca si este tipo de beca puede tener beneficio de comedor',
            'activa': 'Si está desactivada, no se podrá asignar a estudiantes',
        }

    def clean(self):
        cleaned_data = super().clean()
        tiene_monto = cleaned_data.get('tiene_monto')
        monto_sugerido = cleaned_data.get('monto_sugerido')

        # Validación: si tiene_monto es True, debe tener un monto_sugerido
        if tiene_monto and not monto_sugerido:
            self.add_error('monto_sugerido',
                           'Debe especificar un monto sugerido si la beca otorga dinero')

        # Validación: si tiene_monto es False, no debería tener monto_sugerido
        if not tiene_monto and monto_sugerido:
            cleaned_data['monto_sugerido'] = None

        return cleaned_data


# Agregar al final de forms.py

class ValidacionEstudianteForm(forms.Form):
    """Formulario para que el admin valide la documentación del estudiante"""

    validado = forms.BooleanField(
        required=False,
        label="✓ Validar como alumno regular",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Marque si la documentación es correcta y está vigente"
    )

    observaciones = forms.CharField(
        required=False,
        label="Observaciones",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones sobre la validación (opcional)...'
        }),
        help_text="Agregue cualquier nota relevante sobre la validación"
    )
