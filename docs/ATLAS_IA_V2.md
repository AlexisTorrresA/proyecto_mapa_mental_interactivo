# Atlas IA — evolución del mapa conceptual

## Alcance implementado (primera fase)
- Nueva vista Atlas (seleccionable desde la navegación Streamlit) para explorar la base de datos PostgreSQL existente.
- Foco en conceptos, límite configurable de nodos, niveles de expansión, búsqueda y panel educativo.
- Fichas reutilizando los atributos actuales `title`, `examples`, `functions`, `code_example`, `year`, `url`.
- Enlaces opcionales futuros en JSON: `github_url`, `notebook_url`, `article_url` y `resources: [{title,url}]`.
- Cronología exploratoria de conceptos con año conocido.
- Sin migración destructiva y sin cambiar el deployment Y700/PG existente.

## Próxima fase
1. Integrar selección de nodos mediante componente bidireccional (el PyVis embebido actual no informa del click a Streamlit).
2. Editor visual de relaciones, fuentes bibliográficas con fecha de aparición verificada.
3. Laboratorios interactivos aislados en sandbox con control de recursos, sin ejecutar código arbitrario del contenido.
4. Vista 3D opcional WebGL/Three.js con fallback 2D accesible y optimizado para móvil.
5. Completar glosario IA/ML/Deep Learning/LLMs/RAG/agentes/robótica/visión/voz e historial verificable.
6. Vista de previsualización de enlaces con metadatos obtenidos en backend, controles SSRF y caché (no confiar en HTML externo).
7. Diseñar nueva SPA React Flow/Sigma.js si la navegación supera las capacidades de Streamlit.

No asumir que un año histórico es fecha exacta de invención; distinguir propuesta, publicación y popularización, siempre con fuente.
