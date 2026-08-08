---
id: where-is-the-machine-readable-data
question: Where can I get the machine-readable data?
audience: [builder, academic]
category: site-tour
status: locked
last_reviewed: "2026-08-08"
---

Everything the site renders comes from one JSON file, published at /data/latest.json on this host. It carries every metric's current value, unit and scale, methodology version, sources, reconciliation outcome, caveats, and recent history, plus the run metadata (chain tip, epoch, timestamps). A formal data contract document describing each field and the compatibility promise is planned; until it ships, the file's field names are stable in practice and breaking changes are avoided.
