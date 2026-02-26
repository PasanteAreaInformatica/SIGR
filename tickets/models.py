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
    nombre = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.nombre


# =========================
# TICKET
# =========================
class Ticket(models.Model):
    
    class Prioridad(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

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

        self.full_clean()  # Fuerza validaciones

        if self.pk:
            old = Ticket.objects.get(pk=self.pk)

            if old.estado != self.estado:
                self.fecha_cambio_estado = timezone.now()

                if self.estado.nombre == "CLOSED":
                    self.fecha_cierre = timezone.now()

        else:
            # Si es nuevo y no tiene estado, asignar OPEN
            if not self.estado:
                self.estado = TicketEstado.objects.get(nombre="OPEN")

        super().save(*args, **kwargs)

    def clean(self):

        # 1️⃣ No permitir cerrar sin observaciones
        if self.estado.nombre == "CLOSED" and not self.observaciones:
            raise ValidationError("Debe agregar observaciones para cerrar el ticket.")

        # 2️⃣ Validaciones solo si el ticket ya existe
        if self.pk:
            old = Ticket.objects.get(pk=self.pk)

            # 2.1 No permitir modificar si ya está cerrado
            if old.estado.nombre == "CLOSED":
                raise ValidationError("No se puede modificar un ticket cerrado.")

            # 2.2 Validar flujo de estados
            if old.estado != self.estado:
                if not self.cambio_estado_valido(self.estado.nombre):
                    raise ValidationError(
                        f"No se permite cambiar de {old.estado.nombre} a {self.estado.nombre}"
                    )
                
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
            "IN_PROGRESS": ["RESOLVED"],
            "RESOLVED": ["CLOSED", "IN_PROGRESS"],
            "CLOSED": []
        }

        return nuevo_estado in flujo.get(self.estado.nombre, [])