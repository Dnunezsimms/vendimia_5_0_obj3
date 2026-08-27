@echo off
echo ========================================================
echo   Iniciando Suite Vendimia 5.0 - Objetivo 3
echo ========================================================
echo.

:: Cambiar al directorio raÃ­z del proyecto (donde estÃ¡ el .bat)
cd /d "%~dp0"

:: Encontrar Conda dinÃ¡micamente en el perfil del usuario actual (funciona para Diego y Sergio)
set CONDA_PATH=%USERPROFILE%\AppData\Local\miniconda3

:: Verificar si el entorno vendimia_obj3 existe
if not exist "%CONDA_PATH%\envs\vendimia_obj3\python.exe" (
    echo [ERROR] No se encontro el entorno 'vendimia_obj3' en %CONDA_PATH%\envs\
    echo Por favor, asegurate de haber creado el entorno Conda o instalalo.
    pause
    exit /b
)

echo 1) Levantando Servidor Gradio en segundo plano (Puerto 7860)...
start "Servidor Gradio Obj3" cmd /k "%CONDA_PATH%\envs\vendimia_obj3\python.exe" "reports\run_gradio_dashboard.py"

echo 2) Abriendo la Suite Central (HTML) en tu navegador...
timeout /t 3 /nobreak >nul
start "" "reports\dashboards_html\index.html"

echo.
echo Listo. Puedes cerrar esta ventana.
exit

