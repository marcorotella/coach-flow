"""Trainer Assistant module exports."""

from coach_flow.assistant.router import router
from coach_flow.assistant.trainer import TrainerAssistantService

__all__ = ["TrainerAssistantService", "router"]
