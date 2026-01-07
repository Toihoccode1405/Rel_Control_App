"""
kRel - CSV Dialog
Dialog cho import/export CSV
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
import pandas as pd

from src.services.data_event_bus import get_event_bus
from src.services.logger import get_logger

logger = get_logger("csv_dialog")

# Equipment headers
EQUIP_HEADERS = [
    "Factory", "Control No", "Name", "Spec",
    "Recipe 1", "Recipe 2", "Recipe 3", "Recipe 4", "Recipe 5", "Remark"
]


class CsvDialog(QDialog):
    """Dialog cho thao tác CSV"""
    
    def __init__(self, parent, table: str, db, reload_func):
        super().__init__(parent)
        self.table = table
        self.db = db
        self.reload_func = reload_func
        
        self.setWindowTitle("Thao Tác CSV")
        self.setFixedSize(250, 220)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(QLabel("<b>Lựa chọn?</b>", alignment=Qt.AlignmentFlag.AlignCenter))

        btn1 = QPushButton("1. CSV Mẫu")
        btn1.clicked.connect(lambda: [self._download_template(), self.accept()])

        btn2 = QPushButton("2. Nhập CSV")
        btn2.clicked.connect(lambda: [self._import_csv(), self.accept()])

        btn3 = QPushButton("3. Xuất CSV")
        btn3.clicked.connect(lambda: [self._export_csv(), self.accept()])

        btn4 = QPushButton("4. Huỷ")
        btn4.clicked.connect(self.reject)

        for btn in [btn1, btn2, btn3, btn4]:
            btn.setFixedHeight(35)
            layout.addWidget(btn)

    def _download_template(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Lưu mẫu", f"Mau_{self.table}.csv", "CSV (*.csv)"
        )
        if path:
            headers = EQUIP_HEADERS if self.table == "equipment" else ["Gia_Tri"]
            pd.DataFrame(columns=headers).to_csv(path, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, "OK", "Đã lưu mẫu!")

    def _import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Mở CSV", "", "*.csv")
        if path:
            try:
                df = pd.read_csv(path).fillna("")

                with self.db.get_cursor() as cursor:
                    if self.table == "equipment":
                        data = [tuple(str(x) for x in r[:10]) for _, r in df.iterrows()]
                        for row in data:
                            cursor.execute(
                                "IF NOT EXISTS (SELECT 1 FROM equipment WHERE control_no=?) "
                                "INSERT INTO equipment VALUES (?,?,?,?,?,?,?,?,?,?)",
                                (row[1],) + row
                            )
                        get_event_bus().emit_equipment_changed()
                    else:
                        data = [
                            (str(r.iloc[0]),) for _, r in df.iterrows()
                            if str(r.iloc[0]).strip()
                        ]
                        for row in data:
                            cursor.execute(
                                f"IF NOT EXISTS (SELECT 1 FROM {self.table} WHERE name=?) "
                                f"INSERT INTO {self.table} VALUES (?)",
                                (row[0], row[0])
                            )
                        get_event_bus().emit_lookup_changed(self.table)

                QMessageBox.information(self, "OK", "Nhập xong!")
                self.reload_func(self.table)
                logger.debug(f"CSV imported to {self.table}")

            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Xuất CSV", f"Data_{self.table}.csv", "CSV (*.csv)"
        )
        if path:
            try:
                conn = self.db.connect()
                if self.table == "equipment":
                    df = pd.read_sql("SELECT * FROM equipment", conn)
                    df.columns = EQUIP_HEADERS
                else:
                    df = pd.read_sql(f"SELECT name as 'Gia_Tri' FROM {self.table}", conn)

                df.to_csv(path, index=False, encoding='utf-8-sig')
                QMessageBox.information(self, "OK", "Đã xuất file!")

            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

