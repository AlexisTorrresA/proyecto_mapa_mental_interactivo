"""Atlas IA: jerarquía navegable y relaciones semánticas.

Un único concepto puede tener muchos vínculos transversales, pero solo un
lugar principal en el árbol. El estilo del enlace explica la diferencia.
"""
from __future__ import annotations

import html
import json
from collections import Counter
from urllib.parse import urlparse

import networkx as nx
from pyvis.network import Network
import streamlit as st
import streamlit.components.v1 as components

from knowledge_taxonomy import (
    analyze_graph, semantic_neighborhood, semantic_path, HIERARCHY_RELATIONS,
)

ROLE_STYLE = {
    "raíz": ("#fbbf24", "star", "✦", "Mapa general"),
    "dominio": ("#f59e0b", "ellipse", "◉", "Dominio"),
    "área": ("#8b5cf6", "box", "▣", "Área"),
    "grupo": ("#6366f1", "box", "▦", "Grupo temático"),
    "paradigma": ("#38bdf8", "diamond", "◆", "Paradigma"),
    "tarea": ("#22d3ee", "box", "▤", "Tarea"),
    "métrica": ("#34d399", "hexagon", "⬢", "Métrica"),
    "problema": ("#fb7185", "triangle", "▲", "Riesgo o problema"),
    "técnica": ("#c4b5fd", "dot", "●", "Técnica"),
    "modelo": ("#fdba74", "dot", "●", "Modelo"),
    "algoritmo": ("#fdba74", "dot", "●", "Algoritmo"),
    "proceso": ("#2dd4bf", "dot", "●", "Proceso"),
    "concepto": ("#94a3b8", "dot", "●", "Concepto"),
    "herramienta": ("#6ee7b7", "dot", "🛠", "Herramienta"),
    "libreria": ("#6ee7b7", "dot", "⚙", "Librería"),
    "dataset": ("#f9a8d4", "database", "▤", "Dataset"),
    "recurso": ("#bef264", "dot", "↗", "Recurso"),
    "contenedor": ("#64748b", "box", "▥", "Contenedor"),
}

def role_of(attrs: dict) -> str:
    role = attrs.get("semantic_role")
    if role in ROLE_STYLE:
        return role
    kind = attrs.get("kind")
    if kind == "principal":
        return "dominio"
    if kind == "subarea":
        return "área"
    return kind if kind in ROLE_STYLE else "concepto"


def safe_link(url: str | None) -> str | None:
    if not isinstance(url, str):
        return None
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        return None
    return url.strip()


def visible_subgraph(nodes: dict, edges: list, focus: str | None, depth: int, limit: int = 180):
    """Backward-compatible general network helper."""
    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    for src, dst, *_ in edges:
        if src in nodes and dst in nodes and src != dst:
            graph.add_edge(src, dst)
    if not nodes:
        return {}, []
    focus = focus if focus in nodes else next(iter(nodes))
    distances = nx.single_source_shortest_path_length(graph, focus, cutoff=depth)
    kept = sorted(distances, key=lambda key: (distances[key], str(nodes[key].get("label") or key)))[:limit]
    keep_set = set(kept)
    selected_edges = [edge for edge in edges if edge[0] in keep_set and edge[1] in keep_set]
    return {key: nodes[key] for key in kept}, selected_edges


def render_graph(nodes: dict, edges: list, focus: str | None,
                 height: int = 690, semantic_links: bool = False) -> None:
    """Vis.js: solid hierarchy vs dotted transverse semantic association."""
    graph = Network(height=f"{height}px", width="100%", bgcolor="#0b1020", font_color="#f1f5f9",
                    directed=True, cdn_resources="in_line")
    for key, attrs in nodes.items():
        color, shape, symbol, _ = ROLE_STYLE[role_of(attrs)]
        name = str(attrs.get("label") or key)
        desc = str(attrs.get("title") or "Ver ficha del concepto")
        title = html.escape(name) + " · " + html.escape(role_of(attrs)) + "\n" + html.escape(desc[:280])
        graph.add_node(
            key, label=name[:36] + ("…" if len(name) > 36 else ""),
            title=title, color={"background": color, "border": "#e2e8f0" if key == focus else color,
                                "highlight": {"background": "#ffffff", "border": color}},
            font={"color": "#f8fafc", "size": 14, "strokeWidth": 5,
                  "strokeColor": "#0b1020", "face": "Arial"},
            shape=shape, size=34 if key == focus else (23 if role_of(attrs) in ("grupo", "paradigma", "dominio") else 17),
            borderWidth=4 if key == focus else 1, mass=2 if key == focus else 1,
        )
    for src, dst, relation, *_ in edges:
        if src not in nodes or dst not in nodes:
            continue
        taxonomy = relation in HIERARCHY_RELATIONS
        graph.add_edge(
            src, dst, title=html.escape(str(relation)), arrows="to",
            label="" if taxonomy else str(relation)[:28],
            dashes=not taxonomy, color="#64748b" if taxonomy else "#fb923c",
            width=1.6 if taxonomy else 1.2,
            font={"color": "#fed7aa", "strokeWidth": 3, "strokeColor": "#0b1020",
                  "size": 10, "align": "middle"},
            selectionWidth=3,
        )
    if semantic_links:
        config = {
            "interaction": {"hover": True, "navigationButtons": True, "keyboard": True,
                            "tooltipDelay": 150},
            "physics": {"enabled": True, "stabilization": {"iterations": 145},
                        "barnesHut": {"gravitationalConstant": -8500,
                                     "centralGravity": 0.08, "springLength": 210}},
            "edges": {"smooth": {"enabled": True, "type": "continuous"}},
        }
    else:
        config = {
            "interaction": {"hover": True, "navigationButtons": True, "keyboard": True,
                            "tooltipDelay": 150},
            "layout": {"hierarchical": {"enabled": True, "direction": "LR",
                                        "sortMethod": "directed",
                                        "levelSeparation": 205, "nodeSpacing": 125,
                                        "treeSpacing": 215}},
            "physics": {"enabled": False},
            "edges": {"smooth": {"enabled": True, "type": "cubicBezier",
                                 "forceDirection": "horizontal", "roundness": 0.32}},
        }
    graph.set_options(json.dumps(config))
    components.html(graph.generate_html(), height=height + 12, scrolling=False)


def _navigate(key: str):
    st.session_state["atlas_go_to"] = key
    st.rerun()


def _related(key: str, edges: list, nodes: dict):
    subtopics, parents, relations = [], [], []
    for src, dst, relation, *_ in edges:
        if src not in nodes or dst not in nodes:
            continue
        if relation in HIERARCHY_RELATIONS:
            if src == key:
                subtopics.append(dst)
            if dst == key:
                parents.append(src)
        elif src == key:
            relations.append((relation, dst, "saliente"))
        elif dst == key:
            relations.append((relation, src, "entrante"))
    return sorted(set(subtopics)), sorted(set(parents)), relations


def _topic_buttons(keys: list[str], nodes: dict, prefix: str, limit: int = 20):
    if not keys:
        return
    for i in range(0, min(len(keys), limit), 2):
        cols = st.columns(2)
        for j, key in enumerate(keys[i:i+2]):
            kind = role_of(nodes[key])
            symbol = ROLE_STYLE[kind][2]
            label = f"{symbol} {nodes[key].get('label') or key}"
            with cols[j]:
                if st.button(label, key=f"{prefix}_{key}", use_container_width=True):
                    _navigate(key)
    if len(keys) > limit:
        st.caption(f"Hay {len(keys) - limit} vínculos adicionales. Usa el buscador para encontrarlos.")


def render_detail(key: str, attrs: dict, nodes: dict, edges: list) -> None:
    role = role_of(attrs)
    color, shape, symbol, role_name = ROLE_STYLE[role]
    st.markdown(f"### {symbol} {attrs.get('label') or key}")
    st.caption(f"{role_name} · {attrs.get('domain') or 'Conocimiento'}" +
               (f" · {attrs['year']}" if attrs.get("year") else ""))
    st.write(attrs.get("title") or "La ficha necesita una descripción.")
    trail = [k for k in semantic_path(key, edges) if k in nodes]
    if len(trail) > 1:
        st.markdown("**Ruta principal**")
        st.caption("  ›  ".join(str(nodes[k].get("label") or k) for k in trail))
    subtopics, parents, relations = _related(key, edges, nodes)
    if parents:
        st.markdown("**Pertenece a**")
        _topic_buttons(parents, nodes, f"parent_{key}", 6)
    if subtopics:
        st.markdown(f"**Subtemas ({len(subtopics)})**")
        _topic_buttons(subtopics, nodes, f"child_{key}", 20)
    if relations:
        st.markdown(f"**Conexiones transversales ({len(relations)})**")
        st.caption("Estos vínculos no cambian el padre principal ni crean duplicados.")
        for i, (relation, other, direction) in enumerate(relations[:24]):
            context = relation if direction == "saliente" else "recibe: " + relation
            label = f"↔ {context} · {nodes[other].get('label') or other}"
            if st.button(label, key=f"edge_{key}_{i}", use_container_width=True):
                _navigate(other)
        if len(relations) > 24:
            st.caption("Más conexiones disponibles desde el buscador.")
    if attrs.get("examples"):
        with st.expander("Ejemplos", expanded=False):
            for example in attrs["examples"]:
                st.markdown(f"- {example}")
    if attrs.get("functions"):
        with st.expander("Funciones y aplicaciones", expanded=False):
            for item in attrs["functions"]:
                st.markdown(f"- {item}")
    if attrs.get("code_example"):
        with st.expander("Código Python", expanded=False):
            st.code(str(attrs["code_example"]), language="python")
    links = [(name, safe_link(attrs.get(field))) for name, field in [
        ("Referencia", "url"), ("GitHub", "github_url"),
        ("Notebook", "notebook_url"), ("Artículo", "article_url"),
    ]]
    for name, link in links:
        if link:
            st.link_button(name, link, use_container_width=True)


def render_atlas(nodes: dict, edges: list):
    st.title("✦ Atlas IA — mapa de conocimiento")
    st.caption("Navega de lo general a lo específico. Las líneas continuas representan jerarquía; "
               "las punteadas, asociaciones entre temas.")
    if not nodes:
        st.info("No existen conceptos disponibles.")
        return
    current_domains = ["Inteligencia Artificial", "Ingeniería de Software",
                       "Cloud Computing", "Ciberseguridad", "Robótica e IoT",
                       "Computación Cuántica"]
    domains = ["Todas"] + [x for x in current_domains if any(
        x == a.get("domain") for a in nodes.values())]
    default_area = domains.index("Inteligencia Artificial") if "Inteligencia Artificial" in domains else 0
    top = st.columns([1.25, 2.3])
    with top[0]:
        area = st.selectbox("Dominio", domains, index=default_area, key="atlas_domain")
    with top[1]:
        mode = st.radio("Visualización", ["Didáctico", "Jerarquía", "Relaciones"],
                        horizontal=True, key="atlas_mode")
    if mode == "Didáctico" and area == "Inteligencia Artificial":
        from atlas_didactic import render_didactic
        st.caption("Vista tipo ficha de estudio. Pulsa un rectángulo o círculo para abrir sus conexiones y definición. "
                   "Para ver todo el grafo utiliza Jerarquía o Relaciones.")
        render_didactic(nodes, edges)
        return
    if mode == "Didáctico":
        st.info("La ficha didáctica está preparada para Machine Learning. "
                "Aquí se presenta la jerarquía del dominio seleccionado.")
        mode = "Jerarquía"
    settings = st.columns(2)
    with settings[0]:
        depth = st.slider("Niveles de proximidad", 1, 4, 2, key="atlas_depth")
    with settings[1]:
        limit = st.slider("Límite de nodos", 15, 160, 65, step=5, key="atlas_limit")
    hide_assets = not st.toggle("Mostrar también herramientas, librerías, recursos y datasets",
                                 value=False, key="atlas_assets")

    candidates = [k for k, a in nodes.items() if (
        area == "Todas" or a.get("domain") == area or k == "Atlas del conocimiento"
    ) and (not hide_assets or a.get("kind") not in
           {"herramienta", "libreria", "recurso", "dataset", "contenedor"})]
    needle = st.text_input("Buscar concepto por nombre o descripción", key="atlas_search",
                           placeholder="Ej.: supervisado, precisión, regularización, redes neuronales…").casefold().strip()
    if needle:
        found = [k for k in candidates if needle in
                 (str(nodes[k].get("label") or k) + " " + str(nodes[k].get("title") or "")).casefold()]
        if not found:
            st.info("No hay coincidencias con este dominio y tipo de elemento.")
            return
        candidates = found
    candidates = sorted(candidates, key=lambda k: str(nodes[k].get("label") or k).casefold())

    default = ("Machine Learning" if area == "Inteligencia Artificial" and "Machine Learning" in candidates
               else "Atlas del conocimiento" if "Atlas del conocimiento" in candidates
               else candidates[0])
    go_to = st.session_state.pop("atlas_go_to", None)
    if go_to in candidates:
        st.session_state["atlas_focus_picker"] = go_to
    elif st.session_state.get("atlas_focus_picker") not in candidates:
        st.session_state["atlas_focus_picker"] = default

    selected = st.selectbox("Explorar concepto central", candidates,
                            format_func=lambda k: str(nodes[k].get("label") or k),
                            key="atlas_focus_picker")
    visible, filtered_edges = semantic_neighborhood(
        nodes, edges, selected, depth=depth, limit=limit,
        cross=(mode == "Relaciones"), assets=not hide_assets,
    )
    # Restrict graph to chosen domain unless browsing the global index.
    if area != "Todas":
        allowed = {k for k, a in visible.items()
                   if a.get("domain") == area or k == "Atlas del conocimiento"}
        visible = {k: v for k, v in visible.items() if k in allowed}
        filtered_edges = [e for e in filtered_edges if e[0] in visible and e[1] in visible]

    stats = st.columns(3)
    stats[0].metric("Nodos visibles", len(visible))
    stats[1].metric("Jerarquías", sum(e[2] in HIERARCHY_RELATIONS for e in filtered_edges))
    stats[2].metric("Asociaciones", sum(e[2] not in HIERARCHY_RELATIONS for e in filtered_edges))
    st.caption("**Formas:** ◆ paradigmas · ▤ tareas · ⬢ métricas · ▲ problemas · "
               "● técnicas/modelos. **Líneas:** sólida = contiene · punteada = se relaciona con.")
    left, right = st.columns([3.4, 1.35], gap="medium")
    with left:
        render_graph(visible, filtered_edges, selected, height=680, semantic_links=(mode == "Relaciones"))
        st.caption("Arrastra el mapa o usa zoom. Para cambiar el tema central, usa las fichas del panel "
                   "o el selector superior. En Relaciones aparecen enlaces transversales punteados.")
    with right:
        render_detail(selected, nodes[selected], nodes, edges)
    with st.expander("Leyenda completa de tipos y relaciones"):
        legend = [
            ("✦", "Raíz", "#fbbf24"), ("◉", "Dominio", "#f59e0b"),
            ("▣", "Área", "#8b5cf6"), ("▦", "Grupo", "#6366f1"),
            ("◆", "Paradigma", "#38bdf8"), ("▤", "Tarea", "#22d3ee"),
            ("⬢", "Métrica", "#34d399"), ("▲", "Problema", "#fb7185"),
            ("●", "Técnica", "#c4b5fd"), ("●", "Modelo", "#fdba74"),
        ]
        for symbol, label, color in legend:
            st.markdown(f"<span style='color:{color};font-weight:700'>{html.escape(symbol)}</span> {label}",
                        unsafe_allow_html=True)
        st.caption("Una métrica puede evaluar una tarea; una técnica puede mitigar un problema; "
                   "un riesgo puede afectar varios paradigmas. Ninguno de esos vínculos crea otro padre.")
    with st.expander("Auditoría del grafo"):
        report = analyze_graph(nodes, edges)
        st.write(f"{report['nodes']} nodos · {report['edges']} relaciones · "
                 f"{report['components']} componentes conectados · "
                 f"{len(report['isolated'])} conceptos sin enlaces.")
        if report["isolated"]:
            st.caption("Sin conexiones: " + ", ".join(report["isolated"][:20]))
        st.json(report["relations"])


def render_full_atlas(nodes: dict, edges: list, graph_store=None) -> None:
    from catalog_store import CatalogStore
    from catalog_ui import library_panel, model_panel, summary_panel

    catalog = None
    if graph_store is not None:
        try:
            catalog = CatalogStore(graph_store.engine)
            catalog.init_schema()
            catalog.seed()
        except Exception as exc:
            st.warning(f"No se pudo abrir el catálogo PostgreSQL ({type(exc).__name__}).")
    tabs = st.tabs(["🧠 Mapa de conceptos", "🐍 Glosario Python",
                    "🤗 Modelos Hugging Face", "📊 Estadísticas"])
    with tabs[0]:
        render_atlas(nodes, edges)
    with tabs[1]:
        library_panel(catalog)
    with tabs[2]:
        model_panel(catalog)
    with tabs[3]:
        summary_panel(catalog)
