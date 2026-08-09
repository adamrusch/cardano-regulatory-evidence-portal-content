---
id: architecture
title: "How the portal works"
category: overview
audience: [academic, builder, regulator]
summary: "The pipeline, the append-only provenance store, reconciliation, publishing, and the anchoring path, in one narrative."
status: locked
environment_bound: true
last_reviewed: "2026-08-09"
---
The portal is a measurement pipeline, an append-only record, and a static site, connected in one direction: chain data flows in, evidence flows out, and nothing flows back.

## The pipeline

Each run pins a chain tip: one block hash, slot, and epoch that every read in the run is asked against. The pipeline then reads its sources (Koios and Dune today, with the Edinburgh Decentralization Index contributing cluster mappings, and a contracted full node as first source of truth under the ratified design), computes each metric in integer arithmetic with an explicit scale (never floating point, because several quantities exceed what floats represent exactly), and reconciles metrics that have more than one source against a declared tolerance, which is zero for lovelace-denominated quantities.

Every read is recorded: endpoint, parameters, pinned tip, response status, and a content-addressed archive of the raw response. A source that fails is recorded as an error reading, and the affected metrics publish from the remaining source under a single-source label rather than silently falling back.

## The provenance store

Observations, source readings, reconciliations, and methodology versions live in an append-only store. Immutability is enforced by the database itself, not by convention: triggers refuse updates and deletions, corrections are new rows that name what they correct, and methodology versions are content-hashed so a definition cannot drift without changing identity. Only observations from runs that completed are eligible for publication.

## Publishing

One JSON file, latest.json, carries every published value with its methodology, sources, caveats, tier, reconciliation outcome, provenance identifiers, and recent history. The site renders that file and nothing else; it never queries a chain source and never computes a value in a browser. Prose comes separately from a public content repository as a rendered bundle, and the two never mix: a prose failure cannot affect a number.

## Anchoring

The design commits each day's published values to the Cardano chain: leaves are serialized under a frozen canonical encoding, hashed into a BLAKE2b-256 Merkle tree, the leaf manifest is pinned to IPFS under its content address, and an anchor transaction records the root, the manifest address and hash, the methodology bundle hash, and the previous anchor's transaction hash, under CIP-10 metadata label 91694. A standalone verifier reconstructs any published value's leaf from public data and walks the Merkle path without trusting the portal's operators. The anchoring and canonicalization documents specify the construction to the byte; the site banner states plainly whether anchored history has begun.
