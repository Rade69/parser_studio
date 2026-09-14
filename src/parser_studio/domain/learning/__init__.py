# Domain: learning package.
# Eksportuje: LearningEvent, EventType.
# Ne zna za: SQLite, PySide6, Docling, openpyxl/xlrd, contract.
"""Learning domain — append-only history i EventType enum.

SQLite adapter (LearningRepository port) je u A6.
"""
from .learning_event import EventType, LearningEvent

__all__ = ["EventType", "LearningEvent"]
