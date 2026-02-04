from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from accounts.models import UserProfile
from .models import CustomUser
from unfold.admin import StackedInline  # usa unfold admin inline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.admin import ModelAdmin


class UserProfileInline(StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = "Perfil de usuario"
    verbose_name_plural = "Perfil de usuario"
    ordering_field = 'order'  # campo usado para ordenar inlines
    hide_ordering_field = True  # opcional: oculta el campo en UI


# Heredamos de ambos: AuthUserAdmin para mantener funcionalidad usuario,
# y UnfoldModelAdmin para usar unfold admin features
class AccountsUserAdmin(AuthUserAdmin, UnfoldModelAdmin):
    model = CustomUser
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    inlines = [UserProfileInline]
    fieldsets = (
        (None, {'fields': ('username', 'password',)}),

    )
    # Opcional: configura unfold para que el inline esté dentro de un panel desplegable
    # Puedes usar el atributo `unfold` para definir qué campos o inlines se pliegan
    unfold = [
        'userprofileinline',  # nombre en minúsculas del inline
    ]


# Registrar el admin
# admin.site.unregister(CustomUser)  # Descomenta si ya está registrado
admin.site.register(CustomUser, AccountsUserAdmin)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

# admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms`
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass