"""
kRel - Frozen Table View
Table view with frozen (pinned) columns on the left
"""
from PyQt6.QtWidgets import QTableView, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel


class FrozenTableView(QTableView):
    """
    Table view with frozen columns on the left side.
    Useful for keeping ID/key columns visible while scrolling horizontally.
    """
    
    def __init__(self, model: QStandardItemModel, frozen_col_count: int = 4):
        """
        Args:
            model: Data model
            frozen_col_count: Number of columns to freeze (from left)
        """
        super().__init__()
        self.setModel(model)
        self.frozen_col_count = frozen_col_count
        
        # Create frozen table overlay
        self.frozen = QTableView(self)
        self.frozen.setModel(model)
        self.frozen.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Style frozen table
        self.frozen.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )
        self.frozen.setStyleSheet("""
            QTableView {
                border: none;
                background-color: #f9f9f9;
                selection-background-color: #90caf9;
                border-right: 2px solid #ccc;
            }
        """)
        
        # Configure headers
        self.verticalHeader().setFixedWidth(40)
        self.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frozen.verticalHeader().hide()
        
        # Stack frozen table under main viewport
        self.viewport().stackUnder(self.frozen)
        
        # Share selection model
        self.frozen.setSelectionModel(self.selectionModel())
        
        # Configure column visibility
        for col in range(model.columnCount()):
            if col < frozen_col_count:
                # Hide in main table
                self.setColumnHidden(col, True)
            else:
                # Hide in frozen table
                self.frozen.setColumnHidden(col, True)
        
        # Sync vertical scrolling
        self.verticalScrollBar().valueChanged.connect(
            self.frozen.verticalScrollBar().setValue
        )
        self.frozen.verticalScrollBar().valueChanged.connect(
            self.verticalScrollBar().setValue
        )
        
        self.updateFrozenTableGeometry()
    
    def updateFrozenTableGeometry(self):
        """Update frozen table position and size"""
        width = sum([
            self.columnWidth(i) 
            for i in range(self.frozen_col_count) 
            if not self.frozen.isColumnHidden(i)
        ])
        
        self.frozen.setGeometry(
            self.verticalHeader().width() + self.frameWidth(),
            self.frameWidth(),
            width,
            self.viewport().height() + self.horizontalHeader().height()
        )
    
    def resizeEvent(self, event):
        """Handle resize to update frozen table"""
        super().resizeEvent(event)
        self.updateFrozenTableGeometry()
    
    def scrollTo(self, index, hint=QTableView.ScrollHint.EnsureVisible):
        """Override to handle frozen columns"""
        if index.column() < self.frozen_col_count:
            # Don't scroll for frozen columns
            return
        super().scrollTo(index, hint)
    
    def setColumnWidth(self, column: int, width: int):
        """Set column width for both tables"""
        super().setColumnWidth(column, width)
        self.frozen.setColumnWidth(column, width)
        self.updateFrozenTableGeometry()
    
    def setItemDelegateForColumn(self, column: int, delegate):
        """Set delegate for both tables"""
        super().setItemDelegateForColumn(column, delegate)
        if column < self.frozen_col_count:
            self.frozen.setItemDelegateForColumn(column, delegate)

