---
id: data-contract
title: "The data contract"
category: reference
audience: [builder, academic]
summary: "The schema of latest.json, field by field, with the compatibility promise for downstream consumers."
status: locked
environment_bound: true
last_reviewed: "2026-08-09"
---
Everything the site shows comes from one file: `/data/latest.json`. This page is the contract for consuming it directly.

## Top level

| Field | Meaning |
| --- | --- |
| `runId` | Identifier of the pipeline run that produced this file. |
| `network` | The network measured; `mainnet`. |
| `chainTip` | The pinned tip every read was asked against: block hash, slot, epoch. |
| `startedAt`, `completedAt` | Run timestamps, UTC. |
| `codeCommit` | Source revision the pipeline ran at. |
| `counts` | Published, unavailable, and planned metric counts. |
| `sources` | The sources read on this run. |
| `anchoring` | Anchoring status: whether anchored history has begun, first and latest anchor dates, and a plain-language statement. |
| `metrics` | The metric entries, in publication order. |

## Metric entries

Each entry carries: `id` (stable identifier; definitional variants are separate ids with a `__suffix`), `title`, `group` (concept group), `cadence`, `tier` (1, 2, or 3), `status` (`live` or `planned`), `value`, `plainLanguage` (the sentence the site renders, with the value interpolated), `methodology` and `computation` (prose), `caveats` (list), `sources` (list of source ids), `provenance` (run id, observation id, provenance hash, methodology version and its spec hash), `methodologyVersion`, `statutoryAnchor`, `history` (recent values with epoch, date, and methodology version), `breakdowns` (per-metric structured detail), `variants` and `variantLabel` where a metric has definitional siblings, and `plannedReason` or `unavailableReason` where applicable.

## Values are integers with a scale

A value is an object of `value` (a decimal integer as a string), `scale`, and `unit`. The numeric quantity is `value` times ten to the negative `scale`. Values are strings because several quantities exceed 2^53 and a default JSON parse would corrupt them silently; parse them as big integers or leave them as strings. `null` means planned or unavailable, never zero.

## Compatibility promise

Changes are additive: new fields and new metric ids may appear at any time, and consumers should ignore fields they do not recognize. Existing fields are not renamed, removed, or retyped without an announced change recorded in the changelog, and metric definitional changes never reuse an id silently; a changed definition is a new methodology version, visible in the data, and a materially different definition is a new id. Methodology version boundaries appear in each metric's history so consumers can detect definition changes mechanically.

## License and attribution

Cite the portal when republishing values, and carry the tier and reconciliation context where practical, because a bare number loses the qualifications that make it evidence. A formal license statement for the data files will be adopted by operator ruling and stated here.

## The prose bundle

The site's prose is separately available at `/content/content-bundle.json`, built from the public content repository. It carries no metric values.
