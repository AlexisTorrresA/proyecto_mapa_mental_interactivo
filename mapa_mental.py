
import os
import json
import tempfile
import html
from collections import deque, defaultdict

import altair as alt
import networkx as nx
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

st.set_page_config(page_title="Mapa conceptual interactivo", layout="wide")
st.title("Mapa conceptual interactivo de tecnología")
st.write(
    "Haz click en un nodo para ver su detalle ampliado dentro del panel inferior del mapa. "
    "Usa los filtros de la derecha para simplificar la vista."
)

LINKEDIN_URL = "https://www.linkedin.com/in/alexis-torres87/"
GITHUB_URL = "https://github.com/AlexisTorrresA"

# =========================================================
# Estilos
# =========================================================
KIND_STYLES = {
    "principal": {"shape": "dot", "size_boost": 10},
    "subarea": {"shape": "dot", "size_boost": 4},
    "contenedor": {"shape": "dot", "size_boost": 1},
    "concepto": {"shape": "dot", "size_boost": 0},
    "herramienta": {"shape": "box", "size_boost": -2},
    "libreria": {"shape": "box", "size_boost": -2},
    "framework": {"shape": "box", "size_boost": -2},
    "recurso": {"shape": "star", "size_boost": -2},
    "dataset": {"shape": "hexagon", "size_boost": -2},
    "funcion": {"shape": "ellipse", "size_boost": -4},
}

DOMAIN_COLORS = {
    "Inteligencia Artificial": "#f4d35e",
    "Ingeniería de Software": "#06d6a0",
    "Cloud Computing": "#ffd166",
    "Ciberseguridad": "#ff6b6b",
    "Robótica e IoT": "#9b5de5",
    "General": "#adb5bd",
}

TYPE_COLOR_OVERRIDES = {
    "herramienta": "#e9ecef",
    "libreria": "#d8f3dc",
    "framework": "#d8f3dc",
    "recurso": "#fff3bf",
    "dataset": "#e5dbff",
    "funcion": "#f1f3f5",
}

# =========================================================
# Sidebar
# =========================================================
st.sidebar.header("Configuración del mapa")

tipo_mapa = st.sidebar.selectbox(
    "Tipo de mapa", ["Libre", "Jerárquico LR", "Jerárquico UD"]
)

node_distance = st.sidebar.slider("Distancia entre nodos", 150, 700, 320, 10)
spring_length = st.sidebar.slider("Longitud de resortes", 80, 500, 260, 10)
central_gravity = st.sidebar.slider("Gravedad central", 0.0, 1.0, 0.12, 0.01)
physics_enabled = st.sidebar.checkbox("Activar física", True)
show_edges = st.sidebar.checkbox("Mostrar relaciones", True)

st.sidebar.markdown("---")
st.sidebar.subheader("Vista temporal")
show_year_in_label = st.sidebar.checkbox("Mostrar años en nodos", False)
show_timeline = st.sidebar.checkbox("Mostrar línea de tiempo", True)
sort_by_epoch = st.sidebar.checkbox("Ordenar conceptos por época", True)

st.sidebar.markdown("---")
st.sidebar.subheader("Exploración")
st.sidebar.caption("El detalle de cada nodo aparece dentro del panel inferior del mapa al hacer click.")

# =========================================================
# Helpers para datos
# =========================================================
def make_container(domain, parent, label, year=None, title=None):
    return {
        "kind": "contenedor",
        "domain": domain,
        "size": 16,
        "year": year,
        "title": title or f"Contenedor de elementos de tipo {label.lower()} dentro de {parent}.",
        "group_parent": parent,
        "label_type": label,
    }

def make_node(kind, domain, year, title, size=12, url=None, examples=None, tools=None, functions=None, tags=None):
    return {
        "kind": kind,
        "domain": domain,
        "size": size,
        "year": year,
        "title": title,
        "url": url,
        "examples": examples or [],
        "tools": tools or [],
        "functions": functions or [],
        "tags": tags or [],
    }

nodes = {}
edges = []

def add_node(name, attrs):
    if name not in nodes:
        nodes[name] = attrs

def add_edge(src, dst, relation="relaciona"):
    edge = (src, dst, relation)
    if edge not in edges:
        edges.append(edge)

def add_typed_item(parent_container, item_name, kind, domain, year, title, url=None, functions=None):
    add_node(item_name, make_node(kind, domain, year, title, size=12, url=url, functions=functions))
    add_edge(parent_container, item_name, "contiene")


def normalize_item(item, inferred_kind, subarea):
    if isinstance(item, dict):
        item_name = item["name"]
        item_kind = item.get("kind", inferred_kind)
        item_year = item.get("year")
        item_title = item.get("title", f"{item_name} dentro de {subarea}.")
        item_url = item.get("url")
        item_functions = item.get("functions", [])
    else:
        item_name = item
        item_kind = inferred_kind
        item_year = None
        item_title = f"{item} dentro de {subarea}."
        item_url = None
        item_functions = []
    return {
        "name": item_name,
        "kind": item_kind,
        "year": item_year,
        "title": item_title,
        "url": item_url,
        "functions": item_functions,
    }

def build_group_description(label, subarea, items):
    first_line = f"Grupo {label} asociado a {subarea}."
    if label.lower() == "librerías":
        extra = "Incluye librerías y frameworks relevantes, con su propósito, funciones principales y enlaces de consulta."
    elif label.lower() == "herramientas":
        extra = "Incluye herramientas operativas o de uso práctico para trabajar esta subárea."
    elif label.lower() == "recursos":
        extra = "Incluye documentación, portales y material para profundizar."
    elif label.lower() == "datasets":
        extra = "Incluye datasets o fuentes de datos útiles para practicar, evaluar o entrenar."
    elif label.lower() == "aplicaciones":
        extra = "Incluye ejemplos de aplicación y uso real."
    else:
        extra = "Incluye elementos relacionados con esta subárea."
    return first_line + " " + extra + f" Total: {len(items)} elemento(s)."


def add_taxonomy_branch(domain_root, subarea, concept_items=None, tool_items=None, lib_items=None, resource_items=None, dataset_items=None, app_items=None, year=None, description=None):
    add_node(subarea, {
        "kind": "subarea",
        "domain": domain_root,
        "size": 22,
        "year": year,
        "title": description or f"Subárea de {domain_root}: {subarea}.",
        "tags": [domain_root, subarea],
    })
    add_edge(domain_root, subarea, "incluye")

    buckets = [
        ("Conceptos", concept_items or [], "concepto"),
        ("Herramientas", tool_items or [], "herramienta"),
        ("Librerías", lib_items or [], "libreria"),
        ("Recursos", resource_items or [], "recurso"),
        ("Datasets", dataset_items or [], "dataset"),
        ("Aplicaciones", app_items or [], "aplicacion"),
    ]

    for label, items, inferred_kind in buckets:
        if not items:
            continue

        normalized_items = [normalize_item(item, inferred_kind, subarea) for item in items]

        if label == "Conceptos":
            container_name = f"{subarea} :: {label}"
            add_node(
                container_name,
                make_container(
                    domain_root,
                    subarea,
                    label,
                    year=year,
                    title=f"Grupo {label} asociado a {subarea}."
                )
            )
            add_edge(subarea, container_name, "agrupa")

            for item in normalized_items:
                add_typed_item(
                    container_name,
                    item["name"],
                    item["kind"],
                    domain_root,
                    item["year"],
                    item["title"],
                    url=item["url"],
                    functions=item["functions"],
                )
        else:
            container_name = f"{subarea} :: {label}"
            add_node(
                container_name,
                {
                    "kind": "contenedor",
                    "domain": domain_root,
                    "size": 16,
                    "year": year,
                    "title": build_group_description(label, subarea, normalized_items),
                    "items_detail": normalized_items,
                    "group_parent": subarea,
                    "label_type": label,
                    "tags": [domain_root, subarea, label],
                }
            )
            add_edge(subarea, container_name, "agrupa")

# =========================================================
# Nivel 0: dominios principales
# =========================================================
MAIN_DOMAINS = [
    ("Inteligencia Artificial", 1956, "Campo general que crea sistemas capaces de realizar tareas que normalmente requieren inteligencia humana."),
    ("Ingeniería de Software", 1968, "Disciplina para diseñar, construir, probar y mantener sistemas de software."),
    ("Cloud Computing", 2006, "Uso de infraestructura, plataformas y servicios remotos para desarrollar y operar sistemas."),
    ("Ciberseguridad", 1970, "Protección de sistemas, redes, datos y aplicaciones frente a amenazas."),
    ("Robótica e IoT", 1961, "Integración de hardware, sensores, control, conectividad e inteligencia en sistemas físicos."),
]

for name, year, title in MAIN_DOMAINS:
    add_node(name, {
        "kind": "principal",
        "domain": name,
        "size": 38,
        "year": year,
        "title": title,
        "tags": [name],
    })

# =========================================================
# Rama especial: Python -> Librerías
# =========================================================
add_node("Python", {
    "kind": "subarea",
    "domain": "Ingeniería de Software",
    "size": 24,
    "year": 1991,
    "title": "Lenguaje clave para IA, backend, automatización, análisis de datos y scripting.",
    "url": "https://www.python.org/",
    "tags": ["Python", "lenguaje"],
})
add_edge("Ingeniería de Software", "Python", "incluye")

python_libraries_detail = []
for lib in python_libraries:
    python_libraries_detail.append(
        {
            "name": lib["name"],
            "kind": "libreria",
            "year": lib.get("year"),
            "title": lib.get("title", ""),
            "url": lib.get("url"),
            "functions": lib.get("functions", []),
        }
    )

add_node(
    "Python :: Librerías",
    {
        "kind": "contenedor",
        "domain": "Ingeniería de Software",
        "size": 16,
        "year": 1991,
        "title": "Grupo de librerías y frameworks relevantes del ecosistema Python. Haz click para ver el detalle ampliado de cada una.",
        "items_detail": python_libraries_detail,
        "group_parent": "Python",
        "label_type": "Librerías",
        "tags": ["Ingeniería de Software", "Python", "Librerías"],
    }
)
add_edge("Python", "Python :: Librerías", "agrupa")

# =========================================================
# Inteligencia Artificial
# =========================================================
add_taxonomy_branch(
    "Inteligencia Artificial",
    "Machine Learning",
    concept_items=[
        {"name": "aprendizaje supervisado", "title": "Modelos entrenados con datos etiquetados.", "year": 1950},
        {"name": "aprendizaje no supervisado", "title": "Búsqueda de patrones o grupos en datos sin etiquetas.", "year": 1958},
        {"name": "aprendizaje por refuerzo", "title": "Aprendizaje mediante recompensas y penalizaciones.", "year": 1989},
        {"name": "clasificación", "title": "Predicción de clases o categorías."},
        {"name": "regresión", "title": "Predicción de variables continuas."},
        {"name": "clustering", "title": "Agrupación automática por similitud."},
    ],
    tool_items=[
        {"name": "Jupyter", "title": "Entorno de notebooks interactivos.", "year": 2014, "url": "https://jupyter.org/"},
        {"name": "Google Colab", "title": "Entorno de notebooks en la nube.", "year": 2018, "url": "https://colab.research.google.com/"},
    ],
    lib_items=[
        {"name": "scikit-learn", "title": "Librería de machine learning clásico.", "year": 2007, "url": "https://scikit-learn.org/stable/"},
        {"name": "XGBoost", "title": "Implementación de gradient boosting potente para datos tabulares.", "year": 2014, "url": "https://xgboost.readthedocs.io/"},
        {"name": "LightGBM", "title": "Framework de boosting eficiente para grandes volúmenes.", "year": 2017, "url": "https://lightgbm.readthedocs.io/"},
    ],
    resource_items=[
        {"name": "Kaggle Learn", "title": "Ruta guiada de aprendizaje práctico.", "url": "https://www.kaggle.com/learn"},
        {"name": "documentación scikit-learn", "title": "Documentación oficial de scikit-learn.", "url": "https://scikit-learn.org/stable/documentation.html"},
    ],
    dataset_items=[
        {"name": "Iris", "title": "Dataset clásico de clasificación multiclase."},
        {"name": "Titanic", "title": "Dataset popular para clasificación supervisada."},
        {"name": "UCI Repository", "title": "Repositorio histórico de datasets de machine learning.", "url": "https://archive.ics.uci.edu/"},
    ],
    year=1959,
    description="Subárea de IA donde los modelos aprenden patrones a partir de datos."
)

add_taxonomy_branch(
    "Inteligencia Artificial",
    "Deep Learning",
    concept_items=[
        {"name": "redes neuronales", "title": "Base del aprendizaje profundo.", "year": 1943},
        {"name": "CNN", "title": "Redes convolucionales usadas especialmente en imágenes.", "year": 1998},
        {"name": "RNN", "title": "Redes recurrentes para secuencias.", "year": 1986},
        {"name": "LSTM", "title": "Variante recurrente para dependencias largas.", "year": 1997},
        {"name": "Transformers", "title": "Arquitectura clave en NLP y modelos generativos.", "year": 2017, "url": "https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)"},
    ],
    tool_items=[
        {"name": "Colab", "title": "Notebook cloud para entrenamiento rápido.", "year": 2018, "url": "https://colab.research.google.com/"},
        {"name": "Weights & Biases", "title": "Seguimiento de experimentos y observabilidad ML.", "year": 2017, "url": "https://wandb.ai/"},
    ],
    lib_items=[
        {"name": "PyTorch", "title": "Framework de deep learning dinámico.", "year": 2016, "url": "https://pytorch.org/"},
        {"name": "TensorFlow", "title": "Framework de deep learning de Google.", "year": 2015, "url": "https://www.tensorflow.org/"},
        {"name": "Keras", "title": "API de alto nivel para redes neuronales.", "year": 2015, "url": "https://keras.io/"},
    ],
    resource_items=[
        {"name": "documentación PyTorch", "title": "Documentación oficial de PyTorch.", "url": "https://pytorch.org/docs/stable/index.html"},
        {"name": "documentación TensorFlow", "title": "Documentación oficial de TensorFlow.", "url": "https://www.tensorflow.org/api_docs"},
    ],
    dataset_items=[
        {"name": "MNIST", "title": "Dataset clásico de dígitos manuscritos."},
        {"name": "CIFAR-10", "title": "Dataset clásico de clasificación de imágenes."},
        {"name": "ImageNet", "title": "Dataset de gran escala para visión.", "url": "https://www.image-net.org/"},
    ],
    year=2006,
    description="Aprendizaje profundo basado en redes neuronales con múltiples capas."
)

add_taxonomy_branch(
    "Inteligencia Artificial",
    "Procesamiento de Lenguaje Natural",
    concept_items=[
        {"name": "tokenización", "title": "Separación de texto en unidades manejables."},
        {"name": "embeddings", "title": "Representaciones vectoriales densas del lenguaje."},
        {"name": "clasificación de texto", "title": "Asignación de categorías a textos."},
        {"name": "NER", "title": "Reconocimiento de entidades nombradas."},
        {"name": "traducción", "title": "Conversión automática entre idiomas."},
        {"name": "QA", "title": "Sistemas de preguntas y respuestas."},
    ],
    tool_items=[
        {"name": "Hugging Face Hub", "title": "Repositorio de modelos, datasets y demos.", "year": 2020, "url": "https://huggingface.co/"},
    ],
    lib_items=[
        {"name": "Transformers", "title": "Librería de Hugging Face para transformers.", "year": 2019, "url": "https://huggingface.co/docs/transformers/index"},
        {"name": "spaCy NLP", "title": "Librería para NLP orientado a producción.", "year": 2015, "url": "https://spacy.io/"},
        {"name": "NLTK", "title": "Toolkit académico para procesamiento de lenguaje natural.", "year": 2001, "url": "https://www.nltk.org/"},
        {"name": "sentence-transformers", "title": "Embeddings semánticos para búsqueda y similitud.", "year": 2019, "url": "https://www.sbert.net/"},
    ],
    resource_items=[
        {"name": "Hugging Face", "title": "Recurso central de NLP y GenAI.", "url": "https://huggingface.co/"},
        {"name": "Papers with Code", "title": "Papers, benchmarks y código.", "url": "https://paperswithcode.com/"},
    ],
    dataset_items=[
        {"name": "SQuAD", "title": "Dataset de preguntas y respuestas extractivas."},
        {"name": "IMDB", "title": "Dataset clásico de sentimiento."},
        {"name": "Common Crawl", "title": "Gran corpus web reutilizado en LLMs.", "url": "https://commoncrawl.org/"},
        {"name": "CoNLL", "title": "Benchmarks clásicos para NER y parsing."},
    ],
    year=1950,
    description="Área dedicada a entender, analizar y generar lenguaje humano."
)

add_taxonomy_branch(
    "Inteligencia Artificial",
    "Visión por Computador",
    concept_items=[
        {"name": "clasificación de imágenes", "title": "Predicción de la clase principal de una imagen."},
        {"name": "detección de objetos", "title": "Ubicación y clasificación de objetos."},
        {"name": "segmentación", "title": "División semántica o por instancia."},
        {"name": "OCR", "title": "Reconocimiento óptico de caracteres."},
        {"name": "tracking", "title": "Seguimiento temporal de objetos."},
    ],
    tool_items=[
        {"name": "Label Studio", "title": "Herramienta de anotación de datos.", "year": 2019, "url": "https://labelstud.io/"},
        {"name": "Roboflow", "title": "Plataforma de visión y gestión de datasets.", "year": 2020, "url": "https://roboflow.com/"},
    ],
    lib_items=[
        {"name": "OpenCV Vision", "title": "Librería para visión por computador.", "year": 2000, "url": "https://opencv.org/"},
        {"name": "YOLO", "title": "Familia de modelos para detección en tiempo real.", "year": 2016, "url": "https://docs.ultralytics.com/"},
        {"name": "Detectron2", "title": "Framework de Meta para detección y segmentación.", "year": 2019, "url": "https://github.com/facebookresearch/detectron2"},
        {"name": "TensorFlow Vision", "title": "Colección de modelos y utilidades de visión."},
    ],
    resource_items=[
        {"name": "OpenCV docs", "title": "Documentación oficial de OpenCV.", "url": "https://docs.opencv.org/"},
        {"name": "Roboflow Universe", "title": "Colección pública de datasets de visión.", "url": "https://universe.roboflow.com/"},
    ],
    dataset_items=[
        {"name": "COCO", "title": "Benchmark estándar de detección y segmentación."},
        {"name": "Pascal VOC", "title": "Dataset clásico de visión."},
        {"name": "Open Images", "title": "Dataset abierto de gran escala.", "url": "https://storage.googleapis.com/openimages/web/index.html"},
    ],
    year=1966,
    description="Área que permite interpretar imágenes, videos y escenas visuales."
)

add_taxonomy_branch(
    "Inteligencia Artificial",
    "IA Generativa",
    concept_items=[
        {"name": "LLM", "title": "Modelos de lenguaje de gran escala.", "year": 2018},
        {"name": "difusión", "title": "Modelos generativos basados en difusión.", "year": 2015},
        {"name": "prompting", "title": "Diseño de instrucciones para sistemas generativos.", "year": 2022},
        {"name": "RAG", "title": "Retrieval-Augmented Generation para respuestas apoyadas en fuentes.", "year": 2020},
        {"name": "agentes", "title": "Sistemas que usan herramientas y ejecutan acciones.", "year": 2023},
        {"name": "fine-tuning", "title": "Adaptación de modelos preentrenados a tareas específicas.", "year": 2018},
    ],
    tool_items=[
        {"name": "OpenAI Playground", "title": "Entorno de pruebas para modelos generativos.", "url": "https://platform.openai.com/playground"},
        {"name": "Hugging Face Spaces", "title": "Demos interactivas de modelos.", "url": "https://huggingface.co/spaces"},
    ],
    lib_items=[
        {"name": "Transformers GenAI", "title": "Librería base para modelos generativos.", "year": 2019, "url": "https://huggingface.co/docs/transformers/index"},
        {"name": "LangChain", "title": "Framework para cadenas, agentes y apps LLM.", "year": 2022, "url": "https://python.langchain.com/"},
        {"name": "LangGraph", "title": "Framework para agentes con grafos de estado.", "year": 2024, "url": "https://langchain-ai.github.io/langgraph/"},
        {"name": "LlamaIndex", "title": "Framework para RAG y apps basadas en conocimiento.", "year": 2023, "url": "https://www.llamaindex.ai/"},
        {"name": "Diffusers", "title": "Librería para modelos de difusión.", "year": 2022, "url": "https://huggingface.co/docs/diffusers/index"},
    ],
    resource_items=[
        {"name": "Hugging Face GenAI", "title": "Repositorio y documentación de modelos generativos.", "url": "https://huggingface.co/"},
        {"name": "documentación OpenAI", "title": "Documentación oficial de OpenAI.", "url": "https://platform.openai.com/docs/"},
    ],
    dataset_items=[
        {"name": "The Pile", "title": "Gran corpus textual para preentrenamiento."},
        {"name": "datasets instruccionales", "title": "Conjuntos usados para instruction tuning."},
        {"name": "corpus conversacionales", "title": "Datos de diálogo para modelos conversacionales."},
    ],
    year=2020,
    description="Modelos capaces de generar texto, imágenes, audio, código u otro contenido."
)

add_taxonomy_branch(
    "Inteligencia Artificial",
    "Ciencia de Datos",
    concept_items=[
        {"name": "limpieza de datos", "title": "Preparación y corrección de calidad de datos."},
        {"name": "análisis exploratorio", "title": "Exploración inicial de variables y patrones."},
        {"name": "estadística descriptiva", "title": "Resumen cuantitativo de datos."},
        {"name": "inferencia", "title": "Generalización y contraste estadístico."},
        {"name": "visualización", "title": "Representación gráfica de hallazgos."},
        {"name": "feature engineering", "title": "Construcción y transformación de variables útiles."},
    ],
    tool_items=[
        {"name": "Power BI", "title": "Plataforma de BI y dashboards.", "year": 2015, "url": "https://powerbi.microsoft.com/"},
        {"name": "Tableau", "title": "Plataforma de visualización y BI.", "year": 2003, "url": "https://www.tableau.com/"},
        {"name": "Excel", "title": "Herramienta extendida para análisis tabular.", "year": 1985, "url": "https://www.microsoft.com/microsoft-365/excel"},
    ],
    lib_items=[
        {"name": "Pandas DS", "title": "Manipulación de datos tabulares.", "year": 2008, "url": "https://pandas.pydata.org/docs/"},
        {"name": "NumPy DS", "title": "Computación numérica base.", "year": 2006, "url": "https://numpy.org/doc/"},
        {"name": "Matplotlib DS", "title": "Gráficos base para análisis.", "year": 2003, "url": "https://matplotlib.org/stable/"},
        {"name": "Plotly", "title": "Gráficos interactivos.", "year": 2015, "url": "https://plotly.com/python/"},
        {"name": "SciPy", "title": "Herramientas científicas para Python.", "year": 2001, "url": "https://scipy.org/"},
        {"name": "statsmodels", "title": "Modelado estadístico clásico.", "year": 2010, "url": "https://www.statsmodels.org/"},
    ],
    resource_items=[
        {"name": "Kaggle", "title": "Competencias, notebooks y datasets.", "url": "https://www.kaggle.com/"},
        {"name": "StatQuest", "title": "Recurso pedagógico de estadística y ML.", "url": "https://www.youtube.com/@statquest"},
    ],
    dataset_items=[
        {"name": "Kaggle datasets", "title": "Colección amplia de datasets abiertos."},
        {"name": "data.gov", "title": "Portal de datos abiertos de EE. UU.", "url": "https://www.data.gov/"},
        {"name": "datos.gob.cl", "title": "Portal de datos abiertos de Chile.", "url": "https://datos.gob.cl/"},
    ],
    year=1970,
    description="Disciplina de preparación, análisis, modelado y visualización de datos."
)

add_taxonomy_branch(
    "Inteligencia Artificial",
    "MLOps",
    concept_items=[
        {"name": "versionado de modelos", "title": "Seguimiento de artefactos y versiones."},
        {"name": "pipelines ML", "title": "Flujos automatizados de entrenamiento y despliegue."},
        {"name": "serving", "title": "Exposición de modelos para inferencia."},
        {"name": "drift", "title": "Cambio de distribución o desempeño en producción."},
        {"name": "feature store", "title": "Gestión consistente de variables."},
        {"name": "monitoreo", "title": "Seguimiento de performance y salud del modelo."},
    ],
    tool_items=[
        {"name": "MLflow", "title": "Tracking y ciclo de vida de modelos.", "year": 2018, "url": "https://mlflow.org/"},
        {"name": "Kubeflow", "title": "Plataforma de ML sobre Kubernetes.", "year": 2017, "url": "https://www.kubeflow.org/"},
        {"name": "Airflow", "title": "Orquestación de pipelines.", "year": 2015, "url": "https://airflow.apache.org/"},
        {"name": "Weights & Biases MLOps", "title": "Observabilidad y experimentación.", "year": 2017, "url": "https://wandb.ai/"},
    ],
    lib_items=[
        {"name": "MLflow SDK", "title": "SDK y APIs para MLflow."},
        {"name": "Feast", "title": "Feature store open-source.", "year": 2019, "url": "https://feast.dev/"},
        {"name": "BentoML", "title": "Serving y empaquetado de modelos.", "year": 2019, "url": "https://www.bentoml.com/"},
        {"name": "Evidently", "title": "Monitoreo de calidad y drift.", "year": 2021, "url": "https://www.evidentlyai.com/"},
    ],
    resource_items=[
        {"name": "documentación MLflow", "title": "Documentación oficial de MLflow.", "url": "https://mlflow.org/docs/latest/index.html"},
        {"name": "guías MLOps", "title": "Buenas prácticas para producción ML."},
    ],
    dataset_items=[
        {"name": "train", "title": "Conjunto de entrenamiento."},
        {"name": "validation", "title": "Conjunto de validación."},
        {"name": "test", "title": "Conjunto de prueba."},
        {"name": "benchmark sets", "title": "Datasets de comparación y evaluación."},
    ],
    year=2015,
    description="Prácticas para desplegar, monitorear y mantener modelos en producción."
)

add_taxonomy_branch(
    "Inteligencia Artificial",
    "Ética y Gobernanza de IA",
    concept_items=[
        {"name": "sesgo algorítmico", "title": "Distorsiones y discriminaciones en sistemas algorítmicos."},
        {"name": "explicabilidad", "title": "Capacidad de interpretar decisiones del modelo."},
        {"name": "fairness", "title": "Equidad en resultados y tratamiento."},
        {"name": "privacidad", "title": "Protección de datos y uso responsable."},
        {"name": "auditoría", "title": "Evaluación formal del comportamiento del sistema."},
    ],
    tool_items=[
        {"name": "dashboards de monitoreo", "title": "Paneles para seguimiento de comportamiento y riesgo."},
    ],
    lib_items=[
        {"name": "SHAP", "title": "Explicabilidad basada en Shapley values.", "year": 2017, "url": "https://shap.readthedocs.io/"},
        {"name": "LIME", "title": "Explicabilidad local de modelos.", "year": 2016, "url": "https://github.com/marcotcr/lime"},
        {"name": "Fairlearn", "title": "Herramientas para medir y mitigar inequidad.", "year": 2020, "url": "https://fairlearn.org/"},
    ],
    resource_items=[
        {"name": "OECD AI Principles", "title": "Principios internacionales para IA responsable.", "url": "https://oecd.ai/en/ai-principles"},
        {"name": "NIST AI RMF", "title": "Marco de gestión de riesgos para IA.", "url": "https://www.nist.gov/itl/ai-risk-management-framework"},
    ],
    dataset_items=[
        {"name": "datasets de auditoría de sesgo", "title": "Conjuntos usados para evaluar sesgo y fairness."},
    ],
    year=2016,
    description="Marco ético, regulatorio y técnico para desarrollar IA responsable."
)

# =========================================================
# Ingeniería de Software
# =========================================================
add_taxonomy_branch(
    "Ingeniería de Software",
    "Fundamentos de Programación",
    concept_items=[
        {"name": "algoritmos", "title": "Secuencias de pasos para resolver problemas."},
        {"name": "estructuras de datos", "title": "Formas de organizar y acceder a información."},
        {"name": "POO", "title": "Programación orientada a objetos."},
        {"name": "programación funcional", "title": "Paradigma basado en funciones puras."},
        {"name": "complejidad algorítmica", "title": "Costo temporal y espacial de una solución."},
    ],
    tool_items=[
        {"name": "VS Code", "title": "Editor ampliamente usado para desarrollo.", "year": 2015, "url": "https://code.visualstudio.com/"},
        {"name": "IntelliJ", "title": "IDE popular para desarrollo multipropósito.", "year": 2001, "url": "https://www.jetbrains.com/idea/"},
    ],
    lib_items=[
        {"name": "según lenguaje", "title": "Las librerías cambian según el ecosistema del lenguaje."},
    ],
    resource_items=[
        {"name": "documentación oficial", "title": "Documentación de lenguajes y estándares."},
        {"name": "GeeksforGeeks", "title": "Portal amplio de algoritmos y programación.", "url": "https://www.geeksforgeeks.org/"},
    ],
    dataset_items=[],
    year=1968,
    description="Bases teóricas y prácticas para programar sistemas de software."
)

add_taxonomy_branch(
    "Ingeniería de Software",
    "Desarrollo de Aplicaciones",
    concept_items=[
        {"name": "backend", "title": "Lógica de negocio, persistencia y servicios."},
        {"name": "frontend", "title": "Interfaz visual y experiencia del usuario."},
        {"name": "APIs", "title": "Interfaces de comunicación entre sistemas."},
        {"name": "microservicios", "title": "Arquitectura distribuida de servicios pequeños."},
        {"name": "integración", "title": "Conexión e interoperabilidad entre sistemas."},
    ],
    tool_items=[
        {"name": "Postman", "title": "Pruebas y exploración de APIs.", "year": 2012, "url": "https://www.postman.com/"},
        {"name": "Swagger", "title": "Documentación y diseño de APIs.", "year": 2011, "url": "https://swagger.io/"},
    ],
    lib_items=[
        {"name": "FastAPI Apps", "title": "Framework para APIs rápidas en Python.", "year": 2018, "url": "https://fastapi.tiangolo.com/"},
        {"name": "Django", "title": "Framework web full-stack para Python.", "year": 2005, "url": "https://www.djangoproject.com/"},
        {"name": "Flask", "title": "Microframework web para Python.", "year": 2010, "url": "https://flask.palletsprojects.com/"},
        {"name": "Spring Boot", "title": "Framework Java para apps empresariales.", "year": 2014, "url": "https://spring.io/projects/spring-boot"},
        {"name": "Express", "title": "Framework web minimalista para Node.js.", "year": 2010, "url": "https://expressjs.com/"},
        {"name": "React", "title": "Biblioteca para interfaces web.", "year": 2013, "url": "https://react.dev/"},
    ],
    resource_items=[
        {"name": "MDN", "title": "Recurso técnico sólido para web.", "url": "https://developer.mozilla.org/"},
        {"name": "documentación FastAPI", "title": "Documentación oficial de FastAPI.", "url": "https://fastapi.tiangolo.com/"},
    ],
    dataset_items=[
        {"name": "mock data", "title": "Datos simulados para desarrollo y pruebas."},
        {"name": "JSONPlaceholder", "title": "API falsa para pruebas rápidas.", "url": "https://jsonplaceholder.typicode.com/"},
    ],
    year=1990,
    description="Construcción de aplicaciones, servicios y APIs."
)

add_taxonomy_branch(
    "Ingeniería de Software",
    "Bases de Datos",
    concept_items=[
        {"name": "modelo relacional", "title": "Organización tabular con claves y relaciones."},
        {"name": "NoSQL", "title": "Modelos alternativos de almacenamiento de datos."},
        {"name": "normalización", "title": "Reducción de redundancia y mejora del diseño."},
        {"name": "consultas", "title": "Extracción y manipulación de información."},
        {"name": "transacciones", "title": "Unidades lógicas con atomicidad y consistencia."},
        {"name": "índices", "title": "Estructuras de aceleración de búsqueda."},
    ],
    tool_items=[
        {"name": "DBeaver", "title": "Cliente universal de bases de datos.", "year": 2011, "url": "https://dbeaver.io/"},
        {"name": "pgAdmin", "title": "Administración de PostgreSQL.", "year": 1998, "url": "https://www.pgadmin.org/"},
        {"name": "SSMS", "title": "SQL Server Management Studio.", "year": 2005, "url": "https://learn.microsoft.com/sql/ssms/"},
    ],
    lib_items=[
        {"name": "SQLAlchemy", "title": "ORM y toolkit SQL para Python.", "year": 2005, "url": "https://www.sqlalchemy.org/"},
        {"name": "psycopg2", "title": "Driver PostgreSQL para Python.", "year": 2001, "url": "https://www.psycopg.org/"},
        {"name": "pymongo", "title": "Driver MongoDB para Python.", "year": 2009, "url": "https://pymongo.readthedocs.io/"},
        {"name": "Hibernate", "title": "ORM para Java.", "year": 2001, "url": "https://hibernate.org/"},
    ],
    resource_items=[
        {"name": "PostgreSQL docs", "title": "Documentación oficial de PostgreSQL.", "url": "https://www.postgresql.org/docs/"},
        {"name": "SQLBolt", "title": "Tutorial interactivo de SQL.", "url": "https://sqlbolt.com/"},
    ],
    dataset_items=[
        {"name": "Chinook", "title": "Base de ejemplo para SQL."},
        {"name": "Northwind", "title": "Base histórica de ejemplo."},
        {"name": "AdventureWorks", "title": "Base de ejemplo de Microsoft."},
    ],
    year=1970,
    description="Modelado, consulta, administración y uso de sistemas de datos."
)

add_taxonomy_branch(
    "Ingeniería de Software",
    "Arquitectura de Software",
    concept_items=[
        {"name": "monolito", "title": "Aplicación integrada en una sola unidad desplegable."},
        {"name": "arquitectura hexagonal", "title": "Arquitectura orientada a puertos y adaptadores."},
        {"name": "clean architecture", "title": "Separación fuerte por capas y dependencias."},
        {"name": "DDD", "title": "Diseño guiado por el dominio."},
        {"name": "event-driven", "title": "Arquitectura basada en eventos."},
    ],
    tool_items=[
        {"name": "Draw.io", "title": "Diagramación rápida de arquitectura.", "year": 2005, "url": "https://app.diagrams.net/"},
        {"name": "PlantUML", "title": "Diagramas como código.", "year": 2009, "url": "https://plantuml.com/"},
        {"name": "Structurizr", "title": "Modelado arquitectónico con enfoque C4.", "year": 2014, "url": "https://structurizr.com/"},
    ],
    lib_items=[
        {"name": "Spring Cloud", "title": "Componentes de arquitectura distribuida sobre Spring.", "year": 2015, "url": "https://spring.io/projects/spring-cloud"},
        {"name": "Kafka clients", "title": "Clientes para sistemas event-driven.", "year": 2011, "url": "https://kafka.apache.org/documentation/"},
    ],
    resource_items=[
        {"name": "Martin Fowler", "title": "Referencia clave en arquitectura y diseño.", "url": "https://martinfowler.com/"},
        {"name": "C4 Model", "title": "Modelo de visualización arquitectónica.", "url": "https://c4model.com/"},
    ],
    dataset_items=[],
    year=1990,
    description="Diseño estructural de sistemas y decisiones técnicas de alto nivel."
)

add_taxonomy_branch(
    "Ingeniería de Software",
    "DevOps",
    concept_items=[
        {"name": "CI/CD", "title": "Integración y despliegue continuos."},
        {"name": "automatización", "title": "Automatización de build, test y despliegue."},
        {"name": "observabilidad", "title": "Métricas, logs y trazas para entender sistemas."},
        {"name": "contenedores", "title": "Empaquetado reproducible de aplicaciones."},
        {"name": "IaC", "title": "Infraestructura definida como código."},
    ],
    tool_items=[
        {"name": "Jenkins", "title": "Automatización de pipelines CI/CD.", "year": 2011, "url": "https://www.jenkins.io/"},
        {"name": "GitHub Actions", "title": "Automatización integrada en GitHub.", "year": 2019, "url": "https://github.com/features/actions"},
        {"name": "GitLab CI/CD", "title": "Pipelines integrados en GitLab.", "year": 2015, "url": "https://docs.gitlab.com/ee/ci/"},
        {"name": "Docker", "title": "Contenedores reproducibles.", "year": 2013, "url": "https://www.docker.com/"},
        {"name": "Kubernetes", "title": "Orquestación de contenedores.", "year": 2014, "url": "https://kubernetes.io/"},
        {"name": "Terraform", "title": "Infraestructura como código.", "year": 2014, "url": "https://developer.hashicorp.com/terraform/docs"},
    ],
    lib_items=[
        {"name": "runners", "title": "Ejecutores de jobs de automatización."},
        {"name": "scripts pipeline", "title": "Definiciones YAML o scripts para CI/CD."},
    ],
    resource_items=[
        {"name": "docs Docker", "title": "Documentación oficial de Docker.", "url": "https://docs.docker.com/"},
        {"name": "docs Kubernetes", "title": "Documentación oficial de Kubernetes.", "url": "https://kubernetes.io/docs/home/"},
    ],
    dataset_items=[
        {"name": "logs de pipelines", "title": "Registros operativos de integración y despliegue."},
    ],
    year=2009,
    description="Automatización del ciclo de entrega de software y operación."
)

add_taxonomy_branch(
    "Ingeniería de Software",
    "Testing y Calidad",
    concept_items=[
        {"name": "testing unitario", "title": "Validación aislada de componentes."},
        {"name": "testing integración", "title": "Validación de interacción entre módulos."},
        {"name": "TDD", "title": "Desarrollo guiado por pruebas."},
        {"name": "QA", "title": "Aseguramiento de calidad del producto."},
        {"name": "code review", "title": "Revisión técnica de cambios de código."},
    ],
    tool_items=[
        {"name": "SonarQube", "title": "Análisis estático y calidad de código.", "year": 2008, "url": "https://www.sonarsource.com/products/sonarqube/"},
        {"name": "Selenium", "title": "Automatización de pruebas web.", "year": 2004, "url": "https://www.selenium.dev/"},
        {"name": "Postman QA", "title": "Pruebas de APIs y colecciones.", "year": 2012, "url": "https://www.postman.com/"},
    ],
    lib_items=[
        {"name": "pytest", "title": "Framework de testing para Python.", "year": 2004, "url": "https://docs.pytest.org/"},
        {"name": "JUnit", "title": "Framework clásico de testing para Java.", "year": 1997, "url": "https://junit.org/"},
        {"name": "Cypress", "title": "Testing end-to-end moderno para web.", "year": 2017, "url": "https://www.cypress.io/"},
    ],
    resource_items=[
        {"name": "Test Automation University", "title": "Ruta de aprendizaje de automatización.", "url": "https://testautomationu.applitools.com/"},
    ],
    dataset_items=[
        {"name": "datos de prueba", "title": "Conjuntos controlados para validación."},
    ],
    year=1999,
    description="Prácticas y herramientas para asegurar calidad del software."
)

add_taxonomy_branch(
    "Ingeniería de Software",
    "Gestión de Proyectos",
    concept_items=[
        {"name": "Scrum", "title": "Marco ágil basado en iteraciones cortas."},
        {"name": "Kanban", "title": "Sistema visual para flujo de trabajo."},
        {"name": "requisitos", "title": "Necesidades y restricciones del sistema."},
        {"name": "historias de usuario", "title": "Forma práctica de representar necesidades del usuario."},
    ],
    tool_items=[
        {"name": "Jira", "title": "Gestión de proyectos y tickets.", "year": 2002, "url": "https://www.atlassian.com/software/jira"},
        {"name": "Trello", "title": "Tableros ligeros para trabajo visual.", "year": 2011, "url": "https://trello.com/"},
        {"name": "Azure Boards", "title": "Gestión de backlog y seguimiento de trabajo.", "year": 2018, "url": "https://learn.microsoft.com/azure/devops/boards/"},
    ],
    lib_items=[
        {"name": "no aplica mucho", "title": "Generalmente se apoya más en herramientas que en librerías."},
    ],
    resource_items=[
        {"name": "Scrum Guide", "title": "Guía oficial de Scrum.", "url": "https://scrumguides.org/"},
    ],
    dataset_items=[],
    year=1995,
    description="Organización, coordinación y seguimiento del trabajo de software."
)

# =========================================================
# Cloud Computing
# =========================================================
add_taxonomy_branch(
    "Cloud Computing",
    "Infraestructura Cloud",
    concept_items=[
        {"name": "IaaS", "title": "Infraestructura como servicio."},
        {"name": "virtualización", "title": "Abstracción de recursos físicos."},
        {"name": "elasticidad", "title": "Ajuste dinámico a la demanda."},
        {"name": "alta disponibilidad", "title": "Diseño resiliente a fallos."},
    ],
    tool_items=[
        {"name": "AWS Console", "title": "Portal de gestión de AWS.", "year": 2006, "url": "https://aws.amazon.com/"},
        {"name": "Azure Portal", "title": "Portal de gestión de Azure.", "year": 2010, "url": "https://portal.azure.com/"},
        {"name": "GCP Console", "title": "Portal de gestión de GCP.", "year": 2008, "url": "https://console.cloud.google.com/"},
    ],
    lib_items=[
        {"name": "boto3", "title": "SDK de AWS para Python.", "year": 2015, "url": "https://boto3.amazonaws.com/v1/documentation/api/latest/index.html"},
        {"name": "azure-sdk", "title": "SDK de Azure para Python.", "url": "https://learn.microsoft.com/python/api/overview/azure/"},
        {"name": "google-cloud-sdk", "title": "SDKs de Google Cloud.", "url": "https://cloud.google.com/python/docs/reference"},
    ],
    resource_items=[
        {"name": "AWS docs", "title": "Documentación oficial de AWS.", "url": "https://docs.aws.amazon.com/"},
        {"name": "Microsoft Learn", "title": "Ruta oficial de aprendizaje Microsoft.", "url": "https://learn.microsoft.com/"},
        {"name": "Google Cloud docs", "title": "Documentación oficial de GCP.", "url": "https://cloud.google.com/docs"},
    ],
    dataset_items=[
        {"name": "AWS Open Data", "title": "Programas y datasets abiertos en AWS.", "url": "https://registry.opendata.aws/"},
        {"name": "Azure Open Datasets", "title": "Datasets abiertos curados por Azure.", "url": "https://azure.microsoft.com/services/open-datasets/"},
    ],
    year=2006,
    description="Fundamentos de infraestructura y recursos computacionales en la nube."
)

add_taxonomy_branch(
    "Cloud Computing",
    "Servicios Cloud",
    concept_items=[
        {"name": "PaaS", "title": "Plataforma como servicio."},
        {"name": "SaaS", "title": "Software como servicio."},
        {"name": "serverless", "title": "Modelo sin administración directa de servidores."},
        {"name": "managed services", "title": "Servicios administrados por el proveedor."},
    ],
    tool_items=[
        {"name": "Lambda", "title": "Funciones serverless de AWS.", "year": 2014, "url": "https://aws.amazon.com/lambda/"},
        {"name": "Azure Functions", "title": "Funciones serverless de Azure.", "year": 2016, "url": "https://azure.microsoft.com/services/functions/"},
        {"name": "Cloud Run", "title": "Ejecución serverless de contenedores en GCP.", "year": 2019, "url": "https://cloud.google.com/run"},
    ],
    lib_items=[
        {"name": "SDKs cloud", "title": "Clientes y SDKs para consumir servicios gestionados."},
    ],
    resource_items=[
        {"name": "documentación oficial cloud", "title": "Documentación base de servicios cloud."},
    ],
    dataset_items=[
        {"name": "datasets públicos cloud", "title": "Datasets disponibles a través de proveedores cloud."},
    ],
    year=2008,
    description="Capas de servicio y modelos de consumo en cloud."
)

add_taxonomy_branch(
    "Cloud Computing",
    "Redes y Sistemas",
    concept_items=[
        {"name": "redes virtuales", "title": "Segmentación lógica de redes cloud."},
        {"name": "subredes", "title": "Particiones internas dentro de redes virtuales."},
        {"name": "balanceadores", "title": "Distribución de tráfico entre instancias."},
        {"name": "DNS", "title": "Resolución de nombres."},
        {"name": "VPN", "title": "Conectividad segura entre redes."},
        {"name": "VM", "title": "Máquinas virtuales bajo demanda."},
        {"name": "administración Linux/Windows", "title": "Gestión operativa de sistemas en nube."},
    ],
    tool_items=[
        {"name": "EC2", "title": "Instancias virtuales de AWS.", "year": 2006, "url": "https://aws.amazon.com/ec2/"},
        {"name": "Azure VM", "title": "Máquinas virtuales de Azure.", "year": 2010, "url": "https://azure.microsoft.com/services/virtual-machines/"},
        {"name": "VPC", "title": "Red virtual privada en AWS.", "year": 2009, "url": "https://aws.amazon.com/vpc/"},
        {"name": "VNets", "title": "Redes virtuales en Azure.", "year": 2010, "url": "https://learn.microsoft.com/azure/virtual-network/"},
    ],
    lib_items=[
        {"name": "Paramiko", "title": "Automatización SSH en Python.", "year": 2003, "url": "https://www.paramiko.org/"},
        {"name": "Ansible modules", "title": "Módulos para automatización de infraestructura.", "year": 2012, "url": "https://docs.ansible.com/"},
    ],
    resource_items=[
        {"name": "guías de arquitectura cloud", "title": "Patrones y referencia de arquitectura en nube."},
    ],
    dataset_items=[
        {"name": "logs de red", "title": "Registros operativos y de tráfico."},
        {"name": "métricas de sistemas", "title": "Métricas de CPU, memoria, red y disco."},
    ],
    year=2009,
    description="Conectividad, instancias y operación de sistemas en cloud."
)

add_taxonomy_branch(
    "Cloud Computing",
    "Datos en la Nube",
    concept_items=[
        {"name": "data lake", "title": "Almacenamiento flexible de datos a gran escala."},
        {"name": "data warehouse", "title": "Plataforma analítica estructurada."},
        {"name": "bases de datos gestionadas", "title": "Motores DB operados por el proveedor."},
        {"name": "almacenamiento objeto", "title": "Storage escalable basado en objetos."},
    ],
    tool_items=[
        {"name": "S3", "title": "Object storage de AWS.", "year": 2006, "url": "https://aws.amazon.com/s3/"},
        {"name": "Azure Blob", "title": "Object storage de Azure.", "year": 2010, "url": "https://azure.microsoft.com/services/storage/blobs/"},
        {"name": "BigQuery", "title": "Data warehouse serverless de Google.", "year": 2011, "url": "https://cloud.google.com/bigquery"},
        {"name": "Redshift", "title": "Data warehouse de AWS.", "year": 2012, "url": "https://aws.amazon.com/redshift/"},
        {"name": "Snowflake", "title": "Plataforma cloud de datos.", "year": 2014, "url": "https://www.snowflake.com/"},
    ],
    lib_items=[
        {"name": "clientes SQL/cloud", "title": "Drivers y clientes para acceso a datos cloud."},
    ],
    resource_items=[
        {"name": "arquitectura de datos cloud", "title": "Patrones de almacenamiento y analítica en nube."},
    ],
    dataset_items=[
        {"name": "open datasets hospedados", "title": "Datasets alojados y consumibles desde cloud."},
    ],
    year=2010,
    description="Servicios de almacenamiento, analítica y datos administrados en nube."
)

add_taxonomy_branch(
    "Cloud Computing",
    "Seguridad Cloud",
    concept_items=[
        {"name": "IAM", "title": "Gestión de identidades y accesos."},
        {"name": "cifrado", "title": "Protección criptográfica de datos."},
        {"name": "control de acceso", "title": "Políticas y permisos por recurso."},
        {"name": "cumplimiento", "title": "Alineación con normativas y estándares."},
    ],
    tool_items=[
        {"name": "IAM consoles", "title": "Consolas de administración de identidades y accesos."},
        {"name": "Key Vault", "title": "Gestión de secretos y claves en Azure.", "year": 2015, "url": "https://azure.microsoft.com/services/key-vault/"},
        {"name": "Secrets Manager", "title": "Gestión de secretos en AWS.", "year": 2018, "url": "https://aws.amazon.com/secrets-manager/"},
    ],
    lib_items=[
        {"name": "SDKs de seguridad", "title": "Clientes para integrar servicios de seguridad cloud."},
    ],
    resource_items=[
        {"name": "CIS Benchmarks", "title": "Buenas prácticas de hardening y configuración.", "url": "https://www.cisecurity.org/cis-benchmarks/"},
        {"name": "cloud security docs", "title": "Documentación oficial de seguridad cloud."},
    ],
    dataset_items=[
        {"name": "logs de auditoría", "title": "Eventos de acceso, cambios y cumplimiento."},
    ],
    year=2012,
    description="Protección de entornos cloud, identidades y cumplimiento."
)

add_taxonomy_branch(
    "Cloud Computing",
    "Automatización y Operación",
    concept_items=[
        {"name": "provisioning", "title": "Creación automatizada de infraestructura."},
        {"name": "autoescalado", "title": "Escalado dinámico según demanda."},
        {"name": "monitoreo", "title": "Seguimiento del estado de la plataforma."},
        {"name": "observabilidad", "title": "Visibilidad de comportamiento mediante señales."},
        {"name": "despliegue automatizado", "title": "Automatización de releases en cloud."},
    ],
    tool_items=[
        {"name": "Terraform Cloud", "title": "Automatización con Terraform.", "year": 2014, "url": "https://developer.hashicorp.com/terraform"},
        {"name": "Ansible", "title": "Automatización declarativa de sistemas.", "year": 2012, "url": "https://www.ansible.com/"},
        {"name": "CloudWatch", "title": "Monitoreo de AWS.", "year": 2009, "url": "https://aws.amazon.com/cloudwatch/"},
        {"name": "Azure Monitor", "title": "Monitoreo de Azure.", "year": 2014, "url": "https://azure.microsoft.com/services/monitor/"},
        {"name": "Prometheus", "title": "Sistema de monitoreo basado en métricas.", "year": 2014, "url": "https://prometheus.io/"},
        {"name": "Grafana", "title": "Visualización de métricas y logs.", "year": 2014, "url": "https://grafana.com/"},
    ],
    lib_items=[
        {"name": "IaC modules", "title": "Módulos reutilizables de infraestructura como código."},
    ],
    resource_items=[
        {"name": "Well-Architected Framework", "title": "Marco de buenas prácticas cloud.", "url": "https://aws.amazon.com/architecture/well-architected/"},
    ],
    dataset_items=[
        {"name": "métricas de infraestructura", "title": "Datos observables de disponibilidad, consumo y rendimiento."},
    ],
    year=2010,
    description="Operación continua, monitoreo y automatización de entornos cloud."
)

# =========================================================
# Ciberseguridad
# =========================================================
add_taxonomy_branch(
    "Ciberseguridad",
    "Seguridad de Redes",
    concept_items=[
        {"name": "firewalls", "title": "Filtrado de tráfico según reglas."},
        {"name": "IDS/IPS", "title": "Detección y prevención de intrusiones."},
        {"name": "segmentación", "title": "Separación de zonas y superficies de ataque."},
        {"name": "VPN segura", "title": "Túneles privados cifrados."},
        {"name": "análisis de tráfico", "title": "Inspección de flujos y eventos de red."},
    ],
    tool_items=[
        {"name": "Wireshark", "title": "Análisis de tráfico de red.", "year": 1998, "url": "https://www.wireshark.org/"},
        {"name": "pfSense", "title": "Firewall y routing open-source.", "year": 2004, "url": "https://www.pfsense.org/"},
        {"name": "Cisco tools", "title": "Herramientas y plataformas del ecosistema Cisco."},
    ],
    lib_items=[
        {"name": "Scapy", "title": "Manipulación y análisis de paquetes en Python.", "year": 2003, "url": "https://scapy.net/"},
        {"name": "Suricata", "title": "Motor IDS/IPS y NSM open-source.", "year": 2010, "url": "https://suricata.io/"},
    ],
    resource_items=[
        {"name": "Cisco Academy", "title": "Formación en redes y seguridad.", "url": "https://www.netacad.com/"},
        {"name": "MITRE ATT&CK", "title": "Marco de tácticas y técnicas de adversarios.", "url": "https://attack.mitre.org/"},
    ],
    dataset_items=[
        {"name": "PCAP", "title": "Capturas de paquetes para análisis."},
        {"name": "CICIDS", "title": "Dataset de tráfico para intrusión y clasificación."},
    ],
    year=1985,
    description="Defensa del perímetro, tráfico y conectividad de red."
)

add_taxonomy_branch(
    "Ciberseguridad",
    "Seguridad de Sistemas",
    concept_items=[
        {"name": "hardening", "title": "Reducción de superficie de ataque."},
        {"name": "gestión de parches", "title": "Actualización oportuna de vulnerabilidades."},
        {"name": "malware", "title": "Software malicioso y sus técnicas."},
        {"name": "logs", "title": "Registros del comportamiento del sistema."},
        {"name": "privilegios", "title": "Gestión de acceso mínimo necesario."},
    ],
    tool_items=[
        {"name": "Wazuh", "title": "Plataforma open-source de seguridad y monitoreo.", "year": 2015, "url": "https://wazuh.com/"},
        {"name": "Defender", "title": "Protección endpoint de Microsoft.", "url": "https://www.microsoft.com/security/business/microsoft-defender"},
        {"name": "EDR/XDR tools", "title": "Herramientas avanzadas de detección y respuesta."},
    ],
    lib_items=[
        {"name": "YARA", "title": "Reglas para identificación de malware.", "year": 2013, "url": "https://virustotal.github.io/yara/"},
        {"name": "Sigma", "title": "Lenguaje genérico para reglas de detección.", "year": 2017, "url": "https://sigmahq.io/"},
    ],
    resource_items=[
        {"name": "CIS Benchmarks Sistemas", "title": "Benchmarks de hardening de sistemas.", "url": "https://www.cisecurity.org/cis-benchmarks/"},
        {"name": "SANS", "title": "Recursos de formación y práctica en seguridad.", "url": "https://www.sans.org/"},
    ],
    dataset_items=[
        {"name": "logs de sistema", "title": "Registros del sistema operativo y aplicaciones."},
        {"name": "malware samples académicos", "title": "Muestras controladas para análisis seguro."},
    ],
    year=1990,
    description="Protección de hosts, sistemas operativos y endpoints."
)

add_taxonomy_branch(
    "Ciberseguridad",
    "Seguridad de Aplicaciones",
    concept_items=[
        {"name": "OWASP Top 10", "title": "Riesgos comunes de seguridad web."},
        {"name": "validación de entradas", "title": "Prevención de inyección y datos maliciosos."},
        {"name": "gestión de secretos", "title": "Protección de credenciales y tokens."},
        {"name": "autenticación segura", "title": "Mecanismos robustos de acceso."},
    ],
    tool_items=[
        {"name": "Burp Suite", "title": "Suite para pruebas de seguridad web.", "year": 2003, "url": "https://portswigger.net/burp"},
        {"name": "OWASP ZAP", "title": "Scanner open-source de seguridad web.", "year": 2010, "url": "https://www.zaproxy.org/"},
        {"name": "Vault", "title": "Gestión de secretos de HashiCorp.", "year": 2015, "url": "https://developer.hashicorp.com/vault"},
    ],
    lib_items=[
        {"name": "Spring Security", "title": "Seguridad para aplicaciones Spring.", "year": 2004, "url": "https://spring.io/projects/spring-security"},
        {"name": "OAuth libs", "title": "Librerías para flujos OAuth2."},
        {"name": "JWT libs", "title": "Implementaciones para manejo de JWT."},
    ],
    resource_items=[
        {"name": "OWASP", "title": "Comunidad y guía base para AppSec.", "url": "https://owasp.org/"},
        {"name": "NIST", "title": "Marcos y estándares de seguridad.", "url": "https://www.nist.gov/"},
    ],
    dataset_items=[
        {"name": "vulnerabilidad de prueba", "title": "Ejemplos de fallas para práctica controlada."},
        {"name": "datos mock inseguros", "title": "Datos simulados para validación y hardening."},
    ],
    year=2001,
    description="Prácticas para construir aplicaciones seguras."
)

add_taxonomy_branch(
    "Ciberseguridad",
    "Gestión de Identidades",
    concept_items=[
        {"name": "autenticación", "title": "Verificación de identidad."},
        {"name": "autorización", "title": "Control de permisos y acceso."},
        {"name": "MFA", "title": "Autenticación multifactor."},
        {"name": "IAM", "title": "Gestión de identidades y accesos."},
        {"name": "Zero Trust", "title": "Modelo de confianza cero."},
    ],
    tool_items=[
        {"name": "Okta", "title": "Plataforma de identidad y acceso.", "year": 2009, "url": "https://www.okta.com/"},
        {"name": "Azure AD/Entra", "title": "Identidad corporativa de Microsoft.", "year": 2008, "url": "https://www.microsoft.com/security/business/identity-access/microsoft-entra-id"},
        {"name": "Keycloak", "title": "Gestión open-source de identidad.", "year": 2014, "url": "https://www.keycloak.org/"},
    ],
    lib_items=[
        {"name": "OAuth2", "title": "Estándar de autorización delegada.", "year": 2012},
        {"name": "OpenID Connect", "title": "Capa de identidad sobre OAuth2.", "year": 2014},
    ],
    resource_items=[
        {"name": "docs IAM", "title": "Documentación de identidades y acceso."},
    ],
    dataset_items=[
        {"name": "logs de acceso", "title": "Eventos de login, permisos y autenticación."},
    ],
    year=2005,
    description="Control de identidad, acceso y confianza."
)

add_taxonomy_branch(
    "Ciberseguridad",
    "Monitoreo y Respuesta",
    concept_items=[
        {"name": "SIEM", "title": "Correlación y análisis centralizado de eventos."},
        {"name": "SOC", "title": "Centro de operaciones de seguridad."},
        {"name": "respuesta a incidentes", "title": "Proceso de contención, análisis y recuperación."},
        {"name": "correlación de eventos", "title": "Vinculación de señales para detección."},
    ],
    tool_items=[
        {"name": "Splunk", "title": "Plataforma de análisis de logs y SIEM.", "year": 2003, "url": "https://www.splunk.com/"},
        {"name": "QRadar", "title": "SIEM empresarial.", "year": 2001, "url": "https://www.ibm.com/products/qradar-siem"},
        {"name": "Elastic", "title": "Búsqueda, observabilidad y seguridad.", "year": 2010, "url": "https://www.elastic.co/"},
    ],
    lib_items=[
        {"name": "reglas Sigma", "title": "Reglas portables de detección para SIEM."},
    ],
    resource_items=[
        {"name": "MITRE", "title": "Marco ATT&CK y conocimiento táctico.", "url": "https://attack.mitre.org/"},
        {"name": "blue team labs", "title": "Práctica enfocada en defensa."},
    ],
    dataset_items=[
        {"name": "logs SIEM", "title": "Eventos agregados para correlación."},
        {"name": "eventos de seguridad", "title": "Alertas y trazas asociadas a incidentes."},
    ],
    year=2000,
    description="Detección operativa, análisis y respuesta frente a incidentes."
)

add_taxonomy_branch(
    "Ciberseguridad",
    "Gobernanza y Cumplimiento",
    concept_items=[
        {"name": "riesgo", "title": "Identificación y tratamiento de riesgos."},
        {"name": "políticas", "title": "Normas y controles internos."},
        {"name": "auditoría", "title": "Evaluación del cumplimiento de controles."},
        {"name": "cumplimiento", "title": "Alineación con marcos regulatorios."},
        {"name": "continuidad operacional", "title": "Resiliencia y recuperación ante interrupciones."},
    ],
    tool_items=[
        {"name": "GRC platforms", "title": "Herramientas de gobernanza, riesgo y cumplimiento."},
    ],
    lib_items=[
        {"name": "no aplica mucho GRC", "title": "Predominan marcos, procesos y plataformas especializadas."},
    ],
    resource_items=[
        {"name": "ISO 27001", "title": "Norma de gestión de seguridad de la información.", "url": "https://www.iso.org/standard/27001"},
        {"name": "NIST CSF", "title": "Cybersecurity Framework de NIST.", "url": "https://www.nist.gov/cyberframework"},
    ],
    dataset_items=[
        {"name": "matrices de riesgo", "title": "Artefactos de evaluación de impacto y probabilidad."},
    ],
    year=1995,
    description="Gobierno, riesgos y cumplimiento en seguridad."
)

# =========================================================
# Robótica e IoT
# =========================================================
add_taxonomy_branch(
    "Robótica e IoT",
    "Electrónica y Hardware",
    concept_items=[
        {"name": "microcontroladores", "title": "Controladores compactos para dispositivos embebidos."},
        {"name": "energía", "title": "Alimentación y gestión energética de dispositivos."},
        {"name": "señales", "title": "Tratamiento de señales digitales y analógicas."},
        {"name": "circuitos", "title": "Diseño e interconexión de componentes electrónicos."},
    ],
    tool_items=[
        {"name": "multímetro", "title": "Medición de voltaje, corriente y resistencia."},
        {"name": "simuladores", "title": "Simulación de circuitos y prototipos."},
        {"name": "Arduino IDE", "title": "Entorno para placas Arduino.", "year": 2005, "url": "https://www.arduino.cc/en/software"},
    ],
    lib_items=[
        {"name": "Arduino libs", "title": "Librerías para sensores, motores y periféricos."},
        {"name": "MicroPython", "title": "Implementación ligera de Python para microcontroladores.", "year": 2014, "url": "https://micropython.org/"},
    ],
    resource_items=[
        {"name": "Arduino docs", "title": "Documentación oficial de Arduino.", "url": "https://docs.arduino.cc/"},
        {"name": "Adafruit Learning", "title": "Tutoriales y guías de electrónica.", "url": "https://learn.adafruit.com/"},
    ],
    dataset_items=[
        {"name": "telemetría simple", "title": "Lecturas básicas de sensores y estado."},
    ],
    year=1961,
    description="Base física y electrónica de sistemas robóticos e IoT."
)

add_taxonomy_branch(
    "Robótica e IoT",
    "Sensores y Actuadores",
    concept_items=[
        {"name": "lectura de sensores", "title": "Captura de variables físicas del entorno."},
        {"name": "servos", "title": "Actuadores de posición controlada."},
        {"name": "motores", "title": "Elementos de movimiento rotacional o lineal."},
        {"name": "relés", "title": "Conmutación eléctrica de cargas."},
        {"name": "sensores de distancia", "title": "Detección de proximidad y profundidad."},
        {"name": "sensores de temperatura", "title": "Medición térmica del entorno."},
    ],
    tool_items=[
        {"name": "Raspberry Pi", "title": "Computador compacto para prototipos y edge.", "year": 2012, "url": "https://www.raspberrypi.com/"},
        {"name": "ESP32", "title": "Microcontrolador con conectividad Wi-Fi/Bluetooth.", "year": 2016, "url": "https://www.espressif.com/"},
        {"name": "Arduino", "title": "Plataforma de prototipado electrónico.", "year": 2005, "url": "https://www.arduino.cc/"},
    ],
    lib_items=[
        {"name": "gpiozero", "title": "Control sencillo de GPIO en Raspberry Pi.", "year": 2015, "url": "https://gpiozero.readthedocs.io/"},
        {"name": "RPi.GPIO", "title": "Librería clásica de GPIO para Raspberry Pi."},
        {"name": "sensor libs", "title": "Librerías específicas para sensores y actuadores."},
    ],
    resource_items=[
        {"name": "Raspberry Pi docs", "title": "Documentación oficial Raspberry Pi.", "url": "https://www.raspberrypi.com/documentation/"},
    ],
    dataset_items=[
        {"name": "lecturas temporales de sensores", "title": "Series temporales provenientes del mundo físico."},
    ],
    year=1980,
    description="Captura y acción física mediante sensores y actuadores."
)

add_taxonomy_branch(
    "Robótica e IoT",
    "Sistemas Embebidos",
    concept_items=[
        {"name": "firmware", "title": "Software de bajo nivel que gobierna el hardware."},
        {"name": "tiempo real", "title": "Respuesta garantizada en ventanas temporales acotadas."},
        {"name": "edge computing", "title": "Procesamiento cercano al dispositivo o sensor."},
        {"name": "optimización de recursos", "title": "Uso eficiente de CPU, memoria y energía."},
    ],
    tool_items=[
        {"name": "PlatformIO", "title": "Entorno moderno para desarrollo embebido.", "year": 2014, "url": "https://platformio.org/"},
        {"name": "STM32CubeIDE", "title": "IDE para desarrollo sobre STM32.", "year": 2019, "url": "https://www.st.com/en/development-tools/stm32cubeide.html"},
    ],
    lib_items=[
        {"name": "FreeRTOS", "title": "Sistema operativo de tiempo real para embebidos.", "year": 2003, "url": "https://www.freertos.org/"},
        {"name": "MicroPython Embebido", "title": "Python ligero en sistemas embebidos.", "year": 2014, "url": "https://micropython.org/"},
    ],
    resource_items=[
        {"name": "docs embebidos", "title": "Recursos técnicos de plataformas embebidas."},
    ],
    dataset_items=[
        {"name": "logs embebidos", "title": "Registros de ejecución y diagnóstico de dispositivos."},
    ],
    year=1975,
    description="Desarrollo de software cercano al hardware y control del dispositivo."
)

add_taxonomy_branch(
    "Robótica e IoT",
    "Comunicación y Redes IoT",
    concept_items=[
        {"name": "MQTT", "title": "Protocolo ligero de mensajería publish/subscribe.", "year": 1999},
        {"name": "Wi-Fi", "title": "Conectividad inalámbrica local."},
        {"name": "Bluetooth", "title": "Comunicación inalámbrica de corto alcance."},
        {"name": "UART", "title": "Protocolo serie asíncrono."},
        {"name": "I2C", "title": "Bus de comunicación entre chips."},
        {"name": "SPI", "title": "Protocolo serie síncrono de alta velocidad."},
    ],
    tool_items=[
        {"name": "brokers MQTT", "title": "Intermediarios de mensajería IoT."},
        {"name": "analizadores seriales", "title": "Herramientas para inspección de comunicación serial."},
    ],
    lib_items=[
        {"name": "paho-mqtt", "title": "Cliente MQTT para Python.", "year": 2014, "url": "https://eclipse.dev/paho/"},
        {"name": "pyserial", "title": "Comunicación serial desde Python.", "year": 2001, "url": "https://pyserial.readthedocs.io/"},
    ],
    resource_items=[
        {"name": "MQTT docs", "title": "Documentación y recursos del protocolo MQTT."},
    ],
    dataset_items=[
        {"name": "mensajes de telemetría", "title": "Paquetes y eventos emitidos por dispositivos."},
    ],
    year=1999,
    description="Protocolos y medios de comunicación para dispositivos conectados."
)

add_taxonomy_branch(
    "Robótica e IoT",
    "Control y Automatización",
    concept_items=[
        {"name": "PID", "title": "Control proporcional, integral y derivativo."},
        {"name": "navegación", "title": "Movimiento y ubicación en el espacio."},
        {"name": "automatización", "title": "Ejecución de tareas sin intervención continua."},
        {"name": "control de movimiento", "title": "Gestión precisa de trayectorias y actuadores."},
    ],
    tool_items=[
        {"name": "PLC", "title": "Controlador lógico programable para automatización industrial."},
        {"name": "simuladores de control", "title": "Entornos para validar lógica de control."},
    ],
    lib_items=[
        {"name": "ROS", "title": "Middleware y ecosistema para robótica.", "year": 2007, "url": "https://www.ros.org/"},
        {"name": "control libraries", "title": "Librerías para navegación, cinemática y control."},
    ],
    resource_items=[
        {"name": "ROS docs", "title": "Documentación y tutoriales de ROS.", "url": "https://docs.ros.org/"},
    ],
    dataset_items=[
        {"name": "trayectorias", "title": "Datos de movimiento y rutas."},
        {"name": "telemetría de control", "title": "Señales y estados asociados al lazo de control."},
    ],
    year=1960,
    description="Lógica de control, actuación y automatización de procesos físicos."
)

add_taxonomy_branch(
    "Robótica e IoT",
    "Visión e Inteligencia Integrada",
    concept_items=[
        {"name": "detección de objetos robótica", "title": "Percepción visual aplicada a sistemas físicos."},
        {"name": "seguimiento", "title": "Tracking visual en contextos robóticos."},
        {"name": "percepción", "title": "Comprensión del entorno a partir de sensores."},
        {"name": "decisión local", "title": "Capacidad de actuar cerca del borde o dispositivo."},
    ],
    tool_items=[
        {"name": "cámaras", "title": "Sensores visuales para captura de escena."},
        {"name": "Jetson", "title": "Plataforma edge para visión e IA.", "year": 2014, "url": "https://developer.nvidia.com/embedded-computing"},
        {"name": "Raspberry Pi Vision", "title": "Plataforma compacta para visión embebida.", "year": 2012, "url": "https://www.raspberrypi.com/"},
    ],
    lib_items=[
        {"name": "OpenCV IoT", "title": "Procesamiento visual en edge y robótica.", "year": 2000, "url": "https://opencv.org/"},
        {"name": "YOLO IoT", "title": "Detección rápida para edge.", "year": 2016, "url": "https://docs.ultralytics.com/"},
        {"name": "TensorFlow Lite", "title": "Inferencia optimizada en dispositivos.", "year": 2017, "url": "https://www.tensorflow.org/lite"},
    ],
    resource_items=[
        {"name": "OpenCV docs IoT", "title": "Documentación para visión aplicada.", "url": "https://docs.opencv.org/"},
        {"name": "Roboflow IoT", "title": "Datasets y flujos de visión aplicados a edge.", "url": "https://roboflow.com/"},
    ],
    dataset_items=[
        {"name": "COCO visión robótica", "title": "Dataset reutilizado en percepción robótica."},
        {"name": "datasets de visión robótica", "title": "Conjuntos específicos para percepción embarcada."},
    ],
    year=2000,
    description="Combinación de percepción visual, IA y decisión sobre dispositivos físicos."
)

add_taxonomy_branch(
    "Robótica e IoT",
    "Plataformas y Nube IoT",
    concept_items=[
        {"name": "gestión remota", "title": "Administración centralizada de dispositivos."},
        {"name": "ingestión de telemetría", "title": "Recepción y almacenamiento de eventos IoT."},
        {"name": "monitoreo de dispositivos", "title": "Seguimiento del estado y comportamiento de nodos IoT."},
    ],
    tool_items=[
        {"name": "AWS IoT", "title": "Servicios IoT administrados de AWS.", "year": 2015, "url": "https://aws.amazon.com/iot/"},
        {"name": "Azure IoT Hub", "title": "Plataforma IoT de Microsoft.", "year": 2015, "url": "https://azure.microsoft.com/services/iot-hub/"},
        {"name": "Node-RED", "title": "Flujos visuales para integración y automatización.", "year": 2013, "url": "https://nodered.org/"},
    ],
    lib_items=[
        {"name": "SDKs IoT", "title": "Clientes para integración con plataformas IoT."},
    ],
    resource_items=[
        {"name": "documentación IoT cloud", "title": "Recursos para integración entre dispositivos y nube."},
    ],
    dataset_items=[
        {"name": "históricos de sensores", "title": "Series históricas de telemetría."},
        {"name": "eventos IoT", "title": "Registros de estado y operación de dispositivos."},
    ],
    year=2013,
    description="Integración de dispositivos con plataformas cloud y operación remota."
)

# =========================================================
# Relaciones adicionales entre ramas
# =========================================================
cross_links = [
    ("Machine Learning", "Ciencia de Datos"),
    ("Deep Learning", "IA Generativa"),
    ("Procesamiento de Lenguaje Natural", "IA Generativa"),
    ("Visión por Computador", "Robótica e IoT"),
    ("MLOps", "DevOps"),
    ("MLOps", "Cloud Computing"),
    ("Arquitectura de Software", "Cloud Computing"),
    ("Seguridad Cloud", "Ciberseguridad"),
    ("Comunicación y Redes IoT", "Cloud Computing"),
    ("Python", "Inteligencia Artificial"),
    ("Python", "Desarrollo de Aplicaciones"),
]
for src, dst in cross_links:
    if src in nodes and dst in nodes:
        add_edge(src, dst, "relaciona")

# =========================================================
# Utilidades del grafo
# =========================================================

def enrich_title(name, attrs):
    lines = [f"{name}"]
    if attrs.get("kind"):
        lines.append(f"Tipo: {attrs['kind']}")
    if attrs.get("domain"):
        lines.append(f"Dominio: {attrs['domain']}")
    if attrs.get("year"):
        lines.append(f"Año: {attrs['year']}")
    if attrs.get("title"):
        lines.append("")
        lines.append(attrs["title"])

    item_details = attrs.get("items_detail", [])
    if item_details:
        lines.append("")
        lines.append("Detalle del grupo:")
        for item in item_details:
            lines.append("")
            header = f"- {item.get('name', '')}"
            meta_parts = []
            if item.get("kind"):
                meta_parts.append(item["kind"])
            if item.get("year"):
                meta_parts.append(str(item["year"]))
            if meta_parts:
                header += f" ({' | '.join(meta_parts)})"
            lines.append(header)
            if item.get("title"):
                lines.append(f"  Uso: {item['title']}")
            if item.get("functions"):
                lines.append(f"  Funciones principales: {', '.join(item['functions'])}")
            if item.get("url"):
                lines.append(f"  Link: {item['url']}")

    if attrs.get("functions"):
        lines.append("")
        lines.append("Funciones clave:")
        lines.append(", ".join(attrs["functions"]))
    if attrs.get("url"):
        lines.append("")
        lines.append(f"Recurso: {attrs['url']}")
    return "\n".join(lines)

def build_detail_html(name, attrs):
    def esc(v):
        return html.escape(str(v))

    parts = [f"<h3 style='margin:0 0 8px 0'>{esc(name)}</h3>"]
    meta = []
    if attrs.get("kind"):
        meta.append(f"<b>Tipo:</b> {esc(attrs['kind'])}")
    if attrs.get("domain"):
        meta.append(f"<b>Dominio:</b> {esc(attrs['domain'])}")
    if attrs.get("year"):
        meta.append(f"<b>Año:</b> {esc(attrs['year'])}")
    if meta:
        parts.append("<p style='margin:0 0 10px 0'>" + " | ".join(meta) + "</p>")
    if attrs.get("title"):
        parts.append(f"<p style='margin:0 0 12px 0'>{esc(attrs['title'])}</p>")

    item_details = attrs.get("items_detail", [])
    if item_details:
        parts.append("<div style='margin-top:10px'>")
        parts.append("<b>Detalle del grupo</b>")
        parts.append("<ul style='margin-top:8px'>")
        for item in item_details:
            item_line = f"<li><b>{esc(item.get('name',''))}</b>"
            meta_bits = []
            if item.get("kind"):
                meta_bits.append(esc(item["kind"]))
            if item.get("year"):
                meta_bits.append(esc(item["year"]))
            if meta_bits:
                item_line += f" <span style='color:#666'>({' | '.join(meta_bits)})</span>"
            if item.get("title"):
                item_line += f"<br><span>{esc(item['title'])}</span>"
            if item.get("functions"):
                item_line += f"<br><span><b>Funciones principales:</b> {esc(', '.join(item['functions']))}</span>"
            if item.get("url"):
                url = esc(item["url"])
                item_line += f"<br><a href='{url}' target='_blank'>Ver más</a>"
            item_line += "</li>"
            parts.append(item_line)
        parts.append("</ul></div>")

    if attrs.get("examples"):
        parts.append("<div style='margin-top:10px'><b>Ejemplos</b><ul>")
        for ex in attrs["examples"]:
            parts.append(f"<li>{esc(ex)}</li>")
        parts.append("</ul></div>")

    if attrs.get("functions"):
        parts.append(f"<p><b>Funciones clave:</b> {esc(', '.join(attrs['functions']))}</p>")
    if attrs.get("url"):
        url = esc(attrs["url"])
        parts.append(f"<p><a href='{url}' target='_blank'>Ir al recurso</a></p>")

    return "".join(parts)

def build_graph(graph_nodes, graph_edges):
    G = nx.Graph()
    for name, attrs in graph_nodes.items():
        attrs = dict(attrs)
        attrs["full_title"] = enrich_title(name, attrs)
        attrs["detail_html"] = build_detail_html(name, attrs)
        G.add_node(name, **attrs)
    for src, dst, rel in graph_edges:
        if src in graph_nodes and dst in graph_nodes:
            G.add_edge(src, dst, relation=rel)
    return G

def filter_graph(G, selected_kinds, selected_domains):
    H = G.copy()
    remove_nodes = []
    for n, attrs in H.nodes(data=True):
        if selected_kinds and attrs.get("kind") not in selected_kinds:
            remove_nodes.append(n)
            continue
        if selected_domains and attrs.get("domain") not in selected_domains:
            remove_nodes.append(n)
            continue
    H.remove_nodes_from(remove_nodes)
    return H

def create_timeline_df(graph_nodes):
    rows = []
    for name, attrs in graph_nodes.items():
        year = attrs.get("year")
        if year is None:
            continue
        rows.append({
            "Concepto": name,
            "Tipo": attrs.get("kind", ""),
            "Dominio": attrs.get("domain", ""),
            "Año": year,
            "Descripción": attrs.get("title", ""),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    if sort_by_epoch:
        return df.sort_values(["Año", "Dominio", "Concepto"], ascending=[True, True, True]).reset_index(drop=True)
    return df.sort_values(["Dominio", "Año", "Concepto"]).reset_index(drop=True)


def inject_click_behavior(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    detail_panel = """
<div id="selected-node-panel" style="margin-top:16px;padding:14px;border:1px solid #ddd;border-radius:12px;background:#fafafa;font-family:Arial, sans-serif;">
  <div style="font-weight:700;margin-bottom:8px;">Detalle del nodo</div>
  <div id="selected-node-content" style="color:#333;">Haz click sobre un nodo para ver aquí su descripción ampliada, usos, funciones principales y enlaces.</div>
</div>
"""

    js = """
<script type="text/javascript">
function waitForNetwork() {
  if (typeof network === "undefined" || typeof nodes === "undefined") {
    setTimeout(waitForNetwork, 500);
    return;
  }

  function setPanel(html) {
    const panel = document.getElementById("selected-node-content");
    if (panel) {
      panel.innerHTML = html;
    }
  }

  network.on("click", function(params) {
    if (!params.nodes || params.nodes.length === 0) return;
    const nodeId = params.nodes[0];
    const node = nodes.get(nodeId);
    if (node && node.detail_html) {
      setPanel(node.detail_html);
    } else if (node && node.title) {
      setPanel("<pre style='white-space:pre-wrap;font-family:Arial,sans-serif;'>" + node.title + "</pre>");
    }
  });
}
waitForNetwork();
</script>
"""
    if "</body>" in html_content:
        html_content = html_content.replace("</body>", detail_panel + js + "\n</body>")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

def render_graph(G):
    net = Network(height="780px", width="100%", bgcolor="#ffffff", font_color="#111111")
    hierarchical = None
    if tipo_mapa == "Jerárquico LR":
        hierarchical = {"enabled": True, "direction": "LR", "sortMethod": "directed"}
    elif tipo_mapa == "Jerárquico UD":
        hierarchical = {"enabled": True, "direction": "UD", "sortMethod": "directed"}

    for name, attrs in G.nodes(data=True):
        domain = attrs.get("domain", "General")
        kind = attrs.get("kind", "concepto")
        base_color = TYPE_COLOR_OVERRIDES.get(kind, DOMAIN_COLORS.get(domain, DOMAIN_COLORS["General"]))
        style = KIND_STYLES.get(kind, KIND_STYLES["concepto"])
        size = max(8, attrs.get("size", 12) + style.get("size_boost", 0))
        label = name
        if show_year_in_label and attrs.get("year"):
            label = f"{name} ({attrs['year']})"
        net.add_node(
            name,
            label=label,
            title=attrs.get("full_title", name),
            detail_html=attrs.get("detail_html", ""),
            color=base_color,
            shape=style.get("shape", "dot"),
            size=size,
            url=attrs.get("url"),
        )

    for src, dst, edge_attrs in G.edges(data=True):
        title = edge_attrs.get("relation", "")
        net.add_edge(src, dst, title=title)

    options = {
        "nodes": {
            "borderWidth": 1,
            "shadow": True,
            "font": {"size": 18, "face": "Arial"},
        },
        "edges": {
            "smooth": True,
            "color": {"inherit": True},
            "width": 1.0
        },
        "physics": {
            "enabled": physics_enabled and hierarchical is None,
            "barnesHut": {
                "gravitationalConstant": -12000,
                "centralGravity": central_gravity,
                "springLength": spring_length,
                "springConstant": 0.03,
                "damping": 0.35,
                "avoidOverlap": 1.0
            },
            "minVelocity": 0.75
        },
        "layout": {
            "improvedLayout": True,
            "hierarchical": hierarchical if hierarchical else False
        },
        "interaction": {
            "hover": True,
            "navigationButtons": True,
            "keyboard": True,
            "tooltipDelay": 120
        }
    }
    net.set_options(json.dumps(options))

    if not show_edges:
        for edge in net.edges:
            edge["hidden"] = True

    tmp_dir = tempfile.mkdtemp()
    html_path = os.path.join(tmp_dir, "mental_map.html")
    net.save_graph(html_path)
    inject_click_behavior(html_path)

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    components.html(html_content, height=980, scrolling=True)


# =========================================================
# Construcción y filtros del grafo
# =========================================================
graph_nodes = dict(nodes)
graph_edges = list(edges)

G_full = build_graph(graph_nodes, graph_edges)

all_domains = sorted({attrs.get("domain", "General") for attrs in graph_nodes.values()})
all_kinds = sorted({attrs.get("kind", "concepto") for attrs in graph_nodes.values()})
legend_kinds = [k for k in all_kinds if k != "principal"]

selected_domains = st.sidebar.multiselect(
    "Filtrar por dominio",
    all_domains,
    default=[],
)
selected_kinds = st.sidebar.multiselect(
    "Filtrar por tipo",
    all_kinds,
    default=["principal", "subarea", "concepto"] if set(["principal", "subarea", "concepto"]).issubset(set(all_kinds)) else [],
)

G_filtered = filter_graph(G_full, selected_kinds, selected_domains)

# =========================================================
# Layout principal
# =========================================================
left_col, right_col = st.columns([3.6, 1.2], gap="large")

with left_col:
    st.subheader("Mapa visual")
    st.caption(
        f"Nodos mostrados: {len(G_filtered.nodes)} | "
        f"Relaciones: {len(G_filtered.edges)}"
    )
    render_graph(G_filtered)

with right_col:
    st.subheader("Exploración rápida")

    st.markdown("**Autores / enlaces**")
    st.markdown(f"- [LinkedIn]({LINKEDIN_URL})")
    st.markdown(f"- [GitHub]({GITHUB_URL})")

    st.markdown("---")
    st.markdown("**Leyenda de tipos**")
    for kind in legend_kinds:
        if kind in KIND_STYLES:
            st.markdown(f"- **{kind}** → {KIND_STYLES[kind]['shape']}")

    st.markdown("---")
    st.markdown("**Dominios principales**")
    for name, _, _ in MAIN_DOMAINS:
        st.markdown(f"- `{name}`")

    st.markdown("---")
    st.info("El detalle ampliado aparece debajo del mapa al hacer click en un nodo. El tooltip corto sigue disponible al pasar el mouse.")

    st.markdown("---")
    st.markdown("**Submapas sugeridos**")
    suggested = [
        "Inteligencia Artificial",
        "Machine Learning",
        "Procesamiento de Lenguaje Natural",
        "IA Generativa",
        "Ingeniería de Software",
        "Python",
        "Cloud Computing",
        "Ciberseguridad",
        "Robótica e IoT",
    ]
    for s in suggested:
        st.markdown(f"- `{s}`")

# =========================================================
# Línea de tiempo
# =========================================================
if show_timeline:
    st.markdown("---")
    st.subheader("Línea de tiempo")

    visible_names = set(G_filtered.nodes)
    timeline_source_nodes = {k: v for k, v in graph_nodes.items() if k in visible_names}

    timeline_df = create_timeline_df(timeline_source_nodes)

    if timeline_df.empty:
        st.warning("No hay datos suficientes para mostrar la línea de tiempo.")
    else:
        chart = (
            alt.Chart(timeline_df)
            .mark_circle(size=120)
            .encode(
                x=alt.X("Año:Q", title="Año"),
                y=alt.Y("Dominio:N", title="Dominio", sort="-x"),
                tooltip=["Concepto", "Tipo", "Dominio", "Año", "Descripción"],
                color=alt.Color("Dominio:N", legend=None),
            )
            .properties(height=420)
            .interactive()
        )
        st.altair_chart(chart, use_container_width=True)

        with st.expander("Ver tabla cronológica"):
            st.dataframe(timeline_df, use_container_width=True)

# =========================================================
# Tabla resumen
# =========================================================
st.markdown("---")
st.subheader("Resumen tabular del submapa")

summary_rows = []
for node_name in G_filtered.nodes:
    node_data = G_filtered.nodes[node_name]
    summary_rows.append({
        "Nombre": node_name,
        "Tipo": node_data.get("kind", ""),
        "Dominio": node_data.get("domain", ""),
        "Año": node_data.get("year", ""),
        "Descripción": node_data.get("title", ""),
        "URL": node_data.get("url", ""),
    })

summary_df = pd.DataFrame(summary_rows)
if not summary_df.empty:
    if sort_by_epoch and "Año" in summary_df.columns:
        summary_df = summary_df.sort_values(["Año", "Dominio", "Nombre"], na_position="last")
    st.dataframe(summary_df, use_container_width=True)
else:
    st.warning("No hay nodos para mostrar en la tabla.")

st.markdown("---")
st.caption("Sugerencia: usa click para bajar por ramas y profundidad 1-2 para ver submapas más limpios.")
