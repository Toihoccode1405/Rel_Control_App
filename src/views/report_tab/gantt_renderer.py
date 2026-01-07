"""
kRel - Gantt Chart Renderer
Vẽ Gantt chart cho Report Tab 2
"""
import pandas as pd

from PyQt6.QtWidgets import QMessageBox, QGraphicsScene
from PyQt6.QtCore import Qt, QDate, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont

from src.config import PASTEL_COLORS
from src.services.database import get_db
from src.widgets.gantt_chart import GanttBar


class GanttRenderer:
    """Renderer for Gantt chart"""
    
    # Constants
    BAR_H = 20
    BAR_GAP = 5
    ROW_PAD = 15
    DAY_W = 20
    START_X = 200
    HEADER_H = 30
    
    def __init__(self, scene: QGraphicsScene, equip_map: dict, 
                 on_bar_click: callable):
        self.scene = scene
        self.equip_map = equip_map
        self.on_bar_click = on_bar_click
        self.color_map = {}
        self.db = get_db()
    
    def draw(self, equip_filter: str, date_start: str, date_end: str) -> bool:
        """
        Draw Gantt chart
        
        Returns:
            bool: True if data found, False if empty
        """
        self.scene.clear()
        
        df = self._load_data(equip_filter, date_start, date_end)
        if df is None or df.empty:
            self.scene.addText(
                "Không có dữ liệu trong khoảng thời gian này.",
                QFont("Arial", 11)
            )
            return False
        
        view_start = pd.Timestamp(date_start)
        view_end = pd.Timestamp(date_end)
        
        equip_list = sorted(df['equip_no'].unique())
        total_days = (view_end - view_start).days + 1
        scene_width = self.START_X + total_days * self.DAY_W + 50
        
        today_ts = pd.Timestamp(QDate.currentDate().toString("yyyy-MM-dd"))
        current_y = self.HEADER_H
        
        # Draw date headers
        self._draw_date_headers(view_start, total_days, today_ts)
        
        # Draw equipment rows
        for eq_code in equip_list:
            sub_df = df[df['equip_no'] == eq_code].sort_values('start_dt')
            row_height = self._draw_equipment_row(
                eq_code, sub_df, current_y, view_start, view_end, scene_width
            )
            current_y += row_height
        
        # Draw today line
        self._draw_today_line(view_start, total_days, today_ts, current_y)
        
        self.scene.setSceneRect(0, 0, scene_width, current_y + 50)
        return True
    
    def _load_data(self, equip_filter: str, d1: str, d2: str):
        """Load data from database"""
        sql = """
            SELECT equip_no, request_no, project, phase, category,
                   requester, qty, plan_start, plan_end, actual_start, status, factory
            FROM requests
            WHERE equip_no IS NOT NULL AND equip_no != ''
            AND ((plan_start BETWEEN ? AND ?) OR (actual_start BETWEEN ? AND ?))
        """
        params = [d1, d2, d1, d2]
        
        if equip_filter != "Tất cả Thiết Bị":
            sql += " AND equip_no = ? "
            params.append(equip_filter)
        
        sql += " ORDER BY equip_no, plan_start"
        
        try:
            conn = self.db.connect()
            df = pd.read_sql_query(sql, conn, params=tuple(params))
            
            df['start_dt'] = pd.to_datetime(df['plan_start'], errors='coerce')
            df['end_dt'] = pd.to_datetime(df['plan_end'], errors='coerce')
            df = df.dropna(subset=['start_dt'])
            
            return df
        except Exception:
            return None
    
    def _draw_date_headers(self, view_start, total_days, today_ts):
        """Draw date headers"""
        for d in range(total_days):
            curr_date = view_start + pd.Timedelta(days=d)
            x = self.START_X + d * self.DAY_W
            if d % 2 == 0 or total_days < 15:
                txt = self.scene.addText(curr_date.strftime("%d/%m"))
                txt.setDefaultTextColor(
                    QColor("red") if curr_date == today_ts else QColor("gray")
                )
                txt.setPos(x - 5, 0)
    
    def _draw_equipment_row(self, eq_code, sub_df, current_y, 
                             view_start, view_end, scene_width) -> float:
        """Draw single equipment row, return row height"""
        # Calculate lanes
        lanes = []
        test_placements = []
        
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
        
        num_lanes = max(len(lanes), 1)
        row_height = num_lanes * (self.BAR_H + self.BAR_GAP) + self.ROW_PAD
        
        # Draw equipment label
        eq_name = self.equip_map.get(eq_code, eq_code)
        lbl_name = self.scene.addText(eq_name[:25] + ("..." if len(eq_name) > 25 else ""))
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
            self._draw_bar(row, lane, current_y, view_start, view_end)
        
        self.scene.addLine(0, current_y + row_height, scene_width, 
                          current_y + row_height, QPen(QColor("#E0E0E0")))
        
        return row_height

    def _draw_bar(self, row, lane, current_y, view_start, view_end):
        """Draw single bar"""
        draw_start = max(row['start_dt'], view_start)
        real_end = row['end_dt'] if pd.notna(row['end_dt']) else row['start_dt']
        draw_end = min(real_end, view_end)

        if draw_end < draw_start:
            return

        days_w = (draw_end - draw_start).days + 1
        days_x = (draw_start - view_start).days

        x_bar = self.START_X + days_x * self.DAY_W
        w_bar = days_w * self.DAY_W
        y_bar = current_y + 10 + (lane * (self.BAR_H + self.BAR_GAP))

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
        color = self._get_color(row.get('category', ''))
        rect = QRectF(x_bar, y_bar, w_bar, self.BAR_H)

        bar_item = GanttBar(rect, full_info, color, self.on_bar_click)
        self.scene.addItem(bar_item)

        if w_bar > 20:
            display_txt = cat_str[:int(w_bar / 5)]
            t_item = self.scene.addText(display_txt)
            t_item.setFont(QFont("Arial", 8))
            t_item.setPos(x_bar, y_bar - 2)

    def _draw_today_line(self, view_start, total_days, today_ts, max_y):
        """Draw today indicator line"""
        pen_today = QPen(QColor("#FF5252"))
        pen_today.setWidth(2)

        for d in range(total_days):
            curr_date = view_start + pd.Timedelta(days=d)
            if curr_date == today_ts:
                x = self.START_X + d * self.DAY_W
                self.scene.addLine(x, self.HEADER_H, x, max_y, pen_today)

    def _get_color(self, test_type) -> str:
        """Get consistent color for test type"""
        if test_type not in self.color_map:
            self.color_map[test_type] = PASTEL_COLORS[
                len(self.color_map) % len(PASTEL_COLORS)
            ]
        return self.color_map[test_type]

