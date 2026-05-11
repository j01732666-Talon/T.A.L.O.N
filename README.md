# T.A.L.O.N. — Tactical Audit & Learning Operations Network

**Plataforma de Auditoría Inteligente de Datos Maestros para Brinsa S.A.**

T.A.L.O.N. es un sistema interactivo que perfiladistribuciones, evalúa la salud y detecta anomalías en datos maestros SAP (Maestro de Materiales, Directorio Comercial) basándose en las cinco dimensiones de calidad de **DAMA DMBOK**: Completitud, Validez, Unicidad, Consistencia y Exactitud.

---

## Características Implementadas

### Autenticación y Seguridad
- Login corporativo con restricción de dominio `@brinsa.com.co`
- Contraseñas cifradas con `bcrypt` almacenadas en DuckDB local
- Registro de accesos con trazabilidad completa de sesiones
- Interfaz de login animada con identidad visual corporativa (logo T.A.L.O.N. + logo Brinsa)

### Integración con BigQuery (TalonDB)
- Extracción incremental (delta): solo carga registros nuevos de `VW_MAESTRO_MATERIALES` que no existen en `Materiales_TALONBD`
- Consulta de anomalías activas (`Estado_Gestion = 0`) sin duplicados mediante `EXISTS`
- Carga masiva (*bulk insert*) de resultados de auditoría vía `WRITE_APPEND`
- Pre-inicialización automática del tablero al abrir la aplicación (sin clic manual)

### Motor de Calidad (Polars + Pandas)
- Cálculo de scores por dimensión (Completitud, Validez, Unicidad, Consistencia)
- Score Global de Salud ponderado por dimensión
- Detección de falsos positivos (valores `"nan"`, cadenas vacías, etc.)
- Procesamiento ultrarrápido de grandes volúmenes con Apache Arrow / Polars

### Inteligencia Artificial (Google Gemini 2.5 Flash)
- **Auto-perfilamiento**: análisis autónomo del dataset para proponer reglas de calidad estructuradas
- **Agente Conversacional**: interfaz de chat en lenguaje natural con *Parallel Function Calling* para crear, editar y actualizar múltiples reglas simultáneamente
- Reglas persistentes en `st.session_state` con indicadores visuales de actualización reciente

### Dashboard y UX
- Interfaz futurista animada (fondo grid + partículas + efecto glitch en título)
- Favicon personalizado (cuervo T.A.L.O.N.)
- Métricas pre-inicializadas en cero cuando no hay datos
- Pestañas: Explorador de anomalías · Dashboard de métricas · Asistente IA · Historial
- Filtros dinámicos por categoría de material
- Gráficas de Calidad por Dimensión y Top Anomalías Detectadas
- Historial de auditorías con scores y metadatos

### Exportación y Notificaciones
- Exportación de saneamiento a `.xlsx` directamente desde el navegador
- Notificación por correo electrónico al Custodio de Datos con:
  - Reporte HTML con identidad Brinsa (score, dominio, registros a sanear)
  - Excel de saneamiento adjunto
  - SMTP SSL Gmail (puerto 465) configurado en `secrets.toml`

---

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend / UI | Streamlit 1.x |
| Procesamiento | Polars · Pandas · Apache Arrow |
| Base de datos local | DuckDB |
| Base de datos cloud | Google BigQuery |
| Inteligencia Artificial | Google Gemini 2.5 Flash (`google-generativeai`) |
| Autenticación | bcrypt · DuckDB |
| Notificaciones | smtplib SMTP SSL (Gmail) |
| Contenedorización | Docker (Python 3.12-slim) |

---

## Estructura del Proyecto

```
.
├── .streamlit/
│   └── secrets.toml          # Credenciales (no versionado — ver .gitignore)
├── src/
│   ├── app.py                # Punto de entrada Streamlit (login + tema)
│   ├── Dashboard.py          # Tablero principal (post-login)
│   ├── config.py             # Variables globales, catálogos, configuración IA
│   ├── core/
│   │   ├── motor_calidad.py  # Motor de scoring y evaluación DAMA DMBOK
│   │   ├── motor_ia.py       # Agente conversacional + auto-perfilamiento
│   │   └── herramientas_ia.py# Utilidades de acceso a datos para la IA
│   ├── infra/
│   │   ├── bigquery_client.py# Extracción incremental + bulk insert BigQuery
│   │   ├── datalake_manager.py# Historial local de auditorías (DuckDB)
│   │   ├── auth_manager.py   # Registro, login y trazabilidad de usuarios
│   │   └── notificador.py    # Envío de correos SMTP con reporte adjunto
│   └── ui/
│       ├── theme.py          # CSS global + animaciones + inyección de estilos
│       ├── ui_components.py  # Componentes reutilizables (métricas, gráficas)
│       ├── crow_logo.svg     # Logo T.A.L.O.N. (cuervo)
│       └── brinsa_logo.png   # Logo Brinsa para el login
├── scripts/                  # Utilitarios de desarrollo (no son parte de la app)
│   ├── ver_datos.py          # Inspecciona DuckDB local
│   ├── ver_modelos.py        # Lista modelos Gemini disponibles
│   └── GeneralOAuthFlow.py   # Prototipo OAuth 2.0 Google Workspace (pendiente)
├── Dockerfile
├── requirements.txt
├── .gitignore
└── Diccionario_CDEs_TALON.md # Diccionario de datos y definición de CDEs
```

---

## Instalación y Ejecución Local

### Requisitos
- Python 3.12+
- Archivo `credenciales_gcp.json` en la raíz (cuenta de servicio BigQuery)
- Archivo `.streamlit/secrets.toml` configurado (ver plantilla abajo)

### Pasos

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd "Auditoría de Calidad V.5 AI"

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar secrets
# Editar .streamlit/secrets.toml (ver sección de Configuración)

# 4. Ejecutar
streamlit run src/app.py
```

### Plantilla de `secrets.toml`

```toml
GEMINI_API_KEY  = "<tu-api-key-de-google-ai-studio>"
dominio_empresa = "@brinsa.com.co"

[smtp_email]
correo   = "<correo-del-bot-gmail>"
password = "<app-password-de-16-caracteres>"

[theme]
primaryColor = "#001689"
```

> Para generar un App Password de Gmail: Cuenta Google → Seguridad → Verificación en 2 pasos → Contraseñas de aplicaciones.

---

## Ejecución con Docker

```bash
docker build -t talon-app .
docker run -p 8501:8501 \
  -v $(pwd)/.streamlit:/app/.streamlit \
  -v $(pwd)/credenciales_gcp.json:/app/credenciales_gcp.json \
  talon-app
```

---

## Roadmap

| Fase | Estado | Descripción |
|------|--------|-------------|
| Auth corporativa | Pendiente | OAuth 2.0 con Google Workspace (prototipo en `scripts/GeneralOAuthFlow.py`) |
| SSO BigQuery incremental | Activo | Extracción delta + bulk insert operativos |
| Microservicios | Pendiente | Desacoplamiento Frontend / Backend para auditorías asíncronas de alta escala |
| Integración ITSM (CLIC) | Pendiente | Creación automática de tickets cuando score < umbral mínimo |
| Remediación SAP Inbound | Pendiente | Aplicación de correcciones aprobadas vía RFC/OData directamente en el ERP |
| Bucle ReAct autónomo | Pendiente | Agente IA que estructura y envía remediaciones al flujo Inbound SAP |

---

*Diseñado por Jose Miguel Muñoz Ríos — construido para transformar el Gobierno de Datos corporativo en Brinsa S.A.*
