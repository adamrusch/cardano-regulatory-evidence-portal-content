---
id: dune-queries
title: "Dune as second source"
category: methodology
audience: [academic, builder]
summary: "The validated SQL behind every Dune-sourced reading, re-runnable by anyone with a free account."
status: locked
last_reviewed: "2026-08-09"
---
Validated July 25, 2026 against Dune's first-party Cardano tables at mainnet
epoch 645. Every query below was executed and returned the result shown, so
this is a record of what works rather than a set of drafts.

Dune's role in the design is the public witness: the place where anyone with a
browser and an account can re-run the same SQL and get the same number. It is
not the canonical source. That role belongs to the node of record once it is in
service, and until then every Dune figure carries the same single-source or
two-source labeling as everything else.

## Access

The API key on this project can create and execute queries programmatically,
which the audit had left uncertain. Creating a private query and executing it
returns results in a few seconds for all the queries below.

Dune's Cardano tables are current. At the time of validation `adapot` and
`drep_dist_enriched` carried epoch 645, matching Koios, and `epoch_stake`
carried 644. Indexer lag is therefore not the obstacle the audit anticipated,
though it still has to be handled: the pipeline pins one chain tip and asks
both sources for the same epoch, and a metric whose epoch is missing from one
source is reported as unavailable from that source rather than silently taken
from the other.

## A parsing hazard worth knowing before writing the adapter

Dune returns `adapot` amounts as JSON strings but returns
`drep_dist_enriched.amount` as a bare JSON number. Those amounts exceed 2^53:
the always-abstain option alone held 9418104373206017 lovelace at epoch 645. A
default JSON parse maps that to an IEEE 754 double and corrupts it silently.

The adapter must either cast to `VARCHAR` in the SQL, which is what the queries
below do, or parse the response from raw text. Casting in SQL is preferred,
because it makes the guarantee visible in the query a third party re-runs
rather than hiding it in our client code.

## Queries that reconcile exactly against Koios

These three agreed with Koios to the lovelace, with no tolerance required.

Treasury balance, epoch fees, and supply aggregates:

```sql
SELECT CAST(treasury AS VARCHAR)    AS treasury,
       CAST(fees AS VARCHAR)        AS fees,
       CAST(circulation AS VARCHAR) AS circulation
FROM cardano.adapot
WHERE epoch = {{epoch}}
```

At epoch 645 this returned treasury 1473763718394011 and fees 58933613436,
both identical to Koios `/totals`. The `circulation` field is NOT comparable to
Koios's field of the same name; see the source disagreement log.

Total stake under DRep delegation, with the breakdown that resolves the DRep
counting question:

```sql
SELECT drep_type,
       CAST(COUNT(*) AS VARCHAR)                              AS n,
       CAST(SUM(CAST(amount AS DECIMAL(38,0))) AS VARCHAR)    AS total
FROM cardano.drep_dist_enriched
WHERE epoch = {{epoch}}
GROUP BY drep_type
```

At epoch 645: ADDR_KEYHASH 883 representatives holding 5240054873340683,
SCRIPTHASH 10 holding 130062251385534, ABSTAIN 1 holding 9418104373206017, and
NO_CONFIDENCE 1 holding 176451764046729. The four totals sum to
14964673261978963, exactly matching Koios `/drep_epoch_summary.amount`.

The `drep_type` column is what makes this query more useful than the Koios
equivalent: it separates the two predefined ballot options from actual
representatives, which is the distinction the active DRep count depends on.

## Consensus decentralization, and why it is not reconciled yet

```sql
WITH pool_stake AS (
  SELECT pool_hash, SUM(CAST(stake_lovelace AS DECIMAL(38,0))) AS stake
  FROM cardano.epoch_stake
  WHERE epoch = {{epoch}}
  GROUP BY pool_hash
),
tot AS (SELECT SUM(stake) AS total FROM pool_stake),
ranked AS (
  SELECT p.pool_hash, p.stake,
         SUM(p.stake) OVER (ORDER BY p.stake DESC, p.pool_hash) AS running,
         t.total
  FROM pool_stake p CROSS JOIN tot t
)
SELECT CAST(COUNT(*) AS VARCHAR) AS n_pools,
       CAST((SELECT COUNT(*) FROM ranked WHERE running - stake < total / 2) AS VARCHAR) AS nakamoto,
       CAST((SELECT COUNT(*) FROM ranked WHERE stake * 100 > total) AS VARCHAR) AS above_1pct,
       CAST(MAX(total) AS VARCHAR) AS total_stake
FROM ranked
```

At epoch 644 this returned 2845 pools with stake, a Nakamoto coefficient of
160, zero pools above one percent, and total stake 21399646274908035.

Zero pools above one percent is a real result rather than a query bug. Cardano's
saturation parameter caps a pool's rewards past roughly 70 million ADA, which at
current total stake is about a third of one percent, so the metric is measuring
a threshold no pool has an incentive to cross. That is worth saying plainly on
the metric's page, because a regulator reading "0" without explanation will
assume the number is broken.

This query is not yet reconciled against Koios, and the reason is a genuine
alignment problem rather than a disagreement. Cardano maintains three stake
snapshots at any time, conventionally called Mark, Set, and Go, which lag each
other by an epoch and serve different purposes: Go determines current block
production rights, while Mark is the snapshot still being accumulated. Koios's
`pool_list.active_stake` and Dune's `epoch_stake` at a given epoch number do
not obviously refer to the same one of the three. Dune's total at epoch 644 was
21399646274908035, which is closest to the Mark snapshot Koios reports for epoch
646 rather than to either snapshot Koios labels 644.

Reconciling these before establishing which snapshot each source means would
produce either a false disagreement or a tolerance wide enough to be
meaningless. The pipeline therefore treats consensus decentralization as
single-source from Koios for now, and the snapshot question is the first item
to settle when the node of record enters service, since db-sync exposes all
three snapshots explicitly and can adjudicate.

## What Dune unlocks that Koios cannot answer

Two metrics currently marked planned become computable with Dune, and both are
worth doing next session rather than this one:

Active address count has a direct path through `cardano.tx_input` and
`cardano.address_utxo`, aggregating distinct addresses per epoch. This is the
kind of whole-chain aggregation Koios cannot serve and Dune is built for.

Smart contract transaction share has a direct path through
`cardano.transaction_scripts` joined against `cardano.transaction`. Dune also
carries a `smart_contract_registry` table that may make the dApp inventory
group tractable earlier than the plan assumes.

Neither is implemented yet, and both stay marked planned until they are, since
a metric described as available in a document but absent from the portal is
the same failure as one that is silently missing.
