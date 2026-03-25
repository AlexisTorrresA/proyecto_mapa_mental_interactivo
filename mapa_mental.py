import os
import tempfile

import networkx as nx
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

st.set_page_config(page_title="Mapa mental IA interactivo", layout="wide")
st.title("Mapa mental interactivo de IA, ML y Deep Learning")
st.write("Pasa el mouse sobre cada nodo para ver una descripción breve.")

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("Configuración del mapa")

tipo_mapa = st.sidebar.selectbox(
    "Tipo de mapa", ["Libre", "Jerárquico LR", "Jerárquico UD"]
)

node_distance = st.sidebar.slider("Distancia entre nodos", 100, 400, 220, 10)
spring_length = st.sidebar.slider("Longitud de resortes", 50, 300, 180, 10)
central_gravity = st.sidebar.slider("Gravedad central", 0.0, 1.0, 0.2, 0.05)
physics_enabled = st.sidebar.checkbox("Activar física", True)
show_edges = st.sidebar.checkbox("Mostrar relaciones", True)

# -----------------------------
# Definición de nodos
# -----------------------------
nodes = {
    "Inteligencia Artificial": {
        "color": "#f4d35e",
        "size": 38,
        "title": "Campo general que busca crear sistemas capaces de realizar tareas que normalmente requieren inteligencia humana.",
    },
    "Machine Learning": {
        "color": "#4ea8de",
        "size": 28,
        "title": "Subárea de la IA donde los modelos aprenden patrones a partir de datos sin programar cada regla manualmente.",
    },
    "Deep Learning": {
        "color": "#ff6b6b",
        "size": 28,
        "title": "Subárea del machine learning basada en redes neuronales profundas para aprender representaciones complejas.",
    },
    "NLP": {
        "color": "#72efdd",
        "size": 24,
        "title": "Procesamiento del lenguaje natural: permite a las máquinas entender, clasificar, generar y analizar texto o voz.",
    },
    "Visión Artificial": {
        "color": "#80ed99",
        "size": 24,
        "title": "Área que permite a las máquinas interpretar imágenes, videos y contenido visual.",
    },
    "MLOps": {
        "color": "#c77dff",
        "size": 24,
        "title": "Conjunto de prácticas para desplegar, monitorear y mantener modelos de ML en producción.",
    },
    "Data Engineering": {
        "color": "#a8dadc",
        "size": 24,
        "title": "Disciplina enfocada en construir pipelines, almacenamiento y procesamiento de datos confiables y escalables.",
    },
    "Responsible AI": {
        "color": "#f28482",
        "size": 24,
        "title": "Enfoque para desarrollar IA ética, explicable, justa, segura y alineada con normativas.",
    },
    "Aprendizaje Supervisado": {
        "color": "#4ea8de",
        "size": 18,
        "title": "Entrena modelos usando datos etiquetados para predecir una salida conocida.",
    },
    "Aprendizaje No Supervisado": {
        "color": "#4ea8de",
        "size": 18,
        "title": "Busca patrones, grupos o estructuras ocultas en datos sin etiquetas.",
    },
    "Aprendizaje por Refuerzo": {
        "color": "#4ea8de",
        "size": 18,
        "title": "Un agente aprende a tomar decisiones maximizando recompensas en un entorno.",
    },
    "Regresión Lineal": {
        "color": "#5dade2",
        "size": 14,
        "title": "Algoritmo simple para predecir valores continuos mediante una relación lineal.",
    },
    "Regresión Logística": {
        "color": "#5dade2",
        "size": 14,
        "title": "Modelo clásico para clasificación binaria usando probabilidades.",
    },
    "Árboles de Decisión": {
        "color": "#5dade2",
        "size": 14,
        "title": "Modelo interpretable que divide los datos según reglas jerárquicas.",
    },
    "Random Forest": {
        "color": "#5dade2",
        "size": 14,
        "title": "Conjunto de árboles de decisión que mejora robustez y generalización.",
    },
    "XGBoost": {
        "color": "#5dade2",
        "size": 14,
        "title": "Algoritmo de boosting muy potente para datos tabulares y competiciones.",
    },
    "SVM": {
        "color": "#5dade2",
        "size": 14,
        "title": "Máquinas de soporte vectorial: separan clases maximizando el margen entre ellas.",
    },
    "KNN": {
        "color": "#5dade2",
        "size": 14,
        "title": "Clasifica o predice usando los vecinos más cercanos en el espacio de características.",
    },
    "K-Means": {
        "color": "#5dade2",
        "size": 14,
        "title": "Algoritmo de clustering que agrupa datos en k grupos según cercanía.",
    },
    "DBSCAN": {
        "color": "#5dade2",
        "size": 14,
        "title": "Clustering basado en densidad, útil para detectar grupos irregulares y ruido.",
    },
    "PCA": {
        "color": "#5dade2",
        "size": 14,
        "title": "Técnica de reducción de dimensionalidad que conserva la mayor varianza posible.",
    },
    "Redes Neuronales": {
        "color": "#ff6b6b",
        "size": 18,
        "title": "Modelos inspirados en neuronas biológicas que aprenden transformaciones complejas.",
    },
    "MLP": {
        "color": "#ff8787",
        "size": 14,
        "title": "Perceptrón multicapa: red neuronal densa usada en clasificación y regresión.",
    },
    "CNN": {
        "color": "#ff8787",
        "size": 14,
        "title": "Red neuronal convolucional, ideal para imágenes y patrones espaciales.",
    },
    "RNN": {
        "color": "#ff8787",
        "size": 14,
        "title": "Red recurrente diseñada para secuencias y dependencia temporal.",
    },
    "LSTM": {
        "color": "#ff8787",
        "size": 14,
        "title": "Tipo de RNN que maneja dependencias largas en secuencias.",
    },
    "GRU": {
        "color": "#ff8787",
        "size": 14,
        "title": "Variante eficiente de RNN para modelar secuencias.",
    },
    "Transformers": {
        "color": "#ff8787",
        "size": 16,
        "title": "Arquitectura basada en atención que revolucionó NLP, visión y modelos fundacionales.",
    },
    "Autoencoders": {
        "color": "#ff8787",
        "size": 14,
        "title": "Redes que aprenden representaciones comprimidas de los datos.",
    },
    "GANs": {
        "color": "#ff8787",
        "size": 14,
        "title": "Redes generativas adversarias que crean datos sintéticos realistas.",
    },
    "Diffusion Models": {
        "color": "#ff8787",
        "size": 14,
        "title": "Modelos generativos modernos usados para creación de imágenes y otros contenidos.",
    },
    "Tokenización": {
        "color": "#72efdd",
        "size": 14,
        "title": "Proceso de dividir texto en unidades como palabras, subpalabras o tokens.",
    },
    "Embeddings": {
        "color": "#72efdd",
        "size": 14,
        "title": "Representaciones vectoriales de texto que capturan significado semántico.",
    },
    "Clasificación de Texto": {
        "color": "#72efdd",
        "size": 14,
        "title": "Asignación automática de categorías a documentos o mensajes.",
    },
    "NER": {
        "color": "#72efdd",
        "size": 14,
        "title": "Reconocimiento de entidades nombradas como personas, lugares, fechas y organizaciones.",
    },
    "Análisis de Sentimiento": {
        "color": "#72efdd",
        "size": 14,
        "title": "Detección de opinión, polaridad o emoción en un texto.",
    },
    "LLMs": {
        "color": "#72efdd",
        "size": 16,
        "title": "Modelos de lenguaje de gran escala capaces de generar, resumir, razonar y responder preguntas.",
    },
    "RAG": {
        "color": "#72efdd",
        "size": 14,
        "title": "Retrieval-Augmented Generation: combina búsqueda de información con generación de texto.",
    },
    "Fine-Tuning": {
        "color": "#72efdd",
        "size": 14,
        "title": "Ajuste adicional de un modelo preentrenado para una tarea específica.",
    },
    "Clasificación de Imágenes": {
        "color": "#80ed99",
        "size": 14,
        "title": "Identifica la categoría principal presente en una imagen.",
    },
    "Detección de Objetos": {
        "color": "#80ed99",
        "size": 14,
        "title": "Localiza y clasifica múltiples objetos dentro de una imagen.",
    },
    "Segmentación": {
        "color": "#80ed99",
        "size": 14,
        "title": "Divide la imagen en regiones o píxeles con significado.",
    },
    "YOLO": {
        "color": "#80ed99",
        "size": 14,
        "title": "Familia de modelos rápidos para detección de objetos en tiempo real.",
    },
    "OpenCV": {
        "color": "#80ed99",
        "size": 14,
        "title": "Librería muy usada para visión artificial y procesamiento de imágenes.",
    },
    "Despliegue": {
        "color": "#c77dff",
        "size": 14,
        "title": "Proceso de poner un modelo en producción para que sea consumido por usuarios o sistemas.",
    },
    "Monitoreo": {
        "color": "#c77dff",
        "size": 14,
        "title": "Seguimiento del rendimiento técnico y de negocio del modelo en producción.",
    },
    "Drift": {
        "color": "#c77dff",
        "size": 14,
        "title": "Cambio en la distribución de los datos o del comportamiento del modelo con el tiempo.",
    },
    "MLflow": {
        "color": "#c77dff",
        "size": 14,
        "title": "Herramienta para seguimiento de experimentos, modelos y ciclos de vida en ML.",
    },
    "Docker": {
        "color": "#c77dff",
        "size": 14,
        "title": "Tecnología para empaquetar aplicaciones y modelos en contenedores reproducibles.",
    },
    "FastAPI": {
        "color": "#c77dff",
        "size": 14,
        "title": "Framework moderno de Python para exponer modelos mediante APIs rápidas.",
    },
    "ETL": {
        "color": "#a8dadc",
        "size": 14,
        "title": "Extracción, transformación y carga de datos hacia sistemas de análisis o producción.",
    },
    "Pipelines": {
        "color": "#a8dadc",
        "size": 14,
        "title": "Flujos automatizados para mover, transformar y validar datos.",
    },
    "Data Lake": {
        "color": "#a8dadc",
        "size": 14,
        "title": "Repositorio escalable para almacenar grandes volúmenes de datos en distintos formatos.",
    },
    "Spark": {
        "color": "#a8dadc",
        "size": 14,
        "title": "Framework distribuido para procesamiento masivo de datos.",
    },
    "Bias": {
        "color": "#f28482",
        "size": 14,
        "title": "Sesgos que pueden generar decisiones injustas o discriminatorias en modelos.",
    },
    "Explicabilidad": {
        "color": "#f28482",
        "size": 14,
        "title": "Capacidad de entender por qué un modelo produce cierta predicción.",
    },
    "Privacidad": {
        "color": "#f28482",
        "size": 14,
        "title": "Protección de datos personales y uso responsable de información sensible.",
    },
    "Fairness": {
        "color": "#f28482",
        "size": 14,
        "title": "Búsqueda de resultados equitativos para distintos grupos de usuarios.",
    },

        # =============================
    # IA / ML avanzado
    # =============================
    "Aprendizaje Semi-Supervisado": {
        "color": "#4ea8de",
        "size": 18,
        "title": "Usa una pequeña parte de datos etiquetados junto con muchos datos no etiquetados.",
    },
    "Aprendizaje Auto-Supervisado": {
        "color": "#4ea8de",
        "size": 18,
        "title": "El modelo genera señales de entrenamiento a partir de los propios datos sin etiquetas manuales.",
    },
    "Aprendizaje Online": {
        "color": "#4ea8de",
        "size": 16,
        "title": "Entrenamiento incremental que actualiza el modelo a medida que llegan nuevos datos.",
    },
    "Meta-Learning": {
        "color": "#4ea8de",
        "size": 16,
        "title": "Enfoque donde los modelos aprenden a aprender nuevas tareas más rápido.",
    },
    "Ensemble Learning": {
        "color": "#4ea8de",
        "size": 16,
        "title": "Combina varios modelos para mejorar robustez, estabilidad y precisión.",
    },
    "AdaBoost": {
        "color": "#5dade2",
        "size": 14,
        "title": "Algoritmo de boosting que ajusta el peso de observaciones difíciles en cada iteración.",
    },
    "Gradient Boosting": {
        "color": "#5dade2",
        "size": 14,
        "title": "Construye modelos secuenciales que corrigen errores previos mediante gradientes.",
    },
    "LightGBM": {
        "color": "#5dade2",
        "size": 14,
        "title": "Implementación eficiente de gradient boosting optimizada para rendimiento y escala.",
    },
    "CatBoost": {
        "color": "#5dade2",
        "size": 14,
        "title": "Algoritmo de boosting fuerte en variables categóricas con poco preprocesamiento.",
    },
    "Naive Bayes": {
        "color": "#5dade2",
        "size": 14,
        "title": "Clasificador probabilístico basado en el teorema de Bayes con supuestos de independencia.",
    },
    "LDA": {
        "color": "#5dade2",
        "size": 14,
        "title": "Linear Discriminant Analysis para clasificación y reducción dimensional supervisada.",
    },
    "QDA": {
        "color": "#5dade2",
        "size": 14,
        "title": "Quadratic Discriminant Analysis, variante no lineal basada en distribuciones gaussianas.",
    },
    "Isolation Forest": {
        "color": "#5dade2",
        "size": 14,
        "title": "Método para detección de anomalías aislando observaciones raras.",
    },
    "One-Class SVM": {
        "color": "#5dade2",
        "size": 14,
        "title": "Algoritmo para detección de novedad o anomalías con ejemplos de una sola clase.",
    },
    "t-SNE": {
        "color": "#5dade2",
        "size": 14,
        "title": "Técnica no lineal de reducción de dimensionalidad útil para visualización.",
    },
    "UMAP": {
        "color": "#5dade2",
        "size": 14,
        "title": "Reducción dimensional moderna, rápida y útil para explorar estructuras complejas.",
    },

    # =============================
    # Deep Learning avanzado
    # =============================
    "Transfer Learning": {
        "color": "#ff6b6b",
        "size": 16,
        "title": "Reutiliza modelos preentrenados para acelerar aprendizaje en nuevas tareas.",
    },
    "Attention": {
        "color": "#ff8787",
        "size": 14,
        "title": "Mecanismo que permite al modelo enfocarse en partes relevantes de la entrada.",
    },
    "Self-Attention": {
        "color": "#ff8787",
        "size": 14,
        "title": "Tipo de atención donde una secuencia se relaciona consigo misma.",
    },
    "ResNet": {
        "color": "#ff8787",
        "size": 14,
        "title": "Arquitectura profunda con conexiones residuales que facilita el entrenamiento.",
    },
    "U-Net": {
        "color": "#ff8787",
        "size": 14,
        "title": "Arquitectura muy usada en segmentación semántica de imágenes.",
    },
    "GNN": {
        "color": "#ff8787",
        "size": 14,
        "title": "Graph Neural Networks para aprender sobre nodos, enlaces y estructuras de grafos.",
    },
    "VAE": {
        "color": "#ff8787",
        "size": 14,
        "title": "Variational Autoencoder, modelo generativo probabilístico basado en autoencoders.",
    },
    "LoRA": {
        "color": "#ff8787",
        "size": 14,
        "title": "Técnica eficiente para ajustar modelos grandes modificando pocas matrices.",
    },
    "PEFT": {
        "color": "#ff8787",
        "size": 14,
        "title": "Parameter-Efficient Fine-Tuning: familia de métodos para ajustar LLMs con menor costo.",
    },

    # =============================
    # NLP / LLM / GenAI
    # =============================
    "Prompt Engineering": {
        "color": "#72efdd",
        "size": 14,
        "title": "Diseño estratégico de instrucciones para guiar el comportamiento de modelos generativos.",
    },
    "Zero-Shot": {
        "color": "#72efdd",
        "size": 14,
        "title": "Capacidad de resolver tareas sin ejemplos específicos durante ajuste.",
    },
    "Few-Shot": {
        "color": "#72efdd",
        "size": 14,
        "title": "Uso de pocos ejemplos en el prompt para orientar la respuesta del modelo.",
    },
    "In-Context Learning": {
        "color": "#72efdd",
        "size": 14,
        "title": "Aprendizaje implícito a partir del contexto suministrado en la entrada.",
    },
    "Instruction Tuning": {
        "color": "#72efdd",
        "size": 14,
        "title": "Ajuste de modelos con pares instrucción-respuesta para seguir órdenes mejor.",
    },
    "RLHF": {
        "color": "#72efdd",
        "size": 14,
        "title": "Reinforcement Learning from Human Feedback para alinear salidas de modelos.",
    },
    "Agentes IA": {
        "color": "#72efdd",
        "size": 16,
        "title": "Sistemas que combinan modelos, herramientas, memoria y planificación para actuar.",
    },
    "Tool Calling": {
        "color": "#72efdd",
        "size": 14,
        "title": "Capacidad de un modelo para usar funciones, APIs o herramientas externas.",
    },
    "Memoria": {
        "color": "#72efdd",
        "size": 14,
        "title": "Mecanismos para conservar contexto, hechos o historial útil durante interacciones.",
    },
    "Vector DB": {
        "color": "#72efdd",
        "size": 14,
        "title": "Base orientada a búsquedas por similitud sobre embeddings.",
    },
    "Chunking": {
        "color": "#72efdd",
        "size": 14,
        "title": "División de documentos en fragmentos para recuperación y contexto eficiente.",
    },
    "Re-ranking": {
        "color": "#72efdd",
        "size": 14,
        "title": "Reordenamiento de resultados recuperados para mejorar relevancia.",
    },
    "Hallucinations": {
        "color": "#72efdd",
        "size": 14,
        "title": "Respuestas incorrectas o inventadas que parecen plausibles.",
    },
    "Guardrails": {
        "color": "#72efdd",
        "size": 14,
        "title": "Restricciones, validaciones y políticas para controlar salidas de modelos.",
    },
    "Evaluación LLM": {
        "color": "#72efdd",
        "size": 14,
        "title": "Métricas y pruebas para medir calidad, seguridad y utilidad de respuestas.",
    },

    # =============================
    # Visión / multimodal
    # =============================
    "OCR": {
        "color": "#80ed99",
        "size": 14,
        "title": "Reconocimiento óptico de caracteres para extraer texto desde imágenes o PDFs.",
    },
    "Seguimiento de Objetos": {
        "color": "#80ed99",
        "size": 14,
        "title": "Seguimiento temporal de objetos a través de secuencias de video.",
    },
    "Pose Estimation": {
        "color": "#80ed99",
        "size": 14,
        "title": "Estimación de puntos clave del cuerpo u objetos en imágenes y video.",
    },
    "Multimodal": {
        "color": "#80ed99",
        "size": 16,
        "title": "Modelos o sistemas que combinan texto, imagen, audio, video u otras señales.",
    },

    # =============================
    # MLOps / Producción
    # =============================
    "Feature Engineering": {
        "color": "#c77dff",
        "size": 14,
        "title": "Transformación de variables para mejorar el desempeño de modelos.",
    },
    "Feature Store": {
        "color": "#c77dff",
        "size": 14,
        "title": "Sistema para almacenar y servir variables reutilizables de entrenamiento e inferencia.",
    },
    "Experiment Tracking": {
        "color": "#c77dff",
        "size": 14,
        "title": "Registro de métricas, parámetros, modelos y resultados experimentales.",
    },
    "Model Registry": {
        "color": "#c77dff",
        "size": 14,
        "title": "Catálogo versionado de modelos aprobados para pruebas o producción.",
    },
    "CI/CD": {
        "color": "#c77dff",
        "size": 14,
        "title": "Integración y despliegue continuo para automatizar pruebas y liberaciones.",
    },
    "A/B Testing": {
        "color": "#c77dff",
        "size": 14,
        "title": "Comparación controlada entre variantes para medir impacto real.",
    },
    "Inferencia en Tiempo Real": {
        "color": "#c77dff",
        "size": 14,
        "title": "Predicción inmediata a baja latencia para aplicaciones online.",
    },
    "Inferencia Batch": {
        "color": "#c77dff",
        "size": 14,
        "title": "Predicción masiva sobre grandes volúmenes de datos en procesos programados.",
    },
    "Canary Deployment": {
        "color": "#c77dff",
        "size": 14,
        "title": "Despliegue gradual a una pequeña parte del tráfico antes de escalar.",
    },
    "Observabilidad": {
        "color": "#c77dff",
        "size": 14,
        "title": "Monitoreo profundo de logs, métricas, trazas y comportamiento del sistema/modelo.",
    },

    # =============================
    # Data Engineering / Big Data
    # =============================
    "Data Warehouse": {
        "color": "#a8dadc",
        "size": 14,
        "title": "Repositorio estructurado optimizado para análisis y BI.",
    },
    "ELT": {
        "color": "#a8dadc",
        "size": 14,
        "title": "Variante donde los datos se cargan primero y luego se transforman.",
    },
    "Streaming": {
        "color": "#a8dadc",
        "size": 14,
        "title": "Procesamiento continuo de eventos y datos en movimiento.",
    },
    "Kafka": {
        "color": "#a8dadc",
        "size": 14,
        "title": "Plataforma distribuida para mensajería, eventos y pipelines en tiempo real.",
    },
    "Airflow": {
        "color": "#a8dadc",
        "size": 14,
        "title": "Orquestador de workflows y pipelines de datos.",
    },
    "Data Governance": {
        "color": "#a8dadc",
        "size": 14,
        "title": "Políticas y prácticas para calidad, trazabilidad, acceso y uso de datos.",
    },
    "Calidad de Datos": {
        "color": "#a8dadc",
        "size": 14,
        "title": "Medición y aseguramiento de integridad, consistencia y utilidad del dato.",
    },

    # =============================
    # Cloud
    # =============================
    "Cloud Computing": {
        "color": "#ffd166",
        "size": 24,
        "title": "Uso de servicios de infraestructura, plataforma y software bajo demanda.",
    },
    "AWS": {
        "color": "#ffd166",
        "size": 18,
        "title": "Proveedor cloud con servicios para cómputo, almacenamiento, IA y despliegue.",
    },
    "Azure": {
        "color": "#ffd166",
        "size": 18,
        "title": "Plataforma cloud de Microsoft con servicios de datos, IA y aplicaciones.",
    },
    "GCP": {
        "color": "#ffd166",
        "size": 18,
        "title": "Google Cloud Platform, fuerte en datos, analítica, contenedores y ML.",
    },
    "Huawei Cloud": {
        "color": "#ffd166",
        "size": 18,
        "title": "Proveedor cloud con servicios de infraestructura, almacenamiento y AI/cloud-native.",
    },
    "IaaS": {
        "color": "#ffd166",
        "size": 14,
        "title": "Infrastructure as a Service: máquinas, redes y almacenamiento administrables.",
    },
    "PaaS": {
        "color": "#ffd166",
        "size": 14,
        "title": "Platform as a Service: entornos listos para desplegar aplicaciones.",
    },
    "SaaS": {
        "color": "#ffd166",
        "size": 14,
        "title": "Software as a Service: aplicaciones consumidas directamente como servicio.",
    },
    "Serverless": {
        "color": "#ffd166",
        "size": 14,
        "title": "Ejecución de funciones o apps sin administrar servidores directamente.",
    },
    "Kubernetes": {
        "color": "#ffd166",
        "size": 14,
        "title": "Orquestador de contenedores para despliegue, escalado y operación de servicios.",
    },
    "Terraform": {
        "color": "#ffd166",
        "size": 14,
        "title": "Infraestructura como código para definir recursos cloud de forma reproducible.",
    },
    "IAM": {
        "color": "#ffd166",
        "size": 14,
        "title": "Gestión de identidades, roles y permisos en plataformas cloud.",
    },
    "Object Storage": {
        "color": "#ffd166",
        "size": 14,
        "title": "Almacenamiento escalable de objetos como archivos, datasets y artefactos.",
    },
    "Cloud Security": {
        "color": "#ffd166",
        "size": 14,
        "title": "Seguridad de identidades, redes, secretos, cifrado y cumplimiento en la nube.",
    },

    # =============================
    # Desarrollo de software
    # =============================
    "Desarrollo de Software": {
        "color": "#06d6a0",
        "size": 24,
        "title": "Disciplina para diseñar, construir, probar y mantener sistemas y aplicaciones.",
    },
    "Backend": {
        "color": "#06d6a0",
        "size": 14,
        "title": "Lógica de negocio, APIs, datos y procesamiento del lado servidor.",
    },
    "Frontend": {
        "color": "#06d6a0",
        "size": 14,
        "title": "Interfaces de usuario y experiencia visual del lado cliente.",
    },
    "APIs": {
        "color": "#06d6a0",
        "size": 14,
        "title": "Interfaces para comunicación entre sistemas y servicios.",
    },
    "Microservicios": {
        "color": "#06d6a0",
        "size": 14,
        "title": "Arquitectura basada en servicios pequeños, desacoplados y desplegables por separado.",
    },
    "Testing": {
        "color": "#06d6a0",
        "size": 14,
        "title": "Pruebas unitarias, integración y validación para asegurar calidad.",
    },
    "Git": {
        "color": "#06d6a0",
        "size": 14,
        "title": "Sistema de control de versiones para colaboración y trazabilidad del código.",
    },
    "Arquitectura de Software": {
        "color": "#06d6a0",
        "size": 14,
        "title": "Diseño de componentes, integraciones, escalabilidad y mantenibilidad del sistema.",
    },

    # =============================
    # Responsible AI / seguridad
    # =============================
    "Robustez": {
        "color": "#f28482",
        "size": 14,
        "title": "Capacidad del sistema para resistir ruido, ataques o cambios inesperados.",
    },
    "Seguridad IA": {
        "color": "#f28482",
        "size": 14,
        "title": "Protección contra ataques, fugas, abuso y comportamientos inseguros en sistemas de IA.",
    },
    "Gobernanza de IA": {
        "color": "#f28482",
        "size": 14,
        "title": "Políticas, controles y trazabilidad para operar IA de manera responsable.",
    },

    # =============================
    # Quantum Computing
    # =============================
    "Computación Cuántica": {
        "color": "#9b5de5",
        "size": 24,
        "title": "Paradigma de cómputo basado en qubits, superposición y entrelazamiento.",
    },
    "Qubits": {
        "color": "#9b5de5",
        "size": 16,
        "title": "Unidad básica de información cuántica.",
    },
    "Superposición": {
        "color": "#9b5de5",
        "size": 14,
        "title": "Propiedad que permite a un estado cuántico combinar múltiples posibilidades.",
    },
    "Entrelazamiento": {
        "color": "#9b5de5",
        "size": 14,
        "title": "Correlación cuántica fuerte entre qubits.",
    },
    "Puertas Cuánticas": {
        "color": "#9b5de5",
        "size": 14,
        "title": "Operaciones que transforman estados cuánticos en un circuito.",
    },
    "Circuitos Cuánticos": {
        "color": "#9b5de5",
        "size": 14,
        "title": "Secuencia de puertas cuánticas aplicada a qubits.",
    },
    "Medición Cuántica": {
        "color": "#9b5de5",
        "size": 14,
        "title": "Proceso de observación que colapsa el estado cuántico a un resultado clásico.",
    },
    "Algoritmo de Grover": {
        "color": "#9b5de5",
        "size": 14,
        "title": "Algoritmo cuántico para búsqueda con aceleración cuadrática idealizada.",
    },
    "Algoritmo de Shor": {
        "color": "#9b5de5",
        "size": 14,
        "title": "Algoritmo cuántico conocido por factorizar enteros en ciertos contextos.",
    },
    "QAOA": {
        "color": "#9b5de5",
        "size": 14,
        "title": "Quantum Approximate Optimization Algorithm, método híbrido para optimización.",
    },
    "VQE": {
        "color": "#9b5de5",
        "size": 14,
        "title": "Variational Quantum Eigensolver, algoritmo híbrido usado en simulación cuántica.",
    },
    "Qiskit": {
        "color": "#9b5de5",
        "size": 14,
        "title": "SDK popular para programación y experimentación en computación cuántica.",
    },
    "Quantum Machine Learning": {
        "color": "#9b5de5",
        "size": 16,
        "title": "Intersección entre computación cuántica y aprendizaje automático.",
    },
}

# -----------------------------
# Relaciones
# -----------------------------
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
    ("Redes Neuronales", "MLP"),
    ("Redes Neuronales", "CNN"),
    ("Redes Neuronales", "RNN"),
    ("Redes Neuronales", "LSTM"),
    ("Redes Neuronales", "GRU"),
    ("Redes Neuronales", "Transformers"),
    ("Redes Neuronales", "Autoencoders"),
    ("Redes Neuronales", "GANs"),
    ("Redes Neuronales", "Diffusion Models"),
    ("NLP", "Tokenización"),
    ("NLP", "Embeddings"),
    ("NLP", "Clasificación de Texto"),
    ("NLP", "NER"),
    ("NLP", "Análisis de Sentimiento"),
    ("NLP", "LLMs"),
    ("NLP", "RAG"),
    ("NLP", "Fine-Tuning"),
    ("LLMs", "Transformers"),
    ("Visión Artificial", "Clasificación de Imágenes"),
    ("Visión Artificial", "Detección de Objetos"),
    ("Visión Artificial", "Segmentación"),
    ("Visión Artificial", "YOLO"),
    ("Visión Artificial", "OpenCV"),
    ("Detección de Objetos", "YOLO"),
    ("Clasificación de Imágenes", "CNN"),
    ("MLOps", "Despliegue"),
    ("MLOps", "Monitoreo"),
    ("MLOps", "Drift"),
    ("MLOps", "MLflow"),
    ("MLOps", "Docker"),
    ("MLOps", "FastAPI"),
    ("Data Engineering", "ETL"),
    ("Data Engineering", "Pipelines"),
    ("Data Engineering", "Data Lake"),
    ("Data Engineering", "Spark"),
    ("Responsible AI", "Bias"),
    ("Responsible AI", "Explicabilidad"),
    ("Responsible AI", "Privacidad"),
    ("Responsible AI", "Fairness"),
    ("Data Engineering", "MLOps"),
    ("Machine Learning", "MLOps"),
    ("Deep Learning", "MLOps"),
    ("NLP", "RAG"),
    ("NLP", "Embeddings"),
    ("Visión Artificial", "Deep Learning"),
    ("Responsible AI", "Machine Learning"),
    ("Responsible AI", "Deep Learning"),
        # IA y ML
    ("Machine Learning", "Aprendizaje Semi-Supervisado"),
    ("Machine Learning", "Aprendizaje Auto-Supervisado"),
    ("Machine Learning", "Aprendizaje Online"),
    ("Machine Learning", "Meta-Learning"),
    ("Machine Learning", "Ensemble Learning"),
    ("Aprendizaje Supervisado", "Naive Bayes"),
    ("Aprendizaje Supervisado", "LDA"),
    ("Aprendizaje Supervisado", "QDA"),
    ("Aprendizaje Supervisado", "AdaBoost"),
    ("Aprendizaje Supervisado", "Gradient Boosting"),
    ("Aprendizaje Supervisado", "LightGBM"),
    ("Aprendizaje Supervisado", "CatBoost"),
    ("Aprendizaje No Supervisado", "Isolation Forest"),
    ("Aprendizaje No Supervisado", "One-Class SVM"),
    ("Aprendizaje No Supervisado", "t-SNE"),
    ("Aprendizaje No Supervisado", "UMAP"),
    ("Ensemble Learning", "Random Forest"),
    ("Ensemble Learning", "AdaBoost"),
    ("Ensemble Learning", "Gradient Boosting"),
    ("Ensemble Learning", "XGBoost"),
    ("Ensemble Learning", "LightGBM"),
    ("Ensemble Learning", "CatBoost"),

    # Deep Learning
    ("Deep Learning", "Transfer Learning"),
    ("Deep Learning", "Attention"),
    ("Attention", "Self-Attention"),
    ("Transformers", "Attention"),
    ("Transformers", "Self-Attention"),
    ("CNN", "ResNet"),
    ("Segmentación", "U-Net"),
    ("Deep Learning", "GNN"),
    ("Autoencoders", "VAE"),
    ("Fine-Tuning", "LoRA"),
    ("Fine-Tuning", "PEFT"),
    ("Transfer Learning", "ResNet"),

    # NLP / LLM / GenAI
    ("LLMs", "Prompt Engineering"),
    ("LLMs", "Zero-Shot"),
    ("LLMs", "Few-Shot"),
    ("LLMs", "In-Context Learning"),
    ("LLMs", "Instruction Tuning"),
    ("LLMs", "RLHF"),
    ("LLMs", "Agentes IA"),
    ("LLMs", "Tool Calling"),
    ("LLMs", "Hallucinations"),
    ("LLMs", "Guardrails"),
    ("LLMs", "Evaluación LLM"),
    ("Prompt Engineering", "Zero-Shot"),
    ("Prompt Engineering", "Few-Shot"),
    ("Prompt Engineering", "In-Context Learning"),
    ("RAG", "Vector DB"),
    ("RAG", "Chunking"),
    ("RAG", "Re-ranking"),
    ("RAG", "Embeddings"),
    ("Agentes IA", "Tool Calling"),
    ("Agentes IA", "Memoria"),

    # Visión / multimodal
    ("Visión Artificial", "OCR"),
    ("Visión Artificial", "Seguimiento de Objetos"),
    ("Visión Artificial", "Pose Estimation"),
    ("Visión Artificial", "Multimodal"),
    ("Detección de Objetos", "Seguimiento de Objetos"),
    ("Detección de Objetos", "Pose Estimation"),
    ("NLP", "Multimodal"),

    # MLOps
    ("MLOps", "Feature Engineering"),
    ("MLOps", "Feature Store"),
    ("MLOps", "Experiment Tracking"),
    ("MLOps", "Model Registry"),
    ("MLOps", "CI/CD"),
    ("MLOps", "A/B Testing"),
    ("MLOps", "Inferencia en Tiempo Real"),
    ("MLOps", "Inferencia Batch"),
    ("MLOps", "Canary Deployment"),
    ("MLOps", "Observabilidad"),
    ("MLflow", "Experiment Tracking"),
    ("MLflow", "Model Registry"),
    ("Despliegue", "Inferencia en Tiempo Real"),
    ("Despliegue", "Inferencia Batch"),

    # Data Engineering
    ("Data Engineering", "Data Warehouse"),
    ("Data Engineering", "ELT"),
    ("Data Engineering", "Streaming"),
    ("Data Engineering", "Kafka"),
    ("Data Engineering", "Airflow"),
    ("Data Engineering", "Data Governance"),
    ("Data Engineering", "Calidad de Datos"),
    ("Pipelines", "Airflow"),
    ("Streaming", "Kafka"),
    ("Data Lake", "Data Warehouse"),

    # Cloud
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
    ("MLOps", "Kubernetes"),
    ("MLOps", "Terraform"),
    ("MLOps", "Cloud Computing"),
    ("Data Engineering", "Cloud Computing"),

    # Desarrollo de software
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

    # Responsible AI
    ("Responsible AI", "Robustez"),
    ("Responsible AI", "Seguridad IA"),
    ("Responsible AI", "Gobernanza de IA"),
    ("Seguridad IA", "Guardrails"),
    ("Gobernanza de IA", "Evaluación LLM"),

    # Quantum
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

# -----------------------------
# Construcción del grafo
# -----------------------------
G = nx.Graph()

for node_name, attrs in nodes.items():
    G.add_node(
        node_name, color=attrs["color"], size=attrs["size"], title=attrs["title"]
    )

if show_edges:
    for source, target in edges:
        G.add_edge(source, target)

# -----------------------------
# Crear red PyVis
# -----------------------------
net = Network(
    height="820px", width="100%", bgcolor="#111111", font_color="white", notebook=False
)

net.from_nx(G)

for node in net.nodes:
    node["label"] = node["id"]
    node["font"] = {"size": 18, "color": "white"}

# -----------------------------
# Aplicar tipo de mapa
# -----------------------------
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
      "interaction": {{
        "hover": true,
        "tooltipDelay": 150,
        "dragNodes": true,
        "dragView": true,
        "zoomView": true,
        "navigationButtons": true
      }},
      "physics": {{
        "enabled": {str(physics_enabled).lower()}
      }}
    }}
    """)

elif tipo_mapa == "Jerárquico LR":
    net.set_options("""
    var options = {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "LR",
          "sortMethod": "directed",
          "levelSeparation": 180,
          "nodeSpacing": 180,
          "treeSpacing": 220
        }
      },
      "nodes": {
        "shape": "box",
        "margin": 12,
        "font": {
          "size": 16,
          "color": "white"
        }
      },
      "edges": {
        "smooth": {
          "enabled": true,
          "type": "cubicBezier"
        },
        "color": {
          "color": "#999999",
          "highlight": "#ffffff",
          "hover": "#ffffff"
        }
      },
      "interaction": {
        "hover": true,
        "dragView": true,
        "zoomView": true,
        "navigationButtons": true
      },
      "physics": {
        "enabled": false
      }
    }
    """)

elif tipo_mapa == "Jerárquico UD":
    net.set_options("""
    var options = {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",
          "sortMethod": "directed",
          "levelSeparation": 180,
          "nodeSpacing": 180,
          "treeSpacing": 220
        }
      },
      "nodes": {
        "shape": "box",
        "margin": 12,
        "font": {
          "size": 16,
          "color": "white"
        }
      },
      "edges": {
        "smooth": {
          "enabled": true,
          "type": "cubicBezier"
        },
        "color": {
          "color": "#999999",
          "highlight": "#ffffff",
          "hover": "#ffffff"
        }
      },
      "interaction": {
        "hover": true,
        "dragView": true,
        "zoomView": true,
        "navigationButtons": true
      },
      "physics": {
        "enabled": false
      }
    }
    """)

# -----------------------------
# Render HTML
# -----------------------------
with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
    net.save_graph(tmp_file.name)
    html_path = tmp_file.name

with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

components.html(html_content, height=850, scrolling=True)

try:
    os.unlink(html_path)
except Exception:
    pass

# -----------------------------
# Resumen
# -----------------------------
st.subheader("Resumen de áreas")
st.markdown("""
- **IA**: disciplina general que incluye múltiples técnicas para crear sistemas inteligentes.  
- **Machine Learning**: aprende a partir de datos.  
- **Deep Learning**: usa redes neuronales profundas para tareas complejas.  
- **NLP**: trabaja con texto, lenguaje y modelos de lenguaje.  
- **Visión Artificial**: analiza imágenes y video.  
- **MLOps**: lleva modelos a producción y los mantiene sanos.  
- **Data Engineering**: prepara y mueve los datos que alimentan los modelos.  
- **Responsible AI**: evita que la IA haga cosas peligrosas.
""")

# -----------------------------
# Autoría
# -----------------------------
st.markdown("---")
st.caption(
    "Construido por [Alexis Torres](https://www.linkedin.com/in/alexis-torres87) · "
    "[GitHub](https://github.com/AlexisTorrresA)"
)