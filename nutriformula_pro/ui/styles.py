TEMA_OSCURO = """
QMainWindow, QWidget {
    background-color: #1E1E2E;
    color: #E0E0F0;
    font-family: "Segoe UI", "Ubuntu", "DejaVu Sans", sans-serif;
    font-size: 11px;
}
QTabWidget::pane {
    border: 1px solid #2A2A4A;
    background: #1E1E2E;
}
QTabBar::tab {
    background: #16213E;
    color: #6060A0;
    padding: 10px 18px;
    border: none;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: #1E1E2E;
    color: #5CB85C;
    border-bottom: 2px solid #5CB85C;
}
QTabBar::tab:hover { color: #A0A0D0; }

QTableWidget {
    background-color: #1E1E2E;
    alternate-background-color: #252538;
    color: #E0E0F0;
    gridline-color: #2A2A4A;
    border: 1px solid #2A2A4A;
    selection-background-color: #2D7D46;
    selection-color: #FFFFFF;
}
QTableWidget::item { padding: 4px 6px; border: none; }
QTableWidget::item:hover { background-color: #2A2A4A; }
QHeaderView::section {
    background-color: #0F0F1E;
    color: #8080B0;
    padding: 6px 8px;
    border: none;
    border-right: 1px solid #2A2A4A;
    border-bottom: 2px solid #2D7D46;
    font-weight: bold;
    font-size: 10px;
}

QPushButton {
    background-color: #2A2A4A;
    color: #A0A0D0;
    border: none;
    border-radius: 5px;
    padding: 7px 14px;
    font-weight: bold;
}
QPushButton:hover   { background-color: #3A3A6A; color: #E0E0F0; }
QPushButton:pressed { background-color: #2D7D46; color: white; }
QPushButton#btn_primario {
    background-color: #2D7D46;
    color: white;
    font-size: 12px;
    padding: 10px 20px;
}
QPushButton#btn_primario:hover { background-color: #5CB85C; }
QPushButton#btn_peligro {
    background-color: #5A1A1A;
    color: #FF6B6B;
    border: 1px solid #8A2A2A;
}
QPushButton#btn_peligro:hover { background-color: #7A1A1A; }

QComboBox {
    background: #2A2A4A;
    color: #E0E0F0;
    border: 1px solid #3A3A6A;
    border-radius: 4px;
    padding: 5px 10px;
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background: #2A2A4A;
    color: #E0E0F0;
    selection-background-color: #2D7D46;
}

QLineEdit, QDoubleSpinBox, QSpinBox, QPlainTextEdit {
    background: #2A2A4A;
    color: #E0E0F0;
    border: 1px solid #3A3A6A;
    border-radius: 4px;
    padding: 5px 8px;
}
QLineEdit:focus, QDoubleSpinBox:focus {
    border-color: #2D7D46;
}

QDialog {
    background-color: #1E1E2E;
    border: 1px solid #2D7D46;
    border-radius: 8px;
}

QScrollBar:vertical {
    background: #1E1E2E; width: 10px; border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #3A3A6A; border-radius: 5px; min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #2D7D46; }
QScrollBar:horizontal {
    background: #1E1E2E; height: 10px; border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #3A3A6A; border-radius: 5px; min-width: 20px;
}

QStatusBar {
    background: #0F0F1E;
    color: #5060A0;
    font-size: 10px;
    border-top: 1px solid #2A2A4A;
}
QMenuBar {
    background: #0F0F1E;
    color: #8080B0;
}
QMenuBar::item:selected { background: #2A2A4A; color: #E0E0F0; }
QMenu {
    background: #1E1E2E;
    color: #E0E0F0;
    border: 1px solid #2A2A4A;
}
QMenu::item:selected { background: #2D7D46; }
QGroupBox {
    border: 1px solid #2A2A4A;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 8px;
    color: #8080B0;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    color: #5CB85C;
}

QAbstractItemView {
    background-color: #1E1E2E;
    alternate-background-color: #252538;
    color: #E0E0F0;
}
"""


def aplicar_tema(app):
    app.setStyleSheet(TEMA_OSCURO)
    from PyQt6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor('#1E1E2E'))
    palette.setColor(QPalette.ColorRole.WindowText, QColor('#E0E0F0'))
    palette.setColor(QPalette.ColorRole.Base, QColor('#1E1E2E'))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor('#252538'))
    palette.setColor(QPalette.ColorRole.Text, QColor('#E0E0F0'))
    palette.setColor(QPalette.ColorRole.Button, QColor('#2A2A4A'))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor('#E0E0F0'))
    palette.setColor(QPalette.ColorRole.Highlight, QColor('#2D7D46'))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor('#FFFFFF'))
    app.setPalette(palette)
