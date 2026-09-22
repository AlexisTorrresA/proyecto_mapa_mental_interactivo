from __future__ import annotations

import hmac
import os
from typing import Any

import pandas as pd
import streamlit as st

from graph_store import GraphStore


KINDS = [
    "principal",
    "subarea",
    "concepto",
    "herramienta",
    "libreria",
    "framework",
    "recurso",
    "dataset",
    "aplicacion",
    "funcion",
    "contenedor",
]


def _split_lines(value: str) -> list[str]:
    result: list[str] = []
    for raw in (value or "").replace(",", "\n").splitlines():
        item = raw.strip()
        if item and item not in result:
            result.append(item)
    return result


def _join_lines(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        return value
    return "\n".join(str(item) for item in value)


def _safe_year(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_size(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 12.0


def admin_is_configured() -> bool:
    return bool(os.getenv("MAPA_ADMIN_PASSWORD", "").strip())


def render_database_status_sidebar(store: GraphStore | None, fallback_message: str | None = None) -> None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Datos")
    if store is None:
        st.sidebar.warning("Modo local: usando datos incluidos en el código.")
        if fallback_message:
            st.sidebar.caption(fallback_message)
        return

    try:
        stats = store.stats()
        st.sidebar.success("PostgreSQL conectado")
        st.sidebar.caption(f"{stats.nodes} nodos · {stats.edges} relaciones")
    except Exception as exc:
        st.sidebar.error("PostgreSQL no disponible")
        st.sidebar.caption(str(exc))


def render_admin_login_sidebar(store: GraphStore | None) -> bool:
    if store is None or not admin_is_configured():
        return False

    st.sidebar.markdown("---")
    st.sidebar.subheader("Administración")

    if st.session_state.get("map_admin_authenticated", False):
        st.sidebar.success("Sesión de edición activa")
        if st.sidebar.button("Cerrar modo administrador", use_container_width=True):
            st.session_state["map_admin_authenticated"] = False
            st.rerun()
        return True

    password = st.sidebar.text_input(
        "Clave de administrador",
        type="password",
        key="map_admin_password_input",
    )
    if st.sidebar.button("Entrar al editor", use_container_width=True):
        expected = os.getenv("MAPA_ADMIN_PASSWORD", "")
        if expected and hmac.compare_digest(password, expected):
            st.session_state["map_admin_authenticated"] = True
            st.rerun()
        else:
            st.sidebar.error("Clave incorrecta")
    return False


def _node_form_fields(attrs: dict[str, Any], *, key_prefix: str) -> dict[str, Any]:
    kind_value = attrs.get("kind", "concepto")
    kind_index = KINDS.index(kind_value) if kind_value in KINDS else KINDS.index("concepto")

    col1, col2 = st.columns(2)
    with col1:
        kind = st.selectbox(
            "Tipo",
            KINDS,
            index=kind_index,
            key=f"{key_prefix}_kind",
        )
        domain = st.text_input(
            "Dominio",
            value=str(attrs.get("domain") or "General"),
            key=f"{key_prefix}_domain",
        )
        label = st.text_input(
            "Etiqueta visible",
            value=str(attrs.get("label") or ""),
            key=f"{key_prefix}_label",
        )
        label_en = st.text_input(
            "Etiqueta en inglés",
            value=str(attrs.get("label_en") or ""),
            key=f"{key_prefix}_label_en",
        )
    with col2:
        year_raw = st.text_input(
            "Año",
            value="" if attrs.get("year") is None else str(attrs.get("year")),
            key=f"{key_prefix}_year",
        )
        size = st.number_input(
            "Tamaño visual",
            min_value=4.0,
            max_value=80.0,
            value=_safe_size(attrs.get("size", 12)),
            step=1.0,
            key=f"{key_prefix}_size",
        )
        url = st.text_input(
            "URL",
            value=str(attrs.get("url") or ""),
            key=f"{key_prefix}_url",
        )

    title = st.text_area(
        "Descripción",
        value=str(attrs.get("title") or ""),
        height=100,
        key=f"{key_prefix}_title",
    )
    title_en = st.text_area(
        "Descripción en inglés",
        value=str(attrs.get("title_en") or ""),
        height=100,
        key=f"{key_prefix}_title_en",
    )

    col3, col4 = st.columns(2)
    with col3:
        tags = st.text_area(
            "Tags (uno por línea)",
            value=_join_lines(attrs.get("tags", [])),
            height=110,
            key=f"{key_prefix}_tags",
        )
        subareas = st.text_area(
            "Subáreas relacionadas",
            value=_join_lines(attrs.get("related_subareas", [])),
            height=110,
            key=f"{key_prefix}_subareas",
        )
    with col4:
        concepts = st.text_area(
            "Conceptos relacionados",
            value=_join_lines(attrs.get("related_concepts", [])),
            height=110,
            key=f"{key_prefix}_concepts",
        )
        functions = st.text_area(
            "Funciones principales",
            value=_join_lines(attrs.get("functions", [])),
            height=110,
            key=f"{key_prefix}_functions",
        )

    examples = st.text_area(
        "Ejemplos (uno por línea)",
        value=_join_lines(attrs.get("examples", [])),
        height=120,
        key=f"{key_prefix}_examples",
    )
    code_example = st.text_area(
        "Ejemplo de código",
        value=str(attrs.get("code_example") or ""),
        height=150,
        key=f"{key_prefix}_code",
    )

    result = dict(attrs)
    result.update(
        {
            "kind": kind,
            "domain": domain.strip() or "General",
            "label": label.strip() or None,
            "label_en": label_en.strip() or None,
            "title": title.strip() or None,
            "title_en": title_en.strip() or None,
            "year": _safe_year(year_raw),
            "size": float(size),
            "url": url.strip() or None,
            "tags": _split_lines(tags),
            "related_subareas": _split_lines(subareas),
            "related_concepts": _split_lines(concepts),
            "functions": _split_lines(functions),
            "examples": _split_lines(examples),
            "code_example": code_example.rstrip() or None,
        }
    )
    return result


def render_admin_panel(store: GraphStore, nodes: dict[str, dict[str, Any]]) -> None:
    if not st.session_state.get("map_admin_authenticated", False):
        return

    st.markdown("---")
    st.header("Administración del mapa")
    st.caption(
        "Los cambios se guardan directamente en PostgreSQL. "
        "La app los toma al recargar y ya no es necesario editar el archivo Python."
    )

    edit_tab, new_tab, relations_tab, backup_tab = st.tabs(
        ["Editar nodo", "Nuevo nodo", "Relaciones", "Respaldo"]
    )

    with edit_tab:
        if not nodes:
            st.info("No hay nodos disponibles.")
        else:
            selected_key = st.selectbox(
                "Nodo",
                sorted(nodes.keys(), key=lambda item: item.lower()),
                key="admin_existing_node",
            )
            current = store.get_node(selected_key) or nodes[selected_key]

            with st.form("edit_node_form"):
                st.text_input("Identificador", value=selected_key, disabled=True)
                edited = _node_form_fields(current, key_prefix="edit")
                save = st.form_submit_button("Guardar cambios", type="primary")

            if save:
                store.upsert_node(selected_key, edited)
                st.success(f"Nodo '{selected_key}' actualizado.")
                st.rerun()

            with st.expander("Eliminar este nodo"):
                st.warning("También se eliminarán sus relaciones.")
                confirm = st.checkbox(
                    f"Confirmo que deseo eliminar '{selected_key}'",
                    key="confirm_delete_node",
                )
                if st.button(
                    "Eliminar nodo",
                    disabled=not confirm,
                    type="secondary",
                    key="delete_existing_node",
                ):
                    store.delete_node(selected_key)
                    st.success("Nodo eliminado.")
                    st.rerun()

    with new_tab:
        with st.form("new_node_form", clear_on_submit=False):
            new_key = st.text_input(
                "Identificador único",
                placeholder="Ej.: Retrieval-Augmented Generation",
            )
            new_attrs = _node_form_fields(
                {
                    "kind": "concepto",
                    "domain": "Inteligencia Artificial",
                    "size": 12,
                },
                key_prefix="new",
            )
            create = st.form_submit_button("Crear nodo", type="primary")

        if create:
            key = new_key.strip()
            if not key:
                st.error("Debes indicar un identificador.")
            elif key in nodes:
                st.error("Ya existe un nodo con ese identificador.")
            else:
                new_attrs["label"] = new_attrs.get("label") or key
                store.upsert_node(key, new_attrs)
                st.success(f"Nodo '{key}' creado.")
                st.rerun()

    with relations_tab:
        edge_rows = store.list_edge_records()
        if edge_rows:
            df = pd.DataFrame(
                [
                    {
                        "id": row["id"],
                        "origen": row["source_key"],
                        "relación": row["relation"],
                        "destino": row["target_key"],
                    }
                    for row in edge_rows
                ]
            )
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No hay relaciones registradas.")

        node_keys = sorted(nodes.keys(), key=lambda item: item.lower())
        if len(node_keys) >= 2:
            st.subheader("Agregar relación")
            with st.form("add_relation_form"):
                src = st.selectbox("Origen", node_keys, key="new_edge_source")
                dst = st.selectbox("Destino", node_keys, index=1, key="new_edge_target")
                relation = st.text_input("Tipo de relación", value="relaciona")
                add_edge = st.form_submit_button("Guardar relación", type="primary")
            if add_edge:
                try:
                    store.upsert_edge(src, dst, relation)
                    st.success("Relación guardada.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

        if edge_rows:
            st.subheader("Eliminar relación")
            labels = {
                int(row["id"]): f"#{row['id']} · {row['source_key']} — {row['relation']} → {row['target_key']}"
                for row in edge_rows
            }
            edge_id = st.selectbox(
                "Relación",
                list(labels.keys()),
                format_func=lambda value: labels[value],
                key="delete_edge_select",
            )
            if st.button("Eliminar relación", key="delete_edge_button"):
                store.delete_edge(int(edge_id))
                st.success("Relación eliminada.")
                st.rerun()

    with backup_tab:
        st.write(
            "Puedes descargar una copia completa de nodos y relaciones antes de hacer cambios grandes."
        )
        snapshot = store.export_snapshot_json()
        st.download_button(
            "Descargar respaldo JSON",
            data=snapshot,
            file_name="mapa_mental_ia_backup.json",
            mime="application/json",
            use_container_width=True,
        )
