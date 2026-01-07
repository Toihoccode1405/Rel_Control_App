"""
kRel - Settings Pages: Users
Quản lý tài khoản người dùng
"""
import hashlib

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableView,
    QAbstractItemView, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
import pandas as pd

from src.services.database import get_db
from src.styles import BTN_STYLE_BLUE, BTN_STYLE_GREEN, BTN_STYLE_RED


class UsersPage(QWidget):
    """Trang quản lý users"""
    
    def __init__(self):
        super().__init__()
        self.db = get_db()
        self._setup_ui()
        self._load_users()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)

        # Table
        self.tbl_users = QTableView()
        self.tbl_users.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_users.setStyleSheet("QTableView { border: 1px solid #E0E0E0; }")
        self.tbl_users.verticalHeader().hide()
        self.tbl_users.clicked.connect(self._on_user_click)
        layout.addWidget(self.tbl_users, 7)

        # Form
        right = QVBoxLayout()
        right.setContentsMargins(10, 0, 0, 0)
        right.addWidget(QLabel("<h3>Thông tin User</h3>"))

        self.u_username = QLineEdit()
        self.u_username.setPlaceholderText("Username")
        self.u_password = QLineEdit()
        self.u_password.setPlaceholderText("Password")
        self.u_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.u_fullname = QLineEdit()
        self.u_fullname.setPlaceholderText("Họ Tên")
        self.u_email = QLineEdit()
        self.u_email.setPlaceholderText("Email")
        self.u_role = QComboBox()
        self.u_role.addItems(["Operator", "Engineer", "Manager", "Super"])

        form = QFormLayout()
        form.setSpacing(10)
        form.addRow("User:", self.u_username)
        form.addRow("Pass:", self.u_password)
        form.addRow("Name:", self.u_fullname)
        form.addRow("Email:", self.u_email)
        form.addRow("Role:", self.u_role)
        right.addLayout(form)

        # Buttons
        hb = QHBoxLayout()
        btn_new = QPushButton("➕ Mới")
        btn_new.setStyleSheet(BTN_STYLE_BLUE)
        btn_new.clicked.connect(self._clear_form)

        btn_save = QPushButton("💾 Lưu")
        btn_save.setStyleSheet(BTN_STYLE_GREEN)
        btn_save.clicked.connect(self._save_user)

        btn_del = QPushButton("🗑️ Xóa")
        btn_del.setStyleSheet(BTN_STYLE_RED)
        btn_del.clicked.connect(self._delete_user)

        hb.addWidget(btn_new)
        hb.addWidget(btn_save)
        hb.addWidget(btn_del)
        right.addLayout(hb)
        right.addStretch()

        layout.addLayout(right, 3)

    def _load_users(self):
        conn = self.db.connect()
        df = pd.read_sql("SELECT username, fullname, role, email FROM users", conn)

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Tài khoản", "Họ Tên", "Vai trò", "Email"])

        for _, row in df.iterrows():
            model.appendRow([QStandardItem(str(x)) for x in row])

        self.tbl_users.setModel(model)
        h = self.tbl_users.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

    def _on_user_click(self, index):
        row = index.row()
        model = self.tbl_users.model()

        self.u_username.setText(model.item(row, 0).text())
        self.u_username.setEnabled(False)
        self.u_fullname.setText(model.item(row, 1).text())
        self.u_role.setCurrentText(model.item(row, 2).text())
        self.u_email.setText(model.item(row, 3).text())
        self.u_password.clear()

    def _clear_form(self):
        self.u_username.clear()
        self.u_username.setEnabled(True)
        self.u_password.clear()
        self.u_fullname.clear()
        self.u_email.clear()

    def _save_user(self):
        username = self.u_username.text()
        if not username:
            return

        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT 1 FROM users WHERE username=?", (username,))
            exists = cursor.fetchone()

            if exists:
                if self.u_password.text():
                    cursor.execute(
                        "UPDATE users SET fullname=?, email=?, role=?, password=? WHERE username=?",
                        (
                            self.u_fullname.text(), self.u_email.text(),
                            self.u_role.currentText(),
                            hashlib.sha256(self.u_password.text().encode()).hexdigest(),
                            username
                        )
                    )
                else:
                    cursor.execute(
                        "UPDATE users SET fullname=?, email=?, role=? WHERE username=?",
                        (self.u_fullname.text(), self.u_email.text(),
                         self.u_role.currentText(), username)
                    )
            else:
                if not self.u_password.text():
                    return QMessageBox.warning(self, "Lỗi", "Nhập mật khẩu!")

                cursor.execute(
                    "INSERT INTO users VALUES (?,?,?,?,?)",
                    (
                        username,
                        hashlib.sha256(self.u_password.text().encode()).hexdigest(),
                        self.u_fullname.text(), self.u_email.text(),
                        self.u_role.currentText()
                    )
                )

        self._load_users()
        self._clear_form()

    def _delete_user(self):
        username = self.u_username.text()
        if username != "admin" and QMessageBox.question(
            self, "?", "Xóa user?"
        ) == QMessageBox.StandardButton.Yes:
            with self.db.get_cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE username=?", (username,))
            self._load_users()
            self._clear_form()

