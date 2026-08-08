# Contributing

Thank you for helping keep the portal's prose accurate. This repository is the source of the website's FAQ and documentation content; a merged change here reaches the site within minutes, so the bar is accuracy, not ceremony.

## Ways to contribute

- **Something is wrong.** Open an issue with the "content bug" template: name the page, what it says, what it should say, and your source for the correction.
- **Something is missing.** Open an issue with the "content request" template: who needs it and what question it answers.
- **A methodology could be defined differently.** Open an issue with the "methodology question" template. Methodology substance is governed by the portal's methodology process; this repository holds the prose that explains it, and the issue will be routed accordingly.
- **Fix it yourself.** Open a pull request. Small, focused changes merge fastest.

## The mechanics

1. Every file has YAML frontmatter validated against the schemas in `schemas/`. Copy an existing file as a template.
2. Continuous integration runs the style lint ([STYLEGUIDE.md](STYLEGUIDE.md)), markdown lint, link checks, and frontmatter validation on every pull request. A lint failure blocks merge; the failure message names the rule.
3. Update `last_reviewed` in the frontmatter of any file you substantively edit. Typo fixes do not bump it.
4. Sign your commits with a Developer Certificate of Origin sign-off (`git commit -s`).

## Review tiers

- **Files with `status: draft`,** and cosmetic diffs (spelling, punctuation, formatting, links) to any file: one maintainer approval.
- **Files with `status: locked` and a substantive diff:** approval from the maintainer plus the domain reviewer named in [CODEOWNERS](CODEOWNERS). Locked files carry methodology-relevant or legally sensitive prose, and entries tied to a `methodology_version` need a matching entry in the methodology change log in the same pull request.
- **Recognition ledger and statutory framework prose** carry the strictest discipline: verbatim quotations verified character for character against the cited instrument, and append-only treatment where the page says so.

## What does not belong here

Metric values, pipeline code, and anything computed. The website's numbers come from the portal's data pipeline, whose provenance store is append-only and whose methodology is versioned. This repository explains; it never computes.

## License

By contributing you agree that prose contributions are licensed under CC BY 4.0 and tooling contributions under Apache 2.0, per [NOTICE](NOTICE).
