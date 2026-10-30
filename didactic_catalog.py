"""Curated instructional grouping. A visual projection, NOT an alternative taxonomy.

Paradigms are siblings under ML. Algorithms are nested by task. Metrics,
concepts and risks are satellites; deep learning crosses learning paradigms.
"""
from __future__ import annotations

from sqlalchemy import select, insert
from graph_store import map_meta, utcnow
from knowledge_taxonomy import _attrs

EXTRA_TOPICS = [
    ("Clasificación", "k-NN", "modelo", "K-nearest neighbors clasifica según el voto de los vecinos próximos; requiere una escala adecuada de atributos."),
    ("Clasificación", "Naive Bayes", "modelo", "Clasificador probabilístico basado en el teorema de Bayes y una hipótesis de independencia condicional."),
    ("Clasificación", "AdaBoost", "modelo", "Boosting que combina clasificadores débiles y actualiza pesos de ejemplos difíciles."),
    ("Clasificación", "XGBoost", "modelo", "Implementación eficiente de gradient boosting con regularización y optimizaciones para datos tabulares."),
    ("Clasificación", "CatBoost", "modelo", "Gradient boosting especialmente útil para variables categóricas."),
    ("Clustering", "Clustering jerárquico", "modelo", "Construye una jerarquía de grupos por fusiones o divisiones; puede visualizarse como dendrograma."),
    ("Clustering", "GMM", "modelo", "Modelos de mezclas gaussianas; asignan probabilidades de pertenencia a componentes."),
    ("Clustering", "K-means++", "técnica", "Estrategia de inicialización de centroides para mejorar la estabilidad de K-means; no es otro paradigma."),
    ("Reducción de dimensionalidad", "t-SNE", "técnica", "Método no lineal para visualizar vecindades locales en pocas dimensiones; no es un algoritmo de clustering."),
    ("Reducción de dimensionalidad", "UMAP", "técnica", "Método de aprendizaje de variedad para reducción de dimensiones y visualización; no es clustering."),
    ("Aprendizaje por refuerzo", "SARSA", "algoritmo", "Aprendizaje temporal on-policy que actualiza Q usando la acción efectivamente tomada."),
    ("Aprendizaje por refuerzo", "Actor-Critic", "algoritmo", "Familia de métodos de refuerzo con política (actor) y estimador de valor (crítico)."),
    ("Aprendizaje por refuerzo", "PPO", "algoritmo", "Optimización de política proximal para controlar el tamaño de la actualización durante el aprendizaje por refuerzo."),
    ("Machine Learning", "Deep Learning", "grupo", "Familia de redes neuronales profundas utilizada con aprendizaje supervisado, autosupervisado y por refuerzo."),
    ("Deep Learning", "CNN", "modelo", "Redes convolucionales para extraer patrones espaciales de imágenes y señales."),
    ("Deep Learning", "RNN", "modelo", "Redes recurrentes que procesan secuencias usando estados internos."),
    ("Deep Learning", "LSTM", "modelo", "Red recurrente con compuertas que puede aprender dependencias largas."),
    ("Deep Learning", "Transformers", "modelo", "Arquitecturas con atención capaces de modelar dependencias entre tokens."),
    ("Deep Learning", "MLP", "modelo", "Perceptrón multicapa con capas densas para tareas de clasificación o regresión."),
    ("Aprendizaje autosupervisado", "Aprendizaje contrastivo", "técnica", "Aprende representaciones acercando pares relacionados y alejando pares distintos."),
    ("Aprendizaje autosupervisado", "Modelado de lenguaje enmascarado", "técnica", "Objetivo de preentrenamiento que predice tokens ocultos usando su contexto."),
    ("Aprendizaje semisupervisado", "Pseudoetiquetado", "técnica", "Utiliza predicciones del modelo como etiquetas provisionales para ejemplos sin etiqueta."),
    ("Aprendizaje semisupervisado", "Propagación de etiquetas", "técnica", "Difunde etiquetas conocidas a puntos sin etiquetas mediante un grafo de similitud."),
    ("Métricas de clasificación", "Curva ROC", "concepto", "Curva de sensibilidad (TPR) frente a tasa de falsos positivos (FPR) al variar el umbral; ROC-AUC resume su área."),
]
# Existing items (e.g. CNN, Transformers) are never overwritten.
EXTRA_LINKS = [
    ("k-NN", "Regresión", "se utiliza en"),
    ("k-NN", "Clasificación", "se utiliza en"),
    ("Naive Bayes", "Clasificación", "se utiliza en"),
    ("AdaBoost", "Clasificación", "se utiliza en"),
    ("XGBoost", "Clasificación", "se utiliza en"),
    ("XGBoost", "Regresión", "se utiliza en"),
    ("CatBoost", "Clasificación", "se utiliza en"),
    ("CatBoost", "Regresión", "se utiliza en"),
    ("Clustering jerárquico", "Clustering", "se utiliza en"),
    ("GMM", "Clustering", "se utiliza en"),
    ("K-means++", "K-means", "inicializa"),
    ("t-SNE", "Reducción de dimensionalidad", "se utiliza en"),
    ("UMAP", "Reducción de dimensionalidad", "se utiliza en"),
    ("SARSA", "Aprendizaje por refuerzo", "se utiliza en"),
    ("PPO", "Aprendizaje por refuerzo", "se utiliza en"),
    ("Actor-Critic", "Aprendizaje por refuerzo", "se utiliza en"),
    ("Curva ROC", "Clasificación", "evalúa"),
    ("ROC-AUC", "Curva ROC", "resume"),
    ("Curva ROC", "Aprendizaje supervisado", "se usa en"),
    ("MLP", "Aprendizaje supervisado", "se usa en"),
    ("MLP", "Deep Learning", "arquitectura de"),
    ("CNN", "Deep Learning", "arquitectura de"),
    ("RNN", "Deep Learning", "arquitectura de"),
    ("LSTM", "Deep Learning", "arquitectura de"),
    ("Transformers", "Deep Learning", "arquitectura de"),
    ("Deep Learning", "Aprendizaje supervisado", "se combina con"),
    ("Deep Learning", "Aprendizaje autosupervisado", "se combina con"),
    ("Deep Learning", "Aprendizaje por refuerzo", "se combina con"),
]
MIGRATION_KEY = "taxonomy_visual_v3"

# Each algorithm appears ONCE on the visual sheet, even when applicable elsewhere.
BRANCHES = [
    {
        "key": "Aprendizaje supervisado", "short": "Supervisado", "number": "01",
        "emoji": "📈", "accent": "#2563eb", "background": "#eff6ff",
        "description": "Aprende con datos etiquetados para predecir clases o valores.",
        "sections": [
            {"key": "Clasificación", "subtitle": "Predice categorías",
             "items": ["Regresión logística", "k-NN", "Árbol de decisión", "Random Forest", "Máquinas de soporte vectorial (SVM)", "Naive Bayes", "AdaBoost", "XGBoost", "CatBoost"]},
            {"key": "Regresión", "subtitle": "Predice valores continuos",
             "items": ["Regresión lineal", "Gradient Boosting"]},
        ],
        "satellites": ["Precisión (precision)", "Recall (sensibilidad)", "F1-score", "ROC-AUC",
                       "Curva ROC", "Matriz de confusión", "Exactitud (accuracy)", "PR-AUC"],
    },
    {
        "key": "Aprendizaje no supervisado", "short": "No supervisado", "number": "02",
        "emoji": "🔎", "accent": "#16a34a", "background": "#f0fdf4",
        "description": "Descubre patrones sin una etiqueta objetivo explícita.",
        "sections": [
            {"key": "Clustering", "subtitle": "Agrupa por similitud",
             "items": ["K-means", "Clustering jerárquico", "DBSCAN", "GMM", "K-means++"]},
            {"key": "Reducción de dimensionalidad", "subtitle": "Representaciones compactas",
             "items": ["PCA", "t-SNE", "UMAP"]},
        ],
        "satellites": ["Coeficiente silhouette", "Detección de anomalías"],
    },
    {
        "key": "Aprendizaje por refuerzo", "short": "Por refuerzo", "number": "03",
        "emoji": "🎯", "accent": "#ea580c", "background": "#fff7ed",
        "description": "Aprende políticas de decisión a partir de acciones y recompensas.",
        "sections": [
            {"key": "Decisiones secuenciales", "subtitle": "Optimización de políticas",
             "items": ["Q-learning", "SARSA", "Deep Q-Network (DQN)", "Policy gradient", "Actor-Critic", "PPO"]},
        ],
        "satellites": ["Retorno acumulado"],
    },
]
ADDITIONAL = [
    {"key": "Aprendizaje autosupervisado", "items": ["Aprendizaje contrastivo", "Modelado de lenguaje enmascarado"], "accent": "#8b5cf6"},
    {"key": "Aprendizaje semisupervisado", "items": ["Pseudoetiquetado", "Propagación de etiquetas"], "accent": "#0891b2"},
]
CROSS_ARCHITECTURES = ["MLP", "CNN", "RNN", "LSTM", "Transformers"]
CROSS_RISKS = ["Sobreajuste", "Subajuste", "Fuga de datos (data leakage)", "Deriva de datos", "Desbalance de clases"]
CROSS_TECHNIQUES = ["Regularización", "Early stopping", "Validación cruzada", "Ajuste de hiperparámetros"]


def apply_visual_extension_once(store):
    """Idempotently extend DB once; retain all user-authored nodes and links."""
    with store.engine.connect() as conn:
        marker = conn.execute(select(map_meta.c.value).where(map_meta.c.key == MIGRATION_KEY)).scalar_one_or_none()
    if marker == "completed":
        return {"applied": False, "nodes": 0, "edges": 0}
    nodes, edges = store.load_graph()
    present = set(edges)
    new_nodes = new_edges = 0
    for parent, key, role, description in EXTRA_TOPICS:
        if parent not in nodes:
            raise RuntimeError(f"Missing taxonomy parent: {parent}")
        previously_existing = key in nodes
        if not previously_existing:
            attrs = _attrs(key, role, description, parent)
            attrs["taxonomy_source"] = "visual-v3"
            store.upsert_node(key, attrs)
            nodes[key] = attrs
            new_nodes += 1
        # An existing educational node can already have a different primary
        # parent. Preserve it; add a named association instead of a second parent.
        has_other_parent = previously_existing and any(
            b == key and a != parent and relation == "incluye"
            for a, b, relation in present
        )
        relation_kind = ("arquitectura de" if parent == "Deep Learning"
                         else "se relaciona con") if has_other_parent else "incluye"
        relation = (parent, key, relation_kind)
        if relation not in present:
            store.upsert_edge(*relation, payload={"source": "visual-v3"})
            present.add(relation)
            new_edges += 1
    for src, dst, relation in EXTRA_LINKS:
        if src in nodes and dst in nodes and (src, dst, relation) not in present:
            store.upsert_edge(src, dst, relation, payload={"source": "visual-v3"})
            present.add((src, dst, relation))
            new_edges += 1
    with store.engine.begin() as conn:
        conn.execute(insert(map_meta).values(key=MIGRATION_KEY, value="completed", updated_at=utcnow()))
    return {"applied": True, "nodes": new_nodes, "edges": new_edges}
