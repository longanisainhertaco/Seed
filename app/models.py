from datetime import datetime, date
from typing import Optional
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class TaskType(str, Enum):
    PACK = "Pack"
    CATALOG = "Catalog"
    REORDER = "Reorder"


class TaskStatus(str, Enum):
    TODO = "To Do"
    PENDING = "To Do"  # backward compatible alias
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    CANCELLED = "Cancelled"

    @classmethod
    def normalize(cls, value: str) -> str:
        if not value:
            return cls.TODO
        normalized = value.value if isinstance(value, Enum) else str(value).strip()
        lower = normalized.lower()
        mapping = {
            "pending": cls.TODO.value,
            cls.TODO.lower(): cls.TODO.value,
            cls.IN_PROGRESS.lower(): cls.IN_PROGRESS.value,
            cls.DONE.lower(): cls.DONE.value,
            cls.CANCELLED.lower(): cls.CANCELLED.value,
        }
        return mapping.get(lower, normalized)


class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Seed(Base):
    __tablename__ = "seeds"
    __table_args__ = (
        Index("ix_seeds_type", "type"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    packets_made = Column(Integer, default=0)
    seed_source = Column(String)
    date_ordered = Column(Date)
    date_finished = Column(Date)
    date_cataloged = Column(Date)
    date_ran_out = Column(Date)
    amount_text = Column(String)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    tasks = relationship(
        "Task",
        back_populates="seed",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    inventory = relationship(
        "Inventory",
        back_populates="seed",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    adjustments = relationship(
        "InventoryAdjustment",
        back_populates="seed",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(
        self,
        id: Optional[int] = None,
        type: str = "",
        name: str = "",
        packets_made: int = 0,
        seed_source: str = "",
        date_ordered: Optional[date] = None,
        date_finished: Optional[date] = None,
        date_cataloged: Optional[date] = None,
        date_ran_out: Optional[date] = None,
        amount_text: str = "",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.type = type
        self.name = name
        self.packets_made = packets_made
        self.seed_source = seed_source
        self.date_ordered = _as_date(date_ordered)
        self.date_finished = _as_date(date_finished)
        self.date_cataloged = _as_date(date_cataloged)
        self.date_ran_out = _as_date(date_ran_out)
        self.amount_text = amount_text
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("seed_id", "task_type", name="uq_seed_task_type"),
        Index("ix_tasks_seed_id", "seed_id"),
        Index("ix_tasks_due_date", "due_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    seed_id = Column(Integer, ForeignKey("seeds.id", ondelete="CASCADE"), nullable=False)
    task_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    priority = Column(String, nullable=False, default="Medium")
    due_date = Column(Date)
    completed_at = Column(DateTime)
    description = Column(String)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    seed = relationship("Seed", back_populates="tasks")

    def __init__(
        self,
        id: Optional[int] = None,
        seed_id: int = 0,
        task_type: str = TaskType.PACK,
        status: str = TaskStatus.TODO,
        priority: str = TaskPriority.MEDIUM,
        due_date: Optional[date] = None,
        completed_at: Optional[datetime] = None,
        description: str = "",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.seed_id = seed_id
        self.task_type = task_type
        self.status = TaskStatus.normalize(status)
        self.priority = priority or TaskPriority.MEDIUM
        self.due_date = _as_date(due_date)
        self.completed_at = _as_datetime(completed_at)
        self.description = description
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        Index("ix_inventory_seed_id", "seed_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    seed_id = Column(Integer, ForeignKey("seeds.id", ondelete="CASCADE"), nullable=False, unique=True)
    current_amount = Column(String, default="")
    buy_more = Column(Boolean, default=False)
    extra = Column(Boolean, default=False)
    notes = Column(String)
    last_updated = Column(DateTime, nullable=False)

    seed = relationship("Seed", back_populates="inventory")

    def __init__(
        self,
        id: Optional[int] = None,
        seed_id: int = 0,
        current_amount: str = "",
        buy_more: bool = False,
        extra: bool = False,
        notes: str = "",
        last_updated: Optional[datetime] = None,
    ):
        self.id = id
        self.seed_id = seed_id
        self.current_amount = current_amount
        self.buy_more = buy_more
        self.extra = extra
        self.notes = notes
        self.last_updated = last_updated or datetime.now()


class InventoryAdjustment(Base):
    __tablename__ = "inventory_adjustments"
    __table_args__ = (
        Index("ix_inventory_adjustments_seed_id", "seed_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    seed_id = Column(Integer, ForeignKey("seeds.id", ondelete="CASCADE"), nullable=False)
    adjustment_type = Column(String, nullable=False)
    amount_change = Column(String)
    reason = Column(String)
    adjusted_at = Column(DateTime, nullable=False)

    seed = relationship("Seed", back_populates="adjustments")

    def __init__(
        self,
        id: Optional[int] = None,
        seed_id: int = 0,
        adjustment_type: str = "",
        amount_change: str = "",
        reason: str = "",
        adjusted_at: Optional[datetime] = None,
    ):
        self.id = id
        self.seed_id = seed_id
        self.adjustment_type = adjustment_type
        self.amount_change = amount_change
        self.reason = reason
        self.adjusted_at = adjusted_at or datetime.now()


def _as_date(value: Optional[date]):
    """Convert string/datetime values to date objects."""
    if value in (None, "", b""):
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except (TypeError, ValueError):
        return None


def _as_datetime(value: Optional[datetime]):
    """Convert string/date values to datetime objects."""
    if value in (None, "", b""):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
