"""
kRel - Register Dialog
New user registration dialog
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor

from src.styles import LOGIN_STYLE, BTN_STYLE_BLUE
from src.services.auth import get_auth


class RegisterDialog(QDialog):
    """Registration dialog for new users"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Đăng Ký")
        self.setFixedSize(400, 420)
        self.setStyleSheet(LOGIN_STYLE)

        self.auth = get_auth()
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(45, 35, 45, 35)
        layout.setSpacing(14)

        # Header
        header = QLabel("ĐĂNG KÝ MỚI", objectName="Header")
        layout.addWidget(header, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(8)

        # Username
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Tên đăng nhập")
        self.txt_username.setFixedHeight(44)
        self._set_placeholder_color(self.txt_username)
        layout.addWidget(self.txt_username)

        # Password
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Mật khẩu")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setFixedHeight(44)
        self._set_placeholder_color(self.txt_password)
        layout.addWidget(self.txt_password)

        # Full name
        self.txt_fullname = QLineEdit()
        self.txt_fullname.setPlaceholderText("Họ và Tên")
        self.txt_fullname.setFixedHeight(44)
        self._set_placeholder_color(self.txt_fullname)
        layout.addWidget(self.txt_fullname)

        # Email
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("Email")
        self.txt_email.setFixedHeight(44)
        self._set_placeholder_color(self.txt_email)
        layout.addWidget(self.txt_email)

        layout.addSpacing(10)

        # Register button
        btn_register = QPushButton("ĐĂNG KÝ NGAY")
        btn_register.setFixedHeight(48)
        btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_register.setStyleSheet(BTN_STYLE_BLUE)
        btn_register.clicked.connect(self._do_register)
        layout.addWidget(btn_register)

        layout.addStretch()

    def _set_placeholder_color(self, widget: QLineEdit):
        """Set placeholder text color to gray"""
        palette = widget.palette()
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#999999"))
        widget.setPalette(palette)

    def _do_register(self):
        """Perform registration"""
        username = self.txt_username.text().strip()
        password = self.txt_password.text().strip()
        fullname = self.txt_fullname.text().strip()
        email = self.txt_email.text().strip()

        success, message = self.auth.register(
            username=username,
            password=password,
            fullname=fullname,
            email=email,
            role="Operator"  # Default role for new users
        )

        if success:
            QMessageBox.information(self, "Thành công", message)
            self.accept()
        else:
            QMessageBox.warning(self, "Lỗi", message)

