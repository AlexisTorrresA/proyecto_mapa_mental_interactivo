from sqlalchemy import create_engine

from graph_store import GraphStore
from knowledge_taxonomy import (CONCEPTS, CROSS_LINKS, analyze_graph, 
                                semantic_neighborhood, semantic_path, hierarchy_parents)
from taxonomy_store import apply_once


def empty_store():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    store = GraphStore(engine=engine)
    store.init_schema()
    store.upsert_node("Inteligencia Artificial", {"kind": "principal", "domain": "Inteligencia Artificial",
                                                   "title": "Texto histórico del usuario"})
    store.upsert_node("Machine Learning", {"kind": "subarea", "domain": "Inteligencia Artificial",
                                           "title": "ML existente"})
    store.upsert_edge("Inteligencia Artificial", "Machine Learning", "incluye")
    store.upsert_node("Seguridad de Redes", {"kind": "subarea", "domain": "Ciberseguridad", "title": "Área"})
    store.upsert_node("Una herramienta propia", {"kind": "herramienta", "domain": "Ciberseguridad",
                                                  "title": "No borrar"})
    store.upsert_edge("Seguridad de Redes", "Una herramienta propia", "usa")
    return store


def test_taxonomy_creates_semantic_graph_preserving_existing():
    store = empty_store()
    outcome = apply_once(store)
    assert outcome["applied"]
    nodes, edges = store.load_graph()
    assert nodes["Machine Learning"]["title"] == "ML existente"
    assert nodes["Inteligencia Artificial"]["title"] == "Texto histórico del usuario"
    assert nodes["Una herramienta propia"]["title"] == "No borrar"
    assert "Sobreajuste" in nodes
    assert nodes["Sobreajuste"]["semantic_role"] == "problema"
    assert nodes["Precisión (precision)"]["semantic_role"] == "métrica"
    assert nodes["Aprendizaje supervisado"]["semantic_role"] == "paradigma"
    assert ("Regularización", "Sobreajuste", "mitiga") in edges
    assert ("Sobreajuste", "Aprendizaje supervisado", "afecta a") in edges
    assert ("Sobreajuste", "Aprendizaje no supervisado", "afecta a") in edges
    assert ("Sobreajuste", "Aprendizaje por refuerzo", "afecta a") in edges
    assert ("Precisión (precision)", "Clasificación", "evalúa") in edges
    assert ("Aprendizaje supervisado", "Precisión (precision)", "incluye") not in edges
    assert len(nodes) >= 75
    assert len(edges) >= 100


def test_migration_runs_once_and_does_not_resurrect_deleted_topic():
    store = empty_store()
    apply_once(store)
    store.delete_node("Regularización L1")
    again = apply_once(store)
    assert again == {"applied": False, "reason": "already-installed"}
    assert "Regularización L1" not in store.load_graph()[0]


def test_connected_and_all_domains_reachable():
    store = empty_store()
    apply_once(store)
    nodes, edges = store.load_graph()
    diag = analyze_graph(nodes, edges)
    assert diag["components"] == 1
    assert not diag["isolated"]
    assert nodes["Atlas del conocimiento"]["semantic_role"] == "raíz"
    for domain in ("Ciberseguridad", "Cloud Computing", "Computación Cuántica",
                   "Robótica e IoT", "Ingeniería de Software", "Inteligencia Artificial"):
        assert ("Atlas del conocimiento", domain, "incluye") in edges


def test_semantic_view_distinguishes_hierarchy_from_cross_relations():
    store = empty_store()
    apply_once(store)
    nodes, edges = store.load_graph()
    visible_tree, lines_tree = semantic_neighborhood(nodes, edges, "Sobreajuste", depth=2, cross=False)
    assert "Sobreajuste" in visible_tree
    assert all(r == "incluye" for _, _, r in lines_tree)
    assert "Regularización" not in visible_tree
    visible_cross, lines_cross = semantic_neighborhood(nodes, edges, "Sobreajuste", depth=2, cross=True)
    assert ("Regularización", "Sobreajuste", "mitiga") in lines_cross
    assert "Aprendizaje supervisado" in visible_cross


def test_paths_have_exactly_one_primary_parent():
    store = empty_store()
    apply_once(store)
    nodes, edges = store.load_graph()
    parents = hierarchy_parents(edges)
    assert parents["Sobreajuste"] == "Generalización y riesgos"
    assert parents["Precisión (precision)"] == "Métricas de clasificación"
    assert parents["Aprendizaje supervisado"] == "Paradigmas de aprendizaje"
    assert semantic_path("Sobreajuste", edges)[-3:] == [
        "Machine Learning", "Generalización y riesgos", "Sobreajuste"
    ]


def test_no_duplicate_curated_nodes_or_references():
    keys = [name for _, name, _, _ in CONCEPTS]
    assert len(keys) == len(set(keys))
    assert all(parent in keys or parent == "Machine Learning" for parent, _, _, _ in CONCEPTS)
    assert len(CROSS_LINKS) == len(set(CROSS_LINKS))
    assert len(CONCEPTS) >= 65
