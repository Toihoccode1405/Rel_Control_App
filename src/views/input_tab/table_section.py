"""
kRel - Input Tab Table Section
Phần bảng hiển thị và toolbar với giao diện đẹp
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel,
    QLineEdit, QComboBox, QPushButton, QTableView, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem

from src.styles import BTN_STYLE_BLUE, BTN_STYLE_GREEN, BTN_STYLE_RED, BTN_STYLE_ORANGE, TABLE_STYLE


class TableSection:
    """Helper class để tạo phần bảng và toolbar với giao diện đẹp"""

    TABLE_HEADERS = [
        "STT", "Mã YC", "Ngày YC", "Người YC", "Nhà Máy", "Dự Án", "Giai Đoạn",
        "Mã TB", "Tên TB", "ĐK Test", "Vào KH", "Ra KH", "Vào TT", "Ra TT",
        "Trạng Thái", "DRI", "KQ Cuối"
    ]

    # Map search field index to column index (shifted +1 for STT)
    SEARCH_FIELD_MAP = {
        0: None,  # Tất cả
        1: 1,     # Mã YC
        2: 3,     # Người YC
        3: 4,     # Nhà Máy
        4: 5,     # Dự Án
        5: 7,     # Mã TB
        6: 8,     # Tên TB
        7: 14,    # Trạng Thái
        8: 15     # DRI
    }

    # Toolbar frame style - gradient đẹp
    TOOLBAR_STYLE = """
        QFrame#ToolbarFrame {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, stop:0.5 #F8FBFF, stop:1 #F0F7FF);
            border: 1px solid #BBDEFB;
            border-radius: 8px;
            margin: 2px 0;
        }
    """

    def __init__(self, parent: QWidget):
        self.parent = parent
        self.table = None
        self.cb_filter = None
        self.cb_search_field = None
        self.txt_search = None

    def build_toolbar(self, parent_layout, on_filter, on_search,
                      on_template, on_import, on_export,
                      on_edit=None, on_delete=None):
        """Tạo toolbar với filter và search - giao diện đẹp"""
        frame = QFrame()
        frame.setObjectName("ToolbarFrame")
        frame.setStyleSheet(self.TOOLBAR_STYLE)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # ===== LEFT SECTION: Title + Filter =====
        left_section = QHBoxLayout()
        left_section.setSpacing(8)

        # Title with icon
        title = QLabel("📋")
        title.setStyleSheet("font-size: 16px;")
        left_section.addWidget(title)

        title_text = QLabel("<b>Danh sách yêu cầu</b>")
        title_text.setStyleSheet("color: #1565C0; font-size: 13px;")
        left_section.addWidget(title_text)

        left_section.addWidget(self._create_separator())

        # Filter combo with label
        filter_label = QLabel("📅 Hiển thị:")
        filter_label.setStyleSheet("color: #424242; font-size: 11px;")
        left_section.addWidget(filter_label)

        self.cb_filter = QComboBox()
        self.cb_filter.addItems(["Hôm nay", "7 ngày", "30 ngày", "Tất cả"])
        self.cb_filter.setCurrentIndex(1)
        self.cb_filter.setMinimumWidth(100)
        self.cb_filter.setStyleSheet(self._combo_style())
        self.cb_filter.currentIndexChanged.connect(lambda _: on_filter())
        left_section.addWidget(self.cb_filter)

        layout.addLayout(left_section)

        # ===== CENTER SECTION: Search =====
        layout.addWidget(self._create_separator())

        search_section = QHBoxLayout()
        search_section.setSpacing(6)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 14px;")
        search_section.addWidget(search_icon)

        self.cb_search_field = QComboBox()
        self.cb_search_field.addItems([
            "Tất cả", "Mã YC", "Người YC", "Nhà Máy", "Dự Án",
            "Mã TB", "Tên TB", "Trạng Thái", "DRI"
        ])
        self.cb_search_field.setMinimumWidth(90)
        self.cb_search_field.setStyleSheet(self._combo_style())
        search_section.addWidget(self.cb_search_field)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Nhập từ khóa tìm kiếm...")
        self.txt_search.setMinimumWidth(150)
        self.txt_search.setStyleSheet(self._input_style())
        self.txt_search.textChanged.connect(on_search)
        self.txt_search.returnPressed.connect(on_filter)
        search_section.addWidget(self.txt_search)

        btn_search = QPushButton("Tìm")
        btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search.setStyleSheet(self._btn_style_primary())
        btn_search.clicked.connect(on_filter)
        search_section.addWidget(btn_search)

        layout.addLayout(search_section)

        # ===== RIGHT SECTION: Edit/Delete + Import/Export =====
        layout.addStretch()
        layout.addWidget(self._create_separator())

        # Edit/Delete buttons
        if on_edit:
            btn_edit = QPushButton("✏️ Sửa")
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.setStyleSheet(BTN_STYLE_ORANGE)
            btn_edit.setToolTip("Sửa bản ghi đã chọn")
            btn_edit.clicked.connect(on_edit)
            layout.addWidget(btn_edit)

        if on_delete:
            btn_delete = QPushButton("🗑️ Xóa")
            btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_delete.setStyleSheet(BTN_STYLE_RED)
            btn_delete.setToolTip("Xóa bản ghi đã chọn")
            btn_delete.clicked.connect(on_delete)
            layout.addWidget(btn_delete)

        if on_edit or on_delete:
            layout.addWidget(self._create_separator())

        # Import/Export buttons with better styling
        btn_template = QPushButton("📄 Mẫu")
        btn_template.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_template.setStyleSheet(BTN_STYLE_BLUE)
        btn_template.setToolTip("Tải file mẫu CSV")
        btn_template.clicked.connect(on_template)
        layout.addWidget(btn_template)

        btn_import = QPushButton("📥 Nhập")
        btn_import.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_import.setStyleSheet(BTN_STYLE_GREEN)
        btn_import.setToolTip("Nhập dữ liệu từ CSV")
        btn_import.clicked.connect(on_import)
        layout.addWidget(btn_import)

        btn_export = QPushButton("📤 Xuất")
        btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export.setStyleSheet(BTN_STYLE_BLUE)
        btn_export.setToolTip("Xuất dữ liệu ra CSV")
        btn_export.clicked.connect(on_export)
        layout.addWidget(btn_export)

        parent_layout.addWidget(frame)
    
    def build_table(self, parent_layout):
        """Tạo bảng hiển thị với style đẹp"""
        # Table container với shadow effect
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
            }
        """)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableView()
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)

        table_layout.addWidget(self.table)
        parent_layout.addWidget(table_frame, stretch=2)
        return self.table

    def update_table(self, rows: list):
        """Cập nhật dữ liệu bảng"""
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(self.TABLE_HEADERS)

        for idx, row in enumerate(rows, start=1):
            stt_item = QStandardItem(str(idx))
            stt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            items = [stt_item] + [QStandardItem(str(v) if v else "") for v in row]
            model.appendRow(items)

        self.table.setModel(model)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)

        # Set STT column width
        self.table.setColumnWidth(0, 45)

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

    def get_selected_request_nos(self) -> list:
        """Lấy danh sách request_no đã chọn"""
        selected = []
        model = self.table.model()
        if not model:
            return selected

        selection = self.table.selectionModel()
        if not selection:
            return selected

        for index in selection.selectedRows():
            row = index.row()
            # Cột 1 là Mã YC (sau cột STT)
            item = model.item(row, 1)
            if item:
                selected.append(item.text())

        return selected

    def _create_separator(self):
        """Tạo separator dọc đẹp"""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 transparent, stop:0.2 #BBDEFB,
                stop:0.8 #BBDEFB, stop:1 transparent);
            max-width: 1px;
        """)
        sep.setFixedWidth(1)
        return sep

    def _combo_style(self):
        return """
            QComboBox {
                border: 1px solid #CFD8DC; border-radius: 5px;
                padding: 5px 10px; background-color: #FFFFFF;
                min-height: 26px; font-size: 12px; color: #212121;
            }
            QComboBox:hover {
                border-color: #90CAF9;
                background-color: #FAFEFF;
            }
            QComboBox:focus { border: 1.5px solid #1565C0; }
            QComboBox::drop-down { border: none; width: 24px; }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF; color: #212121;
                selection-background-color: #E3F2FD;
                selection-color: #1565C0;
                border: 1px solid #BBDEFB; border-radius: 4px;
            }
        """

    def _input_style(self):
        return """
            QLineEdit {
                border: 1px solid #CFD8DC; border-radius: 5px;
                padding: 5px 10px; background-color: #FFFFFF;
                min-height: 26px; font-size: 12px; color: #212121;
            }
            QLineEdit:hover {
                border-color: #90CAF9;
                background-color: #FAFEFF;
            }
            QLineEdit:focus { border: 1.5px solid #1565C0; }
            QLineEdit::placeholder { color: #9E9E9E; }
        """

    def _btn_style_primary(self):
        return """
            QPushButton {
                background-color: #1565C0; color: white;
                border: none; border-radius: 5px;
                padding: 6px 14px; font-size: 12px; font-weight: 600;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:pressed { background-color: #0D47A1; }
        """

