"""
kRel - Main Window
Main application window with tabs

Performance Features:
- Lazy loading: Tabs are only initialized when first accessed
- Reduced startup time by deferring heavy tab initialization
"""
import os
import logging
from configparser import ConfigParser
from typing import Dict, Optional, Callable

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QToolBar, QLabel,
    QPushButton, QSizePolicy, QMessageBox, QVBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from src.config import APP_TITLE, DEFAULT_LOG_PATH, CONFIG_FILE
from src.styles import BTN_STYLE_RED, TAB_STYLE, TOOLBAR_STYLE

# Module logger
logger = logging.getLogger("kRel.main_window")


class LazyTabWidget(QWidget):
    """
    Placeholder widget for lazy-loaded tabs.

    The actual tab content is only created when the tab is first selected.
    """

    def __init__(self, factory: Callable[[], QWidget], parent=None):
        super().__init__(parent)
        self._factory = factory
        self._actual_widget: Optional[QWidget] = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        # Show loading placeholder
        self._placeholder = QLabel("Đang tải...")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("font-size: 16px; color: #666;")
        self._layout.addWidget(self._placeholder)

    def ensure_loaded(self):
        """Ensure the actual widget is loaded"""
        if self._actual_widget is None:
            logger.debug(f"Lazy loading tab: {self._factory}")

            # Remove placeholder
            self._placeholder.setParent(None)
            self._placeholder.deleteLater()

            # Create actual widget
            self._actual_widget = self._factory()
            self._layout.addWidget(self._actual_widget)

            logger.debug("Tab loaded successfully")

    @property
    def is_loaded(self) -> bool:
        """Check if the actual widget has been loaded"""
        return self._actual_widget is not None


class MainWindow(QMainWindow):
    """
    Main application window with lazy-loaded tabs.

    Features:
    - Lazy loading: Only InputTab is loaded at startup
    - Other tabs are loaded on first access
    - Improved startup performance
    """

    def __init__(self, user_info: dict):
        super().__init__()
        self.user_info = user_info
        self.is_logout = False
        self.log_path = DEFAULT_LOG_PATH
        self._lazy_tabs: Dict[int, LazyTabWidget] = {}

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
        """
        Setup tab widget with lazy-loaded tabs.

        Only InputTab is loaded immediately (most commonly used).
        Other tabs are loaded on first access for faster startup.
        """
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)

        # Import tabs here to avoid circular imports
        from src.views.input_tab import InputTab

        # Tab 0: InputTab - Load immediately (primary tab)
        self.tabs.addTab(
            InputTab(self.log_path, self.user_info),
            "NHẬP LIỆU"
        )

        # Tab 1: EditTab - Lazy load
        edit_tab = LazyTabWidget(self._create_edit_tab)
        self._lazy_tabs[1] = edit_tab
        self.tabs.addTab(edit_tab, "DỮ LIỆU")

        # Tab 2: ReportTab - Lazy load
        report_tab = LazyTabWidget(self._create_report_tab)
        self._lazy_tabs[2] = report_tab
        self.tabs.addTab(report_tab, "BÁO CÁO")

        # Tab 3: SettingsTab - Lazy load
        settings_tab = LazyTabWidget(self._create_settings_tab)
        self._lazy_tabs[3] = settings_tab
        self.tabs.addTab(settings_tab, "CÀI ĐẶT")

        # Connect tab change signal for lazy loading
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Connect edit_request event to navigate to edit tab
        from src.services.data_event_bus import get_event_bus
        get_event_bus().edit_request.connect(self._on_edit_request)

        self.setCentralWidget(self.tabs)
        logger.info("Main window tabs initialized with lazy loading")

    def _create_edit_tab(self) -> QWidget:
        """Factory method for EditTab"""
        from src.views.edit_tab import EditTab
        return EditTab()

    def _create_report_tab(self) -> QWidget:
        """Factory method for ReportTab"""
        from src.views.report_tab import ReportTab
        return ReportTab()

    def _create_settings_tab(self) -> QWidget:
        """Factory method for SettingsTab"""
        from src.views.settings_tab import SettingsTab
        return SettingsTab(self.user_info.get("role", "Operator"))

    def _on_tab_changed(self, index: int):
        """Handle tab change - trigger lazy loading if needed"""
        if index in self._lazy_tabs:
            lazy_tab = self._lazy_tabs[index]
            if not lazy_tab.is_loaded:
                logger.info(f"Loading tab at index {index}")
                lazy_tab.ensure_loaded()

    def _on_edit_request(self, request_no: str):
        """Handle edit_request event - switch to edit tab"""
        # Switch to edit tab (index 1)
        self.tabs.setCurrentIndex(1)

        # Ensure edit tab is loaded
        if 1 in self._lazy_tabs:
            lazy_tab = self._lazy_tabs[1]
            if not lazy_tab.is_loaded:
                lazy_tab.ensure_loaded()

        logger.info(f"Navigated to edit tab for request: {request_no}")

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

