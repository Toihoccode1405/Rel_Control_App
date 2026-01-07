"""
kRel - Frozen Table View
Table view with frozen left columns for better UX
"""
from PyQt6.QtWidgets import QTableView, QHeaderView
from PyQt6.QtCore import Qt


class FrozenTableView(QTableView):
    """Table view with frozen left columns"""

    def __init__(self, model, frozen_col_count=4):
        super().__init__()
        self.setModel(model)
        self.frozen_col_count = frozen_col_count

        # Enable multi-row selection
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)

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
        """Update frozen table position and size"""
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
    
    def setColumnWidth(self, column, width):
        """Override to sync frozen table"""
        super().setColumnWidth(column, width)
        if column < self.frozen_col_count:
            self.frozen.setColumnWidth(column, width)
        self.updateFrozenTableGeometry()

