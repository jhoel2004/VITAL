@echo off
chcp 65001 > nul
echo ========================================
echo   VITAL v2.0 - Build Windows
echo ========================================

pip install -r requirements.txt --quiet

pyinstaller ^
    --onefile ^
    --windowed ^
    --name="VITAL" ^
    --hidden-import=scipy.optimize ^
    --hidden-import=scipy.optimize._linprog ^
    --hidden-import=numpy ^
    --hidden-import=matplotlib.backends.backend_qt5agg ^
    --hidden-import=openpyxl ^
    --hidden-import=reportlab ^
    main.py

echo.
echo Build completado: dist/VITAL.exe
pause
