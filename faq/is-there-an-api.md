---
id: is-there-an-api
question: Is there an API?
audience: [builder]
category: consumption
status: locked
last_reviewed: "2026-08-08"
---

The static file /data/latest.json is the interface today, deliberately: a static file served from a content delivery network has no auth, no rate limit surprises, and nothing to break. It carries current values plus recent history. A richer queryable interface would be a future decision, and the append-only provenance store it would expose already exists; if it ships, the static file remains.
