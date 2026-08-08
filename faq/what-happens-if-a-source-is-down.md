---
id: what-happens-if-a-source-is-down
question: What happens if a source is down?
audience: [builder, academic, skeptic]
category: sources
status: locked
last_reviewed: "2026-08-08"
---

The pipeline records the failure as an error reading, with the HTTP status and note stored in the provenance record, and publishes the affected metrics from the remaining source under an honest single-source label. Nothing silently falls back: a metric that normally says sources agreed will visibly say single source until the second source returns, and the outage itself remains in the append-only store. This has happened in practice, and the behavior you see on the site during an outage is the designed behavior, not a degraded accident.
