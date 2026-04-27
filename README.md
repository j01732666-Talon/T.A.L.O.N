# 🐦‍⬛ T.A.L.O.N. - Data Quality & Profiling Agent

Asistente Inteligente para la Auditoría y Saneamiento de Datos Maestros (SAP)

T.A.L.O.N. es una plataforma interactiva diseñada para perfilar, evaluar y corregir anomalías en datos maestros (Maestro de Materiales, Directorio Comercial) basándose en las dimensiones de calidad de **DAMA DMBOK** (Completitud, Validez, Unicidad, Consistencia).

Integra un motor de procesamiento de datos ultrarrápido con Inteligencia Artificial Generativa para crear reglas de negocio dinámicas y adaptables en tiempo real.

---

## 🚀 Características Principales (Current MVP)

* **Extracción y Lectura Segura:** Ingesta de archivos `.xlsx` (Ej. extracciones SAP `MARA/MARC`, `KNA1`, `LFA1`) con mecanismos de *fallback* para lectura dinámica de pestañas.
* **Motor Matemático (Polars/Pandas):** Cálculos estadísticos y perfilamiento profundo en segundos, atrapando falsos positivos (como los valores "nan").
* **IA Autónoma (Google Gemini 2.5 Pro):** Análisis de radiografías de datos para proponer reglas de calidad estructuradas sin intervención humana.
* **Consultor IA en Tiempo Real (Agente):** Interfaz conversacional tipo Chat donde el usuario puede dar órdenes en lenguaje natural. La IA utiliza **Parallel Function Calling** para crear, editar o actualizar múltiples reglas condicionales al mismo tiempo.
* **Dashboard Dinámico y UX:**
  * Recálculo en tiempo real de los *scores* de salud (Salud Global, Completitud, Validez, etc.).
  * Visualizador interactivo de reglas mediante acordeones que resalta automáticamente en verde (`✨ [ACTUALIZADO]`) las modificaciones recientes hechas por la IA.
* **Exportación y Notificación:** División automatizada de hallazgos en hojas de Excel y generación de correos electrónicos de alerta para los Custodios de Datos.

---

## 🏗️ Arquitectura y Stack Tecnológico

* **Frontend / UI:** [Streamlit](https://streamlit.io/) (Python)
* **Procesamiento de Datos:** Pandas & Polars (Optimizados para grandes volúmenes de registros).
* **Inteligencia Artificial:** Google Generative AI SDK (`gemini-2.5-pro`).
* **Formatos de Intercambio:** JSON (Gestión de reglas en memoria `st.session_state` y almacenamiento en bóveda "Prime").

---

## 🗺️ Roadmap de Integración (Próximos Pasos y Fases)

Basado en el diagrama de arquitectura corporativa actual, la evolución del sistema para romper el monolito y escalar hacia la nube contempla los siguientes hitos de desarrollo técnico:
Fase 1: Blindaje Corporativo y Base de Datos
[Seguridad] Single Sign-On (SSO): Integración de Autenticación OAuth 2.0 con Google Workspace para restringir el acceso por dominio corporativo y auditar las sesiones y acciones de los usuarios en el sistema.
[Data Lake] Integración con BigQuery (TALONBD): Transición del almacenamiento local a la nube mediante la lectura directa de vistas SAP y la escritura del historial de calidad en GCP. (Estado actual: En gestión técnica, a la espera de que el equipo de Infraestructura/TI habilite el entorno de la base de datos y asigne los permisos).
Fase 2: Escalamiento en la Nube
[Arquitectura] Procesos Dinámicos y Microservicios: Desacoplamiento del monolito actual (separando el Frontend en Streamlit del Backend de procesamiento) para ejecutar análisis incrementales (evaluación exclusiva de Deltas/registros nuevos), optimizando drásticamente los costos de cómputo y consumo de IA.
Fase 3: Automatización Operativa
[Automatización] Conexión ITSM (CLIC): Creación automática de tickets de gestión de incidentes y requerimientos cuando los scores de calidad de un dominio caigan por debajo del umbral mínimo permitido, alertando a las mesas de ayuda de datos.
Fase 4: Autonomía y Bucle de Remediación
[Saneamiento] Conexión SAP Inbound: Desarrollo de scripts de carga y actualización (vía RFC/OData) para aplicar las correcciones aprobadas por los custodios directamente en el ERP, sin intervención manual de digitación.
Habilitación del Bucle ReAct: Aprovechar la arquitectura de microservicios para que los agentes de Inteligencia Artificial puedan estructurar la remediación de forma autónoma y enviarla al flujo Inbound de SAP una vez sea validada.

---

Diseñado por Jose Miguel Muñoz Ríos y construido para revolucionar el Gobierno de Datos corporativo.
