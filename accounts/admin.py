from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from accounts.models import UserProfile
from .models import CustomUser
from unfold.admin import StackedInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

# Inline para UserProfile
class UserProfileInline(StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = "Perfil de usuario"
    verbose_name_plural = "Perfil de usuario"
    ordering_field = 'order'
    hide_ordering_field = True

# Admin para CustomUser
class AccountsUserAdmin(AuthUserAdmin, UnfoldModelAdmin):
    model = CustomUser
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    #inlines = [UserProfileInline]
    #fieldsets = (
     #   (None, {'fields': ('username', 'password',)}),
    #)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    #unfold = [
     #   'userprofileinline',
    #]
    filter_horizontal = ()  # Para un widget más cómodo
    # Sobrescribe save_model para poner is_staff=True al crear
    def save_model(self, request, obj, form, change):
        if not change:  # Solo al crear, no al editar
            obj.is_staff = True
        super().save_model(request, obj, form, change)


# Admin para Group base
class GroupAdmin(BaseGroupAdmin, UnfoldModelAdmin):
    pass

# Registrar el admin
admin.site.unregister(Group)
#admin.site.unregister(User)  # Asegúrate de desregistrar antes de registrar el custom

admin.site.register(CustomUser, AccountsUserAdmin)
#admin.site.register(User, CustomBaseUserAdmin)
admin.site.register(Group, GroupAdmin)