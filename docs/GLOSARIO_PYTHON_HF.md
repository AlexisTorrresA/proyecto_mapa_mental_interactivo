# Atlas IA — Glosario Python y modelos Hugging Face

## Alcance implementado

La vista **Atlas IA** incluye cuatro pestañas: mapa de conceptos, glosario Python, modelos Hugging Face y estadísticas. Conserva los **map_nodes/map_edges originales**; no migra ni elimina conceptos anteriores.

- **79 librerías** catalogadas por especialidad, con descripción, documentación oficial, instalación, 395 métodos/clases descritos y un código de ejemplo específico por librería.
- **46 modelos de referencia iniciales**, más los modelos mejor posicionados por descargas en **14 categorías** del Hub (texto, clasificación, traducción, embeddings, reranking, visión, detección, multimodal, OCR, voz, síntesis, audio, imagen y video). Tras cada sincronización aparecen también nuevos modelos descubiertos mediante la API.
- **Metadatos verificables** desde la API del Hub: descargas aproximadas en los últimos 30 días, likes, licencia, tipo de acceso, tarea, librería, fecha de actualización, número de parámetros declarado mediante safetensors.total y claves de configuración documentadas.
- **Ejemplos técnicos** de inferencia por tarea; los laboratorios de texto, clasificación y embeddings permiten variar parámetros que modifican el código generado, sin descargar ni ejecutar pesos grandes en Y700.
- **PostgreSQL**: tablas separadas catalog_items/catalog_meta, con carga de datos idempotente. Los datos existentes en map_nodes y map_edges permanecen intactos. La sincronización API reemplaza solo metadatos de modelos verificados y conserva la última versión válida ante errores de red.

## Actualización

En la aplicación: **Atlas IA → Modelos Hugging Face → Actualizar modelos, estadísticas y arquitectura**.

Desde el contenedor, para automatizar una actualización programada con los secretos del Y700:

    docker exec y700-mapa-mental python scripts/sync_hf.py --per-category 10

La sincronización usa únicamente el API público de lectura, sin necesidad de API key. Son aproximadamente 14 consultas de listas más una consulta individual por modelo (las peticiones son paralelas, con timeouts). El límite de 260 modelos protege la memoria y el tiempo. Si el Hub aplica rate limiting, los modelos ya validados conservan sus métricas previas; los no validados se muestran con métricas «Sin datos» y no con valores ficticios.

**Precauciones:** los parámetros que figuran en un nombre de modelo no equivalen a su total exacto de pesos; se muestra solo el total declarado por Hugging Face. Los permisos de descarga y ejecución dependen de licencia, autorización gated, librerías, hardware y memoria. Las llamadas a Hugging Face no ejecutan código remoto y la aplicación no ejecuta los snippets que muestra.

## Verificación y pruebas

    pip install -r requirements.txt
    pytest -q
    python -m compileall -q mapa_mental.py atlas_ia.py catalog_store.py catalog_ui.py knowledge_catalog.py scripts tests

Datos persistidos:

    SELECT kind, COUNT(*) FROM catalog_items GROUP BY kind;
    SELECT value FROM catalog_meta WHERE key='huggingface_last_sync';

El workflow .github/workflows/publish-image.yml ejecuta pruebas antes de publicar la imagen ghcr.io/alexistorrresa/mapa-mental:main.
