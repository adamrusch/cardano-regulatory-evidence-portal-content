---
id: what-does-planned-versus-live-anchoring-mean
question: What does the anchoring banner tell me?
audience: [community, regulator]
category: anchoring
status: locked
environment_bound: true
last_reviewed: "2026-10-18"
---

The banner states the current truth: mainnet anchoring is live. The first mainnet anchor, the genesis anchor, was submitted on October 18, 2026 in transaction `a08f5ce5663a25bf028121869ea649b9fc1d236b1605b95570e25d0b80846999`, and the banner gives that start date and the most recent anchor. Values for October 18, 2026 and later are verifiable against an on-chain root; values for earlier dates are traceable to their sources but were never anchored on mainnet. Before mainnet, the same machinery ran on the preprod test network from July to October 2026, including independent verification from public data alone. Those preprod anchors stay on chain and still verify, but they are test runs and not part of the record.
