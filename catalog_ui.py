"""Visual explorer for editorial Python library cards and live Hub model metadata."""
from __future__ import annotations

from collections import Counter
import pandas as pd
import streamlit as st
from catalog_store import CatalogStore, model_example, model_url
from knowledge_catalog import library_catalog, MODEL_TASKS


def readable_count(value):
    return f"{value:,}".replace(",", ".") if isinstance(value, int) else "Sin datos"


def readable_params(value):
    if value is None:
        return "No informado"
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f} B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f} M"
    return readable_count(value)


def filtered(items, query, area, field):
    needle = query.casefold().strip()
    return [obj for obj in items if (area == "Todas" or obj.get(field) == area)
            and (not needle or needle in " ".join(str(obj.get(key) or "")
              for key in ("name", "id", "description", "purpose", "area", "category")).casefold())]


def library_panel(store: CatalogStore | None):
    st.subheader("Glosario profesional de librerías Python")
    st.caption("Fichas con documentación, instalación, clases, funciones y un ejemplo propio para cada librería.")
    items = store.list("library") if store else library_catalog()
    a, b, c = st.columns(3)
    a.metric("Librerías", len(items))
    b.metric("Funciones y clases", sum(len(i.get("members") or []) for i in items))
    c.metric("Especialidades", len({i.get("area") for i in items}))
    x, y = st.columns([2, 1])
    with x:
        query = st.text_input("Buscar librería", placeholder="Ej.: embeddings, gráficos, bases de datos…", key="library_search")
    with y:
        area = st.selectbox("Especialidad", ["Todas"] + sorted({i.get("area") for i in items}), key="library_area")
    subset = filtered(items, query, area, "area")
    if not subset:
        st.info("No existen coincidencias con estos filtros.")
        return
    left, right = st.columns([1.1, 2.5], gap="large")
    with left:
        lib_id = st.selectbox("Selecciona una ficha", [i["id"] for i in subset],
                              format_func=lambda identifier: next(i["name"] for i in subset if i["id"] == identifier),
                              key="selected_library")
        st.dataframe(pd.DataFrame([{"Librería": i["name"], "Área": i["area"]} for i in subset]),
                     use_container_width=True, hide_index=True, height=260)
    item = next(i for i in subset if i["id"] == lib_id)
    with right:
        st.markdown("### " + item["name"])
        st.caption(item["area"])
        st.write(item["description"])
        st.code(item["pip_install"], language="bash")
        st.link_button("Documentación oficial", item["documentation_url"], icon="🔗")
        st.markdown("**Clases, funciones y métodos principales**")
        st.dataframe(pd.DataFrame([{"API": v["name"], "Descripción": v["description"]}
                                  for v in item.get("members") or []]), hide_index=True, use_container_width=True)
        st.markdown("**Ejemplo práctico de Python**")
        st.code(item["code_example"], language="python", line_numbers=True)
        with st.expander("Ejercicio interactivo: estudia una función"):
            members = item.get("members") or []
            if members:
                method = st.selectbox("Función a practicar", [m["name"] for m in members], key="lib_method_" + lib_id)
                description = next(m["description"] for m in members if m["name"] == method)
                st.write("**Objetivo:** " + description)
                st.write("Modifica el ejemplo superior para usar " + method + " y compara sus entradas y salidas.")
                st.caption("Copia el código a tu notebook. El servidor no ejecuta código arbitrario.")


def variant_code(model):
    task = model.get("pipeline_tag") or MODEL_TASKS.get(model.get("category"))
    if task == "text-generation":
        a, b = st.columns(2)
        with a:
            tokens = st.slider("Tokens nuevos", 16, 512, 128, step=16, key="variant_tokens")
        with b:
            temp = st.slider("Temperatura", 0.1, 1.5, 0.7, step=0.1, key="variant_temperature")
        st.code("from transformers import pipeline\n"
                + "generator = pipeline('text-generation', model=" + repr(model["id"]) + ")\n"
                + "print(generator('Explica redes neuronales:', max_new_tokens=" + str(tokens)
                + ", temperature=" + str(round(temp, 2)) + ", do_sample=True))", language="python")
    elif task in ("text-classification", "image-classification", "object-detection"):
        if task == "object-detection":
            threshold = st.slider("Umbral de confianza", 0.1, 0.9, 0.5, step=0.05, key="variant_threshold")
            args = ", threshold=" + str(round(threshold, 2))
        else:
            top_k = st.slider("Resultados principales", 1, 10, 5, key="variant_topk")
            args = ", top_k=" + str(top_k)
        sample = "'I enjoy learning Python'" if task == "text-classification" else "'imagen.jpg'"
        st.code("from transformers import pipeline\n"
                + "pipe = pipeline(" + repr(task) + ", model=" + repr(model["id"]) + ")\n"
                + "print(pipe(" + sample + args + "))", language="python")
    elif model.get("category") == "Embeddings":
        norm = st.checkbox("Normalizar embeddings", value=True, key="variant_normalize")
        st.code("from sentence_transformers import SentenceTransformer\n"
                + "model = SentenceTransformer(" + repr(model["id"]) + ")\n"
                + "v = model.encode(['Aprendizaje automático', 'Machine learning'], normalize_embeddings="
                + str(norm) + ")\nprint(v.shape)", language="python")
    else:
        st.code(model_example(model), language="python")
    st.caption("Las opciones compatibles varían según la arquitectura y la versión de la librería.")


def model_panel(store: CatalogStore | None):
    st.subheader("Modelos de IA de Hugging Face")
    st.caption("Texto, visión, audio, embeddings, multimodal, OCR, imagen generativa y video.")
    items = store.list("model") if store else []
    a, b, c, d = st.columns(4)
    a.metric("Modelos", len(items))
    b.metric("Verificados", sum(i.get("verified") is True for i in items))
    c.metric("Modalidades", len({i.get("category") for i in items}))
    d.metric("Con parámetros", sum(i.get("parameter_count") is not None for i in items))
    last = store.meta_get("huggingface_last_sync") if store else None
    st.caption("Última sincronización con el Hub: " + (last or "Sin sincronizar") +
               ". Las descargas reportadas por Hugging Face corresponden aproximadamente a los últimos 30 días.")
    if st.button("Actualizar modelos, estadísticas y arquitectura", key="hf_sync", type="primary", disabled=store is None):
        with st.spinner("Consultando el catálogo oficial y guardando en PostgreSQL…"):
            try:
                result = store.refresh_huggingface(per_category=10)
                if result["verified"]:
                    st.success("Modelos actualizados: " + str(result["verified"]))
                else:
                    st.warning("Sin datos nuevos. Conservé los datos anteriores.")
                if result["errors"]:
                    st.warning("Consultas no disponibles: " + str(len(result["errors"])))
                st.rerun()
            except Exception as exc:
                st.error("Error al actualizar el catálogo: " + type(exc).__name__)
    if not items:
        st.info("La base aún no tiene modelos; comprueba la conexión a PostgreSQL.")
        return
    x, y, z = st.columns([2, 1.2, 1.2])
    with x:
        query = st.text_input("Buscar por modelo u organización", placeholder="Whisper, Qwen, CLIP, OCR…", key="hf_search")
    with y:
        area = st.selectbox("Modalidad", ["Todas"] + sorted({i["category"] for i in items}), key="hf_area")
    with z:
        order = st.selectbox("Orden", ["Más descargados", "Más likes", "Nombre"], key="hf_order")
    subset = filtered(items, query, area, "category")
    if order == "Más descargados":
        subset.sort(key=lambda i: i.get("downloads_30d") or -1, reverse=True)
    elif order == "Más likes":
        subset.sort(key=lambda i: i.get("likes") or -1, reverse=True)
    else:
        subset.sort(key=lambda i: i["id"].lower())
    if not subset:
        st.info("No hay coincidencias.")
        return
    st.caption(str(len(subset)) + " modelos encontrados; la popularidad no equivale a una evaluación de calidad.")
    st.dataframe(pd.DataFrame([{
        "Modelo": i["id"], "Modalidad": i["category"], "Descargas (30 d)": i.get("downloads_30d"),
        "Likes": i.get("likes"), "Parámetros": readable_params(i.get("parameter_count")),
        "Licencia": i.get("license") or "Sin informar",
        "Verificado": "Sí" if i.get("verified") else "Pendiente",
    } for i in subset[:250]]), use_container_width=True, hide_index=True, height=295)
    model_id = st.selectbox("Ficha detallada", [i["id"] for i in subset], key="hf_model_selected")
    item = next(i for i in subset if i["id"] == model_id)
    st.markdown("### " + item["name"])
    st.caption(item["category"] + " · " + item["id"])
    st.write(item.get("purpose") or "Consulta la tarjeta oficial para conocer los usos específicos.")
    one, two, three = st.columns(3)
    one.metric("Descargas 30 días", readable_count(item.get("downloads_30d")))
    two.metric("Likes", readable_count(item.get("likes")))
    three.metric("Parámetros", readable_params(item.get("parameter_count")))
    st.link_button("Abrir modelo en Hugging Face", model_url(item["id"]), icon="🔗")
    if not item.get("verified"):
        st.warning("Identificador aún sin verificar: estadísticas no disponibles. Revisar la ficha oficial.")
    a, b, c = st.columns(3)
    a.write("**Tarea:** " + str(item.get("pipeline_tag") or "Sin informar"))
    b.write("**Licencia:** " + str(item.get("license") or "No indicada"))
    c.write("**Acceso:** " + ("Condicionado" if item.get("gated") else "Público"
                             if item.get("gated") is False else "Sin verificar"))
    st.write("**Librería de origen:** " + str(item.get("library_name") or "No informada"))
    if item.get("last_modified"):
        st.caption("Actualización en Hub: " + item["last_modified"])
    with st.expander("Arquitectura y configuración", expanded=True):
        config = item.get("configuration") or {}
        if config:
            st.dataframe(pd.DataFrame([{"Parámetro": key, "Valor": str(val["value"])[:160],
                                        "Significado": val["meaning"]} for key, val in config.items()]),
                         use_container_width=True, hide_index=True)
        else:
            st.caption("El Hub no proporciona estos parámetros en sus metadatos. Consultar config.json en el repositorio.")
        st.caption("El total de parámetros se muestra únicamente si lo informa el Hub mediante safetensors.total.")
    with st.expander("Etiquetas y metadatos"):
        st.write(", ".join(item.get("tags") or []) or "Pendiente de verificación")
    st.markdown("**Ejemplo de código Python**")
    st.code(model_example(item), language="python", line_numbers=True)
    st.markdown("**Laboratorio de parámetros de inferencia**")
    variant_code(item)


def summary_panel(store: CatalogStore | None):
    st.subheader("Cobertura y estadísticas de la base de conocimiento")
    if store is None:
        st.info("Activa PostgreSQL para disponer de estadísticas persistentes.")
        return
    libs, models = store.list("library"), store.list("model")
    for label, rows, key in [("Librerías por especialidad", libs, "area"),
                             ("Modelos por modalidad", models, "category")]:
        st.markdown("**" + label + "**")
        counts = Counter(x.get(key) for x in rows)
        df = pd.DataFrame([{"Tipo": name, "Cantidad": count} for name, count in counts.most_common()])
        if not df.empty:
            st.bar_chart(df, x="Tipo", y="Cantidad")
    ranked = sorted((i for i in models if i.get("downloads_30d") is not None),
                    key=lambda x: x["downloads_30d"], reverse=True)[:10]
    if ranked:
        st.markdown("**Más descargados de los modelos verificados (30 días aprox.)**")
        st.bar_chart(pd.DataFrame([{"Modelo": x["id"], "Descargas": x["downloads_30d"]} for x in ranked]),
                     x="Modelo", y="Descargas")
