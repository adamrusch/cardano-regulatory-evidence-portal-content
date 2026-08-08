---
id: pool-clustering
title: "Stake pool clustering: methodology, error direction, maintenance"
category: methodology
audience: [academic, regulator]
summary: "How the operator-level concentration readings cluster stake pools, and what each method can and cannot detect."
status: locked
last_reviewed: "2026-08-09"
---
Cardano's saturation cap forces multi-pool operation at any scale. A single
pool stops earning rewards past roughly seventy million ADA, so an operator
running at scale is obliged to spread stake across many pools. A naive count
of pools therefore materially overstates decentralization relative to a count
of operators, and the reconciliation this portal is expected to publish
against the statute is an operator count, not a pool count.

There is no single canonical answer to "how many operators run Cardano".
Cluster boundaries depend on the identifiers you accept as evidence, and the
identifiers a scrupulous operator declares differ from the identifiers a
scrupulous operator can be forced to declare. The portal therefore
publishes three readings under distinct methodology labels and shows the gap
between them. Reading one number without the others reads out of context;
reading all three, with their disclosed methodology, is what makes the
answer honest.

This document specifies the three readings, the direction of error each
carries, the licence position for the external sources involved, and the
operational cadence for keeping the artifact current.

## The three readings

Every reading is registered as its own metric under the double-underscore
variant convention. Values across variants are never reconciled against
each other, because two numbers that answer different questions must not
travel through a numeric tolerance check.

### 1. By pool, Tier 1

Metric id: `nakamoto-coefficient-consensus__by-pool` and
`pools-above-1pct__by-pool`.

Computes the Nakamoto coefficient and the count above one percent over the
raw registered-pool population from Koios `/pool_list`. This is the
pool-level reading. It is exact, cheap, and fully reproducible from a
single source. It is also structurally uninformative about operator
concentration on Cardano, because the saturation cap keeps any pool's
stake below one percent by design. The by-pool `pools-above-1pct` figure
is expected to be zero and remains so as long as the current saturation
parameter is unchanged; nothing about that figure can be read as evidence
about operator concentration.

Direction of error: over-counts operators, under-counts concentration.

### 2. By operator, on-chain lower bound, Tier 2

Metric id: `nakamoto-coefficient-consensus__by-operator-onchain` and
`pools-above-1pct__by-operator`.

Union-find over shared reward accounts and shared owner stake credentials
from Koios `/pool_info`. Two pools merge when their `reward_addr` fields
match or when their `owners` arrays intersect. Both signals are strong
economic links: a shared reward account means one key controls the
rewards, a shared owner credential means one key signs the pledge. The
Nakamoto coefficient and the above-one-percent count are then computed
over the resulting operator groups rather than over individual pools.

This is a Tier 2 reading because we derive it ourselves from on-chain
state, and it is published as an explicit lower bound on concentration
because the derivation is deliberately incomplete. On-chain signals catch
operators who share these identifiers and miss operators who deliberately
separate them, so the direction of error is known and one-sided. Concrete
evidence for the asymmetry, checked against public multi-pool operator
lists:

- IOG runs ten pools that share a single reward account and a single DNS
  domain. Every reward signal and every relay signal groups them
  correctly, and the on-chain reading identifies IOG as one operator.
- Binance runs ten pools with ten distinct owner credentials, ten
  distinct reward accounts, and nine distinct IPv4 addresses. Every
  reward, owner, and relay signal fails. The on-chain reading identifies
  Binance as ten independent operators.

The portal therefore uses this reading only as a lower bound. The
labelling is enforced by a registry-safety test that fails if any of the
user-facing surfaces of the on-chain operator variants ships without the
phrase "lower bound".

### 3. By operator, EDI-attested, Tier 3

Metric id: `nakamoto-coefficient-consensus__by-operator-edi`.

Consumes the Edinburgh Decentralization Index's published Cardano cluster
mapping at
`mapping_information/clusters/cardano.json` in the
`Blockchain-Technology-Lab/consensus-decentralization` repository. Each
pool hash maps to a cluster identifier plus the on-chain and metadata
signals that placed it there. The mapping is applied to Koios's stake
distribution to compute the Nakamoto coefficient over operators.

The EDI clustering heuristic is published (Ovezik/Karakostas/Kiayias,
Financial Cryptography 2024, arXiv:2211.01291; see also Kiayias & Ovezik,
ACM ICAIF 2022, DOI:10.1145/3533271.3561787). It awards +3 for a shared
homepage domain, +2 for a shared normalized ticker, +2 for a shared name,
+1 for a shared description, and -1 for different valid domains; pools
merge when the score reaches 3, and a `legal_links.json` file layers in
known corporate ownership on top. Each cluster's per-pool provenance is
inspectable in the mapping file's `source` field.

Evidentiary tier is 3, not 2, because we consume EDI's execution as well
as their methodology. Self-hosting the EDI toolkit to re-derive the
mapping against our own snapshot would move this reading to Tier 2 and
is registered as a planned upgrade below.

This is the headline operator-level figure the portal publishes. When
the EDI mapping cannot be fetched, the metric renders as unavailable
with the reason; it never falls back to the on-chain lower bound,
because presenting the on-chain figure under the EDI label would defeat
the variant scheme.

Direction of error: EDI's clustering heuristic misses obscured exchange
fleets that `legal_links.json` has not yet caught. Concentration is
therefore slightly under-counted in this reading, though not as
severely as in the on-chain lower bound.

## Publish the gap

The design's honest-disclosure pattern is to show the disclosed figure,
the heuristic figure, and the gap between them. Applied here, the site
shows all three readings together on the pool-clustering panel:

- `by pool` figure from Koios, as reported.
- `by operator, on-chain lower bound` from the union-find, labelled a lower bound.
- `by operator, EDI-attested` from EDI, as the headline operator-level answer.

A short paragraph on the panel names the methodology of each, states the
direction of error, and points at this document.

## Licence and attribution

- **EDI cluster mapping** (`Blockchain-Technology-Lab/consensus-decentralization`):
  MIT for code, MIT for the mapping data, CC BY-SA 4.0 for docs. We
  archive the raw mapping bytes on every fetch, record the upstream
  commit SHA and date, and credit "Edinburgh Decentralization Index at
  the University of Edinburgh Blockchain Technology Lab" on the metric
  panel.
- **Koios**: paid tier under Koios's published terms. Every reading
  records the pinned API version and the archived response hash so a
  later verifier can re-check the value against the response as
  captured.
- **GitHub API**: anonymous rate limit is 60 requests per hour, well
  above one commits-endpoint call per pipeline run. `GITHUB_TOKEN` is
  supported for cases where the anonymous limit is exhausted.

### cexplorer.io: linked as a reader-facing cross-check, never derived from

The cexplorer.io groups page is offered as a third-party editorial view
so a reader can compare our operator groupings against an independent
one, and nothing more. The panel for each operator variant carries a
`Third-party group cross-check` breakdown row that links to
`https://cexplorer.io/groups`. Linking is not redistribution and
requires no permission. Ingesting their data would.

We do not, and cannot responsibly, derive a published value from
cexplorer for three reasons:

1. **The grouping is a website feature, not a documented API.** Their
   published developer documentation covers basics, pool primitives
   (list, hex-to-bech, detail, banned), assets, and top DeFi
   protocols. It does not document a groups endpoint, and their
   static-API host `js.cexplorer.io` does not currently resolve at
   all, so the documented catalogue is stale on top of not covering
   groups.
2. **Their methodology is not published.** No methodology page, no
   FAQ, no primary source describes how a pool is assigned to a
   group. A third-party summary states pairings are updated on the
   go, but that is not a citable primary source. Consuming an
   editorial call whose criteria are undocumented would create a
   published number whose provenance we could not explain if
   challenged.
3. **Their developer documentation prohibits HTML scraping without
   permission.** The relevant sentence is verbatim: "Please avoid
   scraping html outputs on website without written permission." We
   do not have that permission and are not seeking it, because even
   with it, a source whose methodology is undocumented and whose
   groups data is unavailable through a documented API would remain
   a Tier 3 corroboration and could never be the published
   derivation. Chasing permission for a source we would not consume
   as a derivation is not a good use of anyone's time.

The keep-the-line-sharp rule for future maintainers: link and cite
cexplorer freely, never derive a published number from them, and do
not scrape their HTML. If a documented cexplorer groups API ships in
the future with a published methodology and clear redistribution
terms, promoting them from cross-check to attested source is a
separate decision that would need Data Steward review and an
External Advisory Panel note.

## Failure modes and how they surface

The EDI mapping refreshes on a 6- to 18-month cadence upstream, so the
primary failure mode is silent staleness: a mapping that ages out will
start missing new exchange pool fleets and will begin to overstate
decentralization. Mitigations, in order of importance:

1. **Age is displayed on the metric panel.** Every publication of the
   EDI-attested reading includes the mapping's upstream commit date and
   its age in days. A reader who wants to know whether the number is
   current can see the answer without leaving the page.
2. **The metric panel flags ages beyond 180 days.** The age breakdown
   carries a note when the mapping is older than 180 days that the
   next EDI publication is overdue and a maintenance audit is
   required.
3. **A quarterly audit ships an operator diff.** The maintainer reviews
   the upstream `cardano.json` diff, the upstream `legal_links.json`
   diff, and the community-maintained
   `cardano-community/pool_groups` diff to identify new exchange
   fleets EDI has not yet clustered.
4. **The three readings sit side by side.** A reader who sees the
   EDI-attested number diverge unusually from the on-chain lower
   bound has both numbers in front of them and can ask why.

Other failure modes:

- **EDI raw fetch fails.** The metric renders as unavailable with the
  raw HTTP status in the reason. The on-chain reading is unaffected.
- **GitHub commits API fails.** The mapping age cannot be verified,
  so the EDI metric renders as unavailable. The mapping content is
  not accepted without provenance because a value published against
  an unknown mapping revision cannot be reproduced.
- **Koios `/pool_info` fails.** Both operator readings become
  unavailable, since both need `reward_addr` and `owners`.
- **A pool population drift between `/pool_list` and `/pool_info`.**
  Pools that appear in `/pool_list` but are absent from the
  corresponding `/pool_info` batch are excluded from the operator
  computation; the on-chain-metric breakdowns display the count of
  pools evaluated so a drift is visible.

## Maintenance cadence

Steady-state estimate: roughly 7 to 10 hours per month, dominated by a
quarterly audit.

**Per pipeline run (automated, zero human hours):** fetch the EDI
mapping, verify the commit hash and date, apply to the current pool
population, publish alongside the on-chain reading and the pool-level
reading. Freshness is visible on the panel.

**Per month (roughly 2 hours):** review the automated freshness page,
check the EDI upstream repository for new commits, cross-check the
value against community sources (`cardano-community/pool_groups`)
for sanity, and log any observed divergences.

**Per quarter (roughly 2 hours):** audit `legal_links.json` upstream
for new exchange fleets. Cross-reference the on-chain figure and the
EDI figure against community-tracked pool fleet lists to identify
operators the mapping has not yet caught. Where a new fleet is
identified that EDI is missing, file an issue upstream and note the
discrepancy in the source-disagreement log.

**Per year (roughly 4 hours):** re-derive the whole EDI mapping using
the `consensus-decentralization` toolkit against a fresh db-sync
snapshot to sanity-check that the upstream mapping still reflects
current on-chain reality, and confirm the licence and attribution
statements are still accurate.

## Planned upgrades

- **Self-hosted EDI toolkit re-derivation.** Running
  `consensus-decentralization` against our own db-sync snapshot and
  publishing our own re-derived mapping would move the EDI-attested
  reading from Tier 3 to Tier 2, at the cost of roughly two to three
  days of initial setup plus periodic re-runs. Scheduled after the
  node of record enters service.
- **Contribute back on drift.** When the quarterly audit identifies a
  cluster the on-chain reading detects but the EDI mapping is missing,
  filing an upstream PR to `Blockchain-Technology-Lab/consensus-decentralization`
  or `cardano-community/pool_groups` is a small effort with outsized
  benefit for the ecosystem.
- **Publish a labelled ground-truth MPO set.** Would let us publish
  honest false-positive and false-negative rates for the on-chain
  heuristic; adds roughly one to two hours per month of curation.

## Empirical anchors from the July 2026 probe

The following figures were measured against mainnet at epoch 645 with
2,693 registered pools and are the target order of magnitude the
portal's live values should reproduce.

- Pool-level Nakamoto: 160.
- On-chain lower-bound Nakamoto: 139 (13.1 percent lower than pool level).
- On-chain operator groups: 2,606 (from 2,693 pools).
- On-chain multi-pool groups: 21 covering 87 pools and 8.9 percent of
  active stake.
- On-chain operator groups above 1 percent of stake: 2.
- Largest on-chain-detectable groups: Cardano Foundation at 1.59
  percent across five pools (CF1 through CF5), NORTH at 1.45 percent,
  NUFI with thirteen pools.
- EDI-derived figures (from the 2026-06-11 mapping at the time of the
  probe): the mapping identifies 58 operator groups; Balance Analytics
  reports 25-27 including exchange fleets. The gap between the on-chain
  reading (139) and EDI's reading is the concentration that on-chain
  signals cannot see.

The Cardano Foundation appears as a named related person in the
ownership metric group. The five-pool CF fleet and the ownership
disclosure describe the same entity from two angles, and the two
readings are consistent by design.
