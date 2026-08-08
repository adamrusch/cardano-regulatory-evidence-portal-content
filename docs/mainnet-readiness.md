---
id: mainnet-readiness
title: "Mainnet anchoring readiness"
category: operations
audience: [regulator, community]
summary: "The checklist that gates the start of mainnet anchoring, with the status of every item."
status: locked
last_reviewed: "2026-08-09"
---
Starting mainnet anchoring is not reversible. The first submitted anchor begins
the sixty-day anchored-history commitment, and every value it commits to is
permanent, including any that later prove wrong. The correction workflow exists
for that case, but a correction is an addition to the record rather than a
removal, so the bar for starting is that the things which would make a
correction impossible or meaningless are fixed first.

This file is the checklist. Each item states what must be true and the command
or observation that decides it, so that going ahead is a decision about
accepted risk rather than about whether anyone remembered to look. Status
values were determined on 2026-07-25 by running the stated check.

The stopping rule is deliberate. The goal is a defensible line, not zero
defects. Items in the second list are real and worth doing, and none of them
would make an anchored value wrong.

## Blocking

### B1. A correction points at the leaf hash that was actually anchored

Met, 2026-07-25.

The `pipeline_version` fingerprint the observation was computed under is
persisted on the observation row itself (columns `pv_code_commit`,
`pv_node_major`, `pv_icu_version`, `pv_lockfile_hash`), added by ALTER
TABLE with a backfill from `pipeline_runs.code_commit` for pre-B1 rows.
`appendObservation` requires the four fields as a `pipelineVersion`
object and throws when one is missing; `assembleDailySnapshot` reads them
back from the row when it needs to reconstruct a correction's leaf hash,
and throws naming the observation id and the missing field when a
pre-migration row carries a null pv field. The anchoring machine's own
`PipelineVersion` no longer enters any leaf: it stays in the manifest
header as informational context, and each manifest entry now carries the
per-observation `pipelineVersion` (leaf-manifest schema `/2`) so a
verifier reconstructing a leaf reads the fingerprint from the entry
rather than the store.

Same-day supersession: the leaf's `correction_of` is the target's
reconstructed leaf hash only when the target appeared in an anchor
manifest for a strictly earlier date on the same network. Otherwise the
leaf field is null and the store's audit chain carries the full
history separately, so the leaf claims only what the chain can support.

Check: `npx vitest run test/anchor/correction-chain.test.ts` passes with
no `it.fails` wrappers. The suite runs `assembleDailySnapshot` end to end
across two anchor days with two different `PipelineVersion` values,
asserts the correction's leaf preimage contains the anchored leaf hash of
its target byte for byte, and separately asserts the anchoring-time
`PipelineVersion` never enters a leaf.

### B2. A submitted transaction is confirmed on chain before its anchor row is written

Met, 2026-07-25.

`src/anchor/anchorDay.ts` now calls `confirmTxOnChain` (in
`src/anchor/confirm.ts`) between `submitAnchorTx` and `appendAnchor`. The
poll fetches the tx from Blockfrost, ignores mempool 404s, and returns
successfully only once `block_height` is non-null; on timeout it throws
with a message that names the tx hash and warns against resubmission
without checking the chain.

The mirror-fault reconciliation is handled by
`reconcileOrphanedAnchor` in the same module, invoked from `anchorDay`
before every submission. It walks the anchor address's recent
transactions via `BlockfrostClient.addressTransactions`, and for any tx
absent from the store that carries our CIP-10 label, it parses the
metadata (using `parseAnchorMetadatum`) and appends the row.

Check: `grep -n "blockfrost.transaction\|reconcileOrphanedAnchor\|confirmTxOnChain" src/anchor/anchorDay.ts`
shows both hooks in place. `npx vitest run test/anchor/confirm.test.ts`
covers both the helper and the anchorDay integration: the "polls for
confirmation before writing the anchor row" test asserts the submit /
confirm / append order via a recorded event log, and the "reconciles an
orphaned on-chain anchor before submitting the next one" test drives
anchorDay end-to-end with a fabricated on-chain orphan and verifies the
store head after reconciliation matches the orphan and its
`previous_anchor_tx_hash` matches the genesis.

### B3. The genesis anchor is self-describing

Met, 2026-07-25.

`GenesisMetadataInput` in `src/anchor/metadata.ts` carries every field
CANONICALIZATION.md section 6 asks for: canonicalization document hash,
fixture corpus commit, hash function and digest length, both domain
separation prefixes, the odd-node rule, the anchor metadata schema
version, the leaf schema tag, the initial key registry, and the unit,
metric id, and source id enumerations. Fields live in a nested `genesis`
map on the anchor metadatum, present only when the caller supplies
`input.genesis`, and are absent on every non-genesis anchor.
`parseAnchorMetadatum` round-trips them; the tests
`test/anchor/metadata.test.ts` in the "genesis metadata" block cover
field-by-field equality after round-trip, per-field validation, and a
size assertion that the genesis metadatum fits well under Cardano's
16 KB per-transaction limit for the launch corpus.

The launch corpus fits inline; no enumeration is currently large enough to
need the commit-by-hash fallback. CANONICALIZATION.md section 6 documents
the fallback for future maintainers, and the size test locks the current
choice.

Check: `npx vitest run test/anchor/metadata.test.ts` returns green, and
`parseAnchorMetadatum(buildAnchorMetadatum(genesisInput))` returns
`genesisInput` field for field.

### B4. Manifests are pinned through at least two IPFS providers

Not met.

BUILD_PLAN.md section 4 commits to "at least two providers (Blockfrost IPFS
plus one other; single-provider pinning is a single point of failure)."
`src/anchor/manifest.ts` calls `opts.ipfs.pin` on a single `BlockfrostIpfsClient`.
If that pin goes away, the CID stops resolving for anyone who does not already
hold the bytes, and the standalone verification claim in ANCHORING.md section
4a fails.

Check: the anchoring script pins through Blockfrost and one other named
provider, and a manifest retrieved from the second provider hashes to the
on-chain `leaf_manifest_hash`.

### B5. The serialization spec is complete enough to re-implement from

Met (spec completeness), 2026-07-25.

`docs/CANONICALIZATION.md` sections 4.a and 4.b now specify
`hashSourceReading` and `hashReconciliationByContent` field by field, with
the exact CBOR type of every entry. Section 4.a calls out the two
easy-to-miss encodings: `chain_tip_hash` is text (hex) in the source
reading fingerprint even though the leaf itself uses bytes, and
`raw_archive_hash` is SHA-256 rather than BLAKE2b-256 because
`sha256sum archive.json` is what a verifier reproduces at the shell. The
`value` field's `"<value>e-<scale><unit>"` string form is spelled out with
an example.

The full second-implementation exercise (a Rust or Python re-implementation
reproducing the fixture corpus byte for byte and agreeing across a week of
preprod anchors) remains out of scope; the docs' own gate for that check
stays open. What is now in place is the spec completeness that makes the
exercise possible.

Check: `docs/CANONICALIZATION.md` section 4 lists every field entering
either hash, with its CBOR type and encoding rule. A second implementer
starting from the doc reproduces the fingerprint without reading the
TypeScript.

### B6. The verifier cross-checks every field the manifest and the chain share

Met, fixed 2026-07-25.

`src/anchor/verify.ts` now compares `manifest.methodologyBundleHash` against
the on-chain `metadata.methodologyBundleHashHex` and reports a field-specific
failure reason when they disagree. Test in `test/anchor/verify.test.ts`
(`fails with a methodology_bundle_hash-specific reason when the manifest
bundle hash is altered`) exercises the path.

Check: `grep -n "methodologyBundleHash" src/anchor/verify.ts` shows the
comparison; `npx vitest run test/anchor/verify.test.ts` returns green.

### B7. The anchoring script refuses a dirty working tree

Met, fixed 2026-07-25.

`assertCleanTree` in `src/anchor/preflight.ts` runs before any env var,
signing key, or Blockfrost call. When `git status --porcelain` is non-empty
it throws with the dirty paths listed; the shared CLI in `src/anchor/cli.ts`
converts the throw to exit code 2 and prints the reason. `--allow-dirty`
overrides the guard, printing a prominent warning and continuing with a null
code commit.

Check: `npx vitest run test/anchor/preflight.test.ts` runs the guard both
through the helper and through `runAnchorCli`, the exact function
`scripts/anchor-preprod.mjs` delegates to. The production entry path test
asserts that with a dirty tree the CLI exits 2 with a dirty-tree message and
never reaches the env var check that follows.

### B8. A mainnet anchoring script exists and has been dry-run

Partially met, 2026-07-25.

`scripts/anchor-mainnet.mjs` exists as a thin wrapper over the shared
`runAnchorCli` in `src/anchor/cli.ts`. The extraction removes the previous
five hardcoded `'preprod'` strings; the wrappers carry only network config.
`scripts/gen-anchor-key.mjs` accepts `--network mainnet` and writes to
`keys/anchor-mainnet.skey.json` with the `addr1` prefix; it refuses to
overwrite an existing file.

The dry run itself has not been executed. It needs
`BLOCKFROST_MAINNET_PROJECT_ID` and mainnet chain access, both listed under
B11 and both coordinator-side. The mainnet script is coded so the
coordinator can invoke `node scripts/anchor-mainnet.mjs --dry-run` once the
env var is set; the wrapper's help output was verified locally, and the
mainnet code path is exercised in `test/anchor/cli-mainnet.test.ts` (missing
env var, wrong-network signer, missing key file).

Check: run `node scripts/anchor-mainnet.mjs --dry-run` when
`BLOCKFROST_MAINNET_PROJECT_ID` is available; the output prints tx hash and
fee without submitting.

### B9. A mainnet anchor key exists and its address is published

Not met. `keys/` holds `anchor-preprod.skey.json` and `anchor-preprod.addr`
only.

Check: `ls -la keys/anchor-mainnet.skey.json` shows mode `-rw-------`, and the
address appears on a public page of the portal.

### B10. The mainnet anchor address is funded for at least a year

Not met, and not yet checkable, since the address does not exist.

Check: the address balance is at least three times a year of anchoring at the
observed preprod fee of about 185,301 lovelace per anchor, so on the order of
200 ada.

### B11. Chain access for mainnet is configured

Not met. `BLOCKFROST_MAINNET_PROJECT_ID` is unset in `.envrc.local`.

Check: the variable is set and a request to
`https://cardano-mainnet.blockfrost.io/api/v0/blocks/latest` returns 200.

### B12. A preprod anchor verifies standalone from a public gateway

Met, verified 2026-07-25.

`scripts/verify.mjs` returns PASS for `nakamoto-coefficient-consensus` on
2026-07-25 against anchor
`2d4e26df92cb59be9d3055cd333c725b5c6a98d4f3a3810fd0c3ca471be24e39`, fetching
the manifest from `ipfs.io` rather than from a Blockfrost gateway or a local
file. Checked independently as well: the manifest fetched from `ipfs.io`
hashes to `32f5ba78...`, matching the on-chain `leaf_manifest_hash`; all
fifteen leaf preimages hash to their declared leaf hashes; and the tree rebuilds
to `42fbbaa1...`, matching the on-chain root.

Check: run the verifier with no Blockfrost IPFS project id and no `--manifest`
override; exit code 0.

### B13. Observations from runs that did not complete cannot be anchored

Met, fixed 2026-07-25.

Effective selection requires the observation's run to have reached status
`completed`, in the store resolvers, the anchor snapshot and the anchoring
script's default date. See ANCHORING.md section 1a.

Check: `npx vitest run test/anchor/snapshot.test.ts test/provenance/store.test.ts`.

### B14. The provenance database is backed up with a tested restore

Met, 2026-07-25.

`scripts/backup-db.mjs` writes a defragmented consistent snapshot of
`data/provenance.db` via SQLite's `VACUUM INTO`. Default destination is
`data/backups/provenance-<UTC-timestamp>.db`. `scripts/verify-backup.mjs`
opens a backup as a fresh `ProvenanceStore` and, with `--against`, asserts
the latest anchor tx hash matches the live source; exit code 1 on mismatch.
The restore procedure is a straight file copy: `cp <backup>
data/provenance.db`. `docs/RUNBOOK.md` documents the whole loop.

The archive directory (`data/archive/`) is not covered by the SQLite
backup; the runbook notes that off-machine backup of the archive is an open
operational decision for Intersect (S3 with object lock is the target), and
that leaf manifests are already pinned to IPFS at anchor time so the local
archive copy is redundancy rather than authority.

Check: `npx vitest run test/provenance/backup.test.ts` covers the
round-trip. The "restoring the backup file to the source path yields the
same head" test simulates the runbook procedure and verifies
`getLatestAnchor` matches.

## Desirable

None of these would make an anchored value wrong. They reduce the chance of
operational mistakes and improve what a verifier is told when something is off.

- A file lock in the mainnet anchoring script. Two concurrent runs both read
  the chain head before either appends, so both can submit transactions
  chaining to the same predecessor. The store catches the second append and
  rejects it, but by then both transactions are on chain and one of them is
  unrecorded. SQLite's `BEGIN IMMEDIATE` serializes the appends; it does not
  serialize the submissions, which happen earlier and outside the transaction.
  Met 2026-07-25: `acquireAnchorLock` in `src/anchor/preflight.ts` takes an
  advisory lock file (`data/.anchor-<network>.lock`) before submission and
  releases it on exit or signal. Stale locks (whose recorded pid is no longer
  alive) are automatically taken over.
- Pin `@emurgo/cardano-serialization-lib-nodejs` to an exact version rather
  than a range, since it serializes the metadata that goes on chain.
  Met 2026-07-25: package.json holds the exact `15.0.3` string, package-lock
  reflects the pin.
- Dispatch the verifier on the leaf schema tag rather than pinning it to one
  constant, so that shipping a v3 does not make every v2 anchor unverifiable by
  the current tool. The v1 preprod anchors already are.
  Met 2026-07-25: `LEAF_SCHEMA_HANDLERS` in `src/anchor/verify.ts` is the
  dispatch registry; v2 is registered and a v3 handler ships alongside the
  `/3` tag. v1 anchors remain verifiable only via `--manifest`.
- July 2026 product rename: "Cardano Regulatory Dashboard" became "Cardano
  Regulatory Evidence Portal". The on-chain schema tag prefix moved from
  `cardano-regdash` to `cardano-regportal`; the leaf schema versioned
  from /2 to /3 and the leaf-manifest schema from /2 to /3, because those
  tag strings enter the leaf preimage bytes. The anchor metadata schema
  stayed /1 because it identifies the metadata envelope shape, which did
  not change. The rename happened before any mainnet anchor existed, so
  every `cardano-regdash.*` tag on chain is preprod-only. The verifier
  keeps handlers registered for the legacy tags, so those preprod
  anchors continue to verify exactly as they did before the rename; the
  regression is locked in `test/anchor/verify.test.ts` and
  `test/anchor/metadata.test.ts`.
- Return `'unknown'` rather than `'preprod'` from `detectNetwork` in
  `src/anchor/verify.ts` when the Blockfrost base URL names neither network. A
  custom proxy URL currently gets silently reported as preprod.
  Met 2026-07-25: `detectNetwork` returns `'unknown'` for non-matching URLs;
  `VerifyDetails.network` carries it and the CLI prints it.
- Carry `network` in the manifest and cross-check it in the verifier.
  Met 2026-07-25: the manifest already stored `network`; the verifier now
  compares it to the detected network and fails when both are known and
  disagree. Manifest format did not change so no schema bump was needed.
- Run preprod anchoring continuously for at least fourteen days before starting
  mainnet, so the daily path has been exercised unattended.
- File the CIP-10 registration for label 91694. Acceptance is not needed to
  launch; filing is, because the label number is part of what the genesis
  anchor asserts.

## What this scheme proves, and what it does not

Written for publication, so a reader can judge the guarantee rather than take
it on trust.

Anchoring proves that on a stated date this portal published a specific
value for a specific metric, computed under a specific version of a stated
methodology, and that the commitment is signed and recorded in a Cardano
transaction anyone can inspect. The transaction is immutable and its contents
are publicly derivable.

It does not prove the methodology is sound. It does not prove the sources
answered truthfully. It does not prove the number reflects the true state of
the chain, only that it is what the stated methodology produced from the
sources consulted. Whether a methodology is the right one is a question the
methodology document has to answer on its own terms, and its hash is committed
here so you can find the version that applied.

When a value turns out to be wrong it is not removed. The erroneous value stays
anchored under its original transaction. A correction is a new anchored
observation naming the value it supersedes, published on the same terms. The
first real correction will look like a bug report in public, because that is
what it is.

The mechanism verifies bytes, not truth. If the manifest we pinned to IPFS
becomes unfetchable, a verifier can still check the on-chain root against any
surviving copy that hashes to the committed value. If no copy survives
anywhere, the anchor stays visible on chain but the leaves it commits to stop
being independently reconstructable. We commit to preserving the archives, and
a verifier who already holds a manifest does not have to rely on that
commitment.

The key that signs each anchor is an operational hot key. It is low value and
revocable, and rotation will itself be recorded on chain. At launch it is held
by the portal operator, so the trust root is a single organizational key
until rotation authority moves to a cross-organization multi-signature scheme.

An anchor submitted in the last day or so can still be affected by a chain
reorganization. Ouroboros Praos settles fully after roughly 3k/f slots, which
at the current parameters is about thirty-six hours, so a value verified
against a very recent anchor is worth re-checking once that window has passed.

The chain tip slot and hash recorded in a leaf are asserted by the pipeline,
not derived from the chain by the verifier. A verifier who wants to know what
the chain actually held at that slot has to check it against a Cardano node
they trust.

None of the above is a list of defects. It is what cryptographic anchoring
honestly means when the cryptography is doing exactly its part and no more.
