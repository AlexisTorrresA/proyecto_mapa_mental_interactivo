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
- **Responsible AI**: evita que la IA haga tonteras elegantes pero peligrosas.
""")
