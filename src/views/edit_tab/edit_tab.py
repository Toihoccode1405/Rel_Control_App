"""
kRel - Edit Tab (Refactored)
Tab chỉnh sửa dữ liệu với frozen columns support
"""
import os
import shutil
from configparser import ConfigParser

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QComboBox, QHeaderView,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor
import pandas as pd

from src.config import CONFIG_FILE, DEFAULT_LOG_PATH, STATUS_COLORS
from src.services.database import get_db
from src.services.logger import get_logger, log_audit
from src.services.data_event_bus import get_event_bus
from src.styles import (
    BTN_STYLE_BLUE, BTN_STYLE_GREEN_SOLID, BTN_STYLE_ORANGE_SOLID,
    TABLE_STYLE, TOOLBAR_BLUE_STYLE, FILTER_BLUE_STYLE
)
from src.widgets.loading_overlay import LoadingMixin

from src.views.edit_tab.delegates import (
    ComboDelegate, DateDelegate, RecipeDelegate, NoEditDelegate
)
from src.views.edit_tab.frozen_table import FrozenTableView

logger = get_logger("edit_tab")

# Database columns
DB_SELECT_COLS = [
    "id", "request_no", "request_date", "requester", "factory", "project",
    "phase", "category", "qty", "cos", "cos_res", "hcross",
    "xhatch_res", "xcross", "xsection_res", "func_test", "func_res",
    "final_res", "equip_no", "equip_name", "test_condition", "plan_start",
    "plan_end", "status", "dri", "actual_start", "actual_end", "logfile",
    "log_link", "note"
]

DEFAULT_COLOR = "#FFFFFF"


class EditTab(QWidget, LoadingMixin):
    """Tab chỉnh sửa dữ liệu với CRUD support"""

    COL_MAP = {
        4: "factory", 5: "project", 6: "phase",
        7: "category", 18: "equipment", 23: "status"
    }
    DATE_COLS = [2, 21, 22, 25, 26]

    HEADERS = [
        "ID", "Mã YC", "Ngày YC", "Người YC", "Nhà máy", "Dự án", "Giai đoạn",
        "Hạng mục", "SL", "Ngoại quan", "KQ Ngoại Quan",
        "Cross hatch", "KQ X-Hatch", "Cross section", "KQ X-Section",
        "Tính năng", "KQ Tính Năng", "KQ Cuối", "Mã TB", "Tên TB",
        "Điều kiện", "Vào KH", "Ra KH", "Trạng thái", "DRI",
        "Vào TT", "Ra TT", "Logfile", "Link", "Ghi chú"
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_db()
        self.table = None
        self.model = None
        self.log_path = self._load_log_path()
        
        self._setup_ui()
        self._connect_events()
        self._refresh()

    def _load_log_path(self) -> str:
        """Load log path from config"""
        if os.path.exists(CONFIG_FILE):
            config = ConfigParser()
            config.read(CONFIG_FILE, encoding="utf-8")
            if config.has_section("system"):
                return config["system"].get("log_path", DEFAULT_LOG_PATH)
        return DEFAULT_LOG_PATH

    def _connect_events(self):
        """Connect to DataEventBus events"""
        bus = get_event_bus()
        bus.request_created.connect(lambda _: self._refresh())

    def _setup_ui(self):
        """Setup UI với giao diện đẹp"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(8)

        self._setup_filter_bar(main_layout)
        self._setup_toolbar(main_layout)

        # Table container
        self.table_container = QVBoxLayout()
        self.table_container.setSpacing(0)
        main_layout.addLayout(self.table_container)

    def _setup_filter_bar(self, parent_layout):
        """Setup filter bar với style đẹp"""
        frame = QFrame()
        frame.setStyleSheet(FILTER_BLUE_STYLE)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # Filter icon and label
        layout.addWidget(QLabel("<b style='color: #1565C0; font-size: 13px;'>🔍 Lọc dữ liệu:</b>"))

        # Status filter
        self.cb_filter_status = QComboBox()
        self.cb_filter_status.setMinimumWidth(150)
        self.cb_filter_status.setStyleSheet(self._combo_style())
        self.cb_filter_status.currentTextChanged.connect(lambda _: self._load_data())
        layout.addWidget(self.cb_filter_status)

        # Result filter
        self.cb_filter_result = QComboBox()
        self.cb_filter_result.addItems(["Tất cả KQ", "-", "Pass", "Fail", "Waiver"])
        self.cb_filter_result.setMinimumWidth(120)
        self.cb_filter_result.setStyleSheet(self._combo_style())
        self.cb_filter_result.currentTextChanged.connect(lambda _: self._load_data())
        layout.addWidget(self.cb_filter_result)

        layout.addStretch()
        parent_layout.addWidget(frame)

    def _setup_toolbar(self, parent_layout):
        """Setup toolbar với style đẹp"""
        toolbar = QFrame()
        toolbar.setStyleSheet(TOOLBAR_BLUE_STYLE)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # Refresh button
        btn_refresh = QPushButton("🔄 Tải lại")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.clicked.connect(self._refresh)
        btn_refresh.setStyleSheet(BTN_STYLE_BLUE)
        layout.addWidget(btn_refresh)

        layout.addStretch()

        # Save button
        btn_save = QPushButton("💾 Lưu tất cả")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self._save)
        btn_save.setStyleSheet(BTN_STYLE_GREEN_SOLID)
        layout.addWidget(btn_save)

        # Export button
        btn_export = QPushButton("📤 Xuất CSV")
        btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export.clicked.connect(self._export_csv)
        btn_export.setStyleSheet(BTN_STYLE_ORANGE_SOLID)
        layout.addWidget(btn_export)

        parent_layout.addWidget(toolbar)

    def _combo_style(self):
        """Style cho combo box"""
        return """
            QComboBox {
                border: 1px solid #BBDEFB; border-radius: 5px;
                padding: 6px 12px; background-color: #FFFFFF;
                min-height: 28px; font-size: 12px; color: #212121;
            }
            QComboBox:hover { border-color: #90CAF9; background-color: #FAFEFF; }
            QComboBox:focus { border: 1.5px solid #1565C0; }
            QComboBox::drop-down { border: none; width: 24px; }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF; color: #212121;
                selection-background-color: #E3F2FD; selection-color: #1565C0;
                border: 1px solid #BBDEFB; border-radius: 4px;
            }
        """

    def _init_filter_list(self):
        """Initialize status filter list"""
        try:
            current = self.cb_filter_status.currentText()
            self.cb_filter_status.blockSignals(True)
            self.cb_filter_status.clear()
            self.cb_filter_status.addItem("Tất cả Trạng thái")

            rows = self.db.fetch_all("SELECT name FROM status ORDER BY name")
            for row in rows:
                if row[0]:
                    self.cb_filter_status.addItem(row[0])

            self.cb_filter_status.setCurrentText(current)
            self.cb_filter_status.blockSignals(False)
        except Exception:
            pass

    def _refresh(self):
        """Refresh data"""
        self.cb_filter_result.setCurrentIndex(0)
        self._init_filter_list()
        self._load_data()

    def _load_data(self):
        """Load data into table"""
        self.show_loading("Đang tải dữ liệu...")
        try:
            self._do_load_data()
        finally:
            self.hide_loading()

    def _do_load_data(self):
        """Internal data loading logic"""
        # Build combo data
        data = {}
        for col, table in self.COL_MAP.items():
            if table == "equipment":
                rows = self.db.fetch_all(
                    "SELECT control_no FROM equipment ORDER BY control_no"
                )
            else:
                rows = self.db.fetch_all(f"SELECT name FROM {table} ORDER BY name")
            data[col] = [""] + [r[0] for r in rows if r[0]]

        data[18] = ["-", "Pass", "Fail", "Waiver"]

        # Build query with filters
        conditions, params = [], []

        status = self.cb_filter_status.currentText()
        result = self.cb_filter_result.currentText()

        if status and status != "Tất cả Trạng thái":
            conditions.append("status=?")
            params.append(status)

        if result and result != "Tất cả KQ":
            conditions.append("final_res=?")
            params.append(result)

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        cols = ", ".join(DB_SELECT_COLS)
        query = f"SELECT {cols} FROM requests {where} ORDER BY id DESC"

        # Load data
        conn = self.db.connect()
        df = pd.read_sql_query(query, conn, params=tuple(params))

        # Build model
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(self.HEADERS)

        lemon_bg = QColor("#FFF9C4")

        for _, row in df.iterrows():
            status_val = str(row.iloc[23]) if row.iloc[23] else ""
            row_bg = QColor(STATUS_COLORS.get(status_val, DEFAULT_COLOR))

            items = []
            for v in row:
                val = str(v) if v is not None else ""
                item = QStandardItem(val)
                item.setBackground(lemon_bg if not val.strip() else row_bg)
                items.append(item)

            self.model.appendRow(items)

        self.model.itemChanged.connect(self._on_item_changed)

        # Create table
        if self.table:
            self.table_container.removeWidget(self.table)
            self.table.deleteLater()

        self.table = FrozenTableView(self.model, frozen_col_count=4)
        self.table.doubleClicked.connect(self._handle_double_click)
        self._setup_delegates(data)
        self._setup_column_widths()
        self.table_container.addWidget(self.table)

    def _setup_delegates(self, data: dict):
        """Setup table delegates"""
        self.table.setItemDelegate(ComboDelegate(self.table, data))
        self.table.frozen.setItemDelegate(ComboDelegate(self.table.frozen, data))

        self.table.setItemDelegateForColumn(2, DateDelegate(self.table))
        self.table.frozen.setItemDelegateForColumn(2, DateDelegate(self.table.frozen))

        dd = DateDelegate(self.table)
        for col in self.DATE_COLS:
            if col >= 4:
                self.table.setItemDelegateForColumn(col, dd)

        self.table.setItemDelegateForColumn(20, RecipeDelegate(self.table))
        self.table.setItemDelegateForColumn(27, NoEditDelegate(self.table))

    def _setup_column_widths(self):
        """Setup column widths"""
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for i in range(4):
            width = 120 if i > 0 else 50
            self.table.setColumnWidth(i, width)
            self.table.frozen.setColumnWidth(i, width)
        h.setSectionResizeMode(29, QHeaderView.ResizeMode.Stretch)

    def _on_item_changed(self, item):
        """Handle item change"""
        if not item.text().strip():
            item.setBackground(QColor("#FFF9C4"))
        else:
            item.setBackground(QColor("white"))

        # Auto-fill equipment name
        if item.column() == 18:
            equip_no = item.text().strip()
            if equip_no:
                try:
                    rows = self.db.fetch_all(
                        "SELECT name FROM equipment WHERE control_no=?",
                        (equip_no,)
                    )
                    if rows:
                        self.model.blockSignals(True)
                        self.model.setItem(item.row(), 19, QStandardItem(rows[0][0]))
                        self.model.blockSignals(False)
                except Exception:
                    pass

    def _handle_double_click(self, index):
        """Handle double click for log file selection"""
        if index.column() == 27:
            row = index.row()
            req_no = self.model.item(row, 1).text().strip()

            if not req_no:
                return QMessageBox.warning(self, "Lỗi", "Cần có Mã Yêu Cầu!")

            fname, _ = QFileDialog.getOpenFileName(self, "Chọn Logfile")
            if fname:
                try:
                    dest_dir = os.path.join(self.log_path, req_no)
                    os.makedirs(dest_dir, exist_ok=True)
                    dest_path = os.path.join(dest_dir, os.path.basename(fname))
                    shutil.copy(fname, dest_path)

                    self.model.item(row, 28).setText(os.path.basename(fname))
                    self.model.item(row, 29).setText(dest_path)

                    QMessageBox.information(self, "OK", f"Đã tải: {os.path.basename(fname)}")
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi", str(e))

    def _save(self):
        """Save all changes"""
        try:
            updated_count = 0
            with self.db.get_cursor() as cursor:
                for r in range(self.model.rowCount()):
                    row_data = [
                        self.model.item(r, c).text() if self.model.item(r, c) else ""
                        for c in range(self.model.columnCount())
                    ]

                    record_id = row_data[0]
                    if not record_id:
                        continue

                    cursor.execute("""
                        UPDATE requests SET
                            request_no=?, request_date=?, requester=?, factory=?,
                            project=?, phase=?, category=?, qty=?,
                            cos=?, cos_res=?, hcross=?, xhatch_res=?, xcross=?,
                            xsection_res=?, func_test=?, func_res=?, final_res=?,
                            equip_no=?, equip_name=?, test_condition=?,
                            plan_start=?, plan_end=?, status=?, dri=?,
                            actual_start=?, actual_end=?, logfile=?, log_link=?, note=?
                        WHERE id=?
                    """, (
                        row_data[1], row_data[2], row_data[3], row_data[4],
                        row_data[5], row_data[6], row_data[7], row_data[8],
                        row_data[9], row_data[10], row_data[11], row_data[12], row_data[13],
                        row_data[14], row_data[15], row_data[16], row_data[17],
                        row_data[18], row_data[19], row_data[20],
                        row_data[21], row_data[22], row_data[23], row_data[24],
                        row_data[25], row_data[26], row_data[27], row_data[28], row_data[29],
                        record_id
                    ))
                    updated_count += 1

            logger.info(f"Saved {updated_count} records")
            log_audit("DATA_SAVE", details=f"Updated {updated_count} records")

            if updated_count > 0:
                get_event_bus().emit_request_updated("batch")

            QMessageBox.information(self, "Thành công", "Đã lưu!")
            self._load_data()

        except Exception as e:
            logger.error(f"Failed to save: {e}", exc_info=True)
            QMessageBox.critical(self, "Lỗi", str(e))

    def _export_csv(self):
        """Export data to CSV"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Xuất", "kRel_Data.csv", "CSV (*.csv)"
        )

        if path:
            try:
                conditions, params = [], []
                status = self.cb_filter_status.currentText()
                result = self.cb_filter_result.currentText()

                if status and status != "Tất cả Trạng thái":
                    conditions.append("status=?")
                    params.append(status)

                if result and result != "Tất cả KQ":
                    conditions.append("final_res=?")
                    params.append(result)

                where = " WHERE " + " AND ".join(conditions) if conditions else ""
                cols = ", ".join(DB_SELECT_COLS)
                query = f"SELECT {cols} FROM requests {where} ORDER BY id DESC"

                conn = self.db.connect()
                df = pd.read_sql_query(query, conn, params=tuple(params))

                if len(df.columns) == len(self.HEADERS):
                    df.columns = self.HEADERS

                df.to_csv(path, index=False, encoding='utf-8-sig')
                QMessageBox.information(self, "OK", "Đã xuất!")

            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

