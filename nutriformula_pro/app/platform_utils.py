from pathlib import Path

from app.utils import get_data_dir, get_db_path, get_exports_dir, get_system_font, force_utf8


def get_app_data_dir() -> Path:
    return get_data_dir()


def get_font_name() -> str:
    return get_system_font()
