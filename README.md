# 🦅 T.A.L.O.N. - Data Quality & Profiling Agent
**Asistente Inteligente para la Auditoría y Saneamiento de Datos Maestros (SAP)**

T.A.L.O.N. es una plataforma interactiva diseñada para perfilar, evaluar y corregir anomalías en datos maestros (Maestro de Materiales, Directorio Comercial) basándose en las dimensiones de calidad de **DAMA DMBOK** (Completitud, Validez, Unicidad, Consistencia). 

Integra un motor de procesamiento de datos ultrarrápido con Inteligencia Artificial Generativa para crear reglas de negocio dinámicas y adaptables en tiempo real.

---

## 🚀 Características Principales (Current MVP)

* **Extracción y Lectura Segura:** Ingesta de archivos `.xlsx` (Ej. extracciones SAP `MARA/MARC`, `KNA1`, `LFA1`) con mecanismos de *fallback* para lectura dinámica de pestañas.
* **Motor Matemático (Polars/Pandas):** Cálculos estadísticos y perfilamiento profundo en segundos, atrapando falsos positivos (como los valores "nan").
* **IA Autónoma (Google Gemini 1.5 Pro):** Análisis de radiografías de datos para proponer reglas de calidad estructuradas sin intervención humana.
* **Consultor IA en Tiempo Real (Agente):** Interfaz conversacional tipo Chat donde el usuario puede dar órdenes en lenguaje natural. La IA utiliza **Parallel Function Calling** para crear, editar o actualizar múltiples reglas condicionales al mismo tiempo.
* **Dashboard Dinámico y UX:** * Recálculo en tiempo real de los *scores* de salud (Salud Global, Completitud, Validez, etc.).
  * Visualizador interactivo de reglas mediante acordeones que resalta automáticamente en verde (`✨ [ACTUALIZADO]`) las modificaciones recientes hechas por la IA.
* **Exportación y Notificación:** División automatizada de hallazgos en hojas de Excel y generación de correos electrónicos de alerta para los Custodios de Datos.

---

## 🏗️ Arquitectura y Stack Tecnológico

* **Frontend / UI:** [Streamlit](https://streamlit.io/) (Python)
* **Procesamiento de Datos:** Pandas & Polars (Optimizados para grandes volúmenes de registros).
* **Inteligencia Artificial:** Google Generative AI SDK (`gemini-1.5-pro`).
* **Formatos de Intercambio:** JSON (Gestión de reglas en memoria `st.session_state` y almacenamiento en bóveda "Prime").

---

## 🗺️ Roadmap de Integración (Próximos Pasos)

Basado en el diagrama de arquitectura corporativa, los siguientes hitos de desarrollo son:

1. **[Seguridad] Single Sign-On (SSO):** Integración de Autenticación OAuth 2.0 con Google Workspace para restringir acceso por dominio y auditar sesiones de usuarios.
2. **[Datalake] Integración con BigQuery:** Lectura directa de vistas de datos SAP y escritura histórica de resultados (TALONBD) usando credenciales de GCP.
3. **[Automatización] Conexión ITSM (CLIC):** Creación automática de tickets de gestión de incidentes cuando los scores caigan por debajo del umbral permitido.
4. **[Saneamiento] Conexión SAP Inbound:** Desarrollo de scripts de carga (vía RFC/OData) para aplicar las correcciones aprobadas directamente en el ERP sin intervención manual.

---

*Diseñado y construido para revolucionar el Gobierno de Datos corporativo.*