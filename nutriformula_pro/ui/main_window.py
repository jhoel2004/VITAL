from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar,
    QMenuBar, QMenu, QMessageBox, QFileDialog, QLabel
)
from PyQt6.QtGui import QAction, QKeySequence

from ui.tab_ingredientes import TabIngredientes
from ui.tab_calcular import TabCalcular
from ui.tab_formulaciones import TabFormulaciones
from ui.tab_economia import TabEconomia
from ui.tab_lotes import TabLotes
from ui.dialogs import DialogoConfigEmpresa
from app.platform_utils import get_exports_dir


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.moneda = self.db.get_config('moneda') or '$'

        self.setWindowTitle('VITAL — Formulación Nutricional Animal')
        self.setMinimumSize(1400, 850)

        self._crear_tabs()
        self._crear_menu()
        self._crear_statusbar()
        self._crear_atajos()

    def _crear_menu(self):
        menubar = self.menuBar()

        menu_archivo = menubar.addMenu('Archivo')

        accion_nueva = QAction('Nueva formulación', self, shortcut=QKeySequence('Ctrl+N'))
        accion_nueva.triggered.connect(self._nueva_formulacion)
        menu_archivo.addAction(accion_nueva)

        menu_archivo.addSeparator()

        accion_pdf = QAction('Exportar PDF', self, shortcut=QKeySequence('Ctrl+P'))
        accion_pdf.triggered.connect(self._exportar_pdf)
        menu_archivo.addAction(accion_pdf)

        accion_excel = QAction('Exportar Excel', self, shortcut=QKeySequence('Ctrl+E'))
        accion_excel.triggered.connect(self._exportar_excel)
        menu_archivo.addAction(accion_excel)

        menu_archivo.addSeparator()

        accion_config = QAction('⚙️ Configuración', self)
        accion_config.triggered.connect(self._abrir_config)
        menu_archivo.addAction(accion_config)

        menu_archivo.addSeparator()

        accion_salir = QAction('Salir', self)
        accion_salir.triggered.connect(self.close)
        menu_archivo.addAction(accion_salir)

        menu_ver = menubar.addMenu('Ver')
        for i in range(5):
            tab_text = self.tabs.tabText(i)
            accion = QAction(f'Ir a {tab_text}', self)
            accion.setShortcut(QKeySequence(f'Ctrl+{i+1}'))
            accion.triggered.connect(lambda checked, idx=i: self.tabs.setCurrentIndex(idx))
            menu_ver.addAction(accion)

        menu_ayuda = menubar.addMenu('Ayuda')
        accion_ayuda = QAction('❓ Ayuda', self)
        accion_ayuda.triggered.connect(self._mostrar_ayuda)
        menu_ayuda.addAction(accion_ayuda)

    def _crear_tabs(self):
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.tab_ingredientes = TabIngredientes(self.db, self)
        self.tab_calcular = TabCalcular(self.db, self)
        self.tab_formulaciones = TabFormulaciones(self.db, self)
        self.tab_economia = TabEconomia(self.db, self)
        self.tab_lotes = TabLotes(self.db, self)

        self.tabs.addTab(self.tab_ingredientes, '🧪 Ingredientes')
        self.tabs.addTab(self.tab_calcular, '🧮 Calcular')
        self.tabs.addTab(self.tab_formulaciones, '📁 Formulaciones')
        self.tabs.addTab(self.tab_economia, '📈 Economía')
        self.tabs.addTab(self.tab_lotes, '🏭 Lotes')

        self.setCentralWidget(self.tabs)

    def _crear_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.lbl_animal = QLabel('Animal: --')
        self.lbl_animal.setStyleSheet('color: #5060A0; padding: 0 8px;')

        self.lbl_info = QLabel('Ingredientes activos: 0 | Total: 0 kg (0%)')
        self.lbl_info.setStyleSheet('color: #5060A0; padding: 0 8px;')

        self.lbl_costo = QLabel(f'Costo/kg: {self.moneda}0.0000')
        self.lbl_costo.setStyleSheet('color: #5060A0; padding: 0 8px;')

        self.status_bar.addWidget(self.lbl_animal, 1)
        self.status_bar.addWidget(self.lbl_info, 2)
        self.status_bar.addPermanentWidget(self.lbl_costo)

    def _crear_atajos(self):
        atajo_f5 = QAction(self)
        atajo_f5.setShortcut(QKeySequence('F5'))
        atajo_f5.triggered.connect(self._recalcular)
        self.addAction(atajo_f5)

        atajo_save = QAction(self)
        atajo_save.setShortcut(QKeySequence('Ctrl+S'))
        atajo_save.triggered.connect(self._guardar_actual)
        self.addAction(atajo_save)

    def actualizar_statusbar(self, animal, n_ingredientes, total_kg, costo_kg):
        self.lbl_animal.setText(f'Animal: {animal}')
        self.lbl_info.setText(
            f'Ingredientes activos: {n_ingredientes} | '
            f'Total: {total_kg:.4f} kg (100%)'
        )
        self.lbl_costo.setText(f'Costo/kg: {self.moneda}{costo_kg:.4f}')

    def abrir_formulacion(self, form_id):
        self.tab_calcular.cargar_formulacion(form_id)
        self.tabs.setCurrentIndex(1)

        form = self.db.get_formulacion(form_id)
        if form:
            self.setWindowTitle(f'VITAL — {form["nombre"]}')

            ingredientes = self.db.get_formulacion_ingredientes(form_id)
            ingredientes_lista = []
            for ing in ingredientes:
                insumo = self.db.get_insumo_by_id(ing['insumo_id'])
                if insumo:
                    ingredientes_lista.append({
                        'nombre': insumo['nombre'],
                        'tanteo_kg': ing['tanteo_kg'],
                        'porcentaje': ing['porcentaje'],
                        'precio_kg': ing['precio_kg'],
                        'proteina': insumo['proteina'],
                        'em_kcal': insumo['em_kcal'],
                        'fibra': insumo['fibra'],
                        'grasa': insumo['grasa'],
                        'calcio': insumo['calcio'],
                        'fosforo': insumo['fosforo'],
                        'lisina': insumo['lisina'],
                        'metionina': insumo['metionina'],
                        'colina_mgr': insumo['colina_mgr'],
                    })

    def _nueva_formulacion(self):
        self.tab_calcular.limpiar()
        self.setWindowTitle('VITAL — Formulación Nutricional Animal')
        self.actualizar_statusbar('--', 0, 0, 0)

    def _exportar_pdf(self):
        from app.exporter import exportar_formulacion_pdf
        archivo, _ = QFileDialog.getSaveFileName(
            self, 'Exportar PDF',
            str(get_exports_dir() / 'formulacion.pdf'),
            'PDF Files (*.pdf)'
        )
        if archivo:
            try:
                exportar_formulacion_pdf(self.db, archivo)
                QMessageBox.information(self, 'Éxito', f'PDF exportado:\n{archivo}')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'No se pudo exportar:\n{str(e)}')

    def exportar_pdf_formulacion(self, form_id):
        from app.exporter import exportar_formulacion_especifica_pdf
        archivo, _ = QFileDialog.getSaveFileName(
            self, 'Exportar PDF',
            str(get_exports_dir() / f'formulacion_{form_id}.pdf'),
            'PDF Files (*.pdf)'
        )
        if archivo:
            try:
                exportar_formulacion_especifica_pdf(self.db, form_id, archivo)
                QMessageBox.information(self, 'Éxito', f'PDF exportado:\n{archivo}')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'No se pudo exportar:\n{str(e)}')

    def _exportar_excel(self):
        from app.exporter import exportar_formulacion_excel
        archivo, _ = QFileDialog.getSaveFileName(
            self, 'Exportar Excel',
            str(get_exports_dir() / 'formulacion.xlsx'),
            'Excel Files (*.xlsx)'
        )
        if archivo:
            try:
                exportar_formulacion_excel(self.db, archivo)
                QMessageBox.information(self, 'Éxito', f'Excel exportado:\n{archivo}')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'No se pudo exportar:\n{str(e)}')

    def _abrir_config(self):
        dialogo = DialogoConfigEmpresa(self.db, self)
        if dialogo.exec() == DialogoConfigEmpresa.DialogCode.Accepted:
            self.moneda = self.db.get_config('moneda') or '$'

    def _recalcular(self):
        idx = self.tabs.currentIndex()
        if idx == 1:
            self.tab_calcular._filtrar_ing_formular()

    def _guardar_actual(self):
        idx = self.tabs.currentIndex()
        if idx == 1:
            self.tab_calcular._guardar_formulacion()

    def _mostrar_ayuda(self):
        QMessageBox.information(
            self, 'Ayuda — VITAL v2.0',
            'Atajos de teclado:\n\n'
            'Ctrl+N — Nueva formulación\n'
            'Ctrl+S — Guardar formulación\n'
            'Ctrl+P — Exportar PDF\n'
            'Ctrl+E — Exportar Excel\n'
            'Ctrl+1-5 — Cambiar de tab\n'
            'F5 — Recalcular\n\n'
            'Doble clic en ingrediente → ajustar cantidad\n'
            'Doble clic en formulación → abrir en Calcular'
        )
