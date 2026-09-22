from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    delete,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.engine import Engine


metadata = MetaData()

map_nodes = Table(
    "map_nodes",
    metadata,
    Column("node_key", String(255), primary_key=True),
    Column("kind", String(64), nullable=False, index=True),
    Column("domain", String(160), nullable=False, index=True),
    Column("label", String(255), nullable=True),
    Column("label_en", String(255), nullable=True),
    Column("title", Text, nullable=True),
    Column("title_en", Text, nullable=True),
    Column("url", Text, nullable=True),
    Column("year", Integer, nullable=True, index=True),
    Column("size", Float, nullable=True),
    Column("payload", JSON, nullable=False),
    Column("active", Boolean, nullable=False, default=True, index=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

map_edges = Table(
    "map_edges",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "source_key",
        String(255),
        ForeignKey("map_nodes.node_key", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "target_key",
        String(255),
        ForeignKey("map_nodes.node_key", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("relation", String(160), nullable=False, default="relaciona"),
    Column("payload", JSON, nullable=False),
    Column("active", Boolean, nullable=False, default=True, index=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("source_key", "target_key", "relation", name="uq_map_edge"),
)

map_meta = Table(
    "map_meta",
    metadata,
    Column("key", String(120), primary_key=True),
    Column("value", Text, nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)


class DatabaseNotConfigured(RuntimeError):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_database_url(url: str) -> str:
    url = (url or "").strip()
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return str(value)


def _node_row(node_key: str, attrs: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    now = now or utcnow()
    payload = _json_safe(dict(attrs or {}))
    return {
        "node_key": str(node_key),
        "kind": str(payload.get("kind") or "concepto"),
        "domain": str(payload.get("domain") or "General"),
        "label": payload.get("label"),
        "label_en": payload.get("label_en"),
        "title": payload.get("title"),
        "title_en": payload.get("title_en"),
        "url": payload.get("url"),
        "year": payload.get("year") if isinstance(payload.get("year"), int) else None,
        "size": float(payload.get("size")) if isinstance(payload.get("size"), (int, float)) else None,
        "payload": payload,
        "active": bool(payload.get("active", True)),
        "created_at": now,
        "updated_at": now,
    }


def _parse_edge(edge: Any) -> tuple[str, str, str, dict[str, Any]]:
    if isinstance(edge, dict):
        src = str(edge.get("source") or edge.get("source_key") or "")
        dst = str(edge.get("target") or edge.get("target_key") or "")
        relation = str(edge.get("relation") or "relaciona")
        payload = dict(edge.get("payload") or {})
        for key in ("hidden", "cluster"):
            if key in edge:
                payload[key] = edge[key]
        return src, dst, relation, _json_safe(payload)

    if isinstance(edge, (list, tuple)) and len(edge) >= 2:
        src, dst = str(edge[0]), str(edge[1])
        relation = str(edge[2]) if len(edge) >= 3 else "relaciona"
        payload = dict(edge[3]) if len(edge) >= 4 and isinstance(edge[3], dict) else {}
        return src, dst, relation, _json_safe(payload)

    raise ValueError(f"Formato de relación no soportado: {edge!r}")


@dataclass
class GraphStats:
    nodes: int
    edges: int


class GraphStore:
    """Persistencia del mapa conceptual en la base PostgreSQL administrada por Y700."""

    def __init__(self, database_url: str | None = None, *, engine: Engine | None = None):
        if engine is not None:
            self.engine = engine
            self.database_url = str(engine.url)
            return

        raw_url = database_url if database_url is not None else os.getenv("DATABASE_URL", "")
        url = normalize_database_url(raw_url)
        if not url:
            raise DatabaseNotConfigured(
                "DATABASE_URL no está configurada. En Y700 la entrega automáticamente "
                "el Deployment Manager cuando database.postgres=true."
            )

        self.database_url = url
        self.engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_recycle=1800,
            future=True,
        )

    @classmethod
    def from_env(cls, *, required: bool = False) -> "GraphStore | None":
        url = os.getenv("DATABASE_URL", "").strip()
        if not url:
            if required:
                raise DatabaseNotConfigured("DATABASE_URL no está configurada")
            return None
        return cls(url)

    def init_schema(self) -> None:
        metadata.create_all(self.engine)

    def healthcheck(self) -> bool:
        with self.engine.connect() as conn:
            conn.execute(select(func.count()).select_from(map_nodes))
        return True

    def stats(self) -> GraphStats:
        with self.engine.connect() as conn:
            nodes_count = int(
                conn.execute(
                    select(func.count()).select_from(map_nodes).where(map_nodes.c.active.is_(True))
                ).scalar_one()
            )
            edges_count = int(
                conn.execute(
                    select(func.count()).select_from(map_edges).where(map_edges.c.active.is_(True))
                ).scalar_one()
            )
        return GraphStats(nodes=nodes_count, edges=edges_count)

    def seed_if_empty(
        self,
        nodes: dict[str, dict[str, Any]],
        edges: Iterable[Any],
        *,
        seed_version: str = "legacy-v1",
    ) -> bool:
        """Carga los datos históricos solo cuando la tabla está vacía."""
        self.init_schema()
        now = utcnow()

        with self.engine.begin() as conn:
            existing = int(conn.execute(select(func.count()).select_from(map_nodes)).scalar_one())
            if existing > 0:
                return False

            node_rows = [_node_row(key, attrs, now) for key, attrs in nodes.items()]
            if node_rows:
                conn.execute(insert(map_nodes), node_rows)

            known_keys = set(nodes.keys())
            edge_rows: list[dict[str, Any]] = []
            seen: set[tuple[str, str, str]] = set()
            for edge in edges:
                src, dst, relation, payload = _parse_edge(edge)
                if not src or not dst or src == dst:
                    continue
                if src not in known_keys or dst not in known_keys:
                    continue
                identity = (src, dst, relation)
                if identity in seen:
                    continue
                seen.add(identity)
                edge_rows.append(
                    {
                        "source_key": src,
                        "target_key": dst,
                        "relation": relation,
                        "payload": payload,
                        "active": True,
                        "created_at": now,
                        "updated_at": now,
                    }
                )
            if edge_rows:
                conn.execute(insert(map_edges), edge_rows)

            conn.execute(
                insert(map_meta),
                {
                    "key": "seed_version",
                    "value": seed_version,
                    "updated_at": now,
                },
            )
        return True

    def load_graph(self) -> tuple[dict[str, dict[str, Any]], list[tuple[str, str, str]]]:
        self.init_schema()
        with self.engine.connect() as conn:
            node_rows = conn.execute(
                select(map_nodes).where(map_nodes.c.active.is_(True)).order_by(map_nodes.c.node_key)
            ).mappings().all()
            edge_rows = conn.execute(
                select(map_edges)
                .where(map_edges.c.active.is_(True))
                .order_by(map_edges.c.id)
            ).mappings().all()

        nodes: dict[str, dict[str, Any]] = {}
        for row in node_rows:
            attrs = dict(row["payload"] or {})
            attrs.update(
                {
                    "kind": row["kind"],
                    "domain": row["domain"],
                    "label": row["label"] or attrs.get("label") or row["node_key"],
                    "label_en": row["label_en"] or attrs.get("label_en"),
                    "title": row["title"] if row["title"] is not None else attrs.get("title"),
                    "title_en": row["title_en"] if row["title_en"] is not None else attrs.get("title_en"),
                    "url": row["url"] if row["url"] is not None else attrs.get("url"),
                    "year": row["year"] if row["year"] is not None else attrs.get("year"),
                    "size": row["size"] if row["size"] is not None else attrs.get("size", 12),
                }
            )
            nodes[row["node_key"]] = attrs

        edges = [
            (row["source_key"], row["target_key"], row["relation"])
            for row in edge_rows
            if row["source_key"] in nodes and row["target_key"] in nodes
        ]
        return nodes, edges

    def get_node(self, node_key: str) -> dict[str, Any] | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                select(map_nodes).where(map_nodes.c.node_key == node_key)
            ).mappings().first()
        if not row:
            return None
        attrs = dict(row["payload"] or {})
        attrs.update(
            {
                "kind": row["kind"],
                "domain": row["domain"],
                "label": row["label"],
                "label_en": row["label_en"],
                "title": row["title"],
                "title_en": row["title_en"],
                "url": row["url"],
                "year": row["year"],
                "size": row["size"],
                "active": row["active"],
            }
        )
        return attrs

    def upsert_node(self, node_key: str, attrs: dict[str, Any]) -> None:
        node_key = (node_key or "").strip()
        if not node_key:
            raise ValueError("El identificador del nodo no puede estar vacío")
        if len(node_key) > 255:
            raise ValueError("El identificador del nodo excede 255 caracteres")

        now = utcnow()
        row = _node_row(node_key, attrs, now)
        with self.engine.begin() as conn:
            exists = conn.execute(
                select(map_nodes.c.node_key).where(map_nodes.c.node_key == node_key)
            ).first()
            if exists:
                row.pop("created_at", None)
                conn.execute(
                    update(map_nodes)
                    .where(map_nodes.c.node_key == node_key)
                    .values(**row)
                )
            else:
                conn.execute(insert(map_nodes), row)

    def delete_node(self, node_key: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(map_edges).where(map_edges.c.source_key == node_key))
            conn.execute(delete(map_edges).where(map_edges.c.target_key == node_key))
            conn.execute(delete(map_nodes).where(map_nodes.c.node_key == node_key))

    def list_edge_records(self) -> list[dict[str, Any]]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                select(map_edges).where(map_edges.c.active.is_(True)).order_by(map_edges.c.id)
            ).mappings().all()
        return [dict(row) for row in rows]

    def upsert_edge(
        self,
        source_key: str,
        target_key: str,
        relation: str = "relaciona",
        payload: dict[str, Any] | None = None,
    ) -> int:
        source_key = (source_key or "").strip()
        target_key = (target_key or "").strip()
        relation = (relation or "relaciona").strip()
        if not source_key or not target_key:
            raise ValueError("Origen y destino son obligatorios")
        if source_key == target_key:
            raise ValueError("Una relación no puede apuntar al mismo nodo")

        with self.engine.begin() as conn:
            keys = {
                row[0]
                for row in conn.execute(
                    select(map_nodes.c.node_key).where(
                        map_nodes.c.node_key.in_([source_key, target_key])
                    )
                )
            }
            if source_key not in keys or target_key not in keys:
                raise ValueError("El nodo origen o destino no existe")

            existing = conn.execute(
                select(map_edges.c.id).where(
                    map_edges.c.source_key == source_key,
                    map_edges.c.target_key == target_key,
                    map_edges.c.relation == relation,
                )
            ).first()
            now = utcnow()
            if existing:
                edge_id = int(existing[0])
                conn.execute(
                    update(map_edges)
                    .where(map_edges.c.id == edge_id)
                    .values(
                        payload=_json_safe(payload or {}),
                        active=True,
                        updated_at=now,
                    )
                )
                return edge_id

            result = conn.execute(
                insert(map_edges).values(
                    source_key=source_key,
                    target_key=target_key,
                    relation=relation,
                    payload=_json_safe(payload or {}),
                    active=True,
                    created_at=now,
                    updated_at=now,
                )
            )
            return int(result.inserted_primary_key[0])

    def delete_edge(self, edge_id: int) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(map_edges).where(map_edges.c.id == int(edge_id)))

    def export_snapshot(self) -> dict[str, Any]:
        nodes, edges = self.load_graph()
        return {
            "version": 1,
            "exported_at": utcnow().isoformat(),
            "nodes": nodes,
            "edges": [
                {"source": src, "target": dst, "relation": relation}
                for src, dst, relation in edges
            ],
        }

    def export_snapshot_json(self) -> str:
        return json.dumps(self.export_snapshot(), ensure_ascii=False, indent=2)
