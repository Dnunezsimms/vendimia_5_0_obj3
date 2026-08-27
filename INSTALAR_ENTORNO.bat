@echo off
echo ========================================================
echo   Instalador de Entorno - Suite Vendimia 5.0
echo ========================================================
echo.

cd /d "%~dp0"
set CONDA_PATH=%USERPROFILE%\AppData\Local\miniconda3

if not exist "%CONDA_PATH%\Scripts\conda.exe" (
    echo [ERROR] No se encontro Miniconda en %CONDA_PATH%.
    echo Asegurate de haber instalado Miniconda para tu usuario.
    pause
    exit /b
)

echo 1) Creando entorno Conda 'vendimia_obj3' con Python 3.11...
call "%CONDA_PATH%\Scripts\conda.exe" create -n vendimia_obj3 python=3.11 -y

echo.
echo 2) Instalando dependencias desde requirements.txt...
call "%CONDA_PATH%\Scripts\conda.exe" run -n vendimia_obj3 pip install -r models\dashboard_obj3_integrado\requirements.txt

echo.
echo ========================================================
echo   Instalacion Completa. 
echo   Ya puedes ejecutar ABRIR_DASHBOARD.bat
echo ========================================================
pause
exit
