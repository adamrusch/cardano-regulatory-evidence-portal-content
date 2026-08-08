# Governance

Content governance here follows the portal's governance model, recorded in the source repository's GOVERNANCE.md and summarized in the portal's documentation. The short form:

- **Two tracks.** Prose that explains methodology, the recognition ledger, or statutory mappings follows the methodology governance track: locked frontmatter status, a domain reviewer in CODEOWNERS, and (where tagged) a matching methodology change log entry. Everything else follows the lighter code governance track: one maintainer approval.

- **Operator rulings.** Definitional judgment calls are resolved by documented operator rulings recorded in the methodology change log. Prose in this repository describes rulings; it never creates them.

- **External Advisory Panel.** Once chartered, the panel ratifies or overturns rulings by pull request, recorded as new dated entries rather than edits to what they review. Panel members are added to CODEOWNERS for the files they oversee.

- **Editors.** The founding maintainer, and the Open Source Office assigned maintainer once named, act as editors in the manner of the Cardano CIP process: named reviewers, public triage as volume justifies it, and a small enumerated set of file states (`locked`, `draft`).

Changes to this file follow the locked track.
