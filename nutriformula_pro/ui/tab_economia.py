from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QComboBox, QPushButton, QLabel,
    QHeaderView, QGroupBox, QDoubleSpinBox, QGridLayout,
    QFileDialog, QMessageBox, QInputDialog, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from app.config import COLORS


class TabEconomia(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.moneda = self.db.get_config('moneda') or '$'

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        self._crear_cards_resumen(layout)

        fila_filtros = QHBoxLayout()
        fila_filtros.addWidget(QLabel('Animal:'))
        self.selector_animal = QComboBox()
        self.selector_animal.addItem('Todos los animales', None)
        animales = self.db.get_animales()
        for a in animales:
            self.selector_animal.addItem(a['nombre'], a['id'])
        self.selector_animal.currentIndexChanged.connect(self._actualizar_todo)
        self.selector_animal.setMinimumHeight(30)
        fila_filtros.addWidget(self.selector_animal, 1)

        fila_filtros.addWidget(QLabel('Vista:'))
        self.selector_seccion = QComboBox()
        self.selector_seccion.addItems([
            'Evolución de Costos',
            'Comparador de Formulaciones',
            'Simulador de Precios',
            'Resumen Mensual'
        ])
        self.selector_seccion.currentIndexChanged.connect(self._cambiar_seccion)
        self.selector_seccion.setMinimumHeight(30)
        fila_filtros.addWidget(self.selector_seccion, 1)
        layout.addLayout(fila_filtros)

        self.fig = Figure(facecolor=COLORS['bg_dark'])
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas.setMinimumHeight(320)
        layout.addWidget(self.canvas, 3)

        self.tabla_comparativa = QTableWidget()
        self.tabla_comparativa.setVisible(False)
        layout.addWidget(self.tabla_comparativa, 2)

        self.simulador_widget = QWidget()
        self.simulador_widget.setVisible(False)
        self._crear_simulador(self.simulador_widget)
        layout.addWidget(self.simulador_widget, 2)

        self._actualizar_todo()

    def _crear_cards_resumen(self, layout):
        cards_layout = QHBoxLayout()

        formulaciones = self.db.get_formulaciones()

        if formulaciones:
            mas_barata = min(formulaciones, key=lambda f: f['costo_por_kg'])
            mas_cara = max(formulaciones, key=lambda f: f['costo_por_kg'])

            costos = [f['costo_por_kg'] for f in formulaciones if f['costo_por_kg'] > 0]
            costo_prom = sum(costos) / len(costos) if costos else 0

            insumos = self.db.get_insumos()
            insumo_costoso = max(insumos, key=lambda i: i['precio_kg']) if insumos else None
        else:
            mas_barata = {'nombre': '--', 'costo_por_kg': 0}
            mas_cara = {'nombre': '--', 'costo_por_kg': 0}
            costo_prom = 0
            insumo_costoso = None

        cards = [
            ('Fórmula más barata', f"{self.moneda}{mas_barata['costo_por_kg']:.4f}/kg", mas_barata['nombre'], COLORS['primary']),
            ('Fórmula más cara', f"{self.moneda}{mas_cara['costo_por_kg']:.4f}/kg", mas_cara['nombre'], COLORS['danger']),
            ('Costo promedio', f"{self.moneda}{costo_prom:.4f}/kg", f'{len(formulaciones)} fórmulas', COLORS['accent']),
        ]

        if insumo_costoso:
            cards.append(('Insumo más costoso', f"{self.moneda}{insumo_costoso['precio_kg']:.4f}/kg", insumo_costoso['nombre'], COLORS['warning']))

        for titulo, valor, subtitulo, color in cards:
            card = QGroupBox(titulo)
            card.setStyleSheet(f"""
                QGroupBox {{
                    border: 2px solid {color};
                    border-radius: 8px;
                    margin-top: 8px;
                    padding-top: 8px;
                    color: {color};
                    font-weight: bold;
                }}
                QGroupBox::title {{ color: {color}; }}
            """)

            card_layout = QVBoxLayout(card)
            lbl_valor = QLabel(valor)
            lbl_valor.setStyleSheet(f'font-size: 15px; font-weight: bold; color: {COLORS["text"]};')
            lbl_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(lbl_valor)

            lbl_sub = QLabel(subtitulo)
            lbl_sub.setStyleSheet(f'font-size: 9px; color: {COLORS["text_dim"]};')
            lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(lbl_sub)

            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)

    def _crear_simulador(self, widget):
        layout = QVBoxLayout(widget)

        self.sim_insumo = QComboBox()
        insumos = self.db.get_insumos()
        for ing in insumos:
            self.sim_insumo.addItem(ing['nombre'], ing['id'])
        layout.addWidget(QLabel('Seleccionar insumo:'))
        layout.addWidget(self.sim_insumo)

        self.sim_variacion = QDoubleSpinBox()
        self.sim_variacion.setRange(-50, 100)
        self.sim_variacion.setValue(20)
        self.sim_variacion.setSuffix('%')
        layout.addWidget(QLabel('Variación de precio:'))
        layout.addWidget(self.sim_variacion)

        btn_simular = QPushButton('🔄 Simular')
        btn_simular.setObjectName('btn_primario')
        btn_simular.setMinimumHeight(30)
        btn_simular.setMaximumHeight(34)
        btn_simular.setStyleSheet('font-size: 11px; padding: 4px 10px;')
        btn_simular.clicked.connect(self._ejecutar_simulacion)
        layout.addWidget(btn_simular)

        self.tabla_simulacion = QTableWidget()
        self.tabla_simulacion.setColumnCount(5)
        self.tabla_simulacion.setHorizontalHeaderLabels([
            'Formulación', 'Costo Actual', 'Costo Simulado', 'Diferencia', 'Impacto %'
        ])
        self.tabla_simulacion.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabla_simulacion)

    def _actualizar_todo(self):
        seccion = self.selector_seccion.currentIndex()
        self._cambiar_seccion(seccion)

    def _cambiar_seccion(self, index):
        self.fig.clear()
        self.fig.set_facecolor(COLORS['bg_dark'])
        self.tabla_comparativa.setVisible(False)
        self.simulador_widget.setVisible(False)

        animal_id = self.selector_animal.currentData()

        if index == 0:
            self._graficar_evolucion_costos(animal_id)
        elif index == 1:
            self._mostrar_comparador(animal_id)
        elif index == 2:
            self.simulador_widget.setVisible(True)
        elif index == 3:
            self._graficar_resumen_mensual()

        self.canvas.draw()

    def _graficar_evolucion_costos(self, animal_id=None):
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(COLORS['bg_dark'])

        formulaciones = self.db.get_formulaciones_por_animal_fecha()

        if not formulaciones:
            ax.text(0.5, 0.5, 'Sin datos', ha='center', va='center',
                    color=COLORS['muted'], fontsize=14, transform=ax.transAxes)
            return

        datos_por_animal = {}
        for f in formulaciones:
            if animal_id and f['animal_id'] != animal_id:
                continue
            animal = f.get('animal_nombre', 'Sin animal')
            if animal not in datos_por_animal:
                datos_por_animal[animal] = {'fechas': [], 'costos': []}
            datos_por_animal[animal]['fechas'].append(f['fecha_modificacion'][:10])
            datos_por_animal[animal]['costos'].append(f['costo_por_kg'])

        colores = ['#2D7D46', '#5BC0DE', '#F0AD4E', '#D9534F', '#9B59B6', '#E67E22']
        for i, (animal, datos) in enumerate(datos_por_animal.items()):
            color = colores[i % len(colores)]
            x = range(len(datos['fechas']))
            ax.plot(x, datos['costos'], 'o-', color=color, label=animal, linewidth=2)

            if len(datos['costos']) >= 2:
                z = np.polyfit(x, datos['costos'], 1)
                p = np.poly1d(z)
                ax.plot(x, p(x), '--', color=color, alpha=0.5, label=f'{animal} (tendencia)')

        ax.set_xticks(range(max(len(d['fechas']) for d in datos_por_animal.values())))
        todas_fechas = []
        for d in datos_por_animal.values():
            todas_fechas.extend(d['fechas'])
        fechas_unicas = sorted(set(todas_fechas))
        if fechas_unicas:
            ax.set_xticks(range(len(fechas_unicas)))
            ax.set_xticklabels(fechas_unicas, rotation=45, ha='right', fontsize=8, color=COLORS['text'])

        ax.tick_params(colors=COLORS['text'])
        ax.legend(facecolor=COLORS['bg_surface'], edgecolor=COLORS['bg_border'],
                  labelcolor=COLORS['text'])
        ax.set_title('Evolución de Costo/kg por Animal', color=COLORS['text'], fontsize=12)
        ax.set_ylabel(f'Costo ({self.moneda}/kg)', color=COLORS['text'])

        for spine in ax.spines.values():
            spine.set_color(COLORS['bg_border'])

    def _mostrar_comparador(self, animal_id=None):
        self.tabla_comparativa.setVisible(True)

        formulaciones = self.db.get_formulaciones(animal_id)
        if not formulaciones:
            self.tabla_comparativa.setRowCount(0)
            return

        self.tabla_comparativa.setColumnCount(6)
        self.tabla_comparativa.setHorizontalHeaderLabels([
            'Nombre', 'Animal', 'Tipo', 'Costo/kg', 'Costo/ton', 'Proteína%'
        ])
        self.tabla_comparativa.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_comparativa.setRowCount(len(formulaciones))

        for i, f in enumerate(formulaciones):
            self.tabla_comparativa.setItem(i, 0, QTableWidgetItem(f['nombre']))
            self.tabla_comparativa.setItem(i, 1, QTableWidgetItem(f.get('animal_nombre', '--')))
            self.tabla_comparativa.setItem(i, 2, QTableWidgetItem('⚡' if f['tipo'] == 'optimizada' else '✍️'))
            self.tabla_comparativa.setItem(i, 3, QTableWidgetItem(f"{self.moneda}{f['costo_por_kg']:.4f}"))
            self.tabla_comparativa.setItem(i, 4, QTableWidgetItem(f"{self.moneda}{f['costo_por_tonelada']:.2f}"))
            self.tabla_comparativa.setItem(i, 5, QTableWidgetItem(f"{f['proteina_total']:.2f}%"))

    def _ejecutar_simulacion(self):
        insumo_id = self.sim_insumo.currentData()
        variacion = self.sim_variacion.value() / 100

        insumo = self.db.get_insumo_by_id(insumo_id)
        if not insumo:
            return

        precio_nuevo = insumo['precio_kg'] * (1 + variacion)

        formulaciones = self.db.get_formulaciones()
        self.tabla_simulacion.setRowCount(len(formulaciones))

        for i, f in enumerate(formulaciones):
            ingredientes = self.db.get_formulacion_ingredientes(f['id'])
            costo_simulado = 0
            for ing in ingredientes:
                precio_ing = precio_nuevo if ing['insumo_id'] == insumo_id else ing['precio_kg']
                costo_simulado += ing['tanteo_kg'] * precio_ing

            costo_simulado_kg = costo_simulado / f['total_kg'] if f['total_kg'] > 0 else 0
            diferencia = costo_simulado_kg - f['costo_por_kg']
            impacto = (diferencia / f['costo_por_kg'] * 100) if f['costo_por_kg'] > 0 else 0

            self.tabla_simulacion.setItem(i, 0, QTableWidgetItem(f['nombre']))
            self.tabla_simulacion.setItem(i, 1, QTableWidgetItem(f"{self.moneda}{f['costo_por_kg']:.4f}"))
            self.tabla_simulacion.setItem(i, 2, QTableWidgetItem(f"{self.moneda}{costo_simulado_kg:.4f}"))

            item_diff = QTableWidgetItem(f"{self.moneda}{diferencia:+.4f}")
            item_diff.setForeground(QColor(COLORS['danger']) if diferencia > 0 else QColor(COLORS['primary']))
            self.tabla_simulacion.setItem(i, 3, item_diff)

            item_impacto = QTableWidgetItem(f"{impacto:+.2f}%")
            item_impacto.setForeground(QColor(COLORS['danger']) if impacto > 5 else QColor(COLORS['primary']))
            self.tabla_simulacion.setItem(i, 4, item_impacto)

    def _graficar_resumen_mensual(self):
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(COLORS['bg_dark'])

        resumen = self.db.get_resumen_mensual()
        if not resumen:
            ax.text(0.5, 0.5, 'Sin datos de lotes', ha='center', va='center',
                    color=COLORS['muted'], fontsize=14, transform=ax.transAxes)
            return

        meses = [r['mes'] for r in reversed(resumen)]
        costos = [r['costo_promedio'] for r in reversed(resumen)]

        x = range(len(meses))
        ax.bar(x, costos, color=COLORS['primary'], alpha=0.8)
        ax.set_xticks(list(x))
        ax.set_xticklabels(meses, rotation=45, ha='right', fontsize=8, color=COLORS['text'])
        ax.tick_params(colors=COLORS['text'])
        ax.set_title('Costo Promedio/kg por Mes', color=COLORS['text'], fontsize=12)
        ax.set_ylabel(f'Costo ({self.moneda}/kg)', color=COLORS['text'])

        for spine in ax.spines.values():
            spine.set_color(COLORS['bg_border'])
