---
id: what-is-koios
question: What is Koios?
audience: [academic, builder]
category: concepts
status: locked
last_reviewed: "2026-08-24"
---

Koios is a community-operated open API layer over Cardano blockchain data, run by ecosystem participants rather than a single company. It exposes the chain's ledger state, governance state, and history through documented endpoints that anyone can query. The portal reads most of its metrics from Koios and records every endpoint, parameter, and response hash in its provenance store, so a Koios-sourced value can be re-queried by anyone who wants to check it. Koios reads the chain through cardano-db-sync, an indexer lineage separate from the Yaci Store pipeline behind Dune's Cardano datasets, which is what makes it the portal's operationally independent witness.
