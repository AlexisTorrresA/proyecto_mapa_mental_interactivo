"""Persistent catalog regression checks without external network calls."""
from sqlalchemy import create_engine
import pytest

import catalog_store as c
from knowledge_catalog import MODEL_TASKS, library_catalog


@pytest.fixture()
def catalog():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    store = c.CatalogStore(engine)
    store.init_schema()
    return store


def test_library_coverage_and_distinct_examples():
    libs = library_catalog()
    assert len(libs) >= 70
    assert sum(len(x["members"]) for x in libs) >= 350
    assert len({x["id"] for x in libs}) == len(libs)
    assert len({x["code_example"] for x in libs}) == len(libs)
    assert all(x["documentation_url"].startswith("https://") for x in libs)
    assert all(x["pip_install"].startswith("pip install ") for x in libs)
    assert all(all(m["description"] and m["name"] for m in x["members"]) for x in libs)


def test_seed_is_repeatable_and_existing_data_is_preserved(catalog):
    first = catalog.seed()
    assert first >= 100
    assert catalog.seed() == 0
    lib = catalog.get("library", "numpy")
    lib["description"] = "Descripción administrada por el usuario"
    catalog._upsert("library", lib)
    assert catalog.seed() == 0
    assert catalog.get("library", "numpy")["description"] == "Descripción administrada por el usuario"


def test_model_id_and_urls_are_validated():
    assert c.valid_model_id("Qwen/Qwen3-8B")
    assert not c.valid_model_id("https://evil.example/")
    assert not c.valid_model_id("../a")
    with pytest.raises(ValueError):
        c.model_url("javascript:alert(1)")
    with pytest.raises(ValueError):
        c.get_json("http://localhost:8080/config")


def test_missing_params_are_not_invented():
    info = {
        "id": "acme/example", "downloads": 52, "likes": 3,
        "pipeline_tag": "text-generation", "tags": ["license:apache-2.0"],
        "config": {"hidden_size": 2048, "num_hidden_layers": 18},
    }
    cleaned = c.clean_model_info(info, category="Texto y LLM")
    assert cleaned["parameter_count"] is None
    assert cleaned["downloads_30d"] == 52
    assert cleaned["license"] == "apache-2.0"
    assert cleaned["configuration"]["hidden_size"]["value"] == 2048
    assert cleaned["configuration"]["hidden_size"]["meaning"]


def test_safetensors_parameter_count_source():
    info = {
        "id": "acme/example", "safetensors": {"parameters": {"BF16": 100}, "total": 100},
        "config": {"model_type": "bert"},
    }
    cleaned = c.clean_model_info(info, category="Clasificación y NLP")
    assert cleaned["parameter_count"] == 100
    assert cleaned["configuration"]["model_type"]["value"] == "bert"


def test_refresh_uses_api_and_persists_metadata(catalog, monkeypatch):
    catalog.seed()
    def fake_json(url, timeout=10):
        if "?" in url:
            return [{"id": "acme/example", "downloads": 11, "likes": 2}]
        model_id = url.split("/api/models/")[-1]
        return {"id": model_id, "downloads": 101, "likes": 12,
                "pipeline_tag": "text-generation", "cardData": {"license": "mit"},
                "safetensors": {"total": 145000000}}
    monkeypatch.setattr(c, "get_json", fake_json)
    monkeypatch.setattr(c, "MAX_MODELS", 65)
    summary = catalog.refresh_huggingface(per_category=1, max_workers=2)
    assert summary["verified"] >= 46
    assert summary["discovered"] == 1
    model = catalog.get("model", "sentence-transformers/all-MiniLM-L6-v2")
    assert model["downloads_30d"] == 101
    assert model["parameter_count"] == 145000000
    assert model["license"] == "mit"
    assert catalog.meta_get("huggingface_last_sync")


def test_offline_fallback_preserves_last_good(catalog, monkeypatch):
    catalog.seed()
    existing = catalog.get("model", "Qwen/Qwen3-8B")
    existing["verified"] = True
    existing["downloads_30d"] = 27
    catalog._upsert("model", existing)
    def fail(*args, **kwargs):
        raise TimeoutError("offline")
    monkeypatch.setattr(c, "get_json", fail)
    monkeypatch.setattr(c, "MAX_MODELS", 2)
    result = catalog.refresh_huggingface(per_category=1, max_workers=2)
    assert result["verified"] == 0
    assert catalog.get("model", "Qwen/Qwen3-8B")["downloads_30d"] == 27


def test_task_examples_are_specific():
    txt = c.model_example({"id": "Qwen/Qwen3-8B", "category": "Texto y LLM", "pipeline_tag": "text-generation"})
    emb = c.model_example({"id": "BAAI/bge-large-en-v1.5", "category": "Embeddings", "pipeline_tag": "sentence-similarity"})
    other = c.model_example({"id": "acme/audio-model", "category": "Generación de audio", "pipeline_tag": "text-to-audio"})
    assert "pipeline" in txt
    assert "SentenceTransformer" in emb
    assert "HfApi" in other
    assert txt != emb != other
