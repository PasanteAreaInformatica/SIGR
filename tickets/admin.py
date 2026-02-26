from django.contrib import admin
from .models import TipoFalla, TicketEstado, Ticket


admin.site.register(TipoFalla)
admin.site.register(TicketEstado)
admin.site.register(Ticket)
