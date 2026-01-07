"""
kRel - Input Tab Form Section
Phần form nhập liệu - tách từ input_tab.py
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QDateTimeEdit, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QDateTime

from src.config import TEST_PAIRS, FINAL_RESULTS
from src.styles import RESULT_FIELD_STYLE
from src.services.lookup_service import get_lookup_service
from src.widgets.validated_field import ValidatedField


class FormBuilder:
    """Helper class để tạo form fields"""
    
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
    REQUIRED_FIELDS = ["request_no", "requester", "factory", "project"]
    
    def __init__(self, parent: QWidget):
        self.parent = parent
        self.widgets = {}
        self.validated_fields = {}
        self.lookup_service = get_lookup_service()
    
    def build_input_grid(self, parent_layout):
        """Tạo grid nhập liệu chính"""
        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setVerticalSpacing(3)

        MAX_COLS = 4
        row, col = 0, 0

        # Top fields
        for label, field in self.TOP_FIELDS:
            self._create_field(grid, label, field, row, col)
            col += 1
            if col >= MAX_COLS:
                col, row = 0, row + 1

        # Separator
        if col > 0:
            row += 1
        self._add_separator(grid, row)
        row += 1

        # Test section header
        self._add_section_header(grid, row, "📊 Kết Quả Test")
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

        # Column stretches
        for i in range(MAX_COLS):
            grid.setColumnStretch(i * 2 + 1, 1)

        parent_layout.addLayout(grid)

        # Auto-fill for test results
        for inp_key, res_key, _, _ in TEST_PAIRS:
            self._setup_auto_result(inp_key, res_key)

        return self.widgets, self.validated_fields
    
    def _create_field(self, grid, label_text, field_name, row, col, is_result=False):
        """Tạo field với label"""
        is_required = field_name in self.REQUIRED_FIELDS
        label_suffix = " *" if is_required else ""

        label = QLabel(f"{label_text}{label_suffix}:")
        label.setStyleSheet("font-weight: 500; color: #424242; font-size: 11px;")
        grid.addWidget(label, row, col * 2)

        # Create widget
        if field_name == "request_date":
            widget = QDateTimeEdit()
            widget.setCalendarPopup(True)
            widget.setDisplayFormat("yyyy-MM-dd")
            widget.setDateTime(QDateTime.currentDateTime())
        elif field_name == "final_res":
            widget = QComboBox()
            widget.addItems([""] + FINAL_RESULTS)
            widget.setStyleSheet(RESULT_FIELD_STYLE)
        elif field_name in self.COMBO_FIELDS:
            widget = QComboBox()
            widget.setEditable(field_name == "test_condition")
            self._load_combo(widget, field_name)
        else:
            widget = QLineEdit()
            if field_name == "equip_name":
                widget.setReadOnly(True)

        # Wrap with validation if needed
        if field_name in self.REQUIRED_FIELDS or field_name == "qty":
            validated = ValidatedField(widget, field_name, label_text)
            self.validated_fields[field_name] = validated
            grid.addWidget(validated, row, col * 2 + 1)
        else:
            grid.addWidget(widget, row, col * 2 + 1)

        self.widgets[field_name] = widget
    
    def _load_combo(self, combo, field_name):
        """Load items cho combo box"""
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
                items = self.lookup_service.get_lookup_values(table) if table else []
            
            for item in items:
                if item:
                    combo.addItem(item)
        except Exception:
            pass
    
    def _add_separator(self, grid, row):
        """Thêm đường kẻ phân cách"""
        sep = QFrame()
        sep.setStyleSheet("background-color: #1565C0; border-radius: 1px;")
        sep.setFixedHeight(2)
        grid.addWidget(sep, row, 0, 1, 8)
    
    def _add_section_header(self, grid, row, text):
        """Thêm header cho section"""
        label = QLabel(f"<b style='color: #1565C0; font-size: 12px;'>{text}</b>")
        label.setStyleSheet("background-color: #E3F2FD; padding: 3px 8px; border-radius: 3px;")
        grid.addWidget(label, row, 0, 1, 8)
    
    def _setup_auto_result(self, src_key, dest_key):
        """Auto-fill kết quả test"""
        if src_key not in self.widgets or dest_key not in self.widgets:
            return
        
        src = self.widgets[src_key]
        dest = self.widgets[dest_key]
        
        def update(text):
            if text.strip():
                dest.setText(f"xxF/{text.strip()}T")
            else:
                dest.clear()
        
        if isinstance(src, QLineEdit):
            src.textChanged.connect(update)
        elif isinstance(src, QComboBox):
            src.currentTextChanged.connect(update)

