@echo off
title Vendimia 5.0 - Dashboard Obj3
cd /d "%~dp0"

echo ==========================================================
echo    Iniciando Servidor del Dashboard Integrado Obj. 3...
echo ==========================================================
echo.
echo Carga de modelos y tablas pesadas en progreso...
echo Por favor no cierres esta ventana negra mientras utilices el dashboard.
echo.

:: Abrir la pagina de espera/acceso en segundo plano tras 3 segundos
start /b cmd /c "timeout /t 3 /nobreak >nul & start "" "%~dp0ACCESO_DASHBOARD.html""

:: Lanzar motor python
if exist "%LOCALAPPDATA%\miniconda3\envs\vendimia_obj3\python.exe" (
    "%LOCALAPPDATA%\miniconda3\envs\vendimia_obj3\python.exe" -m models.dashboard_obj3_integrado.app
) else if exist "%USERPROFILE%\miniconda3\envs\vendimia_obj3\python.exe" (
    "%USERPROFILE%\miniconda3\envs\vendimia_obj3\python.exe" -m models.dashboard_obj3_integrado.app
) else (
    python -m models.dashboard_obj3_integrado.app
)

pause
