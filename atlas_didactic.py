"""A responsive, image-inspired interactive teaching chart for Machine Learning.

This is an educational *projection* of persisted concepts and relationships;
the primary parent and graph are never rewritten to fit the infographic.
"""
from __future__ import annotations

import html
import json
from urllib.parse import urlparse

import streamlit.components.v1 as components

from didactic_catalog import (
    BRANCHES, ADDITIONAL, CROSS_ARCHITECTURES, CROSS_RISKS, CROSS_TECHNIQUES
)

ROLE_LABELS = {
    "algoritmo": "Algoritmo", "modelo": "Modelo", "técnica": "Técnica",
    "métrica": "Métrica", "concepto": "Concepto", "problema": "Riesgo",
    "paradigma": "Paradigma", "tarea": "Tarea", "subarea": "Área",
}


def _safe(s) -> str:
    return html.escape(str(s or ""), quote=True)


def _button(key: str, nodes: dict, kind: str, text: str | None = None) -> str:
    if key not in nodes:
        return ""
    name = text or str(nodes[key].get("label") or key)
    semantic_role = nodes[key].get("semantic_role", "")
    role = ROLE_LABELS.get(semantic_role, ROLE_LABELS.get(nodes[key].get("kind"), "Concepto"))
    return (
        f'<button type="button" class="concept {kind}" data-id="{_safe(key)}"'
        f' aria-label="Abrir ficha de {_safe(name)}" title="{_safe(role)}: {_safe(name)}">'
        f'<span class="concept-text">{_safe(name)}</span></button>'
    )


def _draw_branch(branch: dict, nodes: dict) -> str:
    key = branch["key"]
    if key not in nodes:
        return ""
    parts = [
        f'<article class="paradigm" style="--accent:{_safe(branch["accent"])};--tint:{_safe(branch["background"])}">',
        '<div class="branch-stem"></div>',
        f'<header class="paradigm-head"><span class="number">{_safe(branch["number"])}</span>'
        f'<span class="emblem">{_safe(branch["emoji"])}</span>',
        _button(key, nodes, "paradigm-title", branch["short"]),
        f'<p>{_safe(branch["description"])}</p></header>',
        '<div class="branch-body">',
    ]
    for section in branch["sections"]:
        if section["key"] not in nodes:
            continue
        parts.append('<section class="topic-block">')
        parts.append('<div class="task-heading">')
        parts.append('<span class="task-icon" aria-hidden="true">⬡</span>')
        parts.append(_button(section["key"], nodes, "task-title"))
        parts.append(f'<small>{_safe(section["subtitle"])}</small></div>')
        parts.append('<div class="algorithms">')
        parts.extend(_button(k, nodes, "algorithm") for k in section["items"] if k in nodes)
        parts.append('</div></section>')
    parts.append('<div class="satellite-area"><div class="satellite-label">'
                 '○ Conceptos relacionados <span>no son algoritmos</span></div>'
                 '<div class="satellite-wrap">')
    parts.extend(_button(k, nodes, "satellite") for k in branch["satellites"] if k in nodes)
    parts.append('</div></div></div></article>')
    return "\n".join(parts)


def _rail(title: str, intro: str, keys: list[str], nodes: dict, css_class: str) -> str:
    parts = [
        f'<section class="rail {css_class}">',
        f'<div class="rail-heading"><b>{_safe(title)}</b><small>{_safe(intro)}</small></div>',
        '<div class="rail-items">',
    ]
    parts.extend(_button(k, nodes, "rail-chip") for k in keys if k in nodes)
    parts.append('</div></section>')
    return "\n".join(parts)


def make_didactic_html(nodes: dict, edges: list) -> str:
    required = {"Machine Learning", "Aprendizaje supervisado",
                "Aprendizaje no supervisado", "Aprendizaje por refuerzo"}
    if not required.issubset(nodes):
        raise ValueError("Faltan paradigmas de la ontología para construir la vista didáctica.")
    shown = set()
    for branch in BRANCHES:
        shown.add(branch["key"])
        shown.update(branch["satellites"])
        for section in branch["sections"]:
            shown.add(section["key"])
            shown.update(section["items"])
    for branch in ADDITIONAL:
        shown.add(branch["key"])
        shown.update(branch["items"])
    shown.update(CROSS_ARCHITECTURES + CROSS_RISKS + CROSS_TECHNIQUES)
    shown.update(["Machine Learning", "Inteligencia Artificial", "Deep Learning"])
    shown.intersection_update(nodes)
    detail_nodes = {
        key: {
            "label": str(nodes[key].get("label") or key),
            "title": str(nodes[key].get("title") or "Ficha en preparación."),
            "role": ROLE_LABELS.get(nodes[key].get("semantic_role"),
                                    ROLE_LABELS.get(nodes[key].get("kind"), "Concepto")),
            "url": (nodes[key].get("url") if isinstance(nodes[key].get("url"), str)
                    and urlparse(nodes[key]["url"]).scheme in {"https", "http"} else ""),
            "year": str(nodes[key].get("year") or ""),
        }
        for key in shown
    }
    relations: dict[str, list[dict]] = {key: [] for key in shown}
    for a, b, verb, *_ in edges:
        if a in shown and b in shown and a != b:
            # Remove duplicate cross-bound references and cap per card.
            if len(relations[a]) < 45:
                relations[a].append({"to": b, "verb": verb, "direction": "out"})
            if len(relations[b]) < 45:
                relations[b].append({"to": a, "verb": verb, "direction": "in"})
    serialized = json.dumps({"nodes": detail_nodes, "relations": relations}, ensure_ascii=False)
    serialized = serialized.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    columns = "\n".join(_draw_branch(b, nodes) for b in BRANCHES)
    extras = "\n".join(
        '<div class="minor-paradigm" style="--extra:' + _safe(b["accent"]) + '">'
        + _button(b["key"], nodes, "minor-title")
        + '<div class="minor-members">'
        + "".join(_button(k, nodes, "minor-chip") for k in b["items"] if k in nodes)
        + '</div></div>' for b in ADDITIONAL if b["key"] in nodes
    )
    doc = r"""<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body>
<div class="sheet">
  <div class="sheet-bar">
    <div><span class="eyebrow">ATLAS IA · MAPA DIDÁCTICO</span>
    <h1>Cómo se organiza el Machine Learning</h1>
    <p class="lead">Paradigmas, tareas, algoritmos y conceptos asociados — cada elemento en su nivel correcto.</p></div>
    <div class="search-wrap"><label for="search">Buscar en el mapa</label><input type="search" id="search" placeholder="ROC, SVM, sobreajuste…" autocomplete="off"></div>
  </div>
  <div class="hierarchy">
    <span class="small-root">INTELIGENCIA ARTIFICIAL</span>
    <span class="down-arrow" aria-hidden="true">↓</span>
    <span class="ml-root">◈ &nbsp; MACHINE LEARNING <small>Aprendizaje automático</small></span>
    <span class="root-subtitle">Tres paradigmas destacados al mismo nivel de jerarquía</span>
  </div>
  <main class="branches">__BRANCHES__</main>
  <div class="section-divider"><span>OTROS PARADIGMAS DE MACHINE LEARNING</span></div>
  <div class="minor-grid">__ADDITIONAL__</div>
  <div class="section-divider"><span>ARQUITECTURAS Y CONCEPTOS TRANSVERSALES</span></div>
  __DL__
  __RISKS__
  __TECH__
  <footer class="legend">
    <span><i class="sample paradigm-sample"></i> Paradigma</span>
    <span><i class="sample task-sample"></i> Tarea</span>
    <span><i class="sample algorithm-sample"></i> Algoritmo / modelo</span>
    <span><i class="sample satellite-sample"></i> Métrica / concepto</span>
    <span><i class="sample risk-sample"></i> Problema / riesgo</span>
    <p>Las tarjetas no representan una jerarquía única de algoritmos: un modelo puede resolver varias tareas.
    Pulsa cualquier elemento para abrir su ficha y ver relaciones reales del grafo.</p>
  </footer>
</div>
<div id="scrim" hidden></div>
<aside id="detail" class="detail" role="dialog" aria-modal="true" aria-labelledby="detail-title" hidden>
  <div class="detail-header"><span>FICHA DEL CONCEPTO</span><button id="close" type="button" aria-label="Cerrar ficha">✕</button></div>
  <h2 id="detail-title"></h2><div id="detail-type" class="detail-type"></div>
  <p id="detail-description"></p><div id="detail-links"></div>
  <h3>Conexiones del mapa</h3><div id="detail-relations"></div>
</aside>
<script id="map-data" type="application/json">__ATLAS_DATA__</script>
<style>
*{box-sizing:border-box} html,body{margin:0;background:#f3f6fb;font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif;color:#14243a}
body{font-size:14px}.sheet{max-width:1450px;margin:0 auto;padding:22px 16px 40px}
.sheet-bar{display:flex;justify-content:space-between;align-items:end;gap:20px;flex-wrap:wrap;margin-bottom:18px}
.eyebrow{color:#2463ba;font-size:11px;font-weight:850;letter-spacing:1.55px}
h1{font-size:clamp(23px,3vw,36px);letter-spacing:-1.3px;margin:6px 0 5px;line-height:1.16}
.lead{margin:0;color:#53647b;line-height:1.6}.search-wrap{display:grid;gap:5px;min-width:220px}
.search-wrap label{font-weight:700;font-size:11px;color:#52637c}.search-wrap input{background:white;border:1px solid #cfdbec;outline:none;border-radius:11px;padding:11px 13px;width:100%}
.search-wrap input:focus{border-color:#2d71ca;box-shadow:0 0 0 3px #dbeafe}
.hierarchy{display:flex;flex-direction:column;align-items:center;text-align:center;margin-bottom:7px}
.small-root{font-weight:800;letter-spacing:1.5px;color:#436187;border:1px solid #dce5f0;background:white;border-radius:100px;font-size:10px;padding:7px 18px}
.down-arrow{color:#4682c5;font-size:20px;line-height:24px}
.ml-root{background:linear-gradient(120deg,#082747,#10385d);color:white;border-radius:16px;padding:14px 36px 13px;min-width:min(390px,94%);font-size:21px;font-weight:900;letter-spacing:.4px;box-shadow:0 9px 19px #0f3c5a22}
.ml-root small{display:block;font-size:11px;font-weight:500;letter-spacing:.5px;color:#b3d5ec}
.root-subtitle{color:#62728a;font-size:11px;margin:12px 0 0}
.branches{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:17px;margin-top:0;position:relative}
.branches:before{content:"";position:absolute;top:16px;left:16.7%;right:16.7%;height:2px;background:linear-gradient(90deg,#2563eb,#16a34a 50%,#ea580c);z-index:0}
.paradigm{--accent:#3b82f6;position:relative;min-width:0;display:flex;flex-direction:column;padding-top:39px}
.paradigm:before{content:"";position:absolute;top:0;left:50%;height:38px;width:2px;background:var(--accent)}
.branch-stem:after{content:"";position:absolute;top:29px;left:calc(50% - 5px);width:10px;height:10px;border-radius:100%;background:var(--accent);border:2px solid #fff}
.paradigm-head{background:var(--tint);border:2px solid var(--accent);border-radius:17px;padding:17px 15px 15px;position:relative;text-align:center;min-height:151px}
.number{position:absolute;top:12px;left:12px;background:var(--accent);color:white;border-radius:50%;width:30px;height:30px;display:grid;place-items:center;font-weight:800;font-size:12px}
.emblem{font-size:28px;display:block;margin-bottom:5px}.paradigm-head p{margin:5px auto 0;color:#4b5b73;max-width:310px;font-size:12px;line-height:1.45}
.concept{font:inherit;cursor:pointer;transition:transform .15s, box-shadow .15s,opacity .15s;color:inherit}
.concept:hover{transform:translateY(-2px);box-shadow:0 5px 14px #0b376022}
.concept:focus-visible{outline:3px solid #111827;outline-offset:2px}
.paradigm-title{font-weight:850;color:var(--accent);border:0;background:transparent;font-size:19px;line-height:1.22;display:block;margin:auto}
.branch-body{background:white;border:1px solid #dae4f0;border-top:none;border-radius:0 0 17px 17px;display:flex;flex-direction:column;flex:1;padding:12px;gap:12px;box-shadow:0 6px 15px #294c6910}
.topic-block{border-radius:12px;border:1px solid #e3eaf2;padding:10px;background:#fafcff}
.task-heading{display:grid;grid-template-columns:27px 1fr;align-items:center;column-gap:5px}
.task-icon{grid-row:span 2;color:var(--accent);font-size:23px;line-height:1}
.task-title{font-size:15px;font-weight:800;text-align:left;background:transparent;border:0;padding:0;color:#23344a}
.task-heading small{color:#758297;font-size:10px}.algorithms{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;margin-top:10px}
.algorithm{background:white;border:1px solid #d9e3ee;border-left:3px solid var(--accent);border-radius:9px;padding:10px 8px;font-size:11px;font-weight:700;text-align:left;min-height:44px;display:flex;align-items:center;word-break:normal;overflow-wrap:anywhere}
.satellite-area{margin-top:auto;padding:11px 7px 5px;border-top:1px dashed #a8b8d1}
.satellite-label{font-size:11px;color:#38536a;font-weight:800;margin-bottom:9px}.satellite-label span{font-size:10px;font-weight:500;color:#687d91}
.satellite-wrap{display:flex;justify-content:center;align-items:center;gap:8px;flex-wrap:wrap}
.satellite{background:var(--tint);border:1.5px dashed var(--accent);border-radius:100%;height:79px;width:79px;display:flex;align-items:center;justify-content:center;text-align:center;padding:6px;line-height:1.2;font-size:10px;font-weight:700;overflow-wrap:anywhere;flex:0 0 79px;color:#24384c}
.section-divider{display:flex;align-items:center;gap:15px;color:#536984;font-size:11px;font-weight:800;letter-spacing:1px;margin:28px 4px 15px;text-align:center}
.section-divider:before,.section-divider:after{content:"";height:1px;background:#d3e0ed;flex:1}
.minor-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.minor-paradigm{display:flex;flex-direction:column;gap:10px;background:white;border:1px solid #dce6f3;border-top:4px solid var(--extra);border-radius:13px;padding:14px}
.minor-title{font-size:15px;font-weight:850;border:none;background:transparent;color:var(--extra);text-align:left}
.minor-members{display:flex;flex-wrap:wrap;gap:9px}.minor-chip{border:1px solid #d4e1ef;background:#f8fafc;border-radius:9px;padding:9px 13px;font-size:12px;font-weight:650}
.rail{display:flex;align-items:center;gap:15px;background:#fff;border:1px solid #dce6f2;border-radius:14px;padding:15px 18px;margin:10px 0}
.rail-heading{width:220px;flex:0 0 220px}.rail-heading b{display:block;color:#213953;font-size:14px}.rail-heading small{display:block;color:#75849a;font-size:11px;margin-top:4px;line-height:1.3}
.rail-items{display:flex;gap:9px;flex-wrap:wrap}.rail-chip{border-radius:100px;padding:10px 14px;background:#f1f5fb;border:1px solid #ccd9ea;color:#374b66;font-weight:700;font-size:11px}
.cross-dl .rail-chip{background:#f3efff;border-color:#d6cafa;color:#6d43b5}
.cross-risks .rail-chip{background:#fff1f2;border-color:#fecdd3;color:#be123c;border-radius:100%}
.cross-tech .rail-chip{background:#f6f2ff;border-color:#ddd6fe;color:#6d28d9}
.legend{display:flex;flex-wrap:wrap;gap:14px;margin-top:23px;align-items:center;background:#eaf0f8;border-radius:14px;padding:14px 18px;color:#31435c;font-size:11px}
.legend span{display:flex;gap:7px;align-items:center}.legend p{margin:0;flex-basis:100%;line-height:1.5;color:#526681}
.sample{height:13px;width:13px;display:inline-block;background:#cbd5e1}
.paradigm-sample{transform:rotate(45deg);background:#2563eb}.task-sample{background:#16a34a;clip-path:polygon(25% 0,75% 0,100% 50%,75% 100%,25% 100%,0 50%)}.algorithm-sample{background:#fff;border:2px solid #2563eb;border-radius:3px}
.satellite-sample{background:#dbeafe;border:1px dashed #2563eb;border-radius:50%}.risk-sample{background:#fda4af;border-radius:50%}
#scrim{position:fixed;inset:0;background:#0f172a77;z-index:8}
.detail{position:fixed;right:0;top:0;bottom:0;width:min(450px,96%);overflow:auto;background:#fff;z-index:9;padding:23px;box-shadow:-9px 0 30px #0f172a44}
.detail-header{display:flex;align-items:center;justify-content:space-between;color:#64748b;letter-spacing:1.2px;font-size:10px;font-weight:800}
#close{border:0;border-radius:9px;background:#e2e8f0;padding:9px 13px;cursor:pointer;font-weight:700}
.detail h2{font-size:24px;line-height:1.2;margin:20px 0 9px}.detail-type{display:inline-block;border-radius:100px;background:#dbeafe;color:#1d4ed8;font-size:11px;padding:6px 12px;font-weight:700}
.detail p{color:#475569;line-height:1.65;margin-top:16px}.detail h3{font-size:14px;margin-top:25px}
#detail-relations{display:flex;flex-direction:column;gap:7px}.relation{border:1px solid #e2e8f0;text-align:left;border-radius:9px;background:#f8fafc;padding:9px;font-size:12px;cursor:pointer}
.relation em{font-size:10px;color:#64748b;display:block;margin-bottom:3px;font-style:normal}
#detail-links a{display:inline-block;margin:4px 0;color:#2563eb;font-size:12px}
.muted{opacity:.24;filter:grayscale(1)}.match{box-shadow:0 0 0 3px #fbbf24aa!important;border-color:#fbbf24!important}
[hidden]{display:none!important}
@media(max-width:950px){.branches{gap:10px}.algorithm{font-size:10px;padding:9px 6px}.satellite{width:68px;height:68px;flex-basis:68px;font-size:9px}.paradigm-head{padding:15px 7px}.paradigm-title{font-size:16px}}
@media(max-width:700px){.sheet{padding:14px 10px}.branches{grid-template-columns:1fr;gap:9px}.paradigm{padding-top:13px}.paradigm:before,.branch-stem,.branches:before{display:none}.paradigm-head{min-height:0}.branch-body{gap:9px}.algorithms{grid-template-columns:repeat(2,minmax(0,1fr))}.satellite{width:76px;height:76px;flex-basis:76px}.minor-grid{grid-template-columns:1fr}.rail{display:block}.rail-heading{width:100%;margin-bottom:10px}.sheet-bar{align-items:stretch}.search-wrap{min-width:100%}.ml-root{font-size:18px}}
</style>
<script>
(() => {
  'use strict';
  const DATA = JSON.parse(document.getElementById('map-data').textContent);
  const scrim = document.getElementById('scrim');
  const panel = document.getElementById('detail');
  const search = document.getElementById('search');
  const close = document.getElementById('close');
  let lastFocus = null;
  const mk = (tag, cls, value) => {const el=document.createElement(tag); if(cls) el.className=cls;if(value)el.textContent=value;return el;};
  const openNode = (key) => {
    const info=DATA.nodes[key]; if(!info)return;
    lastFocus=document.activeElement;
    document.getElementById('detail-title').textContent=info.label;
    document.getElementById('detail-type').textContent=info.role+(info.year?' · '+info.year:'');
    document.getElementById('detail-description').textContent=info.title;
    const linkBox=document.getElementById('detail-links');linkBox.replaceChildren();
    if(info.url && /^https?:\/\//.test(info.url)){const a=mk('a',null,'Abrir documentación ↗');a.href=info.url;a.target='_blank';a.rel='noopener noreferrer';linkBox.append(a);}
    const relationBox=document.getElementById('detail-relations');relationBox.replaceChildren();
    const relations=(DATA.relations[key]||[]).filter(e=>DATA.nodes[e.to]);
    const priority=(r)=>['incluye','es parte de'].includes(r.verb)?0:1;
    relations.sort((a,b)=>priority(a)-priority(b));
    if(!relations.length)relationBox.append(mk('p',null,'Todavía no hay relaciones registradas para este tema.'));
    for(const rel of relations.slice(0,23)){
      const item=mk('button','relation');
      item.type='button';
      const context=rel.direction==='out'?'→ '+rel.verb:'← '+rel.verb;
      item.append(mk('em',null,context),mk('strong',null,DATA.nodes[rel.to].label));
      item.addEventListener('click',()=>openNode(rel.to));relationBox.append(item);
    }
    panel.hidden=false;scrim.hidden=false;close.focus();
  };
  const dismiss=()=>{panel.hidden=true;scrim.hidden=true;if(lastFocus)lastFocus.focus();};
  document.querySelectorAll('[data-id]').forEach(el=>{
    el.addEventListener('click',()=>openNode(el.dataset.id));
  });
  close.addEventListener('click',dismiss);scrim.addEventListener('click',dismiss);
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!panel.hidden)dismiss();});
  search.addEventListener('input',()=>{
    const q=search.value.toLocaleLowerCase('es').trim();
    document.querySelectorAll('.concept').forEach(el=>{
      const obj=DATA.nodes[el.dataset.id];
      const matches=!q||(obj&&(obj.label+' '+obj.title).toLocaleLowerCase('es').includes(q));
      el.classList.toggle('muted',Boolean(q&&!matches));
      el.classList.toggle('match',Boolean(q&&matches));
    });
  });
})();
</script>
</body></html>"""
    doc = doc.replace("__BRANCHES__", columns)
    doc = doc.replace("__ADDITIONAL__", extras)
    doc = doc.replace("__DL__", _rail("Deep Learning", "Familia de arquitecturas; no es otro paradigma al mismo nivel.", CROSS_ARCHITECTURES, nodes, "cross-dl"))
    doc = doc.replace("__RISKS__", _rail("Riesgos y generalización", "Se aplican a distintas formas de aprendizaje.", CROSS_RISKS, nodes, "cross-risks"))
    doc = doc.replace("__TECH__", _rail("Técnicas transversales", "Métodos utilizados para entrenar, regularizar o evaluar.", CROSS_TECHNIQUES, nodes, "cross-tech"))
    return doc.replace("__ATLAS_DATA__", serialized)


def render_didactic(nodes: dict, edges: list):
    """Interactive self-contained graphic; no download of assets or external JS."""
    return components.html(make_didactic_html(nodes, edges), height=1440, scrolling=True)
