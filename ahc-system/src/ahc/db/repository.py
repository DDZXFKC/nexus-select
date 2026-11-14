"""Generic repository: thin CRUD over SQLAlchemy.

Each domain module can either subclass Repository or use it directly.
The intent is to keep call-sites off the Session object so we can later
swap SQLite for Postgres / Supabase without touching business logic.
"""
from __future__ import annotations

from typing import Any, Generic, Iterable, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from .base import Base
from .session import session_scope

T = TypeVar("T", bound=Base)


class Repository(Generic[T]):
    model: Type[T]

    def __init__(self, model: Type[T] | None = None, session: Session | None = None):
        if model is not None:
            self.model = model
        self._external_session = session

    # --- session handling --------------------------------------------------
    def _session(self) -> Session:
        if self._external_session is not None:
            return self._external_session
        # Caller forgot to pass a session and we're in a non-context path.
        # Fall back to a fresh session. Prefer session_scope() in callers.
        return SessionLocal()

    # --- read --------------------------------------------------------------
    def get(self, pk: int) -> T | None:
        with session_scope() as s:
            return s.get(self.model, pk)

    def get_by(self, **filters: Any) -> T | None:
        with session_scope() as s:
            stmt = select(self.model).filter_by(**filters)
            return s.execute(stmt).scalar_one_or_none()

    def list(self, limit: int = 1000, offset: int = 0, **filters: Any) -> Sequence[T]:
        with session_scope() as s:
            stmt = select(self.model).filter_by(**filters).limit(limit).offset(offset)
            return s.execute(stmt).scalars().all()

    # --- write -------------------------------------------------------------
    def add(self, obj: T) -> T:
        with session_scope() as s:
            s.add(obj)
            s.flush()
            s.refresh(obj)
            # Detach so caller can read attributes outside the session.
            s.expunge(obj)
            return obj

    def add_many(self, objs: Iterable[T]) -> list[T]:
        objs = list(objs)
        with session_scope() as s:
            s.add_all(objs)
            s.flush()
            for o in objs:
                s.refresh(o)
                s.expunge(o)
            return objs

    def update(self, obj: T, **fields: Any) -> T:
        with session_scope() as s:
            s.merge(obj)
            for k, v in fields.items():
                setattr(obj, k, v)
            s.flush()
            s.refresh(obj)
            s.expunge(obj)
            return obj

    def delete(self, obj: T) -> None:
        with session_scope() as s:
            managed = s.merge(obj)
            s.delete(managed)

    # --- upsert helper -----------------------------------------------------
    def upsert_by(self, filters: dict[str, Any], defaults: dict[str, Any]) -> T:
        """Find by `filters`; if missing, create with filters+defaults; else update."""
        with session_scope() as s:
            existing = s.execute(
                select(self.model).filter_by(**filters)
            ).scalar_one_or_none()
            if existing is None:
                obj = self.model(**{**filters, **defaults})
                s.add(obj)
                s.flush()
                s.refresh(obj)
                s.expunge(obj)
                return obj
            for k, v in defaults.items():
                setattr(existing, k, v)
            s.flush()
            s.refresh(existing)
            s.expunge(existing)
            return existing


# Late import to avoid circular deps at module load time.
from .session import SessionLocal  # noqa: E402
