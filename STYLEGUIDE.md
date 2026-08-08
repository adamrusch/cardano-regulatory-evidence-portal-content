# Style guide

These rules bind every prose file in this repository. Continuous integration enforces the mechanical ones; a pull request that violates them fails at the lint step with a message naming the rule. The reasons are recorded here so a contributor whose change is rejected can see why the rule exists.

## The rules

1. **Write "DRep", never "dRep", "Drep", or "DREP".** The portal treats the term as a proper noun with fixed casing, matching CIP-1694 usage.

2. **Write "ADA", never "Ada" or "ada".** Fixed casing for the asset name on every surface.

3. **A DRep that has stopped voting is "inactive", never "expired" or "retired".** Retirement is an explicit on-chain act: a retirement certificate signed with the DRep's keys. A DRep that merely stops voting becomes inactive and returns to active by performing an on-chain function. Conflating the states misstates the protocol, so the distinction is enforced as terminology.

4. **No em dashes and no en dashes.** Use commas, semicolons, colons, or restructure the sentence. Hyphens in compound words are fine.

5. **Sentence case for headings.** "How the pipeline works", not "How The Pipeline Works".

6. **No promotional language.** Words like "revolutionary", "world-class", "leading", "unmatched", "cutting-edge" fail lint. The portal states facts and lets the reader conclude; puffery would undercut every factual claim around it.

7. **Quotation discipline.** A quotation from a statute, rule, release, or other instrument must reproduce the published text exactly and be verifiable against a cited source. If the text is described rather than quoted, it must not sit inside quotation marks. When in doubt, paraphrase and say so.

8. **State what the portal is not.** Prose must never assert a regulatory status for Cardano, characterize any builder's product as compliant, or offer a legal opinion. Evidence, sources, and caveats only.

## Length discipline for FAQ entries

A FAQ answer is one to two short paragraphs. If a serious answer needs more, the FAQ entry carries a summary and points at a long-form documentation page, and the substance lives there.

## Enforcement

The `.vale/styles/RegulatoryPortal/` directory implements rules 1 through 6 as Vale checks; `markdownlint` enforces markdown structure; frontmatter is validated against the schemas in `schemas/`. Rules 7 and 8 are review criteria applied by the maintainers and, where designated, domain reviewers in CODEOWNERS.
