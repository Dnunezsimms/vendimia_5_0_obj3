@echo off
echo ========================================================
echo   Iniciando Suite Vendimia 5.0 - Objetivo 3
echo ========================================================
echo.
echo 1) Levantando Servidor Gradio en segundo plano (Puerto 7860)...
start "Servidor Gradio Obj3" /min "C:\Users\dnunezs\AppData\Local\miniconda3\envs\vendimia_obj3\python.exe" "C:\projects\vendimia_5_0_obj3_clean\reports\run_gradio_dashboard.py"

echo 2) Abriendo la Suite Central (HTML) en tu navegador...
timeout /t 3 /nobreak >nul
start "" "C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\index.html"

echo.
echo Listo. Puedes cerrar esta ventana.
exit
