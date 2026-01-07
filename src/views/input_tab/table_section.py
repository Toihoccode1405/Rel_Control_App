"""
kRel - Input Tab Table Section
Phần bảng hiển thị và toolbar
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel,
    QLineEdit, QComboBox, QPushButton, QTableView, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem

from src.styles import BTN_STYLE_BLUE, TABLE_STYLE, TOOLBAR_FRAME_STYLE


class TableSection:
    """Helper class để tạo phần bảng và toolbar"""
    
    TABLE_HEADERS = [
        "Mã YC", "Ngày YC", "Người YC", "Nhà Máy", "Dự Án", "Giai Đoạn",
        "Mã TB", "Tên TB", "ĐK Test", "Vào KH", "Ra KH", "Vào TT", "Ra TT",
        "Trạng Thái", "DRI", "KQ Cuối"
    ]
    
    # Map search field index to column index
    SEARCH_FIELD_MAP = {
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
    
    def __init__(self, parent: QWidget):
        self.parent = parent
        self.table = None
        self.cb_filter = None
        self.cb_search_field = None
        self.txt_search = None
    
    def build_toolbar(self, parent_layout, on_filter, on_search, 
                      on_template, on_import, on_export):
        """Tạo toolbar với filter và search"""
        frame = QFrame()
        frame.setStyleSheet(TOOLBAR_FRAME_STYLE)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # Title
        layout.addWidget(QLabel("<b style='color: #1565C0;'>📋 Danh sách yêu cầu:</b>"))
        
        # Filter combo
        layout.addWidget(QLabel("📅"))
        self.cb_filter = QComboBox()
        self.cb_filter.addItems(["Hôm nay", "7 ngày", "30 ngày", "Tất cả"])
        self.cb_filter.setCurrentIndex(1)
        self.cb_filter.setMinimumWidth(90)
        self.cb_filter.setStyleSheet(self._combo_style())
        self.cb_filter.currentIndexChanged.connect(lambda _: on_filter())
        layout.addWidget(self.cb_filter)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Search section
        layout.addWidget(QLabel("<b style='color: #1565C0;'>🔍 Tìm:</b>"))
        
        self.cb_search_field = QComboBox()
        self.cb_search_field.addItems([
            "Tất cả", "Mã YC", "Người YC", "Nhà Máy", "Dự Án",
            "Mã TB", "Tên TB", "Trạng Thái", "DRI"
        ])
        self.cb_search_field.setMinimumWidth(80)
        self.cb_search_field.setStyleSheet(self._combo_style())
        layout.addWidget(self.cb_search_field)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Nhập từ khóa...")
        self.txt_search.setMinimumWidth(120)
        self.txt_search.setStyleSheet(self._input_style())
        self.txt_search.textChanged.connect(on_search)
        self.txt_search.returnPressed.connect(on_filter)
        layout.addWidget(self.txt_search)
        
        btn_search = QPushButton("🔍 Tìm")
        btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search.setStyleSheet(BTN_STYLE_BLUE)
        btn_search.clicked.connect(on_filter)
        layout.addWidget(btn_search)
        
        layout.addStretch()
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Import/Export buttons
        for text, callback in [("📄 Mẫu", on_template), 
                                ("📥 Nhập", on_import), 
                                ("📤 Xuất", on_export)]:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(BTN_STYLE_BLUE)
            btn.clicked.connect(callback)
            layout.addWidget(btn)
        
        parent_layout.addWidget(frame)
    
    def build_table(self, parent_layout):
        """Tạo bảng hiển thị"""
        self.table = QTableView()
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.setMinimumHeight(280)
        parent_layout.addWidget(self.table, stretch=2)
        return self.table

    def update_table(self, rows: list):
        """Cập nhật dữ liệu bảng"""
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(self.TABLE_HEADERS)
        
        for row in rows:
            items = [QStandardItem(str(v) if v else "") for v in row]
            model.appendRow(items)
        
        self.table.setModel(model)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
    
    def filter_table(self, search_text: str):
        """Lọc bảng theo từ khóa"""
        model = self.table.model()
        if not model:
            return
        
        text = search_text.strip().lower()
        field_idx = self.cb_search_field.currentIndex()
        target_col = self.SEARCH_FIELD_MAP.get(field_idx)
        
        for row in range(model.rowCount()):
            match = False
            
            if target_col is None:
                # Search all columns
                for col in range(model.columnCount()):
                    item = model.item(row, col)
                    if item and text in item.text().lower():
                        match = True
                        break
            else:
                # Search specific column
                item = model.item(row, target_col)
                if item and text in item.text().lower():
                    match = True
            
            self.table.setRowHidden(row, not match)
    
    def get_filter_index(self) -> int:
        """Lấy index của filter hiện tại"""
        return self.cb_filter.currentIndex() if self.cb_filter else 1
    
    def _create_separator(self):
        """Tạo separator dọc"""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("background-color: #CFD8DC; max-width: 1px;")
        sep.setFixedWidth(1)
        return sep
    
    def _combo_style(self):
        return """
            QComboBox {
                border: 1px solid #CFD8DC; border-radius: 4px;
                padding: 4px 8px; background-color: #FFFFFF;
                min-height: 24px; font-size: 11px;
            }
            QComboBox:hover { border-color: #90CAF9; }
            QComboBox:focus { border: 1.5px solid #1565C0; }
        """
    
    def _input_style(self):
        return """
            QLineEdit {
                border: 1px solid #CFD8DC; border-radius: 4px;
                padding: 4px 8px; background-color: #FFFFFF;
                min-height: 24px; font-size: 11px;
            }
            QLineEdit:hover { border-color: #90CAF9; }
            QLineEdit:focus { border: 1.5px solid #1565C0; }
        """

