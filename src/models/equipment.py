"""
kRel - Equipment Model
"""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Equipment:
    """Equipment entity model"""
    control_no: str  # Primary key
    factory: str = ""
    name: str = ""
    spec: str = ""
    recipe1: str = ""
    recipe2: str = ""
    recipe3: str = ""
    recipe4: str = ""
    recipe5: str = ""
    remark: str = ""
    
    @classmethod
    def from_db_row(cls, row: tuple) -> "Equipment":
        """Create Equipment from database row"""
        if not row:
            return cls(control_no="")
        return cls(
            factory=row[0] or "",
            control_no=row[1] or "",
            name=row[2] or "",
            spec=row[3] or "",
            recipe1=row[4] or "" if len(row) > 4 else "",
            recipe2=row[5] or "" if len(row) > 5 else "",
            recipe3=row[6] or "" if len(row) > 6 else "",
            recipe4=row[7] or "" if len(row) > 7 else "",
            recipe5=row[8] or "" if len(row) > 8 else "",
            remark=row[9] or "" if len(row) > 9 else ""
        )
    
    def to_tuple(self) -> tuple:
        """Convert to tuple for database operations"""
        return (
            self.factory, self.control_no, self.name, self.spec,
            self.recipe1, self.recipe2, self.recipe3, self.recipe4, self.recipe5,
            self.remark
        )
    
    def get_recipes(self) -> List[str]:
        """Get list of non-empty recipes"""
        recipes = [self.recipe1, self.recipe2, self.recipe3, self.recipe4, self.recipe5]
        return [r for r in recipes if r and r.strip() and r != "-"]
    
    def get_display_name(self) -> str:
        """Get display name combining control_no and name"""
        return f"{self.control_no} - {self.name}" if self.name else self.control_no

