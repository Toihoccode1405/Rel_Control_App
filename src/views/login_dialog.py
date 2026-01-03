"""
kRel - Login Dialog
User authentication dialog
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor

from src.styles import LOGIN_STYLE, BTN_STYLE_BLUE
from src.services.auth import get_auth
from src.views.register_dialog import RegisterDialog


class LoginDialog(QDialog):
    """Login dialog for user authentication"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Đăng Nhập")
        self.setFixedSize(420, 380)
        self.setStyleSheet(LOGIN_STYLE)

        self.user_info = None
        self.auth = get_auth()

        self._setup_ui()
        self._load_remembered_user()

    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(16)

        # Header
        header = QLabel("HỆ THỐNG RELIABILITY", objectName="Header")
        layout.addWidget(header, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(10)

        # Username input
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Tên tài khoản")
        self.txt_username.setFixedHeight(48)
        self._set_placeholder_color(self.txt_username)
        layout.addWidget(self.txt_username)

        # Password input
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Mật khẩu")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setFixedHeight(48)
        self.txt_password.returnPressed.connect(self._do_login)
        self._set_placeholder_color(self.txt_password)
        layout.addWidget(self.txt_password)

        layout.addSpacing(4)

        # Options row
        options_layout = QHBoxLayout()
        options_layout.setContentsMargins(0, 0, 0, 0)

        btn_register = QPushButton("Đăng ký mới?", objectName="LinkBtn")
        btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_register.clicked.connect(self._show_register)

        self.chk_remember = QCheckBox("Ghi nhớ")
        self.chk_remember.setChecked(True)
        self.chk_remember.setCursor(Qt.CursorShape.PointingHandCursor)

        options_layout.addWidget(btn_register)
        options_layout.addStretch()
        options_layout.addWidget(self.chk_remember)
        layout.addLayout(options_layout)

        layout.addSpacing(8)

        # Login button
        btn_login = QPushButton("ĐĂNG NHẬP")
        btn_login.setFixedHeight(48)
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_login.setStyleSheet(BTN_STYLE_BLUE)
        btn_login.clicked.connect(self._do_login)
        layout.addWidget(btn_login)

        layout.addStretch()

    def _set_placeholder_color(self, widget: QLineEdit):
        """Set placeholder text color to gray"""
        palette = widget.palette()
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#999999"))
        widget.setPalette(palette)

    def _load_remembered_user(self):
        """Load remembered username if any"""
        remembered = self.auth.get_remembered_username()
        if remembered:
            self.txt_username.setText(remembered)
            self.txt_password.setFocus()

    def _do_login(self):
        """Perform login"""
        username = self.txt_username.text().strip()
        password = self.txt_password.text().strip()

        success, user, message = self.auth.login(username, password)

        if success:
            # Save remember me preference
            self.auth.save_remember_me(username, self.chk_remember.isChecked())

            # Store user info for main window
            self.user_info = {
                "name": user.fullname or user.username,
                "role": user.role,
                "username": user.username
            }
            self.accept()
        else:
            QMessageBox.warning(self, "Lỗi", message)

    def _show_register(self):
        """Show registration dialog"""
        dialog = RegisterDialog(self)
        dialog.exec()

