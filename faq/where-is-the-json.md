---
id: where-is-the-json
question: Where is the JSON I can consume?
audience: [builder]
category: consumption
status: locked
last_reviewed: "2026-08-08"
---

At /data/latest.json on this host: one file with every published value and its full context, refreshed on each pipeline run. Values are integers with an explicit scale rather than floats, because several quantities exceed what floating point can represent exactly; parse them as strings or big integers. A data contract document with per-field semantics and a compatibility promise is planned; the prose content of this site is separately available as /content/content-bundle.json.
