# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path

from app.utils import force_utf8, get_db_path
force_utf8()

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow
from ui.styles import aplicar_tema
from app.database import DatabaseManager


def main():
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            'VITAL.v2'
        )

    app = QApplication(sys.argv)
    app.setApplicationName("VITAL")
    app.setOrganizationName("VITAL")

    aplicar_tema(app)

    db = DatabaseManager(str(get_db_path()))
    db.inicializar()

    ventana = MainWindow(db)
    ventana.setMinimumSize(1400, 850)
    ventana.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
