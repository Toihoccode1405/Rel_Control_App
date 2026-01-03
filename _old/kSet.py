# kSet.py - MÀU SẮC NHẸ NHÀNG (PASTEL/MINIMALIST) - SQL SERVER SUPPORT
import hashlib, os
from configparser import ConfigParser
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
import pandas as pd
from kDb import DatabaseConnection
from cryptography.fernet import Fernet

# --- CONSTANTS MÀU SẮC NHẸ NHÀNG ---
# Style: Nền nhạt, Viền mỏng, Chữ đậm vừa phải
BTN_STYLE_ADD = """
    QPushButton { background-color: #E3F2FD; color: #1565C0; border: 1px solid #BBDEFB; border-radius: 4px; padding: 6px 12px; font-weight: 600; }
    QPushButton:hover { background-color: #BBDEFB; }
"""
BTN_STYLE_EDIT = """
    QPushButton { background-color: #E8F5E9; color: #2E7D32; border: 1px solid #C8E6C9; border-radius: 4px; padding: 6px 12px; font-weight: 600; }
    QPushButton:hover { background-color: #C8E6C9; }
"""
BTN_STYLE_DEL = """
    QPushButton { background-color: #FFEBEE; color: #C62828; border: 1px solid #FFCDD2; border-radius: 4px; padding: 6px 12px; font-weight: 600; }
    QPushButton:hover { background-color: #FFCDD2; }
"""
BTN_STYLE_CSV = """
    QPushButton { background-color: #FFF3E0; color: #EF6C00; border: 1px solid #FFE0B2; border-radius: 4px; padding: 6px 12px; font-weight: 600; }
    QPushButton:hover { background-color: #FFE0B2; }
"""

# --- DELEGATE SỬA TRỰC TIẾP ---
class DirectEditDelegate(QStyledItemDelegate):
    def __init__(self, parent, conn, table_name, is_equipment=False):
        super().__init__(parent); self.conn = conn; self.table_name = table_name; self.is_equipment = is_equipment
        self.equip_cols = ["factory", "control_no", "name", "spec", "r1", "r2", "r3", "r4", "r5", "remark"]

    def createEditor(self, parent, option, index): return QLineEdit(parent)

    def setModelData(self, editor, model, index):
        new_val = editor.text().strip(); old_val = index.data(Qt.ItemDataRole.DisplayRole)
        if new_val == str(old_val): return
        try:
            if self.is_equipment:
                col_idx = index.column(); col_db = self.equip_cols[col_idx]
                if col_idx == 1: self.conn.execute(f"UPDATE {self.table_name} SET control_no=? WHERE control_no=?", (new_val, old_val))
                else: 
                    cno = index.siblingAtColumn(1).data()
                    self.conn.execute(f"UPDATE {self.table_name} SET {col_db}=? WHERE control_no=?", (new_val, cno))
            else: self.conn.execute(f"UPDATE {self.table_name} SET name=? WHERE name=?", (new_val, old_val))
            self.conn.commit(); model.setData(index, new_val, Qt.ItemDataRole.EditRole)
        except Exception as e:
            if "UNIQUE" in str(e) or "IntegrityError" in str(e):
                QMessageBox.warning(None, "Trùng", f"Giá trị '{new_val}' đã tồn tại!")
            else:
                QMessageBox.critical(None, "Lỗi", str(e))

class SettingTab(QWidget):
    SIMPLE_TABLES = {
        "Nhà máy": "factory", "Dự án": "project", "Giai đoạn": "phase",
        "Hạng mục": "category", "Trạng thái": "status"
    }
    EQUIP_HEADERS = ["Factory", "Control No", "Name", "Spec", "Recipe 1", "Recipe 2", "Recipe 3", "Recipe 4", "Recipe 5", "Remark"]

    def __init__(self, role, db_path):
        super().__init__()
        self.role = role
        self.db_path = db_path
        db_conn = DatabaseConnection()
        self.conn = db_conn.connect()
        self.views = {}

        main_layout = QHBoxLayout(self); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)

        # --- MENU TRÁI ---
        self.menu = QListWidget(); self.menu.setFixedWidth(240)
        self.menu.setStyleSheet("""
            QListWidget { background-color: #F8F9FA; border: none; border-right: 1px solid #E0E0E0; outline: none; font-size: 14px; }
            QListWidget::item { color: #555; padding: 15px 20px; border-bottom: 1px solid #F0F0F0; margin-bottom: 1px; }
            QListWidget::item:selected { background-color: #E3F2FD; color: #1565C0; font-weight: 600; border-left: 4px solid #1565C0; }
            QListWidget::item:hover:!selected { background-color: #F0F0F0; }
        """)
        
        self.stack = QStackedWidget(); self.stack.setStyleSheet("QWidget { background-color: #FFFFFF; }")

        if role == "Super": self.add_page("Quản lý tài khoản", self.page_user())
        self.add_page("Cấu hình hệ thống", self.page_conf())
        self.add_page("Dữ liệu chung", self.page_general())
        self.add_page("Quản lý thiết bị", self.page_equip())

        self.menu.currentRowChanged.connect(self.stack.setCurrentIndex)
        main_layout.addWidget(self.menu); main_layout.addWidget(self.stack)
        if self.menu.count() > 0: self.menu.setCurrentRow(0)

    def add_page(self, title, widget):
        self.stack.addWidget(widget); self.menu.addItem(QListWidgetItem(title))

    # =========================================================================
    # 1. CẤU HÌNH SQL SERVER
    # =========================================================================
    def page_conf(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(30, 30, 30, 30); l.setSpacing(20); l.setAlignment(Qt.AlignmentFlag.AlignTop)
        l.addWidget(QLabel("<h3>Cấu hình SQL Server</h3>"))

        frame = QFrame(); frame.setStyleSheet("QFrame { border: 1px solid #E0E0E0; border-radius: 6px; background-color: #FAFAFA; } QLineEdit { background: white; border: 1px solid #CCC; padding: 5px; }")
        fl = QFormLayout(frame); fl.setContentsMargins(20, 20, 20, 20); fl.setSpacing(15)

        cfg = ConfigParser()
        if os.path.exists("config.ini"):
            cfg.read("config.ini", encoding="utf-8")

        # Đọc và giải mã thông tin
        self.srv_txt = QLineEdit(self._decrypt_config(cfg, "database", "server", "localhost"))
        self.db_txt = QLineEdit(self._decrypt_config(cfg, "database", "database", "kRel"))
        self.usr_txt = QLineEdit(self._decrypt_config(cfg, "database", "username", ""))
        self.pwd_txt = QLineEdit(self._decrypt_config(cfg, "database", "password", ""))
        self.pwd_txt.setEchoMode(QLineEdit.EchoMode.Password)
        self.drv_txt = QLineEdit(self._decrypt_config(cfg, "database", "driver", "{ODBC Driver 17 for SQL Server}"))

        self.log_txt = QLineEdit(cfg["system"].get("log_path","Logfile") if cfg.has_section("system") else "Logfile")
        b_log = QPushButton("..."); b_log.setFixedWidth(40); b_log.clicked.connect(lambda: self.pick_folder(self.log_txt))
        h_log = QHBoxLayout(); h_log.addWidget(self.log_txt); h_log.addWidget(b_log)

        fl.addRow("Server:", self.srv_txt)
        fl.addRow("Database:", self.db_txt)
        fl.addRow("Username:", self.usr_txt)
        fl.addRow("Password:", self.pwd_txt)
        fl.addRow("Driver:", self.drv_txt)
        fl.addRow("Log Folder:", h_log)
        l.addWidget(frame)

        btn_test = QPushButton("Test Kết Nối"); btn_test.setStyleSheet(BTN_STYLE_CSV); btn_test.setFixedWidth(150); btn_test.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_test.clicked.connect(self.test_connection)

        btn_save = QPushButton("Lưu Cấu Hình"); btn_save.setStyleSheet(BTN_STYLE_ADD); btn_save.setFixedWidth(150); btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self.save_conf)

        lb = QHBoxLayout(); lb.addStretch(); lb.addWidget(btn_test); lb.addWidget(btn_save); l.addLayout(lb)
        return w

    def _get_encryption_key(self):
        key_file = ".dbkey"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            return key

    def _encrypt_value(self, value):
        if not value: return ""
        key = self._get_encryption_key()
        f = Fernet(key)
        return f.encrypt(value.encode()).decode()

    def _decrypt_value(self, encrypted_value):
        if not encrypted_value: return ""
        try:
            key = self._get_encryption_key()
            f = Fernet(key)
            return f.decrypt(encrypted_value.encode()).decode()
        except:
            return encrypted_value

    def _decrypt_config(self, cfg, section, key, default):
        if cfg.has_section(section) and cfg.has_option(section, key):
            encrypted = cfg[section].get(key, default)
            return self._decrypt_value(encrypted)
        return default

    def pick_folder(self, txt):
        p = QFileDialog.getExistingDirectory(self, "Chọn Thư mục")
        if p: txt.setText(p)

    def test_connection(self):
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
            QMessageBox.warning(self, "Lỗi", "Chưa cài đặt pyodbc!\nVui lòng chạy: pip install pyodbc")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi kết nối", f"Không thể kết nối:\n{str(e)}")

    def save_conf(self):
        c = ConfigParser()
        if os.path.exists("config.ini"):
            c.read("config.ini", encoding="utf-8")

        if not c.has_section("system"):
            c.add_section("system")
        c["system"]["log_path"] = self.log_txt.text()

        if not c.has_section("database"):
            c.add_section("database")
        c["database"]["server"] = self._encrypt_value(self.srv_txt.text())
        c["database"]["database"] = self._encrypt_value(self.db_txt.text())
        c["database"]["username"] = self._encrypt_value(self.usr_txt.text())
        c["database"]["password"] = self._encrypt_value(self.pwd_txt.text())
        c["database"]["driver"] = self._encrypt_value(self.drv_txt.text())

        with open("config.ini","w", encoding="utf-8") as f:
            c.write(f)
        QMessageBox.information(self,"Thành công","Đã lưu cấu hình (đã mã hóa)!")

    # =========================================================================
    # 2. TÀI KHOẢN (MÀU NHẸ)
    # =========================================================================
    def page_user(self):
        w = QWidget(); h = QHBoxLayout(w)
        self.tbl_u = QTableView(); self.tbl_u.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.tbl_u.setStyleSheet("QTableView { border: 1px solid #E0E0E0; }")
        self.tbl_u.verticalHeader().hide(); self.tbl_u.clicked.connect(self.clk_u)
        h.addWidget(self.tbl_u, 7)
        
        r = QVBoxLayout(); r.setContentsMargins(10,0,0,0); r.addWidget(QLabel("<h3>Thông tin User</h3>"))
        self.u_u = QLineEdit(); self.u_u.setPlaceholderText("Username")
        self.u_p = QLineEdit(); self.u_p.setPlaceholderText("Password"); self.u_p.setEchoMode(QLineEdit.EchoMode.Password)
        self.u_n = QLineEdit(); self.u_n.setPlaceholderText("Họ Tên"); self.u_e = QLineEdit(); self.u_e.setPlaceholderText("Email")
        self.u_r = QComboBox(); self.u_r.addItems(["Operator","Engineer","Manager","Super"])
        
        form = QFormLayout(); form.setSpacing(10)
        for l, wi in [("User:",self.u_u),("Pass:",self.u_p),("Name:",self.u_n),("Email:",self.u_e),("Role:",self.u_r)]: form.addRow(l, wi)
        r.addLayout(form)
        
        hb = QHBoxLayout()
        b1=QPushButton("Mới"); b1.setStyleSheet(BTN_STYLE_ADD); b1.clicked.connect(self.clr_u)
        b2=QPushButton("Lưu"); b2.setStyleSheet(BTN_STYLE_EDIT); b2.clicked.connect(self.save_u)
        b3=QPushButton("Xóa"); b3.setStyleSheet(BTN_STYLE_DEL); b3.clicked.connect(self.del_u)
        hb.addWidget(b1); hb.addWidget(b2); hb.addWidget(b3)
        r.addLayout(hb); r.addStretch(); h.addLayout(r, 3); self.load_u()
        return w

    def load_u(self):
        df = pd.read_sql("SELECT username, fullname, role, email FROM users", self.conn)
        m = QStandardItemModel(); m.setHorizontalHeaderLabels(["Tài khoản", "Họ Tên", "Vai trò", "Email"])
        for _,r in df.iterrows(): m.appendRow([QStandardItem(str(x)) for x in r])
        self.tbl_u.setModel(m)
        h = self.tbl_u.horizontalHeader(); h.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents); h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

    def clk_u(self, i):
        r = i.row(); m = self.tbl_u.model()
        self.u_u.setText(m.item(r,0).text()); self.u_u.setEnabled(False)
        self.u_n.setText(m.item(r,1).text()); self.u_r.setCurrentText(m.item(r,2).text())
        self.u_e.setText(m.item(r,3).text()); self.u_p.clear()
    def clr_u(self): self.u_u.clear(); self.u_u.setEnabled(True); self.u_p.clear(); self.u_n.clear(); self.u_e.clear()
    def save_u(self):
        u = self.u_u.text();
        if not u: return
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username=?",(u,))
        ex = cursor.fetchone()
        if ex:
            q = "UPDATE users SET fullname=?, email=?, role=?" + (", password=?" if self.u_p.text() else "") + " WHERE username=?"
            p = [self.u_n.text(), self.u_e.text(), self.u_r.currentText()]
            if self.u_p.text(): p.append(hashlib.sha256(self.u_p.text().encode()).hexdigest())
            p.append(u)
            cursor.execute(q, p)
        else:
            if not self.u_p.text(): return QMessageBox.warning(self,"Lỗi","Nhập mật khẩu!")
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?)", (u, hashlib.sha256(self.u_p.text().encode()).hexdigest(), self.u_n.text(), self.u_e.text(), self.u_r.currentText()))
        self.conn.commit(); self.load_u(); self.clr_u()
    def del_u(self):
        u = self.u_u.text()
        if u!="ka" and QMessageBox.question(self,"?","Xóa user?")==QMessageBox.StandardButton.Yes:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM users WHERE username=?",(u,))
            self.conn.commit(); self.load_u(); self.clr_u()

    # =========================================================================
    # 3. DỮ LIỆU CHUNG (MÀU NHẸ)
    # =========================================================================
    def page_general(self):
        w = QWidget(); l = QHBoxLayout(w); l.setSpacing(15)
        self.views = {}
        for t, db in self.SIMPLE_TABLES.items():
            f = QGroupBox(t); f.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #D1D5DB; border-radius: 4px; margin-top: 10px; background: #FAFAFA; }")
            vl = QVBoxLayout(f); vl.setContentsMargins(5,15,5,5)
            
            bl = QGridLayout(); bl.setSpacing(5)
            b_add = QPushButton(); b_add.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)); b_add.setToolTip("Thêm")
            b_add.setStyleSheet(BTN_STYLE_ADD); b_add.clicked.connect(lambda _,x=db: self.add_g(x))
            
            b_edit = QPushButton(); b_edit.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)); b_edit.setToolTip("Sửa")
            b_edit.setStyleSheet(BTN_STYLE_EDIT); b_edit.clicked.connect(lambda _,x=db: self.edit_g(x)) 
            
            b_del = QPushButton(); b_del.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)); b_del.setToolTip("Xóa")
            b_del.setStyleSheet(BTN_STYLE_DEL); b_del.clicked.connect(lambda _,x=db: self.del_g(x))
            
            b_csv = QPushButton("CSV"); b_csv.setStyleSheet(BTN_STYLE_CSV)
            b_csv.clicked.connect(lambda _,x=db: self.csv_dialog(x)) 
            
            bl.addWidget(b_add, 0, 0); bl.addWidget(b_edit, 0, 1); bl.addWidget(b_del, 1, 0); bl.addWidget(b_csv, 1, 1)
            vl.addLayout(bl)
            
            tv = QTableView(); tv.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            tv.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); tv.verticalHeader().hide()
            self.views[db] = tv; vl.addWidget(tv); self.load_g(db)
            l.addWidget(f)
        return w

    def load_g(self, t):
        df = pd.read_sql(f"SELECT name FROM {t} ORDER BY name", self.conn)
        m = QStandardItemModel()
        header_name = "Giá trị"
        for k, v in self.SIMPLE_TABLES.items():
            if v == t: header_name = k; break
        m.setHorizontalHeaderLabels([header_name])
        for _, r in df.iterrows():
            it = QStandardItem(str(r.iloc[0])); it.setData(str(r.iloc[0]), Qt.ItemDataRole.UserRole)
            m.appendRow([it])
        self.views[t].setModel(m); self.views[t].horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def add_g(self, t):
        s, ok = QInputDialog.getText(self, "Thêm Mới", "Nhập tên:")
        if ok and s:
            try:
                cursor = self.conn.cursor()
                cursor.execute(f"IF NOT EXISTS (SELECT 1 FROM {t} WHERE name=?) INSERT INTO {t} VALUES (?)", (s, s))
                self.conn.commit(); self.load_g(t)
            except Exception as e: QMessageBox.warning(self,"Lỗi",str(e))
    def edit_g(self, t):
        tv = self.views[t]; i = tv.currentIndex()
        if not i.isValid(): return QMessageBox.warning(self, "Chọn", "Vui lòng chọn dòng cần sửa!")
        old = i.data(Qt.ItemDataRole.UserRole); new, ok = QInputDialog.getText(self, "Sửa", f"Sửa '{old}' thành:", text=old)
        if ok and new:
            try:
                cursor = self.conn.cursor()
                cursor.execute(f"UPDATE {t} SET name=? WHERE name=?", (new, old))
                self.conn.commit(); self.load_g(t)
            except Exception as e: QMessageBox.warning(self, "Lỗi", str(e))
    def del_g(self, t):
        tv = self.views[t]; i = tv.currentIndex()
        if i.isValid() and QMessageBox.question(self,"Xóa",f"Xóa dòng này?")==QMessageBox.StandardButton.Yes:
            cursor = self.conn.cursor()
            cursor.execute(f"DELETE FROM {t} WHERE name=?", (i.data(Qt.ItemDataRole.UserRole),))
            self.conn.commit(); self.load_g(t)

    # =========================================================================
    # 4. THIẾT BỊ (MÀU NHẸ)
    # =========================================================================
    def page_equip(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(15,15,15,15)
        
        h = QHBoxLayout(); lbl = QLabel("QUẢN LÝ THIẾT BỊ"); lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #444;")
        h.addWidget(lbl); h.addStretch()
        
        b1=QPushButton("Thêm Mới"); b1.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)); b1.setStyleSheet(BTN_STYLE_ADD); b1.clicked.connect(self.add_e)
        b2=QPushButton("Sửa"); b2.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)); b2.setStyleSheet(BTN_STYLE_EDIT); b2.clicked.connect(self.edit_e)
        b3=QPushButton("Xóa"); b3.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)); b3.setStyleSheet(BTN_STYLE_DEL); b3.clicked.connect(self.del_e)
        b4=QPushButton("CSV"); b4.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DriveFDIcon)); b4.setStyleSheet(BTN_STYLE_CSV)
        b4.clicked.connect(lambda: self.csv_dialog("equipment")) 
        
        for b in [b1,b2,b3,b4]: h.addWidget(b)
        l.addLayout(h); l.addSpacing(10)
        
        self.tv_e = QTableView(); self.tv_e.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tv_e.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.tv_e.setStyleSheet("QTableView { border: 1px solid #E0E0E0; }")
        l.addWidget(self.tv_e); self.load_e()
        return w

    def load_e(self):
        df = pd.read_sql("SELECT * FROM equipment ORDER BY control_no", self.conn)
        m = QStandardItemModel(); m.setHorizontalHeaderLabels(self.EQUIP_HEADERS)
        for _, r in df.iterrows():
            row = []; [row.append(QStandardItem(str(x))) for x in r]; row[1].setData(str(r.iloc[1]), Qt.ItemDataRole.UserRole)
            m.appendRow(row)
        self.tv_e.setModel(m); h = self.tv_e.horizontalHeader(); h.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents); h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch); h.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)

    def open_equip_dlg(self, title, data=None):
        d = QDialog(self); d.setWindowTitle(title); d.setMinimumWidth(500); l = QFormLayout(d); inps = []
        for i, head in enumerate(self.EQUIP_HEADERS):
            led = QLineEdit(); 
            if data: led.setText(str(data[i]))
            l.addRow(head, led); inps.append(led)
        btn = QPushButton("LƯU"); btn.setStyleSheet("background:#2E7D32;color:white;font-weight:bold;padding:8px")
        btn.clicked.connect(lambda: self.save_e_db(inps, d, data[1] if data else None))
        l.addRow(btn); d.exec()

    def add_e(self): self.open_equip_dlg("Thêm Thiết Bị Mới")
    def edit_e(self):
        i = self.tv_e.currentIndex()
        if not i.isValid(): return QMessageBox.warning(self, "Lỗi", "Chọn thiết bị cần sửa!")
        r = i.row(); m = self.tv_e.model(); data = [m.item(r, c).text() for c in range(10)]
        self.open_equip_dlg("Sửa Thiết Bị", data)
    def save_e_db(self, inps, d, old_cno=None):
        v = [x.text().strip() for x in inps]
        if not v[1] or not v[2]: return QMessageBox.warning(d, "Lỗi", "Mã và Tên là bắt buộc!")
        try:
            cursor = self.conn.cursor()
            if old_cno:
                cols = ["factory","control_no","name","spec","r1","r2","r3","r4","r5","remark"]
                sql = f"UPDATE equipment SET {','.join([c+'=?' for c in cols])} WHERE control_no=?"
                cursor.execute(sql, v + [old_cno])
            else:
                cursor.execute("INSERT INTO equipment VALUES (?,?,?,?,?,?,?,?,?,?)", v)
            self.conn.commit(); self.load_e(); d.accept()
        except Exception as e: QMessageBox.warning(d, "Lỗi Database", str(e))
    def del_e(self):
        i = self.tv_e.currentIndex()
        if i.isValid() and QMessageBox.question(self,"Xóa","Xóa thiết bị này?")==QMessageBox.StandardButton.Yes:
            old = self.tv_e.model().item(i.row(), 1).data(Qt.ItemDataRole.UserRole)
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM equipment WHERE control_no=?", (old,))
            self.conn.commit(); self.load_e()

    # --- CSV DIALOG ---
    def csv_dialog(self, t):
        d = QDialog(self); d.setWindowTitle("Thao Tác CSV"); d.setFixedSize(250, 220)
        l = QVBoxLayout(d); l.setSpacing(10)
        
        l.addWidget(QLabel("<b>Lựa chọn?</b>", alignment=Qt.AlignmentFlag.AlignCenter))
        b1 = QPushButton("1. CSV Mẫu"); b1.clicked.connect(lambda: [self.dl_template(t), d.accept()])
        b2 = QPushButton("2. Nhập CSV"); b2.clicked.connect(lambda: [self.imp_csv(t), d.accept()])
        b3 = QPushButton("3. Xuất CSV"); b3.clicked.connect(lambda: [self.exp_csv(t), d.accept()])
        b4 = QPushButton("4. Huỷ"); b4.clicked.connect(d.reject)
        
        for b in [b1,b2,b3,b4]: b.setFixedHeight(35); l.addWidget(b)
        d.exec()

    def dl_template(self, t):
        p, _ = QFileDialog.getSaveFileName(self, "Lưu mẫu", f"Mau_{t}.csv", "CSV (*.csv)")
        if p:
            h = self.EQUIP_HEADERS if t == "equipment" else ["Gia_Tri"]
            pd.DataFrame(columns=h).to_csv(p, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, "OK", "Đã lưu mẫu!")

    def imp_csv(self, t):
        p, _ = QFileDialog.getOpenFileName(self, "Mở CSV", "", "*.csv")
        if p:
            try:
                df = pd.read_csv(p).fillna("")
                cursor = self.conn.cursor()
                if t == "equipment":
                    data = [tuple(str(x) for x in r[:10]) for _, r in df.iterrows()]
                    for row in data:
                        cursor.execute("IF NOT EXISTS (SELECT 1 FROM equipment WHERE control_no=?) INSERT INTO equipment VALUES (?,?,?,?,?,?,?,?,?,?)", (row[1],) + row)
                else:
                    data = [(str(r.iloc[0]),) for _, r in df.iterrows() if str(r.iloc[0]).strip()]
                    for row in data:
                        cursor.execute(f"IF NOT EXISTS (SELECT 1 FROM {t} WHERE name=?) INSERT INTO {t} VALUES (?)", (row[0], row[0]))
                self.conn.commit(); QMessageBox.information(self, "OK", "Nhập xong!");
                self.load_g(t) if t!="equipment" else self.load_e()
            except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))

    def exp_csv(self, t):
        p, _ = QFileDialog.getSaveFileName(self, "Xuất CSV", f"Data_{t}.csv", "CSV (*.csv)")
        if p:
            try:
                if t == "equipment":
                    df = pd.read_sql("SELECT * FROM equipment", self.conn)
                    df.columns = self.EQUIP_HEADERS
                else:
                    df = pd.read_sql(f"SELECT name as 'Gia_Tri' FROM {t}", self.conn)
                df.to_csv(p, index=False, encoding='utf-8-sig')
                QMessageBox.information(self, "OK", "Đã xuất file!")
            except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))