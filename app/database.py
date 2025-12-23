import logging
import os
from contextlib import contextmanager
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker, joinedload

from app.config import DATABASE_PATH as CONFIGURED_DATABASE_PATH
from app.models import Base, Seed, Task, TaskStatus, Inventory, InventoryAdjustment

logger = logging.getLogger(__name__)

DATABASE_PATH = CONFIGURED_DATABASE_PATH

_engine = None
SessionLocal = None


def _create_engine():
    """Create a SQLAlchemy engine with SQLite settings."""
    global _engine, SessionLocal

    if _engine:
        _engine.dispose()

    engine = create_engine(
        f"sqlite:///{DATABASE_PATH}",
        connect_args={"check_same_thread": False},
        future=True,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    _engine = engine
    logger.info(f"Database engine created for {DATABASE_PATH}")
    return _engine


def get_engine():
    """Return the active engine, recreating it if needed."""
    global _engine
    if not _engine or str(_engine.url.database) != DATABASE_PATH:
        _engine = _create_engine()
    return _engine


@contextmanager
def get_session() -> Session:
    """Provide a transactional session scope."""
    engine = get_engine()
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def run_migrations():
    """Run Alembic migrations if configuration is present."""
    try:
        from alembic import command
        from alembic.config import Config

        config_path = Path(__file__).resolve().parents[1] / "alembic.ini"
        if not config_path.exists():
            logger.info("Alembic configuration not found; skipping migrations.")
            return

        alembic_cfg = Config(str(config_path))
        alembic_cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{DATABASE_PATH}")
        command.upgrade(alembic_cfg, "head")
        logger.info("Alembic migrations applied")
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Skipping migrations: %s", exc)


def init_database():
    """Initialize database tables using ORM metadata."""
    engine = get_engine()
    run_migrations()
    Base.metadata.create_all(bind=engine)
    _ensure_priority_column(engine)
    _ensure_indexes(engine)
    _migrate_task_status_labels(engine)
    logger.info("Database initialized successfully via ORM")


def _ensure_priority_column(engine):
    """Ensure priority column exists on tasks table for legacy databases."""
    with engine.begin() as conn:
        columns = [row[1] for row in conn.execute(text("PRAGMA table_info(tasks)")).fetchall()]
        if "priority" not in columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'Medium'"))
            logger.info("Added priority column to tasks table")


def _ensure_indexes(engine):
    """Create helpful indexes and constraints for existing databases."""
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tasks_seed_id ON tasks(seed_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tasks_due_date ON tasks(due_date)"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_seed_task_type ON tasks(seed_id, task_type)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_inventory_seed_id ON inventory(seed_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_inventory_adjustments_seed_id ON inventory_adjustments(seed_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_seeds_type ON seeds(type)"))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Index creation skipped: %s", exc)


def _migrate_task_status_labels(engine):
    """Normalize legacy task status values."""
    with engine.begin() as conn:
        conn.execute(text("UPDATE tasks SET status = 'To Do' WHERE status = 'Pending'"))


def _serialize_date(value: Optional[date]) -> Optional[str]:
    if not value:
        return None
    try:
        return value.isoformat()
    except AttributeError:
        return str(value)


def _serialize_datetime(value: Optional[datetime]) -> Optional[str]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    try:
        return datetime.fromisoformat(str(value)).isoformat()
    except (TypeError, ValueError):
        return str(value)


def _parse_date(value: Any) -> Optional[date]:
    if value in (None, "", b""):
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except (TypeError, ValueError):
        return None


def _parse_datetime(value: Any) -> Optional[datetime]:
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


def _prepare_seed_updates(updates: Dict[str, Any]) -> Dict[str, Any]:
    parsed = updates.copy()
    for key in ("date_ordered", "date_finished", "date_cataloged", "date_ran_out"):
        if key in parsed:
            parsed[key] = _parse_date(parsed[key])
    return parsed


def _prepare_task_updates(updates: Dict[str, Any]) -> Dict[str, Any]:
    parsed = updates.copy()
    if "due_date" in parsed:
        parsed["due_date"] = _parse_date(parsed["due_date"])
    if "completed_at" in parsed:
        parsed["completed_at"] = _parse_datetime(parsed["completed_at"])
    return parsed


def _prepare_inventory_updates(updates: Dict[str, Any]) -> Dict[str, Any]:
    return updates.copy()


def _seed_to_dict(seed: Seed) -> Dict[str, Any]:
    return {
        "id": seed.id,
        "type": seed.type,
        "name": seed.name,
        "packets_made": seed.packets_made,
        "seed_source": seed.seed_source,
        "date_ordered": _serialize_date(seed.date_ordered),
        "date_finished": _serialize_date(seed.date_finished),
        "date_cataloged": _serialize_date(seed.date_cataloged),
        "date_ran_out": _serialize_date(seed.date_ran_out),
        "amount_text": seed.amount_text,
        "created_at": _serialize_datetime(seed.created_at),
        "updated_at": _serialize_datetime(seed.updated_at),
    }


def _task_to_dict(task: Task, seed: Optional[Seed] = None) -> Dict[str, Any]:
    task_dict = {
        "id": task.id,
        "seed_id": task.seed_id,
        "task_type": task.task_type,
        "status": TaskStatus.normalize(task.status),
        "priority": getattr(task, "priority", None) or "Medium",
        "due_date": _serialize_date(task.due_date),
        "completed_at": _serialize_datetime(task.completed_at),
        "description": task.description,
        "created_at": _serialize_datetime(task.created_at),
        "updated_at": _serialize_datetime(task.updated_at),
    }
    if seed:
        task_dict["seed_name"] = seed.name
        task_dict["seed_type"] = seed.type
    return task_dict


def _inventory_to_dict(inventory: Inventory, seed: Optional[Seed] = None) -> Dict[str, Any]:
    inventory_dict = {
        "id": inventory.id,
        "seed_id": inventory.seed_id,
        "current_amount": inventory.current_amount,
        "buy_more": bool(inventory.buy_more),
        "extra": bool(inventory.extra),
        "notes": inventory.notes,
        "last_updated": _serialize_datetime(inventory.last_updated),
    }
    if seed:
        inventory_dict["seed_name"] = seed.name
        inventory_dict["seed_type"] = seed.type
    return inventory_dict


def _adjustment_to_dict(adjustment: InventoryAdjustment, seed: Optional[Seed] = None) -> Dict[str, Any]:
    adjustment_dict = {
        "id": adjustment.id,
        "seed_id": adjustment.seed_id,
        "adjustment_type": adjustment.adjustment_type,
        "amount_change": adjustment.amount_change,
        "reason": adjustment.reason,
        "adjusted_at": _serialize_datetime(adjustment.adjusted_at),
    }
    if seed:
        adjustment_dict["seed_name"] = seed.name
    return adjustment_dict


def create_seed(seed: Seed) -> int:
    """Create a new seed record."""
    with get_session() as session:
        new_seed = Seed(
            type=seed.type,
            name=seed.name,
            packets_made=seed.packets_made,
            seed_source=seed.seed_source,
            date_ordered=_parse_date(seed.date_ordered),
            date_finished=_parse_date(seed.date_finished),
            date_cataloged=_parse_date(seed.date_cataloged),
            date_ran_out=_parse_date(seed.date_ran_out),
            amount_text=seed.amount_text,
            created_at=_parse_datetime(seed.created_at) or datetime.now(),
            updated_at=_parse_datetime(seed.updated_at) or datetime.now(),
        )
        session.add(new_seed)
        session.flush()
        seed_id = new_seed.id
        logger.info(f"Created seed with ID: {seed_id}")
        return seed_id


def get_all_seeds() -> List[Dict[str, Any]]:
    """Retrieve all seeds ordered by creation date descending."""
    with get_session() as session:
        seeds = session.query(Seed).order_by(Seed.created_at.desc()).all()
        return [_seed_to_dict(seed) for seed in seeds]


def get_seed_by_id(seed_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a seed by ID."""
    with get_session() as session:
        seed = session.get(Seed, seed_id)
        return _seed_to_dict(seed) if seed else None


def update_seed(seed_id: int, updates: Dict[str, Any]) -> bool:
    """Update a seed record."""
    if not updates:
        return False

    with get_session() as session:
        seed = session.get(Seed, seed_id)
        if not seed:
            return False

        parsed_updates = _prepare_seed_updates(updates)
        parsed_updates["updated_at"] = datetime.now()
        for key, value in parsed_updates.items():
            setattr(seed, key, value)
        session.flush()
        logger.info(f"Updated seed {seed_id}")
        return True


def delete_seed(seed_id: int) -> bool:
    """Delete a seed record along with cascading relations."""
    with get_session() as session:
        seed = session.get(Seed, seed_id)
        if not seed:
            return False
        session.delete(seed)
        logger.info(f"Deleted seed {seed_id}")
        return True


def create_task(task: Task) -> int:
    """Create a new task."""
    with get_session() as session:
        new_task = Task(
            seed_id=task.seed_id,
            task_type=task.task_type,
            status=task.status,
            priority=getattr(task, "priority", None) or "Medium",
            due_date=_parse_date(task.due_date),
            completed_at=_parse_datetime(task.completed_at),
            description=task.description,
            created_at=_parse_datetime(task.created_at) or datetime.now(),
            updated_at=_parse_datetime(task.updated_at) or datetime.now(),
        )
        session.add(new_task)
        session.flush()
        task_id = new_task.id
        logger.info(f"Created task with ID: {task_id}")
        return task_id


def get_all_tasks() -> List[Dict[str, Any]]:
    """Retrieve all tasks with seed information ordered by creation date."""
    with get_session() as session:
        results = (
            session.query(Task, Seed)
            .outerjoin(Seed, Task.seed_id == Seed.id)
            .order_by(Task.created_at.desc())
            .all()
        )
        return [_task_to_dict(task, seed) for task, seed in results]


def get_tasks_by_seed(seed_id: int) -> List[Dict[str, Any]]:
    """Retrieve all tasks for a specific seed."""
    with get_session() as session:
        tasks = (
            session.query(Task)
            .filter(Task.seed_id == seed_id)
            .order_by(Task.created_at.desc())
            .all()
        )
        return [_task_to_dict(task) for task in tasks]


def update_task(task_id: int, updates: Dict[str, Any]) -> bool:
    """Update a task."""
    if not updates:
        return False

    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            return False

        parsed_updates = _prepare_task_updates(updates)
        parsed_updates["updated_at"] = datetime.now()
        for key, value in parsed_updates.items():
            setattr(task, key, value)
        session.flush()
        logger.info(f"Updated task {task_id}")
        return True


def delete_task(task_id: int) -> bool:
    """Delete a task."""
    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            return False
        session.delete(task)
        logger.info(f"Deleted task {task_id}")
        return True


def get_or_create_inventory(seed_id: int) -> Dict[str, Any]:
    """Get or create inventory record for a seed."""
    with get_session() as session:
        inventory = (
            session.query(Inventory)
            .options(joinedload(Inventory.seed))
            .filter(Inventory.seed_id == seed_id)
            .one_or_none()
        )

        if inventory:
            return _inventory_to_dict(inventory, inventory.seed)

        inventory = Inventory(
            seed_id=seed_id,
            current_amount="",
            buy_more=False,
            extra=False,
            notes="",
            last_updated=datetime.now(),
        )
        session.add(inventory)
        session.flush()
        session.refresh(inventory)
        return _inventory_to_dict(inventory, inventory.seed)


def update_inventory(seed_id: int, updates: Dict[str, Any]) -> bool:
    """Update inventory record."""
    if not updates:
        return False

    with get_session() as session:
        inventory = session.query(Inventory).filter(Inventory.seed_id == seed_id).one_or_none()
        if not inventory:
            return False

        parsed_updates = _prepare_inventory_updates(updates)
        parsed_updates["last_updated"] = datetime.now()
        for key, value in parsed_updates.items():
            setattr(inventory, key, value)
        session.flush()
        logger.info(f"Updated inventory for seed {seed_id}")
        return True


def get_all_inventory() -> List[Dict[str, Any]]:
    """Retrieve all inventory records with seed information ordered by seed name."""
    with get_session() as session:
        inventory_items = (
            session.query(Inventory, Seed)
            .outerjoin(Seed, Inventory.seed_id == Seed.id)
            .order_by(Seed.name)
            .all()
        )
        return [_inventory_to_dict(inventory, seed) for inventory, seed in inventory_items]


def create_inventory_adjustment(adjustment: InventoryAdjustment) -> int:
    """Create an inventory adjustment record."""
    with get_session() as session:
        new_adjustment = InventoryAdjustment(
            seed_id=adjustment.seed_id,
            adjustment_type=adjustment.adjustment_type,
            amount_change=adjustment.amount_change,
            reason=adjustment.reason,
            adjusted_at=_parse_datetime(adjustment.adjusted_at) or datetime.now(),
        )
        session.add(new_adjustment)
        session.flush()
        adjustment_id = new_adjustment.id
        logger.info(f"Created inventory adjustment with ID: {adjustment_id}")
        return adjustment_id


def get_inventory_adjustments(seed_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve inventory adjustments, optionally filtered by seed."""
    with get_session() as session:
        query = (
            session.query(InventoryAdjustment, Seed)
            .outerjoin(Seed, InventoryAdjustment.seed_id == Seed.id)
            .order_by(InventoryAdjustment.adjusted_at.desc())
        )

        if seed_id:
            query = query.filter(InventoryAdjustment.seed_id == seed_id)

        adjustments = query.all()
        return [_adjustment_to_dict(adj, seed) for adj, seed in adjustments]
