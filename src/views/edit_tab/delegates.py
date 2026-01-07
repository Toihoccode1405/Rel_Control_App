"""
kRel - Table Delegates
Các delegate cho table editing (combo, date, recipe...)
"""
from PyQt6.QtWidgets import QStyledItemDelegate, QComboBox, QDateTimeEdit
from PyQt6.QtCore import Qt, QDateTime

from src.services.database import get_db


class ComboDelegate(QStyledItemDelegate):
    """Delegate for combo box columns"""
    
    def __init__(self, parent, data_source: dict):
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

    def __init__(self, parent, equip_col: int = 18):
        super().__init__(parent)
        self.equip_col = equip_col

    def createEditor(self, parent, option, index):
        model = index.model()
        equip_idx = model.index(index.row(), self.equip_col)
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

