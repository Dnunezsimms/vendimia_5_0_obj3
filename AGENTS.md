# AGENTS.md — Protocolo Estricto para Agentes IA

1. **Estado del Repositorio:** Este repositorio ya funciona localmente de forma canónica. No intente refactorizaciones estructurales masivas.
2. **Prohibido git add .:** Realice exclusivamente staging controlado por rutas explícitas aprobadas. No versionar carpetas temporales, logs ni reportes obsoletos.
3. **Cero Datos Sintéticos:** No invente ni introduzca datos ficticios, placebos o simulaciones climáticas/fenológicas en las carpetas de datos.
4. **Integridad del Dashboard:** No modifique config.py, loaders.py o plots.py sin verificar localmente la hidratación completa del dashboard en Gradio (pp.py).
5. **Bloque Frío Dinámico:** No ejecute chill_dynamic.py dando por cerrado el cálculo de frío hasta verificar la presencia real de los 7/7 fundos horarios (DataVid + Zentra manual + INIA manual).
6. **Despliegue Web Bloqueado:** No modifique ni prepare integraciones para Vercel, Neon PostgreSQL ni interfaces web externas todavía.
7. **Seguridad Absoluta:** Prohibido versionar archivos .env, claves de API (DATAVID_API_KEY) o cualquier secreto.
