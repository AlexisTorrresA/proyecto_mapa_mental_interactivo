import os
import json
import tempfile
from collections import deque

import altair as alt
import networkx as nx
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

st.set_page_config(page_title="Mapa mental IA interactivo", layout="wide")
st.title("Mapa mental interactivo de IA, ML, Cloud, Software, Python, Robótica y Quantum")
st.write(
    "Haz click en un nodo para enfocar su submapa. "
    "Haz doble click para abrir su recurso externo."
)

# =========================================================
# Configuración general
# =========================================================
LINKEDIN_URL = "https://www.linkedin.com/in/alexis-torres87/"
GITHUB_URL = "https://github.com/AlexisTorrresA"

KIND_STYLES = {
    "concepto":   {"shape": "dot",      "size_boost": 0},
    "herramienta":{"shape": "box",      "size_boost": -2},
    "aplicacion": {"shape": "diamond",  "size_boost": -1},
    "sitio":      {"shape": "star",     "size_boost": -2},
    "libreria":   {"shape": "triangle", "size_boost": -2},
    "dataset":    {"shape": "hexagon",  "size_boost": -2},
    "robotica":   {"shape": "square",   "size_boost": -1},
    "funcion":    {"shape": "ellipse",  "size_boost": -4},
}

DOMAIN_COLORS = {
    "IA": "#f4d35e",
    "ML": "#4ea8de",
    "Deep Learning": "#ff6b6b",
    "NLP": "#72efdd",
    "Visión": "#80ed99",
    "MLOps": "#c77dff",
    "Data Engineering": "#a8dadc",
    "Cloud": "#ffd166",
    "Software": "#06d6a0",
    "Responsible AI": "#f28482",
    "Quantum": "#9b5de5",
    "Python": "#3776ab",
    "Datos": "#8ecae6",
    "Robótica": "#f72585",
    "General": "#adb5bd",
}

# =========================================================
# Sidebar
# =========================================================
st.sidebar.header("Configuración del mapa")

tipo_mapa = st.sidebar.selectbox(
    "Tipo de mapa", ["Libre", "Jerárquico LR", "Jerárquico UD"]
)

node_distance = st.sidebar.slider("Distancia entre nodos", 100, 500, 220, 10)
spring_length = st.sidebar.slider("Longitud de resortes", 50, 400, 180, 10)
central_gravity = st.sidebar.slider("Gravedad central", 0.0, 1.0, 0.2, 0.05)
physics_enabled = st.sidebar.checkbox("Activar física", True)
show_edges = st.sidebar.checkbox("Mostrar relaciones", True)

st.sidebar.markdown("---")
st.sidebar.subheader("Vista temporal")
show_year_in_label = st.sidebar.checkbox("Mostrar años en nodos", False)
show_timeline = st.sidebar.checkbox("Mostrar línea de tiempo", True)
sort_by_epoch = st.sidebar.checkbox("Ordenar conceptos por época", True)

st.sidebar.markdown("---")
st.sidebar.subheader("Exploración")
show_python_functions = st.sidebar.checkbox("Mostrar funciones Python como nodos", False)
max_function_nodes_per_lib = st.sidebar.slider("Máx. funciones por librería", 2, 12, 5, 1)
depth = st.sidebar.slider("Profundidad del submapa", 0, 3, 1, 1)

# =========================================================
# Datos base
# =========================================================
nodes = {
    # -----------------------------
    # Tronco principal
    # -----------------------------
    "Inteligencia Artificial": {
        "kind": "concepto",
        "domain": "IA",
        "size": 38,
        "year": 1956,
        "title": "Campo general que busca crear sistemas capaces de realizar tareas que normalmente requieren inteligencia humana.",
        "examples": ["Asistentes virtuales", "Diagnóstico asistido", "Automatización inteligente"],
        "tools": ["Python", "PyTorch", "TensorFlow"],
        "url": "https://es.wikipedia.org/wiki/Inteligencia_artificial",
        "tags": ["IA", "sistemas inteligentes"],
    },
    "Machine Learning": {
        "kind": "concepto",
        "domain": "ML",
        "size": 30,
        "year": 1959,
        "title": "Subárea de la IA donde los modelos aprenden patrones a partir de datos sin programar cada regla manualmente.",
        "examples": ["Predicción de demanda", "Scoring de riesgo", "Clasificación automática"],
        "tools": ["scikit-learn", "XGBoost"],
        "url": "https://es.wikipedia.org/wiki/Aprendizaje_autom%C3%A1tico",
        "tags": ["ML", "modelos", "aprendizaje"],
    },
    "Deep Learning": {
        "kind": "concepto",
        "domain": "Deep Learning",
        "size": 30,
        "year": 2006,
        "title": "Subárea del machine learning basada en redes neuronales profundas.",
        "examples": ["Clasificación de imágenes", "LLMs", "Reconocimiento de voz"],
        "tools": ["PyTorch", "TensorFlow"],
        "url": "https://es.wikipedia.org/wiki/Aprendizaje_profundo",
    },
    "Generative AI": {
        "kind": "concepto",
        "domain": "IA",
        "size": 28,
        "year": 2020,
        "title": "Modelos capaces de generar texto, imágenes, audio, código u otro contenido.",
        "examples": ["Chatbots", "Generación de imágenes", "Copilots"],
        "tools": ["Transformers", "Diffusers", "OpenAI API"],
        "url": "https://en.wikipedia.org/wiki/Generative_artificial_intelligence",
    },
    "NLP": {
        "kind": "concepto",
        "domain": "NLP",
        "size": 24,
        "year": 1950,
        "title": "Procesamiento del lenguaje natural para entender, analizar y generar texto o voz.",
        "examples": ["Clasificación de texto", "NER", "Resumen automático"],
        "tools": ["spaCy", "Transformers", "NLTK"],
        "url": "https://es.wikipedia.org/wiki/Procesamiento_del_lenguaje_natural",
    },
    "Visión Artificial": {
        "kind": "concepto",
        "domain": "Visión",
        "size": 24,
        "year": 1966,
        "title": "Área que permite a las máquinas interpretar imágenes, videos y contenido visual.",
        "examples": ["Detección de objetos", "OCR", "Segmentación"],
        "tools": ["OpenCV", "YOLO", "PyTorch"],
        "url": "https://es.wikipedia.org/wiki/Visi%C3%B3n_artificial",
    },
    "Cloud Computing": {
        "kind": "concepto",
        "domain": "Cloud",
        "size": 24,
        "year": 2006,
        "title": "Uso de infraestructura, plataformas y servicios remotos para desarrollar y operar sistemas.",
        "examples": ["Desplegar APIs", "Entrenar modelos en la nube", "Almacenamiento escalable"],
        "tools": ["AWS", "Azure", "GCP", "Terraform", "Docker", "Kubernetes"],
        "python_libraries": ["boto3", "azure-storage-blob", "google-cloud-storage"],
        "url": "https://es.wikipedia.org/wiki/Computaci%C3%B3n_en_la_nube",
    },
    "Data Engineering": {
        "kind": "concepto",
        "domain": "Data Engineering",
        "size": 24,
        "year": 2010,
        "title": "Disciplina enfocada en construir pipelines, almacenamiento y procesamiento confiable de datos.",
        "examples": ["ETL", "Ingesta masiva", "Streaming"],
        "tools": ["Airflow", "Kafka", "Spark"],
        "url": "https://en.wikipedia.org/wiki/Data_engineering",
    },
    "MLOps": {
        "kind": "concepto",
        "domain": "MLOps",
        "size": 24,
        "year": 2015,
        "title": "Prácticas para desplegar, monitorear y mantener modelos de ML en producción.",
        "examples": ["Tracking de experimentos", "Model serving", "Monitoreo de drift"],
        "tools": ["MLflow", "Docker", "Kubernetes", "FastAPI"],
        "url": "https://en.wikipedia.org/wiki/MLOps",
    },
    "Python": {
        "kind": "concepto",
        "domain": "Python",
        "size": 26,
        "year": 1991,
        "title": "Lenguaje clave para IA, automatización, backend y análisis de datos.",
        "examples": ["Scripts", "APIs", "Modelado", "Visualización"],
        "tools": ["Pandas", "NumPy", "FastAPI", "Streamlit"],
        "url": "https://www.python.org/",
    },
    "Robótica": {
        "kind": "robotica",
        "domain": "Robótica",
        "size": 26,
        "year": 1961,
        "title": "Disciplina que integra mecánica, electrónica, control, software e IA.",
        "examples": ["Brazos robóticos", "Robots móviles", "Visión embarcada"],
        "tools": ["ROS", "Raspberry Pi", "Servos", "OpenCV"],
        "url": "https://en.wikipedia.org/wiki/Robotics",
    },
    "Computación Cuántica": {
        "kind": "concepto",
        "domain": "Quantum",
        "size": 24,
        "year": 1980,
        "title": "Paradigma de cómputo basado en qubits, superposición y entrelazamiento.",
        "examples": ["VQE", "QAOA", "Algoritmo de Shor"],
        "tools": ["Qiskit"],
        "url": "https://es.wikipedia.org/wiki/Computaci%C3%B3n_cu%C3%A1ntica",
    },
    "Responsible AI": {
        "kind": "concepto",
        "domain": "Responsible AI",
        "size": 24,
        "year": 2016,
        "title": "Enfoque para desarrollar IA ética, explicable, segura y alineada con normativas.",
        "examples": ["Mitigación de sesgo", "Evaluación de riesgos", "Trazabilidad"],
        "tools": ["Guardrails", "Evals"],
        "url": "https://www.ibm.com/think/topics/responsible-ai",
    },

    # -----------------------------
    # ML clásico
    # -----------------------------
    "Aprendizaje Supervisado": {
        "kind": "concepto",
        "domain": "ML",
        "size": 18,
        "year": 1950,
        "title": "Entrena modelos usando datos etiquetados.",
        "examples": ["Fraude", "Churn", "Clasificación de documentos"],
    },
    "Aprendizaje No Supervisado": {
        "kind": "concepto",
        "domain": "ML",
        "size": 18,
        "year": 1958,
        "title": "Busca patrones o grupos en datos sin etiquetas.",
        "examples": ["Segmentación de clientes", "Detección de anomalías"],
    },
    "Aprendizaje por Refuerzo": {
        "kind": "concepto",
        "domain": "ML",
        "size": 18,
        "year": 1989,
        "title": "Un agente aprende maximizando recompensas.",
        "examples": ["Juegos", "Control", "Robótica"],
    },
    "Regresión Lineal": {
        "kind": "herramienta",
        "domain": "ML",
        "size": 14,
        "year": 1805,
        "title": "Algoritmo clásico para predicción continua.",
        "examples": ["Predicción de precios", "Series simples"],
    },
    "Regresión Logística": {
        "kind": "herramienta",
        "domain": "ML",
        "size": 14,
        "year": 1958,
        "title": "Modelo clásico para clasificación binaria.",
    },
    "Árboles de Decisión": {
        "kind": "herramienta",
        "domain": "ML",
        "size": 14,
        "year": 1963,
        "title": "Modelo interpretable basado en reglas jerárquicas.",
    },
    "Random Forest": {
        "kind": "herramienta",
        "domain": "ML",
        "size": 14,
        "year": 2001,
        "title": "Conjunto de árboles para mejorar robustez.",
    },
    "XGBoost": {
        "kind": "herramienta",
        "domain": "ML",
        "size": 14,
        "year": 2014,
        "title": "Boosting potente para datos tabulares.",
        "url": "https://xgboost.readthedocs.io/",
    },
    "K-Means": {
        "kind": "herramienta",
        "domain": "ML",
        "size": 14,
        "year": 1957,
        "title": "Algoritmo de clustering por centroides.",
    },
    "PCA": {
        "kind": "herramienta",
        "domain": "ML",
        "size": 14,
        "year": 1901,
        "title": "Reducción de dimensionalidad por componentes principales.",
    },

    # -----------------------------
    # Deep learning / LLM
    # -----------------------------
    "Redes Neuronales": {
        "kind": "concepto",
        "domain": "Deep Learning",
        "size": 18,
        "year": 1943,
        "title": "Base del deep learning.",
    },
    "CNN": {
        "kind": "herramienta",
        "domain": "Deep Learning",
        "size": 14,
        "year": 1998,
        "title": "Redes convolucionales, usadas en imágenes.",
    },
    "RNN": {
        "kind": "herramienta",
        "domain": "Deep Learning",
        "size": 14,
        "year": 1986,
        "title": "Redes recurrentes para secuencias.",
    },
    "Transformers": {
        "kind": "herramienta",
        "domain": "Deep Learning",
        "size": 16,
        "year": 2017,
        "title": "Arquitectura clave en NLP y modelos generativos.",
        "url": "https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)",
    },
    "Embeddings": {
        "kind": "concepto",
        "domain": "Deep Learning",
        "size": 14,
        "year": 2003,
        "title": "Representaciones vectoriales densas.",
    },
    "Fine-tuning": {
        "kind": "aplicacion",
        "domain": "Deep Learning",
        "size": 14,
        "year": 2018,
        "title": "Ajuste de modelos preentrenados a tareas específicas.",
    },
    "LLMs": {
        "kind": "concepto",
        "domain": "NLP",
        "size": 18,
        "year": 2018,
        "title": "Modelos de lenguaje de gran escala.",
        "examples": ["Chatbots", "RAG", "Generación de código"],
    },
    "Prompt Engineering": {
        "kind": "aplicacion",
        "domain": "NLP",
        "size": 14,
        "year": 2022,
        "title": "Diseño de instrucciones efectivas para modelos generativos.",
    },
    "RAG": {
        "kind": "aplicacion",
        "domain": "NLP",
        "size": 16,
        "year": 2020,
        "title": "Retrieval-Augmented Generation.",
        "examples": ["Asistentes internos", "Búsqueda semántica con respuesta"],
    },
    "Vector DB": {
        "kind": "herramienta",
        "domain": "NLP",
        "size": 14,
        "year": 2019,
        "title": "Base de datos para búsqueda semántica sobre embeddings.",
    },
    "Agentes": {
        "kind": "aplicacion",
        "domain": "NLP",
        "size": 14,
        "year": 2023,
        "title": "Sistemas que razonan, usan herramientas y ejecutan acciones.",
    },
    "Evaluación LLM": {
        "kind": "aplicacion",
        "domain": "NLP",
        "size": 14,
        "year": 2023,
        "title": "Evaluación de calidad, seguridad y factualidad de LLMs.",
    },

    # -----------------------------
    # Visión
    # -----------------------------
    "Clasificación de Imágenes": {
        "kind": "aplicacion",
        "domain": "Visión",
        "size": 14,
        "year": 1990,
        "title": "Predice la categoría principal de una imagen.",
    },
    "Detección de Objetos": {
        "kind": "aplicacion",
        "domain": "Visión",
        "size": 14,
        "year": 2001,
        "title": "Detecta y localiza objetos en imágenes.",
    },
    "Segmentación": {
        "kind": "aplicacion",
        "domain": "Visión",
        "size": 14,
        "year": 1979,
        "title": "Divide una imagen en regiones o píxeles significativos.",
    },
    "YOLO": {
        "kind": "herramienta",
        "domain": "Visión",
        "size": 14,
        "year": 2016,
        "title": "Familia de modelos rápidos para detección en tiempo real.",
        "url": "https://docs.ultralytics.com/",
    },
    "OpenCV": {
        "kind": "libreria",
        "domain": "Visión",
        "size": 14,
        "year": 2000,
        "title": "Librería popular para procesamiento de imágenes y visión por computador.",
        "functions": ["imread", "resize", "cvtColor", "VideoCapture", "findContours"],
        "url": "https://opencv.org/",
    },

    # -----------------------------
    # MLOps / Software / Data
    # -----------------------------
    "Docker": {
        "kind": "herramienta",
        "domain": "MLOps",
        "size": 14,
        "year": 2013,
        "title": "Contenedores reproducibles para aplicaciones y modelos.",
        "url": "https://www.docker.com/",
    },
    "Kubernetes": {
        "kind": "herramienta",
        "domain": "MLOps",
        "size": 14,
        "year": 2014,
        "title": "Orquestador de contenedores.",
        "url": "https://kubernetes.io/",
    },
    "MLflow": {
        "kind": "herramienta",
        "domain": "MLOps",
        "size": 14,
        "year": 2018,
        "title": "Seguimiento de experimentos y ciclo de vida de modelos.",
        "url": "https://mlflow.org/",
    },
    "FastAPI": {
        "kind": "libreria",
        "domain": "Software",
        "size": 14,
        "year": 2018,
        "title": "Framework de Python para construir APIs rápidas.",
        "functions": ["FastAPI", "get", "post", "Depends", "BackgroundTasks"],
        "url": "https://fastapi.tiangolo.com/",
    },
    "Streamlit": {
        "kind": "libreria",
        "domain": "Python",
        "size": 14,
        "year": 2019,
        "title": "Framework Python para construir apps interactivas de datos.",
        "functions": ["title", "write", "sidebar", "selectbox", "dataframe"],
        "url": "https://streamlit.io/",
    },
    "Airflow": {
        "kind": "herramienta",
        "domain": "Data Engineering",
        "size": 14,
        "year": 2015,
        "title": "Orquestador de pipelines.",
        "url": "https://airflow.apache.org/",
    },
    "Kafka": {
        "kind": "herramienta",
        "domain": "Data Engineering",
        "size": 14,
        "year": 2011,
        "title": "Streaming y mensajería distribuida.",
        "url": "https://kafka.apache.org/",
    },
    "ETL": {
        "kind": "aplicacion",
        "domain": "Data Engineering",
        "size": 14,
        "year": 1970,
        "title": "Extracción, transformación y carga de datos.",
    },
    "Pipelines": {
        "kind": "concepto",
        "domain": "Data Engineering",
        "size": 14,
        "year": 2010,
        "title": "Flujos automatizados de procesamiento de datos.",
    },

    # -----------------------------
    # Cloud
    # -----------------------------
    "AWS": {
        "kind": "herramienta",
        "domain": "Cloud",
        "size": 14,
        "year": 2006,
        "title": "Proveedor líder de servicios cloud.",
        "url": "https://aws.amazon.com/",
    },
    "Azure": {
        "kind": "herramienta",
        "domain": "Cloud",
        "size": 14,
        "year": 2010,
        "title": "Plataforma cloud de Microsoft.",
        "url": "https://azure.microsoft.com/",
    },
    "GCP": {
        "kind": "herramienta",
        "domain": "Cloud",
        "size": 14,
        "year": 2008,
        "title": "Google Cloud Platform.",
        "url": "https://cloud.google.com/",
    },
    "Terraform": {
        "kind": "herramienta",
        "domain": "Cloud",
        "size": 14,
        "year": 2014,
        "title": "Infraestructura como código.",
        "url": "https://developer.hashicorp.com/terraform/docs",
    },
    "Serverless": {
        "kind": "concepto",
        "domain": "Cloud",
        "size": 14,
        "year": 2014,
        "title": "Modelo donde la infraestructura la gestiona el proveedor.",
    },
    "IAM": {
        "kind": "concepto",
        "domain": "Cloud",
        "size": 14,
        "year": 1999,
        "title": "Gestión de identidades y accesos.",
    },
    "Object Storage": {
        "kind": "concepto",
        "domain": "Cloud",
        "size": 14,
        "year": 2006,
        "title": "Almacenamiento basado en objetos.",
    },

    # -----------------------------
    # Python / librerías
    # -----------------------------
    "Pandas": {
        "kind": "libreria",
        "domain": "Python",
        "size": 18,
        "year": 2008,
        "title": "Manipulación de datos tabulares.",
        "examples": ["Leer CSV", "Agrupar datos", "Limpieza de columnas"],
        "functions": ["read_csv", "DataFrame", "merge", "groupby", "pivot_table", "fillna"],
        "url": "https://pandas.pydata.org/",
    },
    "NumPy": {
        "kind": "libreria",
        "domain": "Python",
        "size": 18,
        "year": 2006,
        "title": "Cálculo numérico y arreglos multidimensionales.",
        "functions": ["array", "mean", "dot", "linspace", "linalg.inv"],
        "url": "https://numpy.org/",
    },
    "Matplotlib": {
        "kind": "libreria",
        "domain": "Python",
        "size": 16,
        "year": 2003,
        "title": "Visualización en Python.",
        "functions": ["plot", "scatter", "bar", "imshow", "figure"],
        "url": "https://matplotlib.org/",
    },
    "scikit-learn": {
        "kind": "libreria",
        "domain": "Python",
        "size": 18,
        "year": 2007,
        "title": "Librería estándar de ML clásico en Python.",
        "functions": ["fit", "predict", "train_test_split", "Pipeline", "GridSearchCV"],
        "url": "https://scikit-learn.org/",
    },
    "PyTorch": {
        "kind": "libreria",
        "domain": "Python",
        "size": 18,
        "year": 2016,
        "title": "Framework de deep learning muy usado en investigación y producción.",
        "functions": ["tensor", "nn.Module", "DataLoader", "optim.Adam", "backward"],
        "url": "https://pytorch.org/",
    },
    "TensorFlow": {
        "kind": "libreria",
        "domain": "Python",
        "size": 18,
        "year": 2015,
        "title": "Framework de ML y deep learning.",
        "functions": ["keras.Sequential", "fit", "predict", "GradientTape"],
        "url": "https://www.tensorflow.org/",
    },
    "spaCy": {
        "kind": "libreria",
        "domain": "Python",
        "size": 16,
        "year": 2015,
        "title": "Librería potente para NLP industrial.",
        "functions": ["load", "nlp", "ents", "tokenizer"],
        "url": "https://spacy.io/",
    },
    "Transformers Library": {
        "kind": "libreria",
        "domain": "Python",
        "size": 16,
        "year": 2019,
        "title": "Librería de Hugging Face para modelos transformer.",
        "functions": ["pipeline", "AutoTokenizer", "AutoModel", "Trainer"],
        "url": "https://huggingface.co/docs/transformers/index",
    },

    # -----------------------------
    # Sitios y datasets
    # -----------------------------
    "Hugging Face": {
        "kind": "sitio",
        "domain": "IA",
        "size": 18,
        "year": 2016,
        "title": "Plataforma clave para modelos, datasets y demos de IA.",
        "examples": ["Descargar modelos", "Explorar datasets", "Publicar Spaces"],
        "url": "https://huggingface.co/",
    },
    "Kaggle": {
        "kind": "sitio",
        "domain": "Datos",
        "size": 18,
        "year": 2010,
        "title": "Plataforma de datasets, notebooks y competencias.",
        "url": "https://www.kaggle.com/",
    },
    "Papers with Code": {
        "kind": "sitio",
        "domain": "IA",
        "size": 18,
        "year": 2019,
        "title": "Relaciona papers con código y benchmarks.",
        "url": "https://paperswithcode.com/",
    },
    "UCI ML Repository": {
        "kind": "sitio",
        "domain": "Datos",
        "size": 16,
        "year": 1987,
        "title": "Repositorio clásico de datasets para ML.",
        "url": "https://archive.ics.uci.edu/",
    },
    "Roboflow": {
        "kind": "sitio",
        "domain": "Visión",
        "size": 16,
        "year": 2020,
        "title": "Herramientas y datasets para visión artificial.",
        "url": "https://roboflow.com/",
    },
    "Datasets": {
        "kind": "concepto",
        "domain": "Datos",
        "size": 20,
        "year": 2000,
        "title": "Colecciones de datos usadas para entrenar y evaluar modelos.",
        "examples": ["Texto", "Imágenes", "Audio", "Tabular"],
    },
    "COCO": {
        "kind": "dataset",
        "domain": "Visión",
        "size": 16,
        "year": 2014,
        "title": "Dataset popular para detección y segmentación.",
        "url": "https://cocodataset.org/",
    },
    "ImageNet": {
        "kind": "dataset",
        "domain": "Visión",
        "size": 16,
        "year": 2009,
        "title": "Dataset clásico para clasificación de imágenes.",
        "url": "https://www.image-net.org/",
    },
    "SQuAD": {
        "kind": "dataset",
        "domain": "NLP",
        "size": 16,
        "year": 2016,
        "title": "Dataset de preguntas y respuestas en NLP.",
        "url": "https://rajpurkar.github.io/SQuAD-explorer/",
    },

    # -----------------------------
    # Robótica
    # -----------------------------
    "ROS": {
        "kind": "herramienta",
        "domain": "Robótica",
        "size": 18,
        "year": 2007,
        "title": "Robot Operating System para control modular y comunicación entre nodos.",
        "url": "https://www.ros.org/",
    },
    "SLAM": {
        "kind": "aplicacion",
        "domain": "Robótica",
        "size": 16,
        "year": 1986,
        "title": "Simultaneous Localization and Mapping.",
        "examples": ["Robots móviles", "Mapeo con LiDAR"],
    },
    "Control de Movimiento": {
        "kind": "aplicacion",
        "domain": "Robótica",
        "size": 16,
        "year": 1960,
        "title": "Control y planificación de trayectorias de actuadores.",
    },
    "Servos": {
        "kind": "herramienta",
        "domain": "Robótica",
        "size": 14,
        "year": 1930,
        "title": "Actuadores usados para control angular o lineal.",
    },
    "Raspberry Pi": {
        "kind": "herramienta",
        "domain": "Robótica",
        "size": 16,
        "year": 2012,
        "title": "Computador embebido popular para prototipos robóticos.",
        "url": "https://www.raspberrypi.com/",
    },
    "Sensores": {
        "kind": "herramienta",
        "domain": "Robótica",
        "size": 14,
        "year": 1950,
        "title": "Dispositivos para medir variables del entorno o del robot.",
    },
    "Actuadores": {
        "kind": "herramienta",
        "domain": "Robótica",
        "size": 14,
        "year": 1950,
        "title": "Componentes que producen movimiento o acción física.",
    },

    # -----------------------------
    # Responsible AI / quantum
    # -----------------------------
    "Guardrails": {
        "kind": "herramienta",
        "domain": "Responsible AI",
        "size": 14,
        "year": 2023,
        "title": "Mecanismos para restringir o validar respuestas de IA.",
        "url": "https://www.guardrailsai.com/",
    },
    "Seguridad IA": {
        "kind": "concepto",
        "domain": "Responsible AI",
        "size": 14,
        "year": 2023,
        "title": "Protección contra abuso, fuga o comportamientos inseguros.",
    },
    "Qiskit": {
        "kind": "libreria",
        "domain": "Quantum",
        "size": 16,
        "year": 2017,
        "title": "SDK para programación cuántica.",
        "functions": ["QuantumCircuit", "transpile", "measure_all", "AerSimulator"],
        "url": "https://qiskit.org/",
    },
    "Quantum Machine Learning": {
        "kind": "concepto",
        "domain": "Quantum",
        "size": 16,
        "year": 2017,
        "title": "Intersección entre computación cuántica y aprendizaje automático.",
    },
}

edges = [
    # tronco
    ("Inteligencia Artificial", "Machine Learning", "subárea"),
    ("Inteligencia Artificial", "Deep Learning", "subárea"),
    ("Deep Learning", "Generative AI", "evolución"),
    ("Inteligencia Artificial", "NLP", "subárea"),
    ("Inteligencia Artificial", "Visión Artificial", "subárea"),
    ("Inteligencia Artificial", "Cloud Computing", "infraestructura"),
    ("Inteligencia Artificial", "Data Engineering", "datos"),
    ("Inteligencia Artificial", "MLOps", "operación"),
    ("Inteligencia Artificial", "Python", "lenguaje"),
    ("Inteligencia Artificial", "Robótica", "aplicación"),
    ("Inteligencia Artificial", "Responsible AI", "gobernanza"),
    ("Inteligencia Artificial", "Computación Cuántica", "frontera"),

    # ML
    ("Machine Learning", "Aprendizaje Supervisado", "tipo"),
    ("Machine Learning", "Aprendizaje No Supervisado", "tipo"),
    ("Machine Learning", "Aprendizaje por Refuerzo", "tipo"),
    ("Aprendizaje Supervisado", "Regresión Lineal", "algoritmo"),
    ("Aprendizaje Supervisado", "Regresión Logística", "algoritmo"),
    ("Aprendizaje Supervisado", "Árboles de Decisión", "algoritmo"),
    ("Aprendizaje Supervisado", "Random Forest", "algoritmo"),
    ("Aprendizaje Supervisado", "XGBoost", "algoritmo"),
    ("Aprendizaje No Supervisado", "K-Means", "algoritmo"),
    ("Aprendizaje No Supervisado", "PCA", "algoritmo"),

    # DL / NLP / LLM
    ("Deep Learning", "Redes Neuronales", "base"),
    ("Redes Neuronales", "CNN", "arquitectura"),
    ("Redes Neuronales", "RNN", "arquitectura"),
    ("Deep Learning", "Transformers", "arquitectura"),
    ("Deep Learning", "Embeddings", "representación"),
    ("Deep Learning", "Fine-tuning", "ajuste"),
    ("NLP", "LLMs", "modelo"),
    ("LLMs", "Prompt Engineering", "uso"),
    ("LLMs", "RAG", "uso"),
    ("LLMs", "Agentes", "uso"),
    ("LLMs", "Evaluación LLM", "evaluación"),
    ("RAG", "Vector DB", "infraestructura"),
    ("Transformers", "LLMs", "base"),

    # visión
    ("Visión Artificial", "Clasificación de Imágenes", "aplicación"),
    ("Visión Artificial", "Detección de Objetos", "aplicación"),
    ("Visión Artificial", "Segmentación", "aplicación"),
    ("Visión Artificial", "YOLO", "herramienta"),
    ("Visión Artificial", "OpenCV", "librería"),
    ("YOLO", "Detección de Objetos", "resuelve"),

    # MLOps / data / software
    ("MLOps", "Docker", "herramienta"),
    ("MLOps", "Kubernetes", "herramienta"),
    ("MLOps", "MLflow", "herramienta"),
    ("MLOps", "FastAPI", "serving"),
    ("Data Engineering", "ETL", "proceso"),
    ("Data Engineering", "Pipelines", "flujo"),
    ("Data Engineering", "Airflow", "orquestación"),
    ("Data Engineering", "Kafka", "streaming"),

    # Cloud
    ("Cloud Computing", "AWS", "proveedor"),
    ("Cloud Computing", "Azure", "proveedor"),
    ("Cloud Computing", "GCP", "proveedor"),
    ("Cloud Computing", "Terraform", "IaC"),
    ("Cloud Computing", "Serverless", "modelo"),
    ("Cloud Computing", "IAM", "seguridad"),
    ("Cloud Computing", "Object Storage", "almacenamiento"),
    ("Cloud Computing", "Docker", "despliegue"),
    ("Cloud Computing", "Kubernetes", "orquestación"),

    # Python
    ("Python", "Pandas", "librería"),
    ("Python", "NumPy", "librería"),
    ("Python", "Matplotlib", "librería"),
    ("Python", "scikit-learn", "librería"),
    ("Python", "PyTorch", "librería"),
    ("Python", "TensorFlow", "librería"),
    ("Python", "FastAPI", "librería"),
    ("Python", "Streamlit", "librería"),
    ("Python", "spaCy", "librería"),
    ("Python", "Transformers Library", "librería"),

    ("Machine Learning", "scikit-learn", "implementación"),
    ("Deep Learning", "PyTorch", "implementación"),
    ("Deep Learning", "TensorFlow", "implementación"),
    ("NLP", "spaCy", "implementación"),
    ("NLP", "Transformers Library", "implementación"),
    ("Visión Artificial", "PyTorch", "implementación"),

    # sitios y datasets
    ("Machine Learning", "Datasets", "requiere"),
    ("Deep Learning", "Datasets", "requiere"),
    ("NLP", "Datasets", "requiere"),
    ("Visión Artificial", "Datasets", "requiere"),
    ("Generative AI", "Hugging Face", "ecosistema"),
    ("LLMs", "Hugging Face", "ecosistema"),
    ("Machine Learning", "Kaggle", "competencias"),
    ("Deep Learning", "Papers with Code", "papers"),
    ("Datasets", "UCI ML Repository", "fuente"),
    ("Datasets", "Kaggle", "fuente"),
    ("Datasets", "Hugging Face", "fuente"),
    ("Visión Artificial", "Roboflow", "herramienta"),
    ("Visión Artificial", "COCO", "dataset"),
    ("Visión Artificial", "ImageNet", "dataset"),
    ("NLP", "SQuAD", "dataset"),

    # robótica
    ("Robótica", "ROS", "framework"),
    ("Robótica", "SLAM", "aplicación"),
    ("Robótica", "Control de Movimiento", "aplicación"),
    ("Robótica", "Servos", "actuación"),
    ("Robótica", "Raspberry Pi", "hardware"),
    ("Robótica", "Sensores", "entrada"),
    ("Robótica", "Actuadores", "salida"),
    ("Robótica", "OpenCV", "visión"),
    ("Robótica", "YOLO", "percepción"),
    ("Aprendizaje por Refuerzo", "Robótica", "uso"),

    # responsible / quantum
    ("Responsible AI", "Guardrails", "herramienta"),
    ("Responsible AI", "Seguridad IA", "riesgo"),
    ("Computación Cuántica", "Qiskit", "sdk"),
    ("Computación Cuántica", "Quantum Machine Learning", "intersección"),
]

# =========================================================
# Filtros derivados
# =========================================================
all_kinds = sorted({attrs["kind"] for attrs in nodes.values()})
all_domains = sorted({attrs["domain"] for attrs in nodes.values()})

default_focus_from_query = st.query_params.get("focus", "Todo")
if isinstance(default_focus_from_query, list):
    default_focus_from_query = default_focus_from_query[0]

focus_options = ["Todo"] + sorted(nodes.keys())
if default_focus_from_query not in focus_options:
    default_focus_from_query = "Todo"

focus_node = st.sidebar.selectbox(
    "Mostrar submapa de:",
    focus_options,
    index=focus_options.index(default_focus_from_query)
)

selected_kinds = st.sidebar.multiselect(
    "Tipos a mostrar",
    all_kinds,
    default=all_kinds
)

selected_domains = st.sidebar.multiselect(
    "Dominios a mostrar",
    all_domains,
    default=all_domains
)

# =========================================================
# Helpers
# =========================================================
def safe_color(domain: str) -> str:
    return DOMAIN_COLORS.get(domain, DOMAIN_COLORS["General"])


def build_tooltip(node_name: str, attrs: dict) -> str:
    kind = attrs.get("kind", "concepto")
    domain = attrs.get("domain", "General")

    html = f"""
    <div style="font-size:14px; line-height:1.45;">
        <b>{node_name}</b><br>
        <b>Tipo:</b> {kind}<br>
        <b>Dominio:</b> {domain}<br>
        <b>Año:</b> {attrs.get("year", "N/A")}<br><br>
        {attrs.get("title", "")}
    """

    if attrs.get("examples"):
        html += "<br><br><b>Ejemplos de uso:</b><br>" + "".join(
            f"• {x}<br>" for x in attrs["examples"]
        )

    if attrs.get("tools"):
        html += "<br><br><b>Herramientas relacionadas:</b><br>" + ", ".join(attrs["tools"])

    if attrs.get("python_libraries"):
        html += "<br><br><b>Librerías Python:</b><br>" + ", ".join(attrs["python_libraries"])

    if attrs.get("functions"):
        html += "<br><br><b>Funciones clave:</b><br>" + ", ".join(attrs["functions"])

    if attrs.get("tags"):
        html += "<br><br><b>Tags:</b><br>" + ", ".join(attrs["tags"])

    if attrs.get("url"):
        html += f"<br><br><b>Recurso:</b> <a href='{attrs['url']}' target='_blank'>{attrs['url']}</a>"

    if attrs.get("github"):
        html += f"<br><br><b>Git:</b> <a href='{attrs['github']}' target='_blank'>{attrs['github']}</a>"

    html += "</div>"
    return html


def add_function_nodes(base_nodes: dict, base_edges: list, max_functions: int = 5):
    new_nodes = dict(base_nodes)
    new_edges = list(base_edges)

    for lib_name, attrs in list(base_nodes.items()):
        if attrs.get("kind") == "libreria" and attrs.get("functions"):
            for fn in attrs["functions"][:max_functions]:
                fn_node_name = f"{lib_name}.{fn}"
                if fn_node_name not in new_nodes:
                    new_nodes[fn_node_name] = {
                        "kind": "funcion",
                        "domain": attrs.get("domain", "Python"),
                        "size": 10,
                        "year": attrs.get("year", ""),
                        "title": f"Función o componente clave de {lib_name}: {fn}",
                        "examples": [f"Uso de {fn} en {lib_name}"],
                        "url": attrs.get("url", ""),
                    }
                    new_edges.append((lib_name, fn_node_name, "función"))
    return new_nodes, new_edges


def build_graph(graph_nodes: dict, graph_edges: list) -> nx.Graph:
    G = nx.Graph()

    for node_name, attrs in graph_nodes.items():
        style = KIND_STYLES.get(attrs.get("kind", "concepto"), KIND_STYLES["concepto"])
        label = node_name
        if show_year_in_label and attrs.get("year"):
            label = f"{node_name}\\n({attrs['year']})"

        size = max(8, attrs.get("size", 14) + style["size_boost"])

        G.add_node(
            node_name,
            label=label,
            kind=attrs.get("kind", "concepto"),
            domain=attrs.get("domain", "General"),
            color=safe_color(attrs.get("domain", "General")),
            size=size,
            shape=style["shape"],
            title=build_tooltip(node_name, attrs),
            url=attrs.get("url", ""),
            year=attrs.get("year", ""),
            raw_title=attrs.get("title", ""),
        )

    for edge in graph_edges:
        source, target, relation = edge
        if source in G.nodes and target in G.nodes:
            G.add_edge(source, target, label=relation, title=relation)

    return G


def get_subgraph_nodes(graph: nx.Graph, start_node: str, max_depth: int = 1):
    if start_node not in graph:
        return set()

    visited = {start_node}
    queue = deque([(start_node, 0)])

    while queue:
        current, depth_now = queue.popleft()
        if depth_now >= max_depth:
            continue
        for neigh in graph.neighbors(current):
            if neigh not in visited:
                visited.add(neigh)
                queue.append((neigh, depth_now + 1))

    return visited


def filter_graph(G: nx.Graph, focus: str, kinds: list, domains: list, depth_value: int) -> nx.Graph:
    if focus != "Todo" and focus in G.nodes:
        visible = get_subgraph_nodes(G, focus, max_depth=depth_value)
    else:
        visible = set(G.nodes())

    visible = {
        n for n in visible
        if G.nodes[n].get("kind") in kinds and G.nodes[n].get("domain") in domains
    }

    return G.subgraph(visible).copy()


def create_timeline_df(graph_nodes: dict) -> pd.DataFrame:
    rows = []
    for name, attrs in graph_nodes.items():
        if attrs.get("year"):
            rows.append({
                "Concepto": name,
                "Año": attrs.get("year"),
                "Tipo": attrs.get("kind", "concepto"),
                "Dominio": attrs.get("domain", "General"),
                "Descripción": attrs.get("title", "")
            })
    df = pd.DataFrame(rows)
    if not df.empty and sort_by_epoch:
        df = df.sort_values(by=["Año", "Dominio", "Concepto"]).reset_index(drop=True)
    return df


def inject_click_behavior(html_path: str):
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    custom_js = """
<script type="text/javascript">
(function() {
    function updateFocusParam(nodeId) {
        try {
            const url = new URL(window.parent.location.href);
            url.searchParams.set("focus", nodeId);
            window.parent.location.href = url.toString();
        } catch (e) {
            console.log("No se pudo actualizar focus:", e);
        }
    }

    function openNodeUrl(nodeId) {
        try {
            const node = nodes.get(nodeId);
            if (node && node.url) {
                window.open(node.url, "_blank");
            }
        } catch (e) {
            console.log("No se pudo abrir URL:", e);
        }
    }

    network.on("click", function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            updateFocusParam(nodeId);
        }
    });

    network.on("doubleClick", function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            openNodeUrl(nodeId);
        }
    });
})();
</script>
</body>
"""

    html = html.replace("</body>", custom_js)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)


def render_graph(G: nx.Graph):
    net = Network(height="760px", width="100%", bgcolor="#111111", font_color="white", notebook=False)
    net.from_nx(G)

    if tipo_mapa == "Jerárquico LR":
        net.set_options(f"""
        var options = {{
          "layout": {{
            "hierarchical": {{
              "enabled": true,
              "direction": "LR",
              "sortMethod": "directed"
            }}
          }},
          "physics": {{
            "enabled": {str(physics_enabled).lower()},
            "hierarchicalRepulsion": {{
              "nodeDistance": {node_distance}
            }},
            "solver": "hierarchicalRepulsion"
          }},
          "edges": {{
            "smooth": true,
            "color": {{"inherit": true}}
          }}
        }}
        """)
    elif tipo_mapa == "Jerárquico UD":
        net.set_options(f"""
        var options = {{
          "layout": {{
            "hierarchical": {{
              "enabled": true,
              "direction": "UD",
              "sortMethod": "directed"
            }}
          }},
          "physics": {{
            "enabled": {str(physics_enabled).lower()},
            "hierarchicalRepulsion": {{
              "nodeDistance": {node_distance}
            }},
            "solver": "hierarchicalRepulsion"
          }},
          "edges": {{
            "smooth": true,
            "color": {{"inherit": true}}
          }}
        }}
        """)
    else:
        net.set_options(f"""
        var options = {{
          "physics": {{
            "enabled": {str(physics_enabled).lower()},
            "barnesHut": {{
              "gravitationalConstant": -2500,
              "centralGravity": {central_gravity},
              "springLength": {spring_length},
              "springConstant": 0.04,
              "damping": 0.09
            }},
            "solver": "barnesHut"
          }},
          "nodes": {{
            "borderWidth": 2,
            "shadow": true
          }},
          "edges": {{
            "smooth": true,
            "color": {{"inherit": true}}
          }},
          "interaction": {{
            "hover": true,
            "navigationButtons": true,
            "keyboard": true
          }}
        }}
        """)

    if not show_edges:
        for edge in net.edges:
            edge["hidden"] = True

    tmp_dir = tempfile.mkdtemp()
    html_path = os.path.join(tmp_dir, "mental_map.html")
    net.save_graph(html_path)
    inject_click_behavior(html_path)

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    components.html(html_content, height=780, scrolling=True)


# =========================================================
# Expandir funciones Python opcionalmente
# =========================================================
graph_nodes = dict(nodes)
graph_edges = list(edges)

if show_python_functions:
    graph_nodes, graph_edges = add_function_nodes(
        graph_nodes,
        graph_edges,
        max_functions=max_function_nodes_per_lib
    )

# =========================================================
# Construcción y filtros del grafo
# =========================================================
G_full = build_graph(graph_nodes, graph_edges)
G_filtered = filter_graph(G_full, focus_node, selected_kinds, selected_domains, depth)

# =========================================================
# Layout principal
# =========================================================
left_col, right_col = st.columns([3.4, 1.2], gap="large")

with left_col:
    st.subheader("Mapa visual")
    st.caption(
        f"Nodos mostrados: {len(G_filtered.nodes)} | "
        f"Relaciones: {len(G_filtered.edges)} | "
        f"Foco actual: {focus_node}"
    )
    render_graph(G_filtered)

with right_col:
    st.subheader("Exploración rápida")

    st.markdown("**Autores / enlaces**")
    st.markdown(f"- [LinkedIn]({LINKEDIN_URL})")
    st.markdown(f"- [GitHub]({GITHUB_URL})")

    st.markdown("---")
    st.markdown("**Leyenda de tipos**")
    for kind in all_kinds + (["funcion"] if show_python_functions else []):
        if kind in KIND_STYLES:
            st.markdown(f"- **{kind}** → {KIND_STYLES[kind]['shape']}")

    st.markdown("---")
    st.markdown("**Foco actual**")
    if focus_node != "Todo" and focus_node in graph_nodes:
        attrs = graph_nodes[focus_node]
        st.markdown(f"### {focus_node}")
        st.write(attrs.get("title", ""))

        if attrs.get("examples"):
            st.markdown("**Ejemplos de uso**")
            for ex in attrs["examples"]:
                st.write(f"- {ex}")

        if attrs.get("tools"):
            st.markdown("**Herramientas relacionadas**")
            st.write(", ".join(attrs["tools"]))

        if attrs.get("python_libraries"):
            st.markdown("**Librerías Python**")
            st.write(", ".join(attrs["python_libraries"]))

        if attrs.get("functions"):
            st.markdown("**Funciones clave**")
            st.write(", ".join(attrs["functions"]))

        if attrs.get("url"):
            st.markdown(f"[Abrir recurso externo]({attrs['url']})")
    else:
        st.info("Selecciona un nodo con click o usa el filtro lateral para ver su detalle.")

    st.markdown("---")
    st.markdown("**Submapas sugeridos**")
    suggested = [
        "Cloud Computing",
        "Python",
        "Robótica",
        "NLP",
        "Visión Artificial",
        "Machine Learning",
        "Generative AI",
        "Computación Cuántica",
    ]
    for s in suggested:
        st.markdown(f"- `{s}`")

# =========================================================
# Línea de tiempo
# =========================================================
if show_timeline:
    st.markdown("---")
    st.subheader("Línea de tiempo")

    if focus_node != "Todo":
        visible_names = set(G_filtered.nodes)
        timeline_source_nodes = {k: v for k, v in graph_nodes.items() if k in visible_names}
    else:
        timeline_source_nodes = graph_nodes

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
        "Descripción": node_data.get("raw_title", ""),
        "URL": node_data.get("url", ""),
    })

summary_df = pd.DataFrame(summary_rows)
if not summary_df.empty:
    if sort_by_epoch and "Año" in summary_df.columns:
        try:
            summary_df["Año_num"] = pd.to_numeric(summary_df["Año"], errors="coerce")
            summary_df = summary_df.sort_values(
                by=["Año_num", "Dominio", "Nombre"],
                ascending=[True, True, True]
            ).drop(columns=["Año_num"])
        except Exception:
            pass
    st.dataframe(summary_df, use_container_width=True)
else:
    st.warning("No hay nodos para mostrar con la combinación actual de filtros.")