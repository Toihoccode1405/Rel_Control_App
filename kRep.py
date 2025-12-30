# kRep.py - UPDATE: FIX FONT BOLD & COLOR LOGIC - SQL SERVER SUPPORT
import pandas as pd
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QDate, QRectF
from PyQt6.QtGui import (
    QColor, QBrush, QPen, QPainter, QFont,
    QStandardItemModel, QStandardItem
)
from kDb import DatabaseConnection

# --- STYLE & COLORS ---
BTN_STYLE_VIEW = """
    QPushButton { background-color: #E3F2FD; color: #1565C0; border: 1px solid #BBDEFB; border-radius: 4px; padding: 4px 10px; font-weight: 600; }
    QPushButton:hover { background-color: #BBDEFB; }
"""
BTN_STYLE_EXP  = """
    QPushButton { background-color: #FFF3E0; color: #EF6C00; border: 1px solid #FFE0B2; border-radius: 4px; padding: 4px 10px; font-weight: 600; }
    QPushButton:hover { background-color: #FFE0B2; }
"""

PASTEL_COLORS = [
    "#FFB7B2", "#FFDAC1", "#E2F0CB", "#B5EAD7", "#C7CEEA", 
    "#F8BBD0", "#E1BEE7", "#D1C4E9", "#C5CAE9", "#BBDEFB", 
    "#B3E5FC", "#B2EBF2", "#B2DFDB", "#C8E6C9", "#DCEDC8", 
    "#F0F4C3", "#FFF9C4", "#FFECB3", "#FFE0B2", "#FFCCBC"
]

# --- ITEM THANH GANTT ---
class GanttBar(QGraphicsRectItem):
    def __init__(self, rect, full_info_str, color_hex, click_callback):
        super().__init__(rect)
        self.full_info_str = full_info_str
        self.click_callback = click_callback
        
        # Tooltip
        self.setToolTip(full_info_str) 
        
        self.setBrush(QBrush(QColor(color_hex)))
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setAcceptHoverEvents(True)
        
    def hoverEnterEvent(self, event):
        c = self.brush().color()
        self.setBrush(QBrush(c.lighter(110)))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        c = self.brush().color()
        self.setBrush(QBrush(c.darker(110)))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if self.click_callback:
            self.click_callback(self.full_info_str)
        super().mousePressEvent(event)

class ReportTab(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        db_conn = DatabaseConnection()
        self.conn = db_conn.connect()
        self.color_map = {}
        self.equip_map = {}
        
        layout = QVBoxLayout(self); layout.setContentsMargins(10, 10, 10, 10)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.init_ui_report_1(), "Báo Cáo Chi Tiết")
        self.tabs.addTab(self.init_ui_report_2(), "Theo Dõi Thiết Bị")
        layout.addWidget(self.tabs)

    # ... BÁO CÁO 1 (TABLE) ...
    def init_ui_report_1(self):
        w = QWidget(); l = QVBoxLayout(w)
        gb = QGroupBox("Bộ lọc dữ liệu"); gb.setStyleSheet("QGroupBox { font-weight: bold; background: #FAFAFA; border: 1px solid #ddd; border-radius: 5px; margin-top: 10px; }")
        gl = QGridLayout(gb); gl.setSpacing(10)
        gl.addWidget(QLabel("Từ ngày:"), 0, 0)
        self.r1_d1 = QDateEdit(); self.r1_d1.setCalendarPopup(True); self.r1_d1.setDate(QDate.currentDate().addMonths(-1)); self.r1_d1.setDisplayFormat("yyyy-MM-dd"); gl.addWidget(self.r1_d1, 0, 1)
        gl.addWidget(QLabel("Đến ngày:"), 0, 2)
        self.r1_d2 = QDateEdit(); self.r1_d2.setCalendarPopup(True); self.r1_d2.setDate(QDate.currentDate()); self.r1_d2.setDisplayFormat("yyyy-MM-dd"); gl.addWidget(self.r1_d2, 0, 3)
        gl.addWidget(QLabel("Người YC:"), 1, 0)
        self.r1_req = QComboBox(); self.r1_req.setEditable(True); self.r1_req.addItem("Tất cả"); self.load_requesters(); gl.addWidget(self.r1_req, 1, 1)
        self.r1_all_time = QCheckBox("Lấy tất cả thời gian"); gl.addWidget(self.r1_all_time, 1, 2, 1, 2)
        btn_view = QPushButton("Xem"); btn_view.setFixedWidth(80); btn_view.setStyleSheet(BTN_STYLE_VIEW); btn_view.clicked.connect(self.load_report_1)
        btn_exp  = QPushButton("Xuất CSV"); btn_exp.setFixedWidth(80); btn_exp.setStyleSheet(BTN_STYLE_EXP); btn_exp.clicked.connect(lambda: self.export_csv(self.r1_table, "BaoCao_KetQua"))
        h_btn = QHBoxLayout(); h_btn.addStretch(); h_btn.addWidget(btn_view); h_btn.addWidget(btn_exp)
        l.addWidget(gb); l.addLayout(h_btn)
        self.r1_table = QTableView(); self.r1_table.setAlternatingRowColors(True); self.r1_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        l.addWidget(self.r1_table)
        return w

    # ... BÁO CÁO 2 (GANTT CHART) ...
    def init_ui_report_2(self):
        w = QWidget(); l = QVBoxLayout(w)

        # Toolbar
        frame = QFrame(); frame.setStyleSheet("QFrame { background: #FAFAFA; border: 1px solid #ddd; border-radius: 6px; }")
        fl = QHBoxLayout(frame); fl.setContentsMargins(15, 10, 15, 10); fl.setSpacing(15)
        
        fl.addWidget(QLabel("<b>Thời gian:</b>"))
        self.r2_d1 = QDateEdit(); self.r2_d1.setCalendarPopup(True); self.r2_d1.setDate(QDate.currentDate().addDays(-7)); self.r2_d1.setDisplayFormat("yyyy-MM-dd"); self.r2_d1.setFixedWidth(100)
        fl.addWidget(self.r2_d1)
        fl.addWidget(QLabel("-"))
        self.r2_d2 = QDateEdit(); self.r2_d2.setCalendarPopup(True); self.r2_d2.setDate(QDate.currentDate().addDays(7)); self.r2_d2.setDisplayFormat("yyyy-MM-dd"); self.r2_d2.setFixedWidth(100)
        fl.addWidget(self.r2_d2)
        fl.addWidget(QLabel("|")) 
        
        fl.addWidget(QLabel("<b>Thiết bị:</b>"))
        self.r2_equip = QComboBox(); self.r2_equip.setEditable(True); self.r2_equip.addItem("Tất cả Thiết Bị"); self.r2_equip.setFixedWidth(120)
        self.r2_equip.currentTextChanged.connect(self.update_equip_name_label)
        fl.addWidget(self.r2_equip)

        self.r2_name_display = QLineEdit(); self.r2_name_display.setReadOnly(True); self.r2_name_display.setPlaceholderText("Tên thiết bị...")
        self.r2_name_display.setStyleSheet("background: #F5F5F5; color: #333; border: 1px solid #DDD;")
        fl.addWidget(self.r2_name_display, 1)

        self.load_equipments()
        
        btn_view = QPushButton("Xem"); btn_view.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_view.setFixedWidth(80); btn_view.setStyleSheet(BTN_STYLE_VIEW)
        btn_view.clicked.connect(self.draw_gantt)
        fl.addWidget(btn_view)
        
        l.addWidget(frame)

        # Màn hình vẽ
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.view.setStyleSheet("background: white; border: 1px solid #ccc; border-radius: 4px;")
        l.addWidget(self.view)

        # Label hiển thị thông tin
        self.lbl_click_info = QLabel("<i>(Rê chuột hoặc Click vào thanh test để xem chi tiết...)</i>")
        self.lbl_click_info.setStyleSheet("font-size: 13px; color: #1565C0; padding: 5px; font-weight: bold; background: #E3F2FD; border: 1px solid #BBDEFB; border-radius: 4px;")
        self.lbl_click_info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        l.addWidget(self.lbl_click_info)
        
        return w

    # ... Helper Functions ...
    def load_requesters(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT requester FROM requests WHERE requester IS NOT NULL AND requester != '' ORDER BY requester")
            res = cursor.fetchall()
            self.r1_req.addItems([r[0] for r in res])
        except: pass

    def load_equipments(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT control_no, name FROM equipment ORDER BY control_no")
            res = cursor.fetchall()
            self.equip_map = {r[0]: r[1] for r in res}
            self.r2_equip.addItems([r[0] for r in res])
        except: pass

    def update_equip_name_label(self, text):
        if text in self.equip_map: self.r2_name_display.setText(self.equip_map[text])
        elif text == "Tất cả Thiết Bị": self.r2_name_display.setText("--- Tất cả ---")
        else: self.r2_name_display.clear()

    def get_color(self, test_type):
        if test_type not in self.color_map:
            self.color_map[test_type] = PASTEL_COLORS[len(self.color_map) % len(PASTEL_COLORS)]
        return self.color_map[test_type]

    def on_bar_click(self, text):
        self.lbl_click_info.setText(text)

    # --- DRAW GANTT ---
    def draw_gantt(self):
        self.scene.clear()
        self.lbl_click_info.setText("<i>(Click vào thanh test để xem chi tiết...)</i>")
        
        eq_filter = self.r2_equip.currentText()
        d1_str = self.r2_d1.date().toString("yyyy-MM-dd"); d2_str = self.r2_d2.date().toString("yyyy-MM-dd")
        
        # SQL
        sql = """
            SELECT equip_no, request_no, detail, project, phase, category, requester, qty, 
                   plan_start, plan_end, actual_start, status, factory
            FROM requests WHERE equip_no IS NOT NULL AND equip_no != ''
            AND ( (plan_start BETWEEN ? AND ?) OR (actual_start BETWEEN ? AND ?) )
        """
        params = [d1_str, d2_str, d1_str, d2_str]
        if eq_filter != "Tất cả Thiết Bị": sql += " AND equip_no = ? "; params.append(eq_filter)
        sql += " ORDER BY equip_no, plan_start"

        try:
            df = pd.read_sql_query(sql, self.conn, params=tuple(params))
        except Exception as e: return QMessageBox.critical(self, "Lỗi", str(e))

        if df.empty:
            self.scene.addText("Không có dữ liệu trong khoảng thời gian này.", QFont("Arial", 11))
            return

        df['start_dt'] = pd.to_datetime(df['plan_start'], errors='coerce')
        df['end_dt'] = pd.to_datetime(df['plan_end'], errors='coerce')
        df = df.dropna(subset=['start_dt'])
        if df.empty: return

        view_start = pd.Timestamp(d1_str); view_end = pd.Timestamp(d2_str)
        
        BAR_H = 20; BAR_GAP = 5; ROW_PAD = 15; DAY_W = 20; START_X = 200; HEADER_H = 30
        
        equip_list = sorted(df['equip_no'].unique())
        total_days = (view_end - view_start).days + 1
        scene_width = START_X + total_days * DAY_W + 50
        
        pen_today = QPen(QColor("#FF5252")); pen_today.setWidth(2) 
        today_ts = pd.Timestamp(QDate.currentDate().toString("yyyy-MM-dd"))
        
        current_y = HEADER_H

        for d in range(total_days):
            curr_date = view_start + pd.Timedelta(days=d)
            x = START_X + d * DAY_W
            if d % 2 == 0 or total_days < 15: 
                txt = self.scene.addText(curr_date.strftime("%d/%m"))
                txt.setDefaultTextColor(QColor("red") if curr_date == today_ts else QColor("gray"))
                txt.setPos(x - 5, 0)
        
        for eq_code in equip_list:
            sub_df = df[df['equip_no'] == eq_code].sort_values('start_dt')
            lanes = []; test_placements = [] 
            
            for _, row in sub_df.iterrows():
                real_s = row['start_dt']; real_e = row['end_dt'] if pd.notna(row['end_dt']) else real_s
                chosen_lane = -1
                for i, lane_end in enumerate(lanes):
                    if real_s >= lane_end: 
                        chosen_lane = i; lanes[i] = real_e; break
                if chosen_lane == -1:
                    lanes.append(real_e); chosen_lane = len(lanes) - 1
                test_placements.append((row, chosen_lane))

            num_lanes = len(lanes)
            row_height = num_lanes * (BAR_H + BAR_GAP) + ROW_PAD
            
            eq_name = self.equip_map.get(eq_code, eq_code)
            lbl_name = self.scene.addText(eq_name[:25] + ("..." if len(eq_name)>25 else ""))
            lbl_name.setDefaultTextColor(QColor("#1565C0")); lbl_name.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            lbl_name.setPos(5, current_y + (row_height/2) - 15)
            
            lbl_code = self.scene.addText(f"({eq_code})")
            lbl_code.setDefaultTextColor(QColor("#777")); lbl_code.setFont(QFont("Arial", 8))
            lbl_code.setPos(5, current_y + (row_height/2))

            self.scene.addLine(0, current_y, scene_width, current_y, QPen(QColor("#F5F5F5"))) 
            
            for row, lane in test_placements:
                draw_start = max(row['start_dt'], view_start)
                real_end = row['end_dt'] if pd.notna(row['end_dt']) else row['start_dt']
                draw_end = min(real_end, view_end)

                if draw_end < draw_start: continue 

                days_w = (draw_end - draw_start).days + 1
                days_x = (draw_start - view_start).days
                
                x_bar = START_X + days_x * DAY_W
                w_bar = days_w * DAY_W
                y_bar = current_y + 10 + (lane * (BAR_H + BAR_GAP))
                
                info_parts = [
                    str(row.get('factory', '')), str(row.get('project', '')), str(row.get('phase', '')),
                    str(row.get('category', '')), str(row.get('detail', '')), str(row.get('qty', '')),
                    str(row.get('request_no', '')), str(row.get('requester', ''))
                ]
                full_info = "_".join([s for s in info_parts if s != 'None' and s != ''])
                
                cat_str = str(row.get('category', '')); det_str = str(row.get('detail', ''))
                bar_label = f"{cat_str}_{det_str}"

                color = self.get_color(row['detail'])
                rect = QRectF(x_bar, y_bar, w_bar, BAR_H)
                
                bar_item = GanttBar(rect, full_info, color, self.on_bar_click)
                self.scene.addItem(bar_item)
                
                if w_bar > 20:
                    display_txt = bar_label[:int(w_bar/5)]
                    t_item = self.scene.addText(display_txt)
                    t_item.setFont(QFont("Arial", 8))
                    t_item.setPos(x_bar, y_bar - 2)

            current_y += row_height
            self.scene.addLine(0, current_y, scene_width, current_y, QPen(QColor("#E0E0E0")))

        for d in range(total_days):
            curr_date = view_start + pd.Timedelta(days=d)
            if curr_date == today_ts:
                x = START_X + d * DAY_W
                self.scene.addLine(x, HEADER_H, x, current_y, pen_today)

        self.scene.setSceneRect(0, 0, scene_width, current_y + 50)

    # ... Shared Functions ...
    def load_report_1(self):
        req = self.r1_req.currentText(); d1 = self.r1_d1.date().toString("yyyy-MM-dd"); d2 = self.r1_d2.date().toString("yyyy-MM-dd")
        sql = """
            SELECT request_no, factory, project, phase, category, qty, requester, detail, 
                   cos_res, func_res, xhatch_res, xsection_res, final_res 
            FROM requests WHERE 1=1 
        """
        params = []
        if not self.r1_all_time.isChecked(): sql += " AND request_date BETWEEN ? AND ? "; params.extend([d1, d2])
        if req != "Tất cả": sql += " AND requester = ? "; params.append(req)
        sql += " ORDER BY request_date DESC"
        
        headers = ["Mã YC", "Nhà máy", "Dự án", "Giai đoạn", "Hạng mục", "SL", "Người YC", "Loại Test", "KQ N.Quan", "KQ T.Năng", "KQ X-Hatch", "KQ X-Section", "KQ Cuối"]
        self.fill_table(self.r1_table, sql, params, headers)

    def fill_table(self, table_view, sql, params, headers):
        try:
            df = pd.read_sql_query(sql, self.conn, params=tuple(params))
            model = QStandardItemModel(); model.setHorizontalHeaderLabels(headers)
            
            # Index của cột KQ Cuối
            col_final_idx = -1
            if "KQ Cuối" in headers:
                col_final_idx = headers.index("KQ Cuối")

            for _, row in df.iterrows():
                items = []
                for i, x in enumerate(row):
                    val = str(x) if x is not None else ""
                    item = QStandardItem(val)
                    
                    # --- XỬ LÝ MÀU SẮC CHO CỘT KQ CUỐI ---
                    if i == col_final_idx:
                        # Dùng setBold thay vì QFont.Weight.Bold để tương thích tốt hơn
                        f = QFont("Arial", 9); f.setBold(True); item.setFont(f)
                        
                        v_lower = val.lower().strip()
                        if v_lower == "pass":
                            item.setForeground(QBrush(QColor("#1976D2"))) # Xanh dương
                        elif v_lower == "fail":
                            item.setForeground(QBrush(QColor("#D32F2F"))) # Đỏ
                        elif v_lower == "waiver":
                            item.setForeground(QBrush(QColor("#F57F17"))) # Vàng cam
                    # -------------------------------------
                    
                    items.append(item)
                model.appendRow(items)

            table_view.setModel(model); table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            if not df.empty: QMessageBox.information(self, "OK", f"Đã tải {len(df)} dòng.")
            else: QMessageBox.information(self, "Info", "Không có dữ liệu!")     
        except Exception as e: QMessageBox.critical(self, "Lỗi Query", str(e))

    def export_csv(self, table_view, filename_prefix):
        model = table_view.model()
        if not model or model.rowCount() == 0: return QMessageBox.warning(self, "Lỗi", "Không có dữ liệu!")
        path, _ = QFileDialog.getSaveFileName(self, "Xuất CSV", f"{filename_prefix}.csv", "CSV Files (*.csv)")
        if path:
            data = [[model.item(r, c).text() for c in range(model.columnCount())] for r in range(model.rowCount())]
            pd.DataFrame(data, columns=[model.headerData(i, Qt.Orientation.Horizontal) for i in range(model.columnCount())]).to_csv(path, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, "OK", "Đã xuất file!")