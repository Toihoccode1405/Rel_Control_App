# kEdit.py - FIX DATE EDITOR (CURRENT DATE) - SQL SERVER SUPPORT
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QAbstractItemModel, QDateTime, QSize
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor, QIcon, QAction
import pandas as pd, os, shutil
from configparser import ConfigParser
from kDb import DatabaseConnection

STATUS_COLORS = { "Done": "#E8F5E9", "Finish": "#E8F5E9", "Ongoing": "#E3F2FD", "Running": "#E3F2FD", "Pending": "#FFFDE7", "Wait": "#FFFDE7", "Stop": "#FFEBEE", "Fail": "#FFEBEE", "Cancel": "#F3E5F5", "Not Start": "#FAFAFA" }
DEFAULT_COLOR = "#FFFFFF"

class ComboDelegate(QStyledItemDelegate):
    def __init__(self, parent, data_source): super().__init__(parent); self.data_source = data_source
    def createEditor(self, parent, option, index):
        if index.column() in self.data_source: c = QComboBox(parent); c.setEditable(True); c.addItems(self.data_source[index.column()]); return c
        return super().createEditor(parent, option, index)
    def setEditorData(self, editor, index):
        if isinstance(editor, QComboBox):
            idx = editor.findText(index.model().data(index, Qt.ItemDataRole.EditRole)); 
            if idx >= 0: editor.setCurrentIndex(idx)
        else: super().setEditorData(editor, index)
    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox): model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
        else: super().setModelData(editor, model, index)

class RecipeDelegate(QStyledItemDelegate):
    def __init__(self, parent, db_path): super().__init__(parent); self.db_path = db_path
    def createEditor(self, parent, option, index):
        model = index.model(); equip_idx = model.index(index.row(), 19)
        equip_no = model.data(equip_idx, Qt.ItemDataRole.DisplayRole); combo = QComboBox(parent); combo.setEditable(True)
        if equip_no:
            try:
                db_conn = DatabaseConnection()
                conn = db_conn.connect()
                cursor = conn.cursor()
                cursor.execute("SELECT r1, r2, r3, r4, r5 FROM equipment WHERE control_no=?", (str(equip_no),))
                r = cursor.fetchone()
                if r: combo.addItems([str(x) for x in r if x and str(x).strip()])
                conn.close()
            except: pass
        return combo
    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox): model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)

class DateDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        dt = QDateTimeEdit(parent); dt.setCalendarPopup(True); dt.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        # dt.setMinimumDateTime(QDateTime(2000, 1, 1, 0, 0)); # Bỏ min date 2000 để lịch nhảy đúng năm nay
        # dt.setSpecialValueText("---"); 
        return dt
    def setEditorData(self, editor, index):
        val = index.model().data(index, Qt.ItemDataRole.EditRole)
        if val and isinstance(val, str) and val.strip():
            q = QDateTime.fromString(val, "yyyy-MM-dd HH:mm:ss")
            if q.isValid(): editor.setDateTime(q)
            else: editor.setDateTime(QDateTime.currentDateTime()) # Nếu lỗi format -> lấy hiện tại
        else: 
            # --- QUAN TRỌNG: NẾU TRỐNG -> LẤY NGÀY HIỆN TẠI ---
            editor.setDateTime(QDateTime.currentDateTime()) 
            
    def setModelData(self, editor, model, index):
        # Lưu thẳng giá trị đang chọn
        model.setData(index, editor.dateTime().toString("yyyy-MM-dd HH:mm:ss"), Qt.ItemDataRole.EditRole)

class FrozenTableView(QTableView):
    def __init__(self, model, frozen_col_count=4):
        super().__init__(); self.setModel(model); self.frozen_col_count = frozen_col_count
        self.frozen = QTableView(self); self.frozen.setModel(model); self.frozen.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.frozen.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed); self.frozen.setStyleSheet("QTableView { border: none; background-color: #f9f9f9; selection-background-color: #90caf9; border-right: 2px solid #ccc; }")
        self.verticalHeader().setFixedWidth(40); self.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter); self.frozen.verticalHeader().hide()
        self.viewport().stackUnder(self.frozen); self.frozen.setSelectionModel(self.selectionModel())
        for col in range(model.columnCount()):
            if col < frozen_col_count: self.setColumnHidden(col, True)
            else: self.frozen.setColumnHidden(col, True)
        self.verticalScrollBar().valueChanged.connect(self.frozen.verticalScrollBar().setValue); self.frozen.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)
        self.updateFrozenTableGeometry()
    def updateFrozenTableGeometry(self):
        w = sum([self.columnWidth(i) for i in range(self.frozen_col_count) if not self.frozen.isColumnHidden(i)])
        self.frozen.setGeometry(self.verticalHeader().width() + self.frameWidth(), self.frameWidth(), w, self.viewport().height() + self.horizontalHeader().height())
    def resizeEvent(self, event): super().resizeEvent(event); self.updateFrozenTableGeometry()

class NoEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index): return None

class EditTab(QWidget):
    COL_MAP = {4: "factory", 5: "project", 6: "phase", 7: "category", 19: "equipment", 24: "status"} 
    DATE_COLS = [2, 22, 23, 26, 27] 
    HEADERS = [
        "ID","Mã YC","Ngày YC","Người YC","Nhà máy","Dự án","Giai đoạn","Hạng mục","Loại Test","SL",
        "Ngoại quan","KQ Ngoại Quan","Cross hatch","KQ X-Hatch","Cross section","KQ X-Section",
        "Tính năng","KQ Tính Năng","KQ Cuối","Mã TB","Tên TB","Điều kiện",
        "Vào KH","Ra KH","Trạng thái","DRI","Vào TT","Ra TT","Logfile","Link","Ghi chú"
    ]

    def __init__(self, db_path):
        super().__init__(); self.db_path = db_path
        db_conn = DatabaseConnection()
        self.conn = db_conn.connect()
        self.log_path = "Logfile"
        if os.path.exists("config.ini"):
            cfg = ConfigParser(); cfg.read("config.ini", encoding="utf-8")
            if cfg.has_section("system"): self.log_path = cfg["system"].get("log_path", "Logfile")
        
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(10, 10, 10, 10); main_layout.setSpacing(10)
        toolbar_frame = QFrame(); toolbar_frame.setStyleSheet("QFrame { background-color: #ffffff; border: 1px solid #ddd; border-radius: 6px; }")
        tl = QHBoxLayout(toolbar_frame); tl.setContentsMargins(10, 8, 10, 8)
        
        btn_re = QPushButton("  Làm mới"); btn_re.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)); btn_re.setCursor(Qt.CursorShape.PointingHandCursor); btn_re.clicked.connect(self.refresh_data)
        
        self.cb_filter_stt = QComboBox(); self.cb_filter_stt.addItem("Tất cả Trạng thái"); self.cb_filter_stt.setFixedWidth(130); self.cb_filter_stt.currentTextChanged.connect(self.load)
        self.cb_filter_res = QComboBox(); self.cb_filter_res.addItems(["Tất cả KQ", "-", "Pass", "Fail", "Waiver"]); self.cb_filter_res.setFixedWidth(100); self.cb_filter_res.currentTextChanged.connect(self.load)

        btn_sv = QPushButton("  Lưu thay đổi"); btn_sv.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)); btn_sv.setCursor(Qt.CursorShape.PointingHandCursor); btn_sv.clicked.connect(self.save)
        btn_exp = QPushButton("  Xuất CSV"); btn_exp.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DriveFDIcon)); btn_exp.setCursor(Qt.CursorShape.PointingHandCursor); btn_exp.clicked.connect(self.export_csv)
        
        btn_re.setStyleSheet("background:#E3F2FD;color:#1976D2;border:1px solid #BBDEFB;padding:6px;font-weight:bold")
        btn_sv.setStyleSheet("background:#2E7D32;color:white;border:none;padding:6px;font-weight:bold")
        btn_exp.setStyleSheet("background:#FF9800;color:white;border:none;padding:6px;font-weight:bold")
        
        tl.addWidget(QLabel("<b>QUẢN LÝ DỮ LIỆU</b>")); tl.addSpacing(10); tl.addWidget(btn_re); tl.addSpacing(20)
        tl.addWidget(QLabel("Lọc:")); tl.addWidget(self.cb_filter_stt); tl.addWidget(self.cb_filter_res)
        tl.addStretch()
        tl.addWidget(btn_sv); tl.addWidget(btn_exp); main_layout.addWidget(toolbar_frame)
        
        self.table_container = QVBoxLayout(); main_layout.addLayout(self.table_container); self.table = None; self.init_filter_list(); self.load()

    def init_filter_list(self):
        try:
            curr_stt = self.cb_filter_stt.currentText(); self.cb_filter_stt.blockSignals(True); self.cb_filter_stt.clear(); self.cb_filter_stt.addItem("Tất cả Trạng thái")
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM status ORDER BY name")
            res = cursor.fetchall()
            self.cb_filter_stt.addItems([r[0] for r in res if r[0]])
            self.cb_filter_stt.setCurrentText(curr_stt); self.cb_filter_stt.blockSignals(False)
        except: pass
    
    def refresh_data(self): 
        self.cb_filter_res.setCurrentIndex(0); self.init_filter_list(); self.load()

    def load(self):
        data = {}
        cursor = self.conn.cursor()
        for c, t in self.COL_MAP.items():
            if t == "equipment":
                cursor.execute("SELECT control_no FROM equipment ORDER BY control_no")
                res = cursor.fetchall()
            else:
                cursor.execute(f"SELECT name FROM {t} ORDER BY name")
                res = cursor.fetchall()
            data[c] = [""] + [r[0] for r in res if r[0]]
        
        data[18] = ["-", "Pass", "Fail", "Waiver"]

        val_stt = self.cb_filter_stt.currentText(); val_res = self.cb_filter_res.currentText()
        conditions = []; params = []
        if val_stt and val_stt != "Tất cả Trạng thái": conditions.append("status=?"); params.append(val_stt)
        if val_res and val_res != "Tất cả KQ": conditions.append("final_res=?"); params.append(val_res)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"SELECT * FROM requests {where_clause} ORDER BY id DESC"
        
        df = pd.read_sql_query(query, self.conn, params=tuple(params))
        self.model = QStandardItemModel(); self.model.setHorizontalHeaderLabels(self.HEADERS)
        lemon_bg = QColor("#FFF9C4")
        for _, row in df.iterrows():
            stt_val = str(row.iloc[24]) if row.iloc[24] else "" 
            row_bg = QColor(STATUS_COLORS.get(stt_val, DEFAULT_COLOR)); items = []
            for v in row:
                val = str(v) if v is not None else ""; it = QStandardItem(val)
                if not val.strip(): it.setBackground(lemon_bg)
                else: it.setBackground(row_bg)
                items.append(it)
            self.model.appendRow(items)
        self.model.itemChanged.connect(self.on_change)
        
        if self.table: self.table_container.removeWidget(self.table); self.table.deleteLater()
        self.table = FrozenTableView(self.model, frozen_col_count=4)
        self.table.doubleClicked.connect(self.handle_table_double_click)
        
        self.table.setItemDelegate(ComboDelegate(self.table, data))
        self.table.frozen.setItemDelegate(ComboDelegate(self.table.frozen, data))
        
        self.table.setItemDelegateForColumn(2, DateDelegate(self.table)) 
        self.table.frozen.setItemDelegateForColumn(2, DateDelegate(self.table.frozen)) 
        
        dd_main = DateDelegate(self.table)
        for c in self.DATE_COLS: 
            if c >= 4: self.table.setItemDelegateForColumn(c, dd_main)

        self.table.setItemDelegateForColumn(21, RecipeDelegate(self.table, self.db_path)) 
        self.table.setItemDelegateForColumn(28, NoEditDelegate(self.table)) 

        h = self.table.horizontalHeader(); h.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for i in range(4): self.table.setColumnWidth(i, 120 if i>0 else 50); self.table.frozen.setColumnWidth(i, 120 if i>0 else 50)
        h.setSectionResizeMode(30, QHeaderView.ResizeMode.Stretch) 
        self.table_container.addWidget(self.table)

    def handle_table_double_click(self, index):
        if index.column() == 28: 
            row = index.row(); req_no = self.model.item(row, 1).text().strip()
            if not req_no: return QMessageBox.warning(self, "Lỗi", "Cần có Mã Yêu Cầu!")
            fname, _ = QFileDialog.getOpenFileName(self, "Chọn Logfile")
            if fname:
                try:
                    dest_dir = os.path.join(self.log_path, req_no); os.makedirs(dest_dir, exist_ok=True)
                    dest_path = os.path.join(dest_dir, os.path.basename(fname)); shutil.copy(fname, dest_path)
                    self.model.item(row, 28).setText(os.path.basename(fname)); self.model.item(row, 29).setText(dest_path)
                    QMessageBox.information(self, "OK", f"Đã tải: {os.path.basename(fname)}")
                except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))

    def on_change(self, item):
        if not item.text().strip(): item.setBackground(QColor("#FFF9C4"))
        else: item.setBackground(QColor("white"))
        if item.column() == 19:
            equip_no = item.text().strip()
            if equip_no:
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT name FROM equipment WHERE control_no=?", (equip_no,))
                    r = cursor.fetchone()
                    if r:
                        self.model.blockSignals(True); self.model.setItem(item.row(), 20, QStandardItem(r[0])); self.model.blockSignals(False)
                except: pass

    def save(self):
        d = [];
        for r in range(self.model.rowCount()): d.append([self.model.item(r, c).text() if self.model.item(r,c) else "" for c in range(self.model.columnCount())])
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM requests")
            cols = "id,request_no,request_date,requester,factory,project,phase,category,detail,qty,cos,cos_res,hcross,xhatch_res,xcross,xsection_res,func_test,func_res,final_res,equip_no,equip_name,test_condition,plan_start,plan_end,status,dri,actual_start,actual_end,logfile,log_link,note"
            cursor.executemany(f"INSERT INTO requests({cols}) VALUES({','.join(['?']*31)})", d)
            self.conn.commit()
            QMessageBox.information(self, "Thành công", "Đã lưu!"); self.load()
        except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))

    def export_csv(self):
        p, _ = QFileDialog.getSaveFileName(self, "Xuất", "kRel_Data.csv", "CSV (*.csv)")
        if p:
            try:
                val_stt = self.cb_filter_stt.currentText(); val_res = self.cb_filter_res.currentText()
                cond = []; pm = []
                if val_stt and val_stt != "Tất cả Trạng thái": cond.append("status=?"); pm.append(val_stt)
                if val_res and val_res != "Tất cả KQ": cond.append("final_res=?"); pm.append(val_res)
                wc = " WHERE " + " AND ".join(cond) if cond else ""
                q = f"SELECT * FROM requests {wc} ORDER BY id DESC"
                df = pd.read_sql_query(q, self.conn, params=tuple(pm))
                if len(df.columns) == len(self.HEADERS): df.columns = self.HEADERS
                df.to_csv(p, index=False, encoding='utf-8-sig'); QMessageBox.information(self, "OK", "Đã xuất!")
            except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))