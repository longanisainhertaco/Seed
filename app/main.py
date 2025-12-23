from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import logging
import os
import shutil
import tempfile
from pathlib import Path


import pandas as pd
import json
from pydantic import ValidationError

from typing import Optional, List



from app.database import (
    init_database, get_all_seeds, get_seed_by_id, create_seed, update_seed, delete_seed,
    get_all_tasks, get_tasks_by_seed, update_task, delete_task,
    get_all_inventory, get_or_create_inventory, update_inventory,
    get_inventory_adjustments, create_inventory_adjustment
)
from app.models import Seed, Task, TaskStatus, TaskPriority, InventoryAdjustment
from app.services.import_service import import_seeds_from_excel
from app.services.task_service import auto_generate_tasks_for_seed, calculate_task_metrics
from app.logging_config import setup_logging
from app.config import (
    MAX_IMPORT_BYTES,
    ALLOWED_IMPORT_CONTENT_TYPES,
    ALLOWED_IMPORT_EXTENSIONS,
    DATA_DIR,
)
from app.schemas import SeedUpdate, InventoryUpdate

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Seed Library Task Tracker")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

init_database()
logger.info("Seed Library Task Tracker started")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = datetime.now()
    response = await call_next(request)
    duration_ms = (datetime.now() - start).total_seconds() * 1000
    logger.info(
        "%s %s -> %s (%.2f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": exc.status_code,
            "message": exc.detail,
        },
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error for %s %s", request.method, request.url.path)
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": 500,
            "message": "An unexpected error occurred. Please try again.",
        },
        status_code=500,
    )


def get_seed_category_counts(seeds: Optional[list] = None) -> dict:
    """Aggregate seed counts by category/type."""
    seed_records = seeds if seeds is not None else get_all_seeds()
    counts = {}

    for seed in seed_records:
        category = seed.get("type") or "Uncategorized"
        counts[category] = counts.get(category, 0) + 1

    return counts


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard with metrics and overview."""
    metrics = calculate_task_metrics()
    seeds = get_all_seeds()
    seeds_count = len(seeds)
    recent_tasks = get_all_tasks()[:10]
    category_counts = get_seed_category_counts(seeds)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "metrics": metrics,
        "seeds_count": seeds_count,
        "recent_tasks": recent_tasks,
        "category_counts_json": json.dumps(category_counts)
    })


@app.get("/seeds", response_class=HTMLResponse)
async def seeds_list(request: Request):
    """List all seeds."""
    seeds = get_all_seeds()
    return templates.TemplateResponse("seeds.html", {
        "request": request,
        "seeds": seeds
    })


@app.get("/seeds/{seed_id}", response_class=HTMLResponse)
async def seed_detail(request: Request, seed_id: int):
    """View seed details."""
    seed = get_seed_by_id(seed_id)
    if not seed:
        raise HTTPException(status_code=404, detail="Seed not found")

    tasks = get_tasks_by_seed(seed_id)
    inventory = get_or_create_inventory(seed_id)
    adjustments = get_inventory_adjustments(seed_id)

    return templates.TemplateResponse("seed_detail.html", {
        "request": request,
        "seed": seed,
        "tasks": tasks,
        "inventory": inventory,
        "adjustments": adjustments
    })


@app.post("/seeds/{seed_id}/update")
async def update_seed_post(
    request: Request,
    seed_id: int,
    name: str = Form(...),
    type: str = Form(...),
    packets_made: int = Form(0),
    seed_source: str = Form(""),
    date_ordered: Optional[str] = Form(None),
    date_finished: Optional[str] = Form(None),
    date_cataloged: Optional[str] = Form(None),
    date_ran_out: Optional[str] = Form(None),
    amount_text: str = Form("")
):
    """Update seed information."""
    try:
        payload = SeedUpdate(
            name=name,
            type=type,
            packets_made=packets_made,
            seed_source=seed_source,
            date_ordered=date_ordered,
            date_finished=date_finished,
            date_cataloged=date_cataloged,
            date_ran_out=date_ran_out,
            amount_text=amount_text,
        )
    except ValidationError as exc:
        seed = get_seed_by_id(seed_id)
        tasks = get_tasks_by_seed(seed_id)
        inventory = get_or_create_inventory(seed_id)
        adjustments = get_inventory_adjustments(seed_id)
        return templates.TemplateResponse(
            "seed_detail.html",
            {
                "request": request,
                "seed": seed,
                "tasks": tasks,
                "inventory": inventory,
                "adjustments": adjustments,
                "error_message": "Please correct the highlighted fields.",
                "validation_errors": exc.errors(),
            },
            status_code=400,
        )

    update_seed(seed_id, payload.model_dump(exclude_none=True))
    auto_generate_tasks_for_seed(seed_id)
    return RedirectResponse(url=f"/seeds/{seed_id}", status_code=303)


@app.post("/seeds/{seed_id}/delete")
async def delete_seed_post(seed_id: int):
    """Delete a seed."""
    delete_seed(seed_id)
    return RedirectResponse(url="/seeds", status_code=303)


@app.post("/print_labels", response_class=HTMLResponse)
async def print_labels(request: Request, seed_ids: Optional[List[int]] = Form(None)):
    """Render a print-friendly page for selected seed labels."""
    if not seed_ids:
        seeds = get_all_seeds()
        return templates.TemplateResponse("seeds.html", {
            "request": request,
            "seeds": seeds,
            "error_message": "Please select at least one seed to print."
        }, status_code=400)

    selected_seeds = []
    for seed_id in seed_ids:
        seed = get_seed_by_id(seed_id)
        if seed:
            selected_seeds.append(seed)

    if not selected_seeds:
        seeds = get_all_seeds()
        return templates.TemplateResponse("seeds.html", {
            "request": request,
            "seeds": seeds,
            "error_message": "No valid seeds found for printing."
        }, status_code=400)

    return templates.TemplateResponse("print_labels.html", {
        "request": request,
        "seeds": selected_seeds
    })


@app.get("/tasks", response_class=HTMLResponse)
async def tasks_list(request: Request, filter: Optional[str] = None, priority: Optional[str] = None):
    """List all tasks with optional filtering."""
    tasks = get_all_tasks()

    normalized_tasks = []
    for task in tasks:
        task['status'] = TaskStatus.normalize(task['status'])
        task['priority'] = task.get('priority') or TaskPriority.MEDIUM
        normalized_tasks.append(task)

    tasks = normalized_tasks

    if filter == "todo":
        tasks = [t for t in tasks if t['status'] == TaskStatus.TODO]
    elif filter == "in_progress":
        tasks = [t for t in tasks if t['status'] == TaskStatus.IN_PROGRESS]
    elif filter == "done":
        tasks = [t for t in tasks if t['status'] == TaskStatus.DONE]
    elif filter == "cancelled":
        tasks = [t for t in tasks if t['status'] == TaskStatus.CANCELLED]
    elif filter == "overdue":
        today = datetime.now().date()
        tasks = [t for t in tasks if t['status'] not in (TaskStatus.DONE, TaskStatus.CANCELLED) and t['due_date'] and
                datetime.fromisoformat(t['due_date']).date() < today]

    if priority in (TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH):
        tasks = [t for t in tasks if t.get('priority') == priority]

    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "tasks": tasks,
        "filter": filter,
        "priority_filter": priority
    })


@app.post("/tasks/{task_id}/update-status")
async def update_task_status(
    task_id: int,
    status: str = Form(...)
):
    """Update task status."""
    normalized_status = TaskStatus.normalize(status)
    updates = {'status': normalized_status}
    if normalized_status == TaskStatus.DONE:
        updates['completed_at'] = datetime.now().isoformat()
    elif normalized_status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED):
        updates['completed_at'] = None
    update_task(task_id, updates)
    return RedirectResponse(url="/tasks", status_code=303)


@app.post("/tasks/{task_id}/delete")
async def delete_task_post(task_id: int):
    """Delete a task."""
    delete_task(task_id)
    return RedirectResponse(url="/tasks", status_code=303)


@app.post("/tasks/bulk-update")
async def bulk_update_tasks(
    request: Request,
    task_ids: Optional[List[int]] = Form(None),
    status: Optional[str] = Form(None),
    priority: Optional[str] = Form(None),
    due_date: Optional[str] = Form(None)
):
    """Bulk update selected tasks for status/priority/due dates."""
    if not task_ids:
        tasks = get_all_tasks()
        normalized_tasks = []
        for task in tasks:
            task['status'] = TaskStatus.normalize(task['status'])
            task['priority'] = task.get('priority') or TaskPriority.MEDIUM
            normalized_tasks.append(task)
        return templates.TemplateResponse("tasks.html", {
            "request": request,
            "tasks": normalized_tasks,
            "filter": None,
            "priority_filter": None,
            "error_message": "Select at least one task to apply bulk changes."
        }, status_code=400)

    updates = {}
    if status:
        normalized_status = TaskStatus.normalize(status)
        updates['status'] = normalized_status
        if normalized_status == TaskStatus.DONE:
            updates['completed_at'] = datetime.now().isoformat()
        else:
            updates['completed_at'] = None
    if priority:
        updates['priority'] = priority
    if due_date:
        updates['due_date'] = due_date

    if not updates:
        return RedirectResponse(url="/tasks", status_code=303)

    for task_id in task_ids:
        update_task(task_id, updates)

    return RedirectResponse(url="/tasks", status_code=303)


@app.get("/import", response_class=HTMLResponse)
async def import_page(request: Request):
    """Import page."""
    return templates.TemplateResponse("import.html", {
        "request": request,
        "result": None,
        "columns": None,
        "file_path": None,
        "mapping_errors": None,
        "selected_mapping": {}
    })


@app.post("/import/upload", response_class=HTMLResponse)
async def import_upload(request: Request, file: UploadFile = File(...)):
    """Upload Excel file and read headers for mapping."""
    ext = Path(file.filename).suffix.lower()
    content_type = file.content_type or ""
    if ext not in ALLOWED_IMPORT_EXTENSIONS or (
        content_type and content_type not in ALLOWED_IMPORT_CONTENT_TYPES
    ):
        return templates.TemplateResponse("import.html", {
            "request": request,
            "result": {
                'success': False,
                'error': 'Please upload an Excel file (.xlsx or .xls).'
            },
            "columns": None,
            "file_path": None,
            "mapping_errors": None,
            "selected_mapping": {}
        }, status_code=400)

    temp_dir = Path(tempfile.mkdtemp(prefix="seed_import_", dir=DATA_DIR))
    file_path = temp_dir / Path(file.filename).name

    try:
        uploaded_size = 0
        with open(file_path, "wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                uploaded_size += len(chunk)
                if uploaded_size > MAX_IMPORT_BYTES:
                    raise ValueError(f"File exceeds limit of {MAX_IMPORT_BYTES // (1024 * 1024)} MB.")
                buffer.write(chunk)

        df = pd.read_excel(file_path, nrows=0)
        columns = [col.strip() for col in df.columns]

        return templates.TemplateResponse("import.html", {
            "request": request,
            "result": None,
            "columns": columns,
            "file_path": str(file_path),
            "mapping_errors": None,
            "selected_mapping": {}
        })

    except ValueError as exc:
        logger.warning("Import upload rejected: %s", exc)
        shutil.rmtree(temp_dir, ignore_errors=True)
        return templates.TemplateResponse("import.html", {
            "request": request,
            "result": {
                'success': False,
                'error': str(exc)
            },
            "columns": None,
            "file_path": None,
            "mapping_errors": None,
            "selected_mapping": {}
        }, status_code=400)
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return templates.TemplateResponse("import.html", {
            "request": request,
            "result": {
                'success': False,
                'error': 'Unable to read the uploaded file.'
            },
            "columns": None,
            "file_path": None,
            "mapping_errors": None,
            "selected_mapping": {}
        }, status_code=400)
    finally:
        file.file.close()


@app.post("/import/confirm", response_class=HTMLResponse)
async def import_confirm(
    request: Request,
    file_path: str = Form(...),
    type_column: Optional[str] = Form(None),
    name_column: Optional[str] = Form(None),
    packets_made_column: Optional[str] = Form(None),
    seed_source_column: Optional[str] = Form(None),
    date_ordered_column: Optional[str] = Form(None),
    date_finished_column: Optional[str] = Form(None),
    date_cataloged_column: Optional[str] = Form(None),
    date_ran_out_column: Optional[str] = Form(None),
    amount_text_column: Optional[str] = Form(None)
):
    """Confirm import with selected column mappings."""
    file_path_obj = Path(file_path).resolve()
    data_root = DATA_DIR.resolve()

    if not file_path_obj.exists() or not file_path_obj.is_file() or not file_path_obj.is_relative_to(data_root):
        return templates.TemplateResponse("import.html", {
            "request": request,
            "result": {
                'success': False,
                'error': 'Uploaded file could not be found. Please upload again.'
            },
            "columns": None,
            "file_path": None,
            "mapping_errors": None,
            "selected_mapping": {}
        })

    mapping = {
        'Type': type_column,
        'Name': name_column,
        'packets_made': packets_made_column,
        'seed_source': seed_source_column,
        'date_ordered': date_ordered_column,
        'date_finished': date_finished_column,
        'date_cataloged': date_cataloged_column,
        'date_ran_out': date_ran_out_column,
        'amount_text': amount_text_column
    }

    selected_mapping = {k: v for k, v in mapping.items() if v}

    try:
        result = import_seeds_from_excel(str(file_path_obj), mapping)

        if result.get('success'):
            for seed in get_all_seeds():
                auto_generate_tasks_for_seed(seed['id'])
            try:
                shutil.rmtree(file_path_obj.parent, ignore_errors=True)
            except OSError:
                logger.warning(f"Temporary file {file_path_obj} could not be removed.")

            return templates.TemplateResponse("import.html", {
                "request": request,
                "result": result,
                "columns": None,
                "file_path": None,
                "mapping_errors": None,
                "selected_mapping": {}
            })

        if result.get('mapping_errors'):
            df = pd.read_excel(file_path_obj, nrows=0)
            columns = [col.strip() for col in df.columns]

            return templates.TemplateResponse("import.html", {
                "request": request,
                "result": None,
                "columns": columns,
                "file_path": str(file_path_obj),
                "mapping_errors": result.get('mapping_errors', []),
                "selected_mapping": selected_mapping
            })

        try:
            shutil.rmtree(file_path_obj.parent, ignore_errors=True)
        except OSError:
            logger.warning(f"Temporary file {file_path_obj} could not be removed.")

        return templates.TemplateResponse("import.html", {
            "request": request,
            "result": result,
            "columns": None,
            "file_path": None,
            "mapping_errors": None,
            "selected_mapping": selected_mapping
        })

    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        shutil.rmtree(file_path_obj.parent, ignore_errors=True)
        return templates.TemplateResponse("import.html", {
            "request": request,
            "result": {
                'success': False,
                'error': str(e)
            },
            "columns": None,
            "file_path": None,
            "mapping_errors": None,
            "selected_mapping": selected_mapping
        })


@app.get("/inventory", response_class=HTMLResponse)
async def inventory_list(request: Request, filter: Optional[str] = None):
    """List inventory with optional filtering."""
    inventory_items = get_all_inventory()

    if filter == "buy_more":
        inventory_items = [i for i in inventory_items if i['buy_more']]
    elif filter == "extra":
        inventory_items = [i for i in inventory_items if i['extra']]

    return templates.TemplateResponse("inventory.html", {
        "request": request,
        "inventory_items": inventory_items,
        "filter": filter
    })


@app.post("/inventory/{seed_id}/update")
async def update_inventory_post(
    request: Request,
    seed_id: int,
    current_amount: str = Form(""),
    buy_more: bool = Form(False),
    extra: bool = Form(False),
    notes: str = Form("")
):
    """Update inventory."""
    inventory = get_or_create_inventory(seed_id)
    old_amount = inventory.get('current_amount', '')

    try:
        payload = InventoryUpdate(
            current_amount=current_amount,
            buy_more=buy_more,
            extra=extra,
            notes=notes,
        )
    except ValidationError as exc:
        seed = get_seed_by_id(seed_id)
        tasks = get_tasks_by_seed(seed_id)
        adjustments = get_inventory_adjustments(seed_id)
        return templates.TemplateResponse(
            "seed_detail.html",
            {
                "request": request,
                "seed": seed,
                "tasks": tasks,
                "inventory": inventory,
                "adjustments": adjustments,
                "error_message": "Inventory update failed validation.",
                "validation_errors": exc.errors(),
            },
            status_code=400,
        )

    update_inventory(seed_id, payload.model_dump())
    new_amount = payload.current_amount or ""

    if old_amount != new_amount:
        adjustment = InventoryAdjustment(
            seed_id=seed_id,
            adjustment_type='Manual Update',
            amount_change=f"From '{old_amount}' to '{new_amount}'",
            reason='Inventory update from UI'
        )
        create_inventory_adjustment(adjustment)

    return RedirectResponse(url=f"/seeds/{seed_id}", status_code=303)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
