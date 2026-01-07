"""
kRel - CSV Handler
Xử lý import/export CSV cho requests
"""
import os
from datetime import datetime
from typing import List, Tuple

import pandas as pd

from src.services.database import get_db
from src.services.logger import get_logger, log_audit
from src.services.data_event_bus import get_event_bus

logger = get_logger("csv_handler")


class CsvHandler:
    """Xử lý import/export CSV"""
    
    # Mapping columns
    CSV_HEADERS = [
        "request_no", "request_date", "requester", "factory", "project", "phase",
        "category", "equip_no", "equip_name", "qty", "test_condition",
        "cos", "cos_res", "hcross", "xhatch_res", "xcross", "xsection_res",
        "func_test", "func_res", "final_res", "status",
        "plan_start", "plan_end", "actual_start", "actual_end", "note", "dri"
    ]
    
    CSV_HEADERS_VI = [
        "Mã YC", "Ngày YC", "Người YC", "Nhà Máy", "Dự Án", "Giai Đoạn",
        "Hạng Mục", "Mã TB", "Tên TB", "Số Lượng", "ĐK Test",
        "CoS", "KQ CoS", "HCross", "KQ XHatch", "XCross", "KQ XSection",
        "Func Test", "KQ Func", "KQ Cuối", "Trạng Thái",
        "Vào KH", "Ra KH", "Vào TT", "Ra TT", "Ghi Chú", "DRI"
    ]
    
    def __init__(self):
        self.db = get_db()
    
    def create_template(self, path: str) -> Tuple[bool, str]:
        """Tạo file mẫu CSV"""
        try:
            df = pd.DataFrame(columns=self.CSV_HEADERS_VI)
            
            # Sample row
            today = datetime.now().strftime("%Y-%m-%d")
            sample = {
                "Mã YC": "(Tự động)", "Ngày YC": today,
                "Người YC": "Tên người yêu cầu", "Nhà Máy": "F1/F2/F3...",
                "Dự Án": "Tên dự án", "Giai Đoạn": "EVT/DVT/PVT/MP",
                "Hạng Mục": "Hạng mục test", "Mã TB": "Mã thiết bị",
                "Tên TB": "Tên thiết bị", "Số Lượng": "1",
                "ĐK Test": "Điều kiện test",
            }
            df = pd.concat([df, pd.DataFrame([sample])], ignore_index=True)
            df.to_csv(path, index=False, encoding='utf-8-sig')
            
            return True, "Đã tạo file mẫu!"
        except Exception as e:
            logger.error(f"Template error: {e}")
            return False, str(e)
    
    def import_csv(self, path: str) -> Tuple[int, int, List[str]]:
        """
        Import từ CSV
        
        Returns:
            Tuple[imported, skipped, errors]
        """
        imported, skipped = 0, 0
        errors = []
        
        try:
            # Try encodings
            df = None
            for enc in ['utf-8-sig', 'utf-8', 'cp1252']:
                try:
                    df = pd.read_csv(path, encoding=enc)
                    break
                except Exception:
                    continue
            
            if df is None or df.empty:
                return 0, 0, ["Không thể đọc file"]
            
            # Map Vietnamese headers to English
            header_map = dict(zip(self.CSV_HEADERS_VI, self.CSV_HEADERS))
            df.columns = [header_map.get(c, c) for c in df.columns]
            
            with self.db.get_cursor() as cursor:
                for idx, row in df.iterrows():
                    try:
                        # Skip sample/empty rows
                        requester = str(row.get("requester", "")).strip()
                        if not requester or requester == "Tên người yêu cầu":
                            skipped += 1
                            continue
                        
                        # Generate code if empty
                        code = str(row.get("request_no", "")).strip()
                        if not code or code == "(Tự động)":
                            code = self._generate_code(cursor)
                        
                        # Build values
                        values = {"request_no": code}
                        for col in self.CSV_HEADERS[1:]:
                            val = row.get(col, "")
                            values[col] = self._format_value(col, val)
                        
                        # Insert
                        cols = ", ".join(values.keys())
                        placeholders = ", ".join(["?"] * len(values))
                        cursor.execute(
                            f"INSERT INTO requests ({cols}) VALUES ({placeholders})",
                            list(values.values())
                        )
                        imported += 1
                        
                    except Exception as e:
                        errors.append(f"Dòng {idx + 2}: {str(e)}")
            
            if imported > 0:
                get_event_bus().emit_request_created("batch_import")
                log_audit("CSV_IMPORT", details=f"Imported {imported} records")
            
        except Exception as e:
            errors.append(str(e))
        
        return imported, skipped, errors
    
    def export_csv(self, path: str, filter_type: int = 3) -> Tuple[bool, int, str]:
        """Export ra CSV"""
        try:
            from PyQt6.QtCore import QDate
            today = QDate.currentDate()
            
            # Build condition
            if filter_type == 0:
                cond = f"request_date LIKE '{today.toString('yyyy-MM-dd')}%'"
            elif filter_type == 1:
                cond = f"request_date >= '{today.addDays(-7).toString('yyyy-MM-dd')}'"
            elif filter_type == 2:
                cond = f"request_date >= '{today.addDays(-30).toString('yyyy-MM-dd')}'"
            else:
                cond = "1=1"
            
            cols = ", ".join(self.CSV_HEADERS)
            rows = self.db.fetch_all(
                f"SELECT {cols} FROM requests WHERE {cond} ORDER BY id DESC"
            )
            
            df = pd.DataFrame(rows, columns=self.CSV_HEADERS_VI)
            df = df.fillna("")
            df.to_csv(path, index=False, encoding='utf-8-sig')
            
            return True, len(rows), "Xuất thành công!"
        except Exception as e:
            return False, 0, str(e)
    
    def _generate_code(self, cursor) -> str:
        """Generate next code"""
        today = datetime.now().strftime("%Y%m%d")
        cursor.execute(
            "SELECT TOP 1 request_no FROM requests WHERE request_no LIKE ? ORDER BY request_no DESC",
            (f"{today}-%",)
        )
        row = cursor.fetchone()
        if row and row[0]:
            seq = int(row[0].split("-")[1]) + 1
            return f"{today}-{seq:03d}"
        return f"{today}-001"
    
    def _format_value(self, col: str, val) -> str:
        """Format value cho import"""
        if pd.isna(val):
            return ""
        val = str(val).strip()
        if val.lower() == "nan":
            return ""
        return val

