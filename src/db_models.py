import uuid
from datetime import datetime

from sqlalchemy import (
    CHAR,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    SmallInteger,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Tablolar şemasız tanımlanır; gerçek şema (PG_SCHEMA) build_engine içinde
# schema_translate_map ile verilir. Böylece bu modül config'e bağımlı olmaz.
class Base(DeclarativeBase):
    pass


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nickname: Mapped[str] = mapped_column(String(30), nullable=False)
    nickname_key: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    pin_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    pin_salt: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    failed_pins: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    attempts: Mapped[list["Attempt"]] = relationship(back_populates="participant")


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (Index("ix_attempts_participant_created", "participant_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, unique=True, default=uuid.uuid4)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"), nullable=False)
    answers: Mapped[str] = mapped_column(CHAR(30), nullable=False)
    score_rekabet: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score_isbirligi: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score_uzlasma: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score_kacinma: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score_iltifat: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    participant: Mapped[Participant] = relationship(back_populates="attempts")


class AiComment(Base):
    __tablename__ = "ai_comments"

    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id"), primary_key=True)
    model: Mapped[str] = mapped_column(String(60), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
