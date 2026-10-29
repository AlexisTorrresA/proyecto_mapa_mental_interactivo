"""CLI to sync official Hugging Face metadata into the same Y700 PostgreSQL database.

Usage: python scripts/sync_hf.py [--per-category 10]
No model weights are downloaded; does not print database credentials.
"""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalog_store import CatalogStore
from graph_store import GraphStore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-category", type=int, default=10)
    args = parser.parse_args()
    # Y700 keeps DB URL in a protected file mounted into the container.
    if not os.getenv("DATABASE_URL") and Path("/run/secrets/DATABASE_URL").is_file():
        os.environ["DATABASE_URL"] = Path("/run/secrets/DATABASE_URL").read_text().strip()
    store = GraphStore.from_env(required=True)
    assert store is not None
    catalog = CatalogStore(store.engine)
    print("Catalog seed:", catalog.seed())
    print("Hugging Face sync:", catalog.refresh_huggingface(per_category=args.per_category))
    print("Final counts:", catalog.health_stats())


if __name__ == "__main__":
    main()
