"""Asynchronous SQLAlchemy repository implementing domain persistence."""

import json
import logging
from datetime import date, datetime, time, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from coach_flow.domain.enums import AppointmentStatus, ClientStatus
from coach_flow.domain.models import Appointment, Client, Trainer, WorkingHours
from coach_flow.storage.database import get_session_maker
from coach_flow.storage.models import AppointmentModel, ClientModel, TrainerModel

logger = logging.getLogger(__name__)


class SQLAlchemyRepository:
    """Async repository providing thread-safe persistence for domain entities."""

    def __init__(self, session: Optional[AsyncSession] = None) -> None:
        self._external_session = session

    async def _execute_with_session(self, func):
        if self._external_session is not None:
            return await func(self._external_session)

        session_maker = get_session_maker()
        async with session_maker() as session:
            try:
                res = await func(session)
                await session.commit()
                return res
            except Exception:
                await session.rollback()
                raise

    # ------------------ Client Operations ------------------

    async def save_client(self, client: Client) -> Client:
        async def _op(session: AsyncSession):
            stmt = select(ClientModel).where(ClientModel.id == client.id)
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()

            if existing:
                existing.trainer_id = client.trainer_id or ""
                existing.name = client.name
                existing.phone_number = client.phone_number
                existing.status = client.status.value
                existing.fitness_goals = client.fitness_goals
                existing.medical_notes = client.medical_notes
                existing.notes = client.notes
                existing.is_ai_active = client.is_ai_active
            else:
                model = ClientModel(
                    id=client.id,
                    trainer_id=client.trainer_id or "",
                    name=client.name,
                    phone_number=client.phone_number,
                    status=client.status.value,
                    fitness_goals=client.fitness_goals,
                    medical_notes=client.medical_notes,
                    notes=client.notes,
                    is_ai_active=client.is_ai_active,
                    created_at=client.created_at,
                )
                session.add(model)
            return client

        return await self._execute_with_session(_op)

    async def get_client_by_phone(self, phone: str) -> Optional[Client]:
        clean_phone = phone.replace(" ", "").replace("-", "")

        async def _op(session: AsyncSession):
            stmt = select(ClientModel).where(ClientModel.phone_number == clean_phone)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return self._to_client_domain(model)

        return await self._execute_with_session(_op)

    async def get_client_by_id(self, client_id: str) -> Optional[Client]:
        async def _op(session: AsyncSession):
            stmt = select(ClientModel).where(ClientModel.id == client_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return self._to_client_domain(model)

        return await self._execute_with_session(_op)

    async def get_all_clients(self, trainer_id: Optional[str] = None) -> list[Client]:
        async def _op(session: AsyncSession):
            stmt = select(ClientModel).order_by(ClientModel.created_at.desc())
            if trainer_id:
                stmt = stmt.where(ClientModel.trainer_id == trainer_id)
            res = await session.execute(stmt)
            return [self._to_client_domain(m) for m in res.scalars().all()]

        return await self._execute_with_session(_op)

    # ------------------ Appointment Operations ------------------

    async def save_appointment(self, appointment: Appointment) -> Appointment:
        async def _op(session: AsyncSession):
            stmt = select(AppointmentModel).where(AppointmentModel.id == appointment.id)
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()

            if existing:
                existing.trainer_id = appointment.trainer_id
                existing.client_id = appointment.client_id
                existing.calendar_event_id = appointment.calendar_event_id
                existing.start_time = appointment.start_time
                existing.end_time = appointment.end_time
                existing.status = appointment.status.value
                existing.location = appointment.location
                existing.notes = appointment.notes
                existing.reminder_24h_sent = appointment.reminder_24h_sent
                existing.reminder_2h_sent = appointment.reminder_2h_sent
                existing.confirmed_by_client = appointment.confirmed_by_client
                existing.updated_at = appointment.updated_at
            else:
                model = AppointmentModel(
                    id=appointment.id,
                    trainer_id=appointment.trainer_id,
                    client_id=appointment.client_id,
                    calendar_event_id=appointment.calendar_event_id,
                    start_time=appointment.start_time,
                    end_time=appointment.end_time,
                    status=appointment.status.value,
                    location=appointment.location,
                    notes=appointment.notes,
                    reminder_24h_sent=appointment.reminder_24h_sent,
                    reminder_2h_sent=appointment.reminder_2h_sent,
                    confirmed_by_client=appointment.confirmed_by_client,
                    created_at=appointment.created_at,
                    updated_at=appointment.updated_at,
                )
                session.add(model)
            return appointment

        return await self._execute_with_session(_op)

    async def get_appointment(self, appointment_id: str) -> Optional[Appointment]:
        async def _op(session: AsyncSession):
            stmt = select(AppointmentModel).where(AppointmentModel.id == appointment_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return self._to_appointment_domain(model)

        return await self._execute_with_session(_op)

    async def get_all_appointments(
        self, trainer_id: Optional[str] = None
    ) -> list[Appointment]:
        async def _op(session: AsyncSession):
            stmt = select(AppointmentModel).order_by(AppointmentModel.start_time.asc())
            if trainer_id:
                stmt = stmt.where(AppointmentModel.trainer_id == trainer_id)
            res = await session.execute(stmt)
            return [self._to_appointment_domain(m) for m in res.scalars().all()]

        return await self._execute_with_session(_op)

    async def get_appointments_by_date(self, target_date: date) -> list[Appointment]:
        day_start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(target_date, time.max, tzinfo=timezone.utc)

        async def _op(session: AsyncSession):
            stmt = (
                select(AppointmentModel)
                .where(
                    AppointmentModel.start_time >= day_start,
                    AppointmentModel.start_time <= day_end,
                )
                .order_by(AppointmentModel.start_time.asc())
            )
            res = await session.execute(stmt)
            models = res.scalars().all()
            return [self._to_appointment_domain(m) for m in models]

        return await self._execute_with_session(_op)

    async def delete_appointment(self, appointment_id: str) -> bool:
        async def _op(session: AsyncSession):
            stmt = delete(AppointmentModel).where(AppointmentModel.id == appointment_id)
            res = await session.execute(stmt)
            return bool(res.rowcount and res.rowcount > 0)

        return await self._execute_with_session(_op)

    # ------------------ Trainer Operations ------------------

    async def save_trainer(self, trainer: Trainer) -> Trainer:
        wh_data = [
            {
                "day_of_week": w.day_of_week,
                "start_time": w.start_time.isoformat(),
                "end_time": w.end_time.isoformat(),
            }
            for w in trainer.working_hours
        ]
        wh_json = json.dumps(wh_data)

        async def _op(session: AsyncSession):
            stmt = select(TrainerModel).where(TrainerModel.id == trainer.id)
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()

            if existing:
                existing.name = trainer.name
                existing.phone_number = trainer.phone_number
                existing.session_duration_minutes = trainer.session_duration_minutes
                existing.buffer_between_sessions_minutes = (
                    trainer.buffer_between_sessions_minutes
                )
                existing.working_hours_json = wh_json
            else:
                model = TrainerModel(
                    id=trainer.id,
                    name=trainer.name,
                    phone_number=trainer.phone_number,
                    session_duration_minutes=trainer.session_duration_minutes,
                    buffer_between_sessions_minutes=(
                        trainer.buffer_between_sessions_minutes
                    ),
                    working_hours_json=wh_json,
                )
                session.add(model)
            return trainer

        return await self._execute_with_session(_op)

    async def get_trainer(self, trainer_id: str) -> Optional[Trainer]:
        async def _op(session: AsyncSession):
            stmt = select(TrainerModel).where(TrainerModel.id == trainer_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return self._to_trainer_domain(model)

        return await self._execute_with_session(_op)

    async def get_or_create_default_trainer(self) -> Trainer:
        """Fetch or automatically initialize the primary trainer with default schedule."""
        from coach_flow.config import settings

        trainer_id = "default"
        existing = await self.get_trainer(trainer_id)
        if existing:
            return existing

        # Default schedule: Mon-Fri morning (08:00-12:30) & afternoon (15:30-20:00),
        # Sat morning (08:30-13:00)
        default_wh = [
            WorkingHours(day_of_week=d, start_time=time(8, 0), end_time=time(12, 30))
            for d in range(5)
        ] + [
            WorkingHours(day_of_week=d, start_time=time(15, 30), end_time=time(20, 0))
            for d in range(5)
        ] + [
            WorkingHours(day_of_week=5, start_time=time(8, 30), end_time=time(13, 0))
        ]

        phone = settings.PT_PHONE_NUMBER or "+393000000000"
        if not phone.startswith("+"):
            phone = f"+{phone}"

        trainer = Trainer(
            id=trainer_id,
            name=settings.PT_NAME or "Coach",
            phone_number=phone,
            session_duration_minutes=60,
            buffer_between_sessions_minutes=15,
            working_hours=default_wh,
        )
        return await self.save_trainer(trainer)

    # ------------------ Domain Mappers ------------------

    @staticmethod
    def _to_trainer_domain(model: TrainerModel) -> Trainer:
        try:
            wh_raw = json.loads(model.working_hours_json or "[]")
            wh_list = [
                WorkingHours(
                    day_of_week=w["day_of_week"],
                    start_time=time.fromisoformat(w["start_time"]),
                    end_time=time.fromisoformat(w["end_time"]),
                )
                for w in wh_raw
            ]
        except Exception:
            wh_list = []

        return Trainer(
            id=model.id,
            name=model.name,
            phone_number=model.phone_number,
            session_duration_minutes=model.session_duration_minutes,
            buffer_between_sessions_minutes=model.buffer_between_sessions_minutes,
            working_hours=wh_list,
        )

    @staticmethod
    def _to_client_domain(model: ClientModel) -> Client:
        try:
            status = ClientStatus(model.status)
        except ValueError:
            status = ClientStatus.LEAD

        return Client(
            id=model.id,
            trainer_id=model.trainer_id or None,
            name=model.name,
            phone_number=model.phone_number,
            status=status,
            fitness_goals=model.fitness_goals,
            medical_notes=model.medical_notes,
            notes=model.notes,
            is_ai_active=getattr(model, "is_ai_active", True),
            created_at=model.created_at,
        )

    @staticmethod
    def _to_appointment_domain(model: AppointmentModel) -> Appointment:
        try:
            status = AppointmentStatus(model.status)
        except ValueError:
            status = AppointmentStatus.SCHEDULED

        return Appointment(
            id=model.id,
            trainer_id=model.trainer_id,
            client_id=model.client_id,
            calendar_event_id=model.calendar_event_id,
            start_time=model.start_time,
            end_time=model.end_time,
            status=status,
            location=model.location,
            notes=model.notes,
            reminder_24h_sent=model.reminder_24h_sent,
            reminder_2h_sent=model.reminder_2h_sent,
            confirmed_by_client=model.confirmed_by_client,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


# Global default repository instance
repository = SQLAlchemyRepository()
