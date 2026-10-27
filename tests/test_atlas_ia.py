from atlas_ia import safe_link, visible_subgraph


def test_safe_link_blocks_script_schemes():
    assert safe_link("javascript:alert(1)") is None
    assert safe_link("data:text/html,bad") is None
    assert safe_link("https://github.com/example") == "https://github.com/example"


def test_visible_subgraph_respects_depth_and_limit():
    nodes = {key: {"label": key} for key in ["A", "B", "C", "D"]}
    edges = [("A", "B", "incluye"), ("B", "C", "incluye"), ("C", "D", "incluye")]
    visible, subset = visible_subgraph(nodes, edges, "A", depth=1)
    assert set(visible) == {"A", "B"}
    assert len(subset) == 1
    limited, _ = visible_subgraph(nodes, edges, "A", depth=3, limit=2)
    assert len(limited) == 2
