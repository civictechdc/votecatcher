"""Base engine implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy import Engine
from sqlmodel import Session


class BaseEngine(ABC):
    """Abstract base class for database engines."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def connection_url(self) -> str: ...

    @property
    @abstractmethod
    def raw_engine(self) -> Engine: ...

    @abstractmethod
    def create_session(self) -> Session: ...

    @abstractmethod
    def initialize(self) -> None: ...

    @abstractmethod
    def health_check(self) -> bool: ...
