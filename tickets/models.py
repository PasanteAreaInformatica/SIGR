from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from users.models import Role

# =========================
# TIPO DE FALLA
# =========================
class TipoFalla(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


# =========================
# ESTADO DEL TICKET
# =========================
class TicketEstado(models.Model):
    nombre = models.CharField(max_length=30, unique=True)  # código técnico
    descripcion = models.CharField(max_length=50, null=True)

    def __str__(self):
        return self.nombre


# =========================
# TICKET
# =========================
class Ticket(models.Model):
    
    class Prioridad(models.TextChoices):
        LOW = "LOW", "Bajo"
        MEDIUM = "MEDIUM", "Medio"
        HIGH = "HIGH", "Alto"
        CRITICAL = "CRITICAL", "Critico"

    usuario_crea = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets_creados'
    )

    tipo_falla = models.ForeignKey(
        TipoFalla,
        on_delete=models.PROTECT
    )

    estado = models.ForeignKey(
        TicketEstado,
        on_delete=models.PROTECT
    )

    prioridad = models.CharField(
        max_length=20,
        choices=Prioridad.choices
    )

    descripcion = models.TextField()

    observaciones = models.TextField(null=True, blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cambio_estado = models.DateTimeField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.estado}"

    def save(self, *args, **kwargs):

        self.full_clean()

        if not self.pk:
            if not self.estado:
                self.estado = TicketEstado.objects.get(nombre="OPEN")

        super().save(*args, **kwargs)

    def clean(self):

        # 🔹 Si aún no tiene estado asignado, no validar nada
        if not self.estado_id:
            return

        # 1️⃣ No permitir cerrar sin observaciones
        if self.estado.nombre == "CLOSED" and not self.observaciones:
            raise ValidationError("Debe agregar observaciones para cerrar el ticket.")

        # 2️⃣ Validaciones solo si el ticket ya existe
        if self.pk:
            old = Ticket.objects.get(pk=self.pk)

            # 2.1 No permitir modificar si ya está cerrado
            if old.estado.nombre == "CLOSED":
                raise ValidationError("No se puede modificar un ticket cerrado.")
                
    def puede_editar(self, user):

        if self.estado.nombre == "CLOSED":
            return False

        if user.rol.nombre in [Role.ADMIN, Role.TECNICO]:
            return True

        if (
            user.rol.nombre == Role.ADMINISTRATIVO
            and self.usuario_crea == user
        ):
            return True

        return False
    
    def puede_cambiar_estado(self, user):
        if self.estado.nombre == "CLOSED":
            return False
        if not user.rol:
            return False
        return user.rol.nombre in [Role.ADMIN, Role.TECNICO]
    
    def cambio_estado_valido(self, nuevo_estado):
        flujo = {
            "OPEN": ["IN_PROGRESS"],
            "IN_PROGRESS": ["CLOSED"],
            "CLOSED": []
        }
        return nuevo_estado in flujo.get(self.estado.nombre, [])
    
    def cambiar_estado(self, nuevo_estado, user, observaciones=None):

        if user.rol.nombre not in ["ADMIN", "TECNICO"]:
            raise ValidationError("No tienes permiso para cambiar el estado.")

        if not self.cambio_estado_valido(nuevo_estado.nombre):
            raise ValidationError("Cambio de estado no permitido.")

        # 🔹 Solo registrar fecha cuando pasa a IN_PROGRESS
        if (
            self.estado.nombre == "OPEN"
            and nuevo_estado.nombre == "IN_PROGRESS"
            and not self.fecha_cambio_estado
        ):
            self.fecha_cambio_estado = timezone.now()

        # 🔹 Si pasa a CLOSED
        if nuevo_estado.nombre == "CLOSED":
            if not observaciones:
                raise ValidationError("Debe agregar observaciones para cerrar el ticket.")

            self.observaciones = observaciones
            self.fecha_cierre = timezone.now()

        self.estado = nuevo_estado

        self.full_clean()
        self.save()