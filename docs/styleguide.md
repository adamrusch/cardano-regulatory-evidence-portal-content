---
id: styleguide
title: "Why the portal writes the way it does"
category: reference
audience: [community, journalist]
summary: "The portal's prose rules, the reason each exists, and how they are enforced."
status: locked
last_reviewed: "2026-08-09"
---
Every sentence on this site is bound by a short set of prose rules, enforced by automation in the public content repository. The rules exist because the portal's credibility is a writing problem as much as a measurement problem: a site that puffs, hedges, or misuses terms invites the reader to discount its numbers.

## The rules and their reasons

1. **DRep is written DRep.** The term is a proper noun with fixed casing, matching CIP-1694 usage. Inconsistent casing reads as unfamiliarity with the system being measured.
2. **ADA is written ADA.** Fixed casing for the asset name, on every surface.
3. **A DRep that stops voting is inactive, never expired or retired.** Retirement is an explicit on-chain act, a certificate signed with the DRep's keys. An inactive DRep returns to active by performing an on-chain function. Conflating the states misstates the protocol.
4. **No em dashes or en dashes.** Sentences are restructured instead. A small rule with a large effect: it forces complete sentences over fragments.
5. **Headings are sentence case.**
6. **No promotional language.** Words like revolutionary or world-class fail the lint. The portal states facts and lets the reader conclude; one puffed adjective would tax every plain number around it.
7. **Quotations are exact or absent.** Quoted text reproduces the cited instrument exactly and is verified against the source; described text never wears quotation marks.
8. **The portal never asserts a regulatory status, characterizes a product as compliant, or gives legal advice.** Evidence, sources, and caveats only.

## Enforcement

The rules are code, not aspiration: the content repository's continuous integration lints every proposed change and a violation blocks the merge with a message naming the rule. Human review is saved for what automation cannot judge: accuracy and substance.
