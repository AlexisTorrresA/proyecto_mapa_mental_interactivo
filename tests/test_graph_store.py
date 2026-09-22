from sqlalchemy import create_engine

from graph_store import GraphStore


def make_store():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    store = GraphStore(engine=engine)
    store.init_schema()
    return store


def test_seed_and_load_graph():
    store = make_store()
    nodes = {
        "IA": {"kind": "principal", "domain": "Inteligencia Artificial", "title": "Raíz"},
        "ML": {"kind": "subarea", "domain": "Inteligencia Artificial", "title": "Machine Learning"},
    }
    edges = [("IA", "ML", "incluye")]

    assert store.seed_if_empty(nodes, edges) is True
    assert store.seed_if_empty(nodes, edges) is False

    loaded_nodes, loaded_edges = store.load_graph()
    assert set(loaded_nodes) == {"IA", "ML"}
    assert loaded_nodes["ML"]["title"] == "Machine Learning"
    assert loaded_edges == [("IA", "ML", "incluye")]


def test_node_and_edge_crud():
    store = make_store()
    store.upsert_node("A", {"kind": "concepto", "domain": "D", "title": "A"})
    store.upsert_node("B", {"kind": "concepto", "domain": "D", "title": "B"})

    edge_id = store.upsert_edge("A", "B", "relaciona")
    assert edge_id > 0
    assert len(store.list_edge_records()) == 1

    store.upsert_node("A", {"kind": "concepto", "domain": "D", "title": "A editado"})
    assert store.get_node("A")["title"] == "A editado"

    store.delete_edge(edge_id)
    assert store.list_edge_records() == []

    store.delete_node("B")
    nodes, _ = store.load_graph()
    assert "B" not in nodes
