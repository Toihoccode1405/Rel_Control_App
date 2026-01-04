"""
kRel - Settings Tab
System configuration and data management
"""
import os
import hashlib
from configparser import ConfigParser

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QFrame, QGroupBox, QListWidget, QListWidgetItem, QStackedWidget,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableView,
    QAbstractItemView, QHeaderView, QInputDialog, QFileDialog,
    QMessageBox, QStyle, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
import pandas as pd

from src.config import CONFIG_FILE
from src.services.database import get_db
from src.services.encryption import EncryptionService
from src.services.data_event_bus import get_event_bus
from src.services.logger import get_logger
from src.styles import (
    BTN_STYLE_BLUE, BTN_STYLE_GREEN, BTN_STYLE_RED, BTN_STYLE_ORANGE,
    BTN_STYLE_GREEN_SOLID, SETTINGS_MENU_STYLE, TABLE_STYLE, GROUPBOX_STYLE
)

# Module logger
logger = get_logger("settings_tab")


class SettingsTab(QWidget):
    """Settings and configuration tab"""

    SIMPLE_TABLES = {
        "🏭 Nhà máy": "factory",
        "📁 Dự án": "project",
        "📊 Giai đoạn": "phase",
        "📋 Hạng mục": "category",
        "🔄 Trạng thái": "status"
    }

    EQUIP_HEADERS = [
        "Factory", "Control No", "Name", "Spec",
        "Recipe 1", "Recipe 2", "Recipe 3", "Recipe 4", "Recipe 5", "Remark"
    ]

    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self.role = role
        self.db = get_db()
        self.encryption = EncryptionService()
        self.views = {}

        self._setup_ui()

    def _setup_ui(self):
        """Setup UI components"""
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
            self._add_page("👤 Quản lý tài khoản", self._page_users())

        self._add_page("⚙️ Cấu hình hệ thống", self._page_config())
        self._add_page("📦 Dữ liệu chung", self._page_general())
        self._add_page("🔧 Quản lý thiết bị", self._page_equipment())

        self.menu.currentRowChanged.connect(self.stack.setCurrentIndex)

        main_layout.addWidget(self.menu)
        main_layout.addWidget(self.stack)

        if self.menu.count() > 0:
            self.menu.setCurrentRow(0)

    def _add_page(self, title: str, widget: QWidget):
        """Add a page to the stack"""
        self.stack.addWidget(widget)
        self.menu.addItem(QListWidgetItem(title))

    # ==========================================================================
    # Configuration Page
    # ==========================================================================
    def _page_config(self):
        """System configuration page"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Header
        header = QLabel("<h2 style='color: #1565C0;'>⚙️ Cấu hình SQL Server</h2>")
        layout.addWidget(header)

        # Config frame
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: #FAFAFA;
            }
            QLabel {
                font-weight: 500;
                color: #424242;
            }
            QLineEdit {
                background: white;
                border: 1px solid #CFD8DC;
                border-radius: 6px;
                padding: 8px 12px;
                min-height: 36px;
                font-size: 13px;
            }
            QLineEdit:hover {
                border-color: #90CAF9;
            }
            QLineEdit:focus {
                border: 2px solid #1565C0;
            }
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

        return widget
    
    def _get_config(self, cfg, section, key, default):
        """Get decrypted config value"""
        if cfg.has_section(section) and cfg.has_option(section, key):
            encrypted = cfg[section].get(key, default)
            return self.encryption.decrypt(encrypted)
        return default
    
    def _pick_folder(self, txt):
        """Pick folder dialog"""
        path = QFileDialog.getExistingDirectory(self, "Chọn Thư mục")
        if path:
            txt.setText(path)
    
    def _test_connection(self):
        """Test database connection"""
        try:
            import pyodbc
            
            server = self.srv_txt.text()
            database = self.db_txt.text()
            username = self.usr_txt.text()
            password = self.pwd_txt.text()
            driver = self.drv_txt.text()
            
            if username and password:
                conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            else:
                conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes"
            
            conn = pyodbc.connect(conn_str, timeout=5)
            conn.close()
            QMessageBox.information(self, "Thành công", "Kết nối SQL Server thành công!")
            
        except ImportError:
            QMessageBox.warning(
                self, "Lỗi",
                "Chưa cài đặt pyodbc!\nVui lòng chạy: pip install pyodbc"
            )
        except Exception as e:
            QMessageBox.critical(self, "Lỗi kết nối", f"Không thể kết nối:\n{str(e)}")
    
    def _save_config(self):
        """Save configuration"""
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

    # ==========================================================================
    # User Management Page
    # ==========================================================================
    def _page_users(self):
        """User management page"""
        widget = QWidget()
        layout = QHBoxLayout(widget)

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
        btn_new.clicked.connect(self._clear_user_form)

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

        self._load_users()
        return widget

    def _load_users(self):
        """Load users into table"""
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
        """Handle user table click"""
        row = index.row()
        model = self.tbl_users.model()

        self.u_username.setText(model.item(row, 0).text())
        self.u_username.setEnabled(False)
        self.u_fullname.setText(model.item(row, 1).text())
        self.u_role.setCurrentText(model.item(row, 2).text())
        self.u_email.setText(model.item(row, 3).text())
        self.u_password.clear()

    def _clear_user_form(self):
        """Clear user form"""
        self.u_username.clear()
        self.u_username.setEnabled(True)
        self.u_password.clear()
        self.u_fullname.clear()
        self.u_email.clear()

    def _save_user(self):
        """Save user"""
        username = self.u_username.text()
        if not username:
            return

        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT 1 FROM users WHERE username=?", (username,))
            exists = cursor.fetchone()

            if exists:
                # Update
                if self.u_password.text():
                    cursor.execute(
                        "UPDATE users SET fullname=?, email=?, role=?, password=? WHERE username=?",
                        (
                            self.u_fullname.text(),
                            self.u_email.text(),
                            self.u_role.currentText(),
                            hashlib.sha256(self.u_password.text().encode()).hexdigest(),
                            username
                        )
                    )
                else:
                    cursor.execute(
                        "UPDATE users SET fullname=?, email=?, role=? WHERE username=?",
                        (
                            self.u_fullname.text(),
                            self.u_email.text(),
                            self.u_role.currentText(),
                            username
                        )
                    )
            else:
                # Insert
                if not self.u_password.text():
                    return QMessageBox.warning(self, "Lỗi", "Nhập mật khẩu!")

                cursor.execute(
                    "INSERT INTO users VALUES (?,?,?,?,?)",
                    (
                        username,
                        hashlib.sha256(self.u_password.text().encode()).hexdigest(),
                        self.u_fullname.text(),
                        self.u_email.text(),
                        self.u_role.currentText()
                    )
                )

        self._load_users()
        self._clear_user_form()

    def _delete_user(self):
        """Delete user"""
        username = self.u_username.text()
        if username != "admin" and QMessageBox.question(
            self, "?", "Xóa user?"
        ) == QMessageBox.StandardButton.Yes:
            with self.db.get_cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE username=?", (username,))

            self._load_users()
            self._clear_user_form()

    # ==========================================================================
    # General Data Page
    # ==========================================================================
    def _page_general(self):
        """General data management page"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(15)

        self.views = {}

        for title, table in self.SIMPLE_TABLES.items():
            frame = QGroupBox(title)
            frame.setStyleSheet("""
                QGroupBox {
                    font-weight: bold; border: 1px solid #D1D5DB;
                    border-radius: 4px; margin-top: 10px; background: #FAFAFA;
                }
            """)

            vl = QVBoxLayout(frame)
            vl.setContentsMargins(5, 15, 5, 5)

            # Buttons
            bl = QGridLayout()
            bl.setSpacing(8)

            btn_add = QPushButton()
            btn_add.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
            btn_add.setToolTip("Thêm")
            btn_add.setStyleSheet(BTN_STYLE_BLUE)
            btn_add.clicked.connect(lambda _, t=table: self._add_general(t))

            btn_edit = QPushButton()
            btn_edit.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
            btn_edit.setToolTip("Sửa")
            btn_edit.setStyleSheet(BTN_STYLE_GREEN)
            btn_edit.clicked.connect(lambda _, t=table: self._edit_general(t))

            btn_del = QPushButton()
            btn_del.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
            btn_del.setToolTip("Xóa")
            btn_del.setStyleSheet(BTN_STYLE_RED)
            btn_del.clicked.connect(lambda _, t=table: self._delete_general(t))

            btn_csv = QPushButton("CSV")
            btn_csv.setStyleSheet(BTN_STYLE_ORANGE)
            btn_csv.clicked.connect(lambda _, t=table: self._csv_dialog(t))

            bl.addWidget(btn_add, 0, 0)
            bl.addWidget(btn_edit, 0, 1)
            bl.addWidget(btn_del, 1, 0)
            bl.addWidget(btn_csv, 1, 1)
            vl.addLayout(bl)

            # Table
            tv = QTableView()
            tv.setStyleSheet(TABLE_STYLE)
            tv.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            tv.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            tv.verticalHeader().hide()
            self.views[table] = tv
            vl.addWidget(tv)

            self._load_general(table)
            layout.addWidget(frame)

        return widget

    def _load_general(self, table):
        """Load general data"""
        conn = self.db.connect()
        df = pd.read_sql(f"SELECT name FROM {table} ORDER BY name", conn)

        model = QStandardItemModel()
        header_name = "Giá trị"
        for k, v in self.SIMPLE_TABLES.items():
            if v == table:
                header_name = k
                break

        model.setHorizontalHeaderLabels([header_name])

        for _, row in df.iterrows():
            item = QStandardItem(str(row.iloc[0]))
            item.setData(str(row.iloc[0]), Qt.ItemDataRole.UserRole)
            model.appendRow([item])

        self.views[table].setModel(model)
        self.views[table].horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

    def _add_general(self, table):
        """Add general data item"""
        text, ok = QInputDialog.getText(self, "Thêm Mới", "Nhập tên:")
        if ok and text:
            try:
                with self.db.get_cursor() as cursor:
                    cursor.execute(
                        f"IF NOT EXISTS (SELECT 1 FROM {table} WHERE name=?) "
                        f"INSERT INTO {table} VALUES (?)",
                        (text, text)
                    )
                self._load_general(table)

                # Emit event for other tabs to refresh
                get_event_bus().emit_lookup_changed(table)
                logger.debug(f"Added to {table}: {text}")
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", str(e))

    def _edit_general(self, table):
        """Edit general data item"""
        tv = self.views[table]
        index = tv.currentIndex()

        if not index.isValid():
            return QMessageBox.warning(self, "Chọn", "Vui lòng chọn dòng cần sửa!")

        old = index.data(Qt.ItemDataRole.UserRole)
        new, ok = QInputDialog.getText(self, "Sửa", f"Sửa '{old}' thành:", text=old)

        if ok and new:
            try:
                with self.db.get_cursor() as cursor:
                    cursor.execute(
                        f"UPDATE {table} SET name=? WHERE name=?",
                        (new, old)
                    )
                self._load_general(table)

                # Emit event for other tabs to refresh
                get_event_bus().emit_lookup_changed(table)
                logger.debug(f"Updated {table}: {old} -> {new}")
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", str(e))

    def _delete_general(self, table):
        """Delete general data item"""
        tv = self.views[table]
        index = tv.currentIndex()

        if index.isValid() and QMessageBox.question(
            self, "Xóa", "Xóa dòng này?"
        ) == QMessageBox.StandardButton.Yes:
            old_value = index.data(Qt.ItemDataRole.UserRole)
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    f"DELETE FROM {table} WHERE name=?",
                    (old_value,)
                )
            self._load_general(table)

            # Emit event for other tabs to refresh
            get_event_bus().emit_lookup_changed(table)
            logger.debug(f"Deleted from {table}: {old_value}")

    # ==========================================================================
    # Equipment Management Page
    # ==========================================================================
    def _page_equipment(self):
        """Equipment management page"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header = QHBoxLayout()
        header.setSpacing(12)
        lbl = QLabel("<b style='font-size: 16px; color: #1565C0;'>🔧 QUẢN LÝ THIẾT BỊ</b>")
        header.addWidget(lbl)
        header.addStretch()

        # Buttons
        btn_add = QPushButton("  ➕ Thêm Mới")
        btn_add.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        btn_add.setStyleSheet(BTN_STYLE_BLUE)
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self._add_equipment)

        btn_edit = QPushButton("  ✏️ Sửa")
        btn_edit.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        btn_edit.setStyleSheet(BTN_STYLE_GREEN)
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.clicked.connect(self._edit_equipment)

        btn_del = QPushButton("  🗑️ Xóa")
        btn_del.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        btn_del.setStyleSheet(BTN_STYLE_RED)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.clicked.connect(self._delete_equipment)

        btn_csv = QPushButton("  📤 CSV")
        btn_csv.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DriveFDIcon))
        btn_csv.setStyleSheet(BTN_STYLE_ORANGE)
        btn_csv.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_csv.clicked.connect(lambda: self._csv_dialog("equipment"))

        for btn in [btn_add, btn_edit, btn_del, btn_csv]:
            header.addWidget(btn)

        layout.addLayout(header)
        layout.addSpacing(12)

        # Table
        self.tv_equipment = QTableView()
        self.tv_equipment.setStyleSheet(TABLE_STYLE)
        self.tv_equipment.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tv_equipment.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tv_equipment)

        self._load_equipment()
        return widget

    def _load_equipment(self):
        """Load equipment data"""
        conn = self.db.connect()
        df = pd.read_sql("SELECT * FROM equipment ORDER BY control_no", conn)

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(self.EQUIP_HEADERS)

        for _, row in df.iterrows():
            items = []
            for x in row:
                items.append(QStandardItem(str(x) if x else ""))
            if len(items) > 1:
                items[1].setData(str(row.iloc[1]), Qt.ItemDataRole.UserRole)
            model.appendRow(items)

        self.tv_equipment.setModel(model)
        h = self.tv_equipment.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)

    def _open_equipment_dialog(self, title, data=None):
        """Open equipment edit dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(500)

        layout = QFormLayout(dialog)
        inputs = []

        for i, header in enumerate(self.EQUIP_HEADERS):
            led = QLineEdit()
            if data:
                led.setText(str(data[i]))
            layout.addRow(header, led)
            inputs.append(led)

        btn_save = QPushButton("LƯU")
        btn_save.setStyleSheet("background:#2E7D32;color:white;font-weight:bold;padding:8px")
        btn_save.clicked.connect(
            lambda: self._save_equipment(inputs, dialog, data[1] if data else None)
        )
        layout.addRow(btn_save)

        dialog.exec()

    def _add_equipment(self):
        """Add equipment"""
        self._open_equipment_dialog("Thêm Thiết Bị Mới")

    def _edit_equipment(self):
        """Edit equipment"""
        index = self.tv_equipment.currentIndex()
        if not index.isValid():
            return QMessageBox.warning(self, "Lỗi", "Chọn thiết bị cần sửa!")

        row = index.row()
        model = self.tv_equipment.model()
        data = [model.item(row, c).text() for c in range(10)]
        self._open_equipment_dialog("Sửa Thiết Bị", data)

    def _save_equipment(self, inputs, dialog, old_control_no=None):
        """Save equipment to database"""
        values = [x.text().strip() for x in inputs]

        if not values[1] or not values[2]:
            return QMessageBox.warning(dialog, "Lỗi", "Mã và Tên là bắt buộc!")

        try:
            with self.db.get_cursor() as cursor:
                if old_control_no:
                    # Update
                    cols = ["factory", "control_no", "name", "spec",
                            "r1", "r2", "r3", "r4", "r5", "remark"]
                    sql = f"UPDATE equipment SET {','.join([c+'=?' for c in cols])} WHERE control_no=?"
                    cursor.execute(sql, values + [old_control_no])
                else:
                    # Insert
                    cursor.execute(
                        "INSERT INTO equipment VALUES (?,?,?,?,?,?,?,?,?,?)",
                        values
                    )

            self._load_equipment()
            dialog.accept()

            # Emit event for other tabs to refresh
            get_event_bus().emit_equipment_changed()
            logger.debug(f"Equipment saved: {values[1]}")

        except Exception as e:
            QMessageBox.warning(dialog, "Lỗi Database", str(e))

    def _delete_equipment(self):
        """Delete equipment"""
        index = self.tv_equipment.currentIndex()

        if index.isValid() and QMessageBox.question(
            self, "Xóa", "Xóa thiết bị này?"
        ) == QMessageBox.StandardButton.Yes:
            old = self.tv_equipment.model().item(index.row(), 1).data(
                Qt.ItemDataRole.UserRole
            )
            with self.db.get_cursor() as cursor:
                cursor.execute("DELETE FROM equipment WHERE control_no=?", (old,))
            self._load_equipment()

            # Emit event for other tabs to refresh
            get_event_bus().emit_equipment_changed()
            logger.debug(f"Equipment deleted: {old}")

    # ==========================================================================
    # CSV Dialog
    # ==========================================================================
    def _csv_dialog(self, table):
        """CSV import/export dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Thao Tác CSV")
        dialog.setFixedSize(250, 220)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)

        layout.addWidget(QLabel("<b>Lựa chọn?</b>", alignment=Qt.AlignmentFlag.AlignCenter))

        btn1 = QPushButton("1. CSV Mẫu")
        btn1.clicked.connect(lambda: [self._download_template(table), dialog.accept()])

        btn2 = QPushButton("2. Nhập CSV")
        btn2.clicked.connect(lambda: [self._import_csv(table), dialog.accept()])

        btn3 = QPushButton("3. Xuất CSV")
        btn3.clicked.connect(lambda: [self._export_csv(table), dialog.accept()])

        btn4 = QPushButton("4. Huỷ")
        btn4.clicked.connect(dialog.reject)

        for btn in [btn1, btn2, btn3, btn4]:
            btn.setFixedHeight(35)
            layout.addWidget(btn)

        dialog.exec()

    def _download_template(self, table):
        """Download CSV template"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Lưu mẫu", f"Mau_{table}.csv", "CSV (*.csv)"
        )
        if path:
            headers = self.EQUIP_HEADERS if table == "equipment" else ["Gia_Tri"]
            pd.DataFrame(columns=headers).to_csv(path, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, "OK", "Đã lưu mẫu!")

    def _import_csv(self, table):
        """Import CSV data"""
        path, _ = QFileDialog.getOpenFileName(self, "Mở CSV", "", "*.csv")
        if path:
            try:
                df = pd.read_csv(path).fillna("")

                with self.db.get_cursor() as cursor:
                    if table == "equipment":
                        data = [tuple(str(x) for x in r[:10]) for _, r in df.iterrows()]
                        for row in data:
                            cursor.execute(
                                "IF NOT EXISTS (SELECT 1 FROM equipment WHERE control_no=?) "
                                "INSERT INTO equipment VALUES (?,?,?,?,?,?,?,?,?,?)",
                                (row[1],) + row
                            )
                    else:
                        data = [
                            (str(r.iloc[0]),) for _, r in df.iterrows()
                            if str(r.iloc[0]).strip()
                        ]
                        for row in data:
                            cursor.execute(
                                f"IF NOT EXISTS (SELECT 1 FROM {table} WHERE name=?) "
                                f"INSERT INTO {table} VALUES (?)",
                                (row[0], row[0])
                            )

                QMessageBox.information(self, "OK", "Nhập xong!")

                if table != "equipment":
                    self._load_general(table)
                    # Emit event for other tabs to refresh
                    get_event_bus().emit_lookup_changed(table)
                    logger.debug(f"CSV imported to {table}")
                else:
                    self._load_equipment()
                    # Emit event for other tabs to refresh
                    get_event_bus().emit_equipment_changed()
                    logger.debug("CSV imported to equipment")

            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def _export_csv(self, table):
        """Export CSV data"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Xuất CSV", f"Data_{table}.csv", "CSV (*.csv)"
        )
        if path:
            try:
                conn = self.db.connect()
                if table == "equipment":
                    df = pd.read_sql("SELECT * FROM equipment", conn)
                    df.columns = self.EQUIP_HEADERS
                else:
                    df = pd.read_sql(f"SELECT name as 'Gia_Tri' FROM {table}", conn)

                df.to_csv(path, index=False, encoding='utf-8-sig')
                QMessageBox.information(self, "OK", "Đã xuất file!")

            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

