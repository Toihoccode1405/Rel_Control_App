# kRel - Reliability Test Management System

## Project Overview
Ứng dụng quản lý quy trình kiểm tra độ tin cậy (Reliability Test) cho nhà máy sản xuất.

- **Tech Stack**: Python 3.11+, PyQt6, SQL Server, Pandas
- **Architecture**: MVC Pattern với separation of concerns
- **UI Framework**: PyQt6 với modern Material Design styles

## Project Structure

```
kRel/
├── main.py                    # Entry point
├── config.ini                 # Config (encrypted DB credentials)
├── assets/
│   └── images/               # All images (.png, .ico)
├── src/
│   ├── config.py             # App constants, column definitions
│   ├── styles.py             # UI styles (CSS-like)
│   │
│   ├── controllers/          # Business logic (MVC Controller)
│   │   ├── request_controller.py   # CRUD requests
│   │   └── csv_handler.py          # Import/Export CSV
│   │
│   ├── models/               # Data models
│   │   ├── equipment.py
│   │   ├── request.py
│   │   └── user.py
│   │
│   ├── services/             # Core services
│   │   ├── auth.py           # Authentication
│   │   ├── database.py       # SQL Server connection (singleton)
│   │   ├── data_event_bus.py # Event bus for cross-tab updates
│   │   ├── encryption.py     # Config encryption (Fernet)
│   │   ├── logger.py         # Logging + audit
│   │   ├── lookup_service.py # Lookup data caching
│   │   ├── request_service.py
│   │   └── validator.py      # Form validation
│   │
│   ├── views/                # UI Views (MVC View)
│   │   ├── main_window.py    # Main window container
│   │   ├── login_dialog.py
│   │   ├── register_dialog.py
│   │   │
│   │   ├── input_tab/        # Package - Data entry tab
│   │   │   ├── input_tab.py
│   │   │   ├── form_builder.py
│   │   │   └── table_section.py
│   │   │
│   │   ├── edit_tab/         # Package - Data editing tab
│   │   │   ├── edit_tab.py
│   │   │   ├── delegates.py
│   │   │   └── frozen_table.py
│   │   │
│   │   ├── report_tab/       # Package - Reports & Gantt
│   │   │   ├── report_tab.py
│   │   │   └── gantt_renderer.py
│   │   │
│   │   └── settings_tab/     # Package - System settings
│   │       ├── settings_tab.py
│   │       ├── config_page.py
│   │       ├── users_page.py
│   │       ├── general_page.py
│   │       ├── equipment_page.py
│   │       └── csv_dialog.py
│   │
│   ├── widgets/              # Reusable widgets
│   │   ├── delegates.py
│   │   ├── frozen_table.py
│   │   ├── gantt_chart.py
│   │   ├── loading_overlay.py
│   │   └── validated_field.py
│   │
│   └── utils/                # Utility functions
│       ├── date_utils.py
│       └── file_utils.py
│
├── csv/                      # Sample CSV data
├── tests/                    # Unit tests
└── Logfile/                  # Log storage
```

## Coding Conventions

### File Size Limits
- **Maximum 400 lines per file** - Tách thành modules nhỏ nếu vượt quá
- Mỗi class nên có single responsibility

### Naming Conventions
- **Files**: snake_case (e.g., `request_controller.py`)
- **Classes**: PascalCase (e.g., `RequestController`)
- **Functions/Methods**: snake_case (e.g., `_load_data()`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_LOG_PATH`)
- **Private**: prefix với `_` (e.g., `_setup_ui()`)

### Import Order
1. Standard library
2. Third-party packages (PyQt6, pandas)
3. Local imports (src.*)

### Docstrings
- Sử dụng triple quotes cho module và class docstrings
- Viết tiếng Việt hoặc Anh tùy context

## Key Patterns

### Singleton Services
```python
# Sử dụng get_* functions để lấy singleton
from src.services.database import get_db
from src.services.auth import get_auth
```

### Event Bus Pattern
```python
# Cross-tab communication
from src.services.data_event_bus import get_event_bus
get_event_bus().emit_request_created(request_no)
```

### Tab Packages
Mỗi tab lớn được tổ chức thành package:
```
tab_name/
├── __init__.py      # Export main class
├── tab_name.py      # Main tab class
├── sub_component.py # Sub-components
└── helpers.py       # Helper classes
```

## Database

### Tables
- `users` - User accounts
- `requests` - Test requests (main table)
- `equipment` - Equipment/chambers
- `factory`, `project`, `phase`, `category`, `status` - Lookup tables

### Connection
- SQL Server via pyodbc
- Credentials encrypted in config.ini using Fernet

## UI Guidelines

### Styles
- Định nghĩa trong `src/styles.py`
- Sử dụng Material Design colors
- Primary color: #1565C0

### Icons
- Sử dụng emoji cho quick icons: 📊 📁 🔧 💾
- Store images in `assets/images/`

## Build & Deploy

```bash
# Development
python main.py

# Build executable
build.bat
```

## Testing

```bash
# Run tests
python -m pytest tests/
```

