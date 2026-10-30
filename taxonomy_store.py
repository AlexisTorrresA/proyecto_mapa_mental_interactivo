"""Migración idempotente de relaciones semánticas sin borrar información existente."""
from __future__ import annotations

from sqlalchemy import select, insert, update
from graph_store import map_meta, utcnow

from knowledge_taxonomy import CONCEPTS, CROSS_LINKS, DOMAIN, _attrs, analyze_graph

DOMAIN_LABELS = ("Inteligencia Artificial", "Ingeniería de Software",
                 "Cloud Computing", "Ciberseguridad", "Robótica e IoT",
                 "Computación Cuántica")
ROOT = "Atlas del conocimiento"


def _domain_attrs(name: str):
    return {
        "label": name, "kind": "principal", "semantic_role": "dominio",
        "domain": name, "title": f"Área de conocimiento de {name}.",
        "size": 22, "taxonomy_source": "ml-ontology-v2", "examples": [],
        "functions": [], "tags": ["dominio"], "year": None,
    }


def sync_taxonomy(store) -> dict:
    """Add missing topics and edges. Existing authored payloads are NOT overwritten."""
    nodes, edges = store.load_graph()
    already = {(a, b, r) for a, b, r, *_ in edges}
    edges_to_add = []
    node_count = 0

    def ensure(key, attrs):
        nonlocal node_count
        if key not in nodes:
            store.upsert_node(key, attrs)
            nodes[key] = attrs
            node_count += 1

    def link(a, b, relation):
        if a == b or a not in nodes or b not in nodes:
            return
        item = (a, b, relation)
        if item not in already:
            edges_to_add.append(item)
            already.add(item)

    ensure(ROOT, {
        "label": ROOT, "kind": "principal", "semantic_role": "raíz",
        "domain": "Conocimiento", "size": 28,
        "title": "Índice navegable de las áreas tecnológicas; no representa un paradigma de IA.",
        "taxonomy_source": "ml-ontology-v2", "year": None, "tags": ["inicio"],
    })
    for name in DOMAIN_LABELS:
        ensure(name, _domain_attrs(name))
        link(ROOT, name, "incluye")
    for key, attrs in list(nodes.items()):
        if attrs.get("kind") == "subarea":
            domain = attrs.get("domain")
            if domain in DOMAIN_LABELS and key != domain:
                # The older ML -> Deep Learning edge remains authoritative.
                if key == "Deep Learning" and "Machine Learning" in nodes:
                    continue
                link(domain, key, "incluye")

    for parent, key, role, description in CONCEPTS:
        ensure(key, _attrs(key, role, description, parent))
        link(parent, key, "incluye")
    for src, dst, relation in CROSS_LINKS:
        link(src, dst, relation)

    for a, b, relation in edges_to_add:
        store.upsert_edge(a, b, relation, payload={"source": "ml-ontology-v2"})
    nodes_after, edges_after = store.load_graph()
    return {
        "new_nodes": node_count, "new_edges": len(edges_to_add),
        "nodes": len(nodes_after), "edges": len(edges_after),
        "audit": analyze_graph(nodes_after, edges_after),
    }


MIGRATION_KEY = "taxonomy_ml_semantic_v2"

def apply_once(store, *, force=False) -> dict:
    """Install once; leave later manual deletions/edits untouched unless forced."""
    with store.engine.connect() as conn:
        previous = conn.execute(select(map_meta.c.value).where(map_meta.c.key == MIGRATION_KEY)).scalar_one_or_none()
    if previous == "completed" and not force:
        return {"applied": False, "reason": "already-installed"}
    summary = sync_taxonomy(store)
    with store.engine.begin() as conn:
        existing = conn.execute(select(map_meta.c.key).where(map_meta.c.key == MIGRATION_KEY)).first()
        if existing:
            conn.execute(update(map_meta).where(map_meta.c.key == MIGRATION_KEY).values(value="completed", updated_at=utcnow()))
        else:
            conn.execute(insert(map_meta).values(key=MIGRATION_KEY, value="completed", updated_at=utcnow()))
    return {"applied": True, **summary}
