---
id: reeve-attestation-request
title: "Monthly ADA holdings attestation via Reeve: request specification"
category: reference
audience: [regulator, community]
summary: "The request specification for monthly ADA holdings attestations from the Cardano Foundation and Cardano Development Holdings via Reeve."
status: locked
last_reviewed: "2026-08-09"
---
Prepared July 31, 2026, for outreach to the Cardano Foundation and to Cardano
Development Holdings. This document specifies what each entity is asked to
publish, why the portal asks for it in this form, and how the Cardano Regulatory
Evidence Portal will consume it. Intersect MBO appears here only as the
beneficiary of the CDH trust and as the channel through which the CDH request
travels; the publishing entities are CF and CDH themselves. It is written to
accompany the requests; it is not itself the letter.

## What is being asked, in one paragraph

Each entity publishes, monthly, an on-chain Reeve report stating its ADA
holdings at month end, attested under CIP-170, accompanied by a signed registry
of the addresses backing those holdings. The portal ingests the report directly
from chain metadata, verifies the attestation, reconciles the stated balance
against the registered addresses through independent queries, and displays the
result with full provenance. Nothing is asked that either entity would need to
keep private: the request is that holdings already reported in aggregate become
verifiable rather than only stated.

## Why Reeve, and why this form

The Cardano Foundation already publishes monthly balance sheets through Reeve
under metadata label 1447, with a Grant Thornton attestation on the 2025 annual
figures. That practice anchors the report itself to the chain, which makes it
tamper evident. What it does not yet do is make the ADA figure verifiable: the
published balance sheet is denominated in Swiss francs, and no on-chain link
exists between a Reeve entry and the wallets holding the assets. A reader can
know what was said, but cannot check it.

The two additions requested close that gap. An ADA-denominated holdings line
makes the quantity explicit rather than implied by a valuation. The address
registry makes the quantity checkable by anyone running a node or querying any
independent indexer. Together they move the figure from attested to verifiable,
which is the difference the portal's evidentiary tiers exist to mark.

## Shared requirements, both entities

1. Cadence: monthly, published within ten days of month end. The portal
   displays the report date and flags staleness when a month is missed.
2. Content: a Reeve REPORT payload carrying an ADA-denominated holdings figure
   at month end, in lovelace or ADA with the unit stated, alongside whatever
   fiat valuation the entity ordinarily reports.
3. Identity: a CIP-170 attestation chain on each publication, so the portal and
   any third party can verify the publisher cryptographically rather than by
   address reputation.
4. Address registry: a signed list of the mainnet stake addresses or payment
   addresses backing the reported holdings, published on chain or at a stable
   location whose hash is carried in the report. The registry is what permits
   independent verification; without it the figure remains attestation only.
5. Stability: a stable Reeve organisation identifier per entity, and notice
   through the same channel if the schema version or publishing address changes.

## Cardano Foundation specifics

The Foundation's existing monthly practice already satisfies the cadence
requirement. The request reduces to three additions: the ADA-denominated line,
the CIP-170 attestation on each monthly report rather than only on annual
figures, and the address registry. The Foundation's holdings are reported here
as evidence concerning a genesis-allocated related person; the portal presents
the figure with that statutory context and with the Foundation named as the
attesting party.

## Cardano Development Holdings specifics

CDH does not publish through Reeve today, so the request is adoption, not
adjustment. Beyond the shared requirements:

1. Two account classes, separately stated. The endowment held in trust for
   Intersect MBO and the custodial funds administered for Cardano projects
   under their treasury withdrawal governance actions are different things
   under an ownership analysis. Each monthly report states them as separate
   lines, and the address registry identifies which addresses back which class.
   The portal will display the endowment as a beneficial position and the
   custodial pool as administered funds, never summed without that distinction.
2. Identity feasibility. CIP-170 identity rests on a vLEI credential chain.
   Whether a Cayman entity can obtain a vLEI through the current GLEIF
   qualified issuers is unconfirmed and should be resolved early, since it
   gates the attestation requirement. If vLEI issuance proves unavailable, the
   fallback is publication from a declared address whose control is attested in
   writing by Intersect, at a lower evidentiary tier, until the identity chain
   becomes available.
3. Custodial itemization. The custodial line should reference the governance
   actions under which funds are administered, so the portal can cross-link the
   figure to the on-chain treasury withdrawals it already tracks and no reader
   double counts treasury and custody.

## How the portal consumes the publications

The portal adds a Reeve source adapter following its existing source
conventions: it reads label 1447 payloads from the registered publishing
addresses through independent APIs, verifies the CIP-170 attestation, archives
the raw payload content addressed, and records a source reading like any other.
The stated holdings reconcile against live balance queries over the registered
addresses, and the reconciliation outcome is published with the metric. An
attested figure that matches its addresses displays as verified; a figure whose
addresses cannot be confirmed displays as attested only, with the difference
explained. Until either entity publishes, the corresponding line on the portal
is maintained by manual quarterly curation with the publication plan stated,
so the interim is visible rather than silent.

## What this is not

The request does not ask either entity to disclose transaction level detail
beyond what Reeve ordinarily carries, to change custody arrangements, or to
assert any regulatory status. It asks that figures already reported in
aggregate be published in a form that permits independent verification, which
is the standard the portal applies to itself.
