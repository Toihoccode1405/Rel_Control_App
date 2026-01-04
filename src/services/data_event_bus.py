"""
kRel - Data Event Bus
Singleton event bus for cross-tab/component communication.
Enables realtime data synchronization between UI components.
"""
from PyQt6.QtCore import QObject, pyqtSignal

from src.services.logger import get_logger

logger = get_logger("event_bus")


class DataEventBus(QObject):
    """
    Singleton event bus for application-wide data change notifications.
    
    Usage:
        from src.services.data_event_bus import get_event_bus
        
        # Emit event (sender)
        get_event_bus().request_created.emit("20260104-001")
        
        # Listen to event (receiver)
        get_event_bus().request_created.connect(self._on_request_created)
    
    Signals:
        request_created(str): Emitted when a new request is created. Passes request_no.
        request_updated(str): Emitted when a request is updated. Passes request_no.
        request_deleted(str): Emitted when a request is deleted. Passes request_no.
        lookup_changed(str): Emitted when lookup data changes. Passes table name 
                             (factory, project, phase, category, status).
        equipment_changed(): Emitted when equipment data changes.
        data_refresh_needed(): General signal to refresh all data.
    """
    
    _instance = None
    
    # ========== Request Events ==========
    # Emitted when request data changes
    request_created = pyqtSignal(str)   # request_no
    request_updated = pyqtSignal(str)   # request_no
    request_deleted = pyqtSignal(str)   # request_no
    
    # ========== Lookup Data Events ==========
    # Emitted when lookup tables change (factory, project, phase, category, status)
    lookup_changed = pyqtSignal(str)    # table_name
    
    # ========== Equipment Events ==========
    # Emitted when equipment data changes
    equipment_changed = pyqtSignal()
    
    # ========== General Events ==========
    # Emitted to request full data refresh
    data_refresh_needed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("DataEventBus initialized")
    
    @classmethod
    def instance(cls) -> 'DataEventBus':
        """Get singleton instance of DataEventBus"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    # ========== Convenience Methods ==========
    # These methods provide logging and can be extended for debugging
    
    def emit_request_created(self, request_no: str):
        """Emit request_created signal with logging"""
        logger.debug(f"Event: request_created({request_no})")
        self.request_created.emit(request_no)
    
    def emit_request_updated(self, request_no: str):
        """Emit request_updated signal with logging"""
        logger.debug(f"Event: request_updated({request_no})")
        self.request_updated.emit(request_no)
    
    def emit_request_deleted(self, request_no: str):
        """Emit request_deleted signal with logging"""
        logger.debug(f"Event: request_deleted({request_no})")
        self.request_deleted.emit(request_no)
    
    def emit_lookup_changed(self, table_name: str):
        """Emit lookup_changed signal with logging"""
        logger.debug(f"Event: lookup_changed({table_name})")
        self.lookup_changed.emit(table_name)
    
    def emit_equipment_changed(self):
        """Emit equipment_changed signal with logging"""
        logger.debug("Event: equipment_changed()")
        self.equipment_changed.emit()
    
    def emit_data_refresh_needed(self):
        """Emit data_refresh_needed signal with logging"""
        logger.debug("Event: data_refresh_needed()")
        self.data_refresh_needed.emit()


# ========== Module-level accessor ==========
_event_bus: DataEventBus = None


def get_event_bus() -> DataEventBus:
    """
    Get singleton DataEventBus instance.
    
    Returns:
        DataEventBus: The singleton event bus instance
    
    Example:
        from src.services.data_event_bus import get_event_bus
        
        # Emit
        get_event_bus().emit_request_created("20260104-001")
        
        # Or direct signal
        get_event_bus().request_created.emit("20260104-001")
        
        # Listen
        get_event_bus().request_created.connect(my_handler)
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = DataEventBus.instance()
    return _event_bus

