"""
kRel - Request Model
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from datetime import datetime


@dataclass
class Request:
    """Request entity model - represents a reliability test request"""
    id: Optional[int] = None
    request_no: str = ""
    request_date: str = ""
    requester: str = ""
    factory: str = ""
    project: str = ""
    phase: str = ""
    category: str = ""
    detail: str = ""
    qty: str = ""
    
    # Test results
    cos: str = ""           # Cosmetic test quantity
    cos_res: str = ""       # Cosmetic result
    hcross: str = ""        # Cross hatch quantity  
    xhatch_res: str = ""    # Cross hatch result
    xcross: str = ""        # Cross section quantity
    xsection_res: str = ""  # Cross section result
    func_test: str = ""     # Function test quantity
    func_res: str = ""      # Function result
    final_res: str = ""     # Final result (Pass/Fail/Waiver)
    
    # Equipment info
    equip_no: str = ""
    equip_name: str = ""
    test_condition: str = ""
    
    # Schedule
    plan_start: str = ""
    plan_end: str = ""
    actual_start: str = ""
    actual_end: str = ""
    
    # Tracking
    status: str = ""
    dri: str = ""
    logfile: str = ""
    log_link: str = ""
    note: str = ""
    
    # Database field order for INSERT/SELECT
    DB_FIELDS = [
        "request_no", "request_date", "requester", "factory", "project",
        "phase", "category", "detail", "qty", "cos", "hcross", "xcross", 
        "func_test", "cos_res", "xhatch_res", "xsection_res", "func_res", 
        "final_res", "equip_no", "equip_name", "test_condition", "plan_start",
        "plan_end", "status", "dri", "actual_start", "actual_end", "logfile",
        "log_link", "note"
    ]
    
    @classmethod
    def from_db_row(cls, row: tuple) -> "Request":
        """Create Request from database row (includes id as first column)"""
        if not row:
            return cls()
        
        return cls(
            id=row[0],
            request_no=row[1] or "",
            request_date=row[2] or "",
            requester=row[3] or "",
            factory=row[4] or "",
            project=row[5] or "",
            phase=row[6] or "",
            category=row[7] or "",
            detail=row[8] or "",
            qty=row[9] or "",
            cos=row[10] or "",
            hcross=row[11] or "",
            xcross=row[12] or "",
            func_test=row[13] or "",
            cos_res=row[14] or "",
            xhatch_res=row[15] or "",
            xsection_res=row[16] or "",
            func_res=row[17] or "",
            final_res=row[18] or "",
            equip_no=row[19] or "",
            equip_name=row[20] or "",
            test_condition=row[21] or "",
            plan_start=row[22] or "",
            plan_end=row[23] or "",
            status=row[24] or "",
            dri=row[25] or "",
            actual_start=row[26] or "",
            actual_end=row[27] or "",
            logfile=row[28] or "",
            log_link=row[29] or "",
            note=row[30] or "" if len(row) > 30 else ""
        )
    
    def to_insert_tuple(self) -> tuple:
        """Convert to tuple for INSERT (without id)"""
        return (
            self.request_no, self.request_date, self.requester, self.factory,
            self.project, self.phase, self.category, self.detail, self.qty,
            self.cos, self.hcross, self.xcross, self.func_test,
            self.cos_res, self.xhatch_res, self.xsection_res, self.func_res,
            self.final_res, self.equip_no, self.equip_name, self.test_condition,
            self.plan_start, self.plan_end, self.status, self.dri,
            self.actual_start, self.actual_end, self.logfile, self.log_link, self.note
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def is_complete(self) -> bool:
        """Check if request has required fields"""
        return bool(self.request_no and self.request_date and self.requester)
    
    def get_status_color(self) -> str:
        """Get color based on status"""
        from src.config import STATUS_COLORS, EMPTY_CELL_COLOR
        return STATUS_COLORS.get(self.status, EMPTY_CELL_COLOR)
    
    @staticmethod
    def generate_code(date_str: str, last_seq: int = 0) -> str:
        """Generate request code: YYYYMMDD-NNN"""
        seq = last_seq + 1
        return f"{date_str}-{seq:03d}"

