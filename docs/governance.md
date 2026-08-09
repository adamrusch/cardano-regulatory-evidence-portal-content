---
id: governance
title: "How the portal is governed"
category: governance
audience: [regulator, skeptic, community]
summary: "The two governance surfaces, operator rulings, the External Advisory Panel, the custody separation, and the Open Source Office relationship."
status: locked
environment_bound: true
last_reviewed: "2026-08-09"
---
The portal operates under a design ratified by the board of Intersect MBO on August 5, 2026. Governance splits into two deliberately separate surfaces: code governance decides what the software does, and methodology governance decides what the evidence means. Keeping them apart is the design's answer to the question every reader should ask of a self-published evidence site: who could bend this, and what would it cost them?

## Code governance

The repositories are maintained under Intersect's Open Source Office sponsorship, with a named maintainer. Routine changes need maintainer review; changes that alter published values or anchoring formats additionally pass through methodology governance. The prose of this site lives in a public content repository where anyone can open an issue or a pull request, with style rules enforced by automation and substantive changes gated by named domain reviewers.

## Methodology governance

Four rules, mechanical enough to check:

1. Every methodology change is a new content-hashed version with a published rationale, and every published value carries its methodology version.
2. Definitional questions with no single defensible answer are resolved by documented operator rulings, recorded in the methodology change log.
3. Metrics whose definitions remain unsettled are published as planned, with the reason stated, rather than shipped under a quietly chosen definition.
4. Corrections add to the record; nothing is edited or deleted. A correcting observation names what it corrects, and the original stays.

## The External Advisory Panel

The ratified design provides for a panel of three to five members unaffiliated with the organizations that hold anchoring custody. The panel holds methodology oversight: it ratifies or overturns operator rulings and gates content categories that require independent judgment, such as heuristic ownership figures or comparative material. Until the panel is seated, rulings carry an explicit flag that ratification is pending.

## Custody, separated from oversight

The ratified design places anchor key rotation authority under a two-of-three arrangement across Intersect, IOG, and the Cardano Foundation, so no single organization can forge or suppress the record. Those custodians hold no authority over what the record says; methodology oversight belongs to the unaffiliated panel. The organizations most invested in Cardano secure the record precisely because they cannot edit it.

## Disclosures

Engagements that could bear on the evidence are disclosed here as they take effect, including the contracted operator of the node of record, whose own stake pools appear in the portal's concentration metrics and whose contract may not depend on any value the portal publishes.
