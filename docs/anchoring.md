---
id: anchoring
title: "Anchoring and standalone verification"
category: verification
audience: [regulator, academic, skeptic]
summary: "What the portal commits to on the Cardano chain, and how to verify a value against that commitment without trusting the operators."
status: locked
last_reviewed: "2026-08-09"
---
Version 1. Written July 25, 2026.

This document is the outsider's guide to what the portal commits to on the
Cardano chain and how to verify a value against that commitment without
trusting the portal's operators. It assumes a technically literate reader
who does not trust us; the argument for the portal's integrity is that
this document, plus a public Cardano node or any Cardano API, is enough to
reproduce every published value byte for byte.

The serialization rules the anchor pipeline depends on are frozen separately
in [CANONICALIZATION.md](#/docs/canonicalization). Read that document first if
you have not; the rules there are the substrate every hash below rests on.

## 1. What the anchor commits to

Each anchor transaction publishes one metadata entry, at CIP-10 label 91694,
whose value is a canonical map with the fields listed below. The label is in
the CIP-10 private-use range (65536 to 131071); a public label registration
is a later decision and does not change what the metadata means.

Fields at label 91694:

| Field                     | Type     | Meaning |
| ------------------------- | -------- | ------- |
| `schema_version`          | text     | Currently `cardano-regportal.anchor/1`. The pre-July-2026 preprod anchors carry `cardano-regdash.anchor/1`; the verifier accepts both. See section 8 for the rename note. |
| `date`                    | text     | UTC date the anchor covers, `YYYY-MM-DD`. |
| `merkle_root`             | 32 bytes | BLAKE2b-256 root of the day's leaf tree. |
| `leaf_count`              | uint     | Number of leaves in the tree. Committing this defends against the tree-truncation attack CANONICALIZATION.md section 5 names. |
| `methodology_bundle_hash` | 32 bytes | BLAKE2b-256 of the canonical encoding of the sorted list of methodology version hashes active on the day. |
| `prev_anchor_tx`          | 32 bytes | Transaction hash of the immediately previous anchor on this network. The genesis anchor stores an empty byte string here, which the verifier reads back as null. |
| `leaf_manifest_uri`       | text     | Always `ipfs://<CID>`. The CID is the address; no gateway hostname is embedded. Text over 64 bytes is chunked into a list of text pieces per Cardano's per-value size limit and reassembled at read time. See section 4 below. |
| `leaf_manifest_hash`      | 32 bytes | BLAKE2b-256 of the leaf manifest bytes at the URI. |
| `key_id`                  | 28 bytes | BLAKE2b-224 of the public key that signed the transaction. |

The anchor transaction has one input from the anchor address, one output back
to the same address as change, one metadata entry, and one vkey witness.
Nothing else: no certificates, no scripts, no tokens. Anything more would
make what the anchor asserts harder to explain in an exhibit.

## 1a. Which observations are eligible to be anchored

Only an observation written by a pipeline run that reached status
`completed` is eligible to be an effective value, and therefore eligible to
become a leaf. Observations from a run that is still `running`, or from one
that transitioned to `failed`, are excluded everywhere effective selection
happens: `resolveForDate`, `getLatestObservationForMetric` and
`getObservationHistory` in the provenance store, the date-scoped set the
anchor snapshot assembles from, and the default anchor date the anchoring
script picks when none is given.

The rule exists because a run that dies partway through has written rows for
whichever metrics it got to before it died, and those rows are neither a
complete nor an arbitrated view of the day. Before this rule, the effective
value was simply the newest non-superseded row for the metric and date, so a
run that was interrupted after computing four metrics out of twenty could
supply the published value for those four. Nothing visible was wrong when the
defect was found, because the interrupted runs happened to compute the same
numbers, but on a day where an interruption coincided with a source outage the
published value would have been the partial one. After mainnet anchoring
begins such a value would be permanent.

A still-running run is excluded by the same rule as a failed one, and that is
deliberate rather than a convenient simplification. A reader cannot distinguish
a run that is genuinely in flight from one whose process was killed without
ever getting the chance to write a terminal state, so both have to be treated
as not yet published. The cost is that a value becomes effective at the moment
its run completes rather than at the moment it is written, which is the correct
semantics anyway.

The run status is enforced as a controlled state transition rather than as a
free column. A run is created `running`, and the `pipeline_runs_status_transition`
trigger permits exactly one update, to `completed` or to `failed`, which must
also set `completed_at`. Every other column is immutable and deletion is
refused, the same shape the anchors table uses for its supersession link. This
matters because once effective selection depends on the status column, an
unconstrained update to that column would be a way to promote an unfinished
run's rows to published without appending anything. For the same reason
`appendObservation` refuses to write against a run that has already reached a
terminal state: a row appended after completion would inherit the trust the
status confers without having been arbitrated with the rest of the run.

The pipeline marks its own run `failed` when it throws and when it receives
SIGINT or SIGTERM. It cannot do so on SIGKILL or a power loss, which is why
the filter is written against the status rather than against the pipeline
promising to clean up after itself. An orphaned run left `running` by a hard
kill is already excluded from every published value; the failure marking only
keeps the audit view honest about what happened.

Existing orphaned runs are not deleted or rewritten. The store is append only
and a trigger enforces it. Once filtered they simply stop being effective,
which is the design working rather than a cleanup being deferred.

## 2. The leaf and the tree

CANONICALIZATION.md section 4 fixes the leaf shape. Repeated here for
convenience: a leaf is the canonical CBOR encoding of a two-element array
whose first element is the current schema tag string
`cardano-regportal.observation/3` and whose
second is a map with twelve fields, each committing either to a value or to
the BLAKE2b-256 hash of a supporting record. Altering any supporting record
changes its hash, which changes the leaf bytes, which changes the leaf hash
and the Merkle root.

The Merkle tree is BLAKE2b-256 with byte-prefix domain separation (0x00 for
leaves, 0x01 for internal nodes). Leaves are ordered by ascending bytewise
comparison of the leaf hash itself, and unpaired odd nodes are promoted
unchanged to the next level (not duplicated; see the CVE-2012-2459 note in
CANONICALIZATION.md section 5).

The leaf manifest, described in section 4 below, lists every leaf in the
tree with its preimage bytes in hex, so a verifier does not need to
reconstruct the leaf from the observation store to reproduce the hash.

## 3. Manifest order versus tree order

There are two orderings in play, and they solve different problems.

Manifest order is `(metric_id, methodology_version_hash, observed_for_date,
correction_of)`. This is what a human scanning the manifest wants: values
grouped by metric, versioned in order, corrections adjacent to what they
correct.

Merkle tree order is ascending bytewise comparison on the leaf hash itself.
This is what lets a verifier holding an unordered leaf set and a root
rebuild the tree without interpreting any leaf. The Merkle module sorts
internally, so a verifier does not have to.

## 4. The leaf manifest

The manifest is a JSON document that lists every leaf in an anchor. It is
what an outsider fetches to reconstruct the leaves that feed the Merkle root
on chain. It is content-addressed: the file name embeds its own BLAKE2b-256
hash, and the on-chain `leaf_manifest_hash` commits to the exact bytes at
the URI. A manifest whose bytes disagree with the on-chain hash is not the
one the anchor commits to.

Shape:

```json
{
  "schemaVersion": "cardano-regportal.leaf-manifest/3",
  "anchorDate": "2026-07-25",
  "network": "preprod",
  "leafSchemaTag": "cardano-regportal.observation/3",
  "leafCount": 14,
  "merkleRoot": "<64 hex chars>",
  "methodologyBundleHash": "<64 hex chars>",
  "pipelineVersion": {
    "codeCommit": "<git sha or null>",
    "nodeMajor": 22,
    "icuVersion": "76.1",
    "lockfileHash": null
  },
  "entries": [
    {
      "leafHash": "<64 hex chars>",
      "leafPreimageHex": "<hex bytes of the canonical CBOR leaf envelope>",
      "observation": { "metricId": "...", "observedForDate": "...", "value": {...}, ... }
    },
    ...
  ]
}
```

Fields on each `observation` entry match the store's row shape (metric_id,
methodology_version_id, methodology_version_hash, chain_tip_slot,
chain_tip_hash, value as `{value, scale, unit}`, correction_of,
reconciliation_id, provenance_hash, created_at). A verifier ignores fields
it does not need; the ones that matter for verification are `metricId`,
`observedForDate`, `value`, and `leafPreimageHex`.

The manifest is cached locally to `data/archive/anchors/{network}/` for
operator audit and durability, and pinned to IPFS through Blockfrost. The
on-chain URI is always `ipfs://<CID>` and never anything else. Gateway
URLs and filesystem paths are refused at metadata-build time by
`src/anchor/metadata.ts`, and the regression test
`test/anchor/metadata.test.ts` enumerates the rejected forms
(`file://`, `http://`, `https://`, bare CID, decorated ipfs:// with
paths or queries).

The reason is direct. An anchor transaction is immutable. Anything a
verifier needs to fetch it must resolve independently of the machine that
produced it and independently of any single vendor. `ipfs://<CID>`
satisfies both properties: the CID is content-addressed, and any IPFS
gateway can serve it. Embedding `file:///Users/...` or
`https://<vendor>.example/ipfs/<CID>` would make the anchor unfetchable by
a third party the moment the machine or vendor went away, and the sixty-
day anchored-history commitment does not tolerate that failure mode.

## 4a. IPFS pinning and gateway resolution

Pinning uses Blockfrost's IPFS service. `BLOCKFROST_IPFS_PROJECT_ID` must
be set when running `scripts/anchor-preprod.mjs`; if it is absent the
script refuses to run rather than falling back to a filesystem path. A
silent fallback here would reproduce exactly the class of bug this
document exists to prevent, so the failure mode is loud, human-readable,
and cannot be missed.

The verifier never depends on Blockfrost. Given `ipfs://<CID>`, the
verifier walks a fallback chain of gateways:

1. Any extra gateways the caller passes (a Blockfrost IPFS gateway when
   `BLOCKFROST_IPFS_PROJECT_ID` or `--blockfrost-ipfs-project` is given).
2. `https://ipfs.io/ipfs/<CID>`
3. `https://dweb.link/ipfs/<CID>`
4. `https://cloudflare-ipfs.com/ipfs/<CID>`

The first gateway that returns non-empty bytes wins, and the verifier
reports which one served the bytes in its output. A third party with no
Blockfrost account can verify against the public gateways alone; the
`--manifest <path>` override lets a party who obtained the bytes by any
means (local cache, IPFS pin on another provider, S3 replica) verify
fully offline. The on-chain `leaf_manifest_hash` gates correctness in
every case: bytes that hash to something other than the on-chain value
are rejected regardless of where they came from.

## 5. The hash chain

Every anchor after the first references the tx hash of the immediately
preceding anchor via `prev_anchor_tx`. A verifier walks the chain forward,
checking that each row's `prev_anchor_tx` equals the tx hash of the
preceding row, or is empty for the genesis. Any reorder, insertion, or
removal is detectable because the reference breaks.

The store enforces this on the write path: `appendAnchor` refuses a row
whose `previousAnchorTxHash` does not match the current head on that
network. The trigger is application-side rather than at the trigger layer
because the error text is more helpful; the UNIQUE index on
`(network, anchor_date)` and the FOREIGN KEY on `previous_anchor_tx_hash`
are the belt to that suspenders.

## 6. How an outsider verifies a value

You have four pieces of information: a metric id, a UTC date, a value shape
`{value, scale, unit}`, and the tx hash of the anchor. The metric id and
value come from the portal site. The tx hash comes from the site's
anchor list or from Cardanoscan.

Seven steps:

1. Fetch the transaction's metadata from any Cardano node or API. Pull the
   entry at CIP-10 label 91694. Confirm the entry decodes cleanly to the
   CBOR shape in section 1.
2. Confirm the metadata's `schema_version` is `cardano-regportal.anchor/1`, or
   `cardano-regdash.anchor/1` for anchors written before the July 2026
   product rename (see section 8). Any other version means this document
   does not describe the anchor you are looking at; find a document for
   that version.
3. Fetch the leaf manifest. Parse `leaf_manifest_uri` as
   `ipfs://<CID>`, then fetch the CID through any IPFS gateway you
   trust (`ipfs.io`, `dweb.link`, `cloudflare-ipfs.com`, a Blockfrost
   gateway, or a local IPFS daemon). Compute BLAKE2b-256 of the fetched
   bytes; it must equal `leaf_manifest_hash`. If not, the bytes at that
   CID are not the ones the anchor commits to, and the manifest is
   rejected regardless of which gateway served it.
4. Read the manifest's `merkleRoot` and `leafCount`. Both must match the
   on-chain metadata. Any disagreement means the manifest is inconsistent
   with the root and cannot be used to verify.
5. Find the manifest entry for your `(metric_id, observed_for_date)` whose
   `value` matches yours field for field. If no entry matches, the value
   you were asked to verify was not what the portal anchored that day.
6. Confirm the entry's `leafPreimageHex` hashes to its declared `leafHash`
   under the leaf hash rule (BLAKE2b-256 of 0x00 || the bytes). Then walk
   the Merkle path from the leaf up to the root, following the odd-node
   promotion rule and the domain-separated internal node hash rule
   (BLAKE2b-256 of 0x01 || left || right).
7. The reconstructed root must equal the on-chain `merkle_root`. If it
   does, you have verified that the portal anchored exactly this value
   for this metric on this date. If not, one of the earlier steps caught
   an inconsistency; the specific reason names what disagreed.

The `scripts/verify.mjs` CLI in this repository does all seven steps and
prints PASS or FAIL with the reason. It uses only the tx metadata, the
manifest bytes (from any IPFS gateway or from `--manifest <path>`), and a
Cardano API; it does not read the portal's provenance database. That
is the point.

## 7. What a PASS proves and what it does not

A PASS proves this specific value was anchored under this specific metric
on this specific date, and that the pipeline's computation produced a leaf
whose hash appears in a tree whose root is on chain. It does not prove the
methodology behind the value is sound; that is what the methodology
document is for, and its hash is committed here so you can find and read
the version that was in effect. It also does not prove the source
adapters returned truthful answers; that is the reconciliation record's
job, which the leaf's `reconciliation_hash` commits to and whose
supporting readings are archived alongside the manifest.

Anchoring shifts the trust model from "trust the portal operators not to
edit history silently" to "trust that the anchor transaction is on chain
and that the manifest at its URI is what it hashed to." The first is a
promise; the second is a fact you can check yourself.

## 8. Preprod versus mainnet, and the July 2026 schema-tag rename

Preprod anchoring runs continuously. It costs approximately 185,301
lovelace per anchor (about 0.19 tADA) at current preprod fees and produces
a fresh transaction each day. The anchor address is
`addr_test1vq6kyrvyhm7hm2g39pwqvcnw9yy8ezxzfnqkk2ak332yu4cfhhk53` and its
current UTxOs are visible on any preprod explorer.

Mainnet anchoring is a separate, later decision. Once the first mainnet
anchor is submitted, the sixty-day anchored-history commitment starts
running and beta-era mainnet values become permanently anchored, including
any that later prove wrong. The correction workflow, running through
`correction_of` on future observations, is the mechanism for handling that.

In July 2026 the product was renamed from "Cardano Regulatory Dashboard"
to "Cardano Regulatory Evidence Portal". The on-chain schema tags moved
with it: `cardano-regdash.anchor/1` became `cardano-regportal.anchor/1`
(same shape, so the trailing /1 stays), `cardano-regdash.observation/2`
became `cardano-regportal.observation/3`, and
`cardano-regdash.leaf-manifest/2` became
`cardano-regportal.leaf-manifest/3`. The observation and manifest
versions bumped because their tag strings enter the leaf preimage bytes.
The rename happened before any mainnet anchor was written; every
pre-rename anchor is preprod only and remains verifiable exactly as
before because the verifier keeps a handler registered for every
`cardano-regdash.*` tag it ever wrote. See CANONICALIZATION.md section 4
for the leaf-preimage details.

## 9. Design decisions not settled in BUILD_PLAN

Three things the plan left open that this session resolved. All are
recorded here so that a future rev of the plan can adopt or replace them
deliberately.

**Reconciliation hash by content, not by database identity.** The plan
directs the leaf to commit to a reconciliation hash. It does not say
whether the hash is over the reconciliation's row content (with UUIDs) or
over its content-derived fields. Anchoring requires the leaf preimage to
be reproducible from the archive without joining to a database that a
verifier does not have. Two runs of the same day against the same source
responses must therefore produce identical reconciliation hashes. The
anchor pipeline hashes over `(outcome, selected_reading_fingerprint,
max_delta, sorted_reading_fingerprints)`, where each fingerprint is the
same shape the leaf's `source_reading_hashes` uses. UUIDs never appear
under the anchor. The pipeline's own `provenance_hash` on the observation
row is a separate value and does use UUIDs; that hash is not on chain.

**Manifest bytes are allowed to vary across store instances.** The leaf
preimages, the Merkle root, and the methodology bundle hash are
byte-stable across reruns of the same day against equivalent content. The
manifest is a superset of the preimages that includes row UUIDs and
timestamps for human debugging, and those vary across a fresh database.
The on-chain `leaf_manifest_hash` commits to the exact bytes written for
one specific anchor; a verifier fetches those bytes and checks the hash.
Reproducing the manifest bit-for-bit from an independent database is not a
promise the pipeline makes; reproducing the anchored root is.

**No hostname of any kind in the anchor's on-chain URI, ever.** BUILD_PLAN
notes that manifest URIs should be content-addressed and gateway
independent, but does not spell out the rejection rules. The metadata
builder in `src/anchor/metadata.ts` refuses to write anything other than
`ipfs://<CID>` at `leaf_manifest_uri`, and refuses even decorated
`ipfs://` URIs with paths or queries. A short beta cycle demonstrated the
opposite failure directly: an earlier preprod anchor carried a
`file:///Users/.../data/archive/...` URI, and independent verification
failed the moment the local file was moved. That anchor is on chain
permanently as a lesson; every anchor produced after this change carries
`ipfs://<CID>` only. See `docs/CANONICALIZATION.md` section 5 for the
integrity guarantees this URI is one component of.

**No wall-clock time in the leaf, ever.** The v1 leaf format included an
`observed_at` bigint of POSIX seconds. Because the anchor script defaulted
that field from `Date.now()`, two runs seconds apart against the same
database produced different Merkle roots. Five back-to-back runs during
review produced three roots, matching the three second-boundary crossings.
The v2 leaf removes the field entirely and replaces it with
`observed_for_date`, a text `YYYY-MM-DD` drawn from the observation's own
stored row. Chain state is pinned separately via `chain_tip_slot` and
`chain_tip_hash`; a verifier does not need a wall-clock timestamp to
answer "what was the value on this date". The regression test in
`test/anchor/determinism.test.ts` calls the production path twice
without any clock injection and asserts the roots are byte-identical, so
this class of bug cannot come back through a golden-hash test with
injected time.

**Supersession, not deletion, replaces a bad anchor.** The anchors table
is append-only. If an anchor was submitted and later determined to be
wrong (bad URI, wrong methodology version, misconfigured pipeline), the
correct response is a new anchor for the same date that references the
old one via `supersedes_anchor_id` and records a reason in
`supersede_reason`. The old row stays visible; the store's
`getEffectiveAnchorForDate` returns the current non-superseded row, and
`listAnchors` returns everything in chronological order. Enforced by a
partial UNIQUE index on `(network, anchor_date) WHERE
superseded_by_anchor_id IS NULL` (at most one current anchor per date)
and by a partial UNIQUE index on `supersedes_anchor_id` (no fork in the
supersede chain). Weakening either guard is not permitted; the
`anchor-preprod` script exposes `--supersede <id-or-tx>` and
`--supersede-reason "..."` as the legitimate path, and refuses to run if
one is supplied without the other.
