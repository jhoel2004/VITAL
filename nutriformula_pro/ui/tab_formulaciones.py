from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTableWidget,
    QTableWidgetItem, QComboBox, QLineEdit, QPushButton,
    QHeaderView, QMessageBox, QInputDialog, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.dialogs import DialogoAnimal


class TabFormulaciones(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.animal_seleccionado_id = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        panel_animales = self._crear_panel_animales()
        panel_formulaciones = self._crear_panel_formulaciones()

        splitter.addWidget(panel_animales)
        splitter.addWidget(panel_formulaciones)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

        self._cargar_animales()
        self._cargar_formulaciones()

    def _crear_panel_animales(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel('Especies / Animales:'))

        self.lista_animales = QListWidget()
        self.lista_animales.itemSelectionChanged.connect(
            self._on_animal_seleccionado
        )
        self.lista_animales.doubleClicked.connect(self._editar_animal)
        layout.addWidget(self.lista_animales)

        btn_layout = QHBoxLayout()

        btn_agregar = QPushButton('+ Agregar')
        btn_agregar.setObjectName('btn_primario')
        btn_agregar.clicked.connect(self._agregar_animal)

        btn_editar = QPushButton('✏ Editar')
        btn_editar.clicked.connect(self._editar_animal)

        btn_eliminar = QPushButton('🗑 Eliminar')
        btn_eliminar.setObjectName('btn_peligro')
        btn_eliminar.clicked.connect(self._eliminar_animal)

        btn_layout.addWidget(btn_agregar)
        btn_layout.addWidget(btn_editar)
        btn_layout.addWidget(btn_eliminar)
        layout.addLayout(btn_layout)

        return widget

    def _crear_panel_formulaciones(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        filtros = QHBoxLayout()

        self.filtro_animal = QComboBox()
        self.filtro_animal.addItem('Todos los animales', None)
        self.filtro_animal.currentIndexChanged.connect(self._cargar_formulaciones)
        filtros.addWidget(QLabel('Animal:'))
        filtros.addWidget(self.filtro_animal)

        self.buscar_form = QLineEdit()
        self.buscar_form.setPlaceholderText('Buscar por nombre...')
        self.buscar_form.textChanged.connect(self._cargar_formulaciones)
        filtros.addWidget(self.buscar_form)

        layout.addLayout(filtros)

        self.tabla_form = QTableWidget()
        self.tabla_form.setColumnCount(6)
        self.tabla_form.setHorizontalHeaderLabels(
            ['Nombre', 'Animal', 'Tipo', 'Fecha', 'Costo/kg', 'Proteína%']
        )
        self.tabla_form.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabla_form.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tabla_form.setAlternatingRowColors(True)
        self.tabla_form.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabla_form.doubleClicked.connect(self._abrir_formulacion)
        layout.addWidget(self.tabla_form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_abrir = QPushButton('📂 Abrir')
        btn_abrir.setObjectName('btn_primario')
        btn_abrir.clicked.connect(self._abrir_formulacion)

        btn_duplicar = QPushButton('⧉ Duplicar')
        btn_duplicar.clicked.connect(self._duplicar_formulacion)

        btn_eliminar = QPushButton('🗑 Eliminar')
        btn_eliminar.setObjectName('btn_peligro')
        btn_eliminar.clicked.connect(self._eliminar_formulacion)

        btn_pdf = QPushButton('📄 Exportar PDF')
        btn_pdf.clicked.connect(self._exportar_pdf)

        btn_layout.addWidget(btn_abrir)
        btn_layout.addWidget(btn_duplicar)
        btn_layout.addWidget(btn_eliminar)
        btn_layout.addWidget(btn_pdf)
        layout.addLayout(btn_layout)

        return widget

    def _cargar_animales(self):
        self.lista_animales.clear()
        self.filtro_animal.clear()
        self.filtro_animal.addItem('Todos los animales', None)

        animales = self.db.get_animales()
        for a in animales:
            item = QListWidgetItem(a['nombre'])
            item.setData(Qt.ItemDataRole.UserRole, a['id'])
            self.lista_animales.addItem(item)
            self.filtro_animal.addItem(a['nombre'], a['id'])

    def _cargar_formulaciones(self):
        animal_id = self.filtro_animal.currentData()
        texto = self.buscar_form.text().strip()

        if texto:
            formulaciones = self.db.buscar_formulaciones(texto, animal_id)
        elif animal_id:
            formulaciones = self.db.get_formulaciones(animal_id)
        else:
            formulaciones = self.db.get_formulaciones()

        self.tabla_form.setRowCount(0)

        for f in formulaciones:
            fila = self.tabla_form.rowCount()
            self.tabla_form.insertRow(fila)

            tipo_display = '⚡ Optimizada' if f['tipo'] == 'optimizada' else '✍️ Manual'

            valores = [
                f['nombre'],
                f.get('animal_nombre', '--'),
                tipo_display,
                f['fecha_modificacion'][:10],
                f"${f['costo_por_kg']:.4f}",
                f"{f['proteina_total']:.2f}%",
            ]

            for col, valor in enumerate(valores):
                item = QTableWidgetItem(valor)
                item.setData(Qt.ItemDataRole.UserRole, f['id'])
                self.tabla_form.setItem(fila, col, item)

    def _on_animal_seleccionado(self):
        seleccion = self.lista_animales.selectedItems()
        if seleccion:
            self.animal_seleccionado_id = seleccion[0].data(
                Qt.ItemDataRole.UserRole
            )
            for i in range(self.filtro_animal.count()):
                if self.filtro_animal.itemData(i) == self.animal_seleccionado_id:
                    self.filtro_animal.setCurrentIndex(i)
                    break
        else:
            self.animal_seleccionado_id = None
            self.filtro_animal.setCurrentIndex(0)
        self._cargar_formulaciones()

    def _get_form_id_seleccionado(self):
        seleccion = self.tabla_form.selectionModel().selectedRows()
        if not seleccion:
            return None
        fila = seleccion[0].row()
        item = self.tabla_form.item(fila, 0)
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _agregar_animal(self):
        dialogo = DialogoAnimal(self.db, parent=self)
        if dialogo.exec() == DialogoAnimal.DialogCode.Accepted:
            self._cargar_animales()

    def _editar_animal(self):
        seleccion = self.lista_animales.selectedItems()
        if not seleccion:
            return
        animal_id = seleccion[0].data(Qt.ItemDataRole.UserRole)
        dialogo = DialogoAnimal(self.db, animal_id, parent=self)
        if dialogo.exec() == DialogoAnimal.DialogCode.Accepted:
            self._cargar_animales()

    def _eliminar_animal(self):
        seleccion = self.lista_animales.selectedItems()
        if not seleccion:
            QMessageBox.warning(self, 'Atención', 'Selecciona una especie')
            return

        animal_id = seleccion[0].data(Qt.ItemDataRole.UserRole)
        resp = QMessageBox.question(
            self, 'Confirmar',
            '¿Eliminar esta especie?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            try:
                self.db.eliminar_animal(animal_id)
                self._cargar_animales()
                self._cargar_formulaciones()
            except Exception as e:
                QMessageBox.critical(self, 'Error', str(e))

    def _abrir_formulacion(self):
        form_id = self._get_form_id_seleccionado()
        if not form_id:
            return

        try:
            parent = self.parent()
            while parent and not hasattr(parent, 'abrir_formulacion'):
                parent = parent.parent()
            if parent and hasattr(parent, 'abrir_formulacion'):
                parent.abrir_formulacion(form_id)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'No se pudo abrir: {str(e)}')

    def _duplicar_formulacion(self):
        form_id = self._get_form_id_seleccionado()
        if not form_id:
            QMessageBox.warning(self, 'Atención', 'Selecciona una formulación')
            return

        try:
            nuevo_id = self.db.duplicar_formulacion(form_id)
            if nuevo_id:
                self._cargar_formulaciones()
                QMessageBox.information(
                    self, 'Éxito', 'Formulación duplicada'
                )
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def _eliminar_formulacion(self):
        form_id = self._get_form_id_seleccionado()
        if not form_id:
            QMessageBox.warning(self, 'Atención', 'Selecciona una formulación')
            return

        resp = QMessageBox.question(
            self, 'Confirmar',
            '¿Eliminar esta formulación?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            try:
                self.db.eliminar_formulacion(form_id)
                self._cargar_formulaciones()
            except Exception as e:
                QMessageBox.critical(self, 'Error', str(e))

    def _exportar_pdf(self):
        form_id = self._get_form_id_seleccionado()
        if not form_id:
            QMessageBox.warning(self, 'Atención', 'Selecciona una formulación')
            return

        try:
            parent = self.parent()
            while parent and not hasattr(parent, 'exportar_pdf_formulacion'):
                parent = parent.parent()
            if parent and hasattr(parent, 'exportar_pdf_formulacion'):
                parent.exportar_pdf_formulacion(form_id)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'No se pudo exportar: {str(e)}')
