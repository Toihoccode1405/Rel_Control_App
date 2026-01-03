"""
kRel - Main Window
Main application window with tabs
"""
import os
from configparser import ConfigParser

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QToolBar, QLabel,
    QPushButton, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from src.config import APP_TITLE, DEFAULT_LOG_PATH, CONFIG_FILE
from src.styles import BTN_STYLE_RED, TAB_STYLE, TOOLBAR_STYLE


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, user_info: dict):
        super().__init__()
        self.user_info = user_info
        self.is_logout = False
        self.log_path = DEFAULT_LOG_PATH
        
        self._load_config()
        self._setup_ui()
    
    def _load_config(self):
        """Load configuration"""
        if os.path.exists(CONFIG_FILE):
            config = ConfigParser()
            config.read(CONFIG_FILE, encoding="utf-8")
            if config.has_section("system"):
                self.log_path = config["system"].get("log_path", DEFAULT_LOG_PATH)
    
    def _setup_ui(self):
        """Setup UI components"""
        self.setWindowTitle(APP_TITLE)
        
        # Set window size to 90% of screen
        screen = self.screen().availableGeometry()
        width = int(screen.width() * 0.90)
        height = int(screen.height() * 0.90)
        self.setGeometry(
            (screen.width() - width) // 2,
            (screen.height() - height) // 2,
            width, height
        )
        
        # Setup toolbar
        self._setup_toolbar()
        
        # Setup tabs
        self._setup_tabs()
    
    def _setup_toolbar(self):
        """Setup toolbar"""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setStyleSheet(TOOLBAR_STYLE)
        
        # Left spacer
        spacer_left = QWidget()
        spacer_left.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        toolbar.addWidget(spacer_left)
        
        # App title
        lbl_title = QLabel("HỆ THỐNG RELIABILITY")
        lbl_title.setStyleSheet(
            "font-size: 20px; font-weight: 900; color: #1565C0;"
        )
        toolbar.addWidget(lbl_title)
        
        # Right spacer
        spacer_right = QWidget()
        spacer_right.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        toolbar.addWidget(spacer_right)
        
        # User info
        user_name = self.user_info.get("name", "User")
        lbl_user = QLabel(f"Xin chào: <b style='color:#1976D2'>{user_name}</b>")
        lbl_user.setStyleSheet(
            "font-size: 14px; color: #333; margin-right: 15px;"
        )
        toolbar.addWidget(lbl_user)
        
        # Logout button
        btn_logout = QPushButton("Đăng xuất")
        btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_logout.setStyleSheet(BTN_STYLE_RED)
        btn_logout.clicked.connect(self._logout)
        toolbar.addWidget(btn_logout)
    
    def _setup_tabs(self):
        """Setup tab widget with all tabs"""
        tabs = QTabWidget()
        tabs.setStyleSheet(TAB_STYLE)
        
        # Import tabs here to avoid circular imports
        from src.views.input_tab import InputTab
        from src.views.edit_tab import EditTab
        from src.views.report_tab import ReportTab
        from src.views.settings_tab import SettingsTab
        
        # Add tabs
        tabs.addTab(
            InputTab(self.log_path, self.user_info),
            "NHẬP LIỆU"
        )
        tabs.addTab(EditTab(), "DỮ LIỆU")
        tabs.addTab(ReportTab(), "BÁO CÁO")
        tabs.addTab(
            SettingsTab(self.user_info.get("role", "Operator")),
            "CÀI ĐẶT"
        )
        
        self.setCentralWidget(tabs)
    
    def _logout(self):
        """Handle logout"""
        reply = QMessageBox.question(
            self, "Đăng xuất",
            "Bạn có muốn đăng xuất?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.is_logout = True
            self.close()
    
    def closeEvent(self, event):
        """Handle window close"""
        if self.is_logout:
            event.accept()
        else:
            reply = QMessageBox.question(
                self, "Thoát",
                "Thoát chương trình?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()

