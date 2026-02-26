from django.contrib import admin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, Area, Sede


# =========================
# USER ADMIN PERSONALIZADO
# =========================
class UserAdmin(BaseUserAdmin):
    ordering = ['id']
    list_display = ['username', 'email', 'nombre', 'rol', 'area', 'sede', 'is_staff']

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Información Personal', {'fields': ('nombre', 'documento', 'rol', 'area', 'sede')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'rol', 'area', 'sede'),
        }),
    )

    search_fields = ('username', 'email', 'nombre')


# =========================
# REGISTROS
# =========================
admin.site.register(User, UserAdmin)
admin.site.register(Role)
admin.site.register(Area)
admin.site.register(Sede)