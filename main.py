"""
kRel - Reliability Test Management System
Main Entry Point (Refactored Version)
"""
import sys
import os
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon, QPalette, QColor

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import APP_TITLE, APP_VERSION, ICON_FILE
from src.services.database import get_db
from src.services.auth import get_auth
from src.services.logger import get_logger_service, get_logger, log_audit

# Initialize logger early
logger = get_logger("main")


def setup_light_palette(app: QApplication):
    """Setup light palette for Fusion style to ensure proper text colors"""
    palette = QPalette()

    # Base colors
    palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))

    # Placeholder text - gray color
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(128, 128, 128))

    # Selection colors
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

    # Link colors
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))

    # ToolTip
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))

    app.setPalette(palette)


def init_database():
    """Initialize database tables if not exist"""
    try:
        db = get_db()
        conn = db.connect()
        cursor = conn.cursor()
        
        # Create users table
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
        
        # Create requests table
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'requests')
            CREATE TABLE requests (
                id INT IDENTITY(1,1) PRIMARY KEY,
                request_no NVARCHAR(255), request_date NVARCHAR(255), 
                requester NVARCHAR(255), factory NVARCHAR(255),
                project NVARCHAR(255), phase NVARCHAR(255), 
                category NVARCHAR(255), detail NVARCHAR(MAX), qty NVARCHAR(255),
                cos NVARCHAR(MAX), hcross NVARCHAR(MAX), xcross NVARCHAR(MAX), 
                func_test NVARCHAR(MAX),
                cos_res NVARCHAR(255), xhatch_res NVARCHAR(255), 
                xsection_res NVARCHAR(255), func_res NVARCHAR(255), 
                final_res NVARCHAR(255),
                equip_no NVARCHAR(255), equip_name NVARCHAR(255), 
                test_condition NVARCHAR(MAX),
                plan_start NVARCHAR(255), plan_end NVARCHAR(255), 
                status NVARCHAR(255), dri NVARCHAR(255),
                actual_start NVARCHAR(255), actual_end NVARCHAR(255), 
                logfile NVARCHAR(MAX), log_link NVARCHAR(MAX), note NVARCHAR(MAX)
            )
        """)
        
        # Create lookup tables
        for table in ["factory", "project", "phase", "category", "status"]:
            cursor.execute(f"""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '{table}')
                CREATE TABLE {table} (name NVARCHAR(255) PRIMARY KEY)
            """)
        
        # Create equipment table
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'equipment')
            CREATE TABLE equipment (
                factory NVARCHAR(255),
                control_no NVARCHAR(255) PRIMARY KEY,
                name NVARCHAR(255),
                spec NVARCHAR(MAX),
                r1 NVARCHAR(MAX), r2 NVARCHAR(MAX), r3 NVARCHAR(MAX), 
                r4 NVARCHAR(MAX), r5 NVARCHAR(MAX),
                remark NVARCHAR(MAX)
            )
        """)
        
        # Create default admin user if no users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            from src.models.user import User
            hashed = User.hash_password("1")
            cursor.execute(
                "INSERT INTO users VALUES (?,?,?,?,?)",
                ("admin", hashed, "Administrator", "admin@local", "Super")
            )
        
        conn.commit()
        return True
        
    except ValueError:
        # No config yet - will be set up in settings
        return False
    except Exception as e:
        QMessageBox.critical(
            None, "Lỗi Khởi Tạo Database",
            f"Không thể khởi tạo database:\n{str(e)}"
        )
        return False


def main():
    """Main application entry point"""
    # Log application start
    logger.info(f"=== kRel v{APP_VERSION} Starting ===")
    log_audit("APP_START", details=f"Version {APP_VERSION}")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Setup light palette to ensure proper text colors on dark-themed Windows
    setup_light_palette(app)

    # Set application icon
    if os.path.exists(ICON_FILE):
        app.setWindowIcon(QIcon(ICON_FILE))

    # Global exception handler
    def exception_handler(exc_type, exc_value, exc_tb):
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logger.error(f"Unhandled exception: {error_msg}", exc_info=True)
        QMessageBox.critical(None, "Lỗi Nghiêm Trọng", error_msg)

    sys.excepthook = exception_handler

    # Main application loop
    while True:
        # Try to initialize database
        logger.debug("Initializing database...")
        init_database()

        # Show login dialog
        from src.views.login_dialog import LoginDialog
        login = LoginDialog()
        if os.path.exists(ICON_FILE):
            login.setWindowIcon(QIcon(ICON_FILE))

        if login.exec() == login.DialogCode.Accepted:
            try:
                # Show main window
                from src.views.main_window import MainWindow
                window = MainWindow(login.user_info)
                if os.path.exists(ICON_FILE):
                    window.setWindowIcon(QIcon(ICON_FILE))
                window.show()
                logger.info(f"Main window opened for user: {login.user_info.get('username', 'unknown')}")
                app.exec()

                # Check if logout or exit
                if not window.is_logout:
                    logger.info("Application exiting normally")
                    log_audit("APP_EXIT", user=login.user_info.get('username', ''))
                    break  # Exit application
                else:
                    logger.info(f"User {login.user_info.get('username', '')} logged out")
                # else: continue loop to show login again

            except Exception as e:
                logger.error(f"Runtime error: {str(e)}", exc_info=True)
                QMessageBox.critical(
                    None, "Lỗi Vận Hành",
                    f"Lỗi:\n{str(e)}\n\n{traceback.format_exc()}"
                )
                break
        else:
            # User closed login dialog
            logger.info("Login cancelled by user")
            break

    logger.info("=== kRel Shutdown ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

