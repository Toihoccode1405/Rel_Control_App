"""
kRel - Date Utilities
"""
from datetime import datetime, date
from typing import Optional, Union

from PyQt6.QtCore import QDate, QDateTime


# Default formats
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
DATE_FORMAT_DISPLAY = "%d/%m/%Y"


def to_string(dt: Union[datetime, date, QDate, QDateTime, None], 
              fmt: str = DATETIME_FORMAT) -> str:
    """Convert date/datetime to string"""
    if dt is None:
        return ""
    
    if isinstance(dt, QDateTime):
        return dt.toString("yyyy-MM-dd HH:mm")
    
    if isinstance(dt, QDate):
        return dt.toString("yyyy-MM-dd")
    
    if isinstance(dt, datetime):
        return dt.strftime(fmt)
    
    if isinstance(dt, date):
        return dt.strftime(DATE_FORMAT)
    
    return str(dt)


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string to datetime"""
    if not date_str:
        return None
    
    # Try common formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return None


def to_qdate(date_str: str) -> QDate:
    """Convert string to QDate"""
    dt = parse_date(date_str)
    if dt:
        return QDate(dt.year, dt.month, dt.day)
    return QDate.currentDate()


def to_qdatetime(date_str: str) -> QDateTime:
    """Convert string to QDateTime"""
    dt = parse_date(date_str)
    if dt:
        return QDateTime(
            QDate(dt.year, dt.month, dt.day),
            dt.time() if isinstance(dt, datetime) else None
        )
    return QDateTime.currentDateTime()


def today_string(fmt: str = DATE_FORMAT) -> str:
    """Get today's date as string"""
    return datetime.now().strftime(fmt)


def now_string(fmt: str = DATETIME_FORMAT) -> str:
    """Get current datetime as string"""
    return datetime.now().strftime(fmt)


def days_between(start_str: str, end_str: str) -> int:
    """Calculate days between two date strings"""
    start = parse_date(start_str)
    end = parse_date(end_str)
    
    if start and end:
        return (end - start).days
    return 0


def format_for_display(date_str: str) -> str:
    """Format date string for display (DD/MM/YYYY)"""
    dt = parse_date(date_str)
    if dt:
        return dt.strftime(DATE_FORMAT_DISPLAY)
    return date_str

