"""
kRel - Request Service
CRUD operations for reliability test requests
"""
from typing import Optional, List
from datetime import datetime

from src.models.request import Request
from src.services.database import get_db
from src.services.logger import get_logger, log_audit

# Module logger
logger = get_logger("request")


class RequestService:
    """Service for managing test requests"""

    def create(self, request: Request) -> int:
        """
        Create new request
        Returns: new request ID
        """
        db = get_db()

        columns = ", ".join(Request.DB_FIELDS)
        placeholders = ", ".join(["?"] * len(Request.DB_FIELDS))

        with db.get_cursor() as cursor:
            cursor.execute(
                f"INSERT INTO requests ({columns}) VALUES ({placeholders})",
                request.to_insert_tuple()
            )
            # Get the new ID
            cursor.execute("SELECT @@IDENTITY")
            result = cursor.fetchone()
            new_id = result[0] if result else 0

        logger.info(f"Created request: {request.request_no} (ID: {new_id})")
        log_audit("REQUEST_CREATE", user=request.requester,
                  details=f"ID: {new_id}, Code: {request.request_no}")

        return new_id

    def update(self, request: Request) -> bool:
        """
        Update existing request
        Returns: success
        """
        if not request.id:
            return False

        db = get_db()

        set_clause = ", ".join([f"{field} = ?" for field in Request.DB_FIELDS])

        with db.get_cursor() as cursor:
            cursor.execute(
                f"UPDATE requests SET {set_clause} WHERE id = ?",
                (*request.to_insert_tuple(), request.id)
            )

        logger.debug(f"Updated request ID: {request.id}")
        return True

    def delete(self, request_id: int) -> bool:
        """Delete request by ID"""
        db = get_db()

        # Get request info for logging
        existing = self.get_by_id(request_id)
        request_no = existing.request_no if existing else "unknown"

        with db.get_cursor() as cursor:
            cursor.execute("DELETE FROM requests WHERE id = ?", (request_id,))

        logger.info(f"Deleted request ID: {request_id} (Code: {request_no})")
        log_audit("REQUEST_DELETE", details=f"ID: {request_id}, Code: {request_no}")

        return True
        return True
    
    def get_by_id(self, request_id: int) -> Optional[Request]:
        """Get single request by ID"""
        db = get_db()
        row = db.fetch_one("SELECT * FROM requests WHERE id = ?", (request_id,))
        if row:
            return Request.from_db_row(row)
        return None
    
    def get_all(self, order_by: str = "id DESC") -> List[Request]:
        """Get all requests"""
        db = get_db()
        rows = db.fetch_all(f"SELECT * FROM requests ORDER BY {order_by}")
        return [Request.from_db_row(row) for row in rows]
    
    def get_by_date(self, date_str: str) -> List[Request]:
        """Get requests by date (YYYY-MM-DD format matches start of request_date)"""
        db = get_db()
        rows = db.fetch_all(
            "SELECT * FROM requests WHERE request_date LIKE ? ORDER BY id DESC",
            (f"{date_str}%",)
        )
        return [Request.from_db_row(row) for row in rows]
    
    def get_by_date_range(self, start_date: str, end_date: str, 
                          requester: str = None) -> List[Request]:
        """Get requests within date range"""
        db = get_db()
        
        query = "SELECT * FROM requests WHERE request_date BETWEEN ? AND ?"
        params = [start_date, end_date]
        
        if requester:
            query += " AND requester = ?"
            params.append(requester)
        
        query += " ORDER BY request_date DESC"
        
        rows = db.fetch_all(query, tuple(params))
        return [Request.from_db_row(row) for row in rows]
    
    def get_by_status(self, status: str) -> List[Request]:
        """Get requests by status"""
        db = get_db()
        rows = db.fetch_all(
            "SELECT * FROM requests WHERE status = ? ORDER BY id DESC",
            (status,)
        )
        return [Request.from_db_row(row) for row in rows]
    
    def get_by_equipment(self, equip_no: str) -> List[Request]:
        """Get requests by equipment"""
        db = get_db()
        rows = db.fetch_all(
            "SELECT * FROM requests WHERE equip_no = ? ORDER BY plan_start DESC",
            (equip_no,)
        )
        return [Request.from_db_row(row) for row in rows]
    
    def generate_request_code(self, date: datetime) -> str:
        """Generate next request code for given date"""
        db = get_db()
        date_str = date.strftime("%Y%m%d")
        
        # Get last code for this date
        row = db.fetch_one(
            """SELECT TOP 1 request_no FROM requests 
               WHERE request_no LIKE ? 
               ORDER BY request_no DESC""",
            (f"{date_str}-%",)
        )
        
        if row and row[0]:
            try:
                last_seq = int(row[0].split("-")[1])
                return f"{date_str}-{last_seq + 1:03d}"
            except (IndexError, ValueError):
                pass
        
        return f"{date_str}-001"
    
    def get_for_gantt(self, start_date: str, end_date: str, 
                      equip_no: str = None) -> List[Request]:
        """Get requests for Gantt chart view"""
        db = get_db()
        
        query = """
            SELECT * FROM requests 
            WHERE equip_no IS NOT NULL AND equip_no != ''
            AND (
                (plan_start BETWEEN ? AND ?) 
                OR (actual_start BETWEEN ? AND ?)
            )
        """
        params = [start_date, end_date, start_date, end_date]
        
        if equip_no:
            query += " AND equip_no = ?"
            params.append(equip_no)
        
        query += " ORDER BY equip_no, plan_start"
        
        rows = db.fetch_all(query, tuple(params))
        return [Request.from_db_row(row) for row in rows]
    
    def get_distinct_requesters(self) -> List[str]:
        """Get list of distinct requesters"""
        db = get_db()
        rows = db.fetch_all(
            "SELECT DISTINCT requester FROM requests WHERE requester IS NOT NULL AND requester != '' ORDER BY requester"
        )
        return [row[0] for row in rows]
    
    def count_by_status(self) -> dict:
        """Get count of requests grouped by status"""
        db = get_db()
        rows = db.fetch_all(
            "SELECT status, COUNT(*) FROM requests GROUP BY status"
        )
        return {row[0] or "Unknown": row[1] for row in rows}


# Singleton instance
_request_service: Optional[RequestService] = None

def get_request_service() -> RequestService:
    """Get request service instance"""
    global _request_service
    if _request_service is None:
        _request_service = RequestService()
    return _request_service

