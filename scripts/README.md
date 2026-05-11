# scripts/ — Utilitarios de Desarrollo

Esta carpeta contiene scripts auxiliares para **diagnóstico y configuración local**.
No forman parte de la aplicación en producción.

| Archivo | Propósito |
|---------|-----------|
| `ver_datos.py` | Inspecciona usuarios y auditorías registradas en `datalake_local/talon_metastore.duckdb`. Útil para debug local. |
| `ver_modelos.py` | Lista los modelos de Gemini disponibles para `generateContent`. Útil para validar la API Key y elegir modelo. |
| `GeneralOAuthFlow.py` | Prototipo de autenticación OAuth 2.0 con Google Workspace (`streamlit_google_auth`). Pendiente de integración cuando el equipo de TI habilite el cliente OAuth corporativo. |

## Uso

Ejecutar desde la raíz del proyecto:

```bash
python scripts/ver_datos.py
python scripts/ver_modelos.py
```

> Requieren que `datalake_local/` exista (generado al correr la app al menos una vez) y que `GEMINI_API_KEY` esté en `.streamlit/secrets.toml`.
