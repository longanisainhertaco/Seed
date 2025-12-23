# 🌱 Seed Library Task Tracker

A comprehensive Windows desktop application for managing seed libraries with automated task generation, inventory tracking, and metrics dashboard.

## Features

- **FastAPI Backend with Jinja2 UI** - Local web interface running on 127.0.0.1:8000
- **SQLite Database** - Lightweight, single-file database storage
- **Excel Import** - Import seed data from .xlsx files with automatic field mapping
- **Auto-Generated Tasks** - Automatically creates Pack, Catalog, and Reorder tasks based on seed dates
- **Task Management** - Track task status (Pending, In Progress, Done) with due dates
- **Metrics Dashboard** - Real-time metrics showing total/done/overdue/due-today/in-progress tasks with completion percentages
- **Inventory Management** - Track current amounts with BuyMore and Extra flags
- **Inventory Adjustments** - Complete history of inventory changes
- **Logging** - Comprehensive logging to file and console
- **PyInstaller Build** - Single executable for Windows distribution

## Project Structure

```
Seed/
├── app/
│   ├── models.py              # Data models (Seed, Task, Inventory, etc.)
│   ├── database.py            # SQLite database operations
│   ├── logging_config.py      # Logging configuration
│   ├── main.py                # FastAPI application
│   ├── services/
│   │   ├── import_service.py  # Excel import functionality
│   │   └── task_service.py    # Task generation and metrics
│   ├── templates/             # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── seeds.html
│   │   ├── seed_detail.html
│   │   ├── tasks.html
│   │   ├── inventory.html
│   │   └── import.html
│   └── static/
│       └── css/
│           └── style.css      # Application styling
├── tests/
│   ├── test_models.py         # Model tests
│   ├── test_database.py       # Database operation tests
│   └── test_task_service.py   # Service logic tests
├── data/                      # Excel import files location
├── requirements.txt           # Python dependencies
├── build_windows.ps1          # Windows build script
└── README.md                  # This file

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Windows 10 or later

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/longanisainhertaco/Seed.git
   cd Seed
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app/main.py
   ```

5. **Open browser**
   Navigate to http://127.0.0.1:8000

## Building Windows Executable

Run the PowerShell build script:

```powershell
.\build_windows.ps1
```

This will:
- Create a virtual environment (if needed)
- Install all dependencies
- Build a standalone executable using PyInstaller
- Create `dist/SeedLibraryTaskTracker.exe`

The executable can be distributed and run without Python installation.

## Usage

### Importing Seeds from Excel

1. Navigate to the **Import** page
2. Upload an Excel file (.xlsx or .xls) with these columns:
   - `Type` - Seed type (e.g., Vegetable, Herb, Flower)
   - `Name` - Seed name
   - `packets_made` - Number of packets created
   - `seed_source` - Where the seeds came from
   - `date_ordered` - Date ordered (optional)
   - `date_finished` - Date packaging finished (optional)
   - `date_cataloged` - Date cataloged (optional)
   - `date_ran_out` - Date ran out of stock (optional)
   - `amount_text` - Text description of amount

3. Click **Import** - tasks will be auto-generated based on the seed data

### Task Auto-Generation Rules

- **Pack Task**: Created if `date_finished` is empty (due in 7 days)
- **Catalog Task**: Created if `date_finished` exists but `date_cataloged` is empty (due in 3 days)
- **Reorder Task**: Created if `date_ran_out` exists (due in 5 days)

### Managing Tasks

- View all tasks on the **Tasks** page
- Filter by: All, Pending, In Progress, Done, Overdue
- Update task status with dropdown menus
- Tasks automatically mark completion date when set to Done

### Inventory Management

- View inventory on the **Inventory** page
- Update current amounts for each seed
- Toggle **BuyMore** flag for low stock items
- Toggle **Extra** flag for surplus items
- Add notes for each inventory item
- All changes are tracked in adjustment history

### Dashboard Metrics

The dashboard displays:
- **Total Tasks** - All tasks in the system
- **Done** - Completed tasks
- **In Progress** - Tasks being worked on
- **Overdue** - Tasks past their due date
- **Due Today** - Tasks due today
- **Completion %** - Percentage of completed tasks

## Testing

Run the test suite:

```bash
python -m unittest discover tests
```

Individual test files:
```bash
python -m unittest tests.test_models
python -m unittest tests.test_database
python -m unittest tests.test_task_service
```

## Logging

Logs are written to:
- Console (stdout) - INFO level
- File: `seed_library_YYYYMMDD.log` - INFO level

Log format includes timestamp, module name, level, and message.

## Database Schema

### Seeds Table
- id, type, name, packets_made, seed_source
- date_ordered, date_finished, date_cataloged, date_ran_out
- amount_text, created_at, updated_at

### Tasks Table
- id, seed_id, task_type, status, due_date
- completed_at, description, created_at, updated_at

### Inventory Table
- id, seed_id, current_amount, buy_more, extra
- notes, last_updated

### Inventory Adjustments Table
- id, seed_id, adjustment_type, amount_change
- reason, adjusted_at

## Technologies Used

- **FastAPI** - Modern web framework
- **Jinja2** - Template engine
- **SQLite** - Embedded database
- **Pandas** - Excel file processing
- **OpenPyXL** - Excel file reading
- **Uvicorn** - ASGI server
- **PyInstaller** - Executable builder

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please visit:
https://github.com/longanisainhertaco/Seed
