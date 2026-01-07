"""
kRel - Settings Tab (Refactored)
Tab cài đặt hệ thống - đã tách thành modules nhỏ
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QListWidget, QListWidgetItem, QStackedWidget
)

from src.styles import SETTINGS_MENU_STYLE

from src.views.settings_tab.config_page import ConfigPage
from src.views.settings_tab.users_page import UsersPage
from src.views.settings_tab.general_page import GeneralDataPage
from src.views.settings_tab.equipment_page import EquipmentPage


class SettingsTab(QWidget):
    """Tab cài đặt và quản lý hệ thống"""

    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self.role = role
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left menu
        self.menu = QListWidget()
        self.menu.setFixedWidth(260)
        self.menu.setStyleSheet(SETTINGS_MENU_STYLE)

        # Stack widget for pages
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QWidget { background-color: #F8FAFC; }")

        # Add pages based on role
        if self.role == "Super":
            self._add_page("👤 Quản lý tài khoản", UsersPage())

        self._add_page("⚙️ Cấu hình hệ thống", ConfigPage())
        self._add_page("📦 Dữ liệu chung", GeneralDataPage())
        self._add_page("🔧 Quản lý thiết bị", EquipmentPage())

        self.menu.currentRowChanged.connect(self.stack.setCurrentIndex)

        main_layout.addWidget(self.menu)
        main_layout.addWidget(self.stack)

        if self.menu.count() > 0:
            self.menu.setCurrentRow(0)

    def _add_page(self, title: str, widget: QWidget):
        """Add a page to the stack"""
        self.stack.addWidget(widget)
        self.menu.addItem(QListWidgetItem(title))

