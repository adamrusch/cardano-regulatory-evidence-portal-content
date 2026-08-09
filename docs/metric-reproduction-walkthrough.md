---
id: metric-reproduction-walkthrough
title: "Reproduce a value yourself"
category: verification
audience: [academic, skeptic, builder]
summary: "One metric taken end to end, from the public API call to the published value, so reproduction is a demonstrated procedure rather than a claim."
status: locked
last_reviewed: "2026-08-09"
---
Tier 1 means anyone can reproduce the value from a public source. This page demonstrates it once, end to end, with the treasury balance; every metric page names its own endpoints so the same procedure generalizes.

## 1. Find the pinned tip

Every published value was computed against a pinned chain tip, shown in the strip at the top of the site and carried in the data file: the epoch, slot, and block hash of the run. Note the epoch; call it `E`.

## 2. Ask the source the same question

The treasury balance reads Koios `/totals`, which reports per-epoch ledger totals in lovelace. With any HTTP client:

```text
curl -s "https://api.koios.rest/api/v1/totals?_epoch_no=E" \
  -H "accept: application/json"
```

The response includes a `treasury` field: the treasury balance in lovelace as of epoch `E`, as recorded in ledger totals.

## 3. Compare against the published value

Open the treasury balance metric page. The published value is an integer lovelace amount with scale zero; the site renders it in ADA. Divide the lovelace figure by one million to compare in ADA, or compare the raw integers directly against the data file's entry.

## 4. Understand a near miss

If your figure differs slightly, check three things before concluding error. First, the epoch: the portal reads the pinned epoch, and asking for the current epoch mid-way gives a different number. Second, liveness: some quantities move continuously, and two reads moments apart can differ by small amounts; when the portal's own sources disagree this way, the disagreement is published and resolved by declared precedence rather than hidden. Third, the methodology version: the metric page states exactly what is computed, and a definitional difference between your query and the portal's is a methodology conversation, not a discrepancy.

## 5. Cross-check on the public witness

The reconciled metrics also publish the SQL behind their Dune readings, re-runnable by anyone with a free Dune account, so the same quantity can be checked against infrastructure the portal's primary source does not operate. See the Dune queries document.

## What this proves, and what it does not

Reproducing a value proves the portal read the public source honestly. It does not prove the source itself is right; that is what reconciliation across independent sources is for, and once anchored history begins, the chain commitment proves the value has not been rewritten since publication. The three checks compose: reproduction, reconciliation, anchoring.
