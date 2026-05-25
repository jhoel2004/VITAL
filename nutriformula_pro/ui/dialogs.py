from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QDoubleSpinBox, QPushButton, QFormLayout,
    QLineEdit, QComboBox, QMessageBox, QWidget,
    QFileDialog, QPlainTextEdit
)
from PyQt6.QtCore import Qt


class DialogoCantidadIngrediente(QDialog):
    def __init__(self, nombre_ingrediente, cantidad_actual=0.0, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Dialog
        )
        self.cantidad = cantidad_actual
        self.aceptado = False

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E2E;
                border: 2px solid #2D7D46;
                border-radius: 8px;
            }
            QLabel { color: #E0E0F0; font-size: 14px; }
            QLabel#titulo {
                color: #5CB85C;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton#btn_cancelar {
                background-color: #5A1A1A;
                color: #FF6B6B;
                border: 1px solid #8A2A2A;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton#btn_aceptar {
                background-color: #2D7D46;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton#btn_aceptar:hover { background-color: #5CB85C; }
            QPushButton#btn_cancelar:hover { background-color: #7A1A1A; }
        """)

        titulo = QLabel(nombre_ingrediente)
        titulo.setObjectName('titulo')
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        subtitulo = QLabel('Cantidad en kg:')
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitulo)

        self.spin = QDoubleSpinBox()
        self.spin.setRange(0, 10000)
        self.spin.setDecimals(4)
        self.spin.setValue(cantidad_actual)
        self.spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin.setButtonSymbols(
            QDoubleSpinBox.ButtonSymbols.NoButtons
        )
        self.spin.setStyleSheet("""
            QDoubleSpinBox {
                background: #2A2A4A;
                color: #E0E0F0;
                border: 1px solid #3A3A6A;
                border-radius: 4px;
                padding: 8px;
                font-size: 16px;
            }
            QDoubleSpinBox:focus { border-color: #2D7D46; }
        """)
        layout.addWidget(self.spin)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancelar = QPushButton('Cancelar / Quitar')
        btn_cancelar.setObjectName('btn_cancelar')
        btn_cancelar.clicked.connect(self.reject)

        btn_aceptar = QPushButton('✓ Agregar / Actualizar')
        btn_aceptar.setObjectName('btn_aceptar')
        btn_aceptar.clicked.connect(self.accept)

        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_aceptar)
        layout.addLayout(btn_layout)

        self.spin.setFocus()
        self.spin.selectAll()

    def get_cantidad(self):
        return self.spin.value()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.accept()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def accept(self):
        self.cantidad = self.spin.value()
        self.aceptado = True
        super().accept()


class DialogoIngrediente(QDialog):
    def __init__(self, db, insumo_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.insumo_id = insumo_id
        self.setWindowTitle(
            'Editar Ingrediente' if insumo_id else 'Agregar Ingrediente'
        )
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        self.campos = {}

        self.campos['nombre'] = self._crear_input(tipo='text')
        form.addRow('Nombre:', self.campos['nombre'])

        self.campos['proteina'] = self._crear_input(tipo='float', max_val=100)
        form.addRow('Proteína (%):', self.campos['proteina'])

        self.campos['em_kcal'] = self._crear_input(tipo='float', max_val=10000)
        form.addRow('EM (Kcal/kg):', self.campos['em_kcal'])

        self.campos['fibra'] = self._crear_input(tipo='float', max_val=100)
        form.addRow('Fibra (%):', self.campos['fibra'])

        self.campos['grasa'] = self._crear_input(tipo='float', max_val=100)
        form.addRow('Grasa (%):', self.campos['grasa'])

        self.campos['calcio'] = self._crear_input(tipo='float', max_val=100)
        form.addRow('Calcio (%):', self.campos['calcio'])

        self.campos['fosforo'] = self._crear_input(tipo='float', max_val=100)
        form.addRow('Fósforo (%):', self.campos['fosforo'])

        self.campos['lisina'] = self._crear_input(tipo='float', max_val=100)
        form.addRow('Lisina (%):', self.campos['lisina'])

        self.campos['metionina'] = self._crear_input(tipo='float', max_val=100)
        form.addRow('Metionina (%):', self.campos['metionina'])

        self.campos['colina_mgr'] = self._crear_input(tipo='float', max_val=10000)
        form.addRow('Colina (mg/kg):', self.campos['colina_mgr'])

        self.campos['precio_kg'] = self._crear_input(tipo='float', max_val=10000)
        form.addRow('Precio/kg ($):', self.campos['precio_kg'])

        self.campos['categoria'] = QComboBox()
        self.campos['categoria'].addItems([
            'General', 'Cereales', 'Proteínas', 'Grasas',
            'Subproductos', 'Fibras', 'Aditivos'
        ])
        form.addRow('Categoría:', self.campos['categoria'])

        layout.addLayout(form)

        if insumo_id:
            insumo = db.get_insumo_by_id(insumo_id)
            if insumo:
                self.campos['nombre'].setText(insumo['nombre'])
                self.campos['proteina'].setValue(insumo['proteina'])
                self.campos['em_kcal'].setValue(insumo['em_kcal'])
                self.campos['fibra'].setValue(insumo['fibra'])
                self.campos['grasa'].setValue(insumo['grasa'])
                self.campos['calcio'].setValue(insumo['calcio'])
                self.campos['fosforo'].setValue(insumo['fosforo'])
                self.campos['lisina'].setValue(insumo['lisina'])
                self.campos['metionina'].setValue(insumo['metionina'])
                self.campos['colina_mgr'].setValue(insumo['colina_mgr'])
                self.campos['precio_kg'].setValue(insumo['precio_kg'])
                idx = self.campos['categoria'].findText(insumo['categoria'])
                if idx >= 0:
                    self.campos['categoria'].setCurrentIndex(idx)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_guardar = QPushButton('Guardar')
        btn_guardar.setObjectName('btn_primario')
        btn_guardar.clicked.connect(self._guardar)

        btn_cancelar = QPushButton('Cancelar')
        btn_cancelar.clicked.connect(self.reject)

        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        layout.addLayout(btn_layout)

    def _crear_input(self, tipo='text', max_val=100):
        if tipo == 'float':
            spin = QDoubleSpinBox()
            spin.setRange(0, max_val)
            spin.setDecimals(4)
            spin.setSingleStep(0.1)
            return spin
        else:
            return QLineEdit()

    def _guardar(self):
        nombre = self.campos['nombre'].text().strip()
        if not nombre:
            QMessageBox.warning(self, 'Error', 'El nombre es obligatorio')
            return

        datos = {
            'nombre': nombre,
            'proteina': self.campos['proteina'].value(),
            'em_kcal': self.campos['em_kcal'].value(),
            'fibra': self.campos['fibra'].value(),
            'grasa': self.campos['grasa'].value(),
            'calcio': self.campos['calcio'].value(),
            'fosforo': self.campos['fosforo'].value(),
            'lisina': self.campos['lisina'].value(),
            'metionina': self.campos['metionina'].value(),
            'colina_mgr': self.campos['colina_mgr'].value(),
            'precio_kg': self.campos['precio_kg'].value(),
            'categoria': self.campos['categoria'].currentText(),
        }

        try:
            if self.insumo_id:
                self.db.actualizar_insumo(self.insumo_id, datos)
            else:
                self.db.insertar_insumo(datos)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'No se pudo guardar:\n{str(e)}')


class DialogoAnimal(QDialog):
    def __init__(self, db, animal_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.animal_id = animal_id
        self.setWindowTitle(
            'Editar Especie' if animal_id else 'Agregar Especie'
        )
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel('Nombre de la especie:'))

        self.input_nombre = QLineEdit()
        if animal_id:
            animales = db.get_animales()
            for a in animales:
                if a['id'] == animal_id:
                    self.input_nombre.setText(a['nombre'])
                    break
        layout.addWidget(self.input_nombre)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_guardar = QPushButton('Guardar')
        btn_guardar.setObjectName('btn_primario')
        btn_guardar.clicked.connect(self._guardar)

        btn_cancelar = QPushButton('Cancelar')
        btn_cancelar.clicked.connect(self.reject)

        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        layout.addLayout(btn_layout)

    def _guardar(self):
        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, 'Error', 'El nombre es obligatorio')
            return

        try:
            if self.animal_id:
                self.db.actualizar_animal(self.animal_id, nombre)
            else:
                self.db.insertar_animal(nombre)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'No se pudo guardar:\n{str(e)}')


class DialogoConfigEmpresa(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle('Configuración de Empresa')
        self.setMinimumWidth(400)

        layout = QFormLayout(self)
        layout.setSpacing(10)

        config = db.get_all_config()

        self.input_nombre = QLineEdit(config.get('nombre_empresa', ''))
        layout.addRow('Nombre de empresa/granja:', self.input_nombre)

        self.input_responsable = QLineEdit(config.get('responsable', ''))
        layout.addRow('Responsable técnico:', self.input_responsable)

        self.input_moneda = QComboBox()
        self.input_moneda.addItems(['$', 'Bs.', 'S/.', '€', 'Q', 'L'])
        idx = self.input_moneda.findText(config.get('moneda', '$'))
        if idx >= 0:
            self.input_moneda.setCurrentIndex(idx)
        layout.addRow('Moneda:', self.input_moneda)

        self.input_pie = QLineEdit(config.get('pie_pagina', ''))
        layout.addRow('Pie de página PDF:', self.input_pie)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_guardar = QPushButton('Guardar')
        btn_guardar.setObjectName('btn_primario')
        btn_guardar.clicked.connect(self._guardar)

        btn_cancelar = QPushButton('Cancelar')
        btn_cancelar.clicked.connect(self.reject)

        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        layout.addRow(btn_layout)

    def _guardar(self):
        try:
            self.db.set_config('nombre_empresa', self.input_nombre.text().strip())
            self.db.set_config('responsable', self.input_responsable.text().strip())
            self.db.set_config('moneda', self.input_moneda.currentText())
            self.db.set_config('pie_pagina', self.input_pie.text().strip())
            QMessageBox.information(self, 'Éxito', 'Configuración guardada')
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))
