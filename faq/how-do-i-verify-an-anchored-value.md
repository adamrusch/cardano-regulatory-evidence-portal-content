---
id: how-do-i-verify-an-anchored-value
question: How do I verify an anchored value against the chain?
audience: [regulator, academic, skeptic]
category: anchoring
status: locked
last_reviewed: "2026-08-08"
---

Once mainnet anchoring begins, every day's published values are committed as a Merkle root in a Cardano transaction, with the leaf data pinned to IPFS under a content address recorded in the same transaction. A standalone verifier takes a metric, date, value, and transaction hash, fetches the manifest from any public IPFS gateway, walks the Merkle path, and prints pass or fail with a specific reason; it needs no access to the portal's servers or operators. The full construction is frozen in the anchoring and canonicalization documents, written so the verifier can be reimplemented from scratch. A plain-words verification walkthrough, and eventually an in-browser verifier, are planned so the check does not require running a script.
