"""
kRel - Table Delegates
Custom delegates for QTableView editing
"""
from PyQt6.QtWidgets import (
    QStyledItemDelegate, QComboBox, QDateTimeEdit
)
from PyQt6.QtCore import Qt, QDateTime

from src.services.database import get_db


class ComboDelegate(QStyledItemDelegate):
    """Delegate for combo box editing in table cells"""
    
    def __init__(self, parent, data_source: dict):
        """
        Args:
            parent: Parent widget
            data_source: Dict mapping column index to list of values
        """
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
            value = index.model().data(index, Qt.ItemDataRole.EditRole)
            idx = editor.findText(str(value) if value else "")
            if idx >= 0:
                editor.setCurrentIndex(idx)
            else:
                editor.setCurrentText(str(value) if value else "")
        else:
            super().setEditorData(editor, index)
    
    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)


class DateDelegate(QStyledItemDelegate):
    """Delegate for date/time editing in table cells"""
    
    def __init__(self, parent=None, format_str: str = "yyyy-MM-dd HH:mm"):
        super().__init__(parent)
        self.format_str = format_str
    
    def createEditor(self, parent, option, index):
        editor = QDateTimeEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat(self.format_str)
        return editor
    
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        if value and isinstance(value, str) and value.strip():
            # Try parsing with different formats
            for fmt in ["yyyy-MM-dd HH:mm:ss", "yyyy-MM-dd HH:mm", "yyyy-MM-dd"]:
                qdt = QDateTime.fromString(value.strip(), fmt)
                if qdt.isValid():
                    editor.setDateTime(qdt)
                    return
        # Default to current datetime if empty or invalid
        editor.setDateTime(QDateTime.currentDateTime())
    
    def setModelData(self, editor, model, index):
        model.setData(
            index,
            editor.dateTime().toString(self.format_str),
            Qt.ItemDataRole.EditRole
        )


class RecipeDelegate(QStyledItemDelegate):
    """Delegate for recipe selection based on equipment"""
    
    def __init__(self, parent, equip_column: int = 19):
        """
        Args:
            parent: Parent widget
            equip_column: Column index containing equipment code
        """
        super().__init__(parent)
        self.equip_column = equip_column
    
    def createEditor(self, parent, option, index):
        model = index.model()
        equip_idx = model.index(index.row(), self.equip_column)
        equip_no = model.data(equip_idx, Qt.ItemDataRole.DisplayRole)
        
        combo = QComboBox(parent)
        combo.setEditable(True)
        
        if equip_no:
            try:
                db = get_db()
                row = db.fetch_one(
                    "SELECT r1, r2, r3, r4, r5 FROM equipment WHERE control_no = ?",
                    (str(equip_no),)
                )
                if row:
                    recipes = [str(x) for x in row if x and str(x).strip()]
                    combo.addItems(recipes)
            except Exception:
                pass
        
        return combo
    
    def setEditorData(self, editor, index):
        if isinstance(editor, QComboBox):
            value = index.model().data(index, Qt.ItemDataRole.EditRole)
            idx = editor.findText(str(value) if value else "")
            if idx >= 0:
                editor.setCurrentIndex(idx)
    
    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)


class NoEditDelegate(QStyledItemDelegate):
    """Delegate that prevents editing (read-only cells)"""
    
    def createEditor(self, parent, option, index):
        return None  # No editor = no editing


class ResultDelegate(QStyledItemDelegate):
    """Delegate for Pass/Fail result selection"""
    
    OPTIONS = ["-", "Pass", "Fail", "Waiver"]
    
    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(self.OPTIONS)
        return combo
    
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        idx = editor.findText(str(value) if value else "-")
        editor.setCurrentIndex(idx if idx >= 0 else 0)
    
    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)

