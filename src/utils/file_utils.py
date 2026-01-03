"""
kRel - File Utilities
"""
import os
import shutil
import csv
from typing import List, Optional


def ensure_directory(path: str) -> bool:
    """Create directory if it doesn't exist"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception:
        return False


def copy_file(src: str, dest_dir: str, new_name: str = None) -> Optional[str]:
    """
    Copy file to destination directory
    Returns: new file path or None on error
    """
    if not os.path.exists(src):
        return None
    
    ensure_directory(dest_dir)
    
    filename = new_name if new_name else os.path.basename(src)
    dest_path = os.path.join(dest_dir, filename)
    
    # Handle duplicate names
    if os.path.exists(dest_path):
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest_dir, f"{base}_{counter}{ext}")
            counter += 1
    
    try:
        shutil.copy2(src, dest_path)
        return dest_path
    except Exception:
        return None


def read_csv(filepath: str, encoding: str = "utf-8") -> List[List[str]]:
    """Read CSV file and return list of rows"""
    if not os.path.exists(filepath):
        return []
    
    rows = []
    try:
        with open(filepath, "r", encoding=encoding, newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(row)
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                for row in reader:
                    rows.append(row)
        except Exception:
            pass
    except Exception:
        pass
    
    return rows


def write_csv(filepath: str, rows: List[List[str]], headers: List[str] = None,
              encoding: str = "utf-8-sig") -> bool:
    """Write data to CSV file"""
    try:
        ensure_directory(os.path.dirname(filepath))
        
        with open(filepath, "w", encoding=encoding, newline="") as f:
            writer = csv.writer(f)
            if headers:
                writer.writerow(headers)
            writer.writerows(rows)
        return True
    except Exception:
        return False


def get_file_extension(filepath: str) -> str:
    """Get file extension (lowercase, without dot)"""
    _, ext = os.path.splitext(filepath)
    return ext.lower().lstrip(".")


def is_image_file(filepath: str) -> bool:
    """Check if file is an image"""
    image_extensions = {"jpg", "jpeg", "png", "gif", "bmp", "webp"}
    return get_file_extension(filepath) in image_extensions


def get_safe_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename


def open_file_location(filepath: str) -> bool:
    """Open file location in explorer"""
    if not os.path.exists(filepath):
        return False
    
    try:
        folder = os.path.dirname(filepath)
        os.startfile(folder)
        return True
    except Exception:
        return False


def open_file(filepath: str) -> bool:
    """Open file with default application"""
    if not os.path.exists(filepath):
        return False
    
    try:
        os.startfile(filepath)
        return True
    except Exception:
        return False

