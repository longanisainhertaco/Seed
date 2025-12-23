from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
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

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    packets_made = Column(Integer, default=0)
    seed_source = Column(String)
    date_ordered = Column(String)
    date_finished = Column(String)
    date_cataloged = Column(String)
    date_ran_out = Column(String)
    amount_text = Column(String)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

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
        date_ordered: Optional[str] = None,
        date_finished: Optional[str] = None,
        date_cataloged: Optional[str] = None,
        date_ran_out: Optional[str] = None,
        amount_text: str = "",
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        self.id = id
        self.type = type
        self.name = name
        self.packets_made = packets_made
        self.seed_source = seed_source
        self.date_ordered = date_ordered
        self.date_finished = date_finished
        self.date_cataloged = date_cataloged
        self.date_ran_out = date_ran_out
        self.amount_text = amount_text
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    seed_id = Column(Integer, ForeignKey("seeds.id", ondelete="CASCADE"), nullable=False)
    task_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    priority = Column(String, nullable=False, default="Medium")
    due_date = Column(String)
    completed_at = Column(String)
    description = Column(String)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

    seed = relationship("Seed", back_populates="tasks")

    def __init__(
        self,
        id: Optional[int] = None,
        seed_id: int = 0,
        task_type: str = TaskType.PACK,
        status: str = TaskStatus.TODO,
        priority: str = TaskPriority.MEDIUM,
        due_date: Optional[str] = None,
        completed_at: Optional[str] = None,
        description: str = "",
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        self.id = id
        self.seed_id = seed_id
        self.task_type = task_type
        self.status = TaskStatus.normalize(status)
        self.priority = priority or TaskPriority.MEDIUM
        self.due_date = due_date
        self.completed_at = completed_at
        self.description = description
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    seed_id = Column(Integer, ForeignKey("seeds.id", ondelete="CASCADE"), nullable=False, unique=True)
    current_amount = Column(String, default="")
    buy_more = Column(Boolean, default=False)
    extra = Column(Boolean, default=False)
    notes = Column(String)
    last_updated = Column(String, nullable=False)

    seed = relationship("Seed", back_populates="inventory")

    def __init__(
        self,
        id: Optional[int] = None,
        seed_id: int = 0,
        current_amount: str = "",
        buy_more: bool = False,
        extra: bool = False,
        notes: str = "",
        last_updated: Optional[str] = None,
    ):
        self.id = id
        self.seed_id = seed_id
        self.current_amount = current_amount
        self.buy_more = buy_more
        self.extra = extra
        self.notes = notes
        self.last_updated = last_updated or datetime.now().isoformat()


class InventoryAdjustment(Base):
    __tablename__ = "inventory_adjustments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    seed_id = Column(Integer, ForeignKey("seeds.id", ondelete="CASCADE"), nullable=False)
    adjustment_type = Column(String, nullable=False)
    amount_change = Column(String)
    reason = Column(String)
    adjusted_at = Column(String, nullable=False)

    seed = relationship("Seed", back_populates="adjustments")

    def __init__(
        self,
        id: Optional[int] = None,
        seed_id: int = 0,
        adjustment_type: str = "",
        amount_change: str = "",
        reason: str = "",
        adjusted_at: Optional[str] = None,
    ):
        self.id = id
        self.seed_id = seed_id
        self.adjustment_type = adjustment_type
        self.amount_change = amount_change
        self.reason = reason
        self.adjusted_at = adjusted_at or datetime.now().isoformat()
