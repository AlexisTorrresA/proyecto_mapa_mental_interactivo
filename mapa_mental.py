
import os
import json
import tempfile
import html
import io
import keyword
import token
import tokenize
from collections import deque, defaultdict

import altair as alt
import networkx as nx
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

st.set_page_config(
    page_title="Interactive Technology Concept Map",
    layout="wide",
    initial_sidebar_state="collapsed",
)

LINKEDIN_URL = "https://www.linkedin.com/in/alexis-torres87/"
GITHUB_URL = "https://github.com/AlexisTorrresA"
LINKEDIN_DISPLAY_NAME = "Alexis Torres Álvarez"
LINKEDIN_IMAGE_URL = os.getenv("LINKEDIN_IMAGE_URL", "")

top_bar = st.columns([1.2, 2.8], gap="medium")
with top_bar[0]:
    language_choice = st.selectbox("Idioma / Language", ["Español", "English"], index=0)
IS_EN = language_choice == "English"

def tr(es: str, en: str) -> str:
    return en if IS_EN else es

if "show_right_panel" not in st.session_state:
    st.session_state.show_right_panel = True
show_right_panel = st.session_state.show_right_panel
show_function_nodes = True

with top_bar[1]:
    st.caption(
        tr(
            "Los nodos de funciones se muestran automáticamente debajo de cada librería. El panel derecho se abre y cierra con la flecha lateral.",
            "Function nodes are shown automatically below each library. The right panel opens and closes with the side arrow."
        )
    )

st.title(tr("Mapa conceptual interactivo de tecnología", "Interactive Technology Concept Map"))
st.write(
    tr(
        "Haz click en un nodo para ver su detalle ampliado dentro del panel inferior del mapa. Usa los filtros superiores para simplificar la vista.",
        "Click a node to see its detailed information in the panel below the map. Use the top filters to simplify the view."
    )
)

NAME_TRANSLATIONS = {
    "Inteligencia Artificial": "Artificial Intelligence",
    "Ingeniería de Software": "Software Engineering",
    "Cloud Computing": "Cloud Computing",
    "Ciberseguridad": "Cybersecurity",
    "Robótica e IoT": "Robotics and IoT",
    "Computación Cuántica": "Quantum Computing",
    "Procesamiento de Lenguaje Natural": "Natural Language Processing",
    "Visión por Computador": "Computer Vision",
    "IA Generativa": "Generative AI",
    "Ciencia de Datos": "Data Science",
    "Ética y Gobernanza de IA": "AI Ethics and Governance",
    "Fundamentos de Programación": "Programming Fundamentals",
    "Desarrollo de Aplicaciones": "Application Development",
    "Bases de Datos": "Databases",
    "Arquitectura de Software": "Software Architecture",
    "Testing y Calidad": "Testing and Quality",
    "Gestión de Proyectos": "Project Management",
    "Infraestructura Cloud": "Cloud Infrastructure",
    "Servicios Cloud": "Cloud Services",
    "Redes y Sistemas": "Networks and Systems",
    "Datos en la Nube": "Cloud Data",
    "Seguridad Cloud": "Cloud Security",
    "Automatización y Operación": "Automation and Operations",
    "Seguridad de Redes": "Network Security",
    "Seguridad de Sistemas": "System Security",
    "Seguridad de Aplicaciones": "Application Security",
    "Gestión de Identidades": "Identity Management",
    "Monitoreo y Respuesta": "Monitoring and Response",
    "Gobernanza y Cumplimiento": "Governance and Compliance",
    "Electrónica y Hardware": "Electronics and Hardware",
    "Sensores y Actuadores": "Sensors and Actuators",
    "Sistemas Embebidos": "Embedded Systems",
    "Comunicación y Redes IoT": "IoT Communication and Networks",
    "Control y Automatización": "Control and Automation",
    "Visión e Inteligencia Integrada": "Integrated Vision and Intelligence",
    "Plataformas y Nube IoT": "IoT Platforms and Cloud",
    "Fundamentos Cuánticos": "Quantum Foundations",
    "Circuitos y Puertas Cuánticas": "Quantum Circuits and Gates",
    "Algoritmos Cuánticos": "Quantum Algorithms",
    "Machine Learning Cuántico": "Quantum Machine Learning",
    "Hardware y Ecosistema Cuántico": "Quantum Hardware and Ecosystem",
    "aprendizaje supervisado": "supervised learning",
    "aprendizaje no supervisado": "unsupervised learning",
    "aprendizaje por refuerzo": "reinforcement learning",
    "clasificación": "classification",
    "regresión": "regression",
    "clustering": "clustering",
    "redes neuronales": "neural networks",
    "clasificación de imágenes": "image classification",
    "detección de objetos": "object detection",
    "segmentación": "segmentation",
    "tokenización": "tokenization",
    "embeddings": "embeddings",
    "traducción": "translation",
    "limpieza de datos": "data cleaning",
    "análisis exploratorio": "exploratory analysis",
    "estadística descriptiva": "descriptive statistics",
    "inferencia": "inference",
    "visualización": "visualization",
    "feature engineering": "feature engineering",
    "versionado de modelos": "model versioning",
    "pipelines ML": "ML pipelines",
    "monitoreo": "monitoring",
    "sesgo algorítmico": "algorithmic bias",
    "explicabilidad": "explainability",
    "privacidad": "privacy",
    "auditoría": "audit",
    "algoritmos": "algorithms",
    "estructuras de datos": "data structures",
    "programación funcional": "functional programming",
    "complejidad algorítmica": "algorithmic complexity",
    "backend": "backend",
    "frontend": "frontend",
    "microservicios": "microservices",
    "integración": "integration",
    "modelo relacional": "relational model",
    "consultas": "queries",
    "transacciones": "transactions",
    "índices": "indexes",
    "monolito": "monolith",
    "arquitectura hexagonal": "hexagonal architecture",
    "observabilidad": "observability",
    "contenedores": "containers",
    "requisitos": "requirements",
    "historias de usuario": "user stories",
    "virtualización": "virtualization",
    "alta disponibilidad": "high availability",
    "redes virtuales": "virtual networks",
    "subredes": "subnets",
    "balanceadores": "load balancers",
    "administración Linux/Windows": "Linux/Windows administration",
    "data lake": "data lake",
    "data warehouse": "data warehouse",
    "bases de datos gestionadas": "managed databases",
    "almacenamiento objeto": "object storage",
    "cifrado": "encryption",
    "control de acceso": "access control",
    "cumplimiento": "compliance",
    "provisioning": "provisioning",
    "autoescalado": "autoscaling",
    "despliegue automatizado": "automated deployment",
    "firewalls": "firewalls",
    "segmentación": "segmentation",
    "análisis de tráfico": "traffic analysis",
    "hardening": "hardening",
    "gestión de parches": "patch management",
    "malware": "malware",
    "privilegios": "privileges",
    "validación de entradas": "input validation",
    "gestión de secretos": "secret management",
    "autenticación segura": "secure authentication",
    "autenticación": "authentication",
    "autorización": "authorization",
    "respuesta a incidentes": "incident response",
    "correlación de eventos": "event correlation",
    "riesgo": "risk",
    "políticas": "policies",
    "continuidad operacional": "operational continuity",
    "microcontroladores": "microcontrollers",
    "energía": "power",
    "señales": "signals",
    "circuitos": "circuits",
    "lectura de sensores": "sensor reading",
    "servos": "servos",
    "motores": "motors",
    "relés": "relays",
    "sensores de distancia": "distance sensors",
    "sensores de temperatura": "temperature sensors",
    "firmware": "firmware",
    "tiempo real": "real time",
    "edge computing": "edge computing",
    "optimización de recursos": "resource optimization",
    "navegación": "navigation",
    "control de movimiento": "motion control",
    "seguimiento": "tracking",
    "percepción": "perception",
    "decisión local": "local decision making",
    "gestión remota": "remote management",
    "ingestión de telemetría": "telemetry ingestion",
    "monitoreo de dispositivos": "device monitoring",
    "qubit": "qubit",
    "superposición": "superposition",
    "entrelazamiento": "entanglement",
    "interferencia": "interference",
    "medición cuántica": "quantum measurement",
    "puertas cuánticas": "quantum gates",
    "circuitos cuánticos": "quantum circuits",
    "Hadamard": "Hadamard",
    "CNOT": "CNOT",
    "Grover": "Grover",
    "Shor": "Shor",
    "QFT": "QFT",
    "VQE": "VQE",
    "QAOA": "QAOA",
    "circuitos variacionales": "variational circuits",
    "quantum kernels": "quantum kernels",
    "modelos híbridos": "hybrid models",
    "codificación de datos": "data encoding",
    "NISQ": "NISQ",
    "mitigación de errores": "error mitigation",
    "annealing": "annealing",
    "qubits superconductores": "superconducting qubits",
    "iones atrapados": "trapped ions",
}
KIND_TRANSLATIONS = {
    "principal": ("principal", "main"),
    "subarea": ("subárea", "subarea"),
    "concepto": ("concepto", "concept"),
    "herramienta": ("herramienta", "tool"),
    "libreria": ("librería", "library"),
    "framework": ("framework", "framework"),
    "recurso": ("recurso", "resource"),
    "dataset": ("dataset", "dataset"),
    "aplicacion": ("aplicación", "application"),
    "funcion": ("función", "function"),
    "contenedor": ("agrupador", "group"),
}
def translate_name(name: str) -> str:
    if not IS_EN:
        return name
    return NAME_TRANSLATIONS.get(name, name)

def translate_kind(kind: str) -> str:
    if kind not in KIND_TRANSLATIONS:
        return kind
    return KIND_TRANSLATIONS[kind][1] if IS_EN else KIND_TRANSLATIONS[kind][0]

def node_title(attrs: dict) -> str:
    return attrs.get("title_en", attrs.get("title", "")) if IS_EN else attrs.get("title", "")


# =========================================================
# Estilos
# =========================================================
KIND_STYLES = {
    "principal": {"shape": "dot", "size_boost": 10},
    "subarea": {"shape": "dot", "size_boost": 4},
    "concepto": {"shape": "dot", "size_boost": 0},
    "herramienta": {"shape": "box", "size_boost": -2},
    "libreria": {"shape": "box", "size_boost": -2},
    "framework": {"shape": "box", "size_boost": -2},
    "recurso": {"shape": "star", "size_boost": -2},
    "dataset": {"shape": "hexagon", "size_boost": -2},
    "aplicacion": {"shape": "diamond", "size_boost": -1},
    "funcion": {"shape": "ellipse", "size_boost": -4},
    "contenedor": {"shape": "dot", "size_boost": -2},
}

DOMAIN_COLORS = {
    "Inteligencia Artificial": "#f4d35e",
    "Ingeniería de Software": "#06d6a0",
    "Cloud Computing": "#ffd166",
    "Ciberseguridad": "#ff6b6b",
    "Robótica e IoT": "#9b5de5",
    "Computación Cuántica": "#7b6cff",
    "General": "#adb5bd",
}

TYPE_COLOR_OVERRIDES = {
    "herramienta": "#e9ecef",
    "libreria": "#d8f3dc",
    "framework": "#d8f3dc",
    "recurso": "#fff3bf",
    "dataset": "#e5dbff",
    "funcion": "#f1f3f5",
    "contenedor": "#dee2e6",
}

# =========================================================
# Sidebar
# =========================================================
st.sidebar.header(tr("Configuración del mapa", "Map settings"))

tipo_mapa = st.sidebar.selectbox(
    tr("Tipo de mapa", "Map type"),
    [tr("Libre", "Free"), "Jerárquico LR", "Jerárquico UD"]
)
if tipo_mapa == tr("Libre", "Free"):
    tipo_mapa = "Libre"

node_distance = st.sidebar.slider(tr("Distancia entre nodos", "Node distance"), 150, 700, 320, 10)
spring_length = st.sidebar.slider(tr("Longitud de resortes", "Spring length"), 80, 500, 260, 10)
central_gravity = st.sidebar.slider(tr("Gravedad central", "Central gravity"), 0.0, 1.0, 0.12, 0.01)
physics_enabled = st.sidebar.checkbox(tr("Activar física", "Enable physics"), True)
show_edges = st.sidebar.checkbox(tr("Mostrar relaciones", "Show relations"), True)

st.sidebar.markdown("---")
st.sidebar.subheader(tr("Vista temporal", "Timeline view"))
show_year_in_label = st.sidebar.checkbox(tr("Mostrar años en nodos", "Show years in nodes"), False)
show_timeline = st.sidebar.checkbox(tr("Mostrar línea de tiempo", "Show timeline"), True)
sort_by_epoch = st.sidebar.checkbox(tr("Ordenar conceptos por época", "Sort concepts by era"), True)

st.sidebar.markdown("---")
st.sidebar.subheader(tr("Exploración", "Exploration"))
st.sidebar.caption(tr("El detalle de cada nodo aparece dentro del panel inferior del mapa al hacer click.", "The detailed node panel appears below the map when you click a node."))

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

def make_node(kind, domain, year, title, size=12, url=None, examples=None, tools=None, functions=None, tags=None, related_concepts=None, related_subareas=None, code_example=None, title_en=None, label_en=None):
    return {
        "kind": kind,
        "domain": domain,
        "size": size,
        "year": year,
        "title": title,
        "title_en": title_en,
        "label_en": label_en,
        "url": url,
        "examples": examples or [],
        "tools": tools or [],
        "functions": functions or [],
        "tags": tags or [],
        "related_concepts": related_concepts or [],
        "related_subareas": related_subareas or [],
        "code_example": code_example,
    }

nodes = {}
edges = []

ALIASES = {
    "Pandas DS": "pandas",
    "NumPy DS": "NumPy",
    "Matplotlib DS": "Matplotlib",
    "spaCy NLP": "spaCy",
    "OpenCV Vision": "OpenCV",
    "OpenCV IoT": "OpenCV",
    "YOLO IoT": "YOLO",
    "FastAPI Apps": "FastAPI",
    "Weights & Biases MLOps": "Weights & Biases",
    "Colab": "Google Colab",
    "Postman QA": "Postman",
    "Transformers": "Transformers Library",
    "Transformers GenAI": "Transformers Library",
}

def canonical_name(name, kind=None):
    if kind == "concepto":
        return name
    return ALIASES.get(name, name)

def merge_unique_list(base, extra):
    result = list(base or [])
    for item in extra or []:
        if item not in result:
            result.append(item)
    return result

def add_node(name, attrs):
    key = canonical_name(name, attrs.get("kind"))
    attrs = dict(attrs)
    attrs.setdefault("label", key)
    if key not in nodes:
        nodes[key] = attrs
    else:
        existing = nodes[key]
        for list_field in ["examples", "tools", "functions", "tags", "related_concepts", "related_subareas"]:
            existing[list_field] = merge_unique_list(existing.get(list_field, []), attrs.get(list_field, []))
        for field in ["url", "year", "domain", "kind"]:
            if not existing.get(field) and attrs.get(field):
                existing[field] = attrs[field]
        if attrs.get("title"):
            if not existing.get("title"):
                existing["title"] = attrs["title"]
            elif attrs["title"] not in existing["title"]:
                longer = attrs["title"] if len(attrs["title"]) > len(existing["title"]) else existing["title"]
                existing["title"] = longer
        if attrs.get("size") and attrs.get("size", 0) > existing.get("size", 0):
            existing["size"] = attrs["size"]
    return key

def add_edge(src, dst, relation="relaciona"):
    src_key = canonical_name(src)
    dst_key = canonical_name(dst)
    edge = (src_key, dst_key, relation)
    if edge not in edges and src_key != dst_key:
        edges.append(edge)

def normalize_item(item, inferred_kind, subarea):
    if isinstance(item, dict):
        item_name = canonical_name(item["name"], item.get("kind", inferred_kind))
        item_kind = item.get("kind", inferred_kind)
        item_year = item.get("year")
        item_title = item.get("title", f"{item_name} dentro de {subarea}.")
        item_url = item.get("url")
        item_functions = item.get("functions", [])
        item_examples = item.get("examples", [])
        item_related_to = item.get("related_to", [])
    else:
        item_name = canonical_name(item, inferred_kind)
        item_kind = inferred_kind
        item_year = None
        item_title = f"{item} dentro de {subarea}."
        item_url = None
        item_functions = []
        item_examples = []
        item_related_to = []
    return {
        "name": item_name,
        "kind": item_kind,
        "year": item_year,
        "title": item_title,
        "url": item_url,
        "functions": item_functions,
        "examples": item_examples,
        "related_to": item_related_to,
    }

def relation_label(kind):
    return {
        "herramienta": "usa",
        "libreria": "usa",
        "framework": "usa",
        "recurso": "consulta",
        "dataset": "usa datos",
        "aplicacion": "aplica",
    }.get(kind, "relaciona")

def build_related_examples(item_kind, subarea, related):
    if item_kind == "libreria":
        return [
            f"Uso típico dentro de {subarea}.",
            f"Puede aplicarse en: {', '.join(related[:3])}." if related else f"Se relaciona con tareas de {subarea}.",
        ]
    if item_kind == "herramienta":
        return [
            f"Herramienta útil para trabajar {subarea}.",
            f"Suele apoyar flujos como: {', '.join(related[:3])}." if related else f"Se utiliza en actividades de {subarea}.",
        ]
    if item_kind == "recurso":
        return [
            f"Recurso recomendado para profundizar en {subarea}.",
            f"Sirve para estudiar o consultar temas como: {', '.join(related[:3])}." if related else f"Permite ampliar conocimiento de {subarea}.",
        ]
    if item_kind == "dataset":
        return [
            f"Dataset o fuente útil en {subarea}.",
            f"Se puede usar para practicar o evaluar: {', '.join(related[:3])}." if related else f"Apoya experimentación en {subarea}.",
        ]
    if item_kind == "aplicacion":
        return [
            f"Ejemplo de aplicación práctica en {subarea}.",
            f"Relacionado con: {', '.join(related[:3])}." if related else f"Conecta teoría con casos de uso de {subarea}.",
        ]
    return [f"Elemento asociado a {subarea}."]

def make_group_name(subarea, bucket_key):
    return f"{subarea} :: {bucket_key}"

def ensure_bucket_container(domain_root, subarea, bucket_key, label_es, label_en, description_es, description_en, bucket_kind=None):
    container_name = make_group_name(subarea, bucket_key)
    add_node(container_name, {
        "kind": "contenedor",
        "domain": domain_root,
        "size": 14,
        "title": description_es,
        "title_en": description_en,
        "label": label_es,
        "label_en": label_en,
        "tags": [domain_root, subarea, bucket_key],
        "related_subareas": [subarea],
        "related_concepts": [subarea],
        "bucket_key": bucket_key,
        "bucket_kind": bucket_kind,
    })
    add_edge(subarea, container_name, tr("agrupa", "groups"))
    return container_name

def add_taxonomy_branch(domain_root, subarea, concept_items=None, tool_items=None, lib_items=None, resource_items=None, dataset_items=None, app_items=None, year=None, description=None):
    add_node(subarea, {
        "kind": "subarea",
        "domain": domain_root,
        "size": 22,
        "year": year,
        "title": description or f"Subárea de {domain_root}: {subarea}.",
        "tags": [domain_root, subarea],
        "related_subareas": [subarea],
    })
    add_edge(domain_root, subarea, "incluye")

    normalized_concepts = [normalize_item(item, "concepto", subarea) for item in (concept_items or [])]
    concept_names = []

    for item in normalized_concepts:
        node_examples = item["examples"] or [
            f"Concepto perteneciente a {subarea}.",
            f"Forma parte del dominio {domain_root}.",
        ]
        add_node(
            item["name"],
            make_node(
                item["kind"],
                domain_root,
                item["year"],
                item["title"],
                size=13,
                url=item["url"],
                functions=item["functions"],
                examples=node_examples,
                tags=[domain_root, subarea, item["name"]],
                related_concepts=[item["name"]],
                related_subareas=[subarea],
            ),
        )
        add_edge(subarea, item["name"], "incluye")
        concept_names.append(item["name"])

    bucket_specs = [
        (tool_items or [], "herramienta", "tools", "Herramientas", "Tools", "Agrupa herramientas principales usadas en esta subárea.", "Groups the main tools used in this subarea."),
        (lib_items or [], "libreria", "libraries", "Librerías", "Libraries", "Agrupa librerías y frameworks principales de esta subárea.", "Groups the main libraries and frameworks in this subarea."),
        (resource_items or [], "recurso", "resources", "Recursos", "Resources", "Agrupa recursos y sitios recomendados para profundizar.", "Groups recommended resources and sites for further study."),
        (dataset_items or [], "dataset", "datasets", "Datasets", "Datasets", "Agrupa datasets y fuentes de datos representativas.", "Groups representative datasets and data sources."),
        (app_items or [], "aplicacion", "applications", "Aplicaciones", "Applications", "Agrupa aplicaciones y casos de uso prácticos.", "Groups applications and practical use cases."),
    ]

    for items, inferred_kind, bucket_key, label_es, label_en, desc_es, desc_en in bucket_specs:
        normalized_items = [normalize_item(item, inferred_kind, subarea) for item in items]
        if not normalized_items:
            continue

        container_name = ensure_bucket_container(domain_root, subarea, bucket_key, label_es, label_en, desc_es, desc_en)
        for item in normalized_items:
            related = item["related_to"] or concept_names[:] or [subarea]
            node_examples = item["examples"] or build_related_examples(item["kind"], subarea, related)
            extended_title = item["title"]
            if item["url"]:
                extended_title += " Recurso recomendado incluido para profundizar."
            if item["functions"]:
                extended_title += " Incluye funciones principales para consulta rápida."

            add_node(
                item["name"],
                make_node(
                    item["kind"],
                    domain_root,
                    item["year"],
                    extended_title,
                    size=12,
                    url=item["url"],
                    functions=item["functions"],
                    examples=node_examples,
                    tags=[domain_root, subarea, item["kind"], item["name"]],
                    related_concepts=related if concept_names else [],
                    related_subareas=[subarea],
                ),
            )
            add_edge(container_name, item["name"], relation_label(item["kind"]))

# =========================================================
# Nivel 0: dominios principales
# =========================================================
MAIN_DOMAINS = [
    ("Inteligencia Artificial", 1956, "Campo general que crea sistemas capaces de realizar tareas que normalmente requieren inteligencia humana."),
    ("Ingeniería de Software", 1968, "Disciplina para diseñar, construir, probar y mantener sistemas de software."),
    ("Cloud Computing", 2006, "Uso de infraestructura, plataformas y servicios remotos para desarrollar y operar sistemas."),
    ("Ciberseguridad", 1970, "Protección de sistemas, redes, datos y aplicaciones frente a amenazas."),
    ("Robótica e IoT", 1961, "Integración de hardware, sensores, control, conectividad e inteligencia en sistemas físicos."),
    ("Computación Cuántica", 1980, "Paradigma de cómputo basado en qubits, superposición, entrelazamiento y puertas cuánticas."),
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
    "related_subareas": ["Python"],
})
add_edge("Ingeniería de Software", "Python", "incluye")

python_libraries = [
    {
        "name": "Streamlit",
        "year": 2019,
        "title": "Framework Python para construir apps interactivas de datos y prototipos visuales.",
        "url": "https://streamlit.io/",
        "functions": ["title", "write", "sidebar", "selectbox", "dataframe"],
        "examples": ["Dashboards rápidos", "Prototipos de análisis", "Interfaces para modelos y datos"],
    },
    {
        "name": "NumPy",
        "year": 2006,
        "title": "Librería para computación numérica, arreglos multidimensionales y álgebra lineal básica.",
        "url": "https://numpy.org/",
        "functions": ["array", "mean", "dot", "linspace", "reshape"],
        "examples": ["Cálculo científico", "Álgebra lineal", "Preprocesamiento numérico"],
    },
    {
        "name": "Matplotlib",
        "year": 2003,
        "title": "Librería de visualización para gráficos estáticos, científicos y analíticos.",
        "url": "https://matplotlib.org/",
        "functions": ["plot", "scatter", "hist", "imshow", "figure"],
        "examples": ["Gráficos de líneas", "Histogramas", "Visualización exploratoria"],
    },
    {
        "name": "pandas",
        "year": 2008,
        "title": "Librería para manipulación, limpieza, transformación y análisis de datos tabulares.",
        "url": "https://pandas.pydata.org/docs/",
        "functions": ["DataFrame", "read_csv", "groupby", "merge", "pivot_table"],
        "examples": ["Lectura de CSV", "Transformaciones tabulares", "Agregaciones y joins"],
    },
    {
        "name": "spaCy",
        "year": 2015,
        "title": "Librería de NLP orientada a producción para procesamiento eficiente de texto.",
        "url": "https://spacy.io/",
        "functions": ["load", "pipe", "displacy", "Matcher", "Doc"],
        "examples": ["NER", "Lematización", "Pipelines de NLP"],
    },
    {
        "name": "Transformers Library",
        "year": 2019,
        "title": "Librería de Hugging Face para modelos transformer, NLP, visión e IA generativa.",
        "url": "https://huggingface.co/docs/transformers/index",
        "functions": ["pipeline", "AutoTokenizer", "AutoModel", "Trainer"],
        "examples": ["Clasificación de texto", "Embeddings", "Fine-tuning de modelos"],
    },
    {
        "name": "FastAPI",
        "year": 2018,
        "title": "Framework de Python para construir APIs rápidas, tipadas y con documentación automática.",
        "url": "https://fastapi.tiangolo.com/",
        "functions": ["FastAPI", "get", "post", "Depends", "BackgroundTasks"],
        "examples": ["APIs REST", "Serving de modelos", "Backends ligeros"],
    },
    {
        "name": "OpenCV",
        "year": 2000,
        "title": "Librería popular para procesamiento de imágenes, visión por computador y video.",
        "url": "https://opencv.org/",
        "functions": ["imread", "resize", "cvtColor", "VideoCapture", "findContours"],
        "examples": ["Detección visual", "Procesamiento de imágenes", "Visión en tiempo real"],
    },
]

python_libraries_container = ensure_bucket_container(
    "Ingeniería de Software",
    "Python",
    "libraries",
    "Librerías",
    "Libraries",
    "Agrupa las principales librerías del ecosistema Python usadas en el mapa.",
    "Groups the main Python ecosystem libraries used in the map.",
    bucket_kind="libreria",
)

for lib in python_libraries:
    item = normalize_item(lib, "libreria", "Python")
    add_node(
        item["name"],
        make_node(
            item["kind"],
            "Ingeniería de Software",
            item["year"],
            item["title"] + " Haz click para ver funciones principales, ejemplos y enlace.",
            size=12,
            url=item["url"],
            functions=item["functions"],
            examples=item["examples"],
            tags=["Ingeniería de Software", "Python", "libreria", item["name"]],
            related_concepts=["Python"],
            related_subareas=["Python"],
        ),
    )
    add_edge(python_libraries_container, item["name"], "usa")

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
# Computación Cuántica
# =========================================================
add_taxonomy_branch(
    "Computación Cuántica",
    "Fundamentos Cuánticos",
    concept_items=[
        {"name": "qubit", "title": "Unidad básica de información cuántica.", "title_en": "Basic unit of quantum information.", "year": 1980},
        {"name": "superposición", "title": "Capacidad de un estado cuántico para existir en múltiples amplitudes a la vez.", "title_en": "Capability of a quantum state to exist in multiple amplitudes at once."},
        {"name": "entrelazamiento", "title": "Correlación cuántica no clásica entre sistemas.", "title_en": "Non-classical quantum correlation between systems."},
        {"name": "interferencia", "title": "Combinación de amplitudes que refuerzan o cancelan probabilidades.", "title_en": "Combination of amplitudes that reinforce or cancel probabilities."},
        {"name": "medición cuántica", "title": "Proceso de colapso probabilístico del estado cuántico.", "title_en": "Probabilistic collapse of a quantum state during measurement."},
    ],
    tool_items=[
        {"name": "IBM Quantum Composer", "title": "Entorno visual para construir circuitos cuánticos.", "title_en": "Visual environment to build quantum circuits.", "year": 2019, "url": "https://quantum.ibm.com/"},
        {"name": "Quirk", "title": "Simulador visual de circuitos cuánticos en el navegador.", "title_en": "Browser-based visual quantum circuit simulator.", "year": 2016, "url": "https://algassert.com/quirk"},
    ],
    lib_items=[
        {"name": "Qiskit", "title": "SDK principal para circuitos y algoritmos cuánticos.", "title_en": "Main SDK for quantum circuits and algorithms.", "year": 2017, "url": "https://qiskit.org/"},
        {"name": "Cirq", "title": "Framework para construir y simular circuitos cuánticos.", "title_en": "Framework to build and simulate quantum circuits.", "year": 2018, "url": "https://quantumai.google/cirq"},
    ],
    resource_items=[
        {"name": "IBM Quantum Learning", "title": "Ruta de aprendizaje oficial de IBM Quantum.", "title_en": "Official IBM Quantum learning path.", "url": "https://learning.quantum.ibm.com/"},
        {"name": "Qiskit Docs", "title": "Documentación oficial de Qiskit.", "title_en": "Official Qiskit documentation.", "url": "https://docs.quantum.ibm.com/"},
    ],
    dataset_items=[
        {"name": "OpenQASM examples", "title": "Ejemplos y circuitos de referencia en OpenQASM.", "title_en": "Reference examples and circuits in OpenQASM."},
    ],
    year=1980,
    description="Conceptos base para comprender el cómputo cuántico y la representación de información en qubits."
)

add_taxonomy_branch(
    "Computación Cuántica",
    "Circuitos y Puertas Cuánticas",
    concept_items=[
        {"name": "puertas cuánticas", "title": "Operaciones unitarias sobre qubits.", "title_en": "Unitary operations applied to qubits."},
        {"name": "circuitos cuánticos", "title": "Secuencias de puertas y mediciones.", "title_en": "Sequences of gates and measurements."},
        {"name": "Hadamard", "title": "Puerta que crea superposición balanceada.", "title_en": "Gate that creates balanced superposition."},
        {"name": "Pauli-X", "title": "Puerta equivalente a un NOT cuántico.", "title_en": "Gate equivalent to a quantum NOT."},
        {"name": "CNOT", "title": "Puerta de control importante para entrelazamiento.", "title_en": "Controlled gate important for entanglement."},
        {"name": "esfera de Bloch", "title": "Representación geométrica del estado de un qubit.", "title_en": "Geometric representation of a qubit state."},
    ],
    tool_items=[
        {"name": "IBM Quantum Lab", "title": "Entorno cloud para ejecutar notebooks cuánticos.", "title_en": "Cloud environment to run quantum notebooks.", "year": 2019, "url": "https://quantum.ibm.com/"},
    ],
    lib_items=[
        {"name": "Qiskit Circuit Library", "title": "Colección de componentes reutilizables para circuitos.", "title_en": "Reusable building blocks for circuits.", "year": 2020, "url": "https://docs.quantum.ibm.com/api/qiskit/circuit_library"},
        {"name": "Cirq Gates", "title": "Colección de puertas y abstracciones de circuitos en Cirq.", "title_en": "Gate collection and circuit abstractions in Cirq.", "year": 2018, "url": "https://quantumai.google/cirq"},
    ],
    resource_items=[
        {"name": "OpenQASM", "title": "Lenguaje intermedio para circuitos cuánticos.", "title_en": "Intermediate language for quantum circuits.", "url": "https://openqasm.com/"},
        {"name": "Quantum circuit tutorials", "title": "Tutoriales introductorios de circuitos cuánticos.", "title_en": "Introductory quantum circuit tutorials."},
    ],
    dataset_items=[
        {"name": "QASMBench", "title": "Colección de circuitos benchmark para compiladores y hardware cuántico.", "title_en": "Benchmark circuit collection for quantum compilers and hardware.", "url": "https://www.gitlink.org.cn/scnc/QASMBench"},
    ],
    year=1995,
    description="Construcción de circuitos, compuertas y representaciones del estado cuántico."
)

add_taxonomy_branch(
    "Computación Cuántica",
    "Algoritmos Cuánticos",
    concept_items=[
        {"name": "Grover", "title": "Algoritmo de búsqueda con ventaja cuadrática.", "title_en": "Search algorithm with quadratic speedup."},
        {"name": "Shor", "title": "Algoritmo cuántico de factorización.", "title_en": "Quantum factoring algorithm."},
        {"name": "QFT", "title": "Transformada Cuántica de Fourier.", "title_en": "Quantum Fourier Transform."},
        {"name": "VQE", "title": "Algoritmo variacional para química cuántica.", "title_en": "Variational algorithm for quantum chemistry."},
        {"name": "QAOA", "title": "Algoritmo variacional para optimización aproximada.", "title_en": "Variational algorithm for approximate optimization."},
    ],
    tool_items=[
        {"name": "IBM Runtime", "title": "Ejecución administrada de programas cuánticos en IBM.", "title_en": "Managed execution of quantum programs on IBM.", "year": 2021, "url": "https://quantum.ibm.com/"},
        {"name": "Azure Quantum", "title": "Plataforma de acceso a hardware y servicios cuánticos.", "title_en": "Access platform for quantum hardware and services.", "year": 2021, "url": "https://azure.microsoft.com/en-us/products/quantum"},
    ],
    lib_items=[
        {"name": "Qiskit Algorithms", "title": "Módulos para algoritmos cuánticos clásicos y variacionales.", "title_en": "Modules for classical, quantum and variational algorithms.", "year": 2023, "url": "https://qiskit-community.github.io/qiskit-algorithms/"},
        {"name": "D-Wave Ocean", "title": "SDK para annealing cuántico y optimización.", "title_en": "SDK for quantum annealing and optimization.", "year": 2018, "url": "https://docs.ocean.dwavesys.com/"},
    ],
    resource_items=[
        {"name": "Quantum algorithm zoo", "title": "Colección de algoritmos cuánticos.", "title_en": "Collection of quantum algorithms.", "url": "https://quantumalgorithmzoo.org/"},
        {"name": "Qiskit algorithms docs", "title": "Documentación de algoritmos en Qiskit.", "title_en": "Qiskit algorithm documentation.", "url": "https://qiskit-community.github.io/qiskit-algorithms/"},
    ],
    dataset_items=[
        {"name": "benchmark circuits", "title": "Circuitos de referencia para evaluar algoritmos y hardware.", "title_en": "Reference circuits to evaluate algorithms and hardware."},
    ],
    year=1994,
    description="Algoritmos icónicos y variacionales usados en búsqueda, factorización, optimización y simulación."
)

add_taxonomy_branch(
    "Computación Cuántica",
    "Machine Learning Cuántico",
    concept_items=[
        {"name": "circuitos variacionales", "title": "Modelos paramétricos entrenables basados en circuitos.", "title_en": "Trainable parametric models based on circuits."},
        {"name": "quantum kernels", "title": "Kernels derivados de mapas de características cuánticos.", "title_en": "Kernels derived from quantum feature maps."},
        {"name": "modelos híbridos", "title": "Arquitecturas que combinan componentes clásicos y cuánticos.", "title_en": "Architectures that combine classical and quantum components."},
        {"name": "codificación de datos", "title": "Estrategias para incrustar datos clásicos en estados cuánticos.", "title_en": "Strategies to embed classical data into quantum states."},
    ],
    tool_items=[
        {"name": "PennyLane demos", "title": "Colección práctica de ejemplos de QML.", "title_en": "Practical collection of QML examples.", "year": 2020, "url": "https://pennylane.ai/qml/demonstrations"},
    ],
    lib_items=[
        {"name": "PennyLane", "title": "Framework para computación cuántica diferenciable.", "title_en": "Framework for differentiable quantum computing.", "year": 2018, "url": "https://pennylane.ai/"},
        {"name": "Qiskit Machine Learning", "title": "Módulos de aprendizaje automático sobre Qiskit.", "title_en": "Machine learning modules built on Qiskit.", "year": 2021, "url": "https://qiskit-community.github.io/qiskit-machine-learning/"},
        {"name": "TorchQuantum", "title": "Framework experimental para QML con PyTorch.", "title_en": "Experimental framework for QML with PyTorch.", "year": 2022, "url": "https://github.com/mit-han-lab/torchquantum"},
    ],
    resource_items=[
        {"name": "PennyLane docs", "title": "Documentación oficial de PennyLane.", "title_en": "Official PennyLane documentation.", "url": "https://docs.pennylane.ai/"},
        {"name": "QML papers", "title": "Papers y recursos sobre quantum machine learning.", "title_en": "Papers and resources about quantum machine learning."},
    ],
    dataset_items=[
        {"name": "Iris QML", "title": "Uso clásico de Iris como benchmark pedagógico en QML.", "title_en": "Classic Iris benchmark used for educational QML workflows."},
    ],
    year=2018,
    description="Uso de circuitos y kernels cuánticos en problemas de aprendizaje automático."
)

add_taxonomy_branch(
    "Computación Cuántica",
    "Hardware y Ecosistema Cuántico",
    concept_items=[
        {"name": "qubits superconductores", "title": "Tecnología de hardware basada en circuitos superconductores.", "title_en": "Hardware technology based on superconducting circuits."},
        {"name": "iones atrapados", "title": "Plataforma de hardware basada en iones controlados electromagnéticamente.", "title_en": "Hardware platform based on electromagnetically controlled ions."},
        {"name": "annealing", "title": "Paradigma de optimización cuántica basado en annealing.", "title_en": "Quantum optimization paradigm based on annealing."},
        {"name": "NISQ", "title": "Era de dispositivos cuánticos ruidosos de escala intermedia.", "title_en": "Noisy intermediate-scale quantum era."},
        {"name": "mitigación de errores", "title": "Técnicas para reducir el impacto del ruido.", "title_en": "Techniques to reduce the impact of noise."},
    ],
    tool_items=[
        {"name": "IBM Quantum", "title": "Acceso a hardware cuántico superconductivo.", "title_en": "Access to superconducting quantum hardware.", "year": 2016, "url": "https://quantum.ibm.com/"},
        {"name": "D-Wave Leap", "title": "Plataforma cloud para annealing cuántico.", "title_en": "Cloud platform for quantum annealing.", "year": 2018, "url": "https://cloud.dwavesys.com/leap/"},
        {"name": "Azure Quantum Workspace", "title": "Espacio de trabajo para proveedores y simuladores cuánticos.", "title_en": "Workspace for quantum providers and simulators.", "year": 2021, "url": "https://azure.microsoft.com/en-us/products/quantum"},
    ],
    lib_items=[
        {"name": "Qiskit Runtime", "title": "Servicios de ejecución optimizada para IBM Quantum.", "title_en": "Optimized execution services for IBM Quantum.", "year": 2022, "url": "https://docs.quantum.ibm.com/run"},
    ],
    resource_items=[
        {"name": "Azure Quantum docs", "title": "Documentación oficial de Azure Quantum.", "title_en": "Official Azure Quantum documentation.", "url": "https://learn.microsoft.com/azure/quantum/"},
        {"name": "D-Wave docs", "title": "Documentación oficial de D-Wave.", "title_en": "Official D-Wave documentation.", "url": "https://docs.dwavesys.com/"},
    ],
    dataset_items=[
        {"name": "hardware calibration data", "title": "Métricas y calibraciones de dispositivos cuánticos.", "title_en": "Metrics and calibrations from quantum devices."},
    ],
    year=2015,
    description="Panorama de plataformas, hardware, ruido, ejecución y ecosistema cuántico."
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
    ("Machine Learning Cuántico", "Inteligencia Artificial"),
    ("Algoritmos Cuánticos", "Cloud Computing"),
    ("Computación Cuántica", "Ingeniería de Software"),
]
for src, dst in cross_links:
    if src in nodes and dst in nodes:
        add_edge(src, dst, "relaciona")

# =========================================================
# Funciones de librerías y agrupación visual
# =========================================================
LIBRARY_FUNCTION_CATALOG = {
    "Streamlit": [
        {"name": "st.title", "description": "Muestra un título principal en la app.", "code": "import streamlit as st\nst.title('Demo')"},
        {"name": "st.write", "description": "Renderiza texto, tablas u objetos de forma flexible.", "code": "st.write('Hola mundo')"},
        {"name": "st.selectbox", "description": "Crea un selector desplegable.", "code": "option = st.selectbox('Choose', ['A', 'B'])"},
    ],
    "NumPy": [
        {"name": "np.array", "description": "Crea arreglos multidimensionales.", "code": "import numpy as np\na = np.array([1, 2, 3])"},
        {"name": "np.mean", "description": "Calcula el promedio de un arreglo.", "code": "np.mean([1, 2, 3])"},
        {"name": "np.dot", "description": "Producto punto o multiplicación matricial básica.", "code": "np.dot([1, 2], [3, 4])"},
    ],
    "Matplotlib": [
        {"name": "plt.plot", "description": "Genera un gráfico de líneas.", "code": "import matplotlib.pyplot as plt\nplt.plot([1,2,3],[2,4,6])"},
        {"name": "plt.scatter", "description": "Genera un gráfico de dispersión.", "code": "plt.scatter([1,2,3],[2,4,6])"},
    ],
    "pandas": [
        {"name": "pd.DataFrame", "description": "Crea una tabla etiquetada.", "code": "import pandas as pd\ndf = pd.DataFrame({'a':[1,2]})"},
        {"name": "pd.read_csv", "description": "Lee archivos CSV.", "code": "df = pd.read_csv('data.csv')"},
        {"name": "df.groupby", "description": "Agrupa datos para agregaciones.", "code": "df.groupby('category').sum()"},
    ],
    "spaCy": [
        {"name": "spacy.load", "description": "Carga un modelo de lenguaje.", "code": "import spacy\nnlp = spacy.load('en_core_web_sm')"},
        {"name": "nlp.pipe", "description": "Procesa múltiples textos eficientemente.", "code": "docs = list(nlp.pipe(['hello', 'world']))"},
    ],
    "Transformers Library": [
        {"name": "pipeline", "description": "Interfaz de alto nivel para tareas comunes.", "code": "from transformers import pipeline\nclf = pipeline('sentiment-analysis')"},
        {"name": "AutoTokenizer", "description": "Carga el tokenizador adecuado para un modelo.", "code": "from transformers import AutoTokenizer\ntok = AutoTokenizer.from_pretrained('bert-base-uncased')"},
        {"name": "AutoModel", "description": "Carga un modelo preentrenado genérico.", "code": "from transformers import AutoModel\nmodel = AutoModel.from_pretrained('bert-base-uncased')"},
    ],
    "FastAPI": [
        {"name": "FastAPI", "description": "Instancia principal de la aplicación.", "code": "from fastapi import FastAPI\napp = FastAPI()"},
        {"name": "@app.get", "description": "Declara un endpoint GET.", "code": "@app.get('/hello')\ndef hello():\n    return {'msg': 'hi'}"},
        {"name": "Depends", "description": "Inyección de dependencias.", "code": "from fastapi import Depends"},
    ],
    "OpenCV": [
        {"name": "cv2.imread", "description": "Lee una imagen desde disco.", "code": "import cv2\nimg = cv2.imread('image.jpg')"},
        {"name": "cv2.resize", "description": "Redimensiona una imagen.", "code": "resized = cv2.resize(img, (224, 224))"},
    ],
    "scikit-learn": [
        {"name": "fit", "description": "Entrena el modelo con datos.", "code": "model.fit(X_train, y_train)"},
        {"name": "predict", "description": "Predice etiquetas o valores.", "code": "pred = model.predict(X_test)"},
        {"name": "transform", "description": "Transforma datos mediante un estimador.", "code": "X_scaled = scaler.transform(X_test)"},
    ],
    "XGBoost": [
        {"name": "fit", "description": "Entrena un modelo boosting.", "code": "model.fit(X_train, y_train)"},
        {"name": "predict", "description": "Predice con el modelo entrenado.", "code": "pred = model.predict(X_test)"},
    ],
    "LightGBM": [
        {"name": "fit", "description": "Entrena un modelo LightGBM.", "code": "model.fit(X_train, y_train)"},
        {"name": "predict", "description": "Predice con el modelo entrenado.", "code": "pred = model.predict(X_test)"},
    ],
    "PyTorch": [
        {"name": "torch.randn", "description": "Genera tensores con distribución normal estándar, útil para pesos iniciales, ejemplos y pruebas rápidas.", "code": "import torch\nweights = torch.randn(input_size, hidden_size, requires_grad=True)"},
        {"name": "nn.Module", "description": "Clase base para modelos en PyTorch.", "code": "import torch.nn as nn\nclass Net(nn.Module):\n    pass"},
        {"name": "forward", "description": "Define el flujo directo del modelo.", "code": "def forward(self, x):\n    return x"},
        {"name": "optimizer.step", "description": "Actualiza los parámetros del modelo.", "code": "optimizer.step()"},
    ],
    "TensorFlow": [
        {"name": "tf.keras.Sequential", "description": "Crea un modelo secuencial.", "code": "import tensorflow as tf\nmodel = tf.keras.Sequential([])"},
        {"name": "model.fit", "description": "Entrena el modelo.", "code": "model.fit(X_train, y_train, epochs=5)"},
    ],
    "Keras": [
        {"name": "Sequential", "description": "Modelo de capas apiladas.", "code": "from keras import Sequential\nmodel = Sequential()"},
        {"name": "Dense", "description": "Capa densa totalmente conectada.", "code": "from keras.layers import Dense\nDense(64, activation='relu')"},
    ],
    "YOLO": [
        {"name": "model.predict", "description": "Ejecuta inferencia sobre imágenes o video.", "code": "from ultralytics import YOLO\nmodel = YOLO('yolov8n.pt')\nresults = model.predict('image.jpg')"},
        {"name": "model.train", "description": "Entrena o reajusta un modelo YOLO.", "code": "model.train(data='coco128.yaml', epochs=10)"},
    ],
    "Plotly": [
        {"name": "px.line", "description": "Genera líneas rápidas con Plotly Express.", "code": "import plotly.express as px\nfig = px.line(df, x='x', y='y')"},
        {"name": "px.scatter", "description": "Genera dispersión interactiva.", "code": "fig = px.scatter(df, x='x', y='y')"},
    ],
    "SciPy": [
        {"name": "scipy.optimize.minimize", "description": "Minimiza funciones objetivo.", "code": "from scipy.optimize import minimize\nres = minimize(func, x0=[0.0])"},
    ],
    "statsmodels": [
        {"name": "OLS", "description": "Modelo de regresión lineal clásica.", "code": "import statsmodels.api as sm\nmodel = sm.OLS(y, X).fit()"},
    ],
    "MLflow SDK": [
        {"name": "mlflow.start_run", "description": "Abre un experimento rastreable.", "code": "import mlflow\nwith mlflow.start_run():\n    mlflow.log_param('lr', 0.01)"},
        {"name": "mlflow.log_metric", "description": "Registra métricas de entrenamiento.", "code": "mlflow.log_metric('accuracy', 0.95)"},
    ],
    "Feast": [
        {"name": "FeatureStore", "description": "Accede a un feature store.", "code": "from feast import FeatureStore\nstore = FeatureStore('.')"},
    ],
    "BentoML": [
        {"name": "bentoml.service", "description": "Declara un servicio de inferencia.", "code": "import bentoml\n@bentoml.service\nclass MyService: pass"},
    ],
    "Evidently": [
        {"name": "Report", "description": "Construye reportes de calidad y drift.", "code": "from evidently.report import Report\nreport = Report(metrics=[])"},
    ],
    "SQLAlchemy": [
        {"name": "create_engine", "description": "Crea una conexión a base de datos.", "code": "from sqlalchemy import create_engine\nengine = create_engine('sqlite:///db.sqlite3')"},
        {"name": "Session", "description": "Gestiona sesiones ORM.", "code": "from sqlalchemy.orm import Session"},
    ],
    "pymongo": [
        {"name": "MongoClient", "description": "Crea un cliente para MongoDB.", "code": "from pymongo import MongoClient\nclient = MongoClient('mongodb://localhost:27017')"},
    ],
    "Qiskit": [
        {"name": "QuantumCircuit", "description": "Construye circuitos cuánticos.", "code": "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)"},
        {"name": "transpile", "description": "Compila un circuito para un backend.", "code": "from qiskit import transpile\ncompiled = transpile(qc, backend)"},
    ],
    "Cirq": [
        {"name": "Circuit", "description": "Construye circuitos en Cirq.", "code": "import cirq\nq = cirq.LineQubit.range(2)\ncircuit = cirq.Circuit(cirq.H(q[0]))"},
    ],
    "PennyLane": [
        {"name": "qml.qnode", "description": "Convierte una función cuántica en un nodo ejecutable.", "code": "import pennylane as qml\n@qml.qnode(dev)\ndef circuit(x):\n    return qml.expval(qml.Z(0))"},
        {"name": "qml.StronglyEntanglingLayers", "description": "Plantilla común para circuitos variacionales.", "code": "qml.StronglyEntanglingLayers(weights, wires=[0,1])"},
    ],
    "Qiskit Machine Learning": [
        {"name": "QSVC", "description": "Clasificador basado en kernels cuánticos.", "code": "from qiskit_machine_learning.algorithms import QSVC"},
    ],
    "Qiskit Algorithms": [
        {"name": "VQE", "description": "Implementación variacional para encontrar energías mínimas.", "code": "from qiskit_algorithms import VQE"},
        {"name": "QAOA", "description": "Implementación de optimización aproximada cuántica.", "code": "from qiskit_algorithms import QAOA"},
    ],
    "D-Wave Ocean": [
        {"name": "EmbeddingComposite", "description": "Prepara problemas para hardware annealing.", "code": "from dwave.system import EmbeddingComposite"},
    ],
    "Qiskit Runtime": [
        {"name": "Sampler", "description": "Primitive de ejecución para muestrear circuitos.", "code": "from qiskit_ibm_runtime import Sampler"},
    ],
}

MIN_FUNCTIONS_PER_LIBRARY = 10

LIBRARY_FUNCTION_FALLBACKS = {
    "Streamlit": ["st.header", "st.subheader", "st.metric", "st.button", "st.checkbox", "st.radio", "st.slider", "st.columns", "st.tabs", "st.container"],
    "NumPy": ["np.zeros", "np.ones", "np.arange", "np.linspace", "np.reshape", "np.sum", "np.std", "np.random.randn", "np.matmul", "np.concatenate"],
    "Matplotlib": ["plt.figure", "plt.title", "plt.xlabel", "plt.ylabel", "plt.legend", "plt.imshow", "plt.hist", "plt.bar", "plt.subplot", "plt.show"],
    "pandas": ["pd.Series", "df.head", "df.describe", "df.merge", "df.sort_values", "df.fillna", "df.dropna", "df.pivot_table", "df.loc", "df.to_csv"],
    "spaCy": ["nlp", "Doc", "Token", "Span", "Matcher", "PhraseMatcher", "EntityRuler", "displacy.render", "DocBin", "nlp.add_pipe"],
    "Transformers Library": ["AutoModelForSequenceClassification", "AutoModelForCausalLM", "AutoProcessor", "DataCollatorWithPadding", "TrainingArguments", "Trainer", "pipeline", "AutoConfig", "AutoFeatureExtractor", "set_seed"],
    "FastAPI": ["Query", "Path", "Body", "UploadFile", "HTTPException", "status", "APIRouter", "Depends", "BackgroundTasks", "middleware"],
    "OpenCV": ["cv2.cvtColor", "cv2.GaussianBlur", "cv2.threshold", "cv2.Canny", "cv2.imshow", "cv2.VideoCapture", "cv2.rectangle", "cv2.putText", "cv2.findContours", "cv2.imwrite"],
    "scikit-learn": ["fit", "predict", "transform", "fit_transform", "score", "train_test_split", "StandardScaler", "Pipeline", "GridSearchCV", "classification_report"],
    "XGBoost": ["DMatrix", "XGBClassifier", "XGBRegressor", "fit", "predict", "predict_proba", "plot_importance", "cv", "train", "save_model"],
    "LightGBM": ["Dataset", "LGBMClassifier", "LGBMRegressor", "fit", "predict", "predict_proba", "plot_importance", "train", "cv", "save_model"],
    "PyTorch": ["torch.randn", "torch.tensor", "torch.zeros", "torch.ones", "torch.matmul", "nn.Module", "nn.Linear", "torch.relu", "torch.softmax", "optimizer.step"],
    "TensorFlow": ["tf.constant", "tf.Variable", "tf.data.Dataset", "tf.keras.Sequential", "tf.keras.layers.Dense", "tf.keras.Model", "model.compile", "model.fit", "model.evaluate", "model.predict"],
    "Keras": ["Sequential", "Dense", "Dropout", "Conv2D", "MaxPooling2D", "Flatten", "compile", "fit", "evaluate", "predict"],
    "YOLO": ["model.predict", "model.train", "model.val", "model.export", "model.track", "model.info", "model.names", "results.plot", "results.save", "YOLO"],
    "Plotly": ["px.line", "px.scatter", "px.bar", "px.histogram", "go.Figure", "fig.update_layout", "fig.update_traces", "fig.add_trace", "px.imshow", "px.box"],
    "SciPy": ["scipy.optimize.minimize", "scipy.stats.norm", "scipy.linalg.inv", "scipy.signal.find_peaks", "scipy.sparse.csr_matrix", "scipy.interpolate.interp1d", "scipy.integrate.quad", "scipy.fft.fft", "scipy.cluster.vq.kmeans", "scipy.spatial.distance.cdist"],
    "statsmodels": ["OLS", "GLM", "Logit", "add_constant", "fit", "predict", "summary", "tsa.ARIMA", "graphics.plot_regress_exog", "stats.anova_lm"],
    "MLflow SDK": ["mlflow.start_run", "mlflow.end_run", "mlflow.log_param", "mlflow.log_metric", "mlflow.log_artifact", "mlflow.set_experiment", "mlflow.sklearn.log_model", "mlflow.register_model", "mlflow.pyfunc.load_model", "mlflow.search_runs"],
    "Feast": ["FeatureStore", "get_historical_features", "get_online_features", "apply", "materialize", "materialize_incremental", "plan", "push", "teardown", "serve"],
    "BentoML": ["bentoml.service", "bentoml.api", "bentoml.models.get", "bentoml.sklearn.save_model", "bentoml.picklable_model.save_model", "bentoml.server", "bentoml.batch", "bentoml.io.JSON", "bentoml.io.NumpyNdarray", "bentoml.monitor"],
    "Evidently": ["Report", "TestSuite", "DataDefinition", "ColumnMapping", "report.run", "report.save_html", "DriftedColumnsCount", "DataQualityPreset", "TargetDriftPreset", "RegressionPreset"],
    "SQLAlchemy": ["create_engine", "Session", "select", "insert", "update", "delete", "declarative_base", "relationship", "sessionmaker", "text"],
    "pymongo": ["MongoClient", "find", "find_one", "insert_one", "insert_many", "update_one", "delete_one", "aggregate", "create_index", "count_documents"],
    "Qiskit": ["QuantumCircuit", "transpile", "measure", "h", "cx", "x", "z", "AerSimulator", "execute", "Statevector"],
    "Cirq": ["Circuit", "LineQubit.range", "H", "CNOT", "measure", "Simulator", "rx", "rz", "PauliString", "DensityMatrixSimulator"],
    "PennyLane": ["qml.qnode", "qml.device", "qml.RX", "qml.RY", "qml.CNOT", "qml.expval", "qml.probs", "qml.StronglyEntanglingLayers", "qml.AmplitudeEmbedding", "qml.grad"],
    "Qiskit Machine Learning": ["QSVC", "VQC", "EstimatorQNN", "SamplerQNN", "NeuralNetworkClassifier", "NeuralNetworkRegressor", "FidelityQuantumKernel", "TorchConnector", "PegasosQSVC", "QGAN"],
    "Qiskit Algorithms": ["VQE", "QAOA", "NumPyMinimumEigensolver", "SamplingVQE", "PhaseEstimation", "Grover", "AmplificationProblem", "IterativePhaseEstimation", "HamiltonianPhaseEstimation", "AlgorithmJob"],
    "D-Wave Ocean": ["EmbeddingComposite", "DWaveSampler", "BinaryQuadraticModel", "sample_ising", "sample_qubo", "FixedEmbeddingComposite", "LeapHybridSampler", "SimulatedAnnealingSampler", "dimod.ExactSolver", "dwave.inspector.show"],
    "Qiskit Runtime": ["Sampler", "Estimator", "Session", "Options", "QiskitRuntimeService", "Batch", "run", "backend", "transpile", "save_account"],
}

def get_library_function_catalog(lib_name, attrs):
    existing_catalog = list(LIBRARY_FUNCTION_CATALOG.get(lib_name, []))
    used_names = {entry.get("name") for entry in existing_catalog}

    for fn_name in attrs.get("functions", []):
        if fn_name not in used_names:
            existing_catalog.append(build_generic_function_entry(lib_name, fn_name))
            used_names.add(fn_name)

    for fn_name in LIBRARY_FUNCTION_FALLBACKS.get(lib_name, []):
        if fn_name not in used_names:
            existing_catalog.append(build_generic_function_entry(lib_name, fn_name))
            used_names.add(fn_name)
        if len(existing_catalog) >= MIN_FUNCTIONS_PER_LIBRARY:
            break

    if len(existing_catalog) < MIN_FUNCTIONS_PER_LIBRARY:
        generic_candidates = [
            "fit", "predict", "transform", "load", "save",
            "train", "evaluate", "plot", "run", "configure",
            "export", "from_pretrained", "compile", "forward", "step"
        ]
        for fn_name in generic_candidates:
            padded_name = fn_name if fn_name not in used_names else f"{lib_name}.{fn_name}"
            if padded_name not in used_names:
                existing_catalog.append(build_generic_function_entry(lib_name, padded_name))
                used_names.add(padded_name)
            if len(existing_catalog) >= MIN_FUNCTIONS_PER_LIBRARY:
                break

    return existing_catalog[:MIN_FUNCTIONS_PER_LIBRARY]

def build_generic_python_example(lib_name, fn_name):
    alias_map = {
        "NumPy": "np",
        "Matplotlib": "plt",
        "pandas": "pd",
        "PyTorch": "torch",
        "TensorFlow": "tf",
        "OpenCV": "cv2",
        "Plotly": "px",
        "Streamlit": "st",
        "FastAPI": "app",
        "Qiskit": "qc",
        "PennyLane": "qml",
    }

    patterns = {
        "read_csv": "import pandas as pd\ndf = pd.read_csv('data.csv')",
        "DataFrame": "import pandas as pd\ndf = pd.DataFrame({'x': [1, 2], 'y': [3, 4]})",
        "train_test_split": "from sklearn.model_selection import train_test_split\nX_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)",
        "fit_transform": "X_scaled = scaler.fit_transform(X_train)",
        "fit": "model.fit(X_train, y_train)",
        "predict_proba": "proba = model.predict_proba(X_test)",
        "predict": "y_pred = model.predict(X_test)",
        "score": "score = model.score(X_test, y_test)",
        "groupby": "summary = df.groupby('category').mean()",
        "merge": "merged = left_df.merge(right_df, on='id')",
        "pivot_table": "table = df.pivot_table(values='sales', index='region', columns='month')",
        "torch.randn": "import torch\nx = torch.randn(32, 128, requires_grad=True)",
        "torch.tensor": "import torch\nx = torch.tensor([[1.0, 2.0], [3.0, 4.0]])",
        "torch.zeros": "import torch\nmask = torch.zeros((4, 4))",
        "torch.ones": "import torch\nweights = torch.ones((2, 3))",
        "nn.Linear": "import torch.nn as nn\nlayer = nn.Linear(128, 64)",
        "optimizer.step": "optimizer.zero_grad()\nloss.backward()\noptimizer.step()",
        "tf.constant": "import tensorflow as tf\nx = tf.constant([[1.0, 2.0], [3.0, 4.0]])",
        "tf.Variable": "import tensorflow as tf\nw = tf.Variable(tf.random.normal([3, 3]))",
        "model.compile": "model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])",
        "model.fit": "history = model.fit(X_train, y_train, epochs=10, batch_size=32)",
        "model.evaluate": "loss, acc = model.evaluate(X_test, y_test)",
        "model.predict": "predictions = model.predict(X_new)",
        "Sequential": "from keras import Sequential\nmodel = Sequential()",
        "Dense": "from keras.layers import Dense\nlayer = Dense(64, activation='relu')",
        "Dropout": "from keras.layers import Dropout\nregularizer = Dropout(0.3)",
        "cv2.imread": "import cv2\nimage = cv2.imread('image.jpg')",
        "cv2.cvtColor": "gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)",
        "cv2.resize": "resized = cv2.resize(image, (224, 224))",
        "cv2.VideoCapture": "cap = cv2.VideoCapture(0)",
        "px.line": "import plotly.express as px\nfig = px.line(df, x='date', y='sales')",
        "px.scatter": "import plotly.express as px\nfig = px.scatter(df, x='x', y='y', color='class')",
        "plt.figure": "import matplotlib.pyplot as plt\nplt.figure(figsize=(8, 4))",
        "plt.show": "plt.tight_layout()\nplt.show()",
        "mlflow.start_run": "import mlflow\nwith mlflow.start_run():\n    mlflow.log_param('lr', 0.001)",
        "mlflow.log_metric": "mlflow.log_metric('f1_score', 0.91)",
        "create_engine": "from sqlalchemy import create_engine\nengine = create_engine('sqlite:///app.db')",
        "MongoClient": "from pymongo import MongoClient\nclient = MongoClient('mongodb://localhost:27017')",
        "QuantumCircuit": "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)",
        "qml.qnode": "import pennylane as qml\n@qml.qnode(dev)\ndef circuit(x):\n    return qml.expval(qml.Z(0))",
    }

    for key, code in patterns.items():
        if key in fn_name:
            return code

    alias = alias_map.get(lib_name, lib_name.lower().replace(' ', '_'))
    if '.' in fn_name:
        call = fn_name
    elif lib_name == 'FastAPI':
        call = f"{alias}.{fn_name}" if alias != 'app' else f"app.{fn_name}"
    else:
        call = f"{alias}.{fn_name}"

    import_line = ''
    if lib_name == 'FastAPI':
        import_line = 'from fastapi import FastAPI\napp = FastAPI()'
    elif alias in {'np', 'pd', 'plt', 'torch', 'tf', 'cv2', 'px', 'st', 'qml'}:
        module_map = {'np': 'numpy', 'pd': 'pandas', 'plt': 'matplotlib.pyplot', 'torch': 'torch', 'tf': 'tensorflow', 'cv2': 'cv2', 'px': 'plotly.express', 'st': 'streamlit', 'qml': 'pennylane'}
        import_line = f"import {module_map[alias]} as {alias}"
    return f"{import_line}\nresult = {call}(...)".strip()


def build_generic_function_entry(lib_name, fn_name):
    return {
        "name": fn_name,
        "description": f"{fn_name} es una función o componente clave dentro de {lib_name}.",
        "code": build_generic_python_example(lib_name, fn_name),
    }

def add_library_function_nodes(graph_nodes, graph_edges):
    new_nodes = dict(graph_nodes)
    new_edges = list(graph_edges)

    for lib_name, attrs in list(graph_nodes.items()):
        if attrs.get("kind") not in {"libreria", "framework"}:
            continue

        catalog = get_library_function_catalog(lib_name, attrs)

        for entry in catalog:
            fn_node_name = f"{lib_name} :: {entry['name']}"
            if fn_node_name not in new_nodes:
                new_nodes[fn_node_name] = make_node(
                    "funcion",
                    attrs.get("domain", "General"),
                    attrs.get("year"),
                    entry["description"],
                    size=9,
                    url=attrs.get("url"),
                    examples=[
                        tr("Uso típico dentro de la librería.", "Typical usage inside the library."),
                        tr("Se puede estudiar junto con el código de ejemplo del panel.", "It can be studied together with the code example in the panel."),
                        tr(f"Pertenece a {lib_name}.", f"Belongs to {lib_name}."),
                    ],
                    tags=merge_unique_list(attrs.get("tags", []), [fn_node_name]),
                    related_concepts=merge_unique_list(attrs.get("related_concepts", []), [lib_name]),
                    related_subareas=attrs.get("related_subareas", []),
                    code_example=entry.get("code"),
                    title_en=entry["description"],
                )
                new_nodes[fn_node_name]["label"] = entry["name"]
                new_nodes[fn_node_name]["label_en"] = entry["name"]
            edge = (canonical_name(lib_name), canonical_name(fn_node_name), "función")
            if edge not in new_edges:
                new_edges.append(edge)

    return new_nodes, new_edges

def add_similarity_cluster_edges(G):
    H = G.copy()
    grouped = defaultdict(list)
    for node_name, attrs in H.nodes(data=True):
        kind = attrs.get("kind")
        if kind not in {"libreria", "herramienta", "recurso", "dataset"}:
            continue
        for sub in attrs.get("related_subareas", []):
            grouped[(sub, kind)].append(node_name)

    for (_sub, _kind), items in grouped.items():
        items = sorted(set(items))
        for left, right in zip(items, items[1:]):
            if not H.has_edge(left, right):
                H.add_edge(left, right, relation="cluster", hidden=True, cluster=True)
    return H

# =========================================================
# Utilidades del grafo
# =========================================================

def render_python_code_html(code):
    code = (code or '').strip('\n')
    if not code:
        return ''

    styles = {
        'keyword': '#c92c2c',
        'name': '#1f6feb',
        'string': '#0a7f5a',
        'number': '#7c3aed',
        'comment': '#6b7280',
        'operator': '#111827',
        'punct': '#475569',
        'default': '#111827',
    }

    try:
        lines = code.splitlines(keepends=True)
        result = []
        last_row, last_col = 1, 0

        def append_plain(segment):
            if not segment:
                return
            result.append(
                html.escape(segment)
                .replace(' ', '&nbsp;')
                .replace('\t', '&nbsp;' * 4)
                .replace('\n', '<br>')
            )

        def slice_text(sr, sc, er, ec):
            if sr == er:
                return lines[sr - 1][sc:ec]
            chunks = [lines[sr - 1][sc:]]
            for row in range(sr, er - 1):
                chunks.append(lines[row])
            chunks.append(lines[er - 1][:ec])
            return ''.join(chunks)

        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            tok_type, tok_str, start_pos, end_pos, _ = tok
            append_plain(slice_text(last_row, last_col, start_pos[0], start_pos[1]))

            if tok_type == token.NAME and keyword.iskeyword(tok_str):
                color = styles['keyword']
            elif tok_type == token.NAME:
                color = styles['name']
            elif tok_type == token.STRING:
                color = styles['string']
            elif tok_type == token.NUMBER:
                color = styles['number']
            elif tok_type == tokenize.COMMENT:
                color = styles['comment']
            elif tok_type == token.OP:
                color = styles['operator'] if tok_str in {'=', '.', '(', ')', '[', ']', '{', '}', ',', ':'} else styles['punct']
            else:
                color = styles['default']

            styled = (html.escape(tok_str)
                .replace(' ', '&nbsp;')
                .replace('\t', '&nbsp;' * 4)
                .replace('\n', '<br>'))
            weight = '700' if tok_type == token.NAME and keyword.iskeyword(tok_str) else '500'
            result.append(f"<span style='color:{color};font-weight:{weight}'>{styled}</span>")
            last_row, last_col = end_pos

        append_plain(slice_text(last_row, last_col, len(lines), len(lines[-1]) if lines else 0))
        return ''.join(result)
    except Exception:
        return html.escape(code).replace('\n', '<br>').replace(' ', '&nbsp;')


def themed_badge(label, value, bg='#eef2ff', color='#1e3a8a'):
    if value in [None, '']:
        return ''
    return (
        f"<span style='display:inline-block;margin:0 6px 6px 0;padding:5px 10px;"
        f"border-radius:999px;background:{bg};color:{color};font-size:12px;"
        f"font-weight:700;border:1px solid rgba(0,0,0,0.06)'>"
        f"<span style='opacity:.8'>{html.escape(str(label))}:</span> {html.escape(str(value))}</span>"
    )


def format_rich_text_block(text_value):
    if not text_value:
        return ''
    paragraphs = [p.strip() for p in str(text_value).split('\n') if p.strip()]
    return ''.join(
        f"<div style='margin:0 0 8px 0;color:#334155;line-height:1.55'>{html.escape(p)}</div>"
        for p in paragraphs
    )


def build_examples_list(items, title_text):
    if not items:
        return ''
    rows = ''.join(
        f"<li style='margin:0 0 6px 0'><span style='color:#0f172a'>{html.escape(str(item))}</span></li>"
        for item in items
    )
    return (
        f"<div style='margin-top:10px'>"
        f"<div style='font-weight:800;color:#7c2d12;margin-bottom:6px'>{html.escape(title_text)}</div>"
        f"<ul style='margin:0;padding-left:18px;color:#334155'>{rows}</ul></div>"
    )


def build_functions_chips(functions, title_text):
    if not functions:
        return ''
    chips = ''.join(
        f"<span style='display:inline-block;margin:4px 6px 0 0;padding:4px 8px;border-radius:999px;background:#ecfeff;color:#155e75;border:1px solid #a5f3fc;font-size:12px;font-weight:700'>{html.escape(str(fn))}</span>"
        for fn in functions[:12]
    )
    return (
        f"<div style='margin-top:10px'>"
        f"<div style='font-weight:800;color:#0f766e;margin-bottom:4px'>{html.escape(title_text)}</div>{chips}</div>"
    )


def build_rich_card_html(name, attrs, compact=False):
    display_name = translate_name(attrs.get('label', name))
    domain = attrs.get('domain', 'General')
    accent = TYPE_COLOR_OVERRIDES.get(attrs.get('kind'), DOMAIN_COLORS.get(domain, DOMAIN_COLORS['General']))
    accent_text = '#1f2937'
    body_padding = '14px' if compact else '18px'
    radius = '14px' if compact else '16px'
    shadow = '0 8px 20px rgba(15,23,42,.12)' if compact else '0 14px 30px rgba(15,23,42,.14)'

    header = (
        f"<div style='display:flex;align-items:flex-start;justify-content:space-between;gap:10px'>"
        f"<div>"
        f"<div style='font-size:{'17px' if compact else '19px'};font-weight:900;color:{accent_text};margin-bottom:6px'>"
        f"{html.escape(display_name)}</div>"
        f"<div style='height:4px;width:68px;border-radius:999px;background:{accent};opacity:.95'></div>"
        f"</div></div>"
    )

    badges = ''.join([
        themed_badge(tr('Tipo', 'Type'), translate_kind(attrs['kind']) if attrs.get('kind') else '', '#eff6ff', '#1d4ed8') if attrs.get('kind') else '',
        themed_badge(tr('Dominio', 'Domain'), translate_name(attrs['domain']) if attrs.get('domain') else '', '#fff7ed', '#c2410c') if attrs.get('domain') else '',
        themed_badge(tr('Año', 'Year'), attrs.get('year'), '#f5f3ff', '#6d28d9') if attrs.get('year') else '',
    ])

    title_value = node_title(attrs)
    related_subareas = attrs.get('related_subareas', [])
    related_concepts = attrs.get('related_concepts', [])
    related_subareas_html = ''
    if related_subareas:
        related_subareas_html = build_functions_chips([translate_name(v) for v in related_subareas], tr('Subáreas relacionadas', 'Related subareas'))
    related_concepts_html = ''
    if related_concepts:
        related_concepts_html = build_functions_chips([translate_name(v) for v in related_concepts], tr('Conceptos relacionados', 'Related concepts'))

    code_html = ''
    if attrs.get('code_example'):
        code_html = (
            f"<div style='margin-top:12px'>"
            f"<div style='font-weight:800;color:#1d4ed8;margin-bottom:6px'>{html.escape(tr('Ejemplo de código', 'Code example'))}</div>"
            f"<div style='background:#0f172a;border:1px solid #1e293b;border-radius:12px;overflow:auto'>"
            f"<div style='display:flex;gap:6px;padding:8px 10px;border-bottom:1px solid #1e293b;background:#111827'>"
            f"<span style='width:10px;height:10px;border-radius:999px;background:#f87171;display:inline-block'></span>"
            f"<span style='width:10px;height:10px;border-radius:999px;background:#fbbf24;display:inline-block'></span>"
            f"<span style='width:10px;height:10px;border-radius:999px;background:#34d399;display:inline-block'></span>"
            f"<span style='margin-left:8px;font-size:12px;color:#93c5fd;font-weight:700'>Python</span>"
            f"</div>"
            f"<div style='padding:12px 14px;font-family:Consolas, Monaco, monospace;font-size:13px;line-height:1.6;color:#e5e7eb'>{render_python_code_html(attrs['code_example'])}</div>"
            f"</div></div>"
        )

    link_html = ''
    if attrs.get('url'):
        url = html.escape(attrs['url'])
        link_html = f"<div style='margin-top:12px'><a href='{url}' target='_blank' rel='noopener noreferrer' style='color:#2563eb;font-weight:800;text-decoration:none'>{html.escape(tr('Ver más / profundizar en el tema', 'Learn more / go deeper'))} ↗</a></div>"

    max_width = '420px' if compact else '100%'

    return (
        f"<div style='max-width:{max_width};background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);"
        f"border:1px solid #e2e8f0;border-radius:{radius};padding:{body_padding};box-shadow:{shadow};"
        f"font-family:Inter,Segoe UI,Arial,sans-serif;color:#0f172a'>"
        f"{header}"
        f"<div style='margin-top:12px'>{badges}</div>"
        f"<div style='margin-top:10px'>{format_rich_text_block(title_value)}</div>"
        f"{build_examples_list(attrs.get('examples', []), tr('Ejemplos o usos típicos', 'Examples or common uses'))}"
        f"{build_functions_chips(attrs.get('functions', []), tr('Funciones principales', 'Main functions'))}"
        f"{related_subareas_html}"
        f"{related_concepts_html}"
        f"{code_html}"
        f"{link_html}"
        f"</div>"
    )


def enrich_title(name, attrs):
    return build_rich_card_html(name, attrs, compact=True)


def build_detail_html(name, attrs):
    return build_rich_card_html(name, attrs, compact=False)

def build_graph(graph_nodes, graph_edges):
    G = nx.Graph()
    for name, attrs in graph_nodes.items():
        attrs = dict(attrs)
        attrs["full_title"] = enrich_title(name, attrs)
        attrs["detail_html"] = build_detail_html(name, attrs)
        if IS_EN and attrs.get("label_en"):
            attrs["label"] = attrs.get("label_en")
        else:
            attrs["label"] = translate_name(attrs.get("label", name))
        G.add_node(name, **attrs)
    for src, dst, rel in graph_edges:
        if src in graph_nodes and dst in graph_nodes:
            G.add_edge(src, dst, relation=rel)
    return G

def filter_graph(G, selected_kinds, selected_domains, selected_subareas=None):
    H = G.copy()
    remove_nodes = []
    selected_kinds_set = set(selected_kinds or [])
    selected_domains_set = set(selected_domains or [])
    selected_subareas_set = set(selected_subareas or [])

    for n, attrs in H.nodes(data=True):
        node_kind = attrs.get("kind")
        if node_kind == "contenedor":
            bucket_kind = attrs.get("bucket_kind")
            if selected_kinds_set and bucket_kind and bucket_kind not in selected_kinds_set:
                remove_nodes.append(n)
                continue
        elif selected_kinds_set and node_kind not in selected_kinds_set:
            remove_nodes.append(n)
            continue

        if selected_domains_set and attrs.get("domain") not in selected_domains_set:
            remove_nodes.append(n)
            continue

        if selected_subareas_set:
            rel_subareas = set(attrs.get("related_subareas", []))
            if attrs.get("kind") != "principal" and not rel_subareas.intersection(selected_subareas_set):
                remove_nodes.append(n)
                continue

    H.remove_nodes_from(remove_nodes)

    empty_containers = [
        n for n, attrs in H.nodes(data=True)
        if attrs.get("kind") == "contenedor" and H.degree(n) <= 1
    ]
    H.remove_nodes_from(empty_containers)
    return H

def create_timeline_df(graph_nodes):
    rows = []
    for name, attrs in graph_nodes.items():
        year = attrs.get("year")
        if year is None:
            continue
        rows.append({
            "Concepto": translate_name(name),
            "Tipo": translate_kind(attrs.get("kind", "")),
            "Dominio": translate_name(attrs.get("domain", "")),
            "Año": year,
            "Descripción": node_title(attrs),
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

    detail_panel = f"""
<div id="selected-node-panel" style="margin-top:16px;padding:14px;border:1px solid #ddd;border-radius:12px;background:#fafafa;font-family:Arial, sans-serif;">
  <div style="font-weight:700;margin-bottom:8px;">{tr('Detalle del nodo', 'Node details')}</div>
  <div id="selected-node-content" style="color:#333;">{tr('Haz click sobre un nodo para ver aquí su descripción ampliada, usos, funciones principales y enlaces. Haz doble click para abrir el recurso principal del nodo.', 'Click a node to see its detailed description, uses, key functions and links here. Double click to open the main node resource.')}</div>
</div>
"""

    js = """
<script type="text/javascript">
function waitForNetwork() {
  if (typeof network === "undefined" || typeof nodes === "undefined") {
    setTimeout(waitForNetwork, 500);
    return;
  }

  function setPanel(contentHtml) {
    const panel = document.getElementById("selected-node-content");
    if (panel) {
      panel.innerHTML = contentHtml;
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

  network.on("doubleClick", function(params) {
    if (!params.nodes || params.nodes.length === 0) return;
    const nodeId = params.nodes[0];
    const node = nodes.get(nodeId);
    if (node && node.url) {
      window.open(node.url, "_blank");
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
        label = attrs.get("label", translate_name(name))
        if show_year_in_label and attrs.get("year"):
            label = f"{translate_name(name)} ({attrs['year']})"
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
        src_kind = G.nodes[src].get("kind") if src in G.nodes else ""
        dst_kind = G.nodes[dst].get("kind") if dst in G.nodes else ""
        edge_kwargs = {"title": title}
        if src_kind == "contenedor" or dst_kind == "contenedor":
            edge_kwargs.update({"width": 2.0, "color": "#343a40", "arrows": "to"})
        elif src_kind == "libreria" and dst_kind == "funcion":
            edge_kwargs.update({"width": 2.0, "color": "#495057", "arrows": "to", "length": 140})
        if edge_attrs.get("hidden"):
            net.add_edge(src, dst, hidden=True, physics=True, color="rgba(0,0,0,0)", **edge_kwargs)
        else:
            net.add_edge(src, dst, **edge_kwargs)

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
graph_nodes, graph_edges = add_library_function_nodes(graph_nodes, graph_edges)

G_full = build_graph(graph_nodes, graph_edges)
G_full = add_similarity_cluster_edges(G_full)

all_domains = sorted({attrs.get("domain", "General") for attrs in graph_nodes.values()})
all_kinds = sorted({attrs.get("kind", "concepto") for attrs in graph_nodes.values()})
legend_kinds = [k for k in all_kinds if k != "principal"]

all_subareas = sorted({
    n for n, attrs in graph_nodes.items()
    if attrs.get("kind") == "subarea"
})

filter_row = st.columns([1.15, 1.5, 1.5, 1.9], gap="medium")
with filter_row[0]:
    st.caption(tr("Exploración", "Exploration"))
with filter_row[1]:
    selected_domains = st.multiselect(
        tr("Filtrar por dominio", "Filter by domain"),
        all_domains,
        default=[],
        format_func=lambda v: translate_name(v),
        key="top_filter_domains",
    )
with filter_row[2]:
    selected_subareas = st.multiselect(
        tr("Filtrar por subárea", "Filter by subarea"),
        all_subareas,
        default=[],
        format_func=lambda v: translate_name(v),
        key="top_filter_subareas",
    )
with filter_row[3]:
    selected_kinds = st.multiselect(
        tr("Filtrar por tipo", "Filter by type"),
        all_kinds,
        default=[k for k in ["principal", "concepto", "subarea"] if k in all_kinds],
        format_func=lambda v: translate_kind(v),
        key="top_filter_kinds",
    )

G_filtered = filter_graph(G_full, selected_kinds, selected_domains, selected_subareas)

# =========================================================
# Layout principal
# =========================================================
if show_right_panel:
    left_col, toggle_col, right_col = st.columns([4.3, 0.22, 1.25], gap="small")
else:
    left_col, toggle_col = st.columns([1.0, 0.055], gap="small")
    right_col = None

with toggle_col:
    st.markdown("<div style='padding-top:3.2rem'></div>", unsafe_allow_html=True)
    arrow_label = "❮" if show_right_panel else "❯"
    if st.button(arrow_label, key="toggle_right_panel_arrow", help=tr("Mostrar u ocultar panel derecho", "Show or hide right panel"), use_container_width=True):
        st.session_state.show_right_panel = not show_right_panel
        st.rerun()

with left_col:
    st.subheader(tr("Mapa visual", "Visual map"))
    st.caption(
        f"{tr('Nodos mostrados', 'Displayed nodes')}: {len(G_filtered.nodes)} | "
        f"{tr('Relaciones', 'Relations')}: {len(G_filtered.edges)}"
    )
    render_graph(G_filtered)

if show_right_panel and right_col is not None:
    with right_col:
        st.subheader(tr("Exploración rápida", "Quick exploration"))

        st.markdown("**" + tr("Perfil", "Profile") + "**")
        if LINKEDIN_IMAGE_URL:
            st.image(LINKEDIN_IMAGE_URL, width=84)
        else:
            st.markdown(
                "<div style='width:84px;height:84px;border-radius:50%;background:#0A66C2;color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:28px;'>AT</div>",
                unsafe_allow_html=True,
            )
        st.markdown(f"**[{LINKEDIN_DISPLAY_NAME}]({LINKEDIN_URL})**")
        st.markdown(f"- [LinkedIn]({LINKEDIN_URL})")
        st.markdown(f"- [GitHub]({GITHUB_URL})")

        st.markdown("---")
        st.markdown("**" + tr("Leyenda de tipos", "Node type legend") + "**")
        for kind in legend_kinds:
            if kind in KIND_STYLES:
                st.markdown(f"- **{translate_kind(kind)}** → {KIND_STYLES[kind]['shape']}")

        st.markdown("---")
        st.markdown("**" + tr("Dominios principales", "Main domains") + "**")
        for name, _, _ in MAIN_DOMAINS:
            st.markdown(f"- `{translate_name(name)}`")

        st.markdown("---")
        st.info(tr(
            "El detalle ampliado aparece debajo del mapa al hacer click en un nodo. El tooltip corto sigue disponible al pasar el mouse y el doble click abre el recurso principal si existe.",
            "The detailed panel appears below the map when you click a node. A short tooltip remains on hover and double click opens the main resource when available."
        ))

        st.markdown("---")
        st.markdown("**" + tr("Submapas sugeridos", "Suggested submaps") + "**")
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
            "Computación Cuántica",
        ]
        for s in suggested:
            st.markdown(f"- `{translate_name(s)}`")

# =========================================================
# Línea de tiempo
# =========================================================
if show_timeline:
    st.markdown("---")
    st.subheader(tr("Línea de tiempo", "Timeline"))

    visible_names = set(G_filtered.nodes)
    timeline_source_nodes = {k: v for k, v in graph_nodes.items() if k in visible_names}

    timeline_df = create_timeline_df(timeline_source_nodes)

    if timeline_df.empty:
        st.warning(tr("No hay datos suficientes para mostrar la línea de tiempo.", "There is not enough data to show the timeline."))
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

        with st.expander(tr("Ver tabla cronológica", "View chronological table")):
            st.dataframe(timeline_df, use_container_width=True)

# =========================================================
# Tabla resumen
# =========================================================
st.markdown("---")
st.subheader(tr("Resumen tabular del submapa", "Submap table summary"))

summary_rows = []
for node_name in G_filtered.nodes:
    node_data = G_filtered.nodes[node_name]
    summary_rows.append({
        "Nombre": translate_name(node_name),
        "Tipo": translate_kind(node_data.get("kind", "")),
        "Dominio": translate_name(node_data.get("domain", "")),
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
st.caption("Sugerencia: activa tipos como libreria, herramienta, recurso o dataset para ver cómo se conectan directamente con cada concepto.")
