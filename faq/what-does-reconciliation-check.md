---
id: what-does-reconciliation-check
question: What does reconciliation actually check?
audience: [academic, regulator, skeptic]
category: sources
status: locked
last_reviewed: "2026-08-08"
---

For each reconciled metric, the pipeline pins a single chain tip, asks each source for the same quantity as of that tip, and compares the answers against the metric's declared tolerance, which is zero for lovelace-denominated quantities. The outcome is recorded: sources agreed, disagreed and resolved by a stated precedence, or disagreed unresolved. Every comparison that involved two or more sources is logged publicly with the raw readings and reading identifiers, so a disagreement is a published fact rather than a quiet correction.
