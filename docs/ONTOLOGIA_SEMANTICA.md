# Ontología semántica del Atlas IA

## Diagnóstico de la base original

701 nodos; 696 relaciones; 22 componentes desconectados. Clases predominantes de relación: usa (210), incluye (194), agrupa (154), consulta (67), usa datos (64), relaciona (7). Faltaban fichas de aprendizaje supervisado, no supervisado, por refuerzo, sobreajuste y precisión. La única raíz principal era IA; los otros cinco dominios estaban parcialmente desconectados. 154 contenedores de recursos ocultaban la estructura educativa.

## Estructura educativa añadida

Atlas del conocimiento > Inteligencia Artificial > Machine Learning.

- Paradigmas: supervisado, no supervisado, por refuerzo, autosupervisado y semisupervisado.
- Tareas: clasificación, regresión, clustering, reducción de dimensiones, anomalías y decisiones secuenciales.
- Modelos: árboles, SVM, redes, boosting, K-means, DBSCAN, Q-learning y más.
- Preparación: particiones, validación, normalización, regularización y optimización.
- Evaluación: métricas de clasificación, regresión, clustering y aprendizaje por refuerzo.
- Generalización y riesgos: sobreajuste, subajuste, fuga de datos, deriva y desbalance.

Un concepto tiene UN padre en el árbol de lectura, pero puede tener muchos vínculos transversales:
Sobreajuste — afecta a → supervisado / no supervisado / refuerzo.
Regularización — mitiga → sobreajuste.
Precision (TP/(TP+FP)) — evalúa → clasificación.
Accuracy — evalúa → clasificación (no es sinónimo de precision).
MAE/RMSE — evalúan → regresión. Silhouette — evalúa → clustering.

## Representación

Jerarquía: árbol dirigido izquierda a derecha, líneas sólidas; técnicas y recursos ocultos por defecto.
Relaciones: enlaces secundarios punteados naranja con nombre del verbo, sin confundir dependencia temática con pertenencia.
Formas: ✦ raíz; ◉ dominio; ▣ área; ▦ grupo; ◆ paradigma; ▤ tarea; ⬢ métrica; ▲ problema; ● técnica o modelo.
Colores: ámbar raíz, naranja dominio, violeta áreas, índigo grupos, cian paradigmas, verde métricas, coral problemas.
Las fichas distinguen padres, subtemas, conexiones salientes y entrantes, y ofrecen botones de navegación.

Limitación conocida: PyVis embebido no envía el clic en el nodo a Streamlit; se usa el selector y botones de ficha. Para hacerlo bidireccional será necesario un componente personalizado. No se asume que actualmente funcione esa acción.

## Persistencia y seguridad

Migración controlada taxonomy_ml_semantic_v2; exclusivamente inserta nodos y enlaces faltantes, conserva contenido original y registra un marcador en map_meta. No revive entidades eliminadas por el usuario tras el primer arranque. Los enlaces nuevos poseen payload.source ml-ontology-v2. Reutiliza tablas actuales, sin sobrescribir catálogos Python/HF.

Se verifican integridad, idempotencia, rutas semánticas, relaciones transversales y conectividad en pruebas. La integración de otros dominios se puede extender con el mismo sistema de roles.
