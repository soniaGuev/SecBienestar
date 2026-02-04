from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PersonaBeca, Beca
from django.utils import timezone


@receiver(post_save, sender=PersonaBeca)
def crear_beca_comedor_automatica(sender, instance, created, **kwargs):
    """
    Si se asigna beca Residencia, crear automáticamente beca Comedor
    con la misma preferencia de menú del estudiante
    """
    if created and instance.beca.tipo == 'Residencia':
        try:
            # Buscar la beca Comedor en el catálogo
            beca_comedor = Beca.objects.get(tipo='Comedor', activa=True)

            # Verificar que no exista ya una beca Comedor activa para este estudiante
            existe_comedor = PersonaBeca.objects.filter(
                persona_estudiante=instance.persona_estudiante,
                beca__tipo='Comedor',
                estado_beca__in=['ACTIVA', 'APROBADA', 'PENDIENTE']
            ).exists()

            if not existe_comedor:
                # Obtener preferencia del estudiante
                preferencia = instance.persona_estudiante.preferencia_menu

                # Crear la beca Comedor automáticamente con la preferencia
                PersonaBeca.objects.create(
                    persona_estudiante=instance.persona_estudiante,
                    beca=beca_comedor,
                    fecha_inicio=instance.fecha_inicio,
                    fecha_fin=instance.fecha_fin,
                    estado_beca=instance.estado_beca,
                    fecha_aprobacion=instance.fecha_aprobacion if instance.estado_beca in ['APROBADA',
                                                                                           'ACTIVA'] else None,
                    preferencia_menu=preferencia  # *** NUEVO: copiar preferencia ***
                )
        except Beca.DoesNotExist:
            # Si no existe la beca Comedor en el catálogo, no hacer nada
            pass