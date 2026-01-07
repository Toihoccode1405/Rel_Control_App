"""
kRel - Request Controller
Xử lý logic CRUD cho requests, tách khỏi UI
"""
import os
import shutil
from datetime import datetime
from typing import Optional, List, Tuple

from PyQt6.QtCore import QDate

from src.services.database import get_db
from src.services.logger import get_logger, log_audit
from src.services.data_event_bus import get_event_bus

logger = get_logger("request_controller")


class RequestController:
    """Controller xử lý logic cho Request"""
    
    def __init__(self, log_path: str = ""):
        self.log_path = log_path
        self.db = get_db()
    
    def generate_request_code(self, date: datetime = None) -> str:
        """Tạo mã request mới theo format YYYYMMDD-XXX"""
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y%m%d")
        
        try:
            query = """
                SELECT TOP 1 request_no FROM requests 
                WHERE request_no LIKE ? ORDER BY request_no DESC
            """
            row = self.db.fetch_one(query, (f"{date_str}-%",))
            
            if row and row[0]:
                last_seq = int(row[0].split("-")[1])
                return f"{date_str}-{last_seq + 1:03d}"
        except Exception as e:
            logger.error(f"Error generating code: {e}")
        
        return f"{date_str}-001"
    
    def save(self, values: dict, user_name: str) -> Tuple[bool, str]:
        """
        Lưu request mới
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            request_no = values.get("request_no", "")
            
            # Build INSERT query
            columns = list(values.keys())
            placeholders = ", ".join(["?"] * len(columns))
            cols_str = ", ".join(columns)
            
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    f"INSERT INTO requests ({cols_str}) VALUES ({placeholders})",
                    list(values.values())
                )
            
            logger.info(f"Request saved: {request_no}")
            log_audit("REQUEST_CREATE", user=user_name, details=f"Code: {request_no}")
            
            # Emit event
            get_event_bus().emit_request_created(request_no)
            
            return True, "Đã lưu thành công!"
            
        except Exception as e:
            logger.error(f"Failed to save: {e}", exc_info=True)
            return False, str(e)
    
    def copy_log_file(self, source_path: str, request_no: str) -> bool:
        """Copy log file vào thư mục request"""
        if not source_path or not os.path.exists(source_path):
            return False
        
        try:
            dest_dir = os.path.join(self.log_path, request_no)
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy(source_path, dest_dir)
            logger.debug(f"Log copied to {dest_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy log: {e}")
            return False
    
    def get_recent_requests(self, filter_type: int = 1, 
                            search_text: str = "", 
                            search_field: int = 0) -> List[tuple]:
        """
        Lấy danh sách request gần đây
        
        Args:
            filter_type: 0=Hôm nay, 1=7 ngày, 2=30 ngày, 3=Tất cả
            search_text: Từ khóa tìm kiếm
            search_field: 0=Tất cả, 1=Mã YC, 2=Người YC, ...
        """
        try:
            today = QDate.currentDate()
            
            # Build date condition
            if filter_type == 0:
                date_str = today.toString("yyyy-MM-dd")
                condition = "request_date LIKE ?"
                params = [f"{date_str}%"]
            elif filter_type == 1:
                start = today.addDays(-7).toString("yyyy-MM-dd")
                condition = "request_date >= ?"
                params = [start]
            elif filter_type == 2:
                start = today.addDays(-30).toString("yyyy-MM-dd")
                condition = "request_date >= ?"
                params = [start]
            else:
                condition = "1=1"
                params = []
            
            query = f"""
                SELECT request_no, request_date, requester, factory, project, phase,
                       equip_no, equip_name, test_condition,
                       plan_start, plan_end, actual_start, actual_end,
                       status, dri, final_res
                FROM requests WHERE {condition} ORDER BY id DESC
            """
            
            rows = self.db.fetch_all(query, tuple(params) if params else None)
            return rows
            
        except Exception as e:
            logger.error(f"Failed to load requests: {e}")
            return []
    
    def delete(self, request_id: int, user_name: str) -> Tuple[bool, str]:
        """Xóa request"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("DELETE FROM requests WHERE id = ?", (request_id,))
            
            log_audit("REQUEST_DELETE", user=user_name, details=f"ID: {request_id}")
            get_event_bus().emit_request_updated(str(request_id))
            
            return True, "Đã xóa!"
        except Exception as e:
            logger.error(f"Failed to delete: {e}")
            return False, str(e)

