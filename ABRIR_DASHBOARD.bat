@echo off
echo ========================================================
echo   Iniciando Suite Vendimia 5.0 - Objetivo 3
echo ========================================================
echo.

:: Cambiar al directorio raíz del proyecto
cd /d "%~dp0"

set CONDA_PATH=%USERPROFILE%\AppData\Local\miniconda3

if not exist "%CONDA_PATH%\envs\vendimia_obj3\python.exe" (
    echo [ERROR] No se encontro el entorno 'vendimia_obj3'.
    echo Por favor, asegurate de haber corrido INSTALAR_ENTORNO.bat primero.
    pause
    exit /b
)

echo 1) Abriendo la Suite Central (HTML) en tu navegador...
start "" "reports\dashboards_html\index.html"

echo.
echo 2) Levantando Servidor Gradio local...
echo (Manten esta ventana abierta mientras usas el dashboard. Si la cierras, el servidor se apagara)
echo.

:: Activar entorno y ejecutar python en la misma ventana
call "%CONDA_PATH%\Scripts\activate.bat" vendimia_obj3
python "reports\run_gradio_dashboard.py"

echo.
echo [AVISO] El servidor se ha detenido o ha ocurrido un error.
pause
