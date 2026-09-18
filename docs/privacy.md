---
id: privacy
title: "Privacy"
category: reference
audience: [regulator, journalist, community, skeptic]
summary: "What the portal collects about its readers: nothing. No cookies, no analytics, no tracking scripts, and no reader logging on the draft host."
status: locked
environment_bound: true
last_reviewed: "2026-09-18"
---
## The short version

The portal collects nothing about you. It sets no cookies, loads no analytics or tracking scripts, embeds nothing from third parties, and the draft host keeps no access logs of readers. There is no account, no form that stores what you type, and no cookie banner because there are no cookies to consent to.

## What the site does and does not do

The site is a static page served from a content delivery network. When you open it, your browser fetches the page, the published data file, and the reviewed prose bundle from that network, and nothing else. The content security policy shipped with every response forbids the page from loading scripts from anywhere but the site itself, so no advertising, analytics, or social widget can run even by accident.

The verify page is the one part of the site that talks to other services, and it does so only when you ask it to. To check a value it fetches transaction metadata from the public Koios API through the portal's own relay, and the anchored manifest from the portal's mirror or a public IPFS gateway. Those requests carry the transaction hash and manifest identifier you are checking and nothing about you beyond what any web request carries. The relay accepts only the two calls the verifier needs, forwards no cookies or identifying headers, and is rate limited. If you prefer not to touch the portal's infrastructure at all, the verify page shows the command that performs the same check from your own machine against public services only.

## Logging

On the draft host, access logging is switched off on both the content delivery network and the storage behind it, deliberately: a regulator, journalist, or community member reading the record should not leave a trace with the record's publisher. The production operator may enable standard server-side access logs for operational reasons. If that happens, this page will say so, state what is logged and for how long, and confirm that no script-based tracking has been added.

## Data about the network, not about people

Everything the portal publishes is a measurement of the public Cardano ledger: block production, stake, treasury flows, governance participation. Where measurements describe stake pools or delegated representatives, they use the on-chain identifiers those participants registered publicly. The portal does not attempt to link on-chain identifiers to natural persons, and it publishes no data about individuals.

## Questions

Questions about this page go to the contact listed for the portal on the press page.
