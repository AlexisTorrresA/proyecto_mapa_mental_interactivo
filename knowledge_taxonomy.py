"""Taxonomía educativa: jerarquías y relaciones semánticas sin duplicar conceptos.

Un nodo tiene un padre primario para orientación, pero puede relacionarse con
muchos temas sin convertirse en hijo de todos. Las conexiones transversales
no alteran la taxonomía principal.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import networkx as nx

DOMAIN = "Inteligencia Artificial"

# Padre, nombre, rol, descripción. Descripciones específicas, sin textos genéricos.
CONCEPTS = [
("Machine Learning", "Paradigmas de aprendizaje", "grupo", "Formas de aprender a partir de datos y de la interacción con un entorno."),
("Paradigmas de aprendizaje", "Aprendizaje supervisado", "paradigma", "Aprende una función a partir de ejemplos etiquetados (X, y); suele usarse para clasificación y regresión."),
("Paradigmas de aprendizaje", "Aprendizaje no supervisado", "paradigma", "Identifica estructura o patrones en datos sin etiquetas objetivo explícitas; p. ej., clustering."),
("Paradigmas de aprendizaje", "Aprendizaje por refuerzo", "paradigma", "Un agente aprende una política mediante acciones y señales de recompensa en un entorno."),
("Paradigmas de aprendizaje", "Aprendizaje autosupervisado", "paradigma", "Construye tareas de predicción a partir de los propios datos para aprender representaciones."),
("Paradigmas de aprendizaje", "Aprendizaje semisupervisado", "paradigma", "Combina pocos ejemplos etiquetados con muchos datos no etiquetados."),
("Machine Learning", "Tareas de aprendizaje", "grupo", "Problemas concretos a resolver mediante modelos y algoritmos."),
("Tareas de aprendizaje", "Clasificación", "tarea", "Predice una categoría discreta; requiere definir clases, datos de evaluación y métricas apropiadas."),
("Clasificación", "Clasificación binaria", "tarea", "Distingue dos clases; p. ej., fraude frente a no fraude."),
("Clasificación", "Clasificación multiclase", "tarea", "Predice una entre tres o más clases mutuamente excluyentes."),
("Tareas de aprendizaje", "Regresión", "tarea", "Predice un valor numérico continuo; p. ej., demanda o temperatura."),
("Tareas de aprendizaje", "Clustering", "tarea", "Agrupa muestras según similitud sin etiquetas objetivo previas."),
("Tareas de aprendizaje", "Reducción de dimensionalidad", "tarea", "Resume variables en menos dimensiones preservando estructura útil."),
("Tareas de aprendizaje", "Detección de anomalías", "tarea", "Detecta observaciones atípicas respecto de patrones esperados."),
("Tareas de aprendizaje", "Decisiones secuenciales", "tarea", "Optimiza acciones a lo largo del tiempo con recompensas y transiciones."),
("Machine Learning", "Preparación y entrenamiento", "grupo", "Proceso de convertir datos en modelos reproducibles y validados."),
("Preparación y entrenamiento", "División entrenamiento-validación-prueba", "proceso", "Separa datos para ajustar parámetros, seleccionar hiperparámetros y evaluar generalización."),
("Preparación y entrenamiento", "Validación cruzada", "técnica", "Estima desempeño repitiendo entrenamiento y validación sobre diferentes particiones."),
("Preparación y entrenamiento", "Estandarización", "técnica", "Transforma variables para media cero y desviación estándar uno, ajustando solo con entrenamiento."),
("Preparación y entrenamiento", "Normalización de variables", "técnica", "Reescala datos según una regla; debe calcularse sin filtrar información del conjunto de prueba."),
("Preparación y entrenamiento", "Ajuste de hiperparámetros", "técnica", "Selecciona configuraciones como profundidad, tasa de aprendizaje o penalización usando validación."),
("Preparación y entrenamiento", "Regularización", "técnica", "Reduce complejidad efectiva o penaliza parámetros para mejorar generalización."),
("Regularización", "Regularización L1", "técnica", "Penalización proporcional a la magnitud absoluta de coeficientes; puede inducir esparsidad."),
("Regularización", "Regularización L2", "técnica", "Penalización cuadrática de coeficientes; limita pesos grandes."),
("Preparación y entrenamiento", "Early stopping", "técnica", "Detiene el entrenamiento cuando la métrica de validación deja de mejorar."),
("Preparación y entrenamiento", "Aumento de datos", "técnica", "Genera transformaciones plausibles del conjunto de entrenamiento para mejorar robustez."),
("Machine Learning", "Evaluación de modelos", "grupo", "Métricas, diagnósticos y criterios según la tarea y el costo de errores."),
("Evaluación de modelos", "Métricas de clasificación", "grupo", "Miden errores entre clases y dependen del umbral, distribución y objetivo."),
("Métricas de clasificación", "Matriz de confusión", "concepto", "Cuenta verdaderos/falsos positivos y negativos para entender los tipos de error."),
("Métricas de clasificación", "Exactitud (accuracy)", "métrica", "Proporción de predicciones correctas: (TP+TN)/(TP+TN+FP+FN); puede engañar con clases desbalanceadas."),
("Métricas de clasificación", "Precisión (precision)", "métrica", "De los positivos predichos, proporción correcta: TP/(TP+FP). No equivale a accuracy."),
("Métricas de clasificación", "Recall (sensibilidad)", "métrica", "De los positivos reales, proporción detectada: TP/(TP+FN)."),
("Métricas de clasificación", "Especificidad", "métrica", "De los negativos reales, proporción correctamente identificada: TN/(TN+FP)."),
("Métricas de clasificación", "F1-score", "métrica", "Media armónica entre precision y recall: 2PR/(P+R)."),
("Métricas de clasificación", "ROC-AUC", "métrica", "Área bajo ROC: evalúa discriminación para diversos umbrales, con supuestos sobre clases."),
("Métricas de clasificación", "PR-AUC", "métrica", "Área bajo la curva precision-recall; útil ante clases positivas poco frecuentes."),
("Evaluación de modelos", "Métricas de regresión", "grupo", "Evalúan diferencias entre valores continuos predichos y reales."),
("Métricas de regresión", "MAE", "métrica", "Promedio del error absoluto; conserva unidades del objetivo."),
("Métricas de regresión", "RMSE", "métrica", "Raíz del promedio de errores cuadrados; penaliza relativamente más errores grandes."),
("Métricas de regresión", "R²", "métrica", "Fracción de variabilidad explicada frente a una referencia basada en la media."),
("Evaluación de modelos", "Métricas de clustering", "grupo", "Evalúan cohesión y separación de agrupaciones sin etiquetas."),
("Métricas de clustering", "Coeficiente silhouette", "métrica", "Compara similitud dentro del clúster con la de los otros clústeres."),
("Evaluación de modelos", "Métricas de refuerzo", "grupo", "Evalúan retornos y comportamiento de políticas en el entorno."),
("Métricas de refuerzo", "Retorno acumulado", "métrica", "Suma de recompensas obtenidas; puede incluir descuento temporal."),
("Evaluación de modelos", "Selección de umbral", "técnica", "Ajusta umbral de decisión según costes de falsos positivos y falsos negativos."),
("Machine Learning", "Generalización y riesgos", "grupo", "Fenómenos que afectan confiabilidad y transferencia fuera de la muestra."),
("Generalización y riesgos", "Sobreajuste", "problema", "El modelo aprende ruido o patrones específicos del entrenamiento y rinde peor en datos nuevos."),
("Generalización y riesgos", "Subajuste", "problema", "El modelo es demasiado limitado o está insuficientemente entrenado para capturar la señal."),
("Generalización y riesgos", "Compromiso sesgo-varianza", "concepto", "Equilibrio entre error por supuestos restrictivos y sensibilidad a cambios en los datos."),
("Generalización y riesgos", "Fuga de datos (data leakage)", "problema", "Información del conjunto de validación/prueba o del futuro contamina el entrenamiento."),
("Generalización y riesgos", "Desbalance de clases", "problema", "Distribución desigual entre clases que requiere métricas y estrategias de evaluación adecuadas."),
("Generalización y riesgos", "Deriva de datos", "problema", "Cambios de distribución respecto de entrenamiento que pueden degradar el desempeño."),
("Generalización y riesgos", "Robustez y distribución fuera de muestra", "concepto", "Comprueba cómo se comporta un modelo ante perturbaciones o entornos distintos."),
("Machine Learning", "Modelos y algoritmos", "grupo", "Familias de estimadores y algoritmos; no confundir con paradigmas ni métricas."),
("Modelos y algoritmos", "Regresión lineal", "modelo", "Modelo lineal para predecir una variable continua a partir de características."),
("Modelos y algoritmos", "Regresión logística", "modelo", "Clasificador probabilístico lineal que estima log-odds de una clase."),
("Modelos y algoritmos", "Árbol de decisión", "modelo", "Particiones recursivas mediante reglas sobre características."),
("Modelos y algoritmos", "Random Forest", "modelo", "Ensamble de árboles entrenados con aleatoriedad para reducir varianza."),
("Modelos y algoritmos", "Gradient Boosting", "modelo", "Construye un ensamble secuencial que corrige errores del anterior."),
("Modelos y algoritmos", "Máquinas de soporte vectorial (SVM)", "modelo", "Modelos de máximo margen que pueden usar kernels para fronteras no lineales."),
("Modelos y algoritmos", "K-means", "modelo", "Clustering por centroides y minimización de variación intra-grupo."),
("Modelos y algoritmos", "DBSCAN", "modelo", "Clustering basado en densidad que detecta ruido."),
("Modelos y algoritmos", "PCA", "técnica", "Proyección lineal en componentes ortogonales de máxima varianza."),
("Modelos y algoritmos", "Q-learning", "algoritmo", "Aprende estimaciones de valor acción-estado para seleccionar acciones."),
("Modelos y algoritmos", "Deep Q-Network (DQN)", "modelo", "Aproxima Q-valores con redes neuronales para acciones discretas."),
("Modelos y algoritmos", "Policy gradient", "algoritmo", "Optimiza directamente una política parametrizada usando gradientes de retorno."),
]

# Cada relación no jerárquica explica su semántica, sin crear múltiples padres.
CROSS_LINKS = [
("Aprendizaje supervisado", "Clasificación", "resuelve"),
("Aprendizaje supervisado", "Regresión", "resuelve"),
("Aprendizaje no supervisado", "Clustering", "resuelve"),
("Aprendizaje no supervisado", "Reducción de dimensionalidad", "resuelve"),
("Aprendizaje no supervisado", "Detección de anomalías", "puede resolver"),
("Aprendizaje por refuerzo", "Decisiones secuenciales", "resuelve"),
("Aprendizaje autosupervisado", "Deep Learning", "se utiliza en"),
("Aprendizaje semisupervisado", "Clasificación", "se utiliza en"),
("Sobreajuste", "Aprendizaje supervisado", "afecta a"),
("Sobreajuste", "Aprendizaje no supervisado", "afecta a"),
("Sobreajuste", "Aprendizaje por refuerzo", "afecta a"),
("Sobreajuste", "Deep Learning", "afecta a"),
("Subajuste", "Aprendizaje supervisado", "afecta a"),
("Subajuste", "Aprendizaje no supervisado", "afecta a"),
("Regularización", "Sobreajuste", "mitiga"),
("Early stopping", "Sobreajuste", "mitiga"),
("Validación cruzada", "Sobreajuste", "ayuda a detectar"),
("Compromiso sesgo-varianza", "Sobreajuste", "explica"),
("Compromiso sesgo-varianza", "Subajuste", "explica"),
("Fuga de datos (data leakage)", "Evaluación de modelos", "distorsiona"),
("Desbalance de clases", "Exactitud (accuracy)", "puede sesgar"),
("Desbalance de clases", "PR-AUC", "motiva uso de"),
("Selección de umbral", "Precisión (precision)", "modifica"),
("Selección de umbral", "Recall (sensibilidad)", "modifica"),
("Precisión (precision)", "Clasificación", "evalúa"),
("Recall (sensibilidad)", "Clasificación", "evalúa"),
("Exactitud (accuracy)", "Clasificación", "evalúa"),
("F1-score", "Clasificación", "evalúa"),
("ROC-AUC", "Clasificación", "evalúa"),
("Matriz de confusión", "Clasificación", "evalúa"),
("MAE", "Regresión", "evalúa"),
("RMSE", "Regresión", "evalúa"),
("R²", "Regresión", "evalúa"),
("Coeficiente silhouette", "Clustering", "evalúa"),
("Retorno acumulado", "Decisiones secuenciales", "evalúa"),
("Regresión lineal", "Regresión", "se utiliza en"),
("Regresión logística", "Clasificación", "se utiliza en"),
("Árbol de decisión", "Clasificación", "se utiliza en"),
("Árbol de decisión", "Regresión", "se utiliza en"),
("Random Forest", "Clasificación", "se utiliza en"),
("Random Forest", "Regresión", "se utiliza en"),
("Gradient Boosting", "Clasificación", "se utiliza en"),
("Gradient Boosting", "Regresión", "se utiliza en"),
("Máquinas de soporte vectorial (SVM)", "Clasificación", "se utiliza en"),
("Máquinas de soporte vectorial (SVM)", "Regresión", "se utiliza en"),
("K-means", "Clustering", "se utiliza en"),
("DBSCAN", "Clustering", "se utiliza en"),
("PCA", "Reducción de dimensionalidad", "se utiliza en"),
("Q-learning", "Aprendizaje por refuerzo", "se utiliza en"),
("Deep Q-Network (DQN)", "Aprendizaje por refuerzo", "se utiliza en"),
("Policy gradient", "Aprendizaje por refuerzo", "se utiliza en"),
("Regularización", "Regresión logística", "se utiliza en"),
("Regularización", "Deep Learning", "se utiliza en"),
("División entrenamiento-validación-prueba", "Fuga de datos (data leakage)", "ayuda a prevenir"),
("Estandarización", "Máquinas de soporte vectorial (SVM)", "se utiliza en"),
("Ajuste de hiperparámetros", "Validación cruzada", "utiliza"),
("Ajuste de hiperparámetros", "Machine Learning", "optimiza modelos de"),
("Deriva de datos", "MLOps", "se monitorea en"),
("Robustez y distribución fuera de muestra", "Evaluación de modelos", "se analiza en"),
("feature engineering", "Preparación y entrenamiento", "se utiliza en"),
("fine-tuning", "Preparación y entrenamiento", "se utiliza en"),
("sesgo algorítmico", "Generalización y riesgos", "relaciona"),
("drift", "Deriva de datos", "relaciona"),
("Deep Learning", "Transformers", "incluye"),
]

GROUP_TOPICS = {
    "Aprendizaje supervisado": ["Clasificación", "Regresión", "Regresión lineal", "Regresión logística",
                                "Random Forest", "Sobreajuste", "Precisión (precision)", "Recall (sensibilidad)"],
    "Aprendizaje no supervisado": ["Clustering", "Reducción de dimensionalidad", "K-means",
                                   "DBSCAN", "PCA", "Sobreajuste"],
    "Aprendizaje por refuerzo": ["Decisiones secuenciales", "Q-learning", "Deep Q-Network (DQN)",
                                 "Policy gradient", "Sobreajuste"],
}


def _attrs(key: str, role: str, description: str, parent: str) -> dict:
    return {
        "label": key, "kind": "concepto", "domain": DOMAIN, "size": 15,
        "title": description, "semantic_role": role, "primary_parent": parent,
        "taxonomy_source": "ml-ontology-v2", "year": None, "url": None,
        "examples": [], "functions": [], "tags": ["machine-learning", role],
    }


def analyze_graph(nodes: dict, edges: list) -> dict:
    """Diagnóstico replicable para UI y pruebas; no modifica PostgreSQL."""
    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from((a, b) for a, b, *_ in edges if a in nodes and b in nodes)
    components = sorted(nx.connected_components(graph), key=len, reverse=True)
    return {
        "nodes": len(nodes), "edges": len(edges),
        "components": len(components), "isolated": [n for n, degree in graph.degree if degree == 0],
        "relations": dict(Counter(e[2] for e in edges if len(e) > 2)),
        "by_role": dict(Counter(v.get("semantic_role") or v.get("kind") or "concepto" for v in nodes.values())),
        "component_sizes": [len(c) for c in components],
    }


HIERARCHY_RELATIONS = {"incluye", "es parte de"}
ASSOCIATION_RELATIONS = {"relaciona", "se utiliza en", "afecta a", "mitiga", "evalúa", "resuelve",
                         "puede resolver", "optimiza modelos de", "ayuda a detectar",
                         "ayuda a prevenir", "explica", "puede sesgar", "modifica",
                         "motiva uso de", "distorsiona", "utiliza", "se monitorea en",
                         "se analiza en"}


def hierarchy_parents(edges: list) -> dict[str, str]:
    """El padre lo determina PostgreSQL; no imponemos un árbol hardcoded."""
    parents = {}
    for src, dst, relation, *_ in edges:
        if relation in HIERARCHY_RELATIONS and dst not in parents:
            parents[dst] = src
    return parents


def semantic_path(focus: str, edges: list, max_depth: int = 12) -> list[str]:
    parents = hierarchy_parents(edges)
    trail = [focus]
    seen = set(trail)
    while len(trail) < max_depth and trail[-1] in parents:
        p = parents[trail[-1]]
        if p in seen:
            break
        trail.append(p)
        seen.add(p)
    return list(reversed(trail))


def semantic_neighborhood(nodes: dict, edges: list, focus: str, depth: int = 2,
                          limit: int = 110, cross: bool = False, assets: bool = False):
    """Graficar jerarquía centrada, dejando relaciones transversales opcionales.

    Los nodos vecinos por relación transversal se muestran solo cuando el
    usuario habilita 'Conexiones transversales'; así un riesgo no se interpreta
    como hijo de cada paradigma.
    """
    if focus not in nodes:
        return {}, []
    visible = {k for k, a in nodes.items() if assets or a.get("kind") not in
               {"contenedor", "herramienta", "libreria", "dataset", "recurso"}}
    hierarchy = nx.Graph()
    hierarchy.add_nodes_from(visible)
    for a, b, relation, *_ in edges:
        if a in visible and b in visible and relation in HIERARCHY_RELATIONS:
            hierarchy.add_edge(a, b)
    selected = dict(nx.single_source_shortest_path_length(hierarchy, focus, cutoff=depth))
    if cross:
        extra = {}
        for a, b, rel, *_ in edges:
            if rel not in HIERARCHY_RELATIONS and a in visible and b in visible:
                if a in selected and b not in selected:
                    extra[b] = min(extra.get(b, 1000), selected[a] + 1)
                if b in selected and a not in selected:
                    extra[a] = min(extra.get(a, 1000), selected[b] + 1)
        for key, distance in extra.items():
            if distance <= depth + 1:
                selected[key] = distance
    # Prefer path to root, then closest nodes. Sort by semantic group/role.
    trail = semantic_path(focus, edges)
    for key in trail:
        if key in visible:
            selected.setdefault(key, 0)
    scored = sorted(selected, key=lambda k: (
        0 if k in trail else 1, selected[k], 
        0 if nodes[k].get("semantic_role") in ("grupo", "paradigma") else 1,
        str(nodes[k].get("label") or k).casefold()
    ))
    keep = set(scored[:max(5, limit)])
    return ({key: nodes[key] for key in scored if key in keep},
            [e for e in edges if e[0] in keep and e[1] in keep and
             (cross or e[2] in HIERARCHY_RELATIONS)])
