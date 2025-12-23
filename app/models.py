from datetime import datetime, date
from typing import Optional
from enum import Enum


class TaskType(str, Enum):
    PACK = "Pack"
    CATALOG = "Catalog"
    REORDER = "Reorder"


class TaskStatus(str, Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    DONE = "Done"


class Seed:
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


class Task:
    def __init__(
        self,
        id: Optional[int] = None,
        seed_id: int = 0,
        task_type: str = TaskType.PACK,
        status: str = TaskStatus.PENDING,
        due_date: Optional[str] = None,
        completed_at: Optional[str] = None,
        description: str = "",
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        self.id = id
        self.seed_id = seed_id
        self.task_type = task_type
        self.status = status
        self.due_date = due_date
        self.completed_at = completed_at
        self.description = description
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()


class Inventory:
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


class InventoryAdjustment:
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
