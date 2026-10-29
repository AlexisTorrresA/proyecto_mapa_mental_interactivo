"""PostgreSQL-backed, non-destructive catalog and Hugging Face API metadata sync.

This module never downloads model weights and never executes arbitrary snippets.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from sqlalchemy import (MetaData, Table, Column, String, Integer, DateTime, JSON,
                        Text, UniqueConstraint, select, insert, update, func)

from knowledge_catalog import CURATED_MODELS, MODEL_TASKS, MODEL_PARAMETER_KEYS, library_catalog

metadata = MetaData()
catalog_items = Table(
    "catalog_items", metadata,
    Column("kind", String(20), primary_key=True),
    Column("item_id", String(255), primary_key=True),
    Column("category", String(100), nullable=False, index=True),
    Column("title", String(255), nullable=False),
    Column("payload", JSON, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
catalog_meta = Table(
    "catalog_meta", metadata,
    Column("key", String(100), primary_key=True),
    Column("value", Text, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
HF_BASE = "https://huggingface.co"
MODEL_RE = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")
MAX_MODELS = 260


def utcnow():
    return datetime.now(timezone.utc)


def valid_model_id(model_id: str) -> bool:
    return (isinstance(model_id, str) and len(model_id) <= 200
            and bool(MODEL_RE.fullmatch(model_id))
            and all(part not in (".", "..") and not part.startswith(".") for part in model_id.split("/")))


def model_url(model_id: str) -> str:
    if not valid_model_id(model_id):
        raise ValueError("Invalid Hugging Face model ID")
    return HF_BASE + "/" + quote(model_id, safe="/")


def get_json(url: str, timeout: float = 11) -> Any:
    """Restrict outgoing calls to the official HTTPS Hub API to prevent SSRF."""
    if not url.startswith(HF_BASE + "/api/models"):
        raise ValueError("Unsupported API URL")
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "MapaMentalIA-Catalog/2.0"})
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def extract_parameters(info: dict) -> tuple[int | None, dict]:
    """Count parameters only when HF explicitly reports it."""
    safetensors = info.get("safetensors") or {}
    total = safetensors.get("total") if isinstance(safetensors, dict) else None
    if not isinstance(total, (int, float)) or total < 0:
        total = None
    config = info.get("config") if isinstance(info.get("config"), dict) else {}
    fields = {
        key: {"value": config[key], "meaning": meaning}
        for key, meaning in MODEL_PARAMETER_KEYS.items()
        if key in config and isinstance(config[key], (str, int, float, bool, list))
    }
    return (int(total) if total is not None else None), fields


def clean_model_info(info: dict, *, category: str, purpose: str = "", verified_at: str | None = None) -> dict:
    """Keep a bounded, safe metadata subset; never publish tokens or full model cards."""
    model_id = str(info.get("id") or info.get("modelId") or "")
    if not valid_model_id(model_id):
        raise ValueError(f"Invalid model identifier: {model_id!r}")
    total, architecture_params = extract_parameters(info)
    tags = info.get("tags") if isinstance(info.get("tags"), list) else []
    card = info.get("cardData") if isinstance(info.get("cardData"), dict) else {}
    license_id = card.get("license") if isinstance(card.get("license"), str) else None
    if not license_id:
        license_id = next((tag.split(":", 1)[1] for tag in tags if isinstance(tag, str) and tag.startswith("license:")), None)
    downloads = info.get("downloads")
    likes = info.get("likes")
    return {
        "id": model_id, "name": model_id.split("/")[-1], "category": category,
        "purpose": purpose or f"Modelo de {category.lower()} publicado en Hugging Face.",
        "url": model_url(model_id), "verified": True,
        "verified_at": verified_at or utcnow().isoformat(),
        "downloads_30d": downloads if isinstance(downloads, int) and downloads >= 0 else None,
        "likes": likes if isinstance(likes, int) and likes >= 0 else None,
        "gated": info.get("gated", False),
        "license": license_id, "pipeline_tag": info.get("pipeline_tag"),
        "library_name": info.get("library_name"),
        "parameter_count": total, "configuration": architecture_params,
        "created_at": info.get("createdAt"),
        "last_modified": info.get("lastModified"),
        "tags": [tag for tag in tags if isinstance(tag, str)][:25],
    }


def pending_model(model_id: str, category: str, purpose: str) -> dict:
    return {
        "id": model_id, "name": model_id.split("/")[-1], "category": category,
        "purpose": purpose, "url": model_url(model_id),
        "verified": False, "verified_at": None, "downloads_30d": None,
        "likes": None, "gated": None, "license": None,
        "pipeline_tag": MODEL_TASKS.get(category), "parameter_count": None,
        "configuration": {}, "tags": [], "last_modified": None,
    }


def model_example(info: dict) -> str:
    """A task-aware reproducible template, with no misleading claim that weights run locally."""
    model_id = info["id"]
    task = info.get("pipeline_tag") or MODEL_TASKS.get(info.get("category", ""))
    if task == "sentence-similarity" or info.get("category") == "Embeddings":
        return (f"from sentence_transformers import SentenceTransformer\n"
                f"model = SentenceTransformer({model_id!r})\n"
                "sentencias = ['Aprendizaje automático', 'Modelos de machine learning']\n"
                "embeddings = model.encode(sentencias, normalize_embeddings=True)\n"
                "print('Similitud:', float(embeddings[0] @ embeddings[1]))")
    if task in ("text-generation", "text2text-generation", "summarization", "text-classification",
                "token-classification", "translation", "automatic-speech-recognition", "image-classification",
                "object-detection", "image-to-text", "text-to-speech"):
        sample = {
            "text-generation": "'Explica el aprendizaje supervisado:'",
            "text2text-generation": "'Summarize: Machine learning detects patterns in data.'",
            "summarization": "'Researchers built a new machine learning pipeline to classify images.'",
            "text-classification": "'I love learning about Python.'",
            "token-classification": "'Ada Lovelace worked on analytical engines.'",
            "translation": "'Hello, how are you?'",
            "automatic-speech-recognition": "'audio.wav'",
            "image-classification": "'imagen.jpg'",
            "object-detection": "'imagen.jpg'",
            "image-to-text": "'imagen.jpg'",
            "text-to-speech": "'Hola, mundo'",
        }.get(task, "'Ejemplo'")
        return (f"from transformers import pipeline\n"
                f"modelo = pipeline({task!r}, model={model_id!r})\n"
                f"resultado = modelo({sample})\nprint(resultado)\n"
                "# Revisa licencia, requisitos de memoria y formato de entrada en la ficha del modelo.")
    return (f"from huggingface_hub import HfApi\n"
            f"api = HfApi()\ninfo = api.model_info({model_id!r})\n"
            "print(info.id, info.pipeline_tag, info.downloads, info.likes)\n"
            "# Para inferencia, consulta el código oficial de la tarjeta del modelo.\n"
            "# Evita descargar pesos grandes sin comprobar memoria y licencia.")


class CatalogStore:
    def __init__(self, engine):
        self.engine = engine

    def init_schema(self):
        metadata.create_all(self.engine)

    def _upsert(self, kind: str, entry: dict):
        item_id = entry["id"]
        category = entry.get("area") if kind == "library" else entry.get("category")
        title = entry["name"]
        now = utcnow()
        with self.engine.begin() as conn:
            exists = conn.execute(select(catalog_items.c.item_id).where(
                catalog_items.c.kind == kind, catalog_items.c.item_id == item_id
            )).first()
            values = {"category": category, "title": title, "payload": entry, "updated_at": now}
            if exists:
                conn.execute(update(catalog_items).where(
                    catalog_items.c.kind == kind, catalog_items.c.item_id == item_id
                ).values(**values))
            else:
                conn.execute(insert(catalog_items).values(kind=kind, item_id=item_id, **values))

    def seed(self):
        """Idempotent: insert missing records only; never destroy edited records."""
        self.init_schema()
        libraries = library_catalog()
        with self.engine.begin() as conn:
            existing = {
                (row[0], row[1])
                for row in conn.execute(select(catalog_items.c.kind, catalog_items.c.item_id))
            }
            rows = []
            now = utcnow()
            for lib in libraries:
                if ("library", lib["id"]) not in existing:
                    rows.append({"kind": "library", "item_id": lib["id"], "category": lib["area"],
                                 "title": lib["name"], "payload": lib, "updated_at": now})
            for model_id, category, description in CURATED_MODELS:
                if not valid_model_id(model_id):
                    continue
                if ("model", model_id) not in existing:
                    item = pending_model(model_id, category, description)
                    rows.append({"kind": "model", "item_id": model_id, "category": category,
                                 "title": item["name"], "payload": item, "updated_at": now})
            if rows:
                conn.execute(insert(catalog_items), rows)
        return len(rows)

    def list(self, kind: str) -> list[dict]:
        if kind not in ("library", "model"):
            raise ValueError("Invalid catalog kind")
        with self.engine.connect() as conn:
            rows = conn.execute(
                select(catalog_items.c.payload).where(catalog_items.c.kind == kind)
                .order_by(catalog_items.c.category, catalog_items.c.title)
            ).scalars().all()
        return [dict(x) for x in rows]

    def get(self, kind: str, item_id: str) -> dict | None:
        with self.engine.connect() as conn:
            row = conn.execute(select(catalog_items.c.payload).where(
                catalog_items.c.kind == kind, catalog_items.c.item_id == item_id
            )).scalar_one_or_none()
        return dict(row) if row else None

    def meta_get(self, key: str) -> str | None:
        with self.engine.connect() as conn:
            return conn.execute(select(catalog_meta.c.value).where(catalog_meta.c.key == key)).scalar_one_or_none()

    def meta_set(self, key: str, value: str):
        now = utcnow()
        with self.engine.begin() as conn:
            found = conn.execute(select(catalog_meta.c.key).where(catalog_meta.c.key == key)).first()
            if found:
                conn.execute(update(catalog_meta).where(catalog_meta.c.key == key).values(value=value, updated_at=now))
            else:
                conn.execute(insert(catalog_meta).values(key=key, value=value, updated_at=now))

    def refresh_huggingface(self, per_category: int = 10, max_workers: int = 8) -> dict:
        """Fetch top-by-downloads and curated model details, persisting only verified data.

        Each missing model remains explicitly 'not verified'. API errors don't
        touch last-good values, and download statistics are never fabricated.
        """
        per_category = min(20, max(1, int(per_category)))
        now = utcnow().isoformat()
        current = {row["id"]: row for row in self.list("model")}
        discovered: dict[str, tuple[dict, str]] = {}
        warnings = []
        tasks = list(MODEL_TASKS.items())

        def fetch_category(pair):
            label, task = pair
            url = HF_BASE + "/api/models?" + urlencode({
                "pipeline_tag": task, "sort": "downloads", "direction": "-1", "limit": per_category
            })
            data = get_json(url, timeout=14)
            if not isinstance(data, list):
                raise ValueError("Invalid API list response")
            return label, data

        with ThreadPoolExecutor(max_workers=min(max_workers, 6)) as pool:
            futures = {pool.submit(fetch_category, entry): entry[0] for entry in tasks}
            for future in as_completed(futures):
                try:
                    category, data = future.result()
                    for obj in data:
                        model_id = str(obj.get("id") or obj.get("modelId") or "")
                        if valid_model_id(model_id) and model_id not in discovered:
                            discovered[model_id] = (obj, category)
                except (HTTPError, URLError, ValueError, TimeoutError, OSError) as exc:
                    warnings.append(f"{futures[future]}: {type(exc).__name__}")

        verified = []
        # Enrich curated and top models with model-specific details/parameters.
        pool_targets = list(dict.fromkeys(list(current) + list(discovered)))[:MAX_MODELS]

        def fetch_one(model_id):
            url = HF_BASE + "/api/models/" + quote(model_id, safe="/")
            return model_id, get_json(url, timeout=12)

        with ThreadPoolExecutor(max_workers=max(1, min(max_workers, 10))) as pool:
            futures = {pool.submit(fetch_one, model_id): model_id for model_id in pool_targets}
            for future in as_completed(futures):
                model_id = futures[future]
                try:
                    _, info = future.result()
                    if not isinstance(info, dict) or info.get("id") != model_id:
                        continue
                    original = current.get(model_id, {})
                    category = original.get("category") or discovered.get(model_id, ({}, "Otros"))[1]
                    purpose = original.get("purpose", "")
                    verified.append(clean_model_info(info, category=category, purpose=purpose, verified_at=now))
                except (HTTPError, URLError, ValueError, TimeoutError, OSError) as exc:
                    if len(warnings) < 30:
                        warnings.append(f"{model_id}: {type(exc).__name__}")

        for item in verified:
            self._upsert("model", item)
        # Newly discovered models not enriched should stay visible, but not invent metadata.
        for model_id, (info, category) in discovered.items():
            if model_id not in current and all(item["id"] != model_id for item in verified):
                self._upsert("model", pending_model(model_id, category, f"Modelo popular para {category.lower()} según Hugging Face."))
        if verified:
            self.meta_set("huggingface_last_sync", now)
        self.meta_set("huggingface_last_attempt", now)
        return {
            "verified": len(verified), "discovered": len(discovered),
            "errors": warnings[:20], "sync_date": now if verified else None,
        }

    def health_stats(self) -> dict:
        with self.engine.connect() as conn:
            counts = dict(conn.execute(
                select(catalog_items.c.kind, func.count()).group_by(catalog_items.c.kind)
            ).all())
        return {"libraries": counts.get("library", 0), "models": counts.get("model", 0),
                "last_sync": self.meta_get("huggingface_last_sync")}
