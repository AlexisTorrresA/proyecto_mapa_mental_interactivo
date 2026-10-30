# Mapa didáctico: paradigmas, algoritmos y conceptos asociados

## Vista nueva

Se añade **Didáctico** como modo predeterminado en el dominio **Inteligencia Artificial** de la pestaña **Mapa de conceptos**, conservando los modos Jerarquía y Relaciones para explorar el grafo completo y el resto de dominios.

Inspirado en la referencia visual aportada, pero sin copiar sus errores conceptuales:

- **IA → Machine Learning → paradigmas**. Supervisado, no supervisado y refuerzo son tres columnas al mismo nivel; autosupervisado y semisupervisado también son paradigmas y aparecen en una sección adicional.
- Cada columna presenta **tareas** (clasificación/regresión; clustering/reducción de dimensión; decisiones secuenciales) con tarjetas de algoritmos y modelos. Los ensambles (AdaBoost/XGBoost/CatBoost) no se clasifican como paradigmas.
- **Círculos punteados**: métricas y otros conceptos asociados a la tarea, separados de los algoritmos (precision, recall, ROC-AUC, curva ROC, F1, accuracy, matriz de confusión, etc.).
- **Deep Learning** aparece en una franja transversal con MLP, CNN, RNN, LSTM y Transformers, no como hermano exclusivo de aprendizaje supervisado o por refuerzo.
- **Riesgos** (sobreajuste, subajuste, data leakage, etc.) y **técnicas transversales** (regularización, validación cruzada, early stopping) van en franjas distintas.
- Las tarjetas son pulsables y abren dentro del mapa un panel de definición y relaciones reales, con enlaces verificables existentes. Hay búsqueda por texto y diseño responsive.

## Datos e integridad

La migración versionada `taxonomy_visual_v3` agrega solo los nodos y relaciones inexistentes; **no modifica las 773 fichas ni los enlaces anteriores**. Si un nodo ya tiene un padre taxonómico distinto, se crea una **relación semántica** en vez de un segundo padre. La base sigue siendo la misma PostgreSQL del Y700. La migración ocurre una sola vez en `scripts/init_db.py` y conserva las ediciones manuales posteriores.

Es una **proyección visual curada**, no una sustitución del grafo general ni una reescritura de la jerarquía. Algunos algoritmos (p. ej. Random Forest, k-NN, XGBoost) sirven para varias tareas, aunque se presenten una sola vez como ejemplos representativos; sus asociaciones reales siguen disponibles en la ficha.

## Revisión

```bash
python -m pytest -q
python -m compileall -q atlas_ia.py atlas_didactic.py didactic_catalog.py scripts tests
```

En producción abrir https://mapa-mental-ia.alexistorreslabs.com/ y seleccionar **Mapa de conceptos → Visualización: Didáctico**. Pulsa un algoritmo o círculo para abrir su ficha y ver conexiones. Cambia a **Relaciones** para ver la red semántica original.
