import sqlite3
from datetime import datetime


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA encoding = 'UTF-8';

CREATE TABLE IF NOT EXISTS insumos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    proteina    REAL    DEFAULT 0,
    em_kcal     REAL    DEFAULT 0,
    fibra       REAL    DEFAULT 0,
    grasa       REAL    DEFAULT 0,
    calcio      REAL    DEFAULT 0,
    fosforo     REAL    DEFAULT 0,
    lisina      REAL    DEFAULT 0,
    metionina   REAL    DEFAULT 0,
    colina_mgr  REAL    DEFAULT 0,
    precio_kg   REAL    DEFAULT 0,
    categoria   TEXT    DEFAULT 'General',
    activo      INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS animales (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE COLLATE NOCASE
);

CREATE TABLE IF NOT EXISTS formulaciones (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre                    TEXT    NOT NULL,
    fecha_creacion            TEXT    NOT NULL,
    fecha_modificacion        TEXT    NOT NULL,
    animal_id                 INTEGER REFERENCES animales(id),
    total_kg                  REAL    DEFAULT 0,
    proteina_total            REAL    DEFAULT 0,
    em_total                  REAL    DEFAULT 0,
    fibra_total               REAL    DEFAULT 0,
    grasa_total               REAL    DEFAULT 0,
    calcio_total              REAL    DEFAULT 0,
    fosforo_total             REAL    DEFAULT 0,
    lisina_total              REAL    DEFAULT 0,
    metionina_total           REAL    DEFAULT 0,
    colina_total              REAL    DEFAULT 0,
    costo_por_kg              REAL    DEFAULT 0,
    costo_por_tonelada        REAL    DEFAULT 0,
    instrucciones_preparacion TEXT    DEFAULT '',
    notas_generales           TEXT    DEFAULT '',
    tipo                      TEXT    DEFAULT 'manual'
);

CREATE TABLE IF NOT EXISTS formulacion_ingredientes (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    formulacion_id     INTEGER NOT NULL REFERENCES formulaciones(id) ON DELETE CASCADE,
    insumo_id          INTEGER NOT NULL REFERENCES insumos(id),
    tanteo_kg          REAL    DEFAULT 0,
    porcentaje         REAL    DEFAULT 0,
    precio_kg          REAL    DEFAULT 0,
    proteina_aportada  REAL    DEFAULT 0,
    em_aportada        REAL    DEFAULT 0,
    fibra_aportada     REAL    DEFAULT 0,
    grasa_aportada     REAL    DEFAULT 0,
    calcio_aportado    REAL    DEFAULT 0,
    fosforo_aportado   REAL    DEFAULT 0,
    lisina_aportada    REAL    DEFAULT 0,
    metionina_aportada REAL    DEFAULT 0,
    colina_aportada    REAL    DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_form_animal ON formulaciones(animal_id);
CREATE INDEX IF NOT EXISTS idx_fi_form     ON formulacion_ingredientes(formulacion_id);

-- NUEVAS TABLAS v2.0
CREATE TABLE IF NOT EXISTS config_empresa (
    clave  TEXT PRIMARY KEY,
    valor  TEXT
);

CREATE TABLE IF NOT EXISTS lotes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    formulacion_id  INTEGER REFERENCES formulaciones(id) ON DELETE SET NULL,
    nombre          TEXT NOT NULL,
    fecha           TEXT NOT NULL,
    cantidad_kg     REAL DEFAULT 0,
    costo_total     REAL DEFAULT 0,
    notas           TEXT DEFAULT '',
    estado          TEXT DEFAULT 'producido'
);

CREATE TABLE IF NOT EXISTS pacientes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre              TEXT NOT NULL,
    especie             TEXT NOT NULL,
    raza                TEXT DEFAULT '',
    sexo                TEXT DEFAULT '',
    edad_meses          REAL DEFAULT 0,
    peso_kg             REAL DEFAULT 0,
    condicion_corporal  INTEGER DEFAULT 3,
    estado              TEXT DEFAULT 'activo',
    propietario         TEXT DEFAULT '',
    fecha_ingreso       TEXT NOT NULL,
    notas_clinicas      TEXT DEFAULT '',
    animal_id           INTEGER REFERENCES animales(id)
);

CREATE TABLE IF NOT EXISTS seguimiento_nutricional (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id         INTEGER NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    formulacion_id      INTEGER REFERENCES formulaciones(id),
    fecha               TEXT NOT NULL,
    peso_kg             REAL DEFAULT 0,
    condicion_corporal  INTEGER DEFAULT 3,
    consumo_real_kg     REAL DEFAULT 0,
    observaciones       TEXT DEFAULT '',
    ajuste_recomendado  TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS tablas_requerimientos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    especie         TEXT NOT NULL,
    etapa           TEXT NOT NULL,
    peso_ref_kg     REAL DEFAULT 0,
    proteina_min    REAL DEFAULT 0,
    proteina_max    REAL DEFAULT 0,
    em_min          REAL DEFAULT 0,
    em_max          REAL DEFAULT 0,
    fibra_min       REAL DEFAULT 0,
    fibra_max       REAL DEFAULT 0,
    grasa_min       REAL DEFAULT 0,
    grasa_max       REAL DEFAULT 0,
    calcio_min      REAL DEFAULT 0,
    calcio_max      REAL DEFAULT 0,
    fosforo_min     REAL DEFAULT 0,
    fosforo_max     REAL DEFAULT 0,
    lisina_min      REAL DEFAULT 0,
    metionina_min   REAL DEFAULT 0,
    colina_min      REAL DEFAULT 0,
    fuente          TEXT DEFAULT 'NRC',
    notas           TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS restricciones_ingredientes (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    insumo_id               INTEGER NOT NULL REFERENCES insumos(id),
    tms_pct                 REAL DEFAULT 100,
    especie_restringida     TEXT DEFAULT '',
    motivo                  TEXT DEFAULT '',
    fuente_bibliografica    TEXT DEFAULT ''
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_req_especie_etapa_fuente
ON tablas_requerimientos(especie, etapa, fuente);

CREATE UNIQUE INDEX IF NOT EXISTS idx_rest_insumo_especie
ON restricciones_ingredientes(insumo_id, especie_restringida);
"""

INSUMOS_DEFAULT = [
    ('harina maíz amarillo', 8.8, 3350, 1.8, 4.2, 0.03, 0.26, 0.20, 0.18, 496, 0.0, 'Cereales'),
    ('chanca maíz amarillo', 8.8, 3300, 3.0, 4.0, 0.03, 0.26, 0.20, 0.15, 490, 0.0, 'Cereales'),
    ('soya integral', 38.0, 3450, 6.0, 20.0, 0.25, 0.59, 2.40, 0.54, 2800, 0.0, 'Proteínas'),
    ('torta de soya', 45.0, 2200, 6.5, 1.5, 0.30, 0.63, 2.68, 0.52, 2614, 0.0, 'Proteínas'),
    ('palmiste', 15.0, 1600, 20.0, 9.0, 0.20, 0.59, 2.40, 0.50, 2600, 0.0, 'Subproductos'),
    ('sorgo', 8.0, 3000, 7.5, 4.0, 0.03, 0.20, 0.20, 0.17, 450, 0.0, 'Cereales'),
    ('afrecho de trigo', 15.0, 2000, 30.0, 3.0, 0.10, 1.02, 0.57, 0.33, 1000, 0.0, 'Subproductos'),
    ('pasta de algodón', 30.0, 1600, 25.0, 4.0, 0.20, 0.30, 1.91, 0.73, 0, 0.0, 'Proteínas'),
    ('arrocillo nielen', 9.0, 3350, 0.8, 1.8, 0.06, 0.28, 0.27, 0.16, 957, 0.0, 'Subproductos'),
    ('polvo de arroz', 13.96, 2600, 8.0, 14.0, 0.70, 1.50, 0.52, 0.20, 1200, 0.0, 'Subproductos'),
    ('harina de avena', 11.0, 3100, 3.0, 3.0, 0.80, 0.40, 0.53, 0.20, 1100, 0.0, 'Cereales'),
    ('salvado de avena', 17.3, 2460, 15.0, 7.0, 0.80, 0.38, 0.50, 0.18, 990, 0.0, 'Subproductos'),
    ('heno de avena molida', 3.0, 800, 50.0, 0.0, 0.00, 0.00, 0.00, 0.00, 0, 0.0, 'Fibras'),
    ('gallinaza aves', 18.0, 2000, 35.0, 1.0, 0.05, 2.28, 0.05, 0.05, 600, 0.0, 'Aditivos'),
    ('harina de carne', 60.0, 3050, 2.7, 2.5, 8.85, 4.44, 3.23, 0.70, 2041, 0.0, 'Proteínas'),
    ('bagazo de caña azúcar', 2.1, 1450, 47.0, 0.7, 0.82, 0.27, 0.00, 0.00, 0, 0.0, 'Fibras'),
    ('harina de cebada', 13.0, 2500, 4.0, 5.4, 0.04, 0.34, 0.39, 0.15, 1039, 0.0, 'Cereales'),
    ('heno de cebada molida', 3.4, 800, 70.0, 0.0, 0.00, 0.00, 0.00, 0.00, 0, 0.0, 'Fibras'),
    ('galleta molida', 10.4, 3600, 2.0, 4.0, 0.13, 0.24, 0.31, 0.17, 923, 0.0, 'Subproductos'),
    ('aceite vegetal', 0.0, 7000, 0.0, 80.0, 0.00, 0.00, 0.00, 0.00, 0, 0.0, 'Grasas'),
    ('melaza', 3.2, 1950, 0.0, 0.0, 0.75, 0.08, 0.00, 0.00, 750, 0.0, 'Subproductos'),
    ('harina de pescado', 65.0, 3000, 1.0, 5.0, 3.75, 2.49, 5.00, 2.00, 3709, 0.0, 'Proteínas'),
    ('harina de yuca', 2.3, 3330, 4.6, 0.0, 0.25, 0.17, 0.07, 0.03, 800, 0.0, 'Cereales'),
    ('harina alfalfa', 10.5, 2200, 30.0, 0.0, 0.10, 0.25, 0.08, 0.02, 100, 0.0, 'Fibras'),
    ('achiote', 14.5, 2460, 15.0, 7.0, 0.20, 0.30, 1.90, 0.70, 900, 0.0, 'Aditivos'),
    ('harina de banana', 35.0, 3450, 8.0, 7.0, 0.23, 0.60, 0.10, 0.05, 0, 0.0, 'Proteínas'),
]

INSUMOS_ADICIONALES = [
    ('carbonato de calcio', 0.0, 0, 0.0, 0.0, 38.0, 0.0, 0.0, 0.0, 0, 0.0, 'Minerales'),
    ('fosfato bicálcico', 0.0, 0, 0.0, 0.0, 22.0, 18.0, 0.0, 0.0, 0, 0.0, 'Minerales'),
    ('sal común (NaCl)', 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 'Minerales'),
    ('bicarbonato de sodio', 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 'Minerales'),
    ('óxido de zinc', 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 'Minerales'),
    ('premezcla vitamínica aves', 12.0, 0, 0.0, 0.0, 3.5, 2.0, 0.5, 0.3, 2500, 0.0, 'Premezclas'),
    ('premezcla vitamínica porcinos', 10.0, 0, 0.0, 0.0, 2.0, 1.5, 0.4, 0.2, 2000, 0.0, 'Premezclas'),
    ('lisina sintética L-Lys', 78.0, 0, 0.0, 0.0, 0.0, 0.0, 78.0, 0.0, 0, 0.0, 'Aminoácidos'),
    ('DL-metionina', 58.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 99.0, 0, 0.0, 'Aminoácidos'),
    ('treonina sintética', 98.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 'Aminoácidos'),
    ('triptófano sintético', 98.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 'Aminoácidos'),
    ('aceite de palma', 0.0, 8000, 0.0, 80.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 'Grasas'),
    ('aceite de soya', 0.0, 8000, 0.0, 80.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 'Grasas'),
    ('glicerina cruda', 0.0, 3300, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 'Energéticos'),
    ('harina de sangre', 80.0, 2900, 1.0, 1.5, 0.3, 0.25, 7.0, 1.2, 800, 0.0, 'Proteínas'),
    ('harina de plumas', 85.0, 2850, 2.0, 3.5, 0.4, 0.50, 1.8, 0.6, 500, 0.0, 'Proteínas'),
    ('gluten de maíz', 60.0, 3600, 2.0, 4.5, 0.05, 0.5, 1.2, 2.0, 600, 0.0, 'Proteínas'),
    ('cebada grano', 11.5, 2650, 5.5, 2.1, 0.06, 0.38, 0.43, 0.18, 1050, 0.0, 'Cereales'),
    ('trigo grano', 12.5, 3200, 3.0, 1.9, 0.07, 0.38, 0.35, 0.22, 950, 0.0, 'Cereales'),
    ('maíz alto en aceite', 8.5, 3500, 1.5, 6.5, 0.03, 0.27, 0.22, 0.19, 510, 0.0, 'Cereales'),
]

ANIMALES_DEFAULT = [
    'Bovinos', 'Cerdos', 'Equinos', 'Gallinas Ponedoras',
    'Mascotas', 'Ovinos/Caprinos', 'Peces', 'Pollos de Engorde', 'Gallinas'
]

CONFIG_DEFAULT = [
    ('nombre_empresa', 'Mi Granja'),
    ('responsable', ''),
    ('moneda', '$'),
    ('pie_pagina', 'Formulación generada con VITAL'),
]

REQUERIMIENTOS_NRC = [
    ('Pollo de engorde', 'Inicio (0-21 días)', 0.5, 22.0, 24.0, 3050, 3200, 0, 4, 4, 8, 0.90, 1.10, 0.45, 0.55, 1.20, 0.50, 1500, 'NRC 1994'),
    ('Pollo de engorde', 'Crecimiento (22-42d)', 1.5, 20.0, 22.0, 3100, 3250, 0, 4, 4, 8, 0.85, 1.05, 0.42, 0.52, 1.05, 0.45, 1300, 'NRC 1994'),
    ('Pollo de engorde', 'Finalización (>42d)', 2.5, 18.0, 20.0, 3150, 3300, 0, 4, 4, 8, 0.75, 0.95, 0.38, 0.48, 0.95, 0.40, 1100, 'NRC 1994'),
    ('Gallina ponedora', 'Prepostura (17-19 sem)', 1.5, 17.0, 18.5, 2700, 2850, 0, 5, 3, 7, 2.00, 2.50, 0.38, 0.48, 0.80, 0.35, 1100, 'NRC 1994'),
    ('Gallina ponedora', 'Pico de postura', 1.8, 15.5, 17.0, 2750, 2900, 0, 5, 3, 7, 3.50, 4.50, 0.35, 0.45, 0.73, 0.32, 1050, 'NRC 1994'),
    ('Gallina ponedora', 'Postura tardía', 1.9, 14.5, 16.0, 2750, 2900, 0, 5, 3, 7, 4.00, 4.75, 0.32, 0.42, 0.66, 0.29, 1000, 'NRC 1994'),
    ('Pavo', 'Inicio (0-4 sem)', 0.5, 28.0, 30.0, 2800, 2950, 0, 4, 3, 7, 1.20, 1.50, 0.60, 0.70, 1.65, 0.53, 1600, 'NRC 1994'),
    ('Codorniz', 'Postura', 0.15, 20.0, 22.0, 2900, 3000, 0, 4, 3, 6, 2.50, 3.00, 0.40, 0.50, 1.00, 0.40, 1200, 'NRC 1994'),
    ('Cerdo', 'Lechón (5-10 kg)', 7, 28.0, 30.0, 3400, 3600, 0, 4, 5, 9, 0.90, 1.10, 0.75, 0.85, 1.50, 0.40, 800, 'NRC 2012'),
    ('Cerdo', 'Inicio (10-25 kg)', 17, 22.0, 24.0, 3300, 3500, 0, 5, 4, 8, 0.80, 1.00, 0.65, 0.75, 1.25, 0.33, 700, 'NRC 2012'),
    ('Cerdo', 'Crecimiento (25-60 kg)', 42, 18.0, 20.0, 3200, 3400, 0, 6, 4, 8, 0.65, 0.85, 0.55, 0.65, 1.00, 0.27, 600, 'NRC 2012'),
    ('Cerdo', 'Finalización (60-100kg)', 80, 15.0, 17.0, 3200, 3400, 0, 6, 4, 8, 0.55, 0.75, 0.48, 0.58, 0.85, 0.23, 500, 'NRC 2012'),
    ('Cerdo', 'Gestante', 175, 13.0, 14.0, 3000, 3200, 0, 10, 3, 7, 0.90, 1.10, 0.75, 0.85, 0.75, 0.20, 600, 'NRC 2012'),
    ('Cerdo', 'Lactante', 200, 18.5, 20.0, 3300, 3500, 0, 7, 4, 8, 0.90, 1.10, 0.80, 0.90, 1.00, 0.27, 700, 'NRC 2012'),
    ('Bovino', 'Ternero (0-6 meses)', 100, 16.0, 18.0, 2500, 2800, 20, 35, 3, 10, 0.60, 1.00, 0.30, 0.45, 0.70, 0.20, 400, 'NRC 2000'),
    ('Bovino', 'Levante (6-18 meses)', 300, 12.0, 14.0, 2200, 2500, 25, 40, 3, 8, 0.40, 0.80, 0.25, 0.40, 0.50, 0.15, 300, 'NRC 2000'),
    ('Bovino', 'Engorde', 400, 10.0, 12.0, 2400, 2700, 20, 35, 3, 8, 0.40, 0.70, 0.22, 0.38, 0.45, 0.13, 250, 'NRC 2000'),
    ('Bovino', 'Vaca lechera (alta)', 550, 16.0, 18.0, 2600, 2900, 28, 40, 3, 8, 0.60, 1.00, 0.28, 0.45, 0.60, 0.20, 350, 'NRC 2001'),
    ('Bovino', 'Vaca seca/preparto', 600, 11.0, 13.0, 2200, 2500, 30, 45, 2, 7, 0.50, 0.80, 0.24, 0.38, 0.40, 0.13, 250, 'NRC 2001'),
    ('Ovino', 'Cordero (0-3 meses)', 20, 18.0, 20.0, 2700, 2900, 15, 30, 3, 8, 0.55, 0.90, 0.28, 0.40, 0.70, 0.18, 300, 'NRC 2007'),
    ('Ovino', 'Crecimiento', 40, 14.0, 16.0, 2400, 2700, 20, 35, 3, 7, 0.40, 0.70, 0.22, 0.35, 0.50, 0.14, 250, 'NRC 2007'),
    ('Ovino', 'Engorde', 55, 12.0, 14.0, 2500, 2800, 20, 35, 3, 7, 0.35, 0.65, 0.20, 0.33, 0.45, 0.13, 220, 'NRC 2007'),
    ('Ovino', 'Oveja gestante', 65, 11.0, 13.0, 2200, 2500, 25, 40, 2, 6, 0.45, 0.80, 0.24, 0.35, 0.40, 0.12, 200, 'NRC 2007'),
    ('Caprino', 'Cabra lechera', 50, 15.0, 17.0, 2600, 2900, 20, 35, 3, 7, 0.55, 0.90, 0.28, 0.40, 0.65, 0.18, 300, 'NRC 2007'),
    ('Tilapia', 'Alevín (< 5g)', 0.003, 35.0, 38.0, 3200, 3500, 3, 8, 6, 12, 1.50, 2.00, 0.80, 1.00, 2.00, 0.80, 800, 'NRC 2011'),
    ('Tilapia', 'Juvenil (5-50g)', 0.03, 30.0, 33.0, 3200, 3500, 3, 8, 6, 12, 1.30, 1.80, 0.70, 0.90, 1.70, 0.70, 700, 'NRC 2011'),
    ('Tilapia', 'Engorde (>50g)', 0.15, 28.0, 32.0, 3200, 3500, 3, 8, 6, 12, 1.10, 1.60, 0.60, 0.80, 1.50, 0.65, 650, 'NRC 2011'),
    ('Trucha arcoíris', 'Alevín', 0.005, 45.0, 50.0, 3500, 3800, 2, 6, 8, 14, 1.80, 2.20, 1.20, 1.50, 2.40, 1.00, 900, 'NRC 2011'),
    ('Trucha arcoíris', 'Engorde', 0.2, 38.0, 42.0, 3400, 3700, 2, 6, 8, 14, 1.50, 1.90, 1.00, 1.30, 2.10, 0.90, 800, 'NRC 2011'),
    ('Camarón', 'Postlarva-juvenil', 0.001, 35.0, 40.0, 3000, 3300, 3, 7, 6, 10, 2.00, 2.50, 1.50, 1.80, 2.20, 0.90, 700, 'NRC 2011'),
    ('Equino', 'Potro (0-6 meses)', 100, 16.0, 18.0, 2500, 2800, 15, 25, 5, 10, 0.80, 1.20, 0.55, 0.75, 0.70, 0.22, 300, 'NRC 2007'),
    ('Equino', 'Caballo adulto (trabajo)', 550, 10.0, 12.0, 2200, 2600, 20, 35, 4, 8, 0.35, 0.65, 0.22, 0.38, 0.45, 0.15, 200, 'NRC 2007'),
    ('Equino', 'Yegua lactante', 520, 12.5, 14.5, 2400, 2700, 20, 35, 4, 8, 0.45, 0.75, 0.28, 0.45, 0.55, 0.17, 250, 'NRC 2007'),
    ('Perro', 'Cachorro', 5, 28.0, 32.0, 3500, 4000, 2, 5, 8, 15, 1.00, 1.50, 0.75, 1.00, 0.90, 0.35, 1200, 'AAFCO 2023'),
    ('Perro', 'Adulto mantenimiento', 25, 18.0, 22.0, 3500, 4000, 2, 5, 8, 15, 0.60, 1.00, 0.50, 0.75, 0.65, 0.28, 900, 'AAFCO 2023'),
    ('Gato', 'Adulto', 4, 26.0, 30.0, 3500, 4200, 0, 5, 8, 15, 0.60, 1.00, 0.50, 0.75, 0.83, 0.40, 2400, 'AAFCO 2023'),
    ('Conejo', 'Crecimiento', 1, 15.0, 17.0, 2500, 2700, 14, 22, 3, 6, 0.60, 1.00, 0.40, 0.60, 0.65, 0.25, 800, 'NRC 1977'),
    ('Cuy', 'Crecimiento', 0.3, 18.0, 20.0, 2800, 3000, 10, 18, 3, 6, 0.80, 1.20, 0.55, 0.80, 0.84, 0.26, 500, 'NRC 1995'),
]

RESTRICCIONES_DEFAULT = [
    ('melaza', 15.0, 'todos', 'Exceso causa diarrea osmótica', 'Church & Pond 2002'),
    ('harina de pescado', 8.0, 'todos', 'Oxidación lipídica, sabor en carnes y huevos', 'Leeson & Summers 2005'),
    ('gallinaza aves', 10.0, 'bovinos', 'Riesgo de patógenos si no está tratada', 'NRC 2000'),
    ('gallinaza aves', 0.0, 'porcinos', 'Prohibido por bioseguridad en muchos países', 'OIE'),
    ('gallinaza aves', 0.0, 'aves', 'Canibalismo nutricional - prohibido', 'Leeson 2005'),
    ('aceite vegetal', 10.0, 'todos', 'Exceso deprime consumo y altera perfil lipídico', 'NRC 1994'),
    ('harina de sangre', 5.0, 'todos', 'Desequilibra aminoácidos, palatabilidad baja', 'NRC 1994'),
    ('harina de plumas', 5.0, 'todos', 'Baja digestibilidad, AA poco disponibles', 'Leeson 2005'),
    ('bagazo de caña azúcar', 20.0, 'bovinos', 'Dilución excesiva de la dieta', 'NRC 2000'),
    ('sal común (nacl)', 0.5, 'todos', 'Toxicidad por exceso de sodio', 'NRC 1994'),
]


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def inicializar(self):
        conn = self.get_connection()
        try:
            conn.executescript(SCHEMA_SQL)
            self._migrar_bd_v2(conn)
            self._insertar_datos_default(conn)
            self._insertar_requerimientos_default(conn)
            self._insertar_restricciones_default(conn)
            conn.commit()
        finally:
            conn.close()

    def _insertar_datos_default(self, conn):
        for nombre in ANIMALES_DEFAULT:
            conn.execute(
                "INSERT OR IGNORE INTO animales (nombre) VALUES (?)",
                (nombre,)
            )

        for insumo in INSUMOS_DEFAULT + INSUMOS_ADICIONALES:
            conn.execute(
                """INSERT OR IGNORE INTO insumos
                   (nombre, proteina, em_kcal, fibra, grasa, calcio, fosforo,
                    lisina, metionina, colina_mgr, precio_kg, categoria)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                insumo
            )

        for clave, valor in CONFIG_DEFAULT:
            conn.execute(
                "INSERT OR IGNORE INTO config_empresa (clave, valor) VALUES (?,?)",
                (clave, valor)
            )

    def _migrar_bd_v2(self, conn):
        migraciones = [
            "ALTER TABLE insumos ADD COLUMN proveedor TEXT DEFAULT ''",
            "ALTER TABLE insumos ADD COLUMN notas TEXT DEFAULT ''",
            "ALTER TABLE formulaciones ADD COLUMN version INTEGER DEFAULT 1",
            "ALTER TABLE formulaciones ADD COLUMN etiqueta TEXT DEFAULT ''",
            "ALTER TABLE formulaciones ADD COLUMN aprobada INTEGER DEFAULT 0",
            "ALTER TABLE pacientes ADD COLUMN sexo TEXT DEFAULT ''",
        ]
        cursor = conn.cursor()
        for sql in migraciones:
            try:
                cursor.execute(sql)
            except Exception:
                pass
        conn.commit()

    def _insertar_requerimientos_default(self, conn):
        for item in REQUERIMIENTOS_NRC:
            conn.execute(
                """INSERT OR IGNORE INTO tablas_requerimientos
                   (especie, etapa, peso_ref_kg, proteina_min, proteina_max,
                    em_min, em_max, fibra_min, fibra_max, grasa_min, grasa_max,
                    calcio_min, calcio_max, fosforo_min, fosforo_max,
                    lisina_min, metionina_min, colina_min, fuente)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                item
            )

    def _insertar_restricciones_default(self, conn):
        for nombre, tms_pct, especie, motivo, fuente in RESTRICCIONES_DEFAULT:
            cursor = conn.execute(
                "SELECT id FROM insumos WHERE lower(nombre) = lower(?)",
                (nombre,)
            )
            row = cursor.fetchone()
            if not row:
                continue

            conn.execute(
                """INSERT OR IGNORE INTO restricciones_ingredientes
                   (insumo_id, tms_pct, especie_restringida, motivo, fuente_bibliografica)
                   VALUES (?,?,?,?,?)""",
                (row['id'], tms_pct, especie, motivo, fuente)
            )

    def get_config(self, clave):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT valor FROM config_empresa WHERE clave = ?", (clave,)
            )
            row = cursor.fetchone()
            return row['valor'] if row else ''
        finally:
            conn.close()

    def set_config(self, clave, valor):
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO config_empresa (clave, valor) VALUES (?,?)",
                (clave, valor)
            )
            conn.commit()
        finally:
            conn.close()

    def get_all_config(self):
        conn = self.get_connection()
        try:
            cursor = conn.execute("SELECT clave, valor FROM config_empresa")
            return {row['clave']: row['valor'] for row in cursor.fetchall()}
        finally:
            conn.close()

    def get_insumos(self, activo=True):
        conn = self.get_connection()
        try:
            if activo:
                cursor = conn.execute(
                    "SELECT * FROM insumos WHERE activo = 1 ORDER BY nombre"
                )
            else:
                cursor = conn.execute("SELECT * FROM insumos ORDER BY nombre")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_insumo_by_id(self, insumo_id):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM insumos WHERE id = ?", (insumo_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def insertar_insumo(self, datos):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """INSERT INTO insumos
                   (nombre, proteina, em_kcal, fibra, grasa, calcio, fosforo,
                    lisina, metionina, colina_mgr, precio_kg, categoria,
                    proveedor, notas)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    datos['nombre'], datos['proteina'], datos['em_kcal'],
                    datos['fibra'], datos['grasa'], datos['calcio'],
                    datos['fosforo'], datos['lisina'], datos['metionina'],
                    datos['colina_mgr'], datos['precio_kg'], datos['categoria'],
                    datos.get('proveedor', ''), datos.get('notas', '')
                )
            )
            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def actualizar_insumo(self, insumo_id, datos):
        conn = self.get_connection()
        try:
            conn.execute(
                """UPDATE insumos SET
                   nombre=?, proteina=?, em_kcal=?, fibra=?, grasa=?,
                   calcio=?, fosforo=?, lisina=?, metionina=?,
                   colina_mgr=?, precio_kg=?, categoria=?,
                   proveedor=?, notas=?
                   WHERE id=?""",
                (
                    datos['nombre'], datos['proteina'], datos['em_kcal'],
                    datos['fibra'], datos['grasa'], datos['calcio'],
                    datos['fosforo'], datos['lisina'], datos['metionina'],
                    datos['colina_mgr'], datos['precio_kg'], datos['categoria'],
                    datos.get('proveedor', ''), datos.get('notas', ''),
                    insumo_id
                )
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def eliminar_insumo(self, insumo_id):
        conn = self.get_connection()
        try:
            conn.execute("DELETE FROM insumos WHERE id = ?", (insumo_id,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_animales(self):
        conn = self.get_connection()
        try:
            cursor = conn.execute("SELECT * FROM animales ORDER BY nombre")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def insertar_animal(self, nombre):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO animales (nombre) VALUES (?)", (nombre,)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def actualizar_animal(self, animal_id, nombre):
        conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE animales SET nombre = ? WHERE id = ?",
                (nombre, animal_id)
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def eliminar_animal(self, animal_id):
        conn = self.get_connection()
        try:
            conn.execute("DELETE FROM animales WHERE id = ?", (animal_id,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def guardar_formulacion(self, datos, ingredientes):
        conn = self.get_connection()
        try:
            ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor = conn.execute(
                """INSERT INTO formulaciones
                   (nombre, fecha_creacion, fecha_modificacion, animal_id,
                    total_kg, proteina_total, em_total, fibra_total, grasa_total,
                    calcio_total, fosforo_total, lisina_total, metionina_total,
                    colina_total, costo_por_kg, costo_por_tonelada,
                    instrucciones_preparacion, notas_generales, tipo,
                    version, etiqueta, aprobada)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    datos['nombre'], ahora, ahora, datos.get('animal_id'),
                    datos['total_kg'], datos['proteina_total'],
                    datos['em_total'], datos['fibra_total'],
                    datos['grasa_total'], datos['calcio_total'],
                    datos['fosforo_total'], datos['lisina_total'],
                    datos['metionina_total'], datos['colina_total'],
                    datos['costo_por_kg'], datos['costo_por_tonelada'],
                    datos.get('instrucciones', ''),
                    datos.get('notas', ''),
                    datos.get('tipo', 'manual'),
                    datos.get('version', 1),
                    datos.get('etiqueta', ''),
                    datos.get('aprobada', 0)
                )
            )
            form_id = cursor.lastrowid

            for ing in ingredientes:
                conn.execute(
                    """INSERT INTO formulacion_ingredientes
                       (formulacion_id, insumo_id, tanteo_kg, porcentaje,
                        precio_kg, proteina_aportada, em_aportada,
                        fibra_aportada, grasa_aportada, calcio_aportado,
                        fosforo_aportado, lisina_aportada,
                        metionina_aportada, colina_aportada)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        form_id, ing['insumo_id'], ing['tanteo_kg'],
                        ing['porcentaje'], ing['precio_kg'],
                        ing['proteina_aportada'], ing['em_aportada'],
                        ing['fibra_aportada'], ing['grasa_aportada'],
                        ing['calcio_aportado'], ing['fosforo_aportado'],
                        ing['lisina_aportada'], ing['metionina_aportada'],
                        ing['colina_aportada']
                    )
                )

            conn.commit()
            return form_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_formulaciones(self, animal_id=None):
        conn = self.get_connection()
        try:
            if animal_id:
                cursor = conn.execute(
                    """SELECT f.*, a.nombre as animal_nombre
                       FROM formulaciones f
                       LEFT JOIN animales a ON f.animal_id = a.id
                       WHERE f.animal_id = ?
                       ORDER BY f.fecha_modificacion DESC""",
                    (animal_id,)
                )
            else:
                cursor = conn.execute(
                    """SELECT f.*, a.nombre as animal_nombre
                       FROM formulaciones f
                       LEFT JOIN animales a ON f.animal_id = a.id
                       ORDER BY f.fecha_modificacion DESC"""
                )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_formulacion(self, form_id):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """SELECT f.*, a.nombre as animal_nombre
                   FROM formulaciones f
                   LEFT JOIN animales a ON f.animal_id = a.id
                   WHERE f.id = ?""",
                (form_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_formulacion_ingredientes(self, form_id):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """SELECT fi.*, i.nombre as insumo_nombre
                   FROM formulacion_ingredientes fi
                   JOIN insumos i ON fi.insumo_id = i.id
                   WHERE fi.formulacion_id = ?""",
                (form_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def duplicar_formulacion(self, form_id):
        conn = self.get_connection()
        try:
            form = self.get_formulacion(form_id)
            if not form:
                return None
            ingredientes = self.get_formulacion_ingredientes(form_id)

            ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor = conn.execute(
                """INSERT INTO formulaciones
                   (nombre, fecha_creacion, fecha_modificacion, animal_id,
                    total_kg, proteina_total, em_total, fibra_total, grasa_total,
                    calcio_total, fosforo_total, lisina_total, metionina_total,
                    colina_total, costo_por_kg, costo_por_tonelada,
                    instrucciones_preparacion, notas_generales, tipo,
                    version, etiqueta, aprobada)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    f"{form['nombre']} (copia)", ahora, ahora,
                    form['animal_id'], form['total_kg'],
                    form['proteina_total'], form['em_total'],
                    form['fibra_total'], form['grasa_total'],
                    form['calcio_total'], form['fosforo_total'],
                    form['lisina_total'], form['metionina_total'],
                    form['colina_total'], form['costo_por_kg'],
                    form['costo_por_tonelada'],
                    form['instrucciones_preparacion'],
                    form['notas_generales'], form['tipo'],
                    form.get('version', 1) + 1,
                    form.get('etiqueta', ''),
                    0
                )
            )
            nuevo_id = cursor.lastrowid

            for ing in ingredientes:
                conn.execute(
                    """INSERT INTO formulacion_ingredientes
                       (formulacion_id, insumo_id, tanteo_kg, porcentaje,
                        precio_kg, proteina_aportada, em_aportada,
                        fibra_aportada, grasa_aportada, calcio_aportado,
                        fosforo_aportado, lisina_aportada,
                        metionina_aportada, colina_aportada)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        nuevo_id, ing['insumo_id'], ing['tanteo_kg'],
                        ing['porcentaje'], ing['precio_kg'],
                        ing['proteina_aportada'], ing['em_aportada'],
                        ing['fibra_aportada'], ing['grasa_aportada'],
                        ing['calcio_aportado'], ing['fosforo_aportado'],
                        ing['lisina_aportada'], ing['metionina_aportada'],
                        ing['colina_aportada']
                    )
                )

            conn.commit()
            return nuevo_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def eliminar_formulacion(self, form_id):
        conn = self.get_connection()
        try:
            conn.execute("DELETE FROM formulaciones WHERE id = ?", (form_id,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def aprobar_formulacion(self, form_id):
        conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE formulaciones SET aprobada = 1 WHERE id = ?",
                (form_id,)
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def buscar_formulaciones(self, texto, animal_id=None, etiqueta=None, solo_aprobadas=False):
        conn = self.get_connection()
        try:
            condiciones = []
            params = []

            if animal_id:
                condiciones.append("f.animal_id = ?")
                params.append(animal_id)
            if texto:
                condiciones.append("f.nombre LIKE ?")
                params.append(f'%{texto}%')
            if etiqueta:
                condiciones.append("f.etiqueta = ?")
                params.append(etiqueta)
            if solo_aprobadas:
                condiciones.append("f.aprobada = 1")

            where = " AND ".join(condiciones) if condiciones else "1=1"

            cursor = conn.execute(
                f"""SELECT f.*, a.nombre as animal_nombre
                   FROM formulaciones f
                   LEFT JOIN animales a ON f.animal_id = a.id
                   WHERE {where}
                   ORDER BY f.fecha_modificacion DESC""",
                params
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_etiquetas(self):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT DISTINCT etiqueta FROM formulaciones WHERE etiqueta != '' ORDER BY etiqueta"
            )
            return [row['etiqueta'] for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_formulaciones_por_animal_fecha(self):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """SELECT f.*, a.nombre as animal_nombre
                   FROM formulaciones f
                   LEFT JOIN animales a ON f.animal_id = a.id
                   ORDER BY a.nombre, f.fecha_modificacion"""
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_insumos_en_formulaciones(self, insumo_id):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """SELECT DISTINCT f.id, f.nombre, f.fecha_modificacion, a.nombre as animal_nombre
                   FROM formulacion_ingredientes fi
                   JOIN formulaciones f ON fi.formulacion_id = f.id
                   LEFT JOIN animales a ON f.animal_id = a.id
                   WHERE fi.insumo_id = ?
                   ORDER BY f.fecha_modificacion DESC""",
                (insumo_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def guardar_lote(self, datos):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """INSERT INTO lotes
                   (formulacion_id, nombre, fecha, cantidad_kg, costo_total, notas, estado)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    datos.get('formulacion_id'),
                    datos['nombre'],
                    datos.get('fecha', datetime.now().strftime('%Y-%m-%d')),
                    datos['cantidad_kg'],
                    datos.get('costo_total', 0),
                    datos.get('notas', ''),
                    datos.get('estado', 'producido')
                )
            )
            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_lotes(self, animal_id=None, estado=None, mes=None):
        conn = self.get_connection()
        try:
            query = """SELECT l.*, f.nombre as formulacion_nombre, a.nombre as animal_nombre
                       FROM lotes l
                       LEFT JOIN formulaciones f ON l.formulacion_id = f.id
                       LEFT JOIN animales a ON f.animal_id = a.id
                       WHERE 1=1"""
            params = []

            if animal_id:
                query += " AND f.animal_id = ?"
                params.append(animal_id)
            if estado:
                query += " AND l.estado = ?"
                params.append(estado)
            if mes:
                query += " AND strftime('%Y-%m', l.fecha) = ?"
                params.append(mes)

            query += " ORDER BY l.fecha DESC"

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def actualizar_estado_lote(self, lote_id, estado):
        conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE lotes SET estado = ? WHERE id = ?",
                (estado, lote_id)
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def eliminar_lote(self, lote_id):
        conn = self.get_connection()
        try:
            conn.execute("DELETE FROM lotes WHERE id = ?", (lote_id,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_resumen_mensual(self):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """SELECT strftime('%Y-%m', fecha) as mes,
                          COUNT(*) as lotes,
                          SUM(cantidad_kg) as kg_totales,
                          SUM(costo_total) as costo_total,
                          CASE WHEN SUM(cantidad_kg) > 0 THEN SUM(costo_total) / SUM(cantidad_kg) ELSE 0 END as costo_promedio
                   FROM lotes
                   GROUP BY mes
                   ORDER BY mes DESC"""
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_requerimientos(self, especie=None, etapa=None):
        conn = self.get_connection()
        try:
            query = "SELECT * FROM tablas_requerimientos WHERE 1=1"
            params = []
            if especie:
                query += " AND especie = ?"
                params.append(especie)
            if etapa:
                query += " AND etapa = ?"
                params.append(etapa)
            query += " ORDER BY especie, etapa"
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def guardar_requerimiento(self, datos):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """INSERT INTO tablas_requerimientos
                   (especie, etapa, peso_ref_kg, proteina_min, proteina_max,
                    em_min, em_max, fibra_min, fibra_max, grasa_min, grasa_max,
                    calcio_min, calcio_max, fosforo_min, fosforo_max,
                    lisina_min, metionina_min, colina_min, fuente, notas)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    datos['especie'], datos['etapa'], datos.get('peso_ref_kg', 0),
                    datos.get('proteina_min', 0), datos.get('proteina_max', 0),
                    datos.get('em_min', 0), datos.get('em_max', 0),
                    datos.get('fibra_min', 0), datos.get('fibra_max', 0),
                    datos.get('grasa_min', 0), datos.get('grasa_max', 0),
                    datos.get('calcio_min', 0), datos.get('calcio_max', 0),
                    datos.get('fosforo_min', 0), datos.get('fosforo_max', 0),
                    datos.get('lisina_min', 0), datos.get('metionina_min', 0),
                    datos.get('colina_min', 0), datos.get('fuente', 'usuario'),
                    datos.get('notas', ''),
                )
            )
            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_restricciones_ingredientes(self, especie=None):
        conn = self.get_connection()
        try:
            query = """SELECT r.*, i.nombre AS insumo_nombre
                       FROM restricciones_ingredientes r
                       JOIN insumos i ON i.id = r.insumo_id
                       WHERE 1=1"""
            params = []
            if especie:
                query += " AND (lower(r.especie_restringida) = lower(?) OR lower(r.especie_restringida) = 'todos')"
                params.append(especie)
            query += " ORDER BY i.nombre"
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_pacientes(self, especie=None, estado=None, texto=''):
        conn = self.get_connection()
        try:
            query = "SELECT * FROM pacientes WHERE 1=1"
            params = []
            if especie:
                query += " AND especie = ?"
                params.append(especie)
            if estado:
                query += " AND estado = ?"
                params.append(estado)
            if texto:
                query += " AND (nombre LIKE ? OR propietario LIKE ?)"
                like = f"%{texto}%"
                params.extend([like, like])
            query += " ORDER BY nombre"
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def guardar_paciente(self, datos):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """INSERT INTO pacientes
                   (nombre, especie, raza, sexo, edad_meses, peso_kg,
                    condicion_corporal, estado, propietario, fecha_ingreso,
                    notas_clinicas, animal_id)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    datos['nombre'], datos['especie'], datos.get('raza', ''),
                    datos.get('sexo', ''), datos.get('edad_meses', 0),
                    datos.get('peso_kg', 0), datos.get('condicion_corporal', 3),
                    datos.get('estado', 'activo'), datos.get('propietario', ''),
                    datos.get('fecha_ingreso', datetime.now().strftime('%Y-%m-%d')),
                    datos.get('notas_clinicas', ''), datos.get('animal_id'),
                )
            )
            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_seguimiento_paciente(self, paciente_id):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """SELECT s.*, f.nombre AS formulacion_nombre
                   FROM seguimiento_nutricional s
                   LEFT JOIN formulaciones f ON f.id = s.formulacion_id
                   WHERE s.paciente_id = ?
                   ORDER BY s.fecha""",
                (paciente_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def agregar_seguimiento_paciente(self, datos):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """INSERT INTO seguimiento_nutricional
                   (paciente_id, formulacion_id, fecha, peso_kg, condicion_corporal,
                    consumo_real_kg, observaciones, ajuste_recomendado)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    datos['paciente_id'], datos.get('formulacion_id'),
                    datos.get('fecha', datetime.now().strftime('%Y-%m-%d')),
                    datos.get('peso_kg', 0), datos.get('condicion_corporal', 3),
                    datos.get('consumo_real_kg', 0), datos.get('observaciones', ''),
                    datos.get('ajuste_recomendado', ''),
                )
            )
            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
