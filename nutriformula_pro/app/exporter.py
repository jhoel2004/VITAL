import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.lib.colors import HexColor

from app.calculator import calcular_composicion


VERDE_OSCURO = HexColor('#1B4F2E')
VERDE_CLARO = HexColor('#5CB85C')
GRIS_CLARO = HexColor('#F5F5F5')
BLANCO = colors.white
NEGRO = colors.black
GRIS_TEXTO = HexColor('#333333')


def _crear_pdf(archivo, titulo='FORMULACIÓN DE RACIÓN'):
    doc = SimpleDocTemplate(
        archivo,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )
    return doc


def _estilos():
    estilos = getSampleStyleSheet()

    estilos.add(ParagraphStyle(
        'TituloPrincipal',
        parent=estilos['Title'],
        fontSize=18,
        textColor=VERDE_OSCURO,
        alignment=TA_CENTER,
        spaceAfter=6,
    ))

    estilos.add(ParagraphStyle(
        'Subtitulo',
        parent=estilos['Heading2'],
        fontSize=12,
        textColor=VERDE_CLARO,
        spaceBefore=12,
        spaceAfter=6,
    ))

    estilos.add(ParagraphStyle(
        'NormalOscuro',
        parent=estilos['Normal'],
        fontSize=10,
        textColor=GRIS_TEXTO,
    ))

    estilos.add(ParagraphStyle(
        'PiePagina',
        parent=estilos['Normal'],
        fontSize=8,
        textColor=HexColor('#999999'),
        alignment=TA_CENTER,
    ))

    return estilos


def _tabla_composicion(ingredientes, totales):
    encabezados = [
        'Insumo', '%', 'Prot%', 'EM', 'Fibra%', 'Grasa%',
        'Ca%', 'P%', 'Lis%', 'Met%'
    ]

    datos = [encabezados]
    for ing in ingredientes:
        datos.append([
            ing.get('nombre', ''),
            f"{ing.get('porcentaje', 0):.2f}",
            f"{ing.get('proteina_aportada', 0):.4f}",
            f"{ing.get('em_aportada', 0):.2f}",
            f"{ing.get('fibra_aportada', 0):.4f}",
            f"{ing.get('grasa_aportada', 0):.4f}",
            f"{ing.get('calcio_aportado', 0):.4f}",
            f"{ing.get('fosforo_aportado', 0):.4f}",
            f"{ing.get('lisina_aportada', 0):.4f}",
            f"{ing.get('metionina_aportada', 0):.4f}",
        ])

    datos.append([
        'TOTALES', '100.00',
        f"{totales['proteina']:.4f}",
        f"{totales['em_kcal']:.2f}",
        f"{totales['fibra']:.4f}",
        f"{totales['grasa']:.4f}",
        f"{totales['calcio']:.4f}",
        f"{totales['fosforo']:.4f}",
        f"{totales['lisina']:.4f}",
        f"{totales['metionina']:.4f}",
    ])

    col_widths = [
        1.5 * inch, 0.6 * inch, 0.6 * inch, 0.6 * inch,
        0.6 * inch, 0.6 * inch, 0.6 * inch, 0.6 * inch,
        0.6 * inch, 0.6 * inch,
    ]

    tabla = Table(datos, colWidths=col_widths)

    estilo = [
        ('BACKGROUND', (0, 0), (-1, 0), VERDE_OSCURO),
        ('TEXTCOLOR', (0, 0), (-1, 0), BLANCO),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, -1), (-1, -1), VERDE_OSCURO),
        ('TEXTCOLOR', (0, -1), (-1, -1), BLANCO),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -2), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [BLANCO, GRIS_CLARO]),
    ]
    tabla.setStyle(TableStyle(estilo))

    return tabla


def _grafico_radar_bytes(totales, total_kg):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    nutrientes = [
        'proteina', 'em_kcal', 'fibra', 'grasa',
        'calcio', 'fosforo', 'lisina', 'metionina'
    ]
    nombres = [
        'Proteína', 'EM Kcal', 'Fibra', 'Grasa',
        'Calcio', 'Fósforo', 'Lisina', 'Metionina'
    ]

    fig = Figure(figsize=(5, 5), facecolor='white')
    ax = fig.add_subplot(111, projection='polar')

    num_vars = len(nutrientes)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    from app.calculator import normalizar_para_radar
    totales_norm = normalizar_para_radar(totales, total_kg)

    max_vals = []
    for n in nutrientes:
        val = totales_norm.get(n, 0)
        max_vals.append(val if val > 0 else 0)
    max_vals += max_vals[:1]

    ax.plot(angles, max_vals, color='#2D7D46', linewidth=2)
    ax.fill(angles, max_vals, color='#2D7D46', alpha=0.2)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(nombres, fontsize=8)
    ax.set_ylim(0, max(max(max_vals) * 1.2, 1))
    ax.yaxis.grid(True, color='#CCCCCC')

    canvas = FigureCanvasAgg(fig)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    return buf


def _grafico_torta_bytes(ingredientes):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    fig = Figure(figsize=(5, 5), facecolor='white')
    ax = fig.add_subplot(111)

    labels = [ing.get('nombre', '') for ing in ingredientes]
    sizes = [ing.get('porcentaje', 0) for ing in ingredientes]

    colores = [
        '#2D7D46', '#5CB85C', '#F0AD4E', '#D9534F', '#5BC0DE',
        '#9B59B6', '#E67E22', '#1ABC9C', '#3498DB', '#E74C3C'
    ]

    ax.pie(
        sizes, labels=labels, colors=colores[:len(labels)],
        autopct='%1.1f%%', startangle=90,
        textprops={'fontsize': 7}
    )
    ax.set_title('Distribución de Ingredientes', fontsize=10)

    canvas = FigureCanvasAgg(fig)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    return buf


def exportar_formulacion_especifica_pdf(db, form_id, archivo):
    form = db.get_formulacion(form_id)
    if not form:
        raise ValueError('Formulación no encontrada')

    ingredientes_db = db.get_formulacion_ingredientes(form_id)
    ingredientes_lista = []
    for ing in ingredientes_db:
        insumo = db.get_insumo_by_id(ing['insumo_id'])
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

    _generar_pdf_contenido(
        archivo, form, ingredientes_lista, db
    )


def exportar_formulacion_pdf(db, archivo):
    formulaciones = db.get_formulaciones()
    if not formulaciones:
        raise ValueError('No hay formulaciones guardadas')

    form = formulaciones[0]
    ingredientes_db = db.get_formulacion_ingredientes(form['id'])
    ingredientes_lista = []
    for ing in ingredientes_db:
        insumo = db.get_insumo_by_id(ing['insumo_id'])
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

    _generar_pdf_contenido(
        archivo, form, ingredientes_lista, db
    )


def _generar_pdf_contenido(archivo, form, ingredientes_lista, db):
    doc = _crear_pdf(archivo)
    estilos = _estilos()

    totales, _ = calcular_composicion(
        ingredientes_lista, form['total_kg']
    )

    elementos = []

    elementos.append(Paragraph(
        'NutriFormula Pro', estilos['TituloPrincipal']
    ))
    elementos.append(Spacer(1, 6))
    elementos.append(Paragraph(
        'FORMULACIÓN DE RACIÓN', estilos['Subtitulo']
    ))
    elementos.append(Spacer(1, 12))

    datos_generales = [
        ['Nombre:', form['nombre']],
        ['Animal:', form.get('animal_nombre', '--')],
        ['Fecha:', form['fecha_modificacion'][:10]],
        ['Tipo:', 'Optimizada' if form['tipo'] == 'optimizada' else 'Manual'],
        ['Total kg:', f"{form['total_kg']:.2f}"],
        ['Costo/kg:', f"${form['costo_por_kg']:.4f}"],
        ['Costo/ton:', f"${form['costo_por_tonelada']:.2f}"],
    ]

    tabla_datos = Table(datos_generales, colWidths=[1.5*inch, 4*inch])
    tabla_datos.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), GRIS_TEXTO),
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#F0F0F0')),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elementos.append(tabla_datos)
    elementos.append(Spacer(1, 16))

    elementos.append(Paragraph(
        'Composición Nutricional', estilos['Subtitulo']
    ))
    elementos.append(_tabla_composicion(ingredientes_lista, totales))
    elementos.append(Spacer(1, 16))

    instrucciones = form.get('instrucciones_preparacion', '')
    if instrucciones:
        elementos.append(Paragraph(
            'Instrucciones de Preparación', estilos['Subtitulo']
        ))
        for linea in instrucciones.split('\n'):
            if linea.strip():
                elementos.append(Paragraph(
                    f'• {linea.strip()}', estilos['NormalOscuro']
                ))
        elementos.append(Spacer(1, 12))

    try:
        buf_radar = _grafico_radar_bytes(totales, form['total_kg'])
        img_radar = Image(buf_radar, width=3*inch, height=3*inch)
        elementos.append(img_radar)
    except Exception:
        pass

    if ingredientes_lista:
        try:
            buf_torta = _grafico_torta_bytes(ingredientes_lista)
            img_torta = Image(buf_torta, width=3*inch, height=3*inch)
            elementos.append(Spacer(1, 12))
            elementos.append(img_torta)
        except Exception:
            pass

    def _pie_pagina(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(HexColor('#999999'))
        canvas.drawString(
            inch, 0.5 * inch,
            f"{form['nombre']} | {form['fecha_modificacion'][:10]}"
        )
        canvas.drawRightString(
            letter[0] - inch, 0.5 * inch,
            f'Página {canvas.getPageNumber()}'
        )
        canvas.restoreState()

    doc.build(elementos, onFirstPage=_pie_pagina, onLaterPages=_pie_pagina)


def exportar_formulacion_excel(db, archivo):
    import openpyxl

    wb = openpyxl.Workbook()

    formulaciones = db.get_formulaciones()

    for form in formulaciones:
        ws = wb.active
        ws.title = form['nombre'][:31]

        ws.append(['NutriFormula Pro - Formulación'])
        ws.append(['Nombre', form['nombre']])
        ws.append(['Animal', form.get('animal_nombre', '--')])
        ws.append(['Fecha', form['fecha_modificacion'][:10]])
        ws.append(['Total kg', form['total_kg']])
        ws.append(['Costo/kg', form['costo_por_kg']])
        ws.append(['Costo/ton', form['costo_por_tonelada']])
        ws.append([])

        ingredientes_db = db.get_formulacion_ingredientes(form['id'])
        encabezados = [
            'Insumo', 'kg', '%', 'Precio/kg',
            'Proteína', 'EM', 'Fibra', 'Grasa', 'Ca', 'P', 'Lisina', 'Metionina'
        ]
        ws.append(encabezados)

        for ing in ingredientes_db:
            insumo = db.get_insumo_by_id(ing['insumo_id'])
            if insumo:
                ws.append([
                    insumo['nombre'],
                    ing['tanteo_kg'],
                    ing['porcentaje'],
                    ing['precio_kg'],
                    ing['proteina_aportada'],
                    ing['em_aportada'],
                    ing['fibra_aportada'],
                    ing['grasa_aportada'],
                    ing['calcio_aportado'],
                    ing['fosforo_aportado'],
                    ing['lisina_aportada'],
                    ing['metionina_aportada'],
                ])

    wb.save(archivo)


def exportar_etiqueta_lote_pdf(db, lote_id, archivo):
    from reportlab.lib.pagesizes import A6
    from reportlab.lib.units import mm

    lote_data = None
    lotes = db.get_lotes()
    for l in lotes:
        if l['id'] == lote_id:
            lote_data = l
            break

    if not lote_data:
        raise ValueError('Lote no encontrado')

    doc = SimpleDocTemplate(
        archivo, pagesize=A6,
        rightMargin=10*mm, leftMargin=10*mm,
        topMargin=10*mm, bottomMargin=10*mm,
    )

    estilos = _estilos()
    config = db.get_all_config()
    nombre_empresa = config.get('nombre_empresa', 'VITAL')
    moneda = config.get('moneda', '$')

    elementos = []
    elementos.append(Paragraph(nombre_empresa, estilos['TituloPrincipal']))
    elementos.append(Spacer(1, 4))
    elementos.append(Paragraph('ETIQUETA DE LOTE', estilos['Subtitulo']))
    elementos.append(Spacer(1, 8))

    datos = [
        ['Lote:', lote_data['nombre']],
        ['Animal:', lote_data.get('animal_nombre', '--')],
        ['Fecha:', lote_data['fecha'][:10]],
        ['Kg totales:', f"{lote_data['cantidad_kg']:.1f}"],
        ['Costo total:', f"{moneda}{lote_data['costo_total']:.2f}"],
    ]
    tabla = Table(datos, colWidths=[25*mm, 75*mm])
    tabla.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 8))

    if lote_data['formulacion_id']:
        ingredientes = db.get_formulacion_ingredientes(lote_data['formulacion_id'])
        if ingredientes:
            elementos.append(Paragraph('Ingredientes principales:', estilos['Subtitulo']))
            top5 = sorted(ingredientes, key=lambda x: x['porcentaje'], reverse=True)[:5]
            datos_ing = [['Ingrediente', '%', 'kg']]
            for ing in top5:
                kg_lote = (ing['porcentaje'] / 100) * lote_data['cantidad_kg']
                datos_ing.append([
                    ing['insumo_nombre'],
                    f"{ing['porcentaje']:.1f}%",
                    f"{kg_lote:.1f}"
                ])
            tabla_ing = Table(datos_ing, colWidths=[50*mm, 20*mm, 20*mm])
            tabla_ing.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), VERDE_OSCURO),
                ('TEXTCOLOR', (0, 0), (-1, 0), BLANCO),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ]))
            elementos.append(tabla_ing)

    if lote_data.get('notas'):
        elementos.append(Spacer(1, 6))
        elementos.append(Paragraph('Notas:', estilos['Subtitulo']))
        elementos.append(Paragraph(lote_data['notas'], estilos['NormalOscuro']))

    def _pie(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(HexColor('#999999'))
        pie = config.get('pie_pagina', 'Generado con VITAL')
        canvas.drawString(10*mm, 5*mm, f"{pie} | Lote {lote_data['nombre']}")
        canvas.restoreState()

    doc.build(elementos, onFirstPage=_pie, onLaterPages=_pie)



