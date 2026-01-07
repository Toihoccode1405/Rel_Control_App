"""
kRel - Application Constants
Định nghĩa tất cả các hằng số, styles, và cấu hình toàn cục
"""

# ========== APPLICATION INFO ==========
APP_NAME = "kRel"
APP_TITLE = "kRel - Quản Lý Reliability Test"
APP_VERSION = "2.0.0"

# ========== DATE/TIME FORMATS ==========
DATE_FORMAT = "yyyy-MM-dd"
DATETIME_FORMAT = "yyyy-MM-dd HH:mm"
DATE_FORMAT_DISPLAY = "dd/MM/yyyy"
DATETIME_FORMAT_DISPLAY = "dd/MM/yyyy HH:mm"
REQUEST_CODE_FORMAT = "{date}-{seq:03d}"

# ========== USER ROLES ==========
ROLES = ["Operator", "Engineer", "Manager", "Super"]
ROLE_SUPER = "Super"
ROLE_MANAGER = "Manager"
ROLE_ENGINEER = "Engineer"
ROLE_OPERATOR = "Operator"

# ========== FINAL RESULTS ==========
FINAL_RESULTS = ["-", "Pass", "Fail", "Waiver"]

# ========== STATUS OPTIONS ==========
DEFAULT_STATUSES = ["Not Start", "Pending", "Wait", "Ongoing", "Running", "Done", "Finish", "Stop", "Fail", "Cancel"]

# ========== TEST PAIRS MAPPING ==========
# (db_field, result_field, label, result_label)
TEST_PAIRS = [
    ("cos", "cos_res", "Ngoại quan", "KQ N.Quan"),
    ("hcross", "xhatch_res", "Cross Hatch", "KQ X-Hatch"),
    ("xcross", "xsection_res", "Cross Section", "KQ X-Section"),
    ("func_test", "func_res", "Tính năng", "KQ Tính năng")
]

# ========== STATUS COLORS ==========
STATUS_COLORS = {
    "Done": "#E8F5E9",
    "Finish": "#E8F5E9",
    "Ongoing": "#E3F2FD",
    "Running": "#E3F2FD",
    "Pending": "#FFFDE7",
    "Wait": "#FFFDE7",
    "Stop": "#FFEBEE",
    "Fail": "#FFEBEE",
    "Cancel": "#F3E5F5",
    "Not Start": "#FAFAFA"
}
EMPTY_CELL_COLOR = "#FFF9C4"

# ========== GANTT CHART COLORS ==========
PASTEL_COLORS = [
    "#FFB7B2", "#FFDAC1", "#E2F0CB", "#B5EAD7", "#C7CEEA",
    "#F8BBD0", "#E1BEE7", "#D1C4E9", "#C5CAE9", "#BBDEFB",
    "#B3E5FC", "#B2EBF2", "#B2DFDB", "#C8E6C9", "#DCEDC8",
    "#F0F4C3", "#FFF9C4", "#FFECB3", "#FFE0B2", "#FFCCBC"
]

# ========== EDIT TAB HEADERS ==========
EDIT_HEADERS = [
    "ID", "Mã YC", "Ngày YC", "Người YC", "Nhà máy", "Dự án", "Giai đoạn",
    "Hạng mục", "Loại Test", "SL", "Ngoại quan", "KQ Ngoại Quan", "Cross hatch",
    "KQ X-Hatch", "Cross section", "KQ X-Section", "Tính năng", "KQ Tính Năng",
    "KQ Cuối", "Mã TB", "Tên TB", "Điều kiện", "Vào KH", "Ra KH", "Trạng thái",
    "DRI", "Vào TT", "Ra TT", "Logfile", "Link", "Ghi chú"
]

# Column indices
COL_ID = 0
COL_REQUEST_NO = 1
COL_REQUEST_DATE = 2
COL_REQUESTER = 3
COL_FACTORY = 4
COL_PROJECT = 5
COL_PHASE = 6
COL_CATEGORY = 7
COL_DETAIL = 8
COL_QTY = 9
COL_FINAL_RES = 18
COL_EQUIP_NO = 19
COL_EQUIP_NAME = 20
COL_CONDITION = 21
COL_PLAN_START = 22
COL_PLAN_END = 23
COL_STATUS = 24
COL_DRI = 25
COL_ACTUAL_START = 26
COL_ACTUAL_END = 27
COL_LOGFILE = 28
COL_LOG_LINK = 29
COL_NOTE = 30

FROZEN_COLUMNS = 4

# ========== EQUIPMENT HEADERS ==========
EQUIP_HEADERS = [
    "Nhà máy", "Mã TB", "Tên TB", "Thông số",
    "Recipe 1", "Recipe 2", "Recipe 3", "Recipe 4", "Recipe 5",
    "Ghi chú"
]

# ========== LOOKUP TABLES ==========
LOOKUP_TABLES = {
    "Nhà máy": "factory",
    "Dự án": "project", 
    "Giai đoạn": "phase",
    "Hạng mục": "category",
    "Trạng thái": "status"
}

# ========== DATABASE FIELDS MAPPING ==========
REQUEST_DB_FIELDS = [
    "id", "request_no", "request_date", "requester", "factory", "project",
    "phase", "category", "detail", "qty", "cos", "cos_res", "hcross",
    "xhatch_res", "xcross", "xsection_res", "func_test", "func_res",
    "final_res", "equip_no", "equip_name", "test_condition", "plan_start",
    "plan_end", "status", "dri", "actual_start", "actual_end", "logfile",
    "log_link", "note"
]

# ========== FILE PATHS ==========
DEFAULT_LOG_PATH = "Logfile"
CONFIG_FILE = "config.ini"
KEY_FILE = ".dbkey"

# ========== ASSETS PATHS ==========
ASSETS_DIR = "assets"
IMAGES_DIR = "assets/images"
ICON_FILE = "assets/images/Ka.ico"
LOGO_FILE = "assets/images/Ka.png"

# ========== INPUT FORM FIELDS ==========
# (key, label, type, readonly)
TOP_FIELDS = [
    ("request_no", "Mã yêu cầu", "line", True),
    ("request_date", "Ngày tạo", "datetime", False),
    ("requester", "Người yêu cầu", "line", False),
    ("factory", "Nhà máy", "combo", False),
    ("project", "Dự án", "combo", False),
    ("phase", "Giai đoạn", "combo", False),
    ("category", "Hạng mục", "combo", False),
    ("equip_no", "Mã thiết bị", "combo", False),
    ("equip_name", "Tên thiết bị", "line", True),
    ("test_condition", "Điều kiện", "combo", False),
    ("qty", "Số lượng", "line", False),
]

BOTTOM_FIELDS = [
    ("final_res", "KQ Cuối", "combo", False),
    ("status", "Trạng thái", "combo", False),
]

SCHEDULE_FIELDS = [
    ("plan_start", "Vào KH"),
    ("plan_end", "Ra KH"),
    ("actual_start", "Vào TT"),
    ("actual_end", "Ra TT"),
]

