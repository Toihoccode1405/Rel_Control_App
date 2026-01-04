"""
kRel - Loading Overlay Widget
Provides visual feedback during data loading operations
"""
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QFont


class SpinnerWidget(QWidget):
    """Animated spinner widget"""

    def __init__(self, parent=None, size: int = 48, color: str = "#1565C0"):
        super().__init__(parent)
        self._angle = 0
        self._color = QColor(color)
        self._size = size

        self.setFixedSize(size, size)

        # Animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)

    def start(self):
        """Start spinning animation"""
        self._timer.start(50)  # ~20 FPS

    def stop(self):
        """Stop spinning animation"""
        self._timer.stop()

    def _rotate(self):
        """Rotate spinner"""
        self._angle = (self._angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        """Paint spinner"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Center
        cx, cy = self._size // 2, self._size // 2
        radius = (self._size - 8) // 2

        # Draw arcs with varying opacity
        pen = QPen(self._color)
        pen.setWidth(4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        for i in range(8):
            opacity = 1.0 - (i * 0.1)
            color = QColor(self._color)
            color.setAlphaF(max(0.2, opacity))
            pen.setColor(color)
            painter.setPen(pen)

            angle = self._angle - (i * 45)
            start_angle = angle * 16
            span_angle = 30 * 16

            rect = self.rect().adjusted(4, 4, -4, -4)
            painter.drawArc(rect, start_angle, span_angle)


class LoadingOverlay(QWidget):
    """
    Semi-transparent overlay with loading spinner and message.
    Use to indicate loading state on any widget.
    """

    def __init__(self, parent=None, message: str = "Đang tải..."):
        super().__init__(parent)
        self._message = message

        # Make overlay cover parent
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background-color: rgba(255, 255, 255, 0.85);")

        # Layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Spinner
        self.spinner = SpinnerWidget(self, size=48)
        layout.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignCenter)

        # Message label
        self.label = QLabel(message)
        self.label.setStyleSheet("""
            QLabel {
                color: #424242;
                font-size: 14px;
                font-weight: 500;
                padding: 8px;
            }
        """)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        # Opacity effect for fade animation
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0)
        self.setGraphicsEffect(self._opacity)

        # Hide initially
        self.hide()

    def set_message(self, message: str):
        """Update loading message"""
        self._message = message
        self.label.setText(message)

    def show_loading(self, message: str = None):
        """Show overlay with optional message"""
        if message:
            self.set_message(message)

        # Resize to match parent
        if self.parent():
            self.setGeometry(self.parent().rect())

        self.show()
        self.raise_()
        self.spinner.start()

        # Fade in
        self._fade_animation(0, 1, 150)

    def hide_loading(self):
        """Hide overlay with fade out"""
        self.spinner.stop()
        self._fade_animation(1, 0, 150, on_finish=self.hide)

    def _fade_animation(self, start: float, end: float, duration: int, on_finish=None):
        """Animate opacity"""
        anim = QPropertyAnimation(self._opacity, b"opacity", self)
        anim.setDuration(duration)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        if on_finish:
            anim.finished.connect(on_finish)
        anim.start()

    def resizeEvent(self, event):
        """Resize with parent"""
        super().resizeEvent(event)
        if self.parent():
            self.setGeometry(self.parent().rect())


class LoadingMixin:
    """
    Mixin class to add loading overlay functionality to any QWidget.

    Usage:
        class MyTab(QWidget, LoadingMixin):
            def __init__(self):
                super().__init__()
                self.setup_loading()  # Call after UI setup

            def load_data(self):
                self.show_loading("Đang tải dữ liệu...")
                try:
                    # Load data here
                    pass
                finally:
                    self.hide_loading()
    """

    _loading_overlay: LoadingOverlay = None

    def setup_loading(self, message: str = "Đang tải..."):
        """Initialize loading overlay. Call after UI is set up."""
        self._loading_overlay = LoadingOverlay(self, message)

    def show_loading(self, message: str = None):
        """Show loading overlay"""
        if self._loading_overlay is None:
            self.setup_loading()
        self._loading_overlay.show_loading(message)
        # Process events to show overlay immediately
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

    def hide_loading(self):
        """Hide loading overlay"""
        if self._loading_overlay:
            self._loading_overlay.hide_loading()

    def with_loading(self, message: str = "Đang xử lý..."):
        """
        Context manager for loading state.

        Usage:
            with self.with_loading("Đang tải..."):
                # Do work here
                pass
        """
        return LoadingContext(self, message)


class LoadingContext:
    """Context manager for loading state"""

    def __init__(self, widget, message: str):
        self.widget = widget
        self.message = message

    def __enter__(self):
        self.widget.show_loading(self.message)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.widget.hide_loading()
        return False

