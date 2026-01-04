"""
kRel - Validated Input Widgets
Custom widgets with inline error display
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, 
    QDateTimeEdit, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor


# Error styles
ERROR_BORDER_STYLE = "border: 2px solid #C62828 !important; background-color: #FFEBEE !important;"
ERROR_LABEL_STYLE = "color: #C62828; font-size: 11px; font-weight: 500; padding: 2px 0 0 4px; margin: 0;"
NORMAL_BORDER_STYLE = "border: 1px solid #CFD8DC; background-color: #FAFAFA;"


class ValidatedField(QWidget):
    """
    Wrapper widget that adds inline error display below any input widget.
    
    Usage:
        field = ValidatedField(QLineEdit(), "request_no", "Mã yêu cầu")
        field.show_error("Không được để trống")
        field.clear_error()
    """
    
    value_changed = pyqtSignal(str)  # Emitted when value changes
    
    def __init__(self, input_widget: QWidget, field_name: str, label: str = None, parent=None):
        super().__init__(parent)
        
        self.field_name = field_name
        self.label = label or field_name
        self.input_widget = input_widget
        self._original_style = input_widget.styleSheet()
        self._has_error = False
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup the layout with input widget and error label"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Add the input widget
        layout.addWidget(self.input_widget)
        
        # Error label (hidden by default)
        self.error_label = QLabel()
        self.error_label.setStyleSheet(ERROR_LABEL_STYLE)
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
    
    def _connect_signals(self):
        """Connect to input widget's change signals"""
        if isinstance(self.input_widget, QLineEdit):
            self.input_widget.textChanged.connect(self._on_value_changed)
        elif isinstance(self.input_widget, QComboBox):
            self.input_widget.currentTextChanged.connect(self._on_value_changed)
        elif isinstance(self.input_widget, QDateTimeEdit):
            self.input_widget.dateTimeChanged.connect(
                lambda dt: self._on_value_changed(dt.toString())
            )
    
    def _on_value_changed(self, value: str):
        """Handle value change - clear error and emit signal"""
        if self._has_error:
            self.clear_error()
        self.value_changed.emit(value)
    
    def show_error(self, message: str):
        """Show error message below the input"""
        self._has_error = True
        self.error_label.setText(f"⚠ {message}")
        self.error_label.show()
        
        # Add error styling to input
        current_style = self.input_widget.styleSheet()
        if ERROR_BORDER_STYLE not in current_style:
            self.input_widget.setStyleSheet(current_style + ERROR_BORDER_STYLE)
    
    def clear_error(self):
        """Clear error message and restore normal styling"""
        self._has_error = False
        self.error_label.hide()
        self.error_label.clear()
        
        # Restore original style
        self.input_widget.setStyleSheet(self._original_style)
    
    def has_error(self) -> bool:
        """Check if field currently has an error"""
        return self._has_error
    
    def get_value(self) -> str:
        """Get current value from input widget"""
        if isinstance(self.input_widget, QLineEdit):
            return self.input_widget.text().strip()
        elif isinstance(self.input_widget, QComboBox):
            return self.input_widget.currentText().strip()
        elif isinstance(self.input_widget, QDateTimeEdit):
            return self.input_widget.dateTime().toString("yyyy-MM-dd HH:mm")
        return ""
    
    def set_value(self, value: str):
        """Set value to input widget"""
        if isinstance(self.input_widget, QLineEdit):
            self.input_widget.setText(value)
        elif isinstance(self.input_widget, QComboBox):
            self.input_widget.setCurrentText(value)
    
    # Proxy common methods to input widget
    def setFocus(self):
        self.input_widget.setFocus()
    
    def setEnabled(self, enabled: bool):
        self.input_widget.setEnabled(enabled)
    
    def setReadOnly(self, readonly: bool):
        if hasattr(self.input_widget, 'setReadOnly'):
            self.input_widget.setReadOnly(readonly)
    
    def setPlaceholderText(self, text: str):
        if hasattr(self.input_widget, 'setPlaceholderText'):
            self.input_widget.setPlaceholderText(text)

