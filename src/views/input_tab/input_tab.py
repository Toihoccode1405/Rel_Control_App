"""
kRel - Input Tab (Refactored)
Tab nhập liệu với giao diện đẹp - Material Design
"""
import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QDateTimeEdit, QPushButton,
    QFileDialog, QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt, QDateTime, QDate

from src.config import TEST_PAIRS
from src.styles import INPUT_TAB_STYLE
from src.services.database import get_db
from src.services.lookup_service import get_lookup_service
from src.services.request_service import get_request_service
from src.services.logger import get_logger
from src.services.validator import FormValidator
from src.services.data_event_bus import get_event_bus

from src.controllers.request_controller import RequestController
from src.controllers.csv_handler import CsvHandler
from src.views.input_tab.form_builder import FormBuilder
from src.views.input_tab.table_section import TableSection

logger = get_logger("input_tab")


class InputTab(QWidget):
    """Tab nhập liệu với giao diện Material Design đẹp"""

    # GroupBox styles
    SCHEDULE_GROUP_STYLE = """
        QGroupBox {
            font-weight: 600; font-size: 12px; color: #E65100;
            border: 1px solid #FFE0B2; border-radius: 6px;
            margin-top: 12px; padding: 8px 8px 6px 8px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFAF5, stop:1 #FFF8E1);
        }
        QGroupBox::title {
            subcontrol-origin: margin; left: 12px; padding: 0 6px;
            background-color: #FFF3E0; border-radius: 3px;
        }
    """

    NOTE_GROUP_STYLE = """
        QGroupBox {
            font-weight: 600; font-size: 12px; color: #7B1FA2;
            border: 1px solid #E1BEE7; border-radius: 6px;
            margin-top: 12px; padding: 8px 8px 6px 8px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FDF5FF, stop:1 #F3E5F5);
        }
        QGroupBox::title {
            subcontrol-origin: margin; left: 12px; padding: 0 6px;
            background-color: #F3E5F5; border-radius: 3px;
        }
    """

    def __init__(self, log_path: str, user_info: dict, parent=None):
        super().__init__(parent)
        self.log_path = log_path
        self.user_info = user_info

        # Controllers
        self.controller = RequestController(log_path)
        self.csv_handler = CsvHandler()

        # Services
        self.lookup_service = get_lookup_service()
        self.request_service = get_request_service()

        os.makedirs(self.log_path, exist_ok=True)

        self.setStyleSheet(INPUT_TAB_STYLE)
        self._setup_ui()
        self._setup_validation()
        self._connect_events()

        # Initialize
        self._update_request_code(QDate.currentDate())
        self._load_recent_requests()

    def _setup_ui(self):
        """Setup giao diện chính với layout đẹp"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(6)

        # Form section với GroupBox đẹp
        self.form_builder = FormBuilder(self)
        self.widgets, self.validated_fields = self.form_builder.build_input_grid(main_layout)

        # Bottom section (schedule, log, note, save button)
        self._setup_bottom_section(main_layout)

        # Table section
        self.table_section = TableSection(self)
        self.table_section.build_toolbar(
            main_layout,
            on_filter=self._load_recent_requests,
            on_search=self._on_search,
            on_template=self._download_template,
            on_import=self._import_csv,
            on_export=self._export_csv
        )
        self.table_section.build_table(main_layout)

        # Alias for compatibility
        self.table = self.table_section.table
        self.cb_recent_filter = self.table_section.cb_filter

    def _setup_bottom_section(self, parent_layout):
        """Setup phần dưới: lịch trình, log, note, nút lưu - giao diện đẹp"""
        bot_layout = QHBoxLayout()
        bot_layout.setSpacing(10)

        # Schedule group
        self._setup_schedule_group(bot_layout)

        # Note group
        self._setup_note_group(bot_layout)

        # Save button
        self._setup_save_button(bot_layout)

        parent_layout.addLayout(bot_layout)

    def _setup_schedule_group(self, parent_layout):
        """Setup nhóm lịch trình với style đẹp"""
        grp = QGroupBox("📅 Lịch Trình Test")
        grp.setStyleSheet(self.SCHEDULE_GROUP_STYLE)

        grid = QGridLayout(grp)
        grid.setSpacing(6)
        grid.setContentsMargins(10, 6, 10, 6)

        fields = [
            ("Vào KH:", "plan_start", 0), ("Ra KH:", "plan_end", 1),
            ("Vào TT:", "actual_start", 2), ("Ra TT:", "actual_end", 3)
        ]

        for label, key, col in fields:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: 500; color: #424242; font-size: 11px;")
            grid.addWidget(lbl, 0, col * 2)

            dt = QDateTimeEdit()
            dt.setCalendarPopup(True)
            dt.setDisplayFormat("MM-dd HH:mm")
            dt.setDateTime(QDateTime.currentDateTime())
            dt.setStyleSheet("""
                QDateTimeEdit {
                    border: 1px solid #FFE0B2; border-radius: 4px;
                    padding: 4px 6px; background-color: #FFFFFF;
                    font-size: 11px; min-height: 24px;
                }
                QDateTimeEdit:hover { border-color: #FFB74D; }
                QDateTimeEdit:focus { border: 1.5px solid #FF9800; }
            """)
            grid.addWidget(dt, 0, col * 2 + 1)
            self.widgets[key] = dt

        parent_layout.addWidget(grp, stretch=3)

    def _setup_note_group(self, parent_layout):
        """Setup nhóm ghi chú và log với style đẹp"""
        grp = QGroupBox("📝 Thông Tin Thêm")
        grp.setStyleSheet(self.NOTE_GROUP_STYLE)

        grid = QGridLayout(grp)
        grid.setSpacing(6)
        grid.setContentsMargins(10, 6, 10, 6)

        # Log file
        lbl_log = QLabel("Log:")
        lbl_log.setStyleSheet("font-weight: 500; color: #424242; font-size: 11px;")
        grid.addWidget(lbl_log, 0, 0)

        log_layout = QHBoxLayout()
        log_layout.setSpacing(4)

        self.log_label = QLabel("Chưa chọn file...")
        self.log_label.setStyleSheet("""
            background-color: #F3E5F5; padding: 4px 8px; border-radius: 4px;
            color: #7B1FA2; font-size: 11px;
        """)
        log_layout.addWidget(self.log_label, stretch=1)

        btn_log = QPushButton("📂")
        btn_log.setFixedSize(28, 24)
        btn_log.setStyleSheet("""
            QPushButton {
                background-color: #E1BEE7; border: none; border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #CE93D8; }
        """)
        btn_log.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_log.clicked.connect(self._pick_log_file)
        log_layout.addWidget(btn_log)

        grid.addLayout(log_layout, 0, 1)

        # Note
        lbl_note = QLabel("Ghi chú:")
        lbl_note.setStyleSheet("font-weight: 500; color: #424242; font-size: 11px;")
        grid.addWidget(lbl_note, 1, 0)

        self.widgets["note"] = QLineEdit()
        self.widgets["note"].setPlaceholderText("Nhập ghi chú...")
        self.widgets["note"].setStyleSheet("""
            QLineEdit {
                border: 1px solid #E1BEE7; border-radius: 4px;
                padding: 4px 8px; background-color: #FFFFFF;
                font-size: 11px; min-height: 24px;
            }
            QLineEdit:hover { border-color: #CE93D8; }
            QLineEdit:focus { border: 1.5px solid #9C27B0; }
        """)
        grid.addWidget(self.widgets["note"], 1, 1)

        # Hidden log_link
        self.widgets["log_link"] = QLineEdit()

        # DRI
        lbl_dri = QLabel("DRI:")
        lbl_dri.setStyleSheet("font-weight: 500; color: #424242; font-size: 11px;")
        grid.addWidget(lbl_dri, 2, 0)

        dri = QLineEdit(self.user_info.get('name', ''))
        dri.setReadOnly(True)
        dri.setStyleSheet("""
            background-color: #F3E5F5; color: #7B1FA2;
            border: 1px solid #E1BEE7; border-radius: 4px;
            padding: 4px 8px; font-size: 11px; min-height: 24px;
        """)
        grid.addWidget(dri, 2, 1)

        parent_layout.addWidget(grp, stretch=4)

    def _setup_save_button(self, parent_layout):
        """Setup nút lưu với style đẹp"""
        from PyQt6.QtWidgets import QVBoxLayout
        btn_layout = QVBoxLayout()
        btn_layout.setContentsMargins(0, 20, 0, 0)

        btn = QPushButton("💾 LƯU DỮ LIỆU")
        btn.setFixedHeight(60)
        btn.setMinimumWidth(130)
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #43A047, stop:1 #2E7D32);
                color: white; border: none; border-radius: 8px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #388E3C);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #388E3C, stop:1 #1B5E20);
            }
        """)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._save)
        btn_layout.addWidget(btn)
        btn_layout.addStretch()

        parent_layout.addLayout(btn_layout, stretch=1)

    def _setup_validation(self):
        """Setup form validation"""
        # Truyền validated_fields vào FormValidator
        self.form_validator = FormValidator(self.validated_fields)

        # Required fields
        required = ["request_no", "requester", "factory", "project"]
        for field in required:
            if field in self.validated_fields:
                self.form_validator.required(field)

        # Qty validation - numeric
        if "qty" in self.validated_fields:
            self.form_validator.numeric("qty")

    def _connect_events(self):
        """Kết nối events"""
        # Date change -> update request code
        self.widgets["request_date"].dateChanged.connect(self._update_request_code)

        # Equipment change -> auto-fill name
        if "equip_no" in self.widgets:
            self.widgets["equip_no"].currentTextChanged.connect(self._on_equipment_change)

        # DataEventBus events
        bus = get_event_bus()
        bus.request_updated.connect(lambda _: self._load_recent_requests())

    def _update_request_code(self, date):
        """Cập nhật mã request theo ngày"""
        if isinstance(date, QDate):
            dt = datetime(date.year(), date.month(), date.day())
        else:
            dt = datetime.now()
        code = self.request_service.generate_request_code(dt)
        self.widgets["request_no"].setText(code)

    def _on_equipment_change(self, text):
        """Xử lý thay đổi thiết bị"""
        equip = self.lookup_service.get_equipment_by_id(text)
        if equip:
            self.widgets["equip_name"].setText(equip.name)
            cb = self.widgets["test_condition"]
            cb.clear()
            cb.addItems(equip.get_recipes())

    def _on_search(self, text):
        """Xử lý tìm kiếm"""
        if not text.strip():
            self._load_recent_requests()
        else:
            self.table_section.filter_table(text)

    def _load_recent_requests(self):
        """Load danh sách request gần đây"""
        filter_idx = self.table_section.get_filter_index()
        rows = self.controller.get_recent_requests(filter_idx)
        self.table_section.update_table(rows)

    def _pick_log_file(self):
        """Chọn file log"""
        path, _ = QFileDialog.getOpenFileName(self, "Chọn File Log")
        if path:
            name = os.path.basename(path)
            self.log_label.setText(name[:15] + "..." if len(name) > 15 else name)
            self.log_label.setToolTip(name)
            self.log_label.path = path

            req_no = self.widgets["request_no"].text().strip() or "Unknown"
            self.widgets["log_link"].setText(os.path.join(self.log_path, req_no, name))

    def _save(self):
        """Lưu request"""
        try:
            self.form_validator.clear_all_errors()

            if not self.form_validator.validate_all():
                return

            values = self._collect_form_values()

            # Copy log file if selected
            if hasattr(self.log_label, 'path'):
                self.controller.copy_log_file(
                    self.log_label.path,
                    values.get("request_no", "Unknown")
                )

            success, msg = self.controller.save(values, self.user_info.get('name', ''))

            if success:
                QMessageBox.information(self, "Thành công", msg)
                self._clear_form()
                self._load_recent_requests()
            else:
                QMessageBox.critical(self, "Lỗi", msg)

        except Exception as e:
            logger.error(f"Save error: {e}", exc_info=True)
            QMessageBox.critical(self, "Lỗi", str(e))

    def _collect_form_values(self) -> dict:
        """Thu thập giá trị từ form"""
        values = {}

        def get_val(key):
            if key not in self.widgets:
                return ""
            w = self.widgets[key]
            if key == "request_date":
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
        for _, key in FormBuilder.TOP_FIELDS + FormBuilder.BOTTOM_FIELDS:
            values[key] = get_val(key)

        # Test pairs
        for inp, res, _, _ in TEST_PAIRS:
            values[inp] = get_val(inp)
            values[res] = get_val(res)

        # Additional fields
        for key in ["log_link", "note", "plan_start", "plan_end", "actual_start", "actual_end"]:
            values[key] = get_val(key)

        values["dri"] = self.user_info.get('name', '')
        return values

    def _clear_form(self):
        """Xóa form để nhập mới"""
        self._update_request_code(QDate.currentDate())

        self.log_label.setText("...")
        if hasattr(self.log_label, 'path'):
            delattr(self.log_label, 'path')

        if "log_link" in self.widgets:
            self.widgets["log_link"].clear()

        for key in ["plan_start", "plan_end", "actual_start", "actual_end"]:
            if key in self.widgets:
                self.widgets[key].setDateTime(QDateTime.currentDateTime())

        exclude = ["request_no", "request_date", "plan_start", "plan_end",
                   "actual_start", "actual_end", "logfile", "log_link", "dri"]

        for key, widget in self.widgets.items():
            if key not in exclude:
                if isinstance(widget, QLineEdit):
                    widget.clear()
                elif isinstance(widget, QComboBox):
                    widget.setCurrentIndex(0)

    def _download_template(self):
        """Tải file mẫu CSV"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Lưu File Mẫu", "Template_YeuCau.csv", "CSV (*.csv)"
        )
        if path:
            success, msg = self.csv_handler.create_template(path)
            if success:
                QMessageBox.information(self, "Thành công", msg)
            else:
                QMessageBox.critical(self, "Lỗi", msg)

    def _import_csv(self):
        """Import từ CSV"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn File CSV", "", "CSV (*.csv)"
        )
        if not path:
            return

        imported, skipped, errors = self.csv_handler.import_csv(path)

        msg = f"Đã nhập: {imported} dòng\nBỏ qua: {skipped} dòng"
        if errors:
            msg += f"\n\nLỗi ({len(errors)}):\n" + "\n".join(errors[:3])
            if len(errors) > 3:
                msg += f"\n... và {len(errors) - 3} lỗi khác"

        if imported > 0:
            QMessageBox.information(self, "Kết quả Import", msg)
            self._load_recent_requests()
        else:
            QMessageBox.warning(self, "Không có dữ liệu", msg)

    def _export_csv(self):
        """Export ra CSV"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Xuất CSV", "DanhSach_YeuCau.csv", "CSV (*.csv)"
        )
        if not path:
            return

        filter_idx = self.table_section.get_filter_index()
        success, count, msg = self.csv_handler.export_csv(path, filter_idx)

        if success:
            QMessageBox.information(self, "Thành công", f"Đã xuất {count} dòng!")
        else:
            QMessageBox.critical(self, "Lỗi", msg)

