"""
kRel - Report Tab
Report generation with table views and Gantt chart
"""
import pandas as pd

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QFrame,
    QTabWidget, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QDateEdit, QTableView, QFileDialog, QMessageBox, QAbstractItemView,
    QGraphicsScene, QGraphicsView
)
from PyQt6.QtCore import Qt, QDate, QRectF
from PyQt6.QtGui import (
    QStandardItemModel, QStandardItem, QPainter, QPen, QColor, QBrush, QFont
)

from src.config import PASTEL_COLORS
from src.services.database import get_db
from src.services.data_event_bus import get_event_bus
from src.services.logger import get_logger
from src.widgets.gantt_chart import GanttBar
from src.widgets.loading_overlay import LoadingMixin
from src.styles import (
    BTN_STYLE_BLUE, BTN_STYLE_ORANGE, TABLE_STYLE,
    GROUPBOX_STYLE, TOOLBAR_FRAME_STYLE, INFO_LABEL_STYLE, TAB_STYLE
)

# Module logger
logger = get_logger("report_tab")


class ReportTab(QWidget, LoadingMixin):
    """Report tab with detail reports and Gantt chart"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_db()
        self.color_map = {}
        self.equip_map = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)
        self.tabs.addTab(self._init_report_1(), "📊 Báo Cáo Chi Tiết")
        self.tabs.addTab(self._init_report_2(), "📅 Theo Dõi Thiết Bị")
        layout.addWidget(self.tabs)

        # Initialize loading overlay
        self.setup_loading()

        # Connect to DataEventBus
        self._connect_events()

    def _connect_events(self):
        """Connect to DataEventBus events for realtime updates"""
        event_bus = get_event_bus()

        # Listen for request changes - may want to refresh reports
        event_bus.request_created.connect(self._on_data_changed)
        event_bus.request_updated.connect(self._on_data_changed)
        event_bus.request_deleted.connect(self._on_data_changed)

        # Listen for equipment changes - refresh equipment combos
        event_bus.equipment_changed.connect(self._on_equipment_changed)

        logger.debug("ReportTab connected to DataEventBus")

    def _on_data_changed(self, request_no: str = None):
        """Handle data changes - can auto-refresh if needed"""
        # Note: For reports, we don't auto-refresh because user may be viewing
        # a specific report. They can click "Xem" to refresh manually.
        logger.debug(f"Data changed event received: {request_no}")

    def _on_equipment_changed(self):
        """Handle equipment data changes - reload equipment combos"""
        # Reload equipment combo in Report 2 (Gantt)
        if hasattr(self, 'cb_equip'):
            current = self.cb_equip.currentText()
            self._load_equipment_combo()
            idx = self.cb_equip.findText(current)
            if idx >= 0:
                self.cb_equip.setCurrentIndex(idx)
            logger.debug("Reloaded equipment combo in ReportTab")

    def _load_equipment_combo(self):
        """Load equipment combo box"""
        if not hasattr(self, 'cb_equip'):
            return
        self.cb_equip.clear()
        self.cb_equip.addItem("")
        try:
            rows = self.db.fetch_all("SELECT control_no FROM equipment ORDER BY control_no")
            for r in rows:
                self.cb_equip.addItem(r[0])
        except Exception:
            pass

    def _init_report_1(self):
        """Initialize detail report tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 12, 8, 8)

        # Toolbar Frame (like Theo dõi thiết bị)
        frame = QFrame()
        frame.setStyleSheet(TOOLBAR_FRAME_STYLE)

        fl = QHBoxLayout(frame)
        fl.setContentsMargins(12, 8, 12, 8)
        fl.setSpacing(12)

        # Date range
        time_lbl = QLabel("<b style='color: #1565C0;'>📅 Thời gian:</b>")
        fl.addWidget(time_lbl)

        self.r1_d1 = QDateEdit()
        self.r1_d1.setCalendarPopup(True)
        self.r1_d1.setDate(QDate.currentDate().addMonths(-1))
        self.r1_d1.setDisplayFormat("yyyy-MM-dd")
        self.r1_d1.setMinimumWidth(120)
        self.r1_d1.setStyleSheet(self._date_style())
        fl.addWidget(self.r1_d1)

        sep_lbl = QLabel("→")
        sep_lbl.setStyleSheet("color: #9E9E9E; font-size: 14px;")
        fl.addWidget(sep_lbl)

        self.r1_d2 = QDateEdit()
        self.r1_d2.setCalendarPopup(True)
        self.r1_d2.setDate(QDate.currentDate())
        self.r1_d2.setDisplayFormat("yyyy-MM-dd")
        self.r1_d2.setMinimumWidth(120)
        self.r1_d2.setStyleSheet(self._date_style())
        fl.addWidget(self.r1_d2)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet("background-color: #CFD8DC; max-width: 1px;")
        sep1.setFixedWidth(1)
        fl.addWidget(sep1)

        # Requester filter
        req_lbl = QLabel("<b style='color: #1565C0;'>👤 Người YC:</b>")
        fl.addWidget(req_lbl)

        self.r1_req = QComboBox()
        self.r1_req.setEditable(True)
        self.r1_req.addItem("Tất cả")
        self.r1_req.setMinimumWidth(140)
        self.r1_req.setStyleSheet(self._combo_style())
        self._load_requesters()
        fl.addWidget(self.r1_req)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("background-color: #CFD8DC; max-width: 1px;")
        sep2.setFixedWidth(1)
        fl.addWidget(sep2)

        # All time checkbox
        self.r1_all_time = QCheckBox("📅 Tất cả thời gian")
        self.r1_all_time.setStyleSheet("font-weight: 500; color: #424242;")
        fl.addWidget(self.r1_all_time)

        fl.addStretch()

        # Buttons
        btn_view = QPushButton("🔍 Xem")
        btn_view.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_view.setStyleSheet(BTN_STYLE_BLUE)
        btn_view.clicked.connect(self._load_report_1)
        fl.addWidget(btn_view)

        btn_exp = QPushButton("📤 Xuất CSV")
        btn_exp.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exp.setStyleSheet(BTN_STYLE_ORANGE)
        btn_exp.clicked.connect(lambda: self._export_csv(self.r1_table, "BaoCao_KetQua"))
        fl.addWidget(btn_exp)

        layout.addWidget(frame)

        # Table
        self.r1_table = QTableView()
        self.r1_table.setStyleSheet(TABLE_STYLE)
        self.r1_table.setAlternatingRowColors(True)
        self.r1_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.r1_table)

        return widget
    
    def _init_report_2(self):
        """Initialize Gantt chart report tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 12, 8, 8)

        # Toolbar
        frame = QFrame()
        frame.setStyleSheet(TOOLBAR_FRAME_STYLE)

        fl = QHBoxLayout(frame)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(12)

        # Date range
        time_lbl = QLabel("<b style='color: #1565C0;'>📅 Thời gian:</b>")
        fl.addWidget(time_lbl)

        self.r2_d1 = QDateEdit()
        self.r2_d1.setCalendarPopup(True)
        self.r2_d1.setDate(QDate.currentDate().addDays(-7))
        self.r2_d1.setDisplayFormat("yyyy-MM-dd")
        self.r2_d1.setMinimumWidth(130)
        self.r2_d1.setStyleSheet(self._date_style())
        fl.addWidget(self.r2_d1)

        sep_lbl = QLabel("→")
        sep_lbl.setStyleSheet("color: #9E9E9E; font-size: 16px;")
        fl.addWidget(sep_lbl)

        self.r2_d2 = QDateEdit()
        self.r2_d2.setCalendarPopup(True)
        self.r2_d2.setDate(QDate.currentDate().addDays(7))
        self.r2_d2.setDisplayFormat("yyyy-MM-dd")
        self.r2_d2.setMinimumWidth(130)
        self.r2_d2.setStyleSheet(self._date_style())
        fl.addWidget(self.r2_d2)

        # Separator
        sep_frame = QFrame()
        sep_frame.setFrameShape(QFrame.Shape.VLine)
        sep_frame.setStyleSheet("background-color: #CFD8DC; max-width: 1px;")
        sep_frame.setFixedWidth(1)
        fl.addWidget(sep_frame)

        # Equipment filter
        equip_lbl = QLabel("<b style='color: #1565C0;'>🔧 Thiết bị:</b>")
        fl.addWidget(equip_lbl)

        self.r2_equip = QComboBox()
        self.r2_equip.setEditable(True)
        self.r2_equip.addItem("Tất cả Thiết Bị")
        self.r2_equip.setMinimumWidth(160)
        self.r2_equip.setStyleSheet(self._combo_style())
        self.r2_equip.currentTextChanged.connect(self._update_equip_name)
        fl.addWidget(self.r2_equip)

        self.r2_name_display = QLineEdit()
        self.r2_name_display.setReadOnly(True)
        self.r2_name_display.setPlaceholderText("Tên thiết bị...")
        self.r2_name_display.setStyleSheet("""
            background: #ECEFF1;
            color: #607D8B;
            border: 1px solid #CFD8DC;
            border-radius: 6px;
            padding: 6px 10px;
            min-height: 32px;
        """)
        fl.addWidget(self.r2_name_display, 1)

        self._load_equipments()

        btn_view = QPushButton("  🔍 Xem")
        btn_view.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_view.setMinimumWidth(110)
        btn_view.setStyleSheet(BTN_STYLE_BLUE)
        btn_view.clicked.connect(self._draw_gantt)
        fl.addWidget(btn_view)

        layout.addWidget(frame)

        # Gantt view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.view.setStyleSheet("""
            background: white;
            border: 1px solid #E0E0E0;
            border-radius: 8px;
        """)
        layout.addWidget(self.view)

        # Info label
        self.lbl_click_info = QLabel(
            "<i>💡 Rê chuột hoặc Click vào thanh test để xem chi tiết...</i>"
        )
        self.lbl_click_info.setStyleSheet(INFO_LABEL_STYLE)
        self.lbl_click_info.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self.lbl_click_info)

        return widget

    # Helper methods
    def _date_style(self):
        return """
            QDateEdit {
                border: 1px solid #CFD8DC;
                border-radius: 6px;
                padding: 6px 12px;
                background-color: #FFFFFF;
                min-height: 32px;
                font-size: 13px;
            }
            QDateEdit:hover {
                border-color: #90CAF9;
                background-color: #FAFEFF;
            }
            QDateEdit:focus { border: 2px solid #1565C0; }
        """

    def _combo_style(self):
        return """
            QComboBox {
                border: 1px solid #CFD8DC;
                border-radius: 6px;
                padding: 6px 12px;
                background-color: #FFFFFF;
                min-height: 32px;
                font-size: 13px;
            }
            QComboBox:hover {
                border-color: #90CAF9;
                background-color: #FAFEFF;
            }
            QComboBox:focus { border: 2px solid #1565C0; }
        """

    def _btn_style_view(self):
        return BTN_STYLE_BLUE

    def _btn_style_export(self):
        return BTN_STYLE_ORANGE

    def _load_requesters(self):
        """Load requester list"""
        try:
            rows = self.db.fetch_all("""
                SELECT DISTINCT requester FROM requests
                WHERE requester IS NOT NULL AND requester != ''
                ORDER BY requester
            """)
            for row in rows:
                self.r1_req.addItem(row[0])
        except Exception:
            pass
    
    def _load_equipments(self):
        """Load equipment list"""
        try:
            rows = self.db.fetch_all(
                "SELECT control_no, name FROM equipment ORDER BY control_no"
            )
            self.equip_map = {r[0]: r[1] for r in rows}
            for row in rows:
                self.r2_equip.addItem(row[0])
        except Exception:
            pass
    
    def _update_equip_name(self, text):
        """Update equipment name display"""
        if text in self.equip_map:
            self.r2_name_display.setText(self.equip_map[text])
        elif text == "Tất cả Thiết Bị":
            self.r2_name_display.setText("--- Tất cả ---")
        else:
            self.r2_name_display.clear()
    
    def _get_color(self, test_type):
        """Get consistent color for test type"""
        if test_type not in self.color_map:
            self.color_map[test_type] = PASTEL_COLORS[
                len(self.color_map) % len(PASTEL_COLORS)
            ]
        return self.color_map[test_type]
    
    def _on_bar_click(self, text):
        """Handle Gantt bar click"""
        self.lbl_click_info.setText(text)

    def _load_report_1(self):
        """Load detail report data"""
        self.show_loading("Đang tải báo cáo...")
        try:
            self._do_load_report_1()
        finally:
            self.hide_loading()

    def _do_load_report_1(self):
        """Internal report loading logic"""
        req = self.r1_req.currentText()
        d1 = self.r1_d1.date().toString("yyyy-MM-dd")
        d2 = self.r1_d2.date().toString("yyyy-MM-dd")

        sql = """
            SELECT request_no, factory, project, phase, category, qty,
                   requester, cos_res, func_res, xhatch_res,
                   xsection_res, final_res
            FROM requests WHERE 1=1
        """
        params = []

        if not self.r1_all_time.isChecked():
            sql += " AND request_date BETWEEN ? AND ? "
            params.extend([d1, d2])

        if req != "Tất cả":
            sql += " AND requester = ? "
            params.append(req)

        sql += " ORDER BY request_date DESC"

        headers = [
            "Mã YC", "Nhà máy", "Dự án", "Giai đoạn", "Hạng mục", "SL",
            "Người YC", "KQ N.Quan", "KQ T.Năng",
            "KQ X-Hatch", "KQ X-Section", "KQ Cuối"
        ]

        self._fill_table(self.r1_table, sql, params, headers)

    def _fill_table(self, table_view, sql, params, headers):
        """Fill table with query results"""
        try:
            conn = self.db.connect()
            df = pd.read_sql_query(sql, conn, params=tuple(params))

            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(headers)

            # Find final result column index
            col_final_idx = headers.index("KQ Cuối") if "KQ Cuối" in headers else -1

            for _, row in df.iterrows():
                items = []
                for i, x in enumerate(row):
                    val = str(x) if x is not None else ""
                    item = QStandardItem(val)

                    # Color for final result column
                    if i == col_final_idx:
                        font = QFont("Arial", 9)
                        font.setBold(True)
                        item.setFont(font)

                        v_lower = val.lower().strip()
                        if v_lower == "pass":
                            item.setForeground(QBrush(QColor("#1976D2")))
                        elif v_lower == "fail":
                            item.setForeground(QBrush(QColor("#D32F2F")))
                        elif v_lower == "waiver":
                            item.setForeground(QBrush(QColor("#F57F17")))

                    items.append(item)
                model.appendRow(items)

            table_view.setModel(model)

            from PyQt6.QtWidgets import QHeaderView
            table_view.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.ResizeToContents
            )

            if not df.empty:
                QMessageBox.information(self, "OK", f"Đã tải {len(df)} dòng.")
            else:
                QMessageBox.information(self, "Info", "Không có dữ liệu!")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi Query", str(e))

    def _export_csv(self, table_view, filename_prefix):
        """Export table to CSV"""
        model = table_view.model()
        if not model or model.rowCount() == 0:
            return QMessageBox.warning(self, "Lỗi", "Không có dữ liệu!")

        path, _ = QFileDialog.getSaveFileName(
            self, "Xuất CSV", f"{filename_prefix}.csv", "CSV Files (*.csv)"
        )

        if path:
            data = [
                [model.item(r, c).text() for c in range(model.columnCount())]
                for r in range(model.rowCount())
            ]
            headers = [
                model.headerData(i, Qt.Orientation.Horizontal)
                for i in range(model.columnCount())
            ]
            pd.DataFrame(data, columns=headers).to_csv(
                path, index=False, encoding='utf-8-sig'
            )
            QMessageBox.information(self, "OK", "Đã xuất file!")

    def _draw_gantt(self):
        """Draw Gantt chart"""
        self.show_loading("Đang vẽ Gantt chart...")
        try:
            self._do_draw_gantt()
        finally:
            self.hide_loading()

    def _do_draw_gantt(self):
        """Internal Gantt drawing logic"""
        self.scene.clear()
        self.lbl_click_info.setText("<i>(Click vào thanh test để xem chi tiết...)</i>")

        eq_filter = self.r2_equip.currentText()
        d1_str = self.r2_d1.date().toString("yyyy-MM-dd")
        d2_str = self.r2_d2.date().toString("yyyy-MM-dd")

        # Query
        sql = """
            SELECT equip_no, request_no, project, phase, category,
                   requester, qty, plan_start, plan_end, actual_start, status, factory
            FROM requests
            WHERE equip_no IS NOT NULL AND equip_no != ''
            AND ((plan_start BETWEEN ? AND ?) OR (actual_start BETWEEN ? AND ?))
        """
        params = [d1_str, d2_str, d1_str, d2_str]

        if eq_filter != "Tất cả Thiết Bị":
            sql += " AND equip_no = ? "
            params.append(eq_filter)

        sql += " ORDER BY equip_no, plan_start"

        try:
            conn = self.db.connect()
            df = pd.read_sql_query(sql, conn, params=tuple(params))
        except Exception as e:
            return QMessageBox.critical(self, "Lỗi", str(e))

        if df.empty:
            self.scene.addText(
                "Không có dữ liệu trong khoảng thời gian này.",
                QFont("Arial", 11)
            )
            return

        # Process dates
        df['start_dt'] = pd.to_datetime(df['plan_start'], errors='coerce')
        df['end_dt'] = pd.to_datetime(df['plan_end'], errors='coerce')
        df = df.dropna(subset=['start_dt'])

        if df.empty:
            return

        view_start = pd.Timestamp(d1_str)
        view_end = pd.Timestamp(d2_str)

        # Constants
        BAR_H = 20
        BAR_GAP = 5
        ROW_PAD = 15
        DAY_W = 20
        START_X = 200
        HEADER_H = 30

        equip_list = sorted(df['equip_no'].unique())
        total_days = (view_end - view_start).days + 1
        scene_width = START_X + total_days * DAY_W + 50

        pen_today = QPen(QColor("#FF5252"))
        pen_today.setWidth(2)
        today_ts = pd.Timestamp(QDate.currentDate().toString("yyyy-MM-dd"))

        current_y = HEADER_H

        # Draw date headers
        for d in range(total_days):
            curr_date = view_start + pd.Timedelta(days=d)
            x = START_X + d * DAY_W
            if d % 2 == 0 or total_days < 15:
                txt = self.scene.addText(curr_date.strftime("%d/%m"))
                txt.setDefaultTextColor(
                    QColor("red") if curr_date == today_ts else QColor("gray")
                )
                txt.setPos(x - 5, 0)

        # Draw equipment rows
        for eq_code in equip_list:
            sub_df = df[df['equip_no'] == eq_code].sort_values('start_dt')
            lanes = []
            test_placements = []

            # Calculate lanes (handle overlapping)
            for _, row in sub_df.iterrows():
                real_s = row['start_dt']
                real_e = row['end_dt'] if pd.notna(row['end_dt']) else real_s

                chosen_lane = -1
                for i, lane_end in enumerate(lanes):
                    if real_s >= lane_end:
                        chosen_lane = i
                        lanes[i] = real_e
                        break

                if chosen_lane == -1:
                    lanes.append(real_e)
                    chosen_lane = len(lanes) - 1

                test_placements.append((row, chosen_lane))

            num_lanes = len(lanes)
            row_height = num_lanes * (BAR_H + BAR_GAP) + ROW_PAD

            # Draw equipment label
            eq_name = self.equip_map.get(eq_code, eq_code)
            lbl_name = self.scene.addText(
                eq_name[:25] + ("..." if len(eq_name) > 25 else "")
            )
            lbl_name.setDefaultTextColor(QColor("#1565C0"))
            lbl_name.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            lbl_name.setPos(5, current_y + (row_height / 2) - 15)

            lbl_code = self.scene.addText(f"({eq_code})")
            lbl_code.setDefaultTextColor(QColor("#777"))
            lbl_code.setFont(QFont("Arial", 8))
            lbl_code.setPos(5, current_y + (row_height / 2))

            self.scene.addLine(0, current_y, scene_width, current_y, QPen(QColor("#F5F5F5")))

            # Draw bars
            for row, lane in test_placements:
                draw_start = max(row['start_dt'], view_start)
                real_end = row['end_dt'] if pd.notna(row['end_dt']) else row['start_dt']
                draw_end = min(real_end, view_end)

                if draw_end < draw_start:
                    continue

                days_w = (draw_end - draw_start).days + 1
                days_x = (draw_start - view_start).days

                x_bar = START_X + days_x * DAY_W
                w_bar = days_w * DAY_W
                y_bar = current_y + 10 + (lane * (BAR_H + BAR_GAP))

                # Build info text
                info_parts = [
                    str(row.get('factory', '')),
                    str(row.get('project', '')),
                    str(row.get('phase', '')),
                    str(row.get('category', '')),
                    str(row.get('qty', '')),
                    str(row.get('request_no', '')),
                    str(row.get('requester', ''))
                ]
                full_info = "_".join([s for s in info_parts if s != 'None' and s != ''])

                cat_str = str(row.get('category', ''))
                bar_label = cat_str

                color = self._get_color(row.get('category', ''))
                rect = QRectF(x_bar, y_bar, w_bar, BAR_H)

                bar_item = GanttBar(rect, full_info, color, self._on_bar_click)
                self.scene.addItem(bar_item)

                if w_bar > 20:
                    display_txt = bar_label[:int(w_bar / 5)]
                    t_item = self.scene.addText(display_txt)
                    t_item.setFont(QFont("Arial", 8))
                    t_item.setPos(x_bar, y_bar - 2)

            current_y += row_height
            self.scene.addLine(0, current_y, scene_width, current_y, QPen(QColor("#E0E0E0")))

        # Draw today line
        for d in range(total_days):
            curr_date = view_start + pd.Timedelta(days=d)
            if curr_date == today_ts:
                x = START_X + d * DAY_W
                self.scene.addLine(x, HEADER_H, x, current_y, pen_today)

        self.scene.setSceneRect(0, 0, scene_width, current_y + 50)

