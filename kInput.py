# kInput.py - AUTO FILL RESULT & FIX REQUEST CODE INIT - SQL SERVER SUPPORT
from PyQt6.QtCore import QDateTime, Qt, QDate
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont, QIcon
import os, shutil
import pandas as pd
from kDb import DatabaseConnection

# --- CSS GIẢM PADDING CHO GROUPBOX ---
COMPACT_STYLE = """
    QGroupBox { 
        font-weight: bold; color: #1565C0; 
        border: 1px solid #CCC; border-radius: 4px; 
        margin-top: 6px; padding-top: 8px; 
    }
    QGroupBox::title { 
        subcontrol-origin: margin; left: 8px; padding: 0 3px; background-color: #F0F0F0; 
    }
    QLabel { font-size: 11px; } 
    QLineEdit, QComboBox, QDateTimeEdit { font-size: 11px; padding: 2px; }
"""

class InputTab(QWidget):
    TOP_FIELDS = [
        ("Mã Yêu cầu","request_no"), ("Ngày yêu cầu","request_date"), ("Người yêu cầu","requester"), ("Nhà máy","factory"),
        ("Dự án","project"), ("Giai đoạn","phase"), ("Hạng mục","category"), ("Mã Thiết bị","equip_no"),
        ("Tên Thiết bị","equip_name"), ("Số lượng","qty"), ("Loại Test","detail"), ("Điều kiện test","test_condition")
    ]
    BOTTOM_FIELDS = [("KQ Cuối","final_res"), ("Trạng thái","status")]
    COMBO_FIELDS = ["factory","project","phase","category","equip_no","status"]
    TEST_PAIRS = [
        ("cos", "cos_res", "Ngoại quan", "KQ N.Quan"),
        ("hcross", "xhatch_res", "Cross Hatch", "KQ X-Hatch"),
        ("xcross", "xsection_res", "Cross Section", "KQ X-Section"),
        ("func_test", "func_res", "Tính năng", "KQ Tính năng")
    ]

    def __init__(self, db_path, log_path, user_info):
        super().__init__()
        self.db_path = db_path; self.log_path = log_path; self.user_info = user_info
        db_conn = DatabaseConnection()
        self.conn = db_conn.connect(); os.makedirs(self.log_path, exist_ok=True)
        self.w = {}
        
        self.setStyleSheet(COMPACT_STYLE)
        main_layout = QVBoxLayout(self); main_layout.setSpacing(5); main_layout.setContentsMargins(5, 5, 5, 5)

        # --- A. GRID NHẬP LIỆU CHÍNH ---
        grid = QGridLayout(); grid.setSpacing(4)
        
        # 1. Top Fields
        r, c = 0, 0; MAX_COLS = 4 
        for label, field in self.TOP_FIELDS:
            self.create_widget(grid, label, field, r, c)
            c += 1; 
            if c >= MAX_COLS: c, r = 0, r + 1

        # 2. Test Pairs
        if c > 0: r += 1
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setFrameShadow(QFrame.Shadow.Sunken)
        grid.addWidget(line, r, 0, 1, 8); r += 1

        for i, (inp_k, _, lbl_inp, _) in enumerate(self.TEST_PAIRS): self.create_widget(grid, lbl_inp, inp_k, r, i)
        r += 1 
        for i, (_, res_k, _, lbl_res) in enumerate(self.TEST_PAIRS): self.create_widget(grid, lbl_res, res_k, r, i, is_result=True)
        r += 1

        # 3. Bottom Fields
        c = 0
        for label, field in self.BOTTOM_FIELDS:
            self.create_widget(grid, label, field, r, c)
            c += 1
            if c >= MAX_COLS: c, r = 0, r + 1
            
        for i in range(MAX_COLS): grid.setColumnStretch(i * 2 + 1, 1)
        main_layout.addLayout(grid)
        
        for inp, res, _, _ in self.TEST_PAIRS: self.setup_auto_hint(inp, res)

        # --- B. KHU VỰC DƯỚI (COMPACT) ---
        bot_layout = QHBoxLayout(); bot_layout.setSpacing(5)

        # CỘT 1: TIẾN ĐỘ
        grp_date = QGroupBox("Tiến độ"); 
        dg = QGridLayout(grp_date); dg.setSpacing(4); dg.setContentsMargins(4, 10, 4, 4)
        for ti, k, dr, dc in [("Vào KH", "plan_start",0,0), ("Ra KH", "plan_end",0,1), ("Vào TT", "actual_start",1,0), ("Ra TT", "actual_end",1,1)]:
            l = QLabel(ti); l.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
            dg.addWidget(l, dr, dc*2)
            dt = QDateTimeEdit(); dt.setCalendarPopup(True); dt.setDisplayFormat("MM-dd HH:mm")
            dt.setDateTime(QDateTime.currentDateTime()) 
            dg.addWidget(dt, dr, dc*2+1); self.w[k] = dt
        bot_layout.addWidget(grp_date, stretch=3)

        # CỘT 2: THÔNG TIN
        grp_note = QGroupBox("Thông tin"); 
        gn = QGridLayout(grp_note); gn.setSpacing(4); gn.setContentsMargins(4, 10, 4, 4)
        
        gn.addWidget(QLabel("Log:"), 0, 0)
        lw = QWidget(); lh = QHBoxLayout(lw); lh.setContentsMargins(0,0,0,0); lh.setSpacing(2)
        self.log_lbl = QLabel("..."); self.log_lbl.setStyleSheet("color: #777;")
        btn_log = QPushButton("File"); btn_log.setCursor(Qt.CursorShape.PointingHandCursor); btn_log.setFixedWidth(40)
        btn_log.clicked.connect(self.pick_log)
        lh.addWidget(self.log_lbl); lh.addWidget(btn_log)
        gn.addWidget(lw, 0, 1)
        self.w["logfile"] = self.log_lbl

        gn.addWidget(QLabel("Note:"), 1, 0)
        self.w["note"] = QLineEdit(); self.w["note"].setPlaceholderText("...")
        gn.addWidget(self.w["note"], 1, 1)
        
        self.w["log_link"] = QLineEdit() 
        
        gn.addWidget(QLabel("DRI:"), 2, 0)
        dri_txt = QLineEdit(self.user_info['name']); dri_txt.setReadOnly(True); dri_txt.setStyleSheet("background:#F5F5F5;")
        gn.addWidget(dri_txt, 2, 1)
        
        bot_layout.addWidget(grp_note, stretch=4)

        # CỘT 3: NÚT LƯU
        btn_layout = QVBoxLayout(); btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_save = QPushButton("LƯU"); 
        btn_save.setFixedHeight(40)
        btn_save.setStyleSheet("""
            QPushButton { 
                background-color: #2E7D32; color: white; 
                font-weight: bold; border-radius: 4px;
            }
            QPushButton:hover { background-color: #388E3C; }
        """)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        btn_save.clicked.connect(self.save)
        btn_layout.addWidget(btn_save)
        bot_layout.addLayout(btn_layout, stretch=1)

        main_layout.addLayout(bot_layout)

        # --- C. BẢNG DANH SÁCH ---
        main_layout.addWidget(QLabel("<b>Danh sách nhập trong ngày</b>"))
        
        self.tbl = QTableView(); self.tbl.setAlternatingRowColors(True); self.tbl.verticalHeader().hide()
        self.tbl.setMinimumHeight(250)
        main_layout.addWidget(self.tbl, stretch=1) 
        
        # --- FIX 1: Tự động điền Mã Yêu Cầu khi mở ---
        self.update_code(QDate.currentDate())
        # ---------------------------------------------
        
        self.load_recent()

    def create_widget(self, grid, label_text, field_name, r, c, is_result=False):
        lbl = QLabel(f"{label_text}:")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if is_result: lbl.setStyleSheet("font-weight: bold; color: #333;")
        grid.addWidget(lbl, r, c * 2)

        w = None
        if field_name == "request_no": w = QLineEdit(); w.setPlaceholderText("yyyymmdd-sss")
        elif field_name == "request_date":
            w = QDateTimeEdit(); w.setCalendarPopup(True); w.setDisplayFormat("yyyy-MM-dd"); w.setDateTime(QDateTime.currentDateTime()); w.dateChanged.connect(self.update_code)
        elif field_name == "equip_no":
            w = QComboBox(); w.setEditable(True); self.load_combo(w, field_name); w.currentTextChanged.connect(self.on_equip_change)
        elif field_name == "equip_name":
            w = QLineEdit(); w.setReadOnly(True); w.setPlaceholderText("Auto..."); w.setStyleSheet("background-color: #F0F0F0;")
        elif field_name == "final_res": w = QComboBox(); w.addItems(["-", "Pass", "Fail", "Waiver"])
        elif field_name == "test_condition": w = QComboBox(); w.setEditable(True); w.setPlaceholderText("...")
        elif field_name in self.COMBO_FIELDS: w = QComboBox(); w.setEditable(True); self.load_combo(w, field_name)
        else: w = QLineEdit()

        if is_result:
            w.setStyleSheet("background-color: #FFFDE7; border: 1px solid #CCC; border-radius: 3px;") 
            # Không cần placeholder tĩnh nữa vì sẽ tự điền text
            
        self.w[field_name] = w
        grid.addWidget(w, r, c * 2 + 1)

    # --- FIX 2: HÀM TỰ ĐỘNG ĐIỀN KẾT QUẢ ---
    def setup_auto_hint(self, src_key, dest_key):
        if src_key not in self.w or dest_key not in self.w: return
        src_w = self.w[src_key]; dest_w = self.w[dest_key]
        
        def update_text(text):
            val = text.strip()
            # Nếu có giá trị nhập vào thì điền xxF/zzT, nếu không thì xóa trắng
            if val:
                dest_w.setText(f"xxF/{val}T")
            else:
                dest_w.clear()
                
        if isinstance(src_w, QLineEdit): src_w.textChanged.connect(update_text)
        elif isinstance(src_w, QComboBox): src_w.currentTextChanged.connect(update_text)
    # ----------------------------------------

    def update_code(self, d): self.w["request_no"].setText(self.gen_code(d))
    def gen_code(self, d):
        s = d.toString("yyyyMMdd")
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT request_no FROM requests WHERE request_no LIKE ? ORDER BY id DESC LIMIT 1", (f"{s}-%",))
            r = cursor.fetchone()
            if r: return f"{s}-{int(r[0].split('-')[1])+1:03d}"
        except: pass
        return f"{s}-001"
    def on_equip_change(self, txt):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, r1, r2, r3, r4, r5 FROM equipment WHERE control_no=?", (txt,))
        r = cursor.fetchone()
        if r:
            self.w["equip_name"].setText(r[0] or "")
            cb = self.w["test_condition"]; cb.clear(); cb.addItems([str(x) for x in r[1:] if x and str(x).strip()])
    def load_combo(self, c, f):
        t = {"factory":"factory","project":"project","phase":"phase","category":"category","equip_no":"equipment.control_no","status":"status"}.get(f)
        c.clear(); c.addItem("")
        if t:
            col, tbl = ("control_no", "equipment") if "control_no" in t else ("name", t)
            try:
                cursor = self.conn.cursor()
                cursor.execute(f"SELECT {col} FROM {tbl} ORDER BY {col}")
                for r in cursor.fetchall(): c.addItem(r[0] or "")
            except: pass
    def pick_log(self):
        f, _ = QFileDialog.getOpenFileName(self, "Chọn File Log")
        if f:
            self.log_lbl.setText(os.path.basename(f)[:15]+"..."); self.log_lbl.setToolTip(os.path.basename(f)); self.log_lbl.path = f
            req_no = self.w["request_no"].text().strip() or "Unknown"
            self.w["log_link"].setText(os.path.join(self.log_path, req_no, os.path.basename(f)))
    def save(self):
        v = []; c = []
        all_main_fields = self.TOP_FIELDS + self.BOTTOM_FIELDS + [(p[0], p[0]) for p in self.TEST_PAIRS] + [(p[1], p[1]) for p in self.TEST_PAIRS]
        
        def get_val(key):
            if key not in self.w: return ""
            w = self.w[key]
            if key == "logfile": return os.path.basename(getattr(w, 'path', ''))
            elif key == "request_date": return w.dateTime().toString("yyyy-MM-dd")
            elif isinstance(w, QDateTimeEdit): return w.dateTime().toString("yyyy-MM-dd HH:mm")
            elif isinstance(w, QComboBox): return w.currentText()
            else: return w.text()

        processed = set()
        for _, k in all_main_fields:
            if k in processed: continue
            c.append(k); v.append(get_val(k)); processed.add(k)
        
        for k in ["log_link", "note"]: c.append(k); v.append(get_val(k))
        for k in ["plan_start", "plan_end", "actual_start", "actual_end"]: c.append(k); v.append(self.w[k].dateTime().toString("yyyy-MM-dd HH:mm:ss"))
        c.append("dri"); v.append(self.user_info['name'])
        
        try:
            placeholders = ','.join(['?']*len(v))
            columns = ','.join(c)
            cursor = self.conn.cursor()
            cursor.execute(f"INSERT INTO requests ({columns}) VALUES ({placeholders})", v)
            self.conn.commit()
            if hasattr(self.log_lbl, 'path'):
                dest = os.path.join(self.log_path, self.w["request_no"].text().strip() or "Unknown"); os.makedirs(dest, exist_ok=True); shutil.copy(self.log_lbl.path, dest)
            QMessageBox.information(self, "Thành công", "Đã lưu!"); self.clear(); self.load_recent()
        except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))

    def clear(self):
        self.w["request_no"].setText(self.gen_code(QDate.currentDate()))
        self.w["logfile"].setText("..."); delattr(self.w["logfile"], 'path') if hasattr(self.w["logfile"],'path') else None
        if "log_link" in self.w: self.w["log_link"].clear()
        for k in ["plan_start", "plan_end", "actual_start", "actual_end"]: self.w[k].setDateTime(QDateTime.currentDateTime())
        exclude = ["request_no", "request_date", "plan_start", "plan_end", "actual_start", "actual_end", "logfile", "log_link", "dri"]
        for k, w in self.w.items():
            if k not in exclude:
                if isinstance(w, QLineEdit): w.clear()
                elif isinstance(w, QComboBox): w.setCurrentIndex(0)

    def load_recent(self):
        try:
            today_str = QDate.currentDate().toString("yyyy-MM-dd")
            query = """
                SELECT request_no, request_date, requester, factory, project, phase, 
                       equip_no, equip_name, test_condition, 
                       plan_start, plan_end, actual_start, actual_end, 
                       status, dri, final_res 
                FROM requests WHERE request_date = ? ORDER BY id DESC
            """
            df = pd.read_sql_query(query, self.conn, params=(today_str,))
            m = QStandardItemModel()
            m.setHorizontalHeaderLabels(["Mã YC", "Ngày YC", "Người YC", "Nhà Máy", "Dự Án", "Giai Đoạn", "Mã TB", "Tên TB", "ĐK Test", "Vào KH", "Ra KH", "Vào TT", "Ra TT", "Trạng Thái", "DRI", "KQ Cuối"])
            for _, r in df.iterrows(): m.appendRow([QStandardItem(str(v) if v is not None else "") for v in r])
            self.tbl.setModel(m)
            
            # --- CÂN ĐỐI CỘT TỰ ĐỘNG ---
            header = self.tbl.horizontalHeader()
            
            # 1. Mặc định tất cả co gọn (Tiết kiệm chỗ)
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            
            # 2. Những cột dài -> Cho phép giãn (Stretch) để chiếm chỗ trống
            # Col 4: Dự Án, Col 7: Tên TB, Col 5: Giai Đoạn
            #header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) 
            #header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) 
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
            #header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
            
        except: pass