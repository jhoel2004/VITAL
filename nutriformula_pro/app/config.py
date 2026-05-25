from app.utils import get_system_font

FONT = get_system_font()

COLORS = {
    'bg_dark':      '#1E1E2E',
    'bg_surface':   '#252538',
    'bg_deeper':    '#0F0F1E',
    'bg_border':    '#2A2A4A',
    'primary':      '#2D7D46',
    'primary_light':'#5CB85C',
    'primary_dark': '#1B4F2E',
    'accent':       '#5BC0DE',
    'warning':      '#F0AD4E',
    'danger':       '#D9534F',
    'muted':        '#6060A0',
    'text':         '#E0E0F0',
    'text_dim':     '#A0A0C0',
    'text_faint':   '#505070',
    'gold':         '#F0D060',
    'semaforo_ok':  '#1A3A2A',
    'semaforo_warn':'#3A2A0A',
    'semaforo_bad': '#3A1A1A',
}

ESTILO_TABLA = f"""
    QTableWidget {{
        background-color: {COLORS['bg_dark']};
        alternate-background-color: {COLORS['bg_surface']};
        color: {COLORS['text']};
        gridline-color: {COLORS['bg_border']};
        border: 1px solid {COLORS['bg_border']};
        font-family: "{FONT}";
        font-size: 11px;
    }}
    QTableWidget::item {{
        background-color: {COLORS['bg_dark']};
        color: {COLORS['text']};
        padding: 4px 6px;
        border: none;
    }}
    QTableWidget::item:selected {{
        background-color: {COLORS['primary']};
        color: white;
    }}
    QTableWidget::item:hover {{
        background-color: {COLORS['bg_border']};
    }}
    QHeaderView::section {{
        background-color: {COLORS['bg_deeper']};
        color: {COLORS['muted']};
        padding: 6px 8px;
        border: none;
        border-right: 1px solid {COLORS['bg_border']};
        border-bottom: 2px solid {COLORS['primary']};
        font-weight: bold;
        font-size: 10px;
        font-family: "{FONT}";
    }}
    QScrollBar:vertical {{
        background: {COLORS['bg_dark']}; width: 8px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['bg_border']}; border-radius: 4px; min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {COLORS['primary']}; }}
"""

LIMITES_INCLUSION = {
    'melaza':                15.0,
    'harina de pescado':      8.0,
    'gallinaza aves':        10.0,
    'aceite vegetal':        10.0,
    'aceite de palma':       10.0,
    'aceite de soya':        10.0,
    'bagazo de caña azúcar': 20.0,
    'harina de sangre':       5.0,
    'harina de plumas':       5.0,
    'glicerina cruda':        5.0,
    'sal común (nacl)':       0.5,
    'bicarbonato de sodio':   0.5,
    'dl-metionina':           0.5,
    'lisina sintética l-lys': 1.0,
}

RESTRICCIONES_INGREDIENTES = {
    'melaza': {
        'tms_pct': 15.0,
        'especie': 'todos',
        'motivo': 'Exceso causa diarrea osmótica',
        'fuente': 'Church & Pond 2002',
    },
    'harina de pescado': {
        'tms_pct': 8.0,
        'especie': 'todos',
        'motivo': 'Oxidación lipídica, sabor en carnes y huevos',
        'fuente': 'Leeson & Summers 2005',
    },
    'gallinaza aves': {
        'tms_pct': 10.0,
        'especie': 'bovinos',
        'motivo': 'Riesgo de patógenos si no está tratada',
        'fuente': 'NRC 2000',
    },
    'aceite vegetal': {
        'tms_pct': 10.0,
        'especie': 'todos',
        'motivo': 'Exceso deprime consumo y altera perfil lipídico',
        'fuente': 'NRC 1994',
    },
    'harina de sangre': {
        'tms_pct': 5.0,
        'especie': 'todos',
        'motivo': 'Desequilibra aminoácidos y baja palatabilidad',
        'fuente': 'NRC 1994',
    },
    'harina de plumas': {
        'tms_pct': 5.0,
        'especie': 'todos',
        'motivo': 'Baja digestibilidad y menor disponibilidad de AA',
        'fuente': 'Leeson 2005',
    },
    'bagazo de caña azúcar': {
        'tms_pct': 20.0,
        'especie': 'bovinos',
        'motivo': 'Dilución excesiva de la dieta',
        'fuente': 'NRC 2000',
    },
    'sal común (nacl)': {
        'tms_pct': 0.5,
        'especie': 'todos',
        'motivo': 'Toxicidad por exceso de sodio',
        'fuente': 'NRC 1994',
    },
}

CA_P_MIN = 1.2
CA_P_MAX = 2.0
