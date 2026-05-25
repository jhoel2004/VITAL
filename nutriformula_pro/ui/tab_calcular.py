from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
    QPushButton, QLabel, QProgressBar, QStackedWidget,
    QDoubleSpinBox, QMessageBox,
    QInputDialog, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from app.calculator import (
    calcular_composicion, calcular_costo, validar_salud, normalizar_para_radar
)
from app.optimizer import calcular_formulacion_inversa


NUTRIENTES_FORMULAR = [
    'proteina', 'em_kcal', 'fibra', 'grasa',
    'calcio', 'fosforo', 'lisina', 'metionina', 'colina_mgr'
]

NOMBRES_NUTRIENTES = {
    'proteina': 'Proteína%',
    'em_kcal': 'EM Kcal',
    'fibra': 'Fibra%',
    'grasa': 'Grasa%',
    'calcio': 'Calcio%',
    'fosforo': 'Fósforo%',
    'lisina': 'Lisina%',
    'metionina': 'Metionina%',
    'colina_mgr': 'Colina mg/kg',
}

TIPOS_GRAFICA = [
    'Radar Nutricional',
    'Barras: Calculado vs Referencia',
    'Torta: % Ingredientes',
    'Costos por Ingrediente',
]

NUTRIENTES_RADAR = [
    'proteina', 'em_kcal', 'fibra', 'grasa',
    'calcio', 'fosforo', 'lisina', 'metionina'
]

PALETA = [
    '#2D7D46', '#5CB85C', '#F0AD4E', '#D9534F',
    '#5BC0DE', '#E67E22', '#1ABC9C', '#3498DB',
]


class TabCalcular(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.ingredientes_activos = {}
        self.animal_actual_id = None
        self.formulacion_actual_nombre = ''
        self.indice_grafica_actual = 0
        self.totales_referencia = {}
        self.referencia_seleccionada = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        barra_superior = QHBoxLayout()
        barra_superior.addStretch()

        self.btn_formular = QPushButton('✍️ Formular')
        self.btn_formular.setObjectName('btn_primario')
        self.btn_formular.clicked.connect(
            lambda: self.stacked.setCurrentIndex(0)
        )

        self.btn_autoformular = QPushButton('⚡ Autoformular')
        self.btn_autoformular.clicked.connect(
            lambda: self.stacked.setCurrentIndex(1)
        )

        barra_superior.addWidget(self.btn_formular)
        barra_superior.addWidget(self.btn_autoformular)
        layout.addLayout(barra_superior)

        self.stacked = QStackedWidget()

        self.pagina_formular = self._crear_pagina_formular()
        self.pagina_autoformular = self._crear_pagina_autoformular()

        self.stacked.addWidget(self.pagina_formular)
        self.stacked.addWidget(self.pagina_autoformular)

        layout.addWidget(self.stacked)

        self.stacked.currentChanged.connect(self._cambiar_modo)
        self._cambiar_modo(0)

    def _cambiar_modo(self, index):
        if index == 0:
            self.btn_formular.setObjectName('btn_primario')
            self.btn_autoformular.setObjectName('')
        else:
            self.btn_autoformular.setObjectName('btn_primario')
            self.btn_formular.setObjectName('')
        self.btn_formular.setStyle(self.btn_formular.style())
        self.btn_autoformular.setStyle(self.btn_autoformular.style())

    def _crear_pagina_formular(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        panel_izq = self._crear_panel_izquierdo_formular()
        panel_der = self._crear_panel_derecho_formular()

        splitter.addWidget(panel_izq)
        splitter.addWidget(panel_der)
        splitter.setSizes([500, 500])

        self._cargar_ingredientes_formular()

        layout.addWidget(splitter)
        return widget

    def _crear_panel_izquierdo_formular(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.combo_animal_form = QComboBox()
        self.combo_animal_form.currentIndexChanged.connect(
            self._on_animal_changed_formular
        )
        layout.addWidget(self.combo_animal_form)

        self.buscar_ing_form = QLineEdit()
        self.buscar_ing_form.setPlaceholderText('Buscar ingrediente...')
        self.buscar_ing_form.textChanged.connect(self._filtrar_ing_formular)
        layout.addWidget(self.buscar_ing_form)

        self.tabla_ing_form = QTableWidget()
        self.tabla_ing_form.setColumnCount(4)
        self.tabla_ing_form.setHorizontalHeaderLabels(
            ['Ingrediente', 'Cantidad kg', '% Ración', 'Costo']
        )
        self.tabla_ing_form.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabla_ing_form.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tabla_ing_form.setAlternatingRowColors(True)
        self.tabla_ing_form.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.tabla_ing_form)

        self.barra_progreso = QProgressBar()
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        layout.addWidget(self.barra_progreso)

        self.lbl_total_kg = QLabel('Total: 0 kg (0%)')
        layout.addWidget(self.lbl_total_kg)

        self._cargar_animales_formular()

        return widget

    def _crear_panel_derecho_formular(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.tabla_result_form = QTableWidget()
        self.tabla_result_form.setColumnCount(10)
        encabezados = ['Insumo'] + [
            '% Ración', 'Proteína%', 'EM Kcal', 'Fibra%', 'Grasa%',
            'Calcio%', 'Fósforo%', 'Lisina%', 'Metionina%'
        ]
        self.tabla_result_form.setHorizontalHeaderLabels(encabezados)
        self.tabla_result_form.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tabla_result_form.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.tabla_result_form)

        barra_graficas = QHBoxLayout()
        barra_graficas.addWidget(QLabel('Comparativa:'))

        self.btn_graf_prev = QPushButton('<')
        self.btn_graf_prev.setFixedWidth(36)
        self.btn_graf_prev.clicked.connect(self._grafica_anterior)
        barra_graficas.addWidget(self.btn_graf_prev)

        self.lbl_tipo_grafica = QLabel(TIPOS_GRAFICA[0])
        self.lbl_tipo_grafica.setStyleSheet('color: #5BC0DE; font-weight: bold;')
        barra_graficas.addWidget(self.lbl_tipo_grafica, 1)

        self.btn_graf_next = QPushButton('>')
        self.btn_graf_next.setFixedWidth(36)
        self.btn_graf_next.clicked.connect(self._grafica_siguiente)
        barra_graficas.addWidget(self.btn_graf_next)

        self.combo_ref_grafica = QComboBox()
        self.combo_ref_grafica.currentIndexChanged.connect(self._cambiar_referencia_grafica)
        barra_graficas.addWidget(self.combo_ref_grafica)
        layout.addLayout(barra_graficas)

        self.fig = Figure(facecolor='#1E1E2E')
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setMinimumHeight(360)
        layout.addWidget(self.canvas)

        self.tabla_diferencias = QTableWidget()
        self.tabla_diferencias.setColumnCount(4)
        self.tabla_diferencias.setHorizontalHeaderLabels(
            ['Nutriente', 'Actual(1kg)', 'Referencia(1kg)', 'Ratio']
        )
        self.tabla_diferencias.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabla_diferencias.setMaximumHeight(140)
        self.tabla_diferencias.setVisible(False)
        layout.addWidget(self.tabla_diferencias)

        self.lbl_alertas = QLabel('')
        self.lbl_alertas.setWordWrap(True)
        self.lbl_alertas.setStyleSheet('color: #F0AD4E; font-weight: bold;')
        layout.addWidget(self.lbl_alertas)

        btn_guardar = QPushButton('💾 Guardar Formulación')
        btn_guardar.setObjectName('btn_primario')
        btn_guardar.clicked.connect(self._guardar_formulacion)
        layout.addWidget(btn_guardar)

        self._cargar_referencias_grafica()

        return widget

    def _crear_pagina_autoformular(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        panel_izq = self._crear_panel_izquierdo_autoformular()
        panel_der = self._crear_panel_derecho_autoformular()

        splitter.addWidget(panel_izq)
        splitter.addWidget(panel_der)
        splitter.setSizes([500, 500])

        layout.addWidget(splitter)
        return widget

    def _crear_panel_izquierdo_autoformular(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.combo_animal_auto = QComboBox()
        layout.addWidget(self.combo_animal_auto)

        layout.addWidget(QLabel('Nombre de la etapa:'))
        self.input_etapa = QLineEdit()
        layout.addWidget(self.input_etapa)

        self.tabla_metas = QTableWidget()
        self.tabla_metas.setColumnCount(3)
        self.tabla_metas.setHorizontalHeaderLabels(
            ['Nutriente', 'Mínimo', 'Máximo']
        )
        self.tabla_metas.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked
        )
        self.tabla_metas.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        nutrientes = [
            ('Proteína%', 'proteina'),
            ('EM Kcal/kg', 'em_kcal'),
            ('Fibra%', 'fibra'),
            ('Grasa%', 'grasa'),
            ('Calcio%', 'calcio'),
            ('Fósforo%', 'fosforo'),
            ('Lisina%', 'lisina'),
            ('Metionina%', 'metionina'),
            ('Colina mg/kg', 'colina_mgr'),
        ]

        self.tabla_metas.setRowCount(len(nutrientes))
        for i, (nombre, key) in enumerate(nutrientes):
            self.tabla_metas.setItem(i, 0, QTableWidgetItem(nombre))
            min_spin = QDoubleSpinBox()
            min_spin.setRange(0, 10000)
            min_spin.setDecimals(2)
            min_spin.setProperty('nutriente_key', key)
            self.tabla_metas.setCellWidget(i, 1, min_spin)

            max_spin = QDoubleSpinBox()
            max_spin.setRange(0, 10000)
            max_spin.setDecimals(2)
            max_spin.setProperty('nutriente_key', key)
            self.tabla_metas.setCellWidget(i, 2, max_spin)

        layout.addWidget(self.tabla_metas)

        layout.addWidget(QLabel('Total de ración a preparar (kg):'))
        self.input_total_kg = QDoubleSpinBox()
        self.input_total_kg.setRange(1, 100000)
        self.input_total_kg.setValue(100)
        self.input_total_kg.setDecimals(2)
        layout.addWidget(self.input_total_kg)

        btn_calcular = QPushButton('⚡ CALCULAR FORMULACIÓN')
        btn_calcular.setObjectName('btn_primario')
        btn_calcular.clicked.connect(self._calcular_autoformulacion)
        layout.addWidget(btn_calcular)

        self._cargar_animales_autoformular()

        return widget

    def _crear_panel_derecho_autoformular(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.tabla_ing_auto = QTableWidget()
        self.tabla_ing_auto.setColumnCount(4)
        self.tabla_ing_auto.setHorizontalHeaderLabels(
            ['Usar', 'Ingrediente', 'Mín%', 'Máx%']
        )
        self.tabla_ing_auto.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.tabla_ing_auto)

        self.lbl_resultado_auto = QLabel('')
        self.lbl_resultado_auto.setStyleSheet(
            'color: #F0AD4E; font-weight: bold; font-size: 12px;'
        )
        self.lbl_resultado_auto.setWordWrap(True)
        layout.addWidget(self.lbl_resultado_auto)

        self.tabla_result_auto = QTableWidget()
        self.tabla_result_auto.setColumnCount(4)
        self.tabla_result_auto.setHorizontalHeaderLabels(
            ['Ingrediente', '% en Ración', 'kg necesarios', 'Costo($)']
        )
        self.tabla_result_auto.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tabla_result_auto.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabla_result_auto.setVisible(False)
        layout.addWidget(self.tabla_result_auto)

        self.lbl_costos_auto = QLabel('')
        self.lbl_costos_auto.setStyleSheet(
            'color: #5CB85C; font-weight: bold;'
        )
        layout.addWidget(self.lbl_costos_auto)

        btn_layout = QHBoxLayout()

        self.btn_guardar_auto = QPushButton('💾 Guardar Formulación')
        self.btn_guardar_auto.setObjectName('btn_primario')
        self.btn_guardar_auto.clicked.connect(self._guardar_autoformulacion)
        self.btn_guardar_auto.setVisible(False)
        btn_layout.addWidget(self.btn_guardar_auto)

        self.btn_enviar_formular = QPushButton('→ Enviar a Formular')
        self.btn_enviar_formular.clicked.connect(self._enviar_a_formular)
        self.btn_enviar_formular.setVisible(False)
        btn_layout.addWidget(self.btn_enviar_formular)

        layout.addLayout(btn_layout)

        self._cargar_ingredientes_autoformular()

        return widget

    def _cargar_animales_formular(self):
        self.combo_animal_form.clear()
        self.combo_animal_form.addItem('-- Sin animal --', 0)
        animales = self.db.get_animales()
        for a in animales:
            self.combo_animal_form.addItem(a['nombre'], a['id'])

    def _cargar_animales_autoformular(self):
        self.combo_animal_auto.clear()
        self.combo_animal_auto.addItem('-- Sin animal --', 0)
        animales = self.db.get_animales()
        for a in animales:
            self.combo_animal_auto.addItem(a['nombre'], a['id'])

    def _cargar_ingredientes_formular(self):
        insumos = self.db.get_insumos()
        self.todos_insumos = insumos
        self._filtrar_ing_formular()

    def _cargar_ingredientes_autoformular(self):
        insumos = self.db.get_insumos()
        self.todos_insumos_auto = insumos
        self.tabla_ing_auto.setRowCount(len(insumos))
        for i, ing in enumerate(insumos):
            check = QTableWidgetItem()
            check.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable |
                Qt.ItemFlag.ItemIsEnabled
            )
            check.setCheckState(Qt.CheckState.Checked)
            self.tabla_ing_auto.setItem(i, 0, check)
            self.tabla_ing_auto.setItem(
                i, 1, QTableWidgetItem(ing['nombre'])
            )

            min_spin = QDoubleSpinBox()
            min_spin.setRange(0, 100)
            min_spin.setDecimals(2)
            min_spin.setValue(0)
            self.tabla_ing_auto.setCellWidget(i, 2, min_spin)

            max_spin = QDoubleSpinBox()
            max_spin.setRange(0, 100)
            max_spin.setDecimals(2)
            max_spin.setValue(100)
            self.tabla_ing_auto.setCellWidget(i, 3, max_spin)

    def _filtrar_ing_formular(self):
        texto = self.buscar_ing_form.text().lower()
        self.tabla_ing_form.setRowCount(0)

        for ing in self.todos_insumos:
            if texto and texto not in ing['nombre'].lower():
                continue

            fila = self.tabla_ing_form.rowCount()
            self.tabla_ing_form.insertRow(fila)

            cantidad = self.ingredientes_activos.get(ing['id'], {}).get(
                'tanteo_kg', 0
            )
            total_kg = self._get_total_kg()
            porcentaje = (cantidad / total_kg * 100) if total_kg > 0 else 0
            costo = cantidad * ing.get('precio_kg', 0)

            self.tabla_ing_form.setItem(
                fila, 0, QTableWidgetItem(ing['nombre'])
            )

            spin_cantidad = QDoubleSpinBox()
            spin_cantidad.setRange(0, 100000)
            spin_cantidad.setDecimals(4)
            spin_cantidad.setSingleStep(1.0)
            spin_cantidad.setValue(cantidad)
            spin_cantidad.setAccelerated(True)
            spin_cantidad.setKeyboardTracking(True)
            spin_cantidad.setProperty('insumo_id', ing['id'])
            spin_cantidad.valueChanged.connect(self._on_cantidad_changed)
            self.tabla_ing_form.setCellWidget(fila, 1, spin_cantidad)

            self.tabla_ing_form.setItem(
                fila, 2, QTableWidgetItem(f"{porcentaje:.2f}%")
            )
            self.tabla_ing_form.setItem(
                fila, 3, QTableWidgetItem(f"${costo:.4f}")
            )

            if cantidad > 0:
                for col in range(4):
                    item = self.tabla_ing_form.item(fila, col)
                    if item:
                        item.setBackground(QColor('#1A2A3A'))
                        item.setForeground(QColor('#90EE90'))
            else:
                for col in range(4):
                    item = self.tabla_ing_form.item(fila, col)
                    if item:
                        item.setForeground(QColor('#505070'))

        self._actualizar_totales_formular()

    def _refrescar_metricas_tabla_formular(self):
        total_kg = self._get_total_kg()
        for fila in range(self.tabla_ing_form.rowCount()):
            item_nombre = self.tabla_ing_form.item(fila, 0)
            spin_cantidad = self.tabla_ing_form.cellWidget(fila, 1)
            if not item_nombre or not spin_cantidad:
                continue

            insumo_id = spin_cantidad.property('insumo_id')
            cantidad = spin_cantidad.value()
            porcentaje = (cantidad / total_kg * 100) if total_kg > 0 else 0

            precio_kg = 0
            for ing in self.todos_insumos:
                if ing['id'] == insumo_id:
                    precio_kg = ing.get('precio_kg', 0)
                    break
            costo = cantidad * precio_kg

            self.tabla_ing_form.setItem(fila, 2, QTableWidgetItem(f"{porcentaje:.2f}%"))
            self.tabla_ing_form.setItem(fila, 3, QTableWidgetItem(f"${costo:.4f}"))

            color_fg = QColor('#90EE90') if cantidad > 0 else QColor('#505070')
            color_bg = QColor('#1A2A3A') if cantidad > 0 else None
            for col in (0, 2, 3):
                item = self.tabla_ing_form.item(fila, col)
                if not item:
                    continue
                item.setForeground(color_fg)
                if color_bg:
                    item.setBackground(color_bg)
                else:
                    item.setBackground(QColor('#1E1E2E'))

    def _on_cantidad_changed(self, nueva_cantidad):
        spin = self.sender()
        if not spin:
            return

        insumo_id = spin.property('insumo_id')
        if not insumo_id:
            return

        if nueva_cantidad <= 0:
            self.ingredientes_activos.pop(insumo_id, None)
        else:
            insumo = self.db.get_insumo_by_id(insumo_id)
            if not insumo:
                return
            self.ingredientes_activos[insumo_id] = {
                'insumo_id': insumo_id,
                'nombre': insumo['nombre'],
                'tanteo_kg': nueva_cantidad,
                'precio_kg': insumo['precio_kg'],
                'proteina': insumo['proteina'],
                'em_kcal': insumo['em_kcal'],
                'fibra': insumo['fibra'],
                'grasa': insumo['grasa'],
                'calcio': insumo['calcio'],
                'fosforo': insumo['fosforo'],
                'lisina': insumo['lisina'],
                'metionina': insumo['metionina'],
                'colina_mgr': insumo['colina_mgr'],
            }

        self._refrescar_metricas_tabla_formular()
        self._actualizar_totales_formular()

    def _get_total_kg(self):
        return sum(
            ing['tanteo_kg']
            for ing in self.ingredientes_activos.values()
        )

    def _actualizar_totales_formular(self):
        total_kg = self._get_total_kg()
        self.lbl_total_kg.setText(f"Total: {total_kg:.4f} kg (100%)")
        self.barra_progreso.setValue(100)

        self._actualizar_resultados_formular()

    def _actualizar_resultados_formular(self):
        ingredientes_lista = list(self.ingredientes_activos.values())
        total_kg = self._get_total_kg()

        if total_kg <= 0:
            self.tabla_result_form.setRowCount(0)
            self.lbl_alertas.setText('')
            self.fig.clear()
            self.canvas.draw()
            self.tabla_diferencias.setVisible(False)
            return

        totales, ingredientes_calc = calcular_composicion(
            ingredientes_lista, total_kg
        )
        costo_kg, costo_ton = calcular_costo(ingredientes_lista, total_kg)
        alertas = validar_salud(totales, ingredientes_lista, total_kg)

        self.tabla_result_form.setRowCount(len(ingredientes_calc) + 1)

        for i, ing in enumerate(ingredientes_calc):
            self.tabla_result_form.setItem(
                i, 0, QTableWidgetItem(ing.get('nombre', ''))
            )
            self.tabla_result_form.setItem(
                i, 1, QTableWidgetItem(f"{ing['porcentaje']:.2f}")
            )
            self.tabla_result_form.setItem(
                i, 2,
                QTableWidgetItem(f"{ing.get('proteina_aportada', 0):.4f}")
            )
            self.tabla_result_form.setItem(
                i, 3,
                QTableWidgetItem(f"{ing.get('em_aportada', 0):.2f}")
            )
            self.tabla_result_form.setItem(
                i, 4,
                QTableWidgetItem(f"{ing.get('fibra_aportada', 0):.4f}")
            )
            self.tabla_result_form.setItem(
                i, 5,
                QTableWidgetItem(f"{ing.get('grasa_aportada', 0):.4f}")
            )
            self.tabla_result_form.setItem(
                i, 6,
                QTableWidgetItem(f"{ing.get('calcio_aportado', 0):.4f}")
            )
            self.tabla_result_form.setItem(
                i, 7,
                QTableWidgetItem(f"{ing.get('fosforo_aportado', 0):.4f}")
            )
            self.tabla_result_form.setItem(
                i, 8,
                QTableWidgetItem(f"{ing.get('lisina_aportada', 0):.4f}")
            )
            self.tabla_result_form.setItem(
                i, 9,
                QTableWidgetItem(f"{ing.get('metionina_aportada', 0):.4f}")
            )

        fila_total = len(ingredientes_calc)
        for col in range(10):
            item = QTableWidgetItem()
            item.setBackground(QColor('#1B4F2E'))
            item.setForeground(QColor('#FFFFFF'))
            self.tabla_result_form.setItem(fila_total, col, item)

        self.tabla_result_form.setItem(
            fila_total, 0, QTableWidgetItem('TOTALES')
        )
        self.tabla_result_form.setItem(
            fila_total, 1, QTableWidgetItem('100.00')
        )
        self.tabla_result_form.setItem(
            fila_total, 2,
            QTableWidgetItem(f"{totales['proteina']:.4f}")
        )
        self.tabla_result_form.setItem(
            fila_total, 3,
            QTableWidgetItem(f"{totales['em_kcal']:.2f}")
        )
        self.tabla_result_form.setItem(
            fila_total, 4,
            QTableWidgetItem(f"{totales['fibra']:.4f}")
        )
        self.tabla_result_form.setItem(
            fila_total, 5,
            QTableWidgetItem(f"{totales['grasa']:.4f}")
        )
        self.tabla_result_form.setItem(
            fila_total, 6,
            QTableWidgetItem(f"{totales['calcio']:.4f}")
        )
        self.tabla_result_form.setItem(
            fila_total, 7,
            QTableWidgetItem(f"{totales['fosforo']:.4f}")
        )
        self.tabla_result_form.setItem(
            fila_total, 8,
            QTableWidgetItem(f"{totales['lisina']:.4f}")
        )
        self.tabla_result_form.setItem(
            fila_total, 9,
            QTableWidgetItem(f"{totales['metionina']:.4f}")
        )

        if alertas:
            self.lbl_alertas.setText('⚠ ' + ' | '.join(alertas))
        else:
            self.lbl_alertas.setText('')

        self._actualizar_grafica_integrada(totales, total_kg, ingredientes_calc)

        self._emitir_actualizacion_statusbar(total_kg, costo_kg)

    def _cargar_referencias_grafica(self):
        self.combo_ref_grafica.clear()
        self.combo_ref_grafica.addItem('-- Sin referencia --', None)
        for form in self.db.get_formulaciones():
            self.combo_ref_grafica.addItem(form['nombre'], form['id'])

    def _cambiar_referencia_grafica(self):
        form_id = self.combo_ref_grafica.currentData()
        if not form_id:
            self.totales_referencia = {}
            self.referencia_seleccionada = None
            self._actualizar_resultados_formular()
            return

        form = self.db.get_formulacion(form_id)
        if not form:
            self.totales_referencia = {}
            self.referencia_seleccionada = None
            self._actualizar_resultados_formular()
            return

        ingredientes = self.db.get_formulacion_ingredientes(form_id)
        ingredientes_lista = []
        for ing in ingredientes:
            insumo = self.db.get_insumo_by_id(ing['insumo_id'])
            if insumo:
                ingredientes_lista.append({
                    'tanteo_kg': ing['tanteo_kg'],
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
        totales_ref, _ = calcular_composicion(ingredientes_lista, form['total_kg'])
        self.totales_referencia = normalizar_para_radar(totales_ref, form['total_kg'])
        self.referencia_seleccionada = form['nombre']
        self._actualizar_resultados_formular()

    def _grafica_anterior(self):
        self.indice_grafica_actual = (self.indice_grafica_actual - 1) % len(TIPOS_GRAFICA)
        self.lbl_tipo_grafica.setText(TIPOS_GRAFICA[self.indice_grafica_actual])
        self._actualizar_resultados_formular()

    def _grafica_siguiente(self):
        self.indice_grafica_actual = (self.indice_grafica_actual + 1) % len(TIPOS_GRAFICA)
        self.lbl_tipo_grafica.setText(TIPOS_GRAFICA[self.indice_grafica_actual])
        self._actualizar_resultados_formular()

    def _actualizar_grafica_integrada(self, totales, total_kg, ingredientes_calc):
        self.fig.clear()
        self.fig.set_facecolor('#1E1E2E')
        tipo = self.indice_grafica_actual

        if tipo == 0:
            self._dibujar_radar(totales, total_kg)
        elif tipo == 1:
            self._dibujar_barras(totales, total_kg)
        elif tipo == 2:
            self._dibujar_torta(ingredientes_calc)
        else:
            self._dibujar_costos(ingredientes_calc)

        self.canvas.draw()

    def _dibujar_radar(self, totales, total_kg):
        ax = self.fig.add_subplot(111, projection='polar')
        ax.set_facecolor('#1E1E2E')
        num_vars = len(NUTRIENTES_RADAR)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([NOMBRES_NUTRIENTES[n] for n in NUTRIENTES_RADAR], color='#E0E0F0', fontsize=8)
        ax.tick_params(colors='#E0E0F0')
        ax.set_ylim(0, 1.5)
        totales_norm = normalizar_para_radar(totales, total_kg)

        if self.totales_referencia:
            ref_vals = [self.totales_referencia.get(n, 0) for n in NUTRIENTES_RADAR]
            ref_vals = [1.0 if v > 0 else 0 for v in ref_vals] + [1.0 if ref_vals[0] > 0 else 0]
            ax.plot(angles, ref_vals, color='#D9534F', linestyle='--', linewidth=1.3)
            act_vals = []
            for n in NUTRIENTES_RADAR:
                act = totales_norm.get(n, 0)
                ref = self.totales_referencia.get(n, 0)
                act_vals.append(act / ref if ref > 0 else 0)
            act_vals += act_vals[:1]
            ax.plot(angles, act_vals, color='#5BC0DE', linewidth=2)
            ax.fill(angles, act_vals, color='#5BC0DE', alpha=0.18)
            self._mostrar_tabla_diferencias(totales_norm)
            ax.set_title(f'Radar vs "{self.referencia_seleccionada}"', color='#E0E0F0', fontsize=10)
        else:
            vals = [1.0] * num_vars
            vals += vals[:1]
            ax.plot(angles, vals, color='#5CB85C', linewidth=2)
            ax.fill(angles, vals, color='#5CB85C', alpha=0.15)
            self.tabla_diferencias.setVisible(False)
            ax.set_title('Selecciona referencia para comparar', color='#E0E0F0', fontsize=10)

    def _mostrar_tabla_diferencias(self, totales_norm):
        self.tabla_diferencias.setVisible(True)
        self.tabla_diferencias.setRowCount(len(NUTRIENTES_RADAR))
        for i, nut in enumerate(NUTRIENTES_RADAR):
            actual = totales_norm.get(nut, 0)
            referencia = self.totales_referencia.get(nut, 0)
            ratio = actual / referencia if referencia > 0 else 0
            self.tabla_diferencias.setItem(i, 0, QTableWidgetItem(NOMBRES_NUTRIENTES[nut]))
            self.tabla_diferencias.setItem(i, 1, QTableWidgetItem(f"{actual:.4f}"))
            self.tabla_diferencias.setItem(i, 2, QTableWidgetItem(f"{referencia:.4f}"))
            item_ratio = QTableWidgetItem(f"{ratio:.4f}")
            if ratio >= 0.95:
                item_ratio.setForeground(QColor('#5CB85C'))
            elif ratio >= 0.80:
                item_ratio.setForeground(QColor('#F0AD4E'))
            else:
                item_ratio.setForeground(QColor('#D9534F'))
            self.tabla_diferencias.setItem(i, 3, item_ratio)

    def _dibujar_barras(self, totales, total_kg):
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('#1E1E2E')
        nutrientes = NUTRIENTES_RADAR
        x = np.arange(len(nutrientes))
        width = 0.35
        totales_norm = normalizar_para_radar(totales, total_kg)
        vals_actual = [totales_norm.get(n, 0) for n in nutrientes]
        if self.totales_referencia:
            vals_ref = [self.totales_referencia.get(n, 0) for n in nutrientes]
            ax.bar(x - width/2, vals_actual, width, label='Actual', color='#5BC0DE')
            ax.bar(x + width/2, vals_ref, width, label='Referencia', color='#D9534F')
            ax.legend(facecolor='#2A2A4A', edgecolor='#3A3A6A', labelcolor='#E0E0F0')
        else:
            ax.bar(x, vals_actual, width, color='#5CB85C')
        ax.set_xticks(x)
        ax.set_xticklabels([NOMBRES_NUTRIENTES[n] for n in nutrientes], color='#E0E0F0', fontsize=8)
        ax.tick_params(colors='#E0E0F0')
        ax.set_title('Comparación de nutrientes', color='#E0E0F0', fontsize=10)
        self.tabla_diferencias.setVisible(False)

    def _dibujar_torta(self, ingredientes_calc):
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('#1E1E2E')
        labels = [ing.get('nombre', '') for ing in ingredientes_calc if ing.get('porcentaje', 0) > 0]
        sizes = [ing.get('porcentaje', 0) for ing in ingredientes_calc if ing.get('porcentaje', 0) > 0]
        if not sizes:
            ax.text(0.5, 0.5, 'Sin datos', color='#8080B0', ha='center', va='center', transform=ax.transAxes)
            self.tabla_diferencias.setVisible(False)
            return
        colores = [PALETA[i % len(PALETA)] for i in range(len(labels))]
        ax.pie(sizes, labels=labels, colors=colores, autopct='%1.1f%%', startangle=90, textprops={'color': '#E0E0F0', 'fontsize': 8})
        ax.set_title('Distribución de ingredientes', color='#E0E0F0', fontsize=10)
        self.tabla_diferencias.setVisible(False)

    def _dibujar_costos(self, ingredientes_calc):
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('#1E1E2E')
        costos = []
        nombres = []
        for ing in ingredientes_calc:
            costo = ing.get('tanteo_kg', 0) * ing.get('precio_kg', 0)
            if costo > 0:
                nombres.append(ing.get('nombre', ''))
                costos.append(costo)
        if not costos:
            ax.text(0.5, 0.5, 'Sin datos', color='#8080B0', ha='center', va='center', transform=ax.transAxes)
            self.tabla_diferencias.setVisible(False)
            return
        y = np.arange(len(nombres))
        colores = [PALETA[i % len(PALETA)] for i in range(len(nombres))]
        ax.barh(y, costos, color=colores)
        ax.set_yticks(y)
        ax.set_yticklabels(nombres, color='#E0E0F0', fontsize=8)
        ax.tick_params(colors='#E0E0F0')
        ax.set_xlabel('Costo ($)', color='#E0E0F0')
        ax.set_title('Costo por ingrediente', color='#E0E0F0', fontsize=10)
        self.tabla_diferencias.setVisible(False)

    def _emitir_actualizacion_statusbar(self, total_kg, costo_kg):
        try:
            parent = self.parent()
            while parent and not hasattr(parent, 'actualizar_statusbar'):
                parent = parent.parent()
            if parent and hasattr(parent, 'actualizar_statusbar'):
                parent.actualizar_statusbar(
                    self._get_animal_nombre(),
                    len(self.ingredientes_activos),
                    total_kg,
                    costo_kg
                )
        except Exception:
            pass

    def _get_animal_nombre(self):
        combo = self.combo_animal_form
        idx = combo.currentIndex()
        if idx >= 0:
            return combo.currentText()
        return ''

    def _guardar_formulacion(self):
        ingredientes_lista = [
            ing for ing in self.ingredientes_activos.values()
            if ing.get('tanteo_kg', 0) > 0
        ]
        if not ingredientes_lista:
            QMessageBox.warning(
                self, 'Atención',
                'No hay ingredientes con cantidad > 0'
            )
            return

        nombre, ok = QInputDialog.getText(
            self, 'Guardar Formulación', 'Nombre de la formulación:'
        )
        if not ok or not nombre.strip():
            return

        instrucciones, ok_instr = QInputDialog.getMultiLineText(
            self,
            'Instrucciones de preparación',
            'Escribe las instrucciones (opcional):'
        )
        if not ok_instr:
            return

        total_kg = self._get_total_kg()
        totales, ingredientes_calc = calcular_composicion(
            ingredientes_lista, total_kg
        )
        costo_kg, costo_ton = calcular_costo(ingredientes_lista, total_kg)

        animal_id = self.combo_animal_form.currentData()
        if animal_id == 0:
            animal_id = None

        datos = {
            'nombre': nombre.strip(),
            'animal_id': animal_id,
            'total_kg': total_kg,
            'proteina_total': totales['proteina'],
            'em_total': totales['em_kcal'],
            'fibra_total': totales['fibra'],
            'grasa_total': totales['grasa'],
            'calcio_total': totales['calcio'],
            'fosforo_total': totales['fosforo'],
            'lisina_total': totales['lisina'],
            'metionina_total': totales['metionina'],
            'colina_total': totales['colina_mgr'],
            'costo_por_kg': costo_kg,
            'costo_por_tonelada': costo_ton,
            'instrucciones': instrucciones,
            'notas': '',
            'tipo': 'manual',
        }

        ingredientes_db = []
        for ing in ingredientes_lista:
            proporcion = ing['tanteo_kg'] / total_kg if total_kg > 0 else 0
            ingredientes_db.append({
                'insumo_id': ing['insumo_id'],
                'tanteo_kg': ing['tanteo_kg'],
                'porcentaje': proporcion * 100,
                'precio_kg': ing['precio_kg'],
                'proteina_aportada': ing['proteina'] * proporcion,
                'em_aportada': ing['em_kcal'] * proporcion,
                'fibra_aportada': ing['fibra'] * proporcion,
                'grasa_aportada': ing['grasa'] * proporcion,
                'calcio_aportado': ing['calcio'] * proporcion,
                'fosforo_aportado': ing['fosforo'] * proporcion,
                'lisina_aportada': ing['lisina'] * proporcion,
                'metionina_aportada': ing['metionina'] * proporcion,
                'colina_aportada': ing['colina_mgr'] * proporcion,
            })

        try:
            self.db.guardar_formulacion(datos, ingredientes_db)
            self.formulacion_actual_nombre = nombre.strip()
            self._cargar_referencias_grafica()
            QMessageBox.information(
                self, 'Éxito',
                f'Formulación "{nombre}" guardada correctamente'
            )
        except Exception as e:
            QMessageBox.critical(
                self, 'Error', f'No se pudo guardar:\n{str(e)}'
            )

    def _on_animal_changed_formular(self):
        pass

    def _calcular_autoformulacion(self):
        ingredientes_seleccionados = []
        for fila in range(self.tabla_ing_auto.rowCount()):
            check = self.tabla_ing_auto.item(fila, 0)
            if check and check.checkState() == Qt.CheckState.Checked:
                nombre_item = self.tabla_ing_auto.item(fila, 1)
                if nombre_item:
                    nombre = nombre_item.text()
                    for ing in self.todos_insumos_auto:
                        if ing['nombre'] == nombre:
                            min_widget = self.tabla_ing_auto.cellWidget(fila, 2)
                            max_widget = self.tabla_ing_auto.cellWidget(fila, 3)
                            min_val = min_widget.value() if min_widget else 0
                            max_val = max_widget.value() if max_widget else 100
                            ingredientes_seleccionados.append({
                                **ing,
                                'limite_min': min_val,
                                'limite_max': max_val,
                            })
                            break

        if not ingredientes_seleccionados:
            QMessageBox.warning(
                self, 'Atención',
                'Selecciona al menos un ingrediente'
            )
            return

        metas_min = {}
        metas_max = {}
        for fila in range(self.tabla_metas.rowCount()):
            min_widget = self.tabla_metas.cellWidget(fila, 1)
            max_widget = self.tabla_metas.cellWidget(fila, 2)
            if min_widget and max_widget:
                key = min_widget.property('nutriente_key')
                min_val = min_widget.value()
                max_val = max_widget.value()
                if min_val > 0:
                    metas_min[key] = min_val
                if max_val > 0:
                    metas_max[key] = max_val

        limites_ing = {}
        for ing in ingredientes_seleccionados:
            limites_ing[ing['nombre'].lower()] = (
                ing['limite_min'], ing['limite_max']
            )

        total_kg = self.input_total_kg.value()

        resultado, problemas = calcular_formulacion_inversa(
            ingredientes_seleccionados, metas_min, metas_max,
            limites_ing, total_kg
        )

        if resultado:
            self._mostrar_resultado_auto(resultado, total_kg)
            self.lbl_resultado_auto.setText('')
        else:
            self.tabla_result_auto.setVisible(False)
            self.btn_guardar_auto.setVisible(False)
            self.btn_enviar_formular.setVisible(False)
            self.lbl_costos_auto.setText('')

            msg = 'No se puede calcular:\n'
            for p in problemas:
                msg += f'  • {p}\n'
            msg += '\n💡 Ajusta las metas nutricionales o agrega más ingredientes.'
            self.lbl_resultado_auto.setText(msg)

    def _mostrar_resultado_auto(self, resultado, total_kg):
        self.tabla_result_auto.setVisible(True)
        self.btn_guardar_auto.setVisible(True)
        self.btn_enviar_formular.setVisible(True)

        self.resultado_auto_actual = resultado
        self.total_kg_auto = total_kg

        self.tabla_result_auto.setRowCount(len(resultado) + 1)

        costo_total = 0
        for i, (insumo_id, datos) in enumerate(resultado.items()):
            ing = self.db.get_insumo_by_id(insumo_id)
            nombre = ing['nombre'] if ing else f'ID {insumo_id}'

            self.tabla_result_auto.setItem(
                i, 0, QTableWidgetItem(nombre)
            )
            self.tabla_result_auto.setItem(
                i, 1, QTableWidgetItem(f"{datos['porcentaje']:.2f}")
            )
            self.tabla_result_auto.setItem(
                i, 2, QTableWidgetItem(f"{datos['kg']:.4f}")
            )
            self.tabla_result_auto.setItem(
                i, 3, QTableWidgetItem(f"${datos['costo']:.4f}")
            )
            costo_total += datos['costo']

        fila_total = len(resultado)
        costo_kg = costo_total / total_kg if total_kg > 0 else 0
        costo_ton = costo_kg * 1000

        for col in range(4):
            item = QTableWidgetItem()
            item.setBackground(QColor('#1B4F2E'))
            item.setForeground(QColor('#FFFFFF'))
            self.tabla_result_auto.setItem(fila_total, col, item)

        self.tabla_result_auto.setItem(
            fila_total, 0, QTableWidgetItem('TOTALES')
        )
        self.tabla_result_auto.setItem(
            fila_total, 1, QTableWidgetItem('100.00')
        )
        self.tabla_result_auto.setItem(
            fila_total, 2, QTableWidgetItem(f"{total_kg:.4f}")
        )
        self.tabla_result_auto.setItem(
            fila_total, 3, QTableWidgetItem(f"${costo_total:.4f}")
        )

        self.lbl_costos_auto.setText(
            f'Costo/kg: ${costo_kg:.4f} | Costo/tonelada: ${costo_ton:.2f}'
        )

        self.resultado_auto_datos = {
            'costo_kg': costo_kg,
            'costo_ton': costo_ton,
            'costo_total': costo_total,
        }

    def _guardar_autoformulacion(self):
        if not hasattr(self, 'resultado_auto_actual'):
            return

        nombre, ok = QInputDialog.getText(
            self, 'Guardar Formulación', 'Nombre de la formulación:'
        )
        if not ok or not nombre.strip():
            return

        total_kg = self.total_kg_auto
        ingredientes_db = []
        ingredientes_lista = []

        for insumo_id, datos in self.resultado_auto_actual.items():
            ing = self.db.get_insumo_by_id(insumo_id)
            if not ing:
                continue

            proporcion = datos['porcentaje'] / 100
            ingredientes_db.append({
                'insumo_id': insumo_id,
                'tanteo_kg': datos['kg'],
                'porcentaje': datos['porcentaje'],
                'precio_kg': ing['precio_kg'],
                'proteina_aportada': ing['proteina'] * proporcion,
                'em_aportada': ing['em_kcal'] * proporcion,
                'fibra_aportada': ing['fibra'] * proporcion,
                'grasa_aportada': ing['grasa'] * proporcion,
                'calcio_aportado': ing['calcio'] * proporcion,
                'fosforo_aportado': ing['fosforo'] * proporcion,
                'lisina_aportada': ing['lisina'] * proporcion,
                'metionina_aportada': ing['metionina'] * proporcion,
                'colina_aportada': ing['colina_mgr'] * proporcion,
            })
            ingredientes_lista.append({
                'insumo_id': insumo_id,
                'nombre': ing['nombre'],
                'tanteo_kg': datos['kg'],
                'precio_kg': ing['precio_kg'],
                'proteina': ing['proteina'],
                'em_kcal': ing['em_kcal'],
                'fibra': ing['fibra'],
                'grasa': ing['grasa'],
                'calcio': ing['calcio'],
                'fosforo': ing['fosforo'],
                'lisina': ing['lisina'],
                'metionina': ing['metionina'],
                'colina_mgr': ing['colina_mgr'],
            })

        totales, _ = calcular_composicion(ingredientes_lista, total_kg)
        costo_kg = self.resultado_auto_datos['costo_kg']
        costo_ton = self.resultado_auto_datos['costo_ton']

        animal_id = self.combo_animal_auto.currentData()
        if animal_id == 0:
            animal_id = None

        datos = {
            'nombre': nombre.strip(),
            'animal_id': animal_id,
            'total_kg': total_kg,
            'proteina_total': totales['proteina'],
            'em_total': totales['em_kcal'],
            'fibra_total': totales['fibra'],
            'grasa_total': totales['grasa'],
            'calcio_total': totales['calcio'],
            'fosforo_total': totales['fosforo'],
            'lisina_total': totales['lisina'],
            'metionina_total': totales['metionina'],
            'colina_total': totales['colina_mgr'],
            'costo_por_kg': costo_kg,
            'costo_por_tonelada': costo_ton,
            'instrucciones': '',
            'notas': '',
            'tipo': 'optimizada',
        }

        try:
            self.db.guardar_formulacion(datos, ingredientes_db)
            self.formulacion_actual_nombre = nombre.strip()
            self._cargar_referencias_grafica()
            QMessageBox.information(
                self, 'Éxito',
                f'Formulación "{nombre}" guardada correctamente'
            )
        except Exception as e:
            QMessageBox.critical(
                self, 'Error', f'No se pudo guardar:\n{str(e)}'
            )

    def _enviar_a_formular(self):
        if not hasattr(self, 'resultado_auto_actual'):
            return

        self.ingredientes_activos = {}
        for insumo_id, datos in self.resultado_auto_actual.items():
            ing = self.db.get_insumo_by_id(insumo_id)
            if ing:
                self.ingredientes_activos[insumo_id] = {
                    'insumo_id': insumo_id,
                    'nombre': ing['nombre'],
                    'tanteo_kg': datos['kg'],
                    'precio_kg': ing['precio_kg'],
                    'proteina': ing['proteina'],
                    'em_kcal': ing['em_kcal'],
                    'fibra': ing['fibra'],
                    'grasa': ing['grasa'],
                    'calcio': ing['calcio'],
                    'fosforo': ing['fosforo'],
                    'lisina': ing['lisina'],
                    'metionina': ing['metionina'],
                    'colina_mgr': ing['colina_mgr'],
                }

        self.stacked.setCurrentIndex(0)
        self._filtrar_ing_formular()

    def cargar_formulacion(self, form_id):
        form = self.db.get_formulacion(form_id)
        if not form:
            return

        ingredientes = self.db.get_formulacion_ingredientes(form_id)

        self.ingredientes_activos = {}
        for ing in ingredientes:
            insumo = self.db.get_insumo_by_id(ing['insumo_id'])
            if insumo:
                self.ingredientes_activos[ing['insumo_id']] = {
                    'insumo_id': ing['insumo_id'],
                    'nombre': insumo['nombre'],
                    'tanteo_kg': ing['tanteo_kg'],
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
                }

        if form['animal_id']:
            for i in range(self.combo_animal_form.count()):
                if self.combo_animal_form.itemData(i) == form['animal_id']:
                    self.combo_animal_form.setCurrentIndex(i)
                    break

        self.formulacion_actual_nombre = form['nombre']
        self.stacked.setCurrentIndex(0)
        self._filtrar_ing_formular()

    def limpiar(self):
        self.ingredientes_activos = {}
        self.formulacion_actual_nombre = ''
        self.combo_animal_form.setCurrentIndex(0)
        self._filtrar_ing_formular()
