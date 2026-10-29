from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from graph_store import GraphStore
from catalog_store import CatalogStore


def main() -> None:
    store = GraphStore.from_env(required=True)
    assert store is not None
    store.init_schema()
    store.healthcheck()
    added = CatalogStore(store.engine).seed()
    print(f"Catálogo Python/HF: registros nuevos={added}")
    stats = store.stats()
    print(f"PostgreSQL OK · nodos={stats.nodes} · relaciones={stats.edges}")


if __name__ == "__main__":
    main()
