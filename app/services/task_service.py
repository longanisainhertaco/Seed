from datetime import datetime, timedelta, date
from typing import List, Dict, Any
import logging
from app.models import Task, TaskType, TaskStatus
from app.database import create_task, get_tasks_by_seed, get_seed_by_id

logger = logging.getLogger(__name__)


def auto_generate_tasks_for_seed(seed_id: int) -> List[int]:
    """Auto-generate Pack, Catalog, and Reorder tasks for a seed."""
    seed = get_seed_by_id(seed_id)
    if not seed:
        logger.warning(f"Seed {seed_id} not found, cannot generate tasks")
        return []

    existing_tasks = get_tasks_by_seed(seed_id)
    existing_task_types = {task['task_type'] for task in existing_tasks if task['status'] != TaskStatus.DONE}

    task_ids = []
    today = datetime.now().date()

    if TaskType.PACK not in existing_task_types and not seed.get('date_finished'):
        pack_task = Task(
            seed_id=seed_id,
            task_type=TaskType.PACK,
            status=TaskStatus.PENDING,
            due_date=(today + timedelta(days=7)).isoformat(),
            description=f"Pack {seed.get('name', 'seed')} into packets"
        )
        task_id = create_task(pack_task)
        task_ids.append(task_id)
        logger.info(f"Created Pack task {task_id} for seed {seed_id}")

    if TaskType.CATALOG not in existing_task_types and seed.get('date_finished') and not seed.get('date_cataloged'):
        catalog_task = Task(
            seed_id=seed_id,
            task_type=TaskType.CATALOG,
            status=TaskStatus.PENDING,
            due_date=(today + timedelta(days=3)).isoformat(),
            description=f"Catalog {seed.get('name', 'seed')} in the system"
        )
        task_id = create_task(catalog_task)
        task_ids.append(task_id)
        logger.info(f"Created Catalog task {task_id} for seed {seed_id}")

    if TaskType.REORDER not in existing_task_types and seed.get('date_ran_out'):
        reorder_task = Task(
            seed_id=seed_id,
            task_type=TaskType.REORDER,
            status=TaskStatus.PENDING,
            due_date=(today + timedelta(days=5)).isoformat(),
            description=f"Reorder {seed.get('name', 'seed')} from {seed.get('seed_source', 'supplier')}"
        )
        task_id = create_task(reorder_task)
        task_ids.append(task_id)
        logger.info(f"Created Reorder task {task_id} for seed {seed_id}")

    return task_ids


def calculate_task_metrics() -> Dict[str, Any]:
    """Calculate task metrics for dashboard."""
    from app.database import get_all_tasks

    tasks = get_all_tasks()
    today = datetime.now().date()

    total = len(tasks)
    done = sum(1 for t in tasks if t['status'] == TaskStatus.DONE)
    in_progress = sum(1 for t in tasks if t['status'] == TaskStatus.IN_PROGRESS)
    pending = sum(1 for t in tasks if t['status'] == TaskStatus.PENDING)

    overdue = 0
    due_today = 0

    for task in tasks:
        if task['status'] != TaskStatus.DONE and task['due_date']:
            try:
                due_date = datetime.fromisoformat(task['due_date']).date()
                if due_date < today:
                    overdue += 1
                elif due_date == today:
                    due_today += 1
            except (ValueError, TypeError):
                pass

    completion_percentage = round((done / total * 100) if total > 0 else 0, 1)

    return {
        'total': total,
        'done': done,
        'in_progress': in_progress,
        'pending': pending,
        'overdue': overdue,
        'due_today': due_today,
        'completion_percentage': completion_percentage
    }
