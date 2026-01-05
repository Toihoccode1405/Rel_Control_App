"""
kRel - Input Tab
Data entry form for new test requests
"""
import os
import shutil
from datetime import datetime

import pandas as pd

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QDateTimeEdit, QPushButton,
    QTableView, QFrame, QFileDialog, QMessageBox, QStyle,
    QHeaderView, QScrollArea
)
from PyQt6.QtCore import Qt, QDateTime, QDate
from PyQt6.QtGui import QStandardItemModel, QStandardItem

from src.config import TEST_PAIRS, FINAL_RESULTS
from src.styles import (
    INPUT_TAB_STYLE, TABLE_STYLE, BTN_STYLE_GREEN_SOLID,
    BTN_STYLE_BLUE, RESULT_FIELD_STYLE, TOOLBAR_FRAME_STYLE
)
from src.services.database import get_db
from src.services.lookup_service import get_lookup_service
from src.services.request_service import get_request_service
from src.services.logger import get_logger, log_audit
from src.services.validator import FormValidator
from src.services.data_event_bus import get_event_bus
from src.widgets.validated_field import ValidatedField

# Module logger
logger = get_logger("input_tab")


class InputTab(QWidget):
    """Data entry tab for new test requests"""

    # Field definitions
    TOP_FIELDS = [
        ("Mã Yêu cầu", "request_no"), ("Ngày yêu cầu", "request_date"),
        ("Người yêu cầu", "requester"), ("Nhà máy", "factory"),
        ("Dự án", "project"), ("Giai đoạn", "phase"),
        ("Hạng mục", "category"), ("Mã Thiết bị", "equip_no"),
        ("Tên Thiết bị", "equip_name"), ("Số lượng", "qty"),
        ("Điều kiện test", "test_condition")
    ]

    BOTTOM_FIELDS = [("KQ Cuối", "final_res"), ("Trạng thái", "status")]
    COMBO_FIELDS = ["factory", "project", "phase", "category", "equip_no", "status"]

    # Fields that require validation
    REQUIRED_FIELDS = ["request_no", "requester", "factory", "project"]
    VALIDATED_FIELDS = ["request_no", "requester", "factory", "project", "qty"]

    def __init__(self, log_path: str, user_info: dict, parent=None):
        super().__init__(parent)
        self.log_path = log_path
        self.user_info = user_info
        self.widgets = {}  # Store all input widgets
        self.validated_fields = {}  # Store ValidatedField wrappers

        self.db = get_db()
        self.lookup_service = get_lookup_service()
        self.request_service = get_request_service()

        os.makedirs(self.log_path, exist_ok=True)

        self.setStyleSheet(INPUT_TAB_STYLE)
        self._setup_ui()
        self._setup_validation()
        self._connect_events()

        # Initialize request code
        self._update_request_code(QDate.currentDate())
        self._load_recent_requests()

    def _connect_events(self):
        """Connect to DataEventBus events for realtime updates"""
        event_bus = get_event_bus()

        # Listen for lookup data changes (factory, project, phase, category, status)
        event_bus.lookup_changed.connect(self._on_lookup_changed)

        # Listen for equipment changes
        event_bus.equipment_changed.connect(self._on_equipment_data_changed)

        # Listen for request updates (to refresh recent list)
        event_bus.request_updated.connect(self._on_request_updated)

        logger.debug("InputTab connected to DataEventBus")

    def _on_lookup_changed(self, table_name: str):
        """Handle lookup data changes - reload affected combo boxes"""
        # Map table names to widget field names
        table_to_field = {
            "factory": "factory",
            "project": "project",
            "phase": "phase",
            "category": "category",
            "status": "status"
        }

        field_name = table_to_field.get(table_name)
        if field_name and field_name in self.widgets:
            widget = self.widgets[field_name]
            if isinstance(widget, QComboBox):
                current_text = widget.currentText()
                self._load_combo(widget, field_name)
                # Try to restore previous selection
                idx = widget.findText(current_text)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
                logger.debug(f"Reloaded combo: {field_name}")

    def _on_equipment_data_changed(self):
        """Handle equipment data changes - reload equipment combo"""
        if "equip_no" in self.widgets:
            widget = self.widgets["equip_no"]
            if isinstance(widget, QComboBox):
                current_text = widget.currentText()
                self._load_combo(widget, "equip_no")
                idx = widget.findText(current_text)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
                logger.debug("Reloaded equipment combo")

    def _on_request_updated(self, request_no: str = None):
        """Handle request updates - refresh recent requests table"""
        self._load_recent_requests()
        logger.debug(f"Refreshed recent requests after update: {request_no}")

    def _setup_validation(self):
        """Setup form validation rules"""
        self.form_validator = FormValidator(self.validated_fields)

        # Required fields
        self.form_validator.required("request_no")
        self.form_validator.required("requester")
        self.form_validator.required("factory")
        self.form_validator.required("project")

        # Pattern validation
        self.form_validator.pattern(
            "request_no",
            r"^\d{8}-\d{3}$",
            "Định dạng: YYYYMMDD-SSS"
        )

        # Numeric validation
        self.form_validator.numeric("qty")
    
    def _setup_ui(self):
        """Setup UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(10, 8, 10, 8)

        # Input grid
        self._setup_input_grid(main_layout)

        # Bottom section (schedule, notes, save button)
        self._setup_bottom_section(main_layout)

        # Recent requests section - Toolbar Frame (like Theo dõi thiết bị)
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet(TOOLBAR_FRAME_STYLE)

        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(8)

        # Title
        table_header = QLabel("<b style='color: #1565C0;'>📋 Danh sách yêu cầu:</b>")
        toolbar_layout.addWidget(table_header)

        # Filter combo
        toolbar_layout.addWidget(QLabel("📅"))
        self.cb_recent_filter = QComboBox()
        self.cb_recent_filter.addItems(["Hôm nay", "7 ngày", "30 ngày", "Tất cả"])
        self.cb_recent_filter.setCurrentIndex(1)
        self.cb_recent_filter.setMinimumWidth(90)
        self.cb_recent_filter.setStyleSheet(self._combo_style())
        self.cb_recent_filter.currentIndexChanged.connect(lambda _: self._load_recent_requests())
        toolbar_layout.addWidget(self.cb_recent_filter)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet("background-color: #CFD8DC; max-width: 1px;")
        sep1.setFixedWidth(1)
        toolbar_layout.addWidget(sep1)

        # Search section
        toolbar_layout.addWidget(QLabel("<b style='color: #1565C0;'>🔍 Tìm:</b>"))

        self.cb_search_field = QComboBox()
        self.cb_search_field.addItems([
            "Tất cả", "Mã YC", "Người YC", "Nhà Máy", "Dự Án",
            "Mã TB", "Tên TB", "Trạng Thái", "DRI"
        ])
        self.cb_search_field.setMinimumWidth(80)
        self.cb_search_field.setStyleSheet(self._combo_style())
        toolbar_layout.addWidget(self.cb_search_field)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Nhập từ khóa...")
        self.txt_search.setMinimumWidth(120)
        self.txt_search.setStyleSheet(self._input_style())
        self.txt_search.textChanged.connect(self._on_search)
        self.txt_search.returnPressed.connect(self._load_recent_requests)
        toolbar_layout.addWidget(self.txt_search)

        btn_search = QPushButton("🔍 Tìm")
        btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search.setStyleSheet(BTN_STYLE_BLUE)
        btn_search.clicked.connect(self._load_recent_requests)
        toolbar_layout.addWidget(btn_search)

        toolbar_layout.addStretch()

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("background-color: #CFD8DC; max-width: 1px;")
        sep2.setFixedWidth(1)
        toolbar_layout.addWidget(sep2)

        # Import/Export buttons
        btn_template = QPushButton("📄 Mẫu")
        btn_template.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_template.setStyleSheet(BTN_STYLE_BLUE)
        btn_template.clicked.connect(self._download_template)
        toolbar_layout.addWidget(btn_template)

        btn_import = QPushButton("📥 Nhập")
        btn_import.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_import.setStyleSheet(BTN_STYLE_BLUE)
        btn_import.clicked.connect(self._import_csv)
        toolbar_layout.addWidget(btn_import)

        btn_export = QPushButton("📤 Xuất")
        btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export.setStyleSheet(BTN_STYLE_BLUE)
        btn_export.clicked.connect(self._export_csv)
        toolbar_layout.addWidget(btn_export)

        main_layout.addWidget(toolbar_frame)

        self.table = QTableView()
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.setMinimumHeight(280)
        main_layout.addWidget(self.table, stretch=2)

    def _combo_style(self):
        """Combo box style like report tab"""
        return """
            QComboBox {
                border: 1px solid #CFD8DC;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: #FFFFFF;
                min-height: 24px;
                font-size: 11px;
            }
            QComboBox:hover { border-color: #90CAF9; }
            QComboBox:focus { border: 1.5px solid #1565C0; }
        """

    def _input_style(self):
        """Input style like report tab"""
        return """
            QLineEdit {
                border: 1px solid #CFD8DC;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: #FFFFFF;
                min-height: 24px;
                font-size: 11px;
            }
            QLineEdit:hover { border-color: #90CAF9; }
            QLineEdit:focus { border: 1.5px solid #1565C0; }
        """

    def _on_search(self, text):
        """Handle search text change - filter table locally"""
        if not text.strip():
            # If empty, reload from DB
            self._load_recent_requests()
            return

        # Filter current model
        model = self.table.model()
        if not model:
            return

        search_text = text.strip().lower()
        search_field_idx = self.cb_search_field.currentIndex()

        # Map combo index to column index
        field_to_col = {
            0: None,  # Tất cả
            1: 0,     # Mã YC
            2: 2,     # Người YC
            3: 3,     # Nhà Máy
            4: 4,     # Dự Án
            5: 6,     # Mã TB
            6: 7,     # Tên TB
            7: 13,    # Trạng Thái
            8: 14     # DRI
        }

        target_col = field_to_col.get(search_field_idx)

        # Show/hide rows based on search
        for row in range(model.rowCount()):
            match = False

            if target_col is None:
                # Search all columns
                for col in range(model.columnCount()):
                    item = model.item(row, col)
                    if item and search_text in item.text().lower():
                        match = True
                        break
            else:
                # Search specific column
                item = model.item(row, target_col)
                if item and search_text in item.text().lower():
                    match = True

            self.table.setRowHidden(row, not match)

    def _setup_input_grid(self, parent_layout):
        """Setup main input grid"""
        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setVerticalSpacing(3)
        grid.setContentsMargins(0, 0, 0, 0)

        MAX_COLS = 4
        row, col = 0, 0

        # Top fields
        for label, field in self.TOP_FIELDS:
            self._create_field(grid, label, field, row, col)
            col += 1
            if col >= MAX_COLS:
                col, row = 0, row + 1

        # Separator with label
        if col > 0:
            row += 1

        sep_frame = QFrame()
        sep_frame.setStyleSheet("background-color: #1565C0; border-radius: 1px;")
        sep_frame.setFixedHeight(2)
        grid.addWidget(sep_frame, row, 0, 1, 8)
        row += 1

        # Test section header
        test_label = QLabel("<b style='color: #1565C0; font-size: 12px;'>📊 Kết Quả Test</b>")
        test_label.setStyleSheet("background-color: #E3F2FD; padding: 3px 8px; border-radius: 3px;")
        grid.addWidget(test_label, row, 0, 1, 8)
        row += 1

        # Test pairs - input row
        for i, (inp_key, _, lbl_inp, _) in enumerate(TEST_PAIRS):
            self._create_field(grid, lbl_inp, inp_key, row, i)
        row += 1

        # Test pairs - result row
        for i, (_, res_key, _, lbl_res) in enumerate(TEST_PAIRS):
            self._create_field(grid, lbl_res, res_key, row, i, is_result=True)
        row += 1

        # Bottom fields
        col = 0
        for label, field in self.BOTTOM_FIELDS:
            self._create_field(grid, label, field, row, col)
            col += 1

        # Set column stretches
        for i in range(MAX_COLS):
            grid.setColumnStretch(i * 2 + 1, 1)

        parent_layout.addLayout(grid)

        # Setup auto-fill for test results
        for inp_key, res_key, _, _ in TEST_PAIRS:
            self._setup_auto_result(inp_key, res_key)

    def _create_field(self, grid, label_text, field_name, row, col, is_result=False):
        """Create a form field with label"""
        # Label - add * for required fields
        is_required = field_name in self.REQUIRED_FIELDS
        label_suffix = " *" if is_required else ""
        lbl = QLabel(f"{label_text}{label_suffix}:")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if is_result:
            lbl.setStyleSheet("font-weight: 600; color: #E65100;")
        elif is_required:
            lbl.setStyleSheet("font-weight: 600; color: #1565C0;")
        else:
            lbl.setStyleSheet("font-weight: 500; color: #424242;")
        grid.addWidget(lbl, row, col * 2)

        # Widget
        input_widget = self._create_input_widget(field_name, is_result)

        # Wrap with ValidatedField if it's a validated field
        if field_name in self.VALIDATED_FIELDS:
            validated = ValidatedField(input_widget, field_name, label_text)
            self.widgets[field_name] = input_widget  # Store actual widget
            self.validated_fields[field_name] = validated  # Store wrapper
            grid.addWidget(validated, row, col * 2 + 1)
        else:
            self.widgets[field_name] = input_widget
            grid.addWidget(input_widget, row, col * 2 + 1)
    
    def _create_input_widget(self, field_name, is_result=False):
        """Create appropriate input widget based on field name"""
        widget = None

        if field_name == "request_no":
            widget = QLineEdit()
            widget.setPlaceholderText("yyyymmdd-sss")

        elif field_name == "request_date":
            widget = QDateTimeEdit()
            widget.setCalendarPopup(True)
            widget.setDisplayFormat("yyyy-MM-dd")
            widget.setDateTime(QDateTime.currentDateTime())
            widget.dateChanged.connect(self._update_request_code)

        elif field_name == "equip_no":
            widget = QComboBox()
            widget.setEditable(True)
            self._load_combo(widget, field_name)
            widget.currentTextChanged.connect(self._on_equipment_change)

        elif field_name == "equip_name":
            widget = QLineEdit()
            widget.setReadOnly(True)
            widget.setPlaceholderText("Tự động điền...")
            widget.setStyleSheet("""
                background-color: #ECEFF1;
                color: #607D8B;
                border: 1px solid #CFD8DC;
                border-radius: 4px;
            """)

        elif field_name == "final_res":
            widget = QComboBox()
            widget.addItems(FINAL_RESULTS)

        elif field_name == "test_condition":
            widget = QComboBox()
            widget.setEditable(True)
            widget.setPlaceholderText("Chọn điều kiện...")

        elif field_name in self.COMBO_FIELDS:
            widget = QComboBox()
            widget.setEditable(True)
            self._load_combo(widget, field_name)

        else:
            widget = QLineEdit()

        if is_result:
            widget.setStyleSheet("""
                background-color: #FFFDE7;
                border: 1px solid #FFF59D;
                border-radius: 4px;
                font-weight: 500;
            """)

        return widget

    def _setup_bottom_section(self, parent_layout):
        """Setup bottom section with schedule, notes, and save button"""
        bot_layout = QHBoxLayout()
        bot_layout.setSpacing(8)

        # Schedule group
        grp_date = QGroupBox("📅 Tiến độ")
        dg = QGridLayout(grp_date)
        dg.setSpacing(4)
        dg.setContentsMargins(8, 10, 8, 6)

        schedule_fields = [
            ("Vào KH", "plan_start", 0, 0),
            ("Ra KH", "plan_end", 0, 1),
            ("Vào TT", "actual_start", 1, 0),
            ("Ra TT", "actual_end", 1, 1)
        ]

        for title, key, dr, dc in schedule_fields:
            lbl = QLabel(title + ":")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet("font-weight: 500; color: #424242; font-size: 11px;")
            dg.addWidget(lbl, dr, dc * 2)

            dt = QDateTimeEdit()
            dt.setCalendarPopup(True)
            dt.setDisplayFormat("yyyy-MM-dd HH:mm")
            dt.setDateTime(QDateTime.currentDateTime())
            dg.addWidget(dt, dr, dc * 2 + 1)
            self.widgets[key] = dt

        bot_layout.addWidget(grp_date, stretch=3)

        # Notes group
        grp_note = QGroupBox("📝 Thông tin")
        gn = QGridLayout(grp_note)
        gn.setSpacing(4)
        gn.setContentsMargins(8, 10, 8, 6)

        # Log file row
        log_lbl = QLabel("Log:")
        log_lbl.setStyleSheet("font-weight: 500; color: #424242; font-size: 11px;")
        gn.addWidget(log_lbl, 0, 0)

        lw = QWidget()
        lh = QHBoxLayout(lw)
        lh.setContentsMargins(0, 0, 0, 0)
        lh.setSpacing(4)

        self.log_label = QLabel("Chưa chọn file...")
        self.log_label.setStyleSheet("color: #9E9E9E; font-style: italic; font-size: 11px;")

        btn_log = QPushButton("📁 Chọn")
        btn_log.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_log.setFixedWidth(90)
        btn_log.setFixedHeight(35)
        btn_log.setStyleSheet(BTN_STYLE_BLUE)
        btn_log.clicked.connect(self._pick_log_file)

        lh.addWidget(self.log_label, stretch=1)
        lh.addWidget(btn_log)
        gn.addWidget(lw, 0, 1)
        self.widgets["logfile"] = self.log_label

        # Note row
        note_lbl = QLabel("Note:")
        note_lbl.setStyleSheet("font-weight: 500; color: #424242;")
        gn.addWidget(note_lbl, 1, 0)

        self.widgets["note"] = QLineEdit()
        self.widgets["note"].setPlaceholderText("Nhập ghi chú...")
        gn.addWidget(self.widgets["note"], 1, 1)

        # Hidden log_link
        self.widgets["log_link"] = QLineEdit()

        # DRI row
        dri_lbl = QLabel("DRI:")
        dri_lbl.setStyleSheet("font-weight: 500; color: #424242;")
        gn.addWidget(dri_lbl, 2, 0)

        dri_txt = QLineEdit(self.user_info.get('name', ''))
        dri_txt.setReadOnly(True)
        dri_txt.setStyleSheet("""
            background-color: #ECEFF1;
            color: #607D8B;
            border: 1px solid #CFD8DC;
            border-radius: 4px;
        """)
        gn.addWidget(dri_txt, 2, 1)

        bot_layout.addWidget(grp_note, stretch=4)

        # Save button section
        btn_layout = QVBoxLayout()
        btn_layout.setContentsMargins(0, 16, 0, 0)
        btn_layout.setSpacing(8)

        btn_save = QPushButton("  💾 LƯU DỮ LIỆU")
        btn_save.setFixedHeight(50)
        btn_save.setMinimumWidth(120)
        btn_save.setStyleSheet(BTN_STYLE_GREEN_SOLID)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        btn_save.clicked.connect(self._save)
        btn_layout.addWidget(btn_save)
        btn_layout.addStretch()

        bot_layout.addLayout(btn_layout, stretch=1)
        parent_layout.addLayout(bot_layout)

    def _setup_auto_result(self, src_key, dest_key):
        """Setup auto-fill for test results"""
        if src_key not in self.widgets or dest_key not in self.widgets:
            return

        src_widget = self.widgets[src_key]
        dest_widget = self.widgets[dest_key]

        def update_text(text):
            val = text.strip()
            if val:
                dest_widget.setText(f"xxF/{val}T")
            else:
                dest_widget.clear()

        if isinstance(src_widget, QLineEdit):
            src_widget.textChanged.connect(update_text)
        elif isinstance(src_widget, QComboBox):
            src_widget.currentTextChanged.connect(update_text)

    def _update_request_code(self, date):
        """Update request code based on date"""
        dt = datetime(date.year(), date.month(), date.day())
        code = self.request_service.generate_request_code(dt)
        self.widgets["request_no"].setText(code)

    def _on_equipment_change(self, text):
        """Handle equipment selection change"""
        equip = self.lookup_service.get_equipment_by_id(text)
        if equip:
            self.widgets["equip_name"].setText(equip.name)
            cb = self.widgets["test_condition"]
            cb.clear()
            cb.addItems(equip.get_recipes())

    def _load_combo(self, combo, field_name):
        """Load combo box items from database"""
        combo.clear()
        combo.addItem("")

        try:
            if field_name == "equip_no":
                items = self.lookup_service.get_equipment_list()
            else:
                table_map = {
                    "factory": "factory", "project": "project",
                    "phase": "phase", "category": "category", "status": "status"
                }
                table = table_map.get(field_name)
                if table:
                    items = self.lookup_service.get_lookup_values(table)
                else:
                    items = []

            for item in items:
                if item:
                    combo.addItem(item)
        except Exception:
            pass

    def _pick_log_file(self):
        """Pick log file"""
        filepath, _ = QFileDialog.getOpenFileName(self, "Chọn File Log")
        if filepath:
            filename = os.path.basename(filepath)
            self.log_label.setText(filename[:15] + "..." if len(filename) > 15 else filename)
            self.log_label.setToolTip(filename)
            self.log_label.path = filepath

            req_no = self.widgets["request_no"].text().strip() or "Unknown"
            self.widgets["log_link"].setText(os.path.join(self.log_path, req_no, filename))

    def _save(self):
        """Save the request"""
        try:
            # Clear previous errors
            self.form_validator.clear_all_errors()

            # Inline validation first
            if not self.form_validator.validate_all():
                logger.debug("Validation failed - inline errors shown")
                return

            # Collect values
            values = self._collect_form_values()
            request_no = values.get("request_no", "Unknown")
            requester = values.get("requester", "")

            logger.debug(f"Saving request: {request_no}")

            # Build INSERT query
            columns = list(values.keys())
            placeholders = ", ".join(["?"] * len(columns))
            cols_str = ", ".join(columns)

            db = get_db()
            with db.get_cursor() as cursor:
                cursor.execute(
                    f"INSERT INTO requests ({cols_str}) VALUES ({placeholders})",
                    list(values.values())
                )

            # Copy log file if selected
            if hasattr(self.log_label, 'path'):
                dest_dir = os.path.join(
                    self.log_path,
                    self.widgets["request_no"].text().strip() or "Unknown"
                )
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copy(self.log_label.path, dest_dir)
                logger.debug(f"Log file copied to {dest_dir}")

            logger.info(f"Request saved: {request_no} by {requester}")
            log_audit("REQUEST_CREATE", user=requester, details=f"Code: {request_no}")

            # Emit event for other tabs to refresh
            get_event_bus().emit_request_created(request_no)

            QMessageBox.information(self, "Thành công", "Đã lưu!")
            self._clear_form()
            self._load_recent_requests()

        except Exception as e:
            logger.error(f"Failed to save request: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Lỗi", str(e))

    def _collect_form_values(self) -> dict:
        """Collect all form values into a dictionary"""
        values = {}

        def get_value(key):
            if key not in self.widgets:
                return ""
            w = self.widgets[key]
            if key == "logfile":
                return os.path.basename(getattr(w, 'path', ''))
            elif key == "request_date":
                return w.dateTime().toString("yyyy-MM-dd")
            elif isinstance(w, QDateTimeEdit):
                return w.dateTime().toString("yyyy-MM-dd HH:mm")
            elif isinstance(w, QComboBox):
                return w.currentText()
            elif isinstance(w, QLabel):
                return os.path.basename(getattr(w, 'path', ''))
            else:
                return w.text()

        # Main fields
        for _, key in self.TOP_FIELDS + self.BOTTOM_FIELDS:
            values[key] = get_value(key)

        # Test pairs
        for inp_key, res_key, _, _ in TEST_PAIRS:
            values[inp_key] = get_value(inp_key)
            values[res_key] = get_value(res_key)

        # Additional fields
        values["log_link"] = get_value("log_link")
        values["note"] = get_value("note")
        values["plan_start"] = get_value("plan_start")
        values["plan_end"] = get_value("plan_end")
        values["actual_start"] = get_value("actual_start")
        values["actual_end"] = get_value("actual_end")
        values["dri"] = self.user_info.get('name', '')

        return values

    def _clear_form(self):
        """Clear form for new entry"""
        self._update_request_code(QDate.currentDate())

        self.log_label.setText("...")
        if hasattr(self.log_label, 'path'):
            delattr(self.log_label, 'path')

        if "log_link" in self.widgets:
            self.widgets["log_link"].clear()

        for key in ["plan_start", "plan_end", "actual_start", "actual_end"]:
            self.widgets[key].setDateTime(QDateTime.currentDateTime())

        exclude = ["request_no", "request_date", "plan_start", "plan_end",
                   "actual_start", "actual_end", "logfile", "log_link", "dri"]

        for key, widget in self.widgets.items():
            if key not in exclude:
                if isinstance(widget, QLineEdit):
                    widget.clear()
                elif isinstance(widget, QComboBox):
                    widget.setCurrentIndex(0)

    def _load_recent_requests(self):
        """Load recent requests into table based on filter"""
        try:
            db = get_db()

            # Get filter selection
            filter_idx = 1  # Default: 7 days
            if hasattr(self, 'cb_recent_filter'):
                filter_idx = self.cb_recent_filter.currentIndex()

            # Build date condition based on filter
            today = QDate.currentDate()

            if filter_idx == 0:  # Hôm nay
                date_str = today.toString("yyyy-MM-dd")
                condition = "request_date LIKE ?"
                params = (f"{date_str}%",)
            elif filter_idx == 1:  # 7 ngày
                start_date = today.addDays(-7).toString("yyyy-MM-dd")
                condition = "request_date >= ?"
                params = (start_date,)
            elif filter_idx == 2:  # 30 ngày
                start_date = today.addDays(-30).toString("yyyy-MM-dd")
                condition = "request_date >= ?"
                params = (start_date,)
            else:  # Tất cả
                condition = "1=1"
                params = None  # Use None instead of empty tuple

            query = f"""
                SELECT request_no, request_date, requester, factory, project, phase,
                       equip_no, equip_name, test_condition,
                       plan_start, plan_end, actual_start, actual_end,
                       status, dri, final_res
                FROM requests WHERE {condition} ORDER BY id DESC
            """

            logger.debug(f"Loading recent requests with filter {filter_idx}, condition: {condition}")
            rows = db.fetch_all(query, params)
            logger.debug(f"Query returned {len(rows)} rows")

            headers = [
                "Mã YC", "Ngày YC", "Người YC", "Nhà Máy", "Dự Án", "Giai Đoạn",
                "Mã TB", "Tên TB", "ĐK Test", "Vào KH", "Ra KH", "Vào TT", "Ra TT",
                "Trạng Thái", "DRI", "KQ Cuối"
            ]

            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(headers)

            for row in rows:
                items = [QStandardItem(str(v) if v else "") for v in row]
                model.appendRow(items)

            self.table.setModel(model)

            header = self.table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)

            logger.debug(f"Loaded {len(rows)} recent requests (filter: {filter_idx})")

        except Exception as e:
            logger.error(f"Failed to load recent requests: {e}", exc_info=True)

    # ==========================================================================
    # CSV Import/Export
    # ==========================================================================

    # CSV column headers mapping
    CSV_HEADERS = [
        "request_no", "request_date", "requester", "factory", "project", "phase",
        "category", "equip_no", "equip_name", "qty", "test_condition",
        "cos", "cos_res", "hcross", "xhatch_res", "xcross", "xsection_res",
        "func_test", "func_res", "final_res", "status",
        "plan_start", "plan_end", "actual_start", "actual_end", "note", "dri"
    ]

    CSV_HEADERS_VI = [
        "Mã YC", "Ngày YC", "Người YC", "Nhà Máy", "Dự Án", "Giai Đoạn",
        "Hạng Mục", "Mã TB", "Tên TB", "Số Lượng", "ĐK Test",
        "CoS", "KQ CoS", "HCross", "KQ XHatch", "XCross", "KQ XSection",
        "Func Test", "KQ Func", "KQ Cuối", "Trạng Thái",
        "Vào KH", "Ra KH", "Vào TT", "Ra TT", "Ghi Chú", "DRI"
    ]

    def _download_template(self):
        """Download CSV template file"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Lưu File Mẫu", "Template_NhapLieu.csv", "CSV (*.csv)"
        )
        if not path:
            return

        try:
            # Create template with headers and sample row
            df = pd.DataFrame(columns=self.CSV_HEADERS_VI)

            # Add sample row
            today = datetime.now().strftime("%Y-%m-%d")
            sample = {
                "Mã YC": "(Tự động)",
                "Ngày YC": today,
                "Người YC": "Tên người yêu cầu",
                "Nhà Máy": "F1/F2/F3...",
                "Dự Án": "Tên dự án",
                "Giai Đoạn": "EVT/DVT/PVT/MP",
                "Hạng Mục": "Hạng mục test",
                "Mã TB": "Mã thiết bị",
                "Tên TB": "Tên thiết bị",
                "Số Lượng": "1",
                "ĐK Test": "Điều kiện test",
                "CoS": "", "KQ CoS": "",
                "HCross": "", "KQ XHatch": "",
                "XCross": "", "KQ XSection": "",
                "Func Test": "", "KQ Func": "",
                "KQ Cuối": "Pass/Fail/Pending",
                "Trạng Thái": "New/In Progress/Done",
                "Vào KH": "2026-01-15 08:00", "Ra KH": "2026-01-20 17:00",
                "Vào TT": "", "Ra TT": "",
                "Ghi Chú": "Ghi chú thêm",
                "DRI": "Người phụ trách"
            }
            df = pd.concat([df, pd.DataFrame([sample])], ignore_index=True)

            df.to_csv(path, index=False, encoding='utf-8-sig')

            QMessageBox.information(
                self, "Thành công",
                f"Đã tải file mẫu!\n\nHướng dẫn:\n"
                f"1. Mở file bằng Excel\n"
                f"2. Xóa dòng mẫu, nhập dữ liệu mới\n"
                f"3. Cột 'Mã YC' để trống - hệ thống tự sinh\n"
                f"4. Lưu file và dùng 'Nhập CSV' để import\n\n"
                f"Lưu ý format:\n"
                f"• Ngày YC: YYYY-MM-DD (VD: 2026-01-15)\n"
                f"• Vào/Ra KH/TT: YYYY-MM-DD HH:MM (VD: 2026-01-15 08:00)"
            )
            logger.info(f"Template downloaded: {path}")

        except Exception as e:
            logger.error(f"Failed to download template: {e}")
            QMessageBox.critical(self, "Lỗi", str(e))

    def _import_csv(self):
        """Import requests from CSV file"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn File CSV", "", "CSV (*.csv)"
        )
        if not path:
            return

        try:
            # Try different encodings
            df = None
            for encoding in ['utf-8-sig', 'utf-8', 'cp1252', 'latin1']:
                try:
                    df = pd.read_csv(path, encoding=encoding)
                    if not df.empty:
                        break
                except Exception:
                    continue

            if df is None or df.empty:
                return QMessageBox.warning(self, "Lỗi", "Không thể đọc file CSV hoặc file trống!")

            total_rows = len(df)
            logger.debug(f"CSV read: {total_rows} rows, columns: {list(df.columns)}")

            # Map Vietnamese headers to English (case-insensitive, strip spaces)
            header_map = {k.strip().lower(): v for k, v in zip(self.CSV_HEADERS_VI, self.CSV_HEADERS)}
            new_columns = []
            for c in df.columns:
                c_clean = str(c).strip().lower()
                new_columns.append(header_map.get(c_clean, c))
            df.columns = new_columns

            logger.debug(f"Mapped columns: {list(df.columns)}")

            # Validate required columns (request_no is optional - will auto-generate)
            required = ["requester", "factory", "project"]
            missing = [c for c in required if c not in df.columns]
            if missing:
                # Show available columns for debugging
                available = ", ".join(str(c) for c in df.columns[:10])
                return QMessageBox.warning(
                    self, "Lỗi Format",
                    f"Thiếu cột bắt buộc: {', '.join(missing)}\n\n"
                    f"Các cột trong file: {available}...\n\n"
                    f"Vui lòng dùng file mẫu (Tải Mẫu) để đảm bảo đúng format."
                )

            # Import rows
            db = get_db()
            imported = 0
            skipped = 0
            errors = []
            skip_reasons = []

            with db.get_cursor() as cursor:
                for idx, row in df.iterrows():
                    try:
                        # Check if this is a sample row
                        req_no_raw = str(row.get("request_no", "")).strip()
                        if req_no_raw.upper() in ["YYYYMMDD-001", "YYYYMMDD-XXX"]:
                            skipped += 1
                            skip_reasons.append(f"Dòng {idx + 2}: Dòng mẫu")
                            continue

                        # Check required fields have values
                        requester = str(row.get("requester", "")).strip()
                        factory = str(row.get("factory", "")).strip()
                        project = str(row.get("project", "")).strip()

                        if not requester or not factory or not project:
                            skipped += 1
                            missing_fields = []
                            if not requester: missing_fields.append("Người YC")
                            if not factory: missing_fields.append("Nhà Máy")
                            if not project: missing_fields.append("Dự Án")
                            skip_reasons.append(f"Dòng {idx + 2}: Thiếu {', '.join(missing_fields)}")
                            continue

                        # Build values dict with formatting
                        values = {}
                        for col in self.CSV_HEADERS:
                            val = row.get(col, "")
                            values[col] = self._format_import_value(col, val)

                        # Auto-generate request_no
                        values["request_no"] = self._generate_next_request_code(cursor)

                        # Auto-fill request_date if empty
                        if not values.get("request_date"):
                            values["request_date"] = datetime.now().strftime("%Y-%m-%d")

                        # Insert
                        cols = list(values.keys())
                        placeholders = ", ".join(["?"] * len(cols))
                        cols_str = ", ".join(cols)

                        cursor.execute(
                            f"INSERT INTO requests ({cols_str}) VALUES ({placeholders})",
                            list(values.values())
                        )
                        imported += 1

                    except Exception as e:
                        errors.append(f"Dòng {idx + 2}: {str(e)}")

            # Build detailed result message
            msg = f"Kết quả Import:\n\n"
            msg += f"• Tổng dòng trong file: {total_rows}\n"
            msg += f"• Nhập thành công: {imported}\n"
            msg += f"• Bỏ qua: {skipped}\n"
            msg += f"• Lỗi: {len(errors)}\n"

            if skip_reasons:
                msg += f"\nChi tiết bỏ qua ({len(skip_reasons)}):\n"
                msg += "\n".join(skip_reasons[:5])
                if len(skip_reasons) > 5:
                    msg += f"\n... và {len(skip_reasons) - 5} dòng khác"

            if errors:
                msg += f"\n\nChi tiết lỗi ({len(errors)}):\n"
                msg += "\n".join(errors[:3])
                if len(errors) > 3:
                    msg += f"\n... và {len(errors) - 3} lỗi khác"

            if imported > 0:
                QMessageBox.information(self, "Kết quả Import", msg)
            else:
                msg += "\n\nGợi ý:\n"
                msg += "1. Kiểm tra file có dữ liệu thực (không phải dòng mẫu)\n"
                msg += "2. Đảm bảo các cột bắt buộc có giá trị: Mã YC, Người YC, Nhà Máy, Dự Án\n"
                msg += "3. Dùng 'Tải Mẫu' để lấy file đúng format"
                QMessageBox.warning(self, "Không có dữ liệu được nhập", msg)

            # Refresh and emit event
            if imported > 0:
                self._load_recent_requests()
                get_event_bus().emit_request_created("batch_import")

            logger.info(f"CSV import: {imported}/{total_rows} from {path}, skipped: {skipped}, errors: {len(errors)}")
            log_audit("CSV_IMPORT", details=f"Imported {imported}/{total_rows} records")

        except Exception as e:
            logger.error(f"Failed to import CSV: {e}", exc_info=True)
            QMessageBox.critical(self, "Lỗi", str(e))

    def _export_csv(self):
        """Export requests to CSV with full template columns"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Xuất CSV", "DanhSach_YeuCau.csv", "CSV (*.csv)"
        )
        if not path:
            return

        try:
            db = get_db()

            # Get filter condition (same as _load_recent_requests)
            filter_idx = self.cb_recent_filter.currentIndex() if hasattr(self, 'cb_recent_filter') else 1
            today = QDate.currentDate()

            if filter_idx == 0:  # Hôm nay
                date_str = today.toString("yyyy-MM-dd")
                condition = "request_date LIKE ?"
                params = (f"{date_str}%",)
            elif filter_idx == 1:  # 7 ngày
                start_date = today.addDays(-7).toString("yyyy-MM-dd")
                condition = "request_date >= ?"
                params = (start_date,)
            elif filter_idx == 2:  # 30 ngày
                start_date = today.addDays(-30).toString("yyyy-MM-dd")
                condition = "request_date >= ?"
                params = (start_date,)
            else:  # Tất cả
                condition = "1=1"
                params = None

            # Query with all columns matching CSV_HEADERS
            query = f"""
                SELECT request_no, request_date, requester, factory, project, phase,
                       category, equip_no, equip_name, qty, test_condition,
                       cos, cos_res, hcross, xhatch_res, xcross, xsection_res,
                       func_test, func_res, final_res, status,
                       plan_start, plan_end, actual_start, actual_end, note, dri
                FROM requests
                WHERE {condition}
                ORDER BY id DESC
            """

            rows = db.fetch_all(query, params)

            # Create DataFrame with Vietnamese headers
            data = []
            for row in rows:
                data.append(list(row))

            df = pd.DataFrame(data, columns=self.CSV_HEADERS_VI)

            # Fill NaN with empty string
            df = df.fillna("")

            df.to_csv(path, index=False, encoding='utf-8-sig')

            QMessageBox.information(self, "Thành công", f"Đã xuất {len(data)} dòng!")
            logger.info(f"CSV exported: {len(data)} rows to {path}")

        except Exception as e:
            logger.error(f"Failed to export CSV: {e}", exc_info=True)
            QMessageBox.critical(self, "Lỗi", str(e))

    def _generate_next_request_code(self, cursor) -> str:
        """Generate next request code for today (format: YYYYMMDD-XXX)"""
        today_str = datetime.now().strftime("%Y%m%d")

        # Get last code for today
        cursor.execute(
            """SELECT TOP 1 request_no FROM requests
               WHERE request_no LIKE ?
               ORDER BY request_no DESC""",
            (f"{today_str}-%",)
        )
        row = cursor.fetchone()

        if row and row[0]:
            try:
                last_seq = int(row[0].split("-")[1])
                return f"{today_str}-{last_seq + 1:03d}"
            except (IndexError, ValueError):
                pass

        return f"{today_str}-001"

    def _format_import_value(self, col: str, val) -> str:
        """Format import value to match software input format"""
        if pd.isna(val) or val is None:
            return ""

        val_str = str(val).strip()

        # Skip empty values
        if not val_str or val_str.lower() == "nan":
            return ""

        # Date fields: format to YYYY-MM-DD or MM-DD HH:MM
        date_fields = ["request_date"]
        datetime_fields = ["plan_start", "plan_end", "actual_start", "actual_end"]

        if col in date_fields:
            return self._parse_date(val_str, "%Y-%m-%d")

        if col in datetime_fields:
            return self._parse_datetime(val_str, "%Y-%m-%d %H:%M")

        # Numeric fields
        if col == "qty":
            try:
                # Remove decimals if whole number
                num = float(val_str)
                return str(int(num)) if num == int(num) else str(num)
            except ValueError:
                return val_str

        return val_str

    def _parse_date(self, val: str, output_format: str) -> str:
        """Parse date string to standard format"""
        if not val:
            return ""

        # Common date formats to try
        formats = [
            "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
            "%Y/%m/%d", "%d-%m-%Y", "%Y.%m.%d"
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(val, fmt)
                return dt.strftime(output_format)
            except ValueError:
                continue

        return val  # Return original if can't parse

    def _parse_datetime(self, val: str, output_format: str) -> str:
        """Parse datetime string to standard format MM-dd HH:mm"""
        if not val:
            return ""

        # Common datetime formats to try (from Excel exports, manual input, etc.)
        formats = [
            # Already correct format
            "%m-%d %H:%M",
            # Full datetime formats
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            # Date only - default time to 08:00
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y/%m/%d",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(val, fmt)
                return dt.strftime(output_format)
            except ValueError:
                continue

        return val  # Return original if can't parse

