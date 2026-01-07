"""
kRel - Input Tab Form Section
Phần form nhập liệu với giao diện đẹp
"""
from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QDateTimeEdit
)
from PyQt6.QtCore import QDateTime

from src.config import TEST_PAIRS, FINAL_RESULTS
from src.styles import RESULT_FIELD_STYLE
from src.services.lookup_service import get_lookup_service
from src.widgets.validated_field import ValidatedField


class FormBuilder:
    """Helper class để tạo form fields với giao diện đẹp"""

    # Field definitions - chia thành 2 hàng
    ROW1_FIELDS = [
        ("Mã Yêu cầu", "request_no"), ("Ngày yêu cầu", "request_date"),
        ("Người yêu cầu", "requester"), ("Nhà máy", "factory"),
        ("Dự án", "project"), ("Giai đoạn", "phase"),
    ]

    ROW2_FIELDS = [
        ("Hạng mục", "category"), ("Mã Thiết bị", "equip_no"),
        ("Tên Thiết bị", "equip_name"), ("Số lượng", "qty"),
        ("Điều kiện test", "test_condition"), ("Trạng thái", "status"),
    ]

    # For compatibility
    TOP_FIELDS = ROW1_FIELDS + ROW2_FIELDS
    BOTTOM_FIELDS = [("KQ Cuối", "final_res")]

    COMBO_FIELDS = ["factory", "project", "phase", "category", "equip_no", "status"]
    REQUIRED_FIELDS = ["request_no", "requester", "factory", "project"]

    # GroupBox styles
    INFO_GROUP_STYLE = """
        QGroupBox {
            font-weight: 600; font-size: 12px; color: #1565C0;
            border: 1px solid #BBDEFB; border-radius: 6px;
            margin-top: 12px; padding: 8px 8px 6px 8px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #F8FBFF, stop:1 #F0F7FF);
        }
        QGroupBox::title {
            subcontrol-origin: margin; left: 12px; padding: 0 6px;
            background-color: #E3F2FD; border-radius: 3px;
        }
    """

    TEST_GROUP_STYLE = """
        QGroupBox {
            font-weight: 600; font-size: 12px; color: #2E7D32;
            border: 1px solid #C8E6C9; border-radius: 6px;
            margin-top: 12px; padding: 8px 8px 6px 8px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #F8FFF8, stop:1 #F1F8E9);
        }
        QGroupBox::title {
            subcontrol-origin: margin; left: 12px; padding: 0 6px;
            background-color: #E8F5E9; border-radius: 3px;
        }
    """

    def __init__(self, parent: QWidget):
        self.parent = parent
        self.widgets = {}
        self.validated_fields = {}
        self.lookup_service = get_lookup_service()

    def build_input_grid(self, parent_layout):
        """Tạo form nhập liệu với GroupBox đẹp"""
        # ===== THÔNG TIN YÊU CẦU =====
        info_group = QGroupBox("📋 Thông Tin Yêu Cầu")
        info_group.setStyleSheet(self.INFO_GROUP_STYLE)
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(6)
        info_layout.setContentsMargins(10, 8, 10, 8)

        # Row 1: 6 fields
        for i, (label, field) in enumerate(self.ROW1_FIELDS):
            self._create_field(info_layout, label, field, 0, i)

        # Row 2: 6 fields
        for i, (label, field) in enumerate(self.ROW2_FIELDS):
            self._create_field(info_layout, label, field, 1, i)

        # Column stretches
        for i in range(6):
            info_layout.setColumnStretch(i * 2 + 1, 1)

        parent_layout.addWidget(info_group)

        # ===== KẾT QUẢ TEST =====
        test_group = QGroupBox("📊 Kết Quả Test")
        test_group.setStyleSheet(self.TEST_GROUP_STYLE)
        test_layout = QGridLayout(test_group)
        test_layout.setSpacing(6)
        test_layout.setContentsMargins(10, 8, 10, 8)

        # Test pairs - input row (row 0)
        for i, (inp_key, _, lbl_inp, _) in enumerate(TEST_PAIRS):
            self._create_field(test_layout, lbl_inp, inp_key, 0, i)

        # Test pairs - result row (row 1)
        for i, (_, res_key, _, lbl_res) in enumerate(TEST_PAIRS):
            self._create_field(test_layout, lbl_res, res_key, 1, i, is_result=True)

        # Final result (row 2, first column)
        self._create_field(test_layout, "KQ Cuối", "final_res", 2, 0)

        # Column stretches
        for i in range(len(TEST_PAIRS)):
            test_layout.setColumnStretch(i * 2 + 1, 1)

        parent_layout.addWidget(test_group)

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

