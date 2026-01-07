"""
kRel - Lookup Service
Manage lookup tables (factory, project, phase, category, status) and equipment

Performance Features:
- In-memory caching with TTL (Time To Live)
- Cache invalidation on data changes
- Reduced database calls
"""
import time
import logging
from typing import List, Optional, Dict, Any

from src.models.equipment import Equipment
from src.services.database import get_db

# Module logger
lookup_logger = logging.getLogger("kRel.lookup")


class CacheEntry:
    """Cache entry with TTL support"""

    def __init__(self, data: Any, ttl_seconds: int = 300):
        self.data = data
        self.created_at = time.time()
        self.ttl = ttl_seconds

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() - self.created_at > self.ttl


class LookupService:
    """
    Service for managing lookup tables and equipment.

    Features:
    - Caching with configurable TTL (default 5 minutes)
    - Automatic cache invalidation on data changes
    - Thread-safe cache operations
    """

    # Valid lookup table names (whitelist for security)
    VALID_TABLES = {"factory", "project", "phase", "category", "status"}

    # Cache TTL in seconds
    CACHE_TTL = 300  # 5 minutes

    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._equipment_cache: Optional[CacheEntry] = None
        self._equipment_map_cache: Dict[str, CacheEntry] = {}

    def _validate_table_name(self, table_name: str) -> bool:
        """Validate table name to prevent SQL injection"""
        return table_name in self.VALID_TABLES

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired():
                return entry.data
            else:
                del self._cache[key]
        return None

    def _set_cache(self, key: str, data: Any, ttl: int = None):
        """Set cache value"""
        self._cache[key] = CacheEntry(data, ttl or self.CACHE_TTL)

    def invalidate_cache(self, table_name: str = None):
        """
        Invalidate cache for a specific table or all caches.

        Args:
            table_name: Specific table to invalidate, or None for all
        """
        if table_name:
            cache_key = f"lookup_{table_name}"
            if cache_key in self._cache:
                del self._cache[cache_key]
                lookup_logger.debug(f"Cache invalidated for: {table_name}")
        else:
            self._cache.clear()
            self._equipment_cache = None
            self._equipment_map_cache.clear()
            lookup_logger.debug("All caches invalidated")

    def invalidate_equipment_cache(self):
        """Invalidate equipment-related caches"""
        self._equipment_cache = None
        self._equipment_map_cache.clear()
        # Also clear equipment list cache
        if "equipment_list" in self._cache:
            del self._cache["equipment_list"]
        lookup_logger.debug("Equipment cache invalidated")
    
    # ========== LOOKUP TABLES (factory, project, phase, category, status) ==========

    def get_lookup_values(self, table_name: str) -> List[str]:
        """Get all values from a lookup table (cached)"""
        # Validate table name for security
        if not self._validate_table_name(table_name):
            lookup_logger.warning(f"Invalid table name requested: {table_name}")
            return []

        # Check cache first
        cache_key = f"lookup_{table_name}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        # Fetch from database
        db = get_db()
        rows = db.fetch_all(f"SELECT name FROM {table_name} ORDER BY name")
        result = [row[0] for row in rows if row[0]]

        # Cache the result
        self._set_cache(cache_key, result)
        lookup_logger.debug(f"Cached lookup values for: {table_name}")

        return result

    def add_lookup_value(self, table_name: str, value: str) -> tuple[bool, str]:
        """Add new value to lookup table"""
        if not self._validate_table_name(table_name):
            return False, "Tên bảng không hợp lệ!"

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

            # Invalidate cache
            self.invalidate_cache(table_name)
            return True, "Thêm thành công!"
        except Exception as e:
            return False, str(e)

    def update_lookup_value(self, table_name: str, old_value: str,
                            new_value: str) -> tuple[bool, str]:
        """Update value in lookup table"""
        if not self._validate_table_name(table_name):
            return False, "Tên bảng không hợp lệ!"

        if not new_value or not new_value.strip():
            return False, "Giá trị không được để trống!"

        try:
            db = get_db()
            with db.get_cursor() as cursor:
                cursor.execute(
                    f"UPDATE {table_name} SET name = ? WHERE name = ?",
                    (new_value, old_value)
                )

            # Invalidate cache
            self.invalidate_cache(table_name)
            return True, "Cập nhật thành công!"
        except Exception as e:
            return False, str(e)

    def delete_lookup_value(self, table_name: str, value: str) -> tuple[bool, str]:
        """Delete value from lookup table"""
        if not self._validate_table_name(table_name):
            return False, "Tên bảng không hợp lệ!"

        try:
            db = get_db()
            with db.get_cursor() as cursor:
                cursor.execute(f"DELETE FROM {table_name} WHERE name = ?", (value,))

            # Invalidate cache
            self.invalidate_cache(table_name)
            return True, "Xóa thành công!"
        except Exception as e:
            return False, str(e)
    
    # ========== EQUIPMENT ==========

    def get_all_equipment(self) -> List[Equipment]:
        """Get all equipment (cached)"""
        # Check cache
        if self._equipment_cache and not self._equipment_cache.is_expired():
            return self._equipment_cache.data

        db = get_db()
        rows = db.fetch_all(
            "SELECT factory, control_no, name, spec, r1, r2, r3, r4, r5, remark FROM equipment ORDER BY control_no"
        )
        result = [Equipment.from_db_row(row) for row in rows]

        # Cache result
        self._equipment_cache = CacheEntry(result, self.CACHE_TTL)
        lookup_logger.debug("Cached all equipment data")

        return result

    def get_equipment_by_id(self, control_no: str) -> Optional[Equipment]:
        """Get equipment by control number (cached)"""
        if not control_no:
            return None

        # Check individual cache
        cache_key = f"equip_{control_no}"
        if cache_key in self._equipment_map_cache:
            entry = self._equipment_map_cache[cache_key]
            if not entry.is_expired():
                return entry.data

        db = get_db()
        row = db.fetch_one(
            "SELECT factory, control_no, name, spec, r1, r2, r3, r4, r5, remark FROM equipment WHERE control_no = ?",
            (control_no,)
        )

        result = Equipment.from_db_row(row) if row else None

        # Cache result
        self._equipment_map_cache[cache_key] = CacheEntry(result, self.CACHE_TTL)

        return result

    def get_equipment_list(self) -> List[str]:
        """Get list of equipment control numbers (cached)"""
        # Check cache
        cached = self._get_from_cache("equipment_list")
        if cached is not None:
            return cached

        db = get_db()
        rows = db.fetch_all("SELECT control_no FROM equipment ORDER BY control_no")
        result = [row[0] for row in rows if row[0]]

        # Cache result
        self._set_cache("equipment_list", result)

        return result

    def get_equipment_name(self, control_no: str) -> str:
        """Get equipment name by control number (uses cached equipment)"""
        equip = self.get_equipment_by_id(control_no)
        return equip.name if equip else ""

    def get_equipment_recipes(self, control_no: str) -> List[str]:
        """Get recipes for equipment (uses cached equipment)"""
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

            # Invalidate cache
            self.invalidate_equipment_cache()
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

            # Invalidate cache
            self.invalidate_equipment_cache()
            return True, "Cập nhật thành công!"
        except Exception as e:
            return False, str(e)

    def delete_equipment(self, control_no: str) -> tuple[bool, str]:
        """Delete equipment"""
        try:
            db = get_db()
            with db.get_cursor() as cursor:
                cursor.execute("DELETE FROM equipment WHERE control_no = ?", (control_no,))

            # Invalidate cache
            self.invalidate_equipment_cache()
            return True, "Xóa thành công!"
        except Exception as e:
            return False, str(e)

    def preload_cache(self):
        """Preload all lookup caches for better performance"""
        lookup_logger.info("Preloading lookup caches...")

        # Preload lookup tables
        for table in self.VALID_TABLES:
            self.get_lookup_values(table)

        # Preload equipment
        self.get_equipment_list()

        lookup_logger.info("Lookup caches preloaded successfully")


# Singleton instance
_lookup_service: Optional[LookupService] = None

def get_lookup_service() -> LookupService:
    """Get lookup service instance"""
    global _lookup_service
    if _lookup_service is None:
        _lookup_service = LookupService()
    return _lookup_service

