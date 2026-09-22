from graph_store import GraphStore


def main() -> None:
    store = GraphStore.from_env(required=True)
    assert store is not None
    store.init_schema()
    store.healthcheck()
    stats = store.stats()
    print(f"PostgreSQL OK · nodos={stats.nodes} · relaciones={stats.edges}")


if __name__ == "__main__":
    main()
