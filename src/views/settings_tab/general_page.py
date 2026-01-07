"""
kRel - Settings Pages: General Data
Quản lý dữ liệu chung (factory, project, phase, category, status)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QTableView, QPushButton, QAbstractItemView, QHeaderView,
    QInputDialog, QMessageBox, QStyle
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
import pandas as pd

from src.services.database import get_db
from src.services.data_event_bus import get_event_bus
from src.services.logger import get_logger
from src.styles import (
    BTN_STYLE_BLUE, BTN_STYLE_GREEN, BTN_STYLE_RED, BTN_STYLE_ORANGE, TABLE_STYLE
)
from src.views.settings_tab.csv_dialog import CsvDialog

logger = get_logger("general_page")


class GeneralDataPage(QWidget):
    """Trang quản lý dữ liệu chung"""

    SIMPLE_TABLES = {
        "🏭 Nhà máy": "factory",
        "📁 Dự án": "project",
        "📊 Giai đoạn": "phase",
        "📋 Hạng mục": "category",
        "🔄 Trạng thái": "status"
    }

    GROUPBOX_BLUE = """
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

    def __init__(self):
        super().__init__()
        self.db = get_db()
        self.views = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(15)

        for title, table in self.SIMPLE_TABLES.items():
            frame = QGroupBox(title)
            frame.setStyleSheet(self.GROUPBOX_BLUE)

            vl = QVBoxLayout(frame)
            vl.setContentsMargins(5, 15, 5, 5)

            # Buttons
            bl = QGridLayout()
            bl.setSpacing(8)

            btn_add = QPushButton()
            btn_add.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
            btn_add.setToolTip("Thêm")
            btn_add.setStyleSheet(BTN_STYLE_BLUE)
            btn_add.clicked.connect(lambda _, t=table: self._add(t))

            btn_edit = QPushButton()
            btn_edit.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
            btn_edit.setToolTip("Sửa")
            btn_edit.setStyleSheet(BTN_STYLE_GREEN)
            btn_edit.clicked.connect(lambda _, t=table: self._edit(t))

            btn_del = QPushButton()
            btn_del.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
            btn_del.setToolTip("Xóa")
            btn_del.setStyleSheet(BTN_STYLE_RED)
            btn_del.clicked.connect(lambda _, t=table: self._delete(t))

            btn_csv = QPushButton("CSV")
            btn_csv.setStyleSheet(BTN_STYLE_ORANGE)
            btn_csv.clicked.connect(lambda _, t=table: self._csv_dialog(t))

            bl.addWidget(btn_add, 0, 0)
            bl.addWidget(btn_edit, 0, 1)
            bl.addWidget(btn_del, 1, 0)
            bl.addWidget(btn_csv, 1, 1)
            vl.addLayout(bl)

            # Table
            tv = QTableView()
            tv.setStyleSheet(TABLE_STYLE)
            tv.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            tv.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            tv.verticalHeader().hide()
            self.views[table] = tv
            vl.addWidget(tv)

            self._load(table)
            layout.addWidget(frame)

    def _load(self, table):
        conn = self.db.connect()
        df = pd.read_sql(f"SELECT name FROM {table} ORDER BY name", conn)

        model = QStandardItemModel()
        header_name = "Giá trị"
        for k, v in self.SIMPLE_TABLES.items():
            if v == table:
                header_name = k
                break

        model.setHorizontalHeaderLabels([header_name])

        for _, row in df.iterrows():
            item = QStandardItem(str(row.iloc[0]))
            item.setData(str(row.iloc[0]), Qt.ItemDataRole.UserRole)
            model.appendRow([item])

        self.views[table].setModel(model)
        self.views[table].horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

    def _add(self, table):
        text, ok = QInputDialog.getText(self, "Thêm Mới", "Nhập tên:")
        if ok and text:
            try:
                with self.db.get_cursor() as cursor:
                    cursor.execute(
                        f"IF NOT EXISTS (SELECT 1 FROM {table} WHERE name=?) "
                        f"INSERT INTO {table} VALUES (?)",
                        (text, text)
                    )
                self._load(table)
                get_event_bus().emit_lookup_changed(table)
                logger.debug(f"Added to {table}: {text}")
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", str(e))

    def _edit(self, table):
        tv = self.views[table]
        index = tv.currentIndex()

        if not index.isValid():
            return QMessageBox.warning(self, "Chọn", "Vui lòng chọn dòng cần sửa!")

        old = index.data(Qt.ItemDataRole.UserRole)
        new, ok = QInputDialog.getText(self, "Sửa", f"Sửa '{old}' thành:", text=old)

        if ok and new:
            try:
                with self.db.get_cursor() as cursor:
                    cursor.execute(f"UPDATE {table} SET name=? WHERE name=?", (new, old))
                self._load(table)
                get_event_bus().emit_lookup_changed(table)
                logger.debug(f"Updated {table}: {old} -> {new}")
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", str(e))

    def _delete(self, table):
        tv = self.views[table]
        index = tv.currentIndex()

        if index.isValid() and QMessageBox.question(
            self, "Xóa", "Xóa dòng này?"
        ) == QMessageBox.StandardButton.Yes:
            old = index.data(Qt.ItemDataRole.UserRole)
            with self.db.get_cursor() as cursor:
                cursor.execute(f"DELETE FROM {table} WHERE name=?", (old,))
            self._load(table)
            get_event_bus().emit_lookup_changed(table)
            logger.debug(f"Deleted from {table}: {old}")

    def _csv_dialog(self, table):
        dialog = CsvDialog(self, table, self.db, self._load)
        dialog.exec()

