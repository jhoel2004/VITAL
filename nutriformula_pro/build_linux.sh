#!/bin/bash
set -e
echo "========================================"
echo "  VITAL v2.0 - Build Linux"
echo "========================================"

pip install -r requirements.txt

pyinstaller \
    --onefile \
    --windowed \
    --name="VITAL" \
    --hidden-import=scipy.optimize \
    --hidden-import=scipy.optimize._linprog \
    --hidden-import=numpy \
    --hidden-import=matplotlib.backends.backend_qt5agg \
    --hidden-import=openpyxl \
    --hidden-import=reportlab \
    main.py

chmod +x dist/VITAL
echo ""
echo "Build completado: dist/VITAL"
