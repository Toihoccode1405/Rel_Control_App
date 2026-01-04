"""
kRel - Edit Tab
Data editing and management tab with frozen columns support
"""
import os
import shutil
from configparser import ConfigParser

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QComboBox, QTableView, QHeaderView,
    QDateTimeEdit, QFileDialog, QMessageBox, QStyle,
    QStyledItemDelegate
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor
import pandas as pd

from src.config import CONFIG_FILE, DEFAULT_LOG_PATH
from src.services.database import get_db
from src.services.logger import get_logger, log_audit
from src.services.data_event_bus import get_event_bus
from src.styles import (
    BTN_STYLE_BLUE, BTN_STYLE_GREEN_SOLID, BTN_STYLE_ORANGE_SOLID,
    TABLE_STYLE, TOOLBAR_FRAME_STYLE, FILTER_FRAME_STYLE
)
from src.widgets.loading_overlay import LoadingMixin

# Module logger
logger = get_logger("edit_tab")


# Status colors for row highlighting
STATUS_COLORS = {
    "Done": "#E8F5E9", "Finish": "#E8F5E9",
    "Ongoing": "#E3F2FD", "Running": "#E3F2FD",
    "Pending": "#FFFDE7", "Wait": "#FFFDE7",
    "Stop": "#FFEBEE", "Fail": "#FFEBEE",
    "Cancel": "#F3E5F5", "Not Start": "#FAFAFA"
}
DEFAULT_COLOR = "#FFFFFF"

# Database columns to SELECT (excluding 'detail' field)
DB_SELECT_COLS = [
    "id", "request_no", "request_date", "requester", "factory", "project",
    "phase", "category", "qty", "cos", "cos_res", "hcross",
    "xhatch_res", "xcross", "xsection_res", "func_test", "func_res",
    "final_res", "equip_no", "equip_name", "test_condition", "plan_start",
    "plan_end", "status", "dri", "actual_start", "actual_end", "logfile",
    "log_link", "note"
]


class ComboDelegate(QStyledItemDelegate):
    """Delegate for combo box columns"""
    
    def __init__(self, parent, data_source):
        super().__init__(parent)
        self.data_source = data_source
    
    def createEditor(self, parent, option, index):
        if index.column() in self.data_source:
            combo = QComboBox(parent)
            combo.setEditable(True)
            combo.addItems(self.data_source[index.column()])
            return combo
        return super().createEditor(parent, option, index)
    
    def setEditorData(self, editor, index):
        if isinstance(editor, QComboBox):
            idx = editor.findText(index.model().data(index, Qt.ItemDataRole.EditRole))
            if idx >= 0:
                editor.setCurrentIndex(idx)
        else:
            super().setEditorData(editor, index)
    
    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)


class DateDelegate(QStyledItemDelegate):
    """Delegate for date columns"""
    
    def createEditor(self, parent, option, index):
        dt = QDateTimeEdit(parent)
        dt.setCalendarPopup(True)
        dt.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        return dt
    
    def setEditorData(self, editor, index):
        val = index.model().data(index, Qt.ItemDataRole.EditRole)
        if val and isinstance(val, str) and val.strip():
            q = QDateTime.fromString(val, "yyyy-MM-dd HH:mm:ss")
            if q.isValid():
                editor.setDateTime(q)
            else:
                editor.setDateTime(QDateTime.currentDateTime())
        else:
            editor.setDateTime(QDateTime.currentDateTime())
    
    def setModelData(self, editor, model, index):
        model.setData(
            index,
            editor.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            Qt.ItemDataRole.EditRole
        )


class RecipeDelegate(QStyledItemDelegate):
    """Delegate for recipe/test condition column"""

    def createEditor(self, parent, option, index):
        model = index.model()
        equip_idx = model.index(index.row(), 18)  # equip_no column
        equip_no = model.data(equip_idx, Qt.ItemDataRole.DisplayRole)
        
        combo = QComboBox(parent)
        combo.setEditable(True)
        
        if equip_no:
            try:
                db = get_db()
                rows = db.fetch_all(
                    "SELECT r1, r2, r3, r4, r5 FROM equipment WHERE control_no=?",
                    (str(equip_no),)
                )
                if rows:
                    combo.addItems([str(x) for x in rows[0] if x and str(x).strip()])
            except Exception:
                pass
        
        return combo
    
    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)


class NoEditDelegate(QStyledItemDelegate):
    """Delegate that disables editing"""
    
    def createEditor(self, parent, option, index):
        return None


class FrozenTableView(QTableView):
    """Table view with frozen left columns"""
    
    def __init__(self, model, frozen_col_count=4):
        super().__init__()
        self.setModel(model)
        self.frozen_col_count = frozen_col_count

        # Create frozen view
        self.frozen = QTableView(self)
        self.frozen.setModel(model)
        self.frozen.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.frozen.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )
        self.frozen.setStyleSheet("""
            QTableView {
                border: none;
                background-color: #F0F7FF;
                selection-background-color: #BBDEFB;
                border-right: 2px solid #1565C0;
            }
            QTableView::item {
                padding: 6px 8px;
                border-bottom: 1px solid #E3F2FD;
            }
            QHeaderView::section {
                background-color: #E3F2FD;
                color: #1565C0;
                font-weight: 600;
                border: none;
                border-right: 1px solid #BBDEFB;
                border-bottom: 2px solid #1565C0;
                padding: 8px 10px;
            }
        """)
        
        # Setup headers
        self.verticalHeader().setFixedWidth(40)
        self.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frozen.verticalHeader().hide()
        
        # Stack views
        self.viewport().stackUnder(self.frozen)
        self.frozen.setSelectionModel(self.selectionModel())
        
        # Hide/show columns
        for col in range(model.columnCount()):
            if col < frozen_col_count:
                self.setColumnHidden(col, True)
            else:
                self.frozen.setColumnHidden(col, True)
        
        # Sync scrolling
        self.verticalScrollBar().valueChanged.connect(
            self.frozen.verticalScrollBar().setValue
        )
        self.frozen.verticalScrollBar().valueChanged.connect(
            self.verticalScrollBar().setValue
        )
        
        self.updateFrozenTableGeometry()
    
    def updateFrozenTableGeometry(self):
        w = sum([
            self.columnWidth(i)
            for i in range(self.frozen_col_count)
            if not self.frozen.isColumnHidden(i)
        ])
        self.frozen.setGeometry(
            self.verticalHeader().width() + self.frameWidth(),
            self.frameWidth(),
            w,
            self.viewport().height() + self.horizontalHeader().height()
        )
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateFrozenTableGeometry()


class EditTab(QWidget, LoadingMixin):
    """Data editing tab with full CRUD support"""

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
        self.log_path = DEFAULT_LOG_PATH
        self._load_config()

        self.table = None
        self.model = None

        self._setup_ui()
        self.setup_loading()  # Initialize loading overlay
        self._init_filter_list()
        self._load_data()
        self._connect_events()

    def _connect_events(self):
        """Connect to DataEventBus events for realtime updates"""
        event_bus = get_event_bus()

        # Listen for request changes
        event_bus.request_created.connect(self._on_request_changed)
        event_bus.request_updated.connect(self._on_request_changed)
        event_bus.request_deleted.connect(self._on_request_changed)

        # Listen for lookup data changes (to refresh filter combos)
        event_bus.lookup_changed.connect(self._on_lookup_changed)

        # Listen for equipment changes
        event_bus.equipment_changed.connect(self._on_equipment_changed)

        logger.debug("EditTab connected to DataEventBus")

    def _on_request_changed(self, request_no: str = None):
        """Handle request data changes - refresh table"""
        logger.debug(f"Request changed event received: {request_no}")
        self._load_data()

    def _on_lookup_changed(self, table_name: str):
        """Handle lookup data changes - reload filter combos"""
        # Reload filter combos
        self._init_filter_list()
        logger.debug(f"Lookup changed, reloaded filters: {table_name}")

    def _on_equipment_changed(self):
        """Handle equipment data changes"""
        self._init_filter_list()
        logger.debug("Equipment changed, reloaded filters")

    def _load_config(self):
        """Load configuration"""
        if os.path.exists(CONFIG_FILE):
            cfg = ConfigParser()
            cfg.read(CONFIG_FILE, encoding="utf-8")
            if cfg.has_section("system"):
                self.log_path = cfg["system"].get("log_path", DEFAULT_LOG_PATH)

    def _setup_ui(self):
        """Setup UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(TOOLBAR_FRAME_STYLE)

        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(16, 12, 16, 12)
        tl.setSpacing(12)

        # Title
        title_lbl = QLabel("<b style='font-size: 16px; color: #1565C0;'>📊 QUẢN LÝ DỮ LIỆU</b>")
        tl.addWidget(title_lbl)
        tl.addSpacing(16)

        # Refresh button
        btn_refresh = QPushButton("  🔄 Làm mới")
        btn_refresh.setIcon(self.style().standardIcon(
            QStyle.StandardPixmap.SP_BrowserReload
        ))
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.clicked.connect(self._refresh)
        btn_refresh.setStyleSheet(BTN_STYLE_BLUE)
        tl.addWidget(btn_refresh)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet("color: #E0E0E0;")
        tl.addWidget(sep1)

        # Filter section
        filter_lbl = QLabel("<b>🔍 Lọc:</b>")
        filter_lbl.setStyleSheet("color: #424242;")
        tl.addWidget(filter_lbl)

        # Status filter
        self.cb_filter_status = QComboBox()
        self.cb_filter_status.addItem("Tất cả Trạng thái")
        self.cb_filter_status.setMinimumWidth(160)
        self.cb_filter_status.setStyleSheet("""
            QComboBox {
                border: 1px solid #CFD8DC;
                border-radius: 6px;
                padding: 6px 10px;
                background-color: #FFFFFF;
                min-height: 32px;
            }
            QComboBox:hover { border-color: #90CAF9; background-color: #FAFEFF; }
            QComboBox:focus { border: 2px solid #1565C0; }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #212121;
                selection-background-color: #E3F2FD;
                selection-color: #1565C0;
                border: 1px solid #BBDEFB;
            }
        """)
        self.cb_filter_status.currentTextChanged.connect(self._load_data)
        tl.addWidget(self.cb_filter_status)

        # Result filter
        self.cb_filter_result = QComboBox()
        self.cb_filter_result.addItems(["Tất cả KQ", "-", "Pass", "Fail", "Waiver"])
        self.cb_filter_result.setMinimumWidth(130)
        self.cb_filter_result.setStyleSheet("""
            QComboBox {
                border: 1px solid #CFD8DC;
                border-radius: 6px;
                padding: 6px 10px;
                background-color: #FFFFFF;
                min-height: 32px;
            }
            QComboBox:hover { border-color: #90CAF9; background-color: #FAFEFF; }
            QComboBox:focus { border: 2px solid #1565C0; }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #212121;
                selection-background-color: #E3F2FD;
                selection-color: #1565C0;
                border: 1px solid #BBDEFB;
            }
        """)
        self.cb_filter_result.currentTextChanged.connect(self._load_data)
        tl.addWidget(self.cb_filter_result)

        tl.addStretch()

        # Save button
        btn_save = QPushButton("  💾 Lưu thay đổi")
        btn_save.setIcon(self.style().standardIcon(
            QStyle.StandardPixmap.SP_DialogSaveButton
        ))
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self._save)
        btn_save.setStyleSheet(BTN_STYLE_GREEN_SOLID)
        tl.addWidget(btn_save)

        # Export button
        btn_export = QPushButton("  📤 Xuất CSV")
        btn_export.setIcon(self.style().standardIcon(
            QStyle.StandardPixmap.SP_DriveFDIcon
        ))
        btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export.clicked.connect(self._export_csv)
        btn_export.setStyleSheet(BTN_STYLE_ORANGE_SOLID)
        tl.addWidget(btn_export)

        main_layout.addWidget(toolbar)

        # Table container
        self.table_container = QVBoxLayout()
        self.table_container.setSpacing(0)
        main_layout.addLayout(self.table_container)

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
        conditions = []
        params = []

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
                if not val.strip():
                    item.setBackground(lemon_bg)
                else:
                    item.setBackground(row_bg)
                items.append(item)

            self.model.appendRow(items)

        self.model.itemChanged.connect(self._on_item_changed)

        # Create table
        if self.table:
            self.table_container.removeWidget(self.table)
            self.table.deleteLater()

        self.table = FrozenTableView(self.model, frozen_col_count=4)
        self.table.doubleClicked.connect(self._handle_double_click)

        # Set delegates
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

        # Resize columns
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for i in range(4):
            width = 120 if i > 0 else 50
            self.table.setColumnWidth(i, width)
            self.table.frozen.setColumnWidth(i, width)
        h.setSectionResizeMode(29, QHeaderView.ResizeMode.Stretch)

        self.table_container.addWidget(self.table)

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

                    QMessageBox.information(
                        self, "OK", f"Đã tải: {os.path.basename(fname)}"
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi", str(e))

    def _save(self):
        """Save all changes"""
        try:
            updated_count = 0
            with self.db.get_cursor() as cursor:
                for r in range(self.model.rowCount()):
                    # Get row data
                    row_data = []
                    for c in range(self.model.columnCount()):
                        item = self.model.item(r, c)
                        row_data.append(item.text() if item else "")

                    # row_data[0] is ID
                    record_id = row_data[0]
                    if not record_id:
                        continue

                    # Build UPDATE query (without detail field)
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

            # Emit event for other tabs (InputTab's recent list may need refresh)
            if updated_count > 0:
                get_event_bus().emit_request_updated("batch")

            QMessageBox.information(self, "Thành công", "Đã lưu!")
            self._load_data()

        except Exception as e:
            logger.error(f"Failed to save data: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Lỗi", str(e))

    def _export_csv(self):
        """Export data to CSV"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Xuất", "kRel_Data.csv", "CSV (*.csv)"
        )

        if path:
            try:
                # Build query
                conditions = []
                params = []

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

