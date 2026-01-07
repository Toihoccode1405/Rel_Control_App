"""
kRel - Settings Pages: Config, Users
Các trang cài đặt hệ thống và quản lý users
"""
import os
import hashlib
from configparser import ConfigParser

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QFrame,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableView,
    QAbstractItemView, QHeaderView, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
import pandas as pd

from src.config import CONFIG_FILE
from src.services.database import get_db
from src.services.encryption import EncryptionService
from src.styles import (
    BTN_STYLE_BLUE, BTN_STYLE_GREEN, BTN_STYLE_RED,
    BTN_STYLE_ORANGE, BTN_STYLE_GREEN_SOLID
)


class ConfigPage(QWidget):
    """Trang cấu hình SQL Server"""
    
    def __init__(self):
        super().__init__()
        self.encryption = EncryptionService()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Header
        layout.addWidget(QLabel("<h2 style='color: #1565C0;'>⚙️ Cấu hình SQL Server</h2>"))

        # Config frame
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { border: 1px solid #E0E0E0; border-radius: 8px; background-color: #FAFAFA; }
            QLabel { font-weight: 500; color: #424242; }
            QLineEdit {
                background: white; border: 1px solid #CFD8DC; border-radius: 6px;
                padding: 8px 12px; min-height: 36px; font-size: 13px;
            }
            QLineEdit:hover { border-color: #90CAF9; }
            QLineEdit:focus { border: 2px solid #1565C0; }
        """)
        
        fl = QFormLayout(frame)
        fl.setContentsMargins(24, 24, 24, 24)
        fl.setSpacing(16)

        # Load config
        cfg = ConfigParser()
        if os.path.exists(CONFIG_FILE):
            cfg.read(CONFIG_FILE, encoding="utf-8")

        self.srv_txt = QLineEdit(self._get_config(cfg, "database", "server", "localhost"))
        self.db_txt = QLineEdit(self._get_config(cfg, "database", "database", "kRel"))
        self.usr_txt = QLineEdit(self._get_config(cfg, "database", "username", ""))
        self.pwd_txt = QLineEdit(self._get_config(cfg, "database", "password", ""))
        self.pwd_txt.setEchoMode(QLineEdit.EchoMode.Password)
        self.drv_txt = QLineEdit(
            self._get_config(cfg, "database", "driver", "{ODBC Driver 17 for SQL Server}")
        )

        log_path = cfg["system"].get("log_path", "Logfile") if cfg.has_section("system") else "Logfile"
        self.log_txt = QLineEdit(log_path)

        btn_log = QPushButton("📁")
        btn_log.setFixedWidth(50)
        btn_log.setStyleSheet(BTN_STYLE_BLUE)
        btn_log.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_log.clicked.connect(lambda: self._pick_folder(self.log_txt))

        h_log = QHBoxLayout()
        h_log.setSpacing(8)
        h_log.addWidget(self.log_txt)
        h_log.addWidget(btn_log)

        fl.addRow("🖥️ Server:", self.srv_txt)
        fl.addRow("🗄️ Database:", self.db_txt)
        fl.addRow("👤 Username:", self.usr_txt)
        fl.addRow("🔑 Password:", self.pwd_txt)
        fl.addRow("🔌 Driver:", self.drv_txt)
        fl.addRow("📁 Log Folder:", h_log)

        layout.addWidget(frame)

        # Buttons
        btn_test = QPushButton("  🔗 Test Kết Nối")
        btn_test.setStyleSheet(BTN_STYLE_ORANGE)
        btn_test.setFixedWidth(160)
        btn_test.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_test.clicked.connect(self._test_connection)

        btn_save = QPushButton("  💾 Lưu Cấu Hình")
        btn_save.setStyleSheet(BTN_STYLE_GREEN_SOLID)
        btn_save.setFixedWidth(160)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self._save_config)

        lb = QHBoxLayout()
        lb.setSpacing(12)
        lb.addStretch()
        lb.addWidget(btn_test)
        lb.addWidget(btn_save)
        layout.addLayout(lb)
    
    def _get_config(self, cfg, section, key, default):
        if cfg.has_section(section) and cfg.has_option(section, key):
            encrypted = cfg[section].get(key, default)
            return self.encryption.decrypt(encrypted)
        return default
    
    def _pick_folder(self, txt):
        path = QFileDialog.getExistingDirectory(self, "Chọn Thư mục")
        if path:
            txt.setText(path)
    
    def _test_connection(self):
        try:
            import pyodbc
            server, database = self.srv_txt.text(), self.db_txt.text()
            username, password = self.usr_txt.text(), self.pwd_txt.text()
            driver = self.drv_txt.text()
            
            if username and password:
                conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            else:
                conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes"
            
            conn = pyodbc.connect(conn_str, timeout=5)
            conn.close()
            QMessageBox.information(self, "Thành công", "Kết nối SQL Server thành công!")
        except ImportError:
            QMessageBox.warning(self, "Lỗi", "Chưa cài đặt pyodbc!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi kết nối", f"Không thể kết nối:\n{str(e)}")
    
    def _save_config(self):
        cfg = ConfigParser()
        if os.path.exists(CONFIG_FILE):
            cfg.read(CONFIG_FILE, encoding="utf-8")
        
        if not cfg.has_section("system"):
            cfg.add_section("system")
        cfg["system"]["log_path"] = self.log_txt.text()
        
        if not cfg.has_section("database"):
            cfg.add_section("database")
        cfg["database"]["server"] = self.encryption.encrypt(self.srv_txt.text())
        cfg["database"]["database"] = self.encryption.encrypt(self.db_txt.text())
        cfg["database"]["username"] = self.encryption.encrypt(self.usr_txt.text())
        cfg["database"]["password"] = self.encryption.encrypt(self.pwd_txt.text())
        cfg["database"]["driver"] = self.encryption.encrypt(self.drv_txt.text())
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            cfg.write(f)
        
        QMessageBox.information(self, "Thành công", "Đã lưu cấu hình (đã mã hóa)!")

