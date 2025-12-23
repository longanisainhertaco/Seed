import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
from app.models import Seed, Task, Inventory, InventoryAdjustment, TaskStatus

logger = logging.getLogger(__name__)

DATABASE_PATH = "seed_library.db"


def get_db_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            packets_made INTEGER DEFAULT 0,
            seed_source TEXT,
            date_ordered TEXT,
            date_finished TEXT,
            date_cataloged TEXT,
            date_ran_out TEXT,
            amount_text TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seed_id INTEGER NOT NULL,
            task_type TEXT NOT NULL,
            status TEXT NOT NULL,
            due_date TEXT,
            completed_at TEXT,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (seed_id) REFERENCES seeds (id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seed_id INTEGER NOT NULL UNIQUE,
            current_amount TEXT,
            buy_more BOOLEAN DEFAULT 0,
            extra BOOLEAN DEFAULT 0,
            notes TEXT,
            last_updated TEXT NOT NULL,
            FOREIGN KEY (seed_id) REFERENCES seeds (id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_adjustments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seed_id INTEGER NOT NULL,
            adjustment_type TEXT NOT NULL,
            amount_change TEXT,
            reason TEXT,
            adjusted_at TEXT NOT NULL,
            FOREIGN KEY (seed_id) REFERENCES seeds (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


def create_seed(seed: Seed) -> int:
    """Create a new seed record."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO seeds (
            type, name, packets_made, seed_source,
            date_ordered, date_finished, date_cataloged, date_ran_out,
            amount_text, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        seed.type, seed.name, seed.packets_made, seed.seed_source,
        seed.date_ordered, seed.date_finished, seed.date_cataloged,
        seed.date_ran_out, seed.amount_text, seed.created_at, seed.updated_at
    ))

    seed_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logger.info(f"Created seed with ID: {seed_id}")
    return seed_id


def get_all_seeds() -> List[Dict[str, Any]]:
    """Retrieve all seeds."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM seeds ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_seed_by_id(seed_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a seed by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM seeds WHERE id = ?", (seed_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_seed(seed_id: int, updates: Dict[str, Any]) -> bool:
    """Update a seed record."""
    if not updates:
        return False

    updates['updated_at'] = datetime.now().isoformat()
    set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
    values = list(updates.values()) + [seed_id]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE seeds SET {set_clause} WHERE id = ?", values)
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    logger.info(f"Updated seed {seed_id}, affected rows: {affected}")
    return affected > 0


def delete_seed(seed_id: int) -> bool:
    """Delete a seed record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM seeds WHERE id = ?", (seed_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    logger.info(f"Deleted seed {seed_id}, affected rows: {affected}")
    return affected > 0


def create_task(task: Task) -> int:
    """Create a new task."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tasks (
            seed_id, task_type, status, due_date, completed_at,
            description, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        task.seed_id, task.task_type, task.status, task.due_date,
        task.completed_at, task.description, task.created_at, task.updated_at
    ))

    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logger.info(f"Created task with ID: {task_id}")
    return task_id


def get_all_tasks() -> List[Dict[str, Any]]:
    """Retrieve all tasks with seed information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.*, s.name as seed_name, s.type as seed_type
        FROM tasks t
        LEFT JOIN seeds s ON t.seed_id = s.id
        ORDER BY t.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_tasks_by_seed(seed_id: int) -> List[Dict[str, Any]]:
    """Retrieve all tasks for a specific seed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE seed_id = ? ORDER BY created_at DESC", (seed_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_task(task_id: int, updates: Dict[str, Any]) -> bool:
    """Update a task."""
    if not updates:
        return False

    updates['updated_at'] = datetime.now().isoformat()
    set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
    values = list(updates.values()) + [task_id]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    logger.info(f"Updated task {task_id}, affected rows: {affected}")
    return affected > 0


def delete_task(task_id: int) -> bool:
    """Delete a task."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    logger.info(f"Deleted task {task_id}, affected rows: {affected}")
    return affected > 0


def get_or_create_inventory(seed_id: int) -> Dict[str, Any]:
    """Get or create inventory record for a seed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE seed_id = ?", (seed_id,))
    row = cursor.fetchone()

    if row:
        conn.close()
        return dict(row)

    cursor.execute("""
        INSERT INTO inventory (seed_id, current_amount, buy_more, extra, notes, last_updated)
        VALUES (?, '', 0, 0, '', ?)
    """, (seed_id, datetime.now().isoformat()))

    inventory_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM inventory WHERE id = ?", (inventory_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}


def update_inventory(seed_id: int, updates: Dict[str, Any]) -> bool:
    """Update inventory record."""
    if not updates:
        return False

    updates['last_updated'] = datetime.now().isoformat()
    set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
    values = list(updates.values()) + [seed_id]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE inventory SET {set_clause} WHERE seed_id = ?", values)
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    logger.info(f"Updated inventory for seed {seed_id}, affected rows: {affected}")
    return affected > 0


def get_all_inventory() -> List[Dict[str, Any]]:
    """Retrieve all inventory records with seed information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.*, s.name as seed_name, s.type as seed_type
        FROM inventory i
        LEFT JOIN seeds s ON i.seed_id = s.id
        ORDER BY s.name
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_inventory_adjustment(adjustment: InventoryAdjustment) -> int:
    """Create an inventory adjustment record."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO inventory_adjustments (
            seed_id, adjustment_type, amount_change, reason, adjusted_at
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        adjustment.seed_id, adjustment.adjustment_type,
        adjustment.amount_change, adjustment.reason, adjustment.adjusted_at
    ))

    adjustment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logger.info(f"Created inventory adjustment with ID: {adjustment_id}")
    return adjustment_id


def get_inventory_adjustments(seed_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve inventory adjustments, optionally filtered by seed."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if seed_id:
        cursor.execute("""
            SELECT ia.*, s.name as seed_name
            FROM inventory_adjustments ia
            LEFT JOIN seeds s ON ia.seed_id = s.id
            WHERE ia.seed_id = ?
            ORDER BY ia.adjusted_at DESC
        """, (seed_id,))
    else:
        cursor.execute("""
            SELECT ia.*, s.name as seed_name
            FROM inventory_adjustments ia
            LEFT JOIN seeds s ON ia.seed_id = s.id
            ORDER BY ia.adjusted_at DESC
        """)

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
