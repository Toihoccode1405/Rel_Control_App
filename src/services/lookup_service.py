"""
kRel - Lookup Service
Manage lookup tables (factory, project, phase, category, status) and equipment
"""
from typing import List, Optional

from src.models.equipment import Equipment
from src.services.database import get_db


class LookupService:
    """Service for managing lookup tables and equipment"""
    
    # ========== LOOKUP TABLES (factory, project, phase, category, status) ==========
    
    def get_lookup_values(self, table_name: str) -> List[str]:
        """Get all values from a lookup table"""
        db = get_db()
        rows = db.fetch_all(f"SELECT name FROM {table_name} ORDER BY name")
        return [row[0] for row in rows if row[0]]
    
    def add_lookup_value(self, table_name: str, value: str) -> tuple[bool, str]:
        """Add new value to lookup table"""
        if not value or not value.strip():
            return False, "Giá trị không được để trống!"
        
        try:
            db = get_db()
            with db.get_cursor() as cursor:
                # Check if exists
                cursor.execute(f"SELECT name FROM {table_name} WHERE name = ?", (value,))
                if cursor.fetchone():
                    return False, "Giá trị đã tồn tại!"
                
                cursor.execute(f"INSERT INTO {table_name} (name) VALUES (?)", (value,))
            return True, "Thêm thành công!"
        except Exception as e:
            return False, str(e)
    
    def update_lookup_value(self, table_name: str, old_value: str, 
                            new_value: str) -> tuple[bool, str]:
        """Update value in lookup table"""
        if not new_value or not new_value.strip():
            return False, "Giá trị không được để trống!"
        
        try:
            db = get_db()
            with db.get_cursor() as cursor:
                cursor.execute(
                    f"UPDATE {table_name} SET name = ? WHERE name = ?",
                    (new_value, old_value)
                )
            return True, "Cập nhật thành công!"
        except Exception as e:
            return False, str(e)
    
    def delete_lookup_value(self, table_name: str, value: str) -> tuple[bool, str]:
        """Delete value from lookup table"""
        try:
            db = get_db()
            with db.get_cursor() as cursor:
                cursor.execute(f"DELETE FROM {table_name} WHERE name = ?", (value,))
            return True, "Xóa thành công!"
        except Exception as e:
            return False, str(e)
    
    # ========== EQUIPMENT ==========
    
    def get_all_equipment(self) -> List[Equipment]:
        """Get all equipment"""
        db = get_db()
        rows = db.fetch_all(
            "SELECT factory, control_no, name, spec, r1, r2, r3, r4, r5, remark FROM equipment ORDER BY control_no"
        )
        return [Equipment.from_db_row(row) for row in rows]
    
    def get_equipment_by_id(self, control_no: str) -> Optional[Equipment]:
        """Get equipment by control number"""
        db = get_db()
        row = db.fetch_one(
            "SELECT factory, control_no, name, spec, r1, r2, r3, r4, r5, remark FROM equipment WHERE control_no = ?",
            (control_no,)
        )
        if row:
            return Equipment.from_db_row(row)
        return None
    
    def get_equipment_list(self) -> List[str]:
        """Get list of equipment control numbers"""
        db = get_db()
        rows = db.fetch_all("SELECT control_no FROM equipment ORDER BY control_no")
        return [row[0] for row in rows if row[0]]
    
    def get_equipment_name(self, control_no: str) -> str:
        """Get equipment name by control number"""
        db = get_db()
        row = db.fetch_one(
            "SELECT name FROM equipment WHERE control_no = ?",
            (control_no,)
        )
        return row[0] if row else ""
    
    def get_equipment_recipes(self, control_no: str) -> List[str]:
        """Get recipes for equipment"""
        equip = self.get_equipment_by_id(control_no)
        if equip:
            return equip.get_recipes()
        return []
    
    def add_equipment(self, equipment: Equipment) -> tuple[bool, str]:
        """Add new equipment"""
        if not equipment.control_no:
            return False, "Mã thiết bị không được để trống!"
        
        try:
            db = get_db()
            with db.get_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO equipment 
                       (factory, control_no, name, spec, r1, r2, r3, r4, r5, remark)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    equipment.to_tuple()
                )
            return True, "Thêm thành công!"
        except Exception as e:
            if "duplicate" in str(e).lower() or "primary key" in str(e).lower():
                return False, "Mã thiết bị đã tồn tại!"
            return False, str(e)
    
    def update_equipment(self, equipment: Equipment) -> tuple[bool, str]:
        """Update equipment"""
        try:
            db = get_db()
            with db.get_cursor() as cursor:
                cursor.execute(
                    """UPDATE equipment SET 
                       factory=?, name=?, spec=?, r1=?, r2=?, r3=?, r4=?, r5=?, remark=?
                       WHERE control_no=?""",
                    (equipment.factory, equipment.name, equipment.spec,
                     equipment.recipe1, equipment.recipe2, equipment.recipe3,
                     equipment.recipe4, equipment.recipe5, equipment.remark,
                     equipment.control_no)
                )
            return True, "Cập nhật thành công!"
        except Exception as e:
            return False, str(e)
    
    def delete_equipment(self, control_no: str) -> tuple[bool, str]:
        """Delete equipment"""
        try:
            db = get_db()
            with db.get_cursor() as cursor:
                cursor.execute("DELETE FROM equipment WHERE control_no = ?", (control_no,))
            return True, "Xóa thành công!"
        except Exception as e:
            return False, str(e)


# Singleton instance
_lookup_service: Optional[LookupService] = None

def get_lookup_service() -> LookupService:
    """Get lookup service instance"""
    global _lookup_service
    if _lookup_service is None:
        _lookup_service = LookupService()
    return _lookup_service

