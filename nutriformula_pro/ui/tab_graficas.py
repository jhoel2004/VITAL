from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.figure import Figure

from app.calculator import calcular_composicion, normalizar_para_radar


PALETA = [
    '#2D7D46', '#5CB85C', '#F0AD4E', '#D9534F', '#5BC0DE',
    '#9B59B6', '#E67E22', '#1ABC9C', '#3498DB', '#E74C3C'
]

NUTRIENTES_RADAR = [
    'proteina', 'em_kcal', 'fibra', 'grasa',
    'calcio', 'fosforo', 'lisina', 'metionina'
]

NOMBRES_NUTRIENTES_ESP = {
    'proteina': 'Proteína',
    'em_kcal': 'EM Kcal',
    'fibra': 'Fibra',
    'grasa': 'Grasa',
    'calcio': 'Calcio',
    'fosforo': 'Fósforo',
    'lisina': 'Lisina',
    'metionina': 'Metionina',
}


class TabGraficas(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.parent_window = parent
        self.totales_actuales = {}
        self.total_kg_actual = 0
        self.ingredientes_actuales = []
        self.referencia_seleccionada = None
        self.totales_referencia = {}

        layout = QVBoxLayout(self)

        controles = QHBoxLayout()
        controles.addWidget(QLabel('Tipo de gráfica:'))

        self.selector_grafica = QComboBox()
        self.selector_grafica.addItems([
            'Radar Nutricional',
            'Barras: Calculado vs Referencia',
            'Torta: % Ingredientes',
            'Costos por Ingrediente'
        ])
        self.selector_grafica.currentIndexChanged.connect(self._actualizar_grafica)
        controles.addWidget(self.selector_grafica)

        self.selector_referencia = QComboBox()
        self.selector_referencia.addItem('-- Sin referencia --', None)
        self.selector_referencia.currentIndexChanged.connect(self._cambiar_referencia)
        controles.addWidget(self.selector_referencia)

        btn_exportar = QPushButton('📄 Exportar PNG/PDF')
        btn_exportar.clicked.connect(self._exportar_grafica)
        controles.addWidget(btn_exportar)

        controles.addStretch()
        layout.addLayout(controles)

        self.canvas_container = QWidget()
        self.canvas_layout = QVBoxLayout(self.canvas_container)
        self.canvas_layout.setContentsMargins(0, 0, 0, 0)

        self.fig = Figure(facecolor='#1E1E2E')
        self.canvas = FigureCanvas(self.fig)
        self.canvas_layout.addWidget(self.canvas)

        toolbar = NavigationToolbar(self.canvas, self)
        toolbar.setStyleSheet("""
            QToolBar { background: #1E1E2E; border: none; }
            QToolButton { color: #E0E0F0; background: #2A2A4A; border: none; border-radius: 3px; padding: 4px; }
            QToolButton:hover { background: #3A3A6A; }
        """)
        self.canvas_layout.addWidget(toolbar)

        layout.addWidget(self.canvas_container)

        self.tabla_diferencias = QTableWidget()
        self.tabla_diferencias.setColumnCount(4)
        self.tabla_diferencias.setHorizontalHeaderLabels(
            ['Nutriente', 'Actual(1kg)', 'Referencia(1kg)', 'Ratio']
        )
        self.tabla_diferencias.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabla_diferencias.setVisible(False)
        layout.addWidget(self.tabla_diferencias)

        self._cargar_referencias()
        self._actualizar_grafica()

    def actualizar_datos(self, totales, total_kg, ingredientes):
        self.totales_actuales = totales
        self.total_kg_actual = total_kg
        self.ingredientes_actuales = ingredientes
        self._actualizar_grafica()

    def _cargar_referencias(self):
        self.selector_referencia.clear()
        self.selector_referencia.addItem('-- Sin referencia --', None)
        formulaciones = self.db.get_formulaciones()
        for f in formulaciones:
            self.selector_referencia.addItem(f['nombre'], f['id'])

    def _cambiar_referencia(self):
        form_id = self.selector_referencia.currentData()
        if form_id:
            form = self.db.get_formulacion(form_id)
            if form:
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
                totales, _ = calcular_composicion(
                    ingredientes_lista, form['total_kg']
                )
                self.totales_referencia = normalizar_para_radar(
                    totales, form['total_kg']
                )
                self.referencia_seleccionada = form['nombre']
            else:
                self.totales_referencia = {}
                self.referencia_seleccionada = None
        else:
            self.totales_referencia = {}
            self.referencia_seleccionada = None

        self._actualizar_grafica()

    def _actualizar_grafica(self):
        tipo = self.selector_grafica.currentIndex()

        self.fig.clear()
        self.fig.set_facecolor('#1E1E2E')

        if tipo == 0:
            self._dibujar_radar()
        elif tipo == 1:
            self._dibujar_barras()
        elif tipo == 2:
            self._dibujar_torta()
        elif tipo == 3:
            self._dibujar_costos()

        self.canvas.draw()

    def _dibujar_radar(self):
        ax = self.fig.add_subplot(111, projection='polar')
        ax.set_facecolor('#1E1E2E')

        num_vars = len(NUTRIENTES_RADAR)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]

        for spine in ax.spines.values():
            spine.set_color('#2A2A4A')
        ax.tick_params(colors='#E0E0F0', labelsize=9)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(
            [NOMBRES_NUTRIENTES_ESP[n] for n in NUTRIENTES_RADAR],
            color='#E0E0F0', fontsize=9
        )
        ax.yaxis.grid(True, color='#2A2A4A')
        ax.set_ylim(0, 1.5)
        ax.set_yticks([0.5, 1.0, 1.5])
        ax.set_yticklabels(['0.5', '1.0', '1.5'], color='#8080B0', fontsize=8)

        totales_norm = normalizar_para_radar(
            self.totales_actuales, self.total_kg_actual
        )

        if self.totales_referencia:
            ref_vals = [
                self.totales_referencia.get(n, 0) for n in NUTRIENTES_RADAR
            ]
            ref_vals_norm = [
                ref_vals[i] / max(ref_vals[i], 0.0001)
                if ref_vals[i] > 0 else 0
                for i in range(num_vars)
            ]
            ref_vals_norm += ref_vals_norm[:1]
            ref_angles = angles[:]
            ax.plot(ref_angles, ref_vals_norm,
                    color='#D9534F', linestyle='--', linewidth=1.5, alpha=0.7)
            ax.fill(ref_angles, ref_vals_norm,
                    color='#D9534F', alpha=0.15)

            act_vals = []
            for i, n in enumerate(NUTRIENTES_RADAR):
                act = totales_norm.get(n, 0)
                ref = self.totales_referencia.get(n, 0)
                if ref > 0:
                    act_vals.append(act / ref)
                else:
                    act_vals.append(1.0 if act > 0 else 0)
            act_vals += act_vals[:1]

            self._pintar_radar_datos(ax, act_vals, angles)
            self._mostrar_tabla_diferencias(totales_norm)
        else:
            vals = [1.0] * num_vars
            vals += vals[:1]
            ax.plot(angles, vals, color='#5CB85C', linewidth=2)
            ax.fill(angles, vals, color='#5CB85C', alpha=0.15)
            ax.set_title(
                'Perfil base — selecciona referencia para comparar',
                color='#E0E0F0', fontsize=11, pad=15
            )
            self.tabla_diferencias.setVisible(False)

    def _pintar_radar_datos(self, ax, valores, angles):
        ax.plot(angles, valores, color='#5BC0DE', linewidth=2, solid_capstyle='round')
        ax.fill(angles, valores, color='#5BC0DE', alpha=0.15)

        for i, val in enumerate(valores[:-1]):
            color = '#5CB85C' if val >= 0.95 else (
                '#F0AD4E' if val >= 0.80 else '#D9534F'
            )
            ax.plot(angles[i], valores[i], 'o', color=color, markersize=8)

        ax.set_title(
            f'Radar Nutricional vs "{self.referencia_seleccionada}"',
            color='#E0E0F0', fontsize=11, pad=15
        )

        ax.annotate(
            '1.0', xy=(0, 1.0), xytext=(10, 0),
            textcoords='offset points', color='#5CB85C', fontsize=8
        )

    def _mostrar_tabla_diferencias(self, totales_norm):
        self.tabla_diferencias.setVisible(True)
        self.tabla_diferencias.setRowCount(len(NUTRIENTES_RADAR))

        for i, nut in enumerate(NUTRIENTES_RADAR):
            actual = totales_norm.get(nut, 0)
            referencia = self.totales_referencia.get(nut, 0)
            ratio = actual / referencia if referencia > 0 else (1.0 if actual > 0 else 0)

            self.tabla_diferencias.setItem(
                i, 0, QTableWidgetItem(NOMBRES_NUTRIENTES_ESP[nut])
            )
            self.tabla_diferencias.setItem(
                i, 1, QTableWidgetItem(f"{actual:.4f}")
            )
            self.tabla_diferencias.setItem(
                i, 2, QTableWidgetItem(f"{referencia:.4f}")
            )

            item_ratio = QTableWidgetItem(f"{ratio:.4f}")
            if ratio >= 0.95:
                item_ratio.setForeground(QColor('#5CB85C'))
            elif ratio >= 0.80:
                item_ratio.setForeground(QColor('#F0AD4E'))
            else:
                item_ratio.setForeground(QColor('#D9534F'))
            self.tabla_diferencias.setItem(i, 3, item_ratio)

    def _dibujar_barras(self):
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('#1E1E2E')

        nutrientes = NUTRIENTES_RADAR
        x = np.arange(len(nutrientes))
        width = 0.35

        totales_norm = normalizar_para_radar(
            self.totales_actuales, self.total_kg_actual
        )
        vals_actual = [totales_norm.get(n, 0) for n in nutrientes]

        if self.totales_referencia:
            vals_ref = [
                self.totales_referencia.get(n, 0) for n in nutrientes
            ]
            ax.bar(x - width/2, vals_actual, width,
                   label='Actual', color='#5BC0DE')
            ax.bar(x + width/2, vals_ref, width,
                   label='Referencia', color='#D9534F')
        else:
            ax.bar(x, vals_actual, width, color='#5CB85C')

        ax.set_xticks(x)
        ax.set_xticklabels(
            [NOMBRES_NUTRIENTES_ESP[n] for n in nutrientes],
            color='#E0E0F0', fontsize=9
        )
        ax.tick_params(colors='#E0E0F0')
        ax.legend(facecolor='#2A2A4A', edgecolor='#3A3A6A',
                  labelcolor='#E0E0F0')

        for spine in ax.spines.values():
            spine.set_color('#2A2A4A')

        ax.set_title(
            'Comparación de Nutrientes',
            color='#E0E0F0', fontsize=12, pad=10
        )
        self.tabla_diferencias.setVisible(False)

    def _dibujar_torta(self):
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('#1E1E2E')

        if not self.ingredientes_actuales:
            ax.text(
                0.5, 0.5, 'Sin datos',
                ha='center', va='center',
                color='#8080B0', fontsize=14,
                transform=ax.transAxes
            )
            self.tabla_diferencias.setVisible(False)
            return

        labels = [
            ing.get('nombre', '') for ing in self.ingredientes_actuales
        ]
        sizes = [
            ing.get('porcentaje', 0) for ing in self.ingredientes_actuales
        ]

        colores = PALETA[:len(labels)]
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colores,
            autopct='%1.1f%%', startangle=90,
            textprops={'color': '#E0E0F0', 'fontsize': 8}
        )
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(8)

        ax.set_title(
            'Distribución de Ingredientes',
            color='#E0E0F0', fontsize=12, pad=10
        )
        self.tabla_diferencias.setVisible(False)

    def _dibujar_costos(self):
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('#1E1E2E')

        if not self.ingredientes_actuales:
            ax.text(
                0.5, 0.5, 'Sin datos',
                ha='center', va='center',
                color='#8080B0', fontsize=14,
                transform=ax.transAxes
            )
            self.tabla_diferencias.setVisible(False)
            return

        costos = []
        nombres = []
        for ing in self.ingredientes_actuales:
            costo = ing.get('tanteo_kg', 0) * ing.get('precio_kg', 0)
            if costo > 0:
                costos.append(costo)
                nombres.append(ing.get('nombre', ''))

        orden = sorted(range(len(costos)), key=lambda i: costos[i], reverse=True)
        costos = [costos[i] for i in orden]
        nombres = [nombres[i] for i in orden]
        colores = [PALETA[i % len(PALETA)] for i in range(len(nombres))]

        y = range(len(nombres))
        ax.barh(y, costos, color=colores)
        ax.set_yticks(list(y))
        ax.set_yticklabels(nombres, color='#E0E0F0', fontsize=9)
        ax.tick_params(colors='#E0E0F0')

        for spine in ax.spines.values():
            spine.set_color('#2A2A4A')

        ax.set_title(
            'Costo por Ingrediente',
            color='#E0E0F0', fontsize=12, pad=10
        )
        ax.set_xlabel('Costo ($)', color='#E0E0F0')
        self.tabla_diferencias.setVisible(False)

    def _exportar_grafica(self):
        archivo, _ = QFileDialog.getSaveFileName(
            self, 'Exportar Gráfica', '', 'PNG Files (*.png)'
        )
        if archivo:
            self.fig.savefig(archivo, dpi=150, facecolor='#1E1E2E')
            QMessageBox.information(
                self, 'Éxito', f'Gráfica exportada:\n{archivo}'
            )
