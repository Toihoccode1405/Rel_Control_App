"""
kRel - Report Tab (Refactored)
Tab báo cáo với báo cáo chi tiết và Gantt chart
"""
import pandas as pd

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QTabWidget, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QDateEdit, QTableView, QFileDialog, QMessageBox, QHeaderView,
    QGraphicsScene, QGraphicsView
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QPainter, QColor, QBrush, QFont

from src.services.database import get_db
from src.services.data_event_bus import get_event_bus
from src.services.logger import get_logger
from src.widgets.loading_overlay import LoadingMixin
from src.styles import (
    BTN_STYLE_BLUE, BTN_STYLE_ORANGE, TABLE_STYLE,
    TOOLBAR_BLUE_STYLE, INFO_LABEL_STYLE, TAB_STYLE
)
from src.views.report_tab.gantt_renderer import GanttRenderer

logger = get_logger("report_tab")


class ReportTab(QWidget, LoadingMixin):
    """Report tab with detail reports and Gantt chart"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_db()
        self.equip_map = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)
        self.tabs.addTab(self._init_report_1(), "📊 Báo Cáo Chi Tiết")
        self.tabs.addTab(self._init_report_2(), "📅 Theo Dõi Thiết Bị")
        layout.addWidget(self.tabs)

        self.setup_loading()
        self._connect_events()

    def _connect_events(self):
        """Connect to DataEventBus events"""
        bus = get_event_bus()
        bus.request_created.connect(lambda _: logger.debug("Data changed"))
        bus.request_updated.connect(lambda _: logger.debug("Data changed"))
        bus.equipment_changed.connect(self._load_equipments)

    # ==================== REPORT 1: Chi tiết ====================
    def _init_report_1(self) -> QWidget:
        """Initialize detail report tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # Filter frame
        frame = QFrame()
        frame.setStyleSheet(TOOLBAR_BLUE_STYLE)
        fl = QHBoxLayout(frame)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(12)

        # Date filters
        fl.addWidget(QLabel("<b style='color: #1565C0;'>📅 Từ:</b>"))
        self.r1_d1 = QDateEdit(QDate.currentDate().addMonths(-1))
        self.r1_d1.setCalendarPopup(True)
        self.r1_d1.setStyleSheet(self._date_style())
        fl.addWidget(self.r1_d1)

        fl.addWidget(QLabel("<b style='color: #1565C0;'>đến:</b>"))
        self.r1_d2 = QDateEdit(QDate.currentDate())
        self.r1_d2.setCalendarPopup(True)
        self.r1_d2.setStyleSheet(self._date_style())
        fl.addWidget(self.r1_d2)

        self.r1_all_time = QCheckBox("Tất cả thời gian")
        self.r1_all_time.setCursor(Qt.CursorShape.PointingHandCursor)
        self.r1_all_time.setStyleSheet("color: #424242; font-size: 12px;")
        fl.addWidget(self.r1_all_time)

        # Requester filter
        fl.addWidget(QLabel("<b style='color: #1565C0;'>👤 Người YC:</b>"))
        self.r1_req = QComboBox()
        self.r1_req.addItem("Tất cả")
        self.r1_req.setMinimumWidth(140)
        self.r1_req.setStyleSheet(self._combo_style())
        self._load_requesters()
        fl.addWidget(self.r1_req)

        fl.addStretch()

        # Buttons
        btn_view = QPushButton("🔍 Xem")
        btn_view.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_view.setStyleSheet(BTN_STYLE_BLUE)
        btn_view.clicked.connect(self._load_report_1)
        fl.addWidget(btn_view)

        btn_export = QPushButton("📤 Xuất CSV")
        btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export.setStyleSheet(BTN_STYLE_ORANGE)
        btn_export.clicked.connect(lambda: self._export_csv(self.r1_table, "BaoCao_ChiTiet"))
        fl.addWidget(btn_export)

        layout.addWidget(frame)

        # Table
        self.r1_table = QTableView()
        self.r1_table.setStyleSheet(TABLE_STYLE)
        self.r1_table.setAlternatingRowColors(True)
        layout.addWidget(self.r1_table)

        return widget

    # ==================== REPORT 2: Gantt ====================
    def _init_report_2(self) -> QWidget:
        """Initialize Gantt chart tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # Filter frame
        frame = QFrame()
        frame.setStyleSheet(TOOLBAR_BLUE_STYLE)
        fl = QHBoxLayout(frame)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(12)

        # Date filters
        fl.addWidget(QLabel("<b style='color: #1565C0;'>📅 Từ:</b>"))
        self.r2_d1 = QDateEdit(QDate.currentDate().addDays(-7))
        self.r2_d1.setCalendarPopup(True)
        self.r2_d1.setStyleSheet(self._date_style())
        fl.addWidget(self.r2_d1)

        fl.addWidget(QLabel("<b style='color: #1565C0;'>đến:</b>"))
        self.r2_d2 = QDateEdit(QDate.currentDate().addDays(14))
        self.r2_d2.setCalendarPopup(True)
        self.r2_d2.setStyleSheet(self._date_style())
        fl.addWidget(self.r2_d2)

        # Equipment filter
        fl.addWidget(QLabel("<b style='color: #1565C0;'>🔧 Thiết bị:</b>"))
        self.r2_equip = QComboBox()
        self.r2_equip.addItem("Tất cả Thiết Bị")
        self.r2_equip.setMinimumWidth(160)
        self.r2_equip.setStyleSheet(self._combo_style())
        self.r2_equip.currentTextChanged.connect(self._update_equip_name)
        fl.addWidget(self.r2_equip)

        self.r2_name_display = QLineEdit()
        self.r2_name_display.setReadOnly(True)
        self.r2_name_display.setPlaceholderText("Tên thiết bị...")
        self.r2_name_display.setStyleSheet("""
            background: #E3F2FD; color: #1565C0;
            border: 1px solid #BBDEFB; border-radius: 6px;
            padding: 6px 10px; min-height: 32px;
        """)
        fl.addWidget(self.r2_name_display, 1)

        self._load_equipments()

        btn_view = QPushButton("🔍 Xem")
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

        # Gantt renderer
        self.gantt_renderer = GanttRenderer(
            self.scene, self.equip_map, self._on_bar_click
        )

        return widget

    # ==================== Helper Methods ====================
    def _date_style(self):
        return """
            QDateEdit {
                border: 1px solid #CFD8DC; border-radius: 6px;
                padding: 6px 12px; background-color: #FFFFFF;
                min-height: 32px; font-size: 13px;
            }
            QDateEdit:hover { border-color: #90CAF9; }
            QDateEdit:focus { border: 2px solid #1565C0; }
        """

    def _combo_style(self):
        return """
            QComboBox {
                border: 1px solid #CFD8DC; border-radius: 6px;
                padding: 6px 12px; background-color: #FFFFFF;
                min-height: 32px; font-size: 13px;
            }
            QComboBox:hover { border-color: #90CAF9; }
            QComboBox:focus { border: 2px solid #1565C0; }
        """

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

            # Update combo
            current = self.r2_equip.currentText()
            self.r2_equip.blockSignals(True)
            self.r2_equip.clear()
            self.r2_equip.addItem("Tất cả Thiết Bị")
            for code in self.equip_map:
                self.r2_equip.addItem(code)
            self.r2_equip.setCurrentText(current)
            self.r2_equip.blockSignals(False)

            # Update gantt renderer
            if hasattr(self, 'gantt_renderer'):
                self.gantt_renderer.equip_map = self.equip_map
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

    def _on_bar_click(self, text):
        """Handle Gantt bar click"""
        self.lbl_click_info.setText(text)

    # ==================== Data Loading ====================
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

            col_final_idx = headers.index("KQ Cuối") if "KQ Cuối" in headers else -1

            for _, row in df.iterrows():
                items = []
                for i, x in enumerate(row):
                    val = str(x) if x is not None else ""
                    item = QStandardItem(val)

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
            self.lbl_click_info.setText("<i>(Click vào thanh test để xem chi tiết...)</i>")

            d1 = self.r2_d1.date().toString("yyyy-MM-dd")
            d2 = self.r2_d2.date().toString("yyyy-MM-dd")
            equip = self.r2_equip.currentText()

            self.gantt_renderer.draw(equip, d1, d2)
        finally:
            self.hide_loading()

