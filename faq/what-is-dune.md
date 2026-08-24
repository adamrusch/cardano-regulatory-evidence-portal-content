---
id: what-is-dune
question: What is Dune?
audience: [academic, journalist]
category: concepts
status: locked
last_reviewed: "2026-08-24"
---

Dune is an analytics platform that indexes blockchain data and lets anyone run SQL queries against it in a browser. The portal uses Dune as its public witness: the exact SQL behind each Dune-sourced reading is published, so a reader with a free account can re-run the query and compare the result. Dune's value to the portal is that its queries are public and re-runnable, not that it is a fully independent pipeline: the Cardano Foundation has stated that Dune's Cardano datasets are produced with the Yaci Store Analytics export pipeline, so Dune shares an indexer lineage with any Yaci-derived source. Agreement between Koios and Dune remains informative because Koios reads through a different indexer lineage entirely (cardano-db-sync).
