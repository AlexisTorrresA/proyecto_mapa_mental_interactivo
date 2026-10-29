"""Vista experimental de atlas IA: navegación exploratoria y fichas educativas.

Se integra con las tablas PostgreSQL existentes sin alterar ni sobreescribir datos.
"""
from __future__ import annotations

import html
import json
from collections import defaultdict, deque
from urllib.parse import urlparse

import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
from pyvis.network import Network


def safe_link(url: str | None) -> str | None:
    """Solo enlaces web seguros, nunca javascript: ni data:."""
    if not isinstance(url, str):
        return None
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        return None
    return url.strip()


def visible_subgraph(nodes: dict, edges: list, focus: str | None, depth: int, limit: int = 180):
    """Reduce el número de nodos renderizados para mantener la fluidez."""
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


def render_graph(nodes: dict, edges: list, focus: str | None, height: int = 680) -> None:
    """Lienzo oscuro con enfoque, física moderada y tooltip legible."""
    colors = {
        "principal": "#f59e0b", "subarea": "#8b5cf6", "concepto": "#38bdf8",
        "herramienta": "#34d399", "framework": "#fb7185", "libreria": "#34d399",
        "dataset": "#f472b6", "recurso": "#a3e635",
    }
    graph = Network(height=f"{height}px", width="100%", bgcolor="#0b1020", font_color="#f8fafc",
                    directed=False, cdn_resources="in_line")
    for key, attrs in nodes.items():
        name = str(attrs.get("label") or key)
        desc = str(attrs.get("title") or "Explora este concepto")
        graph.add_node(key, label=name[:43], title=html.escape(desc[:300]),
                       color=colors.get(attrs.get("kind"), "#94a3b8"),
                       size=28 if key == focus else min(25, max(12, int(float(attrs.get("size") or 12)))),
                       borderWidth=3 if key == focus else 1, shape="dot")
    for edge in edges:
        src, dst = edge[0], edge[1]
        if src in nodes and dst in nodes:
            graph.add_edge(src, dst, color="#445375", width=1.2)
    graph.set_options(json.dumps({
        "interaction": {"hover": True, "navigationButtons": True, "keyboard": True, "tooltipDelay": 100},
        "physics": {"enabled": True, "stabilization": {"iterations": 110},
                    "barnesHut": {"gravitationalConstant": -6500, "springLength": 165, "springConstant": 0.035}},
        "nodes": {"font": {"face": "Inter,Arial", "size": 16, "strokeWidth": 3, "strokeColor": "#0b1020"}},
        "edges": {"smooth": {"type": "continuous"}, "color": {"inherit": False}}
    }))
    components.html(graph.generate_html(), height=height + 12, scrolling=False)


def render_detail(key: str, attrs: dict, related: list[str], nodes: dict) -> None:
    st.subheader(str(attrs.get("label") or key))
    st.caption(f"{attrs.get('domain') or 'IA'} · {attrs.get('kind') or 'concepto'}" +
               (f" · {attrs['year']}" if attrs.get("year") else ""))
    description = attrs.get("title") or "Este concepto todavía necesita una definición."
    st.markdown(str(description))
    if attrs.get("examples"):
        with st.expander("Ejemplos", expanded=True):
            for example in attrs["examples"]:
                st.markdown(f"• {example}")
    if attrs.get("functions"):
        with st.expander("Funciones y aplicaciones"):
            for item in attrs["functions"]:
                st.markdown(f"• {item}")
    if attrs.get("code_example"):
        with st.expander("Código Python", expanded=True):
            st.code(str(attrs["code_example"]), language="python")
    st.markdown("**Enlaces y recursos**")
    links = [("Referencia", attrs.get("url")), ("GitHub", attrs.get("github_url")),
             ("Notebook", attrs.get("notebook_url")), ("Artículo", attrs.get("article_url"))]
    links += [(str(item.get("title") or "Recurso"), item.get("url"))
              for item in (attrs.get("resources") or []) if isinstance(item, dict)]
    found = False
    for label, raw_url in links:
        url = safe_link(raw_url)
        if url:
            st.link_button(label, url, use_container_width=True)
            found = True
    if not found:
        st.caption("Próximamente: fuentes, notebooks y repositorios.")
    if attrs.get("year"):
        st.caption("Año asociado al concepto (puede representar origen, publicación o popularización; validar con fuente).")
    if related:
        st.markdown("**Conceptos conectados**")
        for item in related[:15]:
            if st.button(str(nodes[item].get("label") or item), key=f"atlas_related_{key}_{item}",
                         use_container_width=True):
                st.session_state.atlas_focus = item
                st.rerun()


def render_atlas(nodes: dict, edges: list) -> None:
    st.markdown("""<style>
        .block-container {max-width: 100% !important; padding-top: 1rem; padding-bottom: 1rem}
        [data-testid="stAppViewContainer"] {background: #070c19; color:#ecf3ff}
        div[data-testid="stVerticalBlock"] {gap:.65rem}
    </style>""", unsafe_allow_html=True)
    st.title("✦ Atlas IA — conocimiento conectado")
    st.caption("Explora, expande, estudia y relaciona conceptos. El contenido proviene de tu propia base de datos.")
    if not nodes:
        st.info("La base de datos aún no tiene conceptos disponibles.")
        return
    query = st.text_input("Buscar temas", placeholder="Ej.: transformers, RAG, visión artificial…",
                          key="atlas_search")
    keys = list(nodes)
    if query.strip():
        q = query.casefold().strip()
        found = [key for key in keys if q in key.casefold() or
                 q in str(nodes[key].get("label") or "").casefold() or
                 q in str(nodes[key].get("domain") or "").casefold()]
        keys = found or keys
        if not found:
            st.warning("No hay coincidencias; se muestran todos los conceptos.")
    default = st.session_state.get("atlas_focus")
    if default not in nodes:
        default = max(nodes, key=lambda x: int(nodes[x].get("kind") == "principal"))
    chosen_idx = keys.index(default) if default in keys else 0
    selectors = st.columns([3, 1, 1, 1])
    with selectors[0]:
        chosen = st.selectbox("Concepto central", keys, index=chosen_idx,
                              format_func=lambda x: str(nodes[x].get("label") or x),
                              key="atlas_select")
    with selectors[1]:
        depth = st.slider("Niveles", 1, 4, 2)
    with selectors[2]:
        limit = st.slider("Nodos máximos", 30, 250, 120, step=10)
    with selectors[3]:
        if st.button("Centrar selección", use_container_width=True):
            st.session_state.atlas_focus = chosen
            st.rerun()
    focused = chosen
    visible_nodes, visible_edges = visible_subgraph(nodes, edges, focused, depth, limit)
    left, right = st.columns([3.3, 1.2], gap="medium")
    with left:
        render_graph(visible_nodes, visible_edges, focused)
        st.caption(f"{len(visible_nodes)} conceptos visibles · {len(visible_edges)} conexiones. "
                   "Arrastra para mover, usa la rueda para acercar. Selecciona un tema arriba para centrar el mapa.")
    with right:
        related = []
        for src, dst, *_ in edges:
            if src == focused and dst in nodes:
                related.append(dst)
            elif dst == focused and src in nodes:
                related.append(src)
        render_detail(focused, nodes[focused], list(dict.fromkeys(related)), nodes)
    with st.expander("Cronología de conceptos"):
        historical = sorted([(key, attrs) for key, attrs in nodes.items()
                             if isinstance(attrs.get("year"), int)], key=lambda x: x[1]["year"])
        for key, attrs in historical[:200]:
            st.markdown(f"**{attrs['year']}** · {attrs.get('label') or key}")


def render_full_atlas(nodes: dict, edges: list, graph_store=None) -> None:
    """Unified Atlas navigation: concept map + persistent technical catalogs."""
    from catalog_store import CatalogStore
    from catalog_ui import library_panel, model_panel, summary_panel

    catalog = None
    if graph_store is not None:
        try:
            catalog = CatalogStore(graph_store.engine)
            catalog.init_schema()
            catalog.seed()
        except Exception as exc:
            st.warning(f"El catálogo PostgreSQL no está disponible ({type(exc).__name__}).")
            catalog = None
    tabs = st.tabs(["🧠 Mapa de conceptos", "🐍 Glosario Python", "🤗 Modelos Hugging Face", "📊 Estadísticas"])
    with tabs[0]:
        render_atlas(nodes, edges)
    with tabs[1]:
        library_panel(catalog)
    with tabs[2]:
        model_panel(catalog)
    with tabs[3]:
        summary_panel(catalog)
