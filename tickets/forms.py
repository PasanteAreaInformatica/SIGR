from django import forms
from .models import Ticket

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        exclude = ["usuario_crea", "estado", "fecha_cambio_estado"]