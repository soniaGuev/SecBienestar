from django.contrib.auth.models import AbstractUser
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.urls import reverse
from django.contrib.auth.models import Group

from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill


class CustomUser(AbstractUser):
    # proyectos = models.ManyToManyField(Proyectos, blank=True, related_name="usuarios")
    # pass
    # cuit,tipo de persona, razon social , nombre de fantasia
    # cuit = models.CharField(max_length=15, blank=True)
    # tipo_persona = models.CharField(blank=True)
    # razon_social = models.CharField(blank=True)
    # nombre_fantasia= models.CharField(blank=True)
    # nombres= models.CharField(blank=True)
    # apellidos= models.CharField(blank=True)
    # phone_number = models.CharField(max_length=15, blank=True)
    # address = models.TextField(blank=True)

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0, db_index=True)
    nombre = models.CharField(max_length=25, default='', blank=True)
    apellido = models.CharField(max_length=25, default='', blank=True)
    # proyectos = models.ManyToManyField(Proyectos, blank=True, related_name='usuarios')
    bio = models.CharField(max_length=250, default='', blank=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/user_avatar.png')
    avatar_thumbnail = ImageSpecField(source='avatar',
                                      processors=[ResizeToFill(150, 150)],
                                      format='JPEG',
                                      options={'quality': 60})

    def __str__(self):
        return self.user.username

    def get_user_initials(self):
        return self.nombre[0]

    def get_public_profile_url(self):
        return reverse('accounts:public-profile', kwargs={'username': self.user.username})


# auto create user profile after user signup
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    # agrega el grupo de usuario prestadores
    # try:
    #     group = Group.objects.get(name='prestadores')
    # except Group.DoesNotExist:
    #    group = Group.objects.create(name='prestadores')

    # instance.groups.add(group)

@receiver(post_save, sender=CustomUser)
def create_persona_for_user(sender, instance, created, **kwargs):
    """
    Crea automáticamente un objeto Persona cuando se crea un CustomUser
    """
    if created:
        from persona.models import Persona
        # Solo crear si no existe ya una Persona asociada
        if not hasattr(instance, 'persona'):
            Persona.objects.create(
                usuario=instance,
                correo=instance.email,
                nombre=instance.first_name or '',
                apellido=instance.last_name or '',
                # Documento temporal hasta que complete el perfil
                documento=f'TEMP_{instance.id}',
                # Rol vacío, lo seleccionará después
                rol=''
            )