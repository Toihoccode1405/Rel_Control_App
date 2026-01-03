"""
kRel - Gantt Chart Widget
Interactive Gantt chart for equipment/test scheduling visualization
"""
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QBrush, QPen, QFont, QPainter

from src.config import PASTEL_COLORS


class GanttBar(QGraphicsRectItem):
    """Interactive Gantt chart bar representing a test/task"""
    
    def __init__(self, rect: QRectF, info_text: str, color_hex: str, 
                 click_callback=None):
        """
        Args:
            rect: Bar rectangle
            info_text: Information text for tooltip and click display
            color_hex: Bar color in hex format
            click_callback: Function to call when bar is clicked
        """
        super().__init__(rect)
        self.info_text = info_text
        self.click_callback = click_callback
        self.original_color = QColor(color_hex)
        
        # Setup appearance
        self.setToolTip(info_text)
        self.setBrush(QBrush(self.original_color))
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setAcceptHoverEvents(True)
    
    def hoverEnterEvent(self, event):
        """Lighten color on hover"""
        self.setBrush(QBrush(self.original_color.lighter(115)))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Restore original color"""
        self.setBrush(QBrush(self.original_color))
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle click to show info"""
        if self.click_callback:
            self.click_callback(self.info_text)
        super().mousePressEvent(event)


class GanttChartView(QGraphicsView):
    """Gantt chart view with pan and zoom support"""
    
    def __init__(self, scene: QGraphicsScene = None):
        super().__init__(scene or QGraphicsScene())
        
        # Setup rendering
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setStyleSheet("""
            background: white;
            border: 1px solid #ccc;
            border-radius: 4px;
        """)
        
        # Enable drag scrolling
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        factor = 1.1
        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1 / factor, 1 / factor)


class GanttChartHelper:
    """Helper class for Gantt chart calculations and color management"""
    
    def __init__(self):
        self.color_map = {}
        self.color_index = 0
    
    def get_color(self, category: str) -> str:
        """Get consistent color for a category"""
        if category not in self.color_map:
            self.color_map[category] = PASTEL_COLORS[
                self.color_index % len(PASTEL_COLORS)
            ]
            self.color_index += 1
        return self.color_map[category]
    
    def reset_colors(self):
        """Reset color mapping"""
        self.color_map = {}
        self.color_index = 0
    
    @staticmethod
    def calculate_lanes(items: list, get_start, get_end) -> list:
        """
        Calculate lane assignments for overlapping items.
        
        Args:
            items: List of items to place
            get_start: Function to get start datetime from item
            get_end: Function to get end datetime from item
            
        Returns:
            List of (item, lane_index) tuples
        """
        lanes = []  # Track end time of each lane
        placements = []
        
        for item in items:
            start = get_start(item)
            end = get_end(item)
            
            # Find available lane
            chosen_lane = -1
            for i, lane_end in enumerate(lanes):
                if start >= lane_end:
                    chosen_lane = i
                    lanes[i] = end
                    break
            
            # Create new lane if needed
            if chosen_lane == -1:
                lanes.append(end)
                chosen_lane = len(lanes) - 1
            
            placements.append((item, chosen_lane))
        
        return placements
    
    @staticmethod
    def format_info_text(data: dict, fields: list) -> str:
        """Format data dictionary into info string"""
        parts = []
        for field in fields:
            value = data.get(field, "")
            if value and str(value) != "None":
                parts.append(str(value))
        return " | ".join(parts)

