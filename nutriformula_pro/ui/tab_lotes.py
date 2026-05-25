from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QComboBox, QPushButton, QLabel,
    QHeaderView, QMessageBox, QFileDialog, QDialog,
    QFormLayout, QDoubleSpinBox, QPlainTextEdit, QDateEdit,
    QLineEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from app.config import COLORS


class DialogoNuevoLote(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle('Crear Nuevo Lote')
        self.setMinimumWidth(450)

        layout = QFormLayout(self)

        self.input_nombre = QLineEdit()
        layout.addRow('Nombre del lote:', self.input_nombre)

        self.combo_formulacion = QComboBox()
        formulaciones = db.get_formulaciones()
        for f in formulaciones:
            self.combo_formulacion.addItem(f['nombre'], f['id'])
        layout.addRow('Formulación base:', self.combo_formulacion)

        self.input_cantidad = QDoubleSpinBox()
        self.input_cantidad.setRange(1, 100000)
        self.input_cantidad.setDecimals(2)
        self.input_cantidad.setValue(100)
        layout.addRow('Cantidad a producir (kg):', self.input_cantidad)

        self.input_fecha = QDateEdit()
        self.input_fecha.setDate(QDate.currentDate())
        self.input_fecha.setCalendarPopup(True)
        layout.addRow('Fecha de producción:', self.input_fecha)

        self.input_notas = QPlainTextEdit()
        self.input_notas.setMaximumHeight(80)
        layout.addRow('Notas:', self.input_notas)

        btn_layout = QHBoxLayout()
        btn_guardar = QPushButton('Crear Lote')
        btn_guardar.setObjectName('btn_primario')
        btn_guardar.clicked.connect(self._guardar)
        btn_cancelar = QPushButton('Cancelar')
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        layout.addRow(btn_layout)

    def _guardar(self):
        if not self.input_nombre.text().strip():
            QMessageBox.warning(self, 'Error', 'El nombre del lote es obligatorio')
            return

        form_id = self.combo_formulacion.currentData()
        cantidad = self.input_cantidad.value()

        form = self.db.get_formulacion(form_id)
        costo_total = form['costo_por_kg'] * cantidad if form else 0

        datos = {
            'formulacion_id': form_id,
            'nombre': self.input_nombre.text().strip(),
            'fecha': self.input_fecha.date().toString('yyyy-MM-dd'),
            'cantidad_kg': cantidad,
            'costo_total': costo_total,
            'notas': self.input_notas.toPlainText(),
            'estado': 'producido',
        }

        try:
            lote_id = self.db.guardar_lote(datos)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))


class TabLotes(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        layout = QVBoxLayout(self)

        filtros = QHBoxLayout()

        self.filtro_animal = QComboBox()
        self.filtro_animal.addItem('Todos', None)
        for a in self.db.get_animales():
            self.filtro_animal.addItem(a['nombre'], a['id'])
        self.filtro_animal.currentIndexChanged.connect(self._cargar_lotes)
        filtros.addWidget(QLabel('Animal:'))
        filtros.addWidget(self.filtro_animal)

        self.filtro_estado = QComboBox()
        self.filtro_estado.addItems(['Todos', 'producido', 'en_uso', 'agotado'])
        self.filtro_estado.currentTextChanged.connect(self._cargar_lotes)
        filtros.addWidget(QLabel('Estado:'))
        filtros.addWidget(self.filtro_estado)

        filtros.addStretch()
        layout.addLayout(filtros)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            '#', 'Nombre del Lote', 'Formulación', 'Animal',
            'Fecha', 'Kg', 'Costo Total', 'Estado'
        ])
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.doubleClicked.connect(self._ver_detalle)
        layout.addWidget(self.tabla)

        botones = QHBoxLayout()
        botones.addStretch()

        btn_nuevo = QPushButton('+ Nuevo Lote')
        btn_nuevo.setObjectName('btn_primario')
        btn_nuevo.clicked.connect(self._crear_lote)

        btn_en_uso = QPushButton('🔄 En Uso')
        btn_en_uso.clicked.connect(lambda: self._cambiar_estado('en_uso'))

        btn_agotado = QPushButton('⬛ Agotado')
        btn_agotado.clicked.connect(lambda: self._cambiar_estado('agotado'))

        btn_eliminar = QPushButton('🗑 Eliminar')
        btn_eliminar.setObjectName('btn_peligro')
        btn_eliminar.clicked.connect(self._eliminar_lote)

        btn_etiqueta = QPushButton('📄 Etiqueta PDF')
        btn_etiqueta.clicked.connect(self._exportar_etiqueta)

        botones.addWidget(btn_nuevo)
        botones.addWidget(btn_en_uso)
        botones.addWidget(btn_agotado)
        botones.addWidget(btn_eliminar)
        botones.addWidget(btn_etiqueta)
        layout.addLayout(botones)

        self._cargar_lotes()

    def _cargar_lotes(self):
        animal_id = self.filtro_animal.currentData()
        estado = self.filtro_estado.currentText()
        if estado == 'Todos':
            estado = None

        lotes = self.db.get_lotes(animal_id=animal_id, estado=estado)

        self.tabla.setRowCount(0)
        for i, lote in enumerate(lotes):
            self.tabla.insertRow(i)
            valores = [
                str(lote['id']),
                lote['nombre'],
                lote.get('formulacion_nombre', '--'),
                lote.get('animal_nombre', '--'),
                lote['fecha'][:10],
                f"{lote['cantidad_kg']:.1f}",
                f"${lote['costo_total']:.2f}",
                lote['estado'],
            ]
            for col, valor in enumerate(valores):
                item = QTableWidgetItem(valor)
                item.setData(Qt.ItemDataRole.UserRole, lote['id'])
                if col == 7:
                    if valor == 'producido':
                        item.setForeground(QColor(COLORS['primary']))
                    elif valor == 'en_uso':
                        item.setForeground(QColor(COLORS['warning']))
                    elif valor == 'agotado':
                        item.setForeground(QColor(COLORS['danger']))
                self.tabla.setItem(i, col, item)

    def _get_lote_id(self):
        seleccion = self.tabla.selectionModel().selectedRows()
        if not seleccion:
            return None
        return self.tabla.item(seleccion[0].row(), 0).data(Qt.ItemDataRole.UserRole)

    def _crear_lote(self):
        dialogo = DialogoNuevoLote(self.db, self)
        if dialogo.exec() == DialogoNuevoLote.DialogCode.Accepted:
            self._cargar_lotes()

    def _cambiar_estado(self, estado):
        lote_id = self._get_lote_id()
        if not lote_id:
            QMessageBox.warning(self, 'Atención', 'Selecciona un lote')
            return
        try:
            self.db.actualizar_estado_lote(lote_id, estado)
            self._cargar_lotes()
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def _eliminar_lote(self):
        lote_id = self._get_lote_id()
        if not lote_id:
            QMessageBox.warning(self, 'Atención', 'Selecciona un lote')
            return
        resp = QMessageBox.question(
            self, 'Confirmar', '¿Eliminar este lote?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            try:
                self.db.eliminar_lote(lote_id)
                self._cargar_lotes()
            except Exception as e:
                QMessageBox.critical(self, 'Error', str(e))

    def _ver_detalle(self, index):
        lote_id = self.tabla.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
        lotes = self.db.get_lotes()
        lote = None
        for l in lotes:
            if l['id'] == lote_id:
                lote = l
                break
        if not lote:
            return

        dialogo = QDialog(self)
        dialogo.setWindowTitle(f'Detalle — {lote["nombre"]}')
        dialogo.setMinimumSize(500, 400)

        layout = QVBoxLayout(dialogo)

        info = QFormLayout()
        info.addRow('Nombre:', QLabel(lote['nombre']))
        info.addRow('Formulación:', QLabel(lote.get('formulacion_nombre', '--')))
        info.addRow('Animal:', QLabel(lote.get('animal_nombre', '--')))
        info.addRow('Fecha:', QLabel(lote['fecha'][:10]))
        info.addRow('Kg producidos:', QLabel(f"{lote['cantidad_kg']:.1f}"))
        info.addRow('Costo total:', QLabel(f"${lote['costo_total']:.2f}"))
        info.addRow('Estado:', QLabel(lote['estado']))
        if lote.get('notas'):
            info.addRow('Notas:', QLabel(lote['notas']))
        layout.addLayout(info)

        if lote['formulacion_id']:
            ingredientes = self.db.get_formulacion_ingredientes(lote['formulacion_id'])
            if ingredientes:
                tabla_ing = QTableWidget()
                tabla_ing.setColumnCount(3)
                tabla_ing.setHorizontalHeaderLabels(['Ingrediente', '%', 'kg en lote'])
                tabla_ing.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                tabla_ing.setRowCount(len(ingredientes))

                for j, ing in enumerate(ingredientes):
                    tabla_ing.setItem(j, 0, QTableWidgetItem(ing['insumo_nombre']))
                    tabla_ing.setItem(j, 1, QTableWidgetItem(f"{ing['porcentaje']:.2f}%"))
                    kg_lote = (ing['porcentaje'] / 100) * lote['cantidad_kg']
                    tabla_ing.setItem(j, 2, QTableWidgetItem(f"{kg_lote:.2f}"))

                layout.addWidget(QLabel('Ingredientes:'))
                layout.addWidget(tabla_ing)

        btn_cerrar = QPushButton('Cerrar')
        btn_cerrar.clicked.connect(dialogo.close)
        layout.addWidget(btn_cerrar)

        dialogo.exec()

    def _exportar_etiqueta(self):
        lote_id = self._get_lote_id()
        if not lote_id:
            QMessageBox.warning(self, 'Atención', 'Selecciona un lote')
            return

        lotes = self.db.get_lotes()
        lote = None
        for l in lotes:
            if l['id'] == lote_id:
                lote = l
                break
        if not lote:
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, 'Exportar Etiqueta', '', 'PDF Files (*.pdf)'
        )
        if not archivo:
            return

        try:
            from app.exporter import exportar_etiqueta_lote_pdf
            exportar_etiqueta_lote_pdf(self.db, lote_id, archivo)
            QMessageBox.information(self, 'Éxito', f'Etiqueta exportada:\n{archivo}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))
