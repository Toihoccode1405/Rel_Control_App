"""
kRel - Application Styles
Định nghĩa tất cả CSS/QSS styles cho UI

Design System:
- Spacing: 4, 8, 12, 16, 24, 32 px
- Font sizes: 11 (small), 13 (body), 15 (subtitle), 18 (title), 22 (header)
- Border-radius: 4px (small), 6px (medium), 8px (large)
- Colors: Primary (#1565C0), Success (#2E7D32), Warning (#EF6C00), Error (#C62828)
"""

# ========== DESIGN TOKENS ==========
COLORS = {
    "primary": "#1565C0",
    "primary_light": "#E3F2FD",
    "primary_border": "#BBDEFB",
    "primary_bg": "#F0F7FF",
    "success": "#2E7D32",
    "success_light": "#E8F5E9",
    "success_border": "#C8E6C9",
    "warning": "#EF6C00",
    "warning_light": "#FFF3E0",
    "warning_border": "#FFE0B2",
    "error": "#C62828",
    "error_light": "#FFEBEE",
    "error_border": "#FFCDD2",
    "text_primary": "#212121",
    "text_secondary": "#666666",
    "text_disabled": "#BDBDBD",
    "background": "#FFFFFF",
    "background_alt": "#F5F7FA",
    "background_section": "#F0F4F8",
    "border": "#E0E0E0",
    "border_light": "#F0F0F0",
}

SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32}
FONT_SIZES = {"xs": 11, "sm": 13, "md": 15, "lg": 18, "xl": 22}
RADIUS = {"sm": 4, "md": 6, "lg": 8}


# ========== BUTTON STYLES ==========
BTN_STYLE_BLUE = """
    QPushButton {
        background-color: #E3F2FD;
        color: #1565C0;
        border: 1px solid #BBDEFB;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 600;
    }
    QPushButton:hover {
        background-color: #BBDEFB;
        border-color: #90CAF9;
    }
    QPushButton:pressed {
        background-color: #90CAF9;
    }
    QPushButton:disabled {
        background-color: #F5F5F5;
        color: #BDBDBD;
        border-color: #E0E0E0;
    }
"""

BTN_STYLE_RED = """
    QPushButton {
        background-color: #FFEBEE;
        color: #C62828;
        border: 1px solid #FFCDD2;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 600;
    }
    QPushButton:hover {
        background-color: #FFCDD2;
        border-color: #EF9A9A;
    }
    QPushButton:pressed {
        background-color: #EF9A9A;
    }
"""

BTN_STYLE_GREEN = """
    QPushButton {
        background-color: #E8F5E9;
        color: #2E7D32;
        border: 1px solid #C8E6C9;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 600;
    }
    QPushButton:hover {
        background-color: #C8E6C9;
        border-color: #A5D6A7;
    }
    QPushButton:pressed {
        background-color: #A5D6A7;
    }
"""

BTN_STYLE_GREEN_SOLID = """
    QPushButton {
        background-color: #2E7D32;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-size: 13px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #388E3C;
    }
    QPushButton:pressed {
        background-color: #1B5E20;
    }
"""

BTN_STYLE_ORANGE = """
    QPushButton {
        background-color: #FFF3E0;
        color: #E65100;
        border: 1px solid #FFE0B2;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 600;
    }
    QPushButton:hover {
        background-color: #FFE0B2;
        border-color: #FFCC80;
    }
    QPushButton:pressed {
        background-color: #FFCC80;
    }
"""

BTN_STYLE_ORANGE_SOLID = """
    QPushButton {
        background-color: #FF9800;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #FB8C00;
    }
    QPushButton:pressed {
        background-color: #F57C00;
    }
"""

# ========== LOGIN DIALOG STYLE ==========
LOGIN_STYLE = """
    QDialog {
        background-color: #FFFFFF;
    }
    QLabel#Header {
        color: #1565C0;
        font-weight: 900;
        font-size: 24px;
        margin-bottom: 16px;
        padding: 0;
    }
    QLineEdit {
        border: 1px solid #CFD8DC;
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 14px;
        color: #212121;
        background-color: #FAFAFA;
        margin: 0;
    }
    QLineEdit:focus {
        border: 2px solid #1565C0;
        background-color: #FFFFFF;
    }
    QCheckBox {
        color: #212121;
        font-size: 13px;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
    }
    QPushButton#LinkBtn {
        border: none;
        background: transparent;
        color: #1565C0;
        text-align: left;
        font-size: 13px;
        padding: 4px;
        font-weight: 500;
    }
    QPushButton#LinkBtn:hover {
        color: #0D47A1;
        text-decoration: underline;
    }
"""

# ========== TAB WIDGET STYLE ==========
TAB_STYLE = """
    QTabWidget::pane {
        border: 1px solid #E0E0E0;
        background: white;
        border-radius: 8px;
        top: -1px;
    }
    QTabBar::tab {
        background: #F5F5F5;
        color: #666;
        padding: 12px 32px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        border: 1px solid #E0E0E0;
        border-bottom: none;
        min-width: 100px;
    }
    QTabBar::tab:selected {
        background: #FFFFFF;
        color: #1565C0;
        border-top: 3px solid #1565C0;
        border-bottom: 1px solid #FFFFFF;
        padding-top: 10px;
    }
    QTabBar::tab:hover:!selected {
        background: #E3F2FD;
        color: #1565C0;
    }
"""

# ========== TOOLBAR STYLE ==========
TOOLBAR_STYLE = """
    QToolBar {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #F0F4F8);
        border-bottom: 2px solid #BBDEFB;
        padding: 8px 16px;
        spacing: 12px;
    }
"""

TOOLBAR_FRAME_STYLE = """
    QFrame {
        background-color: #F0F7FF;
        border: 1px solid #BBDEFB;
        border-radius: 8px;
    }
"""

# ========== TABLE STYLE ==========
TABLE_STYLE = """
    QTableView {
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        gridline-color: #E8EBF0;
        background-color: white;
        alternate-background-color: #F8FAFC;
        selection-background-color: #E3F2FD;
        selection-color: #1565C0;
        font-size: 13px;
        color: #212121;
    }
    QTableView::item {
        padding: 8px 12px;
        border-bottom: 1px solid #E8EBF0;
        color: #212121;
    }
    QTableView::item:selected {
        background-color: #E3F2FD;
        color: #1565C0;
    }
    QHeaderView::section {
        background-color: #E8F0FE;
        color: #212121;
        padding: 10px 12px;
        border: none;
        border-right: 1px solid #E0E0E0;
        border-bottom: 2px solid #BBDEFB;
        font-weight: 600;
        font-size: 13px;
    }
    QHeaderView::section:hover {
        background-color: #BBDEFB;
    }
"""

# ========== GROUPBOX STYLE ==========
GROUPBOX_STYLE = """
    QGroupBox {
        font-weight: 600;
        font-size: 14px;
        color: #1565C0;
       border: 1px solid #BBDEFB;
        border-radius: 8px;
        margin-top: 16px;
        padding: 16px 12px 12px 12px;
       background-color: #F5F9FF;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        padding: 0 8px;
       background-color: #F5F9FF;
    }
"""

GROUPBOX_BLUE_STYLE = """
    QGroupBox {
        font-weight: 600; font-size: 12px; color: #1565C0;
        border: 1px solid #BBDEFB; border-radius: 6px;
        margin-top: 12px; padding: 8px 8px 6px 8px;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #F8FBFF, stop:1 #F0F7FF);
    }
    QGroupBox::title {
        subcontrol-origin: margin; left: 12px; padding: 0 6px;
        background-color: #E3F2FD; border-radius: 3px;
    }
"""

TOOLBAR_BLUE_STYLE = """
    QFrame {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #FFFFFF, stop:0.5 #F8FBFF, stop:1 #F0F7FF);
        border: 1px solid #BBDEFB;
        border-radius: 8px;
        margin: 2px 0;
    }
"""

FILTER_BLUE_STYLE = """
    QFrame {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #F8FBFF, stop:1 #E3F2FD);
        border: 1px solid #BBDEFB;
        border-radius: 8px;
    }
"""

# ========== CARD STYLE ==========
CARD_STYLE = """
    QFrame#Card {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 16px;
    }
    QFrame#Card:hover {
        border-color: #BBDEFB;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
"""

# ========== INPUT FORM STYLE ==========
INPUT_FORM_STYLE = """
    QLabel {
        font-size: 13px;
        color: #424242;
        font-weight: 500;
    }
    QLineEdit, QComboBox, QDateTimeEdit, QDateEdit {
        border: 1px solid #CFD8DC;
        border-radius: 6px;
        padding: 8px 12px;
        background-color: #FAFAFA;
        min-height: 36px;
        font-size: 13px;
        color: #212121;
    }
    QLineEdit:hover, QComboBox:hover, QDateTimeEdit:hover, QDateEdit:hover {
        border-color: #90CAF9;
        background-color: #FFFFFF;
    }
    QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus, QDateEdit:focus {
        border: 2px solid #1565C0;
        background-color: #FFFFFF;
    }
    QLineEdit:read-only {
        background-color: #ECEFF1;
        color: #607D8B;
        border-color: #CFD8DC;
    }
    QLineEdit::placeholder {
        color: #9E9E9E;
    }
    QComboBox::drop-down {
        border: none;
        width: 30px;
    }
    QComboBox::down-arrow {
        width: 12px;
        height: 12px;
    }
    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        color: #212121;
        selection-background-color: #E3F2FD;
        selection-color: #1565C0;
        border: 1px solid #BBDEFB;
        border-radius: 4px;
        padding: 4px;
    }
    QComboBox QAbstractItemView::item {
        padding: 8px 12px;
        min-height: 32px;
    }
    QComboBox QAbstractItemView::item:hover {
        background-color: #F0F7FF;
        color: #1565C0;
    }
    QTextEdit {
        border: 1px solid #CFD8DC;
        border-radius: 6px;
        padding: 8px;
        background-color: #FAFAFA;
        font-size: 13px;
    }
    QTextEdit:focus {
        border: 2px solid #1565C0;
        background-color: #FFFFFF;
    }
"""

# ========== INPUT TAB COMPACT STYLE ==========
INPUT_TAB_STYLE = """
    QGroupBox {
        font-weight: 600;
        font-size: 12px;
        color: #1565C0;
        border: 1px solid #BBDEFB;
        border-radius: 6px;
        margin-top: 8px;
        padding: 8px 6px 6px 6px;
        background-color: #F5F9FF;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
        background-color: #F5F9FF;
    }
    QLabel {
        font-size: 11px;
        color: #424242;
    }
    QLineEdit, QComboBox, QDateTimeEdit {
        font-size: 11px;
        padding: 4px 6px;
        min-height: 22px;
        max-height: 24px;
        border: 1px solid #CFD8DC;
        border-radius: 4px;
        background-color: #FFFFFF;
        color: #212121;
    }
    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        color: #212121;
        selection-background-color: #E3F2FD;
        selection-color: #1565C0;
        border: 1px solid #CFD8DC;
    }
    QComboBox QAbstractItemView::item {
        padding: 4px 8px;
        min-height: 20px;
    }
    QLineEdit:hover, QComboBox:hover, QDateTimeEdit:hover {
        border-color: #90CAF9;
        background-color: #FAFEFF;
    }
    QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus {
        border: 1.5px solid #1565C0;
    }
    QLineEdit:read-only {
        background-color: #ECEFF1;
        color: #757575;
    }
"""

# ========== SETTINGS MENU STYLE ==========
SETTINGS_MENU_STYLE = """
    QListWidget {
        border: none;
        border-right: 2px solid #BBDEFB;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F0F7FF, stop:1 #F8FAFC);
        font-size: 14px;
        outline: none;
    }
    QListWidget::item {
        padding: 18px 20px;
        border-bottom: 1px solid #E3F2FD;
        color: #424242;
        margin-bottom: 2px;
    }
    QListWidget::item:selected {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #BBDEFB, stop:1 #E3F2FD);
        color: #1565C0;
        font-weight: 700;
        border-left: 4px solid #1565C0;
        padding-left: 16px;
    }
    QListWidget::item:hover:!selected {
        background: #E3F2FD;
        color: #1976D2;
    }
"""

# ========== FILTER FRAME STYLE ==========
FILTER_FRAME_STYLE = """
    QFrame {
        background-color: #F0F7FF;
        border: 1px solid #BBDEFB;
        border-radius: 8px;
    }
    QLabel {
        font-size: 13px;
        color: #424242;
        font-weight: 500;
    }
    QComboBox, QDateEdit {
        border: 1px solid #CFD8DC;
        border-radius: 6px;
        padding: 6px 10px;
        background-color: #FFFFFF;
        min-height: 32px;
        font-size: 13px;
    }
    QComboBox:hover, QDateEdit:hover {
        border-color: #90CAF9;
    }
    QComboBox:focus, QDateEdit:focus {
        border: 2px solid #1565C0;
    }
    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        color: #212121;
        selection-background-color: #E3F2FD;
        selection-color: #1565C0;
        border: 1px solid #BBDEFB;
    }
    QComboBox QAbstractItemView::item {
        padding: 6px 10px;
        min-height: 28px;
    }
    QComboBox QAbstractItemView::item:hover {
        background-color: #F0F7FF;
    }
"""

# ========== INFO LABEL STYLE ==========
INFO_LABEL_STYLE = """
    QLabel {
        font-size: 13px;
        color: #1565C0;
        padding: 8px 12px;
        font-weight: 600;
        background: #E3F2FD;
        border: 1px solid #BBDEFB;
        border-radius: 6px;
    }
"""

# ========== RESULT FIELD STYLE ==========
RESULT_FIELD_STYLE = """
    QLineEdit {
        background-color: #FFFDE7;
        border: 1px solid #FFF59D;
        border-radius: 4px;
        font-weight: 500;
    }
    QLineEdit:focus {
        border: 2px solid #FBC02D;
    }
"""

