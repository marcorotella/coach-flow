"""Dashboard Router serving responsive web interface for Personal Trainers."""

from datetime import datetime, time, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from coach_flow.domain.enums import AppointmentStatus, ClientStatus
from coach_flow.domain.models import Appointment, Client, WorkingHours
from coach_flow.storage.repository import repository

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

DAY_NAMES = [
    "Lunedì",
    "Martedì",
    "Mercoledì",
    "Giovedì",
    "Venerdì",
    "Sabato",
    "Domenica",
]


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def dashboard_overview(request: Request):
    """Render main overview dashboard with today's sessions and metrics."""
    trainer = await repository.get_or_create_default_trainer()
    clients = await repository.get_all_clients(trainer_id=trainer.id)
    appointments = await repository.get_all_appointments(trainer_id=trainer.id)

    clients_map = {c.id: c.name for c in clients}

    today = datetime.now(timezone.utc).date()
    today_list = []
    for app in appointments:
        if app.start_time.date() == today:
            client_name = clients_map.get(app.client_id, "Impegno Personale / Blocco")
            today_list.append({
                "id": app.id,
                "client_name": client_name,
                "start_time": app.start_time,
                "end_time": app.end_time,
                "status": app.status,
                "notes": app.notes,
            })

    stats = {
        "today_appointments": len(
            [a for a in today_list if a["status"] != AppointmentStatus.CANCELLED]
        ),
        "active_clients": len([c for c in clients if c.status == ClientStatus.ACTIVE]),
        "leads_count": len([c for c in clients if c.status == ClientStatus.LEAD]),
    }

    return templates.TemplateResponse(
        request=request,
        name="overview.html",
        context={
            "active_page": "overview",
            "trainer": trainer,
            "stats": stats,
            "today_list": today_list,
        },
    )


@router.get("/working-hours", response_class=HTMLResponse)
async def get_working_hours(request: Request, saved: Optional[bool] = None):
    """Render working hours and shifts configuration page."""
    trainer = await repository.get_or_create_default_trainer()

    days_schedule = []
    for day_idx, day_name in enumerate(DAY_NAMES):
        day_whs = [wh for wh in trainer.working_hours if wh.day_of_week == day_idx]
        is_active = len(day_whs) > 0

        s1_start = day_whs[0].start_time.strftime("%H:%M") if is_active else "08:00"
        s1_end = day_whs[0].end_time.strftime("%H:%M") if is_active else "12:30"

        s2_enabled = len(day_whs) > 1
        s2_start = day_whs[1].start_time.strftime("%H:%M") if s2_enabled else "16:00"
        s2_end = day_whs[1].end_time.strftime("%H:%M") if s2_enabled else "20:00"

        days_schedule.append({
            "day_of_week": day_idx,
            "name": day_name,
            "is_active": is_active,
            "s1_start": s1_start,
            "s1_end": s1_end,
            "s2_enabled": s2_enabled,
            "s2_start": s2_start,
            "s2_end": s2_end,
        })

    alert_message = "Orari e regole aggiornati con successo!" if saved else None

    return templates.TemplateResponse(
        request=request,
        name="working_hours.html",
        context={
            "active_page": "working_hours",
            "trainer": trainer,
            "days_schedule": days_schedule,
            "alert_message": alert_message,
        },
    )


@router.post("/working-hours")
async def post_working_hours(request: Request):
    """Save updated working hours and session buffer rules."""
    form_data = await request.form()
    trainer = await repository.get_or_create_default_trainer()

    session_duration = int(form_data.get("session_duration", 60))
    buffer_minutes = int(form_data.get("buffer_minutes", 15))

    new_working_hours: list[WorkingHours] = []

    for day_idx in range(7):
        active_key = f"day_{day_idx}_active"
        if active_key in form_data:
            # Shift 1
            s1_start_raw = form_data.get(f"day_{day_idx}_s1_start", "08:00")
            s1_end_raw = form_data.get(f"day_{day_idx}_s1_end", "12:30")
            t_s1_start = time.fromisoformat(str(s1_start_raw))
            t_s1_end = time.fromisoformat(str(s1_end_raw))
            if t_s1_end > t_s1_start:
                new_working_hours.append(
                    WorkingHours(
                        day_of_week=day_idx,
                        start_time=t_s1_start,
                        end_time=t_s1_end,
                    )
                )

            # Shift 2 (Optional split shift)
            s2_enabled_key = f"day_{day_idx}_s2_enabled"
            if s2_enabled_key in form_data:
                s2_start_raw = form_data.get(f"day_{day_idx}_s2_start", "16:00")
                s2_end_raw = form_data.get(f"day_{day_idx}_s2_end", "20:00")
                t_s2_start = time.fromisoformat(str(s2_start_raw))
                t_s2_end = time.fromisoformat(str(s2_end_raw))
                if t_s2_end > t_s2_start:
                    new_working_hours.append(
                        WorkingHours(
                            day_of_week=day_idx,
                            start_time=t_s2_start,
                            end_time=t_s2_end,
                        )
                    )

    trainer.session_duration_minutes = session_duration
    trainer.buffer_between_sessions_minutes = buffer_minutes
    trainer.working_hours = new_working_hours

    await repository.save_trainer(trainer)

    return RedirectResponse(
        url="/dashboard/working-hours?saved=true",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/calendar", response_class=HTMLResponse)
async def get_calendar(request: Request, blocked: Optional[bool] = None):
    """View appointment agenda and create blackout/blocked personal slots."""
    trainer = await repository.get_or_create_default_trainer()
    clients = await repository.get_all_clients(trainer_id=trainer.id)
    appointments = await repository.get_all_appointments(trainer_id=trainer.id)

    clients_map = {c.id: c.name for c in clients}

    formatted_apps = []
    for app in appointments:
        client_name = clients_map.get(app.client_id, "Blocco Personale")
        formatted_apps.append({
            "id": app.id,
            "client_name": client_name,
            "start_time": app.start_time,
            "end_time": app.end_time,
            "duration_minutes": app.duration_minutes,
            "status": app.status,
            "reminder_24h_sent": app.reminder_24h_sent,
            "reminder_2h_sent": app.reminder_2h_sent,
            "notes": app.notes,
        })

    alert_message = "Slot personale bloccato con successo!" if blocked else None

    return templates.TemplateResponse(
        request=request,
        name="calendar.html",
        context={
            "active_page": "calendar",
            "trainer": trainer,
            "appointments": formatted_apps,
            "alert_message": alert_message,
        },
    )


@router.post("/calendar/block")
async def block_personal_slot(
    request: Request,
    start_time: str = Form(...),
    end_time: str = Form(...),
    notes: Optional[str] = Form(None),
):
    """Block a custom time interval for trainer personal training or outside appointments."""
    trainer = await repository.get_or_create_default_trainer()

    dt_start = datetime.fromisoformat(start_time).replace(tzinfo=timezone.utc)
    dt_end = datetime.fromisoformat(end_time).replace(tzinfo=timezone.utc)

    block_notes = f"[IMPEGNO PERSONALE] {notes or 'Non disponibile'}"

    appointment = Appointment(
        trainer_id=trainer.id,
        client_id="trainer_personal_block",
        start_time=dt_start,
        end_time=dt_end,
        status=AppointmentStatus.CANCELLED,
        notes=block_notes,
    )
    await repository.save_appointment(appointment)

    return RedirectResponse(
        url="/dashboard/calendar?blocked=true",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/calendar/{appointment_id}/cancel")
async def cancel_dashboard_appointment(appointment_id: str):
    """Cancel an appointment from the dashboard."""
    app = await repository.get_appointment_by_id(appointment_id)
    if app:
        app.status = AppointmentStatus.CANCELLED
        await repository.save_appointment(app)

    return RedirectResponse(
        url="/dashboard/calendar",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/clients", response_class=HTMLResponse)
async def get_clients(request: Request):
    """View athlete and lead directory with AI pause/active toggles."""
    trainer = await repository.get_or_create_default_trainer()
    clients = await repository.get_all_clients(trainer_id=trainer.id)

    return templates.TemplateResponse(
        request=request,
        name="clients.html",
        context={
            "active_page": "clients",
            "trainer": trainer,
            "clients": clients,
        },
    )


@router.post("/clients/{client_id}/toggle-ai")
async def toggle_client_ai(client_id: str):
    """Toggle the automated AI assistant on or off for a specific client."""
    client = await repository.get_client_by_id(client_id)
    if client:
        client.is_ai_active = not client.is_ai_active
        await repository.save_client(client)

    return RedirectResponse(
        url="/dashboard/clients",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/clients/new")
async def add_new_client(
    name: str = Form(...),
    phone_number: str = Form(...),
    fitness_goals: Optional[str] = Form(None),
):
    """Quickly register a new lead or athlete into the system."""
    trainer = await repository.get_or_create_default_trainer()

    cleaned_phone = phone_number.replace(" ", "").replace("-", "")
    if not cleaned_phone.startswith("+"):
        cleaned_phone = f"+{cleaned_phone}"

    client = Client(
        trainer_id=trainer.id,
        name=name,
        phone_number=cleaned_phone,
        status=ClientStatus.LEAD,
        fitness_goals=fitness_goals,
    )
    await repository.save_client(client)

    return RedirectResponse(
        url="/dashboard/clients",
        status_code=status.HTTP_303_SEE_OTHER,
    )
