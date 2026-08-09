---
id: source-disagreements
title: "The source disagreement log"
category: methodology
audience: [academic, skeptic, regulator]
summary: "Every case where independent sources answered the same question differently, published from the provenance store with raw readings and resolutions."
status: locked
environment_bound: true
last_reviewed: "2026-08-09"
---
The portal's claim is not that its numbers are correct, which nobody can promise, but that its numbers are checked, and that where checking finds a difference the difference is visible. This log is that visibility: every reconciliation involving two or more sources, published from the provenance store itself rather than from hand-maintained page copy.

Three outcomes appear. Sources agreed means the readings matched within the metric's declared tolerance, which is zero for lovelace-denominated quantities; the observed delta is reported even when it is zero, because checked-and-matched is the log's positive record. Disagreed, resolved by precedence means the tolerance did not accept the readings as agreement and the declared source precedence selected the published value, with the losing reading preserved. Disagreed, unresolved means no value was published at all; the metric shows as unavailable and the log preserves what each source said.

Single-source outcomes do not appear here, because a metric with one source has nothing to disagree with; those carry a single-source label on every surface where the value appears. Every entry names its run, its pinned chain tip, and its reading identifiers, so any entry can be traced into the provenance record and, where the source is public, re-queried.
