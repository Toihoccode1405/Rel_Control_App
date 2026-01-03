"""
kRel - Input Tab
Data entry form for new test requests
"""
import os
import shutil
from datetime import datetime

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
    BTN_STYLE_BLUE, RESULT_FIELD_STYLE
)
from src.services.database import get_db
from src.services.lookup_service import get_lookup_service
from src.services.request_service import get_request_service
from src.services.logger import get_logger, log_audit

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

    def __init__(self, log_path: str, user_info: dict, parent=None):
        super().__init__(parent)
        self.log_path = log_path
        self.user_info = user_info
        self.widgets = {}  # Store all input widgets

        self.db = get_db()
        self.lookup_service = get_lookup_service()
        self.request_service = get_request_service()

        os.makedirs(self.log_path, exist_ok=True)

        self.setStyleSheet(INPUT_TAB_STYLE)
        self._setup_ui()

        # Initialize request code
        self._update_request_code(QDate.currentDate())
        self._load_recent_requests()
    
    def _setup_ui(self):
        """Setup UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Input grid
        self._setup_input_grid(main_layout)

        # Bottom section (schedule, notes, save button)
        self._setup_bottom_section(main_layout)

        # Recent requests section
        table_header = QLabel("<b style='font-size: 14px; color: #1565C0;'>📋 Danh sách nhập trong ngày</b>")
        table_header.setContentsMargins(0, 8, 0, 4)
        main_layout.addWidget(table_header)

        self.table = QTableView()
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.setMinimumHeight(200)
        main_layout.addWidget(self.table, stretch=1)

    def _setup_input_grid(self, parent_layout):
        """Setup main input grid"""
        grid = QGridLayout()
        grid.setSpacing(8)
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
        sep_frame.setStyleSheet("background-color: #1565C0; border-radius: 2px;")
        sep_frame.setFixedHeight(3)
        grid.addWidget(sep_frame, row, 0, 1, 8)
        row += 1

        # Test section header
        test_label = QLabel("<b style='color: #1565C0; font-size: 14px;'>📊 Kết Quả Test</b>")
        test_label.setStyleSheet("background-color: #E3F2FD; padding: 6px 12px; border-radius: 4px;")
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
        # Label
        lbl = QLabel(f"{label_text}:")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if is_result:
            lbl.setStyleSheet("font-weight: 600; color: #E65100;")
        else:
            lbl.setStyleSheet("font-weight: 500; color: #424242;")
        grid.addWidget(lbl, row, col * 2)

        # Widget
        widget = self._create_input_widget(field_name, is_result)
        self.widgets[field_name] = widget
        grid.addWidget(widget, row, col * 2 + 1)
    
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
        bot_layout.setSpacing(12)

        # Schedule group
        grp_date = QGroupBox("📅 Tiến độ")
        dg = QGridLayout(grp_date)
        dg.setSpacing(8)
        dg.setContentsMargins(12, 16, 12, 12)

        schedule_fields = [
            ("Vào KH", "plan_start", 0, 0),
            ("Ra KH", "plan_end", 0, 1),
            ("Vào TT", "actual_start", 1, 0),
            ("Ra TT", "actual_end", 1, 1)
        ]

        for title, key, dr, dc in schedule_fields:
            lbl = QLabel(title + ":")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet("font-weight: 500; color: #424242;")
            dg.addWidget(lbl, dr, dc * 2)

            dt = QDateTimeEdit()
            dt.setCalendarPopup(True)
            dt.setDisplayFormat("MM-dd HH:mm")
            dt.setDateTime(QDateTime.currentDateTime())
            dg.addWidget(dt, dr, dc * 2 + 1)
            self.widgets[key] = dt

        bot_layout.addWidget(grp_date, stretch=3)

        # Notes group
        grp_note = QGroupBox("📝 Thông tin")
        gn = QGridLayout(grp_note)
        gn.setSpacing(8)
        gn.setContentsMargins(12, 16, 12, 12)

        # Log file row
        log_lbl = QLabel("Log:")
        log_lbl.setStyleSheet("font-weight: 500; color: #424242;")
        gn.addWidget(log_lbl, 0, 0)

        lw = QWidget()
        lh = QHBoxLayout(lw)
        lh.setContentsMargins(0, 0, 0, 0)
        lh.setSpacing(8)

        self.log_label = QLabel("Chưa chọn file...")
        self.log_label.setStyleSheet("color: #9E9E9E; font-style: italic;")

        btn_log = QPushButton("📁 Chọn")
        btn_log.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_log.setFixedWidth(70)
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
        """Load today's requests into table"""
        try:
            today_str = QDate.currentDate().toString("yyyy-MM-dd")

            db = get_db()
            rows = db.fetch_all("""
                SELECT request_no, request_date, requester, factory, project, phase,
                       equip_no, equip_name, test_condition,
                       plan_start, plan_end, actual_start, actual_end,
                       status, dri, final_res
                FROM requests WHERE request_date LIKE ? ORDER BY id DESC
            """, (f"{today_str}%",))

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

        except Exception:
            pass

