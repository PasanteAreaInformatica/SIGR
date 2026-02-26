from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Ticket,  TicketEstado
from users.models import Role
from .forms import TicketForm


@login_required
def crear_ticket(request):
    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.usuario_crea = request.user
            ticket.estado = TicketEstado.objects.get(nombre="OPEN")
            ticket.save()
            return redirect("lista_tickets")
    else:
        form = TicketForm()

    return render(request, "tickets/crear_ticket.html", {"form": form})

def lista_tickets(request):

    user = request.user

    if not user.rol:
        tickets = Ticket.objects.all()

    if user.rol.nombre == Role.ADMIN:
        tickets = Ticket.objects.all()

    elif user.rol.nombre == Role.TECNICO:
        tickets = Ticket.objects.all()

    elif user.rol.nombre == Role.ADMINISTRATIVO:
        tickets = Ticket.objects.filter(usuario_crea=user)

    else:
        tickets = Ticket.objects.none()

    context = {
        "tickets": tickets
    }

    return render(request, "tickets/lista_tickets.html", context)
