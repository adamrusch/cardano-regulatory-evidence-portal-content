---
id: what-sources-does-the-portal-use
question: What sources does the portal use?
audience: [academic, builder, regulator]
category: sources
status: locked
environment_bound: true
last_reviewed: "2026-08-24"
---

Three today. Koios, a community-operated open API over Cardano chain data, is the primary reading for most metrics. Dune, an analytics platform whose SQL queries anyone can re-run, acts as the public witness and second source for reconciled metrics. The Edinburgh Decentralization Index contributes the research-grade cluster mapping behind one operator-level concentration reading. The design also names a full Cardano node, operated by Intersect and/or a partner stake pool operator, as the intended first source of truth; the node is planned and the current sources become witnesses when it arrives. Source independence is tracked by named indexer lineage rather than by brand: Koios reads through cardano-db-sync, while Dune's Cardano datasets are produced with the Yaci Store Analytics pipeline, per the Cardano Foundation. A future node-attached index (Yaci Store) would therefore join as the first-party source of truth, never counted as another independent witness of Dune.
