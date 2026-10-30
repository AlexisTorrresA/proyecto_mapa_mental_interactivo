from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from graph_store import GraphStore
from catalog_store import CatalogStore
from taxonomy_store import apply_once
from didactic_catalog import apply_visual_extension_once


def main() -> None:
    store = GraphStore.from_env(required=True)
    assert store is not None
    store.init_schema()
    store.healthcheck()
    added = CatalogStore(store.engine).seed()
    print(f"Catálogo Python/HF: registros nuevos={added}")
    migration = apply_once(store)
    print(f"Ontología semántica: {migration.get('new_nodes', 0)} nodos nuevos, {migration.get('new_edges', 0)} relaciones nuevas (aplicada={migration['applied']})")
    visual = apply_visual_extension_once(store)
    print(f"Vista didáctica: {visual['nodes']} nodos y {visual['edges']} enlaces nuevos (aplicada={visual['applied']})")
    stats = store.stats()
    print(f"PostgreSQL OK · nodos={stats.nodes} · relaciones={stats.edges}")


if __name__ == "__main__":
    main()
