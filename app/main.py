from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import logging
import os
import shutil
import json
from typing import Optional

from app.database import (
    init_database, get_all_seeds, get_seed_by_id, create_seed, update_seed, delete_seed,
    get_all_tasks, get_tasks_by_seed, update_task, delete_task,
    get_all_inventory, get_or_create_inventory, update_inventory,
    get_inventory_adjustments, create_inventory_adjustment
)
from app.models import Seed, Task, TaskStatus, InventoryAdjustment
from app.services.import_service import import_seeds_from_excel
from app.services.task_service import auto_generate_tasks_for_seed, calculate_task_metrics
from app.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Seed Library Task Tracker")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

init_database()
logger.info("Seed Library Task Tracker started")


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
    updates = {
        'name': name,
        'type': type,
        'packets_made': packets_made,
        'seed_source': seed_source,
        'date_ordered': date_ordered if date_ordered else None,
        'date_finished': date_finished if date_finished else None,
        'date_cataloged': date_cataloged if date_cataloged else None,
        'date_ran_out': date_ran_out if date_ran_out else None,
        'amount_text': amount_text
    }
    update_seed(seed_id, updates)
    auto_generate_tasks_for_seed(seed_id)
    return RedirectResponse(url=f"/seeds/{seed_id}", status_code=303)


@app.post("/seeds/{seed_id}/delete")
async def delete_seed_post(seed_id: int):
    """Delete a seed."""
    delete_seed(seed_id)
    return RedirectResponse(url="/seeds", status_code=303)


@app.get("/tasks", response_class=HTMLResponse)
async def tasks_list(request: Request, filter: Optional[str] = None):
    """List all tasks with optional filtering."""
    tasks = get_all_tasks()

    if filter == "pending":
        tasks = [t for t in tasks if t['status'] == TaskStatus.PENDING]
    elif filter == "in_progress":
        tasks = [t for t in tasks if t['status'] == TaskStatus.IN_PROGRESS]
    elif filter == "done":
        tasks = [t for t in tasks if t['status'] == TaskStatus.DONE]
    elif filter == "overdue":
        today = datetime.now().date()
        tasks = [t for t in tasks if t['status'] != TaskStatus.DONE and t['due_date'] and
                datetime.fromisoformat(t['due_date']).date() < today]

    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "tasks": tasks,
        "filter": filter
    })


@app.post("/tasks/{task_id}/update-status")
async def update_task_status(
    task_id: int,
    status: str = Form(...)
):
    """Update task status."""
    updates = {'status': status}
    if status == TaskStatus.DONE:
        updates['completed_at'] = datetime.now().isoformat()
    update_task(task_id, updates)
    return RedirectResponse(url="/tasks", status_code=303)


@app.post("/tasks/{task_id}/delete")
async def delete_task_post(task_id: int):
    """Delete a task."""
    delete_task(task_id)
    return RedirectResponse(url="/tasks", status_code=303)


@app.get("/import", response_class=HTMLResponse)
async def import_page(request: Request):
    """Import page."""
    return templates.TemplateResponse("import.html", {
        "request": request,
        "result": None
    })


@app.post("/import", response_class=HTMLResponse)
async def import_excel(request: Request, file: UploadFile = File(...)):
    """Import seeds from Excel file."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        return templates.TemplateResponse("import.html", {
            "request": request,
            "result": {
                'success': False,
                'error': 'Please upload an Excel file (.xlsx or .xls)'
            }
        })

    os.makedirs("data", exist_ok=True)
    file_path = f"data/{file.filename}"

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = import_seeds_from_excel(file_path)

        for seed in get_all_seeds():
            auto_generate_tasks_for_seed(seed['id'])

        return templates.TemplateResponse("import.html", {
            "request": request,
            "result": result
        })

    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        return templates.TemplateResponse("import.html", {
            "request": request,
            "result": {
                'success': False,
                'error': str(e)
            }
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
    seed_id: int,
    current_amount: str = Form(""),
    buy_more: bool = Form(False),
    extra: bool = Form(False),
    notes: str = Form("")
):
    """Update inventory."""
    inventory = get_or_create_inventory(seed_id)
    old_amount = inventory.get('current_amount', '')

    updates = {
        'current_amount': current_amount,
        'buy_more': buy_more,
        'extra': extra,
        'notes': notes
    }
    update_inventory(seed_id, updates)

    if old_amount != current_amount:
        adjustment = InventoryAdjustment(
            seed_id=seed_id,
            adjustment_type='Manual Update',
            amount_change=f"From '{old_amount}' to '{current_amount}'",
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
