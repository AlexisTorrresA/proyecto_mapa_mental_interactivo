import os
import tempfile

import altair as alt
import networkx as nx
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

st.set_page_config(page_title="Mapa mental IA interactivo", layout="wide")
st.title("Mapa mental interactivo de IA, ML, Cloud, Software y Quantum")
st.write("Pasa el mouse sobre cada nodo para ver una descripción. También puedes abrir un recurso para profundizar.")

# =========================================================
# Links de autor
# =========================================================
LINKEDIN_URL = "https://www.linkedin.com/in/alexis-torres87/"
GITHUB_URL = "https://github.com/AlexisTorrresA"

# =========================================================
# Sidebar
# =========================================================
st.sidebar.header("Configuración del mapa")

tipo_mapa = st.sidebar.selectbox(
    "Tipo de mapa", ["Libre", "Jerárquico LR", "Jerárquico UD"]
)

node_distance = st.sidebar.slider("Distancia entre nodos", 100, 400, 220, 10)
spring_length = st.sidebar.slider("Longitud de resortes", 50, 300, 180, 10)
central_gravity = st.sidebar.slider("Gravedad central", 0.0, 1.0, 0.2, 0.05)
physics_enabled = st.sidebar.checkbox("Activar física", True)
show_edges = st.sidebar.checkbox("Mostrar relaciones", True)

# Nuevas opciones de tiempo
st.sidebar.markdown("---")
st.sidebar.subheader("Vista temporal")
show_year_in_label = st.sidebar.checkbox("Mostrar años en nodos", False)
show_timeline = st.sidebar.checkbox("Mostrar línea de tiempo", True)
sort_by_epoch = st.sidebar.checkbox("Ordenar conceptos por época", True)

# =========================================================
# Definición de nodos
# =========================================================
nodes = {
    # =============================
    # IA general
    # =============================
    "Inteligencia Artificial": {
        "color": "#f4d35e",
        "size": 38,
        "year": 1956,
        "title": "Campo general que busca crear sistemas capaces de realizar tareas que normalmente requieren inteligencia humana.",
    },
    "Machine Learning": {
        "color": "#4ea8de",
        "size": 28,
        "year": 1959,
        "title": "Subárea de la IA donde los modelos aprenden patrones a partir de datos sin programar cada regla manualmente.",
    },
    "Deep Learning": {
        "color": "#ff6b6b",
        "size": 28,
        "year": 2006,
        "title": "Subárea del machine learning basada en redes neuronales profundas para aprender representaciones complejas.",
    },
    "NLP": {
        "color": "#72efdd",
        "size": 24,
        "year": 1950,
        "title": "Procesamiento del lenguaje natural: permite a las máquinas entender, clasificar, generar y analizar texto o voz.",
    },
    "Visión Artificial": {
        "color": "#80ed99",
        "size": 24,
        "year": 1966,
        "title": "Área que permite a las máquinas interpretar imágenes, videos y contenido visual.",
    },
    "MLOps": {
        "color": "#c77dff",
        "size": 24,
        "year": 2015,
        "title": "Conjunto de prácticas para desplegar, monitorear y mantener modelos de ML en producción.",
    },
    "Data Engineering": {
        "color": "#a8dadc",
        "size": 24,
        "year": 2010,
        "title": "Disciplina enfocada en construir pipelines, almacenamiento y procesamiento de datos confiables y escalables.",
    },
    "Responsible AI": {
        "color": "#f28482",
        "size": 24,
        "year": 2016,
        "title": "Enfoque para desarrollar IA ética, explicable, justa, segura y alineada con normativas.",
    },

    # =============================
    # ML clásico
    # =============================
    "Aprendizaje Supervisado": {
        "color": "#4ea8de",
        "size": 18,
        "year": 1950,
        "title": "Entrena modelos usando datos etiquetados para predecir una salida conocida.",
    },
    "Aprendizaje No Supervisado": {
        "color": "#4ea8de",
        "size": 18,
        "year": 1958,
        "title": "Busca patrones, grupos o estructuras ocultas en datos sin etiquetas.",
    },
    "Aprendizaje por Refuerzo": {
        "color": "#4ea8de",
        "size": 18,
        "year": 1989,
        "title": "Un agente aprende a tomar decisiones maximizando recompensas en un entorno.",
    },
    "Regresión Lineal": {
        "color": "#5dade2",
        "size": 14,
        "year": 1805,
        "title": "Algoritmo simple para predecir valores continuos mediante una relación lineal.",
    },
    "Regresión Logística": {
        "color": "#5dade2",
        "size": 14,
        "year": 1958,
        "title": "Modelo clásico para clasificación binaria usando probabilidades.",
    },
    "Árboles de Decisión": {
        "color": "#5dade2",
        "size": 14,
        "year": 1963,
        "title": "Modelo interpretable que divide los datos según reglas jerárquicas.",
    },
    "Random Forest": {
        "color": "#5dade2",
        "size": 14,
        "year": 2001,
        "title": "Conjunto de árboles de decisión que mejora robustez y generalización.",
    },
    "XGBoost": {
        "color": "#5dade2",
        "size": 14,
        "year": 2014,
        "title": "Algoritmo de boosting muy potente para datos tabulares y competiciones.",
    },
    "SVM": {
        "color": "#5dade2",
        "size": 14,
        "year": 1995,
        "title": "Máquinas de soporte vectorial: separan clases maximizando el margen entre ellas.",
    },
    "KNN": {
        "color": "#5dade2",
        "size": 14,
        "year": 1951,
        "title": "Clasifica o predice usando los vecinos más cercanos en el espacio de características.",
    },
    "K-Means": {
        "color": "#5dade2",
        "size": 14,
        "year": 1957,
        "title": "Algoritmo de clustering que agrupa datos según centroides.",
    },
    "DBSCAN": {
        "color": "#5dade2",
        "size": 14,
        "year": 1996,
        "title": "Algoritmo de clustering basado en densidad, útil para detectar ruido y formas arbitrarias.",
    },
    "PCA": {
        "color": "#5dade2",
        "size": 14,
        "year": 1901,
        "title": "Técnica de reducción de dimensionalidad que proyecta los datos en componentes principales.",
    },

    # =============================
    # Deep Learning
    # =============================
    "Redes Neuronales": {
        "color": "#ff6b6b",
        "size": 20,
        "year": 1943,
        "title": "Modelos inspirados en neuronas artificiales, base de gran parte del deep learning.",
    },
    "CNN": {
        "color": "#ff6b6b",
        "size": 14,
        "year": 1998,
        "title": "Redes convolucionales, muy usadas en imágenes y visión artificial.",
    },
    "RNN": {
        "color": "#ff6b6b",
        "size": 14,
        "year": 1986,
        "title": "Redes recurrentes, diseñadas para secuencias temporales o texto.",
    },
    "LSTM": {
        "color": "#ff6b6b",
        "size": 14,
        "year": 1997,
        "title": "Variante de RNN que maneja mejor dependencias largas en secuencias.",
    },
    "Transformers": {
        "color": "#ff6b6b",
        "size": 16,
        "year": 2017,
        "title": "Arquitectura moderna basada en atención, clave en NLP y modelos generativos.",
    },
    "Embeddings": {
        "color": "#ff6b6b",
        "size": 14,
        "year": 2003,
        "title": "Representaciones vectoriales densas de palabras, imágenes u otros objetos.",
    },
    "Fine-tuning": {
        "color": "#ff6b6b",
        "size": 14,
        "year": 2018,
        "title": "Ajuste de un modelo preentrenado a una tarea o dominio específico.",
    },

    # =============================
    # NLP / LLMs
    # =============================
    "Tokenización": {
        "color": "#72efdd",
        "size": 14,
        "year": 1950,
        "title": "Proceso de dividir texto en unidades como palabras, subpalabras o tokens.",
    },
    "NER": {
        "color": "#72efdd",
        "size": 14,
        "year": 1995,
        "title": "Reconocimiento de entidades nombradas como personas, lugares, organizaciones o fechas.",
    },
    "Clasificación de Texto": {
        "color": "#72efdd",
        "size": 14,
        "year": 1960,
        "title": "Asignación de categorías o etiquetas a documentos o frases.",
    },
    "Análisis de Sentimiento": {
        "color": "#72efdd",
        "size": 14,
        "year": 2001,
        "title": "Técnica para identificar polaridad u opiniones en texto.",
    },
    "LLMs": {
        "color": "#72efdd",
        "size": 18,
        "year": 2018,
        "title": "Modelos de lenguaje de gran escala entrenados sobre enormes volúmenes de texto.",
    },
    "Prompt Engineering": {
        "color": "#72efdd",
        "size": 14,
        "year": 2022,
        "title": "Diseño de instrucciones efectivas para guiar la salida de modelos generativos.",
    },
    "RAG": {
        "color": "#72efdd",
        "size": 14,
        "year": 2020,
        "title": "Retrieval-Augmented Generation: combina recuperación de información con generación de texto.",
    },
    "Vector DB": {
        "color": "#72efdd",
        "size": 14,
        "year": 2019,
        "title": "Base de datos especializada en búsqueda semántica sobre embeddings.",
    },
    "Agentes": {
        "color": "#72efdd",
        "size": 14,
        "year": 2023,
        "title": "Sistemas que usan modelos para razonar, planificar y ejecutar acciones con herramientas.",
    },
    "Evaluación LLM": {
        "color": "#72efdd",
        "size": 14,
        "year": 2023,
        "title": "Prácticas para medir calidad, seguridad, factualidad y utilidad de modelos de lenguaje.",
    },

    # =============================
    # Visión Artificial
    # =============================
    "Clasificación de Imágenes": {
        "color": "#80ed99",
        "size": 14,
        "year": 1990,
        "title": "Predice la categoría principal de una imagen.",
    },
    "Detección de Objetos": {
        "color": "#80ed99",
        "size": 14,
        "year": 2001,
        "title": "Detecta y localiza objetos dentro de una imagen usando cajas delimitadoras.",
    },
    "Segmentación": {
        "color": "#80ed99",
        "size": 14,
        "year": 1979,
        "title": "Divide una imagen en regiones o píxeles con significado específico.",
    },
    "YOLO": {
        "color": "#80ed99",
        "size": 14,
        "year": 2016,
        "title": "Familia de modelos rápidos para detección de objetos en tiempo real.",
    },
    "OpenCV": {
        "color": "#80ed99",
        "size": 14,
        "year": 2000,
        "title": "Librería muy usada para procesamiento de imágenes y visión por computador.",
    },

    # =============================
    # MLOps / despliegue
    # =============================
    "CI/CD": {
        "color": "#c77dff",
        "size": 14,
        "year": 2000,
        "title": "Integración y despliegue continuo para automatizar pruebas y entregas.",
    },
    "Docker": {
        "color": "#c77dff",
        "size": 14,
        "year": 2013,
        "title": "Tecnología para empaquetar aplicaciones y modelos en contenedores reproducibles.",
    },
    "Kubernetes": {
        "color": "#c77dff",
        "size": 14,
        "year": 2014,
        "title": "Orquestador de contenedores para despliegue, escalado y operación de servicios.",
    },
    "MLflow": {
        "color": "#c77dff",
        "size": 14,
        "year": 2018,
        "title": "Herramienta para seguimiento de experimentos, modelos y ciclos de vida de ML.",
    },
    "Serving": {
        "color": "#c77dff",
        "size": 14,
        "year": 2015,
        "title": "Publicación de modelos para inferencia en tiempo real o batch.",
    },
    "Monitoreo de Modelos": {
        "color": "#c77dff",
        "size": 14,
        "year": 2019,
        "title": "Seguimiento del desempeño, deriva y salud de modelos en producción.",
    },
    "Drift": {
        "color": "#c77dff",
        "size": 14,
        "year": 2010,
        "title": "Cambio en datos o comportamiento del entorno que afecta la calidad del modelo.",
    },

    # =============================
    # Data Engineering
    # =============================
    "ETL": {
        "color": "#a8dadc",
        "size": 14,
        "year": 1970,
        "title": "Proceso de extracción, transformación y carga de datos.",
    },
    "Pipelines": {
        "color": "#a8dadc",
        "size": 14,
        "year": 2010,
        "title": "Flujos automatizados para mover, transformar y procesar datos.",
    },
    "Data Lake": {
        "color": "#a8dadc",
        "size": 14,
        "year": 2011,
        "title": "Repositorio escalable para almacenar datos estructurados y no estructurados.",
    },
    "Data Warehouse": {
        "color": "#a8dadc",
        "size": 14,
        "year": 1988,
        "title": "Base orientada a analítica y consultas estructuradas para BI.",
    },
    "Streaming": {
        "color": "#a8dadc",
        "size": 14,
        "year": 1992,
        "title": "Procesamiento continuo de eventos o datos en tiempo real.",
    },
    "Airflow": {
        "color": "#a8dadc",
        "size": 14,
        "year": 2015,
        "title": "Plataforma popular para orquestación de workflows y pipelines.",
    },
    "Kafka": {
        "color": "#a8dadc",
        "size": 14,
        "year": 2011,
        "title": "Sistema distribuido para mensajería y streaming de eventos.",
    },
    "Calidad de Datos": {
        "color": "#a8dadc",
        "size": 14,
        "year": 2000,
        "title": "Prácticas para asegurar consistencia, completitud, precisión y confiabilidad de datos.",
    },

    # =============================
    # Cloud
    # =============================
    "Cloud Computing": {
        "color": "#ffd166",
        "size": 24,
        "year": 2006,
        "title": "Uso de infraestructura, plataformas y servicios remotos para desarrollar y operar sistemas.",
    },
    "AWS": {
        "color": "#ffd166",
        "size": 14,
        "year": 2006,
        "title": "Proveedor líder de servicios cloud.",
    },
    "Azure": {
        "color": "#ffd166",
        "size": 14,
        "year": 2010,
        "title": "Plataforma cloud de Microsoft.",
    },
    "GCP": {
        "color": "#ffd166",
        "size": 14,
        "year": 2008,
        "title": "Google Cloud Platform, enfocada en datos, ML y servicios escalables.",
    },
    "Huawei Cloud": {
        "color": "#ffd166",
        "size": 14,
        "year": 2017,
        "title": "Plataforma cloud de Huawei con servicios de infraestructura, datos y ML.",
    },
    "IaaS": {
        "color": "#ffd166",
        "size": 14,
        "year": 2006,
        "title": "Infraestructura como servicio.",
    },
    "PaaS": {
        "color": "#ffd166",
        "size": 14,
        "year": 2007,
        "title": "Plataforma como servicio.",
    },
    "SaaS": {
        "color": "#ffd166",
        "size": 14,
        "year": 1999,
        "title": "Software como servicio.",
    },
    "Serverless": {
        "color": "#ffd166",
        "size": 14,
        "year": 2014,
        "title": "Modelo donde el proveedor administra la infraestructura y se ejecuta bajo demanda.",
    },
    "Terraform": {
        "color": "#ffd166",
        "size": 14,
        "year": 2014,
        "title": "Infraestructura como código para aprovisionar recursos cloud.",
    },
    "IAM": {
        "color": "#ffd166",
        "size": 14,
        "year": 1999,
        "title": "Gestión de identidades y accesos.",
    },
    "Object Storage": {
        "color": "#ffd166",
        "size": 14,
        "year": 2006,
        "title": "Servicio de almacenamiento escalable basado en objetos.",
    },
    "Cloud Security": {
        "color": "#ffd166",
        "size": 14,
        "year": 2010,
        "title": "Prácticas y controles para proteger sistemas y datos en la nube.",
    },

    # =============================
    # Desarrollo de software
    # =============================
    "Desarrollo de Software": {
        "color": "#06d6a0",
        "size": 24,
        "year": 1968,
        "title": "Disciplina para diseñar, construir, probar y mantener aplicaciones.",
    },
    "Backend": {
        "color": "#06d6a0",
        "size": 14,
        "year": 1990,
        "title": "Lógica de servidor, APIs, bases de datos y reglas de negocio.",
    },
    "Frontend": {
        "color": "#06d6a0",
        "size": 14,
        "year": 1990,
        "title": "Interfaz de usuario y experiencia visual de la aplicación.",
    },
    "APIs": {
        "color": "#06d6a0",
        "size": 14,
        "year": 2000,
        "title": "Interfaces que permiten la comunicación entre sistemas.",
    },
    "Microservicios": {
        "color": "#06d6a0",
        "size": 14,
        "year": 2011,
        "title": "Arquitectura de servicios pequeños, independientes y desplegables por separado.",
    },
    "Testing": {
        "color": "#06d6a0",
        "size": 14,
        "year": 1979,
        "title": "Pruebas para validar el comportamiento y calidad del software.",
    },
    "Git": {
        "color": "#06d6a0",
        "size": 14,
        "year": 2005,
        "title": "Sistema de control de versiones para colaboración y trazabilidad del código.",
    },
    "Arquitectura de Software": {
        "color": "#06d6a0",
        "size": 14,
        "year": 1969,
        "title": "Diseño de componentes, integraciones, escalabilidad y mantenibilidad del sistema.",
    },
    "FastAPI": {
        "color": "#06d6a0",
        "size": 14,
        "year": 2018,
        "title": "Framework moderno de Python para construir APIs rápidas.",
    },

    # =============================
    # Responsible AI / seguridad
    # =============================
    "Robustez": {
        "color": "#f28482",
        "size": 14,
        "year": 1990,
        "title": "Capacidad del sistema para resistir ruido, ataques o cambios inesperados.",
    },
    "Seguridad IA": {
        "color": "#f28482",
        "size": 14,
        "year": 2023,
        "title": "Protección contra ataques, fugas, abuso y comportamientos inseguros en sistemas de IA.",
    },
    "Gobernanza de IA": {
        "color": "#f28482",
        "size": 14,
        "year": 2018,
        "title": "Políticas, controles y trazabilidad para operar IA de manera responsable.",
    },
    "Guardrails": {
        "color": "#f28482",
        "size": 14,
        "year": 2023,
        "title": "Restricciones y mecanismos de control para reducir respuestas dañinas o fuera de política.",
    },

    # =============================
    # Quantum Computing
    # =============================
    "Computación Cuántica": {
        "color": "#9b5de5",
        "size": 24,
        "year": 1980,
        "title": "Paradigma de cómputo basado en qubits, superposición y entrelazamiento.",
    },
    "Qubits": {
        "color": "#9b5de5",
        "size": 16,
        "year": 1995,
        "title": "Unidad básica de información cuántica.",
    },
    "Superposición": {
        "color": "#9b5de5",
        "size": 14,
        "year": 1926,
        "title": "Propiedad que permite a un estado cuántico combinar múltiples posibilidades.",
    },
    "Entrelazamiento": {
        "color": "#9b5de5",
        "size": 14,
        "year": 1935,
        "title": "Correlación cuántica fuerte entre qubits.",
    },
    "Puertas Cuánticas": {
        "color": "#9b5de5",
        "size": 14,
        "year": 1995,
        "title": "Operaciones que transforman estados cuánticos en un circuito.",
    },
    "Circuitos Cuánticos": {
        "color": "#9b5de5",
        "size": 14,
        "year": 1989,
        "title": "Secuencia de puertas cuánticas aplicada a qubits.",
    },
    "Medición Cuántica": {
        "color": "#9b5de5",
        "size": 14,
        "year": 1926,
        "title": "Proceso de observación que colapsa el estado cuántico a un resultado clásico.",
    },
    "Algoritmo de Grover": {
        "color": "#9b5de5",
        "size": 14,
        "year": 1996,
        "title": "Algoritmo cuántico para búsqueda con aceleración cuadrática idealizada.",
    },
    "Algoritmo de Shor": {
        "color": "#9b5de5",
        "size": 14,
        "year": 1994,
        "title": "Algoritmo cuántico conocido por factorizar enteros en ciertos contextos.",
    },
    "QAOA": {
        "color": "#9b5de5",
        "size": 14,
        "year": 2014,
        "title": "Quantum Approximate Optimization Algorithm, método híbrido para optimización.",
    },
    "VQE": {
        "color": "#9b5de5",
        "size": 14,
        "year": 2014,
        "title": "Variational Quantum Eigensolver, algoritmo híbrido usado en simulación cuántica.",
    },
    "Qiskit": {
        "color": "#9b5de5",
        "size": 14,
        "year": 2017,
        "title": "SDK popular para programación y experimentación en computación cuántica.",
    },
    "Quantum Machine Learning": {
        "color": "#9b5de5",
        "size": 16,
        "year": 2017,
        "title": "Intersección entre computación cuántica y aprendizaje automático.",
    },
}

# =========================================================
# Recursos / links por concepto
# =========================================================
resources = {
    "Inteligencia Artificial": "https://es.wikipedia.org/wiki/Inteligencia_artificial",
    "Machine Learning": "https://es.wikipedia.org/wiki/Aprendizaje_autom%C3%A1tico",
    "Deep Learning": "https://es.wikipedia.org/wiki/Aprendizaje_profundo",
    "NLP": "https://es.wikipedia.org/wiki/Procesamiento_del_lenguaje_natural",
    "Visión Artificial": "https://es.wikipedia.org/wiki/Visi%C3%B3n_artificial",
    "MLOps": "https://en.wikipedia.org/wiki/MLOps",
    "Data Engineering": "https://en.wikipedia.org/wiki/Data_engineering",
    "Responsible AI": "https://www.ibm.com/think/topics/responsible-ai",

    "Aprendizaje Supervisado": "https://developers.google.com/machine-learning/glossary#supervised-learning",
    "Aprendizaje No Supervisado": "https://developers.google.com/machine-learning/glossary#unsupervised-learning",
    "Aprendizaje por Refuerzo": "https://en.wikipedia.org/wiki/Reinforcement_learning",
    "Regresión Lineal": "https://es.wikipedia.org/wiki/Regresi%C3%B3n_lineal",
    "Regresión Logística": "https://es.wikipedia.org/wiki/Regresi%C3%B3n_log%C3%ADstica",
    "Árboles de Decisión": "https://es.wikipedia.org/wiki/%C3%81rbol_de_decisi%C3%B3n",
    "Random Forest": "https://en.wikipedia.org/wiki/Random_forest",
    "XGBoost": "https://xgboost.readthedocs.io/",
    "SVM": "https://es.wikipedia.org/wiki/M%C3%A1quinas_de_vectores_de_soporte",
    "KNN": "https://es.wikipedia.org/wiki/K_vecinos_m%C3%A1s_pr%C3%B3ximos",
    "K-Means": "https://es.wikipedia.org/wiki/K-means",
    "DBSCAN": "https://en.wikipedia.org/wiki/DBSCAN",
    "PCA": "https://es.wikipedia.org/wiki/An%C3%A1lisis_de_componentes_principales",

    "Redes Neuronales": "https://es.wikipedia.org/wiki/Red_neuronal_artificial",
    "CNN": "https://en.wikipedia.org/wiki/Convolutional_neural_network",
    "RNN": "https://en.wikipedia.org/wiki/Recurrent_neural_network",
    "LSTM": "https://en.wikipedia.org/wiki/Long_short-term_memory",
    "Transformers": "https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)",
    "Embeddings": "https://developers.google.com/machine-learning/crash-course/embeddings/video-lecture",
    "Fine-tuning": "https://platform.openai.com/docs/guides/fine-tuning",

    "Tokenización": "https://es.wikipedia.org/wiki/Tokenizaci%C3%B3n",
    "NER": "https://en.wikipedia.org/wiki/Named-entity_recognition",
    "Clasificación de Texto": "https://developers.google.com/machine-learning/guides/text-classification",
    "Análisis de Sentimiento": "https://es.wikipedia.org/wiki/An%C3%A1lisis_de_sentimientos",
    "LLMs": "https://en.wikipedia.org/wiki/Large_language_model",
    "Prompt Engineering": "https://platform.openai.com/docs/guides/prompt-engineering",
    "RAG": "https://www.pinecone.io/learn/retrieval-augmented-generation/",
    "Vector DB": "https://www.pinecone.io/learn/vector-database/",
    "Agentes": "https://platform.openai.com/docs/guides/agents",
    "Evaluación LLM": "https://platform.openai.com/docs/guides/evals",

    "Clasificación de Imágenes": "https://developers.google.com/machine-learning/practica/image-classification",
    "Detección de Objetos": "https://en.wikipedia.org/wiki/Object_detection",
    "Segmentación": "https://en.wikipedia.org/wiki/Image_segmentation",
    "YOLO": "https://docs.ultralytics.com/",
    "OpenCV": "https://opencv.org/",

    "CI/CD": "https://es.wikipedia.org/wiki/CI/CD",
    "Docker": "https://www.docker.com/",
    "Kubernetes": "https://kubernetes.io/",
    "MLflow": "https://mlflow.org/",
    "Serving": "https://en.wikipedia.org/wiki/Model_serving",
    "Monitoreo de Modelos": "https://evidentlyai.com/ml-observability",
    "Drift": "https://evidentlyai.com/ml-in-production/data-drift",

    "ETL": "https://es.wikipedia.org/wiki/Extract,_transform,_load",
    "Pipelines": "https://en.wikipedia.org/wiki/Data_pipeline",
    "Data Lake": "https://es.wikipedia.org/wiki/Data_lake",
    "Data Warehouse": "https://es.wikipedia.org/wiki/Data_warehouse",
    "Streaming": "https://en.wikipedia.org/wiki/Stream_processing",
    "Airflow": "https://airflow.apache.org/",
    "Kafka": "https://kafka.apache.org/",
    "Calidad de Datos": "https://en.wikipedia.org/wiki/Data_quality",

    "Cloud Computing": "https://es.wikipedia.org/wiki/Computaci%C3%B3n_en_la_nube",
    "AWS": "https://aws.amazon.com/",
    "Azure": "https://azure.microsoft.com/",
    "GCP": "https://cloud.google.com/",
    "Huawei Cloud": "https://www.huaweicloud.com/intl/en-us/",
    "IaaS": "https://en.wikipedia.org/wiki/Infrastructure_as_a_service",
    "PaaS": "https://en.wikipedia.org/wiki/Platform_as_a_service",
    "SaaS": "https://en.wikipedia.org/wiki/Software_as_a_service",
    "Serverless": "https://en.wikipedia.org/wiki/Serverless_computing",
    "Terraform": "https://developer.hashicorp.com/terraform/docs",
    "IAM": "https://en.wikipedia.org/wiki/Identity_and_access_management",
    "Object Storage": "https://en.wikipedia.org/wiki/Object_storage",
    "Cloud Security": "https://en.wikipedia.org/wiki/Cloud_computing_security",

    "Desarrollo de Software": "https://es.wikipedia.org/wiki/Desarrollo_de_software",
    "Backend": "https://es.wikipedia.org/wiki/Back-end",
    "Frontend": "https://es.wikipedia.org/wiki/Front-end_y_back-end",
    "APIs": "https://es.wikipedia.org/wiki/Interfaz_de_programaci%C3%B3n_de_aplicaciones",
    "Microservicios": "https://es.wikipedia.org/wiki/Microservicios",
    "Testing": "https://es.wikipedia.org/wiki/Pruebas_de_software",
    "Git": "https://git-scm.com/",
    "Arquitectura de Software": "https://es.wikipedia.org/wiki/Arquitectura_de_software",
    "FastAPI": "https://fastapi.tiangolo.com/",

    "Robustez": "https://en.wikipedia.org/wiki/Robustness_(computer_science)",
    "Seguridad IA": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
    "Gobernanza de IA": "https://www.oecd.org/en/topics/ai-governance.html",
    "Guardrails": "https://www.guardrailsai.com/",

    "Computación Cuántica": "https://es.wikipedia.org/wiki/Computaci%C3%B3n_cu%C3%A1ntica",
    "Qubits": "https://es.wikipedia.org/wiki/Qubit",
    "Superposición": "https://es.wikipedia.org/wiki/Superposici%C3%B3n_cu%C3%A1ntica",
    "Entrelazamiento": "https://es.wikipedia.org/wiki/Entrelazamiento_cu%C3%A1ntico",
    "Puertas Cuánticas": "https://es.wikipedia.org/wiki/Puerta_cu%C3%A1ntica",
    "Circuitos Cuánticos": "https://en.wikipedia.org/wiki/Quantum_circuit",
    "Medición Cuántica": "https://en.wikipedia.org/wiki/Measurement_in_quantum_mechanics",
    "Algoritmo de Grover": "https://es.wikipedia.org/wiki/Algoritmo_de_Grover",
    "Algoritmo de Shor": "https://es.wikipedia.org/wiki/Algoritmo_de_Shor",
    "QAOA": "https://en.wikipedia.org/wiki/Quantum_optimization_algorithms#QAOA",
    "VQE": "https://en.wikipedia.org/wiki/Variational_quantum_eigensolver",
    "Qiskit": "https://qiskit.org/",
    "Quantum Machine Learning": "https://en.wikipedia.org/wiki/Quantum_machine_learning",
}

# Añadir links a los nodos
for node_name in nodes:
    nodes[node_name]["url"] = resources.get(node_name, "")

# =========================================================
# Relaciones
# =========================================================
edges = [
    ("Inteligencia Artificial", "Machine Learning"),
    ("Inteligencia Artificial", "Deep Learning"),
    ("Inteligencia Artificial", "NLP"),
    ("Inteligencia Artificial", "Visión Artificial"),
    ("Inteligencia Artificial", "MLOps"),
    ("Inteligencia Artificial", "Data Engineering"),
    ("Inteligencia Artificial", "Responsible AI"),

    ("Machine Learning", "Aprendizaje Supervisado"),
    ("Machine Learning", "Aprendizaje No Supervisado"),
    ("Machine Learning", "Aprendizaje por Refuerzo"),
    ("Aprendizaje Supervisado", "Regresión Lineal"),
    ("Aprendizaje Supervisado", "Regresión Logística"),
    ("Aprendizaje Supervisado", "Árboles de Decisión"),
    ("Aprendizaje Supervisado", "Random Forest"),
    ("Aprendizaje Supervisado", "XGBoost"),
    ("Aprendizaje Supervisado", "SVM"),
    ("Aprendizaje Supervisado", "KNN"),
    ("Aprendizaje No Supervisado", "K-Means"),
    ("Aprendizaje No Supervisado", "DBSCAN"),
    ("Aprendizaje No Supervisado", "PCA"),

    ("Deep Learning", "Redes Neuronales"),
    ("Redes Neuronales", "CNN"),
    ("Redes Neuronales", "RNN"),
    ("RNN", "LSTM"),
    ("Deep Learning", "Transformers"),
    ("Deep Learning", "Embeddings"),
    ("Deep Learning", "Fine-tuning"),
    ("Transformers", "LLMs"),

    ("NLP", "Tokenización"),
    ("NLP", "NER"),
    ("NLP", "Clasificación de Texto"),
    ("NLP", "Análisis de Sentimiento"),
    ("NLP", "LLMs"),
    ("LLMs", "Prompt Engineering"),
    ("LLMs", "RAG"),
    ("LLMs", "Agentes"),
    ("RAG", "Vector DB"),
    ("LLMs", "Evaluación LLM"),

    ("Visión Artificial", "Clasificación de Imágenes"),
    ("Visión Artificial", "Detección de Objetos"),
    ("Visión Artificial", "Segmentación"),
    ("Detección de Objetos", "YOLO"),
    ("Visión Artificial", "OpenCV"),

    ("MLOps", "CI/CD"),
    ("MLOps", "Docker"),
    ("MLOps", "Kubernetes"),
    ("MLOps", "MLflow"),
    ("MLOps", "Serving"),
    ("MLOps", "Monitoreo de Modelos"),
    ("Monitoreo de Modelos", "Drift"),

    ("Data Engineering", "ETL"),
    ("Data Engineering", "Pipelines"),
    ("Data Engineering", "Data Lake"),
    ("Data Engineering", "Data Warehouse"),
    ("Data Engineering", "Streaming"),
    ("Data Engineering", "Calidad de Datos"),
    ("Pipelines", "Airflow"),
    ("Streaming", "Kafka"),
    ("Data Lake", "Data Warehouse"),

    ("Inteligencia Artificial", "Cloud Computing"),
    ("Cloud Computing", "AWS"),
    ("Cloud Computing", "Azure"),
    ("Cloud Computing", "GCP"),
    ("Cloud Computing", "Huawei Cloud"),
    ("Cloud Computing", "IaaS"),
    ("Cloud Computing", "PaaS"),
    ("Cloud Computing", "SaaS"),
    ("Cloud Computing", "Serverless"),
    ("Cloud Computing", "Kubernetes"),
    ("Cloud Computing", "Terraform"),
    ("Cloud Computing", "IAM"),
    ("Cloud Computing", "Object Storage"),
    ("Cloud Computing", "Cloud Security"),
    ("MLOps", "Cloud Computing"),
    ("Data Engineering", "Cloud Computing"),

    ("Inteligencia Artificial", "Desarrollo de Software"),
    ("Desarrollo de Software", "Backend"),
    ("Desarrollo de Software", "Frontend"),
    ("Desarrollo de Software", "APIs"),
    ("Desarrollo de Software", "Microservicios"),
    ("Desarrollo de Software", "Testing"),
    ("Desarrollo de Software", "Git"),
    ("Desarrollo de Software", "Arquitectura de Software"),
    ("Backend", "FastAPI"),
    ("APIs", "FastAPI"),
    ("Microservicios", "Docker"),
    ("Microservicios", "Kubernetes"),
    ("Testing", "CI/CD"),

    ("Responsible AI", "Robustez"),
    ("Responsible AI", "Seguridad IA"),
    ("Responsible AI", "Gobernanza de IA"),
    ("Seguridad IA", "Guardrails"),
    ("Gobernanza de IA", "Evaluación LLM"),

    ("Inteligencia Artificial", "Computación Cuántica"),
    ("Computación Cuántica", "Qubits"),
    ("Computación Cuántica", "Superposición"),
    ("Computación Cuántica", "Entrelazamiento"),
    ("Computación Cuántica", "Puertas Cuánticas"),
    ("Computación Cuántica", "Circuitos Cuánticos"),
    ("Computación Cuántica", "Medición Cuántica"),
    ("Computación Cuántica", "Algoritmo de Grover"),
    ("Computación Cuántica", "Algoritmo de Shor"),
    ("Computación Cuántica", "QAOA"),
    ("Computación Cuántica", "VQE"),
    ("Computación Cuántica", "Qiskit"),
    ("Computación Cuántica", "Quantum Machine Learning"),
    ("Qubits", "Superposición"),
    ("Qubits", "Entrelazamiento"),
    ("Puertas Cuánticas", "Circuitos Cuánticos"),
    ("Circuitos Cuánticos", "Medición Cuántica"),
    ("Qiskit", "Algoritmo de Grover"),
    ("Qiskit", "Algoritmo de Shor"),
    ("Qiskit", "QAOA"),
    ("Qiskit", "VQE"),
    ("Quantum Machine Learning", "Machine Learning"),
    ("Quantum Machine Learning", "Computación Cuántica"),
]

# =========================================================
# Sidebar de recursos
# =========================================================
st.sidebar.markdown("---")
st.sidebar.subheader("Recurso por concepto")

selected_topic = st.sidebar.selectbox(
    "Selecciona un concepto",
    sorted(nodes.keys())
)

selected_url = nodes[selected_topic].get("url", "")
selected_desc = nodes[selected_topic].get("title", "")
selected_year = nodes[selected_topic].get("year", "Sin año")

st.sidebar.markdown(f"**Año:** {selected_year}")
st.sidebar.markdown(f"**Descripción:** {selected_desc}")
if selected_url:
    st.sidebar.markdown(f"[Abrir recurso de {selected_topic}]({selected_url})")
else:
    st.sidebar.info("No hay link definido para este concepto.")

# =========================================================
# Construcción del grafo
# =========================================================
G = nx.Graph()

for node_name, attrs in nodes.items():
    descripcion = attrs["title"]
    url = attrs.get("url", "")
    year = attrs.get("year", "")

    if year:
        descripcion = f"<b>Año:</b> {year}<br><br>{descripcion}"

    if url:
        descripcion += f"<br><br><b>Más información:</b><br><a href='{url}' target='_blank'>{url}</a>"

    G.add_node(
        node_name,
        color=attrs["color"],
        size=attrs["size"],
        title=descripcion,
        url=url,
        year=year,
    )

if show_edges:
    for source, target in edges:
        G.add_edge(source, target)

# =========================================================
# Crear red PyVis
# =========================================================
net = Network(
    height="820px",
    width="100%",
    bgcolor="#111111",
    font_color="white",
    notebook=False,
)

net.from_nx(G)

for node in net.nodes:
    base_label = node["id"]
    year = G.nodes[node["id"]].get("year", "")

    if show_year_in_label and year:
        node["label"] = f"{base_label} ({year})"
    else:
        node["label"] = base_label

    node["font"] = {"size": 18, "color": "white"}
    node["title"] = G.nodes[node["id"]].get("title", "")
    node["url"] = G.nodes[node["id"]].get("url", "")
    node["target"] = "_blank"

# =========================================================
# Aplicar tipo de mapa
# =========================================================
if tipo_mapa == "Libre":
    if physics_enabled:
        net.repulsion(
            node_distance=node_distance,
            central_gravity=central_gravity,
            spring_length=spring_length,
            spring_strength=0.05,
            damping=0.09,
        )

    net.set_options(f"""
    var options = {{
      "nodes": {{
        "shape": "dot",
        "scaling": {{
          "min": 10,
          "max": 40
        }},
        "font": {{
          "size": 16,
          "strokeWidth": 0
        }}
      }},
      "edges": {{
        "smooth": {{
          "enabled": true,
          "type": "dynamic"
        }},
        "color": {{
          "color": "#999999",
          "highlight": "#ffffff",
          "hover": "#ffffff"
        }},
        "width": 1.2
      }},
      "physics": {{
        "enabled": {str(physics_enabled).lower()},
        "repulsion": {{
          "nodeDistance": {node_distance},
          "centralGravity": {central_gravity},
          "springLength": {spring_length},
          "springConstant": 0.05,
          "damping": 0.09
        }},
        "solver": "repulsion"
      }},
      "interaction": {{
        "hover": true,
        "tooltipDelay": 150,
        "navigationButtons": true,
        "keyboard": true
      }}
    }}
    """)
else:
    direction = "LR" if tipo_mapa == "Jerárquico LR" else "UD"

    net.set_options(f"""
    var options = {{
      "layout": {{
        "hierarchical": {{
          "enabled": true,
          "direction": "{direction}",
          "sortMethod": "directed",
          "levelSeparation": 180,
          "nodeSpacing": 160,
          "treeSpacing": 220
        }}
      }},
      "physics": {{
        "enabled": false
      }},
      "nodes": {{
        "shape": "dot",
        "scaling": {{
          "min": 10,
          "max": 40
        }},
        "font": {{
          "size": 16,
          "strokeWidth": 0
        }}
      }},
      "edges": {{
        "smooth": {{
          "enabled": true,
          "type": "cubicBezier"
        }},
        "color": {{
          "color": "#999999",
          "highlight": "#ffffff",
          "hover": "#ffffff"
        }},
        "width": 1.2
      }},
      "interaction": {{
        "hover": true,
        "tooltipDelay": 150,
        "navigationButtons": true,
        "keyboard": true
      }}
    }}
    """)

# =========================================================
# Guardar HTML temporal y renderizar
# =========================================================
with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
    net.save_graph(tmp_file.name)
    tmp_file_path = tmp_file.name

with open(tmp_file_path, "r", encoding="utf-8") as f:
    html_content = f.read()

components.html(html_content, height=840, scrolling=True)

try:
    os.unlink(tmp_file_path)
except Exception:
    pass

# =========================================================
# Timeline paralela
# =========================================================
if show_timeline:
    st.markdown("---")
    st.subheader("Evolución histórica de tecnologías")

    timeline_rows = []
    for nombre, attrs in nodes.items():
        year = attrs.get("year", None)
        if year is not None:
            timeline_rows.append({
                "Concepto": nombre,
                "Año": year,
                "Descripción": attrs.get("title", ""),
                "Recurso": attrs.get("url", ""),
            })

    if timeline_rows:
        df_timeline = pd.DataFrame(timeline_rows)

        if sort_by_epoch:
            df_timeline = df_timeline.sort_values(["Año", "Concepto"], ascending=[True, True])
        else:
            df_timeline = df_timeline.sort_values(["Concepto"], ascending=[True])

        st.markdown("### Tabla interactiva")
        st.dataframe(
            df_timeline,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Concepto": st.column_config.TextColumn("Concepto"),
                "Año": st.column_config.NumberColumn("Año", format="%d"),
                "Descripción": st.column_config.TextColumn("Descripción", width="large"),
                "Recurso": st.column_config.LinkColumn("Recurso"),
            }
        )

        st.markdown("### Línea de tiempo visual")
        chart = alt.Chart(df_timeline).mark_circle(size=130).encode(
            x=alt.X("Año:Q", title="Año"),
            y=alt.Y(
                "Concepto:N",
                sort=alt.SortField(field="Año", order="ascending") if sort_by_epoch else None,
                title="Concepto"
            ),
            tooltip=["Concepto", "Año", "Descripción", "Recurso"]
        ).interactive()

        st.altair_chart(chart, use_container_width=True)

# =========================================================
# Resumen
# =========================================================
st.subheader("Resumen de áreas")
st.markdown("""
- **IA**: disciplina general que incluye múltiples técnicas para crear sistemas inteligentes.  
- **Machine Learning**: aprende a partir de datos.  
- **Deep Learning**: usa redes neuronales profundas para tareas complejas.  
- **NLP**: trabaja con texto, lenguaje y modelos de lenguaje.  
- **Visión Artificial**: analiza imágenes y video.  
- **MLOps**: lleva modelos a producción y los mantiene sanos.  
- **Data Engineering**: prepara y mueve los datos que alimentan los modelos.  
- **Responsible AI**: busca una IA más segura, ética y confiable.  
- **Cloud Computing**: permite desplegar y escalar sistemas modernos.  
- **Desarrollo de Software**: da la base arquitectónica y operativa para construir productos reales.  
- **Computación Cuántica**: explora nuevos paradigmas de cómputo y su cruce con ML.
""")

# =========================================================
# Autoría
# =========================================================
st.markdown("---")
st.caption(
    f"Construido por [Alexis Torres]({LINKEDIN_URL}) · [GitHub]({GITHUB_URL})"
)