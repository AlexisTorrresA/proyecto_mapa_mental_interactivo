"""Tests for the new illustration-inspired teaching diagram."""
import re
from sqlalchemy import create_engine

from graph_store import GraphStore
from taxonomy_store import apply_once
from didactic_catalog import (EXTRA_TOPICS, BRANCHES, ADDITIONAL, CROSS_ARCHITECTURES,
                              apply_visual_extension_once)
from atlas_didactic import make_didactic_html


def _make():
    store = GraphStore(engine=create_engine("sqlite+pysqlite:///:memory:"))
    store.init_schema()
    store.upsert_node("Inteligencia Artificial", {"kind": "principal", "domain": "Inteligencia Artificial",
                                                    "title": "IA original"})
    store.upsert_node("Machine Learning", {"kind": "subarea", "domain": "Inteligencia Artificial",
                                            "title": "Machine Learning original"})
    store.upsert_edge("Inteligencia Artificial", "Machine Learning", "incluye")
    apply_once(store)
    return store


def test_seed_preserves_existing_and_is_idempotent():
    store = _make()
    before, edges_before = store.load_graph()
    summary = apply_visual_extension_once(store)
    assert summary["applied"]
    assert summary["nodes"] >= 15
    after, edges_after = store.load_graph()
    assert all(k in after and after[k]["title"] == v["title"] for k, v in before.items())
    assert all(e in edges_after for e in edges_before)
    assert store.get_node("Machine Learning")["title"] == "Machine Learning original"
    assert apply_visual_extension_once(store) == {"applied": False, "nodes": 0, "edges": 0}
    assert "Curva ROC" in after
    assert after["Curva ROC"]["semantic_role"] == "concepto"


def test_visual_map_respects_paradigm_and_task_hierarchy():
    store = _make()
    apply_visual_extension_once(store)
    nodes, edges = store.load_graph()
    html = make_didactic_html(nodes, edges)
    assert "Aprendizaje supervisado" in html
    assert "Aprendizaje no supervisado" in html
    assert "Aprendizaje por refuerzo" in html
    assert "ROC-AUC" in html
    assert "Curva ROC" in html
    assert 'class="concept satellite"' in html
    assert 'class="concept algorithm"' in html
    assert "Familia de arquitecturas; no es otro paradigma" in html
    assert 'id="detail"' in html
    assert 'id="search"' in html
    assert "__ATLAS_DATA__" not in html
    assert "__BRANCHES__" not in html
    assert html.count('class="paradigm"') == 3


def test_extra_topics_reference_valid_parents():
    store = _make()
    apply_visual_extension_once(store)
    nodes, edges = store.load_graph()
    for parent, name, role, _ in EXTRA_TOPICS:
        assert parent in nodes and name in nodes
        assert (parent, name, "incluye") in edges
    assert ("ROC-AUC", "Curva ROC", "resume") in edges
    assert ("Deep Learning", "Aprendizaje supervisado", "se combina con") in edges


def test_visually_shown_models_exist_without_duplicates():
    store = _make()
    apply_visual_extension_once(store)
    nodes, _ = store.load_graph()
    model_ids = [
        item for branch in BRANCHES
        for section in branch["sections"] for item in section["items"]
    ]
    assert len(model_ids) == len(set(model_ids))
    assert all(name in nodes for name in model_ids)
    assert all(item in nodes for item in CROSS_ARCHITECTURES)


def test_json_content_is_safe_from_html_script_injection():
    store = _make()
    apply_visual_extension_once(store)
    item = store.get_node("Sobreajuste")
    item["title"] = 'Concepto </script><img src=x onerror=alert(1)>'
    store.upsert_node("Sobreajuste", item)
    nodes, edges = store.load_graph()
    rendered = make_didactic_html(nodes, edges)
    assert 'Concepto </script><img' not in rendered
    assert "\\u003c/script" in rendered


def test_existing_cnn_keeps_original_parent():
    store = _make()
    store.upsert_node("Visión por Computador", {"kind":"subarea", "domain":"Inteligencia Artificial", "title":"Visión"})
    store.upsert_node("CNN", {"kind":"concepto", "domain":"Inteligencia Artificial", "title":"Descripción original"})
    store.upsert_edge("Visión por Computador", "CNN", "incluye")
    apply_visual_extension_once(store)
    nodes, edges = store.load_graph()
    assert nodes["CNN"]["title"] == "Descripción original"
    assert ("Visión por Computador", "CNN", "incluye") in edges
    assert ("Deep Learning", "CNN", "incluye") not in edges
    assert ("Deep Learning", "CNN", "arquitectura de") in edges
