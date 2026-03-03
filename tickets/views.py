from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Ticket,  TicketEstado
from users.models import Role
from .forms import TicketForm
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from datetime import datetime
from django.core.paginator import Paginator

@login_required
def crear_ticket(request):
    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)

            # Asignaciones obligatorias antes de guardar
            ticket.usuario_crea = request.user
            ticket.estado = TicketEstado.objects.get(nombre="OPEN")

            ticket.save()

            return redirect("lista_tickets")
    else:
        form = TicketForm()

    return render(request, "tickets/crear_ticket.html", {"form": form})

def lista_tickets(request):

    user = request.user

    # 🔹 Base queryset según rol (SIN filtros)
    if not user.rol:
        base_tickets = Ticket.objects.all()

    elif user.rol.nombre == Role.ADMIN:
        base_tickets = Ticket.objects.all()

    elif user.rol.nombre == Role.TECNICO:
        base_tickets = Ticket.objects.all()

    elif user.rol.nombre == Role.ADMINISTRATIVO:
        base_tickets = Ticket.objects.filter(usuario_crea=user)

    else:
        base_tickets = Ticket.objects.none()

    # 🔹 Copia para aplicar filtros
    tickets = base_tickets

    # -------- FILTROS --------

    estado = request.GET.get("estado")
    prioridad = request.GET.get("prioridad")
    ticket_id = request.GET.get("id")
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    if ticket_id:
        tickets = tickets.filter(id=ticket_id)

    if estado:
        tickets = tickets.filter(estado__nombre=estado)

    if prioridad:
        tickets = tickets.filter(prioridad=prioridad)

    if fecha_inicio:
        tickets = tickets.filter(fecha_creacion__date__gte=fecha_inicio)

    if fecha_fin:
        tickets = tickets.filter(fecha_creacion__date__lte=fecha_fin)

    # 📊 ESTADÍSTICAS (sobre base sin filtros)
    total = base_tickets.count()
    open_count = base_tickets.filter(estado__nombre="OPEN").count()
    in_progress_count = base_tickets.filter(estado__nombre="IN_PROGRESS").count()
    closed_count = base_tickets.filter(estado__nombre="CLOSED").count()

    # 🔹 PAGINACIÓN
    paginator = Paginator(tickets.order_by("-fecha_creacion"), 20)  # 10 por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "tickets": page_obj,  #  ahora enviamos page_obj
        "page_obj": page_obj,
        "estado_actual": estado,
        "prioridad_actual": prioridad,
        "id_actual": ticket_id,
        "fecha_inicio_actual": fecha_inicio,
        "fecha_fin_actual": fecha_fin,
        "total": total,
        "open_count": open_count,
        "in_progress_count": in_progress_count,
        "closed_count": closed_count,
    }

    return render(request, "tickets/lista_tickets.html", context)

@login_required
def detalle_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    # 🔐 Control básico de acceso
    if request.user.rol.nombre == "ADMIN":
        pass
    elif request.user.rol.nombre == "TECNICO":
        pass
    elif request.user.rol.nombre == "ADMINISTRATIVO":
        if ticket.usuario_crea != request.user:
            return HttpResponseForbidden("No tienes permiso para ver este ticket.")

    return render(request, "tickets/detalle_ticket.html", {"ticket": ticket})

@require_POST
@login_required
def cambiar_estado(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    # Permisos
    if request.user.rol.nombre not in ["ADMIN", "TECNICO"]:
        return HttpResponseForbidden("No tienes permiso.")

    nuevo_estado_nombre = request.POST.get("estado")
    nuevo_estado = TicketEstado.objects.get(nombre=nuevo_estado_nombre)
    observaciones = request.POST.get("observaciones")

    try:
        ticket.cambiar_estado(
            nuevo_estado=nuevo_estado,
            user=request.user,
            observaciones=observaciones
        )
        messages.success(request, "Estado actualizado correctamente.")

    except Exception as e:
        messages.error(request, str(e))

    return redirect("detalle_ticket", pk=pk)

def exportar_tickets_excel(request):

    user = request.user

    # 🔐 Permisos
    if user.rol.nombre not in [Role.ADMIN, Role.TECNICO]:
        return HttpResponse("No tienes permiso para exportar.", status=403)

    # 🔹 Base queryset según rol
    if user.rol.nombre == Role.ADMIN:
        tickets = Ticket.objects.all()

    elif user.rol.nombre == Role.TECNICO:
        tickets = Ticket.objects.all()

    else:
        tickets = Ticket.objects.none()

    # 🔹 Aplicar los mismos filtros que la lista
    estado = request.GET.get("estado")
    prioridad = request.GET.get("prioridad")
    ticket_id = request.GET.get("id")
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    if ticket_id:
        tickets = tickets.filter(id=ticket_id)

    if estado:
        tickets = tickets.filter(estado__nombre=estado)

    if prioridad:
        tickets = tickets.filter(prioridad=prioridad)

    if fecha_inicio:
        tickets = tickets.filter(fecha_creacion__date__gte=fecha_inicio)

    if fecha_fin:
        tickets = tickets.filter(fecha_creacion__date__lte=fecha_fin)

    # 📊 Crear Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Tickets"

    headers = [
        "ID",
        "Estado",
        "Prioridad",
        "Usuario Creador",
        "Fecha Creación",
        "Fecha Inicio Gestión",
        "Fecha Cierre",
        "Descripción",
        "Observaciones",
    ]

    ws.append(headers)

    # Encabezados en negrita
    for cell in ws[1]:
        cell.font = Font(bold=True)

    # Agregar datos
    for ticket in tickets:
        ws.append([
            ticket.id,
            ticket.estado.nombre,
            ticket.prioridad,
            ticket.usuario_crea.username,
            ticket.fecha_creacion.replace(tzinfo=None) if ticket.fecha_creacion else None,
            ticket.fecha_cambio_estado.replace(tzinfo=None) if ticket.fecha_cambio_estado else None,
            ticket.fecha_cierre.replace(tzinfo=None) if ticket.fecha_cierre else None,
            ticket.descripcion,
            ticket.observaciones,
        ])

    # 📥 Respuesta HTTP
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    nombre_archivo = f"tickets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'

    wb.save(response)

    return response