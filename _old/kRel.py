# kRel.py - FINAL INTEGRATION (WITH REPORT TAB) - SQL SERVER SUPPORT
import sys, os, hashlib, traceback
from configparser import ConfigParser
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon, QFont, QPixmap

# --- IMPORT MODULES ---
# Đảm bảo bạn đã có đủ 5 file: kInput.py, kEdit.py, kRep.py, kSet.py, kDb.py
try:
    from kDb import DatabaseConnection
    from kInput import InputTab
    from kEdit import EditTab
    from kSet import SettingTab
    from kRep import ReportTab  # <--- Đã thêm module Báo cáo mới
except Exception as e:
    app = QApplication(sys.argv)
    QMessageBox.critical(None, "Lỗi Khởi Động", f"Không thể tải các file thành phần:\n{str(e)}\n\nHãy kiểm tra xem các file cần thiết đã có trong thư mục chưa.")
    sys.exit(1)

LOG_PATH = "Logfile"

# --- STYLE MÀU SẮC CHUẨN (ĐỒNG BỘ) ---
BTN_STYLE_BLUE = "QPushButton { background-color: #E3F2FD; color: #1565C0; border: 1px solid #BBDEFB; border-radius: 4px; padding: 8px 16px; font-weight: 600; } QPushButton:hover { background-color: #BBDEFB; }"
BTN_STYLE_RED  = "QPushButton { background-color: #FFEBEE; color: #C62828; border: 1px solid #FFCDD2; border-radius: 4px; padding: 6px 12px; font-weight: 600; } QPushButton:hover { background-color: #FFCDD2; }"

# --- DATABASE INIT ---
def init_db():
    global LOG_PATH
    cfg = ConfigParser()
    if os.path.exists("config.ini"):
        try:
            cfg.read("config.ini", encoding="utf-8")
            if cfg.has_section("system"):
                LOG_PATH = cfg["system"].get("log_path", "Logfile")
        except: pass

    try:
        db_conn = DatabaseConnection()
        conn = db_conn.connect()
    except ValueError:
        return
    except Exception as e:
        QMessageBox.critical(None, "Lỗi Kết Nối", f"Không thể kết nối database:\n{str(e)}")
        return

    cursor = conn.cursor()

    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
        CREATE TABLE users (
            username NVARCHAR(255) PRIMARY KEY,
            password NVARCHAR(255),
            fullname NVARCHAR(255),
            email NVARCHAR(255),
            role NVARCHAR(50)
        )
    """)

    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'requests')
        CREATE TABLE requests (
            id INT IDENTITY(1,1) PRIMARY KEY,
            request_no NVARCHAR(255), request_date NVARCHAR(255), requester NVARCHAR(255), factory NVARCHAR(255),
            project NVARCHAR(255), phase NVARCHAR(255), category NVARCHAR(255), detail NVARCHAR(MAX), qty NVARCHAR(255),
            cos NVARCHAR(MAX), hcross NVARCHAR(MAX), xcross NVARCHAR(MAX), func_test NVARCHAR(MAX),
            cos_res NVARCHAR(255), xhatch_res NVARCHAR(255), xsection_res NVARCHAR(255), func_res NVARCHAR(255), final_res NVARCHAR(255),
            equip_no NVARCHAR(255), equip_name NVARCHAR(255), test_condition NVARCHAR(MAX),
            plan_start NVARCHAR(255), plan_end NVARCHAR(255), status NVARCHAR(255), dri NVARCHAR(255),
            actual_start NVARCHAR(255), actual_end NVARCHAR(255), logfile NVARCHAR(MAX), log_link NVARCHAR(MAX), note NVARCHAR(MAX)
        )
    """)

    cursor.execute("""
        IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('requests') AND name = 'function')
        BEGIN
            EXEC sp_rename 'requests.function', 'func_test', 'COLUMN'
        END
    """)

    for t in ["factory", "project", "phase", "category", "status"]:
        cursor.execute(f"""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '{t}')
            CREATE TABLE {t} (name NVARCHAR(255) PRIMARY KEY)
        """)

    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'equipment')
        CREATE TABLE equipment (
            factory NVARCHAR(255),
            control_no NVARCHAR(255) PRIMARY KEY,
            name NVARCHAR(255),
            spec NVARCHAR(MAX),
            r1 NVARCHAR(MAX), r2 NVARCHAR(MAX), r3 NVARCHAR(MAX), r4 NVARCHAR(MAX), r5 NVARCHAR(MAX),
            remark NVARCHAR(MAX)
        )
    """)

    count_result = cursor.execute("SELECT COUNT(*) FROM users").fetchone()
    if count_result[0] == 0:
        h = hashlib.sha256("1".encode()).hexdigest()
        cursor.execute("INSERT INTO users VALUES (?,?,?,?,?)", ("admin", h, "Administrator", "admin@local", "Super"))

    conn.commit()
    conn.close()

# --- LOGIN & REGISTER DIALOGS ---
LOGIN_CSS = """
    QDialog { background-color: #FFFFFF; }
    QLabel#Header { color: #1565C0; font-weight: 900; font-size: 24px; margin-bottom: 20px; }
    QLineEdit { 
        border: 1px solid #CFD8DC; border-radius: 4px; padding: 5px 10px; font-size: 14px; 
        background-color: #FAFAFA; min-height: 35px; margin-bottom: 5px;
    }
    QLineEdit:focus { border: 2px solid #2196F3; background-color: #FFFFFF; }
    QPushButton#LinkBtn { border: none; background: transparent; color: #666; text-align: left; }
    QPushButton#LinkBtn:hover { color: #1976D2; text-decoration: underline; }
"""

class RegisterDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Đăng Ký")
        self.setFixedSize(350, 350)
        self.setStyleSheet(LOGIN_CSS)
        
        l = QVBoxLayout(self); l.setContentsMargins(30,30,30,30); l.setSpacing(10)
        l.addWidget(QLabel("ĐĂNG KÝ MỚI", objectName="Header"), alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.u = QLineEdit(); self.u.setPlaceholderText("Tên đăng nhập"); self.u.setFixedHeight(40)
        self.p = QLineEdit(); self.p.setPlaceholderText("Mật khẩu"); self.p.setEchoMode(QLineEdit.EchoMode.Password); self.p.setFixedHeight(40)
        self.n = QLineEdit(); self.n.setPlaceholderText("Họ và Tên"); self.n.setFixedHeight(40)
        self.e = QLineEdit(); self.e.setPlaceholderText("Email"); self.e.setFixedHeight(40)
        
        for w in [self.u, self.p, self.n, self.e]: l.addWidget(w)
        btn = QPushButton("ĐĂNG KÝ NGAY"); btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(BTN_STYLE_BLUE)
        btn.clicked.connect(self.reg)
        l.addWidget(btn)

    def reg(self):
        u, p, n = self.u.text().strip(), self.p.text().strip(), self.n.text().strip()
        if not u or not p: return QMessageBox.warning(self, "Lỗi", "Nhập đủ thông tin!")
        try:
            db_conn = DatabaseConnection()
            conn = db_conn.connect()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?)", (u, hashlib.sha256(p.encode()).hexdigest(), n, self.e.text(), "Operator"))
            conn.commit(); conn.close()
            QMessageBox.information(self, "Thành công", "Đăng ký thành công!"); self.accept()
        except: QMessageBox.warning(self, "Lỗi", "Tài khoản đã tồn tại!")

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Đăng Nhập")
        self.setFixedSize(400, 320)
        self.setStyleSheet(LOGIN_CSS)
        self.user_info = None
        
        l = QVBoxLayout(self); l.setContentsMargins(40, 40, 40, 40); l.setSpacing(15)
        l.addWidget(QLabel("HỆ THỐNG RELIABILITY", objectName="Header"), alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.u = QLineEdit(); self.u.setPlaceholderText("Tên tài khoản"); self.u.setFixedHeight(45)
        self.p = QLineEdit(); self.p.setPlaceholderText("Mật khẩu"); self.p.setEchoMode(QLineEdit.EchoMode.Password); self.p.setFixedHeight(45)
        self.p.returnPressed.connect(self.login)
        
        cfg = ConfigParser()
        if os.path.exists("config.ini"):
            cfg.read("config.ini", encoding="utf-8")
            if cfg.has_section("login"): self.u.setText(cfg["login"].get("user", ""))
        
        l.addWidget(self.u); l.addWidget(self.p)
        
        h = QHBoxLayout()
        btn_reg = QPushButton("Đăng ký mới?", objectName="LinkBtn"); btn_reg.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reg.clicked.connect(lambda: RegisterDialog().exec())
        self.rem = QCheckBox("Ghi nhớ"); self.rem.setChecked(True); self.rem.setCursor(Qt.CursorShape.PointingHandCursor)
        h.addWidget(btn_reg); h.addStretch(); h.addWidget(self.rem)
        l.addLayout(h)
        
        btn = QPushButton("ĐĂNG NHẬP"); btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(BTN_STYLE_BLUE)
        btn.clicked.connect(self.login); l.addWidget(btn)

    def login(self):
        u, p = self.u.text().strip(), self.p.text().strip()
        h = hashlib.sha256(p.encode()).hexdigest()
        try:
            db_conn = DatabaseConnection()
            conn = db_conn.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT fullname, role FROM users WHERE username=? AND password=?", (u, h))
            row = cursor.fetchone()
            conn.close()
            if row:
                cfg = ConfigParser(); cfg.read("config.ini", encoding="utf-8")
                if not cfg.has_section("login"): cfg.add_section("login")
                if self.rem.isChecked(): cfg["login"]["user"] = u
                elif cfg.has_option("login", "user"): cfg.remove_option("login", "user")
                with open("config.ini", "w", encoding="utf-8") as f: cfg.write(f)
                self.user_info = {"name": row[0], "role": row[1]}
                self.accept()
            else: QMessageBox.warning(self, "Lỗi", "Sai thông tin đăng nhập!")
        except Exception as e: QMessageBox.critical(self, "Lỗi DB", str(e))

# --- MAIN WINDOW ---
class MainWindow(QMainWindow):
    def __init__(self, info):
        super().__init__()
        self.info = info
        self.is_logout = False
        self.setWindowTitle(f"kRel - Quản Lý Reliability Test")
        
        screen = QApplication.primaryScreen().availableGeometry()
        w = int(screen.width() * 0.90); h = int(screen.height() * 0.90)
        self.setGeometry((screen.width()-w)//2, (screen.height()-h)//2, w, h)
        
        # Toolbar
        tb = self.addToolBar("Main"); tb.setMovable(False)
        tb.setStyleSheet("QToolBar { background: #FFFFFF; border-bottom: 1px solid #E0E0E0; padding: 8px; spacing: 10px; }")
        
        sl = QWidget(); sl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred); tb.addWidget(sl)
        lbl_app = QLabel("HỆ THỐNG RELIABILITY"); lbl_app.setStyleSheet("font-size: 20px; font-weight: 900; color: #1565C0;")
        tb.addWidget(lbl_app)
        sr = QWidget(); sr.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred); tb.addWidget(sr)
        
        lbl_hello = QLabel(f"Xin chào: <b style='color:#1976D2'>{info['name']}</b>"); lbl_hello.setStyleSheet("font-size: 14px; color: #333; margin-right: 15px;")
        tb.addWidget(lbl_hello)
        
        btn_logout = QPushButton("Đăng xuất"); btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_logout.setStyleSheet(BTN_STYLE_RED)
        btn_logout.clicked.connect(self.logout)
        tb.addWidget(btn_logout)

        # Tabs
        try:
            tabs = QTabWidget()
            tabs.setStyleSheet("""
                QTabWidget::pane { border: 1px solid #E0E0E0; background: white; border-radius: 4px; top: -1px; }
                QTabBar::tab { background: #F5F5F5; color: #555; padding: 8px 30px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; font-size: 13px; font-weight: 600; border: 1px solid #E0E0E0; border-bottom: none; }
                QTabBar::tab:selected { background: #FFFFFF; color: #1565C0; border-top: 3px solid #1565C0; border-bottom: 1px solid #FFFFFF; }
                QTabBar::tab:hover:!selected { background: #E3F2FD; }
            """)
            
            # --- ADD TABS ---
            tabs.addTab(InputTab(None, LOG_PATH, info), "NHẬP LIỆU")
            tabs.addTab(EditTab(None), "DỮ LIỆU")
            tabs.addTab(ReportTab(None), "BÁO CÁO")
            tabs.addTab(SettingTab(info['role'], None), "CÀI ĐẶT")
            
            self.setCentralWidget(tabs)
        except Exception as e: 
            raise Exception(f"Lỗi Khởi tạo Tab:\n{traceback.format_exc()}")

    def logout(self):
        if QMessageBox.question(self, "Đăng xuất", "Bạn có muốn đăng xuất?", QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.is_logout = True; self.close()
            
    def closeEvent(self, e):
        if self.is_logout: e.accept()
        else:
            if QMessageBox.question(self, "Thoát", "Thoát chương trình?", QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes: e.accept()
            else: e.ignore()

# --- MAIN ENTRY ---
if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyle("Fusion")
    if os.path.exists("Ka.ico"): app.setWindowIcon(QIcon("Ka.ico"))
    
    # Error Handling Global
    sys.excepthook = lambda c, e, t: QMessageBox.critical(None, "Lỗi Nghiêm Trọng", "".join(traceback.format_exception(c, e, t)))
    
    while True:
        try:
            init_db()
        except:
            pass

        dlg = LoginDialog()
        if os.path.exists("Ka.ico"): dlg.setWindowIcon(QIcon("Ka.ico"))

        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                win = MainWindow(dlg.user_info)
                if os.path.exists("Ka.ico"): win.setWindowIcon(QIcon("Ka.ico"))
                win.show()
                app.exec()
                if not win.is_logout: break
            except Exception as e:
                QMessageBox.critical(None, "Lỗi Vận Hành", f"Lỗi:\n{str(e)}")
                break
        else:
            break