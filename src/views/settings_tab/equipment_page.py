"""
kRel - Settings Pages: Equipment
Quản lý thiết bị
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTableView, QDialog,
    QAbstractItemView, QHeaderView, QMessageBox, QStyle
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
from src.views.settings_tab.csv_dialog import CsvDialog, EQUIP_HEADERS

logger = get_logger("equipment_page")


class EquipmentPage(QWidget):
    """Trang quản lý thiết bị"""
    
    def __init__(self):
        super().__init__()
        self.db = get_db()
        self._setup_ui()
        self._load()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header = QHBoxLayout()
        header.setSpacing(12)
        header.addWidget(QLabel("<b style='font-size: 16px; color: #1565C0;'>🔧 QUẢN LÝ THIẾT BỊ</b>"))
        header.addStretch()

        # Buttons
        btn_add = QPushButton("  ➕ Thêm Mới")
        btn_add.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        btn_add.setStyleSheet(BTN_STYLE_BLUE)
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self._add)

        btn_edit = QPushButton("  ✏️ Sửa")
        btn_edit.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        btn_edit.setStyleSheet(BTN_STYLE_GREEN)
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.clicked.connect(self._edit)

        btn_del = QPushButton("  🗑️ Xóa")
        btn_del.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        btn_del.setStyleSheet(BTN_STYLE_RED)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.clicked.connect(self._delete)

        btn_csv = QPushButton("  📤 CSV")
        btn_csv.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DriveFDIcon))
        btn_csv.setStyleSheet(BTN_STYLE_ORANGE)
        btn_csv.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_csv.clicked.connect(self._csv_dialog)

        for btn in [btn_add, btn_edit, btn_del, btn_csv]:
            header.addWidget(btn)

        layout.addLayout(header)
        layout.addSpacing(12)

        # Table
        self.table = QTableView()
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def _load(self, table=None):
        conn = self.db.connect()
        df = pd.read_sql("SELECT * FROM equipment ORDER BY control_no", conn)

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(EQUIP_HEADERS)

        for _, row in df.iterrows():
            items = []
            for x in row:
                items.append(QStandardItem(str(x) if x else ""))
            if len(items) > 1:
                items[1].setData(str(row.iloc[1]), Qt.ItemDataRole.UserRole)
            model.appendRow(items)

        self.table.setModel(model)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)

    def _open_dialog(self, title, data=None):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(500)

        layout = QFormLayout(dialog)
        inputs = []

        for i, header in enumerate(EQUIP_HEADERS):
            led = QLineEdit()
            if data:
                led.setText(str(data[i]))
            layout.addRow(header, led)
            inputs.append(led)

        btn_save = QPushButton("LƯU")
        btn_save.setStyleSheet("background:#2E7D32;color:white;font-weight:bold;padding:8px")
        btn_save.clicked.connect(
            lambda: self._save(inputs, dialog, data[1] if data else None)
        )
        layout.addRow(btn_save)

        dialog.exec()

    def _add(self):
        self._open_dialog("Thêm Thiết Bị Mới")

    def _edit(self):
        index = self.table.currentIndex()
        if not index.isValid():
            return QMessageBox.warning(self, "Lỗi", "Chọn thiết bị cần sửa!")

        row = index.row()
        model = self.table.model()
        data = [model.item(row, c).text() for c in range(10)]
        self._open_dialog("Sửa Thiết Bị", data)

    def _save(self, inputs, dialog, old_control_no=None):
        values = [x.text().strip() for x in inputs]

        if not values[1] or not values[2]:
            return QMessageBox.warning(dialog, "Lỗi", "Mã và Tên là bắt buộc!")

        try:
            with self.db.get_cursor() as cursor:
                if old_control_no:
                    cols = ["factory", "control_no", "name", "spec",
                            "r1", "r2", "r3", "r4", "r5", "remark"]
                    sql = f"UPDATE equipment SET {','.join([c+'=?' for c in cols])} WHERE control_no=?"
                    cursor.execute(sql, values + [old_control_no])
                else:
                    cursor.execute(
                        "INSERT INTO equipment VALUES (?,?,?,?,?,?,?,?,?,?)",
                        values
                    )

            self._load()
            dialog.accept()
            get_event_bus().emit_equipment_changed()
            logger.debug(f"Equipment saved: {values[1]}")

        except Exception as e:
            QMessageBox.warning(dialog, "Lỗi Database", str(e))

    def _delete(self):
        index = self.table.currentIndex()

        if index.isValid() and QMessageBox.question(
            self, "Xóa", "Xóa thiết bị này?"
        ) == QMessageBox.StandardButton.Yes:
            old = self.table.model().item(index.row(), 1).data(Qt.ItemDataRole.UserRole)
            with self.db.get_cursor() as cursor:
                cursor.execute("DELETE FROM equipment WHERE control_no=?", (old,))
            self._load()
            get_event_bus().emit_equipment_changed()
            logger.debug(f"Equipment deleted: {old}")

    def _csv_dialog(self):
        dialog = CsvDialog(self, "equipment", self.db, self._load)
        dialog.exec()

