import sys
import os
from pathlib import Path


def get_base_path() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent


def get_data_dir() -> Path:
    """
    Windows: AppData/Local/VITAL/
    Linux:   ~/.local/share/VITAL/
    """
    if sys.platform == 'win32':
        base = Path(os.environ.get('LOCALAPPDATA', Path.home()))
    else:
        base = Path.home() / '.local' / 'share'
    d = base / 'VITAL'
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_db_path() -> Path:
    return get_data_dir() / 'vital.db'


def get_exports_dir() -> Path:
    d = get_data_dir() / 'Exportaciones'
    d.mkdir(exist_ok=True)
    return d


def get_logo_path() -> Path:
    return get_base_path() / 'logo.png'


def force_utf8():
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        os.environ['PYTHONIOENCODING'] = 'utf-8'


def get_system_font() -> str:
    return 'Segoe UI' if sys.platform == 'win32' else 'Ubuntu'
