---
id: canonicalization
title: "Canonical serialization and hash construction"
category: verification
audience: [academic, builder]
summary: "The frozen serialization and hash construction, written to be reimplementable from scratch in another language."
status: locked
last_reviewed: "2026-08-09"
---
Version 2. Frozen July 25, 2026.

This document specifies exactly how the Cardano Regulatory Evidence Portal
turns an observation into bytes, and those bytes into a hash that ends up in a Cardano
transaction. It is written to be implementable from scratch, in any language,
by someone who has never seen this repository's source code. That is the point:
the argument for the portal's integrity is that anyone can recompute what it
published, and an argument that depends on being able to run a particular
version of a particular npm package in a particular year is not much of an
argument.

The rules below are frozen. Changing any of them produces different hashes for
the same facts, which would invalidate every verification bundle issued under
the previous rules. When a change becomes necessary it is made by incrementing
the schema tag described in section 4.

Version 2 replaced version 1 the same day. Version 1's leaf carried an
`observed_at` bigint of POSIX seconds set from the pipeline's wall clock,
which meant that two anchor runs against the same database seconds apart
produced different Merkle roots. Version 2 removes that field and replaces
it with `observed_for_date` (the UTC calendar date the observation describes,
a property of the data). No mainnet anchors were ever written under version
1; a single superseded preprod anchor remains on chain as the lesson.

## 1. Why this is specified rather than delegated

Deterministic serialization is the failure most likely to be discovered late
and to be expensive when it is. Every float, every unordered map, and every
Unicode normalization inconsistency between JavaScript, SQL, and JSON tooling
is a different Merkle root on rerun. A portal whose past values cannot be
recomputed has no answer to the self-attestation critique it exists to rebut,
so this is the one component where the specification precedes the code.

We do not depend on a general-purpose CBOR library. The encoder we need is
small, perhaps three hundred lines, and every widely used JavaScript CBOR
package has at least one behavior that silently diverges from what this design
requires. Naming them is worth the space, because each is a plausible mistake
for a future maintainer to make:

The `cbor` package's `canonical: true` option implements the RFC 7049 rule that
sorts map keys by length first and only then bytewise. RFC 8949 sorts purely
bytewise over the encoded key. The two rules disagree, so the option that looks
correct produces the wrong roots. That package also accepts JavaScript numbers
and emits CBOR floats for fractional values, and routes integers above
2^53 into bignum tags, which means a quantity changes its own encoding as it
grows past a threshold that ADA totals cross routinely.

`cbor-x` is built for speed and uses non-standard extensions including shared
structure records and reference tags for repeated objects. Its canonical mode
is not the library's primary concern.

`cbor2` is the closest of the four to what we want and still accepts numbers,
still encodes floats, and performs no Unicode validation.

`borc` targets IPLD's dag-cbor profile, which is strict but again sorts keys
length-first.

The pattern is that the defaults are wrong for this use in a way that produces
plausible output, which is the worst kind of wrong.

## 2. Accepted value domain

The encoder accepts exactly seven things: unsigned integers, negative integers,
byte strings, text strings, arrays, maps, and the three simple values false,
true, and null. Anything else is an error at encode time, reported with the
path at which the offending value appeared.

Integers are supplied as JavaScript `bigint` and only as `bigint`. A JavaScript
`number` anywhere in an encodable structure throws, including when its value is
integral. Coercing an integral number would be the helpful behavior and it is
precisely the behavior that lets a float reach the encoder from a code path
that happened to be tested with a small value. Integers must fall within the
range that CBOR major types 0 and 1 express in eight bytes, which is negative
2^64 through 2^64 minus one. Values outside that range throw rather than
falling back to the bignum tags, because a quantity that changes its wire
encoding as it grows has two encodings and therefore two hashes.

Integers use the shortest encoding that represents them. The value 24 encodes
as `0x1818` and not as `0x190018`.

Arrays, maps, byte strings, and text strings use definite-length encoding. The
indefinite-length forms are rejected on both encode and decode.

## 3. Numbers, scales, and text

Quantities travel through the pipeline in one of two representations, and which
one applies is a property of the metric rather than of the value.

Whole quantities, meaning lovelace amounts, counts of pools or DReps or blocks,
slot numbers, and epoch numbers, are CBOR integers. Lovelace at the scale of
total supply is roughly 4.5 times 10 to the sixteenth, which exceeds the range
JavaScript numbers represent exactly, so this is not a stylistic preference.

Ratios and percentages, meaning Gini coefficients, concentration shares, and
participation rates, are normalized decimal strings. They are not floats, not
CBOR tag 4 decimal fractions, and not numerator and denominator pairs. A
decimal string is self-describing in the raw archive, needs no library to
interpret, and is published at exactly the precision at which it is hashed, so
a disagreement in the nineteenth decimal place between two implementations
cannot destabilize a Merkle root.

A normalized decimal string uses ASCII digits only. It carries a leading minus
sign only when the value is strictly negative, never a leading plus. Zero is
the single character `0`, never `-0` and never `0.0`. The integer part carries
no leading zeros beyond the single digit zero. A fractional part, when present,
follows a single period and carries at least one digit and no trailing zeros.
Scientific notation, digit grouping, and whitespace are all rejected.

The precision of a ratio is declared in the metric's methodology version, not
inferred from the value. Values are computed as exact integer ratios and
converted by long division truncated toward zero at the declared precision.
Truncation rather than rounding, because truncation has no tie-breaking rule to
disagree about across languages.

The unit of a quantity is a required field drawn from a versioned enumeration.
A verifier reading a leaf in 2033 recovers meaning by following the leaf's
methodology version hash to the methodology document, which states the unit and
the precision. Neither is ever implicit.

Text is UTF-8 and must be in Unicode normalization form C. Normalization is
applied when a string enters the pipeline from a source, through a function
named `normalizeForIngest` that the encoder itself never calls. The encoder
then verifies rather than repeats it: if a string is not already NFC at encode
time, the encoder throws. Verifying rather than silently normalizing is what
turns NFC from a convention into an invariant, because a string that reaches
the encoder in NFD form indicates a bug upstream that would otherwise be
masked permanently in a hash.

Lone UTF-16 surrogates are rejected outright. They survive NFC normalization
unchanged, so the normalization check does not catch them, and JavaScript's
text encoder silently replaces them with the replacement character where an
encoder in another language would raise an error. Left alone, that is a case
where two conforming implementations would produce different bytes for input
they both accepted, which is precisely the class of divergence this document
exists to eliminate.

The ICU version the pipeline ran under is recorded per run, because Unicode's
stability guarantees cover characters already assigned and not characters
assigned later.

## 4. The observation leaf

A leaf is the canonical CBOR encoding of a two-element array whose first
element is a schema tag string and whose second is a map:

```text
["cardano-regportal.observation/3", { ... }]
```

The schema tag is how this specification evolves. A change to the field set
produces `cardano-regportal.observation/4`, and leaves written under any
prior tag remain verifiable under that prior tag forever.

The current tag replaced `cardano-regdash.observation/2` in July 2026 when
the product was renamed from "Cardano Regulatory Dashboard" to "Cardano
Regulatory Evidence Portal". The field set did not change; only the tag
string did. The version incremented from /2 to /3 because the tag string
enters the leaf preimage bytes, so a new prefix requires a new version
number by the same rule any field change would. Pre-rename preprod
anchors under `cardano-regdash.observation/2` remain fully verifiable
because the verifier keeps a handler registered for the legacy tag. No
mainnet anchor was ever written under either the earlier v1 or v2 tags,
so the rename is preprod-only in observable effect.

The map commits to hashes of its supporting records rather than embedding them.
The verification bundle carries the records themselves, so embedding would
enlarge every Merkle proof without adding any guarantee. The fields:

- `metric_id`, a text string from the versioned metric enumeration
- `methodology_version_hash`, 32 bytes over the canonical encoding of the
  methodology document
- `chain_tip_slot`, an integer
- `chain_tip_hash`, 32 bytes
- `observed_for_date`, a text string of the UTC calendar date this
  observation describes, formatted `YYYY-MM-DD`. A property of the data;
  no wall-clock timestamp enters the leaf. See the version 2 note above.
- `value`, an integer or a normalized decimal string per section 3
- `unit`, a text string from the versioned unit enumeration
- `source_reading_hashes`, an array of 32-byte hashes ordered by source
  identifier so that ordering is stable across runs
- `reconciliation_hash`, 32 bytes over the canonical encoding of the
  reconciliation record
- `correction_of`, the 32-byte leaf hash of the observation this one corrects,
  or null
- `correction_reason_hash`, 32 bytes over a rationale document, or null
- `pipeline_version_hash`, 32 bytes over the git commit, the lockfile hash, the
  Node major version, and the ICU version. The four inputs describe the
  environment at the moment the value was **computed and reconciled**, never
  the moment it was anchored. The observation store persists them on the
  observation row (columns `pv_code_commit`, `pv_node_major`,
  `pv_icu_version`, `pv_lockfile_hash`), and leaf reconstruction reads
  those stored values back; the anchoring machine's own environment does
  not enter any leaf. This is what lets a correction chain be
  reconstructed from stored fields alone (MAINNET_READINESS.md B1). A row
  with any of the four fields null cannot be honestly rebuilt, and the
  assembler refuses to fabricate a value.

The invariant that every anchored observation's provenance hash transitively
covers its methodology, its source readings, and its reconciliation follows
directly. Altering any supporting record changes that record's hash, which
changes the bytes of the leaf, which changes the leaf hash and the Merkle root.

Corrections do not touch the original leaf. A correction is a new observation,
published in a later day's tree, whose `correction_of` field carries the leaf
hash of what it supersedes. The erroneous leaf stays anchored under its
original root permanently. The store enforces that a correction references a
leaf from a strictly earlier anchor, which makes a backdated correction
impossible rather than merely discouraged.

### 4.a. `source_reading_hashes` field-by-field

Each entry of `source_reading_hashes` is BLAKE2b-256 over the canonical CBOR
encoding of a map whose keys and values are exactly the following. Ordering
of keys is bytewise ascending on the encoded key per section 2; the map is
written in a natural order below and the encoder rearranges it. Every value
is one of the seven accepted CBOR types from section 2. Nothing else enters.

- `source_id`: text string. The source identifier drawn from the versioned
  source enumeration recorded in the genesis anchor (section 6).
- `api_version`: text string. The pinned upstream API version, e.g. `"v1"`.
  Load-bearing because sources have historically changed numeric formatting
  between versions.
- `endpoint`: text string. The upstream URL path the reading was fetched
  from, without the host component. Hosts are versioned by the source
  registry and are not part of the fingerprint.
- `status`: text string. One of `ok`, `error`, `auth_failed`, `outage`,
  `schema_mismatch`.
- `executed_at`: text string. ISO 8601 UTC timestamp of the read, with
  second precision, as `YYYY-MM-DDTHH:MM:SSZ`. Two runs against the same
  source at different wall-clock moments produce different source-reading
  fingerprints; the leaf itself carries `observed_for_date` rather than
  a wall clock, so wall-clock drift in the source reading does not
  destabilise the leaf across reruns.
- `chain_tip_slot`: integer.
- `chain_tip_hash`: text string. The chain tip's block hash as **lowercase
  hex**, encoded as a CBOR text string. The observation leaf itself uses a
  32-byte byte string for the same value (see the field list above); the
  source reading fingerprint uses the hex text form because that is what
  the store row carries. A second implementer producing the source-reading
  hash must encode this field as text, not bytes.
- `raw_archive_hash`: text string or null. When the read succeeded, this is
  the **SHA-256 of the raw response body**, encoded as lowercase hex text.
  BLAKE2b-256 is what the pipeline uses everywhere else; the raw archive
  hash is the one exception because SHA-256 is what every command-line
  tool computes without ceremony (`sha256sum archive.json`) and the raw
  archive is meant to be verifiable by anyone with `sha256sum` and the
  file. When the read failed, the value is null (CBOR simple value 22).
- `value`: text string or null. When the reading produced a value, this is
  the string `"<value>e-<scale><unit>"`, where `<value>` is the canonical
  base-10 integer string (no leading zeros, no leading `+`, no leading `-`
  for zero), `<scale>` is the decimal scale as base-10 without leading
  zeros, and `<unit>` is the unit string from the enumeration. For
  example, a Gini coefficient of 0.412345 stored as `{value: "412345",
  scale: 6, unit: "ratio"}` fingerprints as the text
  `"412345e-6ratio"`. Concatenating rather than nesting a map keeps the
  fingerprint's encoding trivial to reproduce and is what
  `src/anchor/snapshot.ts:hashSourceReading` does. When the read failed,
  the value is null.

The full source-reading map, then, has exactly these nine keys and no
others. A second implementation that adds a key would produce a different
hash and its output would not match any anchored leaf.

### 4.b. `reconciliation_hash` field-by-field

`reconciliation_hash` is BLAKE2b-256 over the canonical CBOR encoding of a
map with the following four keys. Reconciliation identity is
content-derived: reading UUIDs never enter this hash. Two runs of the same
day that read the same source responses produce byte-identical
reconciliation hashes, which is the property the daily anchor's
byte-stability rests on.

- `outcome`: text string. One of `single_source`, `agreed`,
  `disagreed_resolved`, `disagreed_unresolved`.
- `selected`: byte string or null. When the reconciliation selected a
  reading, this is the 32-byte BLAKE2b-256 fingerprint of that reading
  (i.e., the value described in section 4.a, but as raw bytes, not hex
  text). When no reading was selected, null.
- `max_delta`: text string or null. The largest observed pairwise
  difference between candidate readings, encoded as a canonical
  base-10 integer string in the scale of the metric (matching how it is
  stored on the reconciliation row). Null when there was no delta to
  report, which is the `single_source` case.
- `reading_fingerprints`: array of byte strings. The 32-byte BLAKE2b-256
  fingerprints of every reading that fed the reconciliation, **sorted
  ascending by bytewise comparison of the hash**. Sorting fixes the wire
  form regardless of insertion order, so a second implementation
  reproduces the hash without needing to know the order readings were
  written to the database.

That map has exactly these four keys. `src/anchor/snapshot.ts:
hashReconciliationByContent` is the reference implementation; a second
implementation matches its output by producing exactly the same map,
sorting the reading fingerprints, and canonically CBOR-encoding it.

## 5. Merkle construction

The hash function is BLAKE2b with a 32-byte digest.

Domain separation uses byte prefixes rather than BLAKE2b's personalization
parameter. Personalization is cleaner in principle, but many BLAKE2
implementations in other languages do not expose it conveniently, and a
verifier in 2033 should not need a particular binding to check our work.

```text
leaf hash     = BLAKE2b-256(0x00 || canonical_cbor(leaf_envelope))
internal node = BLAKE2b-256(0x01 || left_hash || right_hash)
```

Leaves are ordered by ascending bytewise comparison of the leaf hash itself.
Sorting on the hash rather than on metric identity means a verifier holding an
unordered set of leaves and a root can rebuild the tree without interpreting
any leaf's contents.

When a level of the tree has an odd number of nodes, the unpaired final node is
promoted unchanged to the next level. It is not duplicated. Duplicating the
last node is the Bitcoin construction that CVE-2012-2459 describes, and it
permits two distinct leaf sets to produce the same root, which would let
someone claim a leaf set we never published. The promotion rule is the one RFC
6962 specifies for certificate transparency and it has no such property.

The anchor transaction's metadata commits to the root, the leaf count, a
methodology bundle hash covering every methodology version active that day, the
previous anchor's transaction hash, the leaf manifest's content identifier as
raw multihash bytes, the anchor schema version, and the signing key identifier.
Committing the leaf count matters because without it a tree can be presented
with leaves removed.

## 6. What has to exist before the first mainnet anchor

Several things are nearly free to produce now and cannot be added later without
re-anchoring history. They are listed here so that the anchoring session treats
them as prerequisites rather than as follow-up work.

This document needs a content hash of its own, recorded in the genesis anchor,
so that a verifier can confirm which version of the rules applied.

The fixture corpus needs a stable commit identifier, also recorded in the
genesis anchor. A future re-implementation in Rust or Python validates against
the fixtures, not against this repository's TypeScript.

The genesis anchor transaction itself needs to be self-describing. It records
the hash of this document, the fixture corpus commit, the hash function and
digest length, the two domain separation prefixes, the odd-node rule, the
anchor metadata schema version, the leaf schema tag, the initial key registry,
and the enumerations for units, metric identifiers, and source identifiers.
Registering the CIP-10 label precedes it, because the label number is part of
what the genesis anchor asserts.

The mechanical shape of these fields is fixed in
`src/anchor/metadata.ts:GenesisMetadataInput`. They live in a nested
`genesis` map inside the anchor metadatum, present only in the first anchor
per network and absent on every subsequent anchor. `parseAnchorMetadatum`
round-trips them, so a verifier reading the genesis transaction on chain
recovers the same struct the anchoring machine wrote.

Correction chain reconstruction requires the per-observation
pipeline_version fingerprint (`pv_code_commit`, `pv_node_major`,
`pv_icu_version`, `pv_lockfile_hash`) to be present on every row a
correction ever points to. The columns landed with MAINNET_READINESS.md
B1; earlier rows carry `pv_code_commit` backfilled from the run's own
`code_commit` and the other three null, and the assembler throws when it
encounters a null on a row it must rebuild. A verifier reconstructing a
correction from the leaf manifest reads the four fields from the per-entry
`pipelineVersion` object (`cardano-regdash.leaf-manifest/2` and `cardano-regportal.leaf-manifest/3`), so
the reconstruction does not depend on the store.

The three enumerations (units, metric identifiers, source identifiers) are
committed inline as arrays of text metadatums, one text entry per identifier.
Every identifier is short enough to fit under Cardano's 64-byte
per-metadatum limit, and the total encoded size of the genesis metadatum
for the launch corpus is a few kilobytes, well under the ~16 KB
per-transaction ceiling. A regression test asserts the size stays under
4 KB so that a future change to the enumerations that pushes past the
comfortable margin fails loudly and forces the fallback below.

If a future corpus outgrows what fits inline, commit each enumeration by
hash (BLAKE2b-256 over the canonical CBOR encoding of the sorted array of
identifiers) as a bytes metadatum, and publish the full sorted list in the
leaf manifest at a well-known key (e.g. `enumerations.units`). The genesis
anchor's `hash_function`, `digest_length_bytes`, and `metadata_schema_version`
fields tell a verifier exactly how the by-hash form was computed, so the
choice between inline and by-hash is visible in the on-chain rules and does
not require a schema tag bump. Today that fallback is not needed and the
inline form is used.

Before mainnet anchoring begins, a second implementation of the encoder in
another language should reproduce the fixture corpus byte for byte and agree
with the TypeScript implementation across a week of preprod anchors. That
agreement is the only real test of whether this document is unambiguous, as
opposed to merely detailed.

## Appendix: frozen golden values

These are the values the implementation produces as of version 2 of this
document. They are recorded here, in prose rather than only in test code, so
that a second implementation in another language has something to check itself
against without reading TypeScript, and so that any change to them is visible
in this file's history rather than only in a diff to a test fixture.

If any value below changes, the serialization has changed, and that is a
version increment rather than a bug fix.

The fixture corpus digest, which is the hash over the encoding of every fixture
in the corpus:

```text
0db5c66395a2649d19b746af904c39d8e74230f91e9fe206ed6ede90627a68bc
```

Domain separation, demonstrating that a leaf hash and an internal node hash
over the same underlying bytes differ:

```text
leafHash(bytes 0x00..0x3f)
  5450d0d0dc7eb22a12f09617236354bde65426d37c7221ea1dad7ff37b58ab26
nodeHash(bytes 0x00..0x1f, bytes 0x20..0x3f)
  65a386efc0b9954da9312c6e07616c7102c8074eb3d204ef7dba08d049b7ba73
```

Known-answer Merkle roots, where each leaf is a 32-byte fill of the given byte
value. The single-leaf case returns the leaf itself, which is the expected
behavior of a tree with nothing to combine:

```text
1 leaf   0x01              0101010101010101010101010101010101010101010101010101010101010101
2 leaves 0x01..0x02        81f855f6e4eac8d9e571c539b652e1574f085015711abed480cf6defe7a1f1ac
3 leaves 0x01..0x03        a371147dc440c4ba64ede69137ae8774b6f451e955725873445e51fa8853993e
4 leaves 0x01..0x04        65419f568d7a4fb4ec1d0b2c7de8e5866961e8965deb5e5f5074a9168fd76e92
5 leaves 0x01..0x05        98b572c089e78cbe8a8634e8e64440651c8cef8f982e7154aa0a2ebd7503d656
7 leaves 0x10..0x16        c14f6afab08d37143d93406edf5898b48ceced59c59cad1f1818689b55e7b73e
8 leaves 0x01..0x08        6306b772e241c2c5f8f559be4dc9bb2bee7a58ca0af3429ff0b8781865d2d210
```

The malleability check from section 5, which is the most important value in
this appendix. Under the duplicate-last construction these two leaf sets would
produce the same root, which would let someone present a leaf set we never
published. Under the promotion rule they differ:

```text
leaves [0xa1, 0xb2, 0xc3]
  3a1c297d63994e7a2f234381e531e8b38770d69754076c2ad30b72802049143d
leaves [0xa1, 0xb2, 0xc3, 0xc3]
  da6663cadff27d89126d195f5f502a19fe8a184c04c274e982eb7334f68f272b
```

A fully populated observation leaf under the current `cardano-regportal.observation/3`
schema tag, and the same leaf shape carrying a normalized decimal string
value rather than an integer:

```text
integer value leaf   fe13e1a60a81f0a2aa48c69aaa986f412ac5726bbf15748dc0946a94e9e19287
decimal string leaf  79c37fcd5e2dcc76e0ac4b3cc696feb235d1f6d99544f9b8a8e6a48d757bcbbb
```

For anyone verifying pre-rename preprod anchors: the same leaves under
the legacy `cardano-regdash.observation/2` schema tag hash to the values
below. Every field of the map is byte-identical between the two tags;
only the leading tag string differs.

```text
integer value leaf, legacy tag   f2bcbbf84e53f5efbf87489f0eee5037da1bdae5b891070700f7eaa7e7f2d5cb
decimal string leaf, legacy tag  05c7f7e88e8f409ed1dc4374bc306e66f8a213fa077086379466aa0e97f6207e
```

The fixture inputs are the ones in `test/canonical/leaf.test.ts`:
`observed_for_date = "2026-07-25"`, `chain_tip_slot = 138429421`,
`chain_tip_hash = 32 bytes of 0x02`, etc. Any implementation that produces
different bytes for those inputs disagrees with this specification.
