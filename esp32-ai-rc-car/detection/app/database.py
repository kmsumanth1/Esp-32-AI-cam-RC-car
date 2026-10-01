from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class DetectionLog(Base):
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(64), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Database:
    """Stores detection events. SQLite by default, MySQL via DATABASE_URL."""

    def __init__(self, url: str):
        kwargs: dict = {"pool_pre_ping": True}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
            if url in ("sqlite://", "sqlite:///:memory:"):
                kwargs["poolclass"] = StaticPool  # keep one in-memory DB across threads
        self.engine = create_engine(url, **kwargs)
        self._session = sessionmaker(self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

    def log(self, label: str, confidence: float) -> None:
        with self._session() as session:
            session.add(DetectionLog(label=label, confidence=confidence))
            session.commit()

    def recent(self, limit: int = 50) -> list[dict]:
        stmt = select(DetectionLog).order_by(DetectionLog.id.desc()).limit(limit)
        with self._session() as session:
            rows = session.scalars(stmt).all()
        return [
            {
                "id": r.id,
                "label": r.label,
                "confidence": round(r.confidence, 3),
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
