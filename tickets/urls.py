from django.urls import path
from . import views

urlpatterns = [
    path("lista/", views.lista_tickets, name="lista_tickets"),
    path("crear/", views.crear_ticket, name="crear_ticket"),
    path("<int:pk>/", views.detalle_ticket, name="detalle_ticket"),
    path("<int:pk>/cambiar_estado/", views.cambiar_estado, name="cambiar_estado"),
    path("tickets/exportar/", views.exportar_tickets_excel, name="exportar_tickets"),
]