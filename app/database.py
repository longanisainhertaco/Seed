import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker, joinedload

from app.models import Base, Seed, Task, Inventory, InventoryAdjustment

logger = logging.getLogger(__name__)

DATABASE_PATH = "seed_library.db"

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


def init_database():
    """Initialize database tables using ORM metadata."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully via ORM")


def _seed_to_dict(seed: Seed) -> Dict[str, Any]:
    return {
        "id": seed.id,
        "type": seed.type,
        "name": seed.name,
        "packets_made": seed.packets_made,
        "seed_source": seed.seed_source,
        "date_ordered": seed.date_ordered,
        "date_finished": seed.date_finished,
        "date_cataloged": seed.date_cataloged,
        "date_ran_out": seed.date_ran_out,
        "amount_text": seed.amount_text,
        "created_at": seed.created_at,
        "updated_at": seed.updated_at,
    }


def _task_to_dict(task: Task, seed: Optional[Seed] = None) -> Dict[str, Any]:
    task_dict = {
        "id": task.id,
        "seed_id": task.seed_id,
        "task_type": task.task_type,
        "status": task.status,
        "due_date": task.due_date,
        "completed_at": task.completed_at,
        "description": task.description,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
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
        "last_updated": inventory.last_updated,
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
        "adjusted_at": adjustment.adjusted_at,
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
            date_ordered=seed.date_ordered,
            date_finished=seed.date_finished,
            date_cataloged=seed.date_cataloged,
            date_ran_out=seed.date_ran_out,
            amount_text=seed.amount_text,
            created_at=seed.created_at or datetime.now().isoformat(),
            updated_at=seed.updated_at or datetime.now().isoformat(),
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

        updates["updated_at"] = datetime.now().isoformat()
        for key, value in updates.items():
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
            due_date=task.due_date,
            completed_at=task.completed_at,
            description=task.description,
            created_at=task.created_at or datetime.now().isoformat(),
            updated_at=task.updated_at or datetime.now().isoformat(),
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

        updates["updated_at"] = datetime.now().isoformat()
        for key, value in updates.items():
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
            last_updated=datetime.now().isoformat(),
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

        updates["last_updated"] = datetime.now().isoformat()
        for key, value in updates.items():
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
            adjusted_at=adjustment.adjusted_at or datetime.now().isoformat(),
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
