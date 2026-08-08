# Cardano Regulatory Evidence Portal: content

This repository holds the reader-facing prose of the [Cardano Regulatory Evidence Portal](https://portal.drep.tools): the FAQ entries, the per-metric question framings, and (in later phases) the long-form documentation pages. The portal's website draws its prose from this repository; its metric values come from the portal's own data pipeline and never from here.

The two are deliberately separate. Prose can be corrected, extended, and discussed in public through issues and pull requests on this repository, on its own release cadence, without touching the software that computes the evidence. The portal's source code lives in a separate repository that is scheduled for public release under Intersect MBO's Open Source Office; this content repository is designed to become public first.

## How content reaches the website

On every merge to `main`, continuous integration renders the markdown in this repository into a single schema-versioned artifact, `content-bundle.json`, and publishes it to the website's content delivery network. The site fetches that artifact at page load, alongside its data file. A merged correction is typically visible on the site within minutes. No website rebuild is involved.

## Repository layout

```text
faq/        one file per FAQ entry, YAML frontmatter + markdown body
metrics/    one file per metric id: the question framing shown on the FAQ page
docs/       long-form documentation pages (later phases)
assets/     images and diagrams referenced by docs
schemas/    JSON schemas for frontmatter and for the published bundle
scripts/    the bundle build script used by CI
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: open an issue with one of the templates, or open a pull request. Continuous integration enforces the [style rules](STYLEGUIDE.md) mechanically, so review can stay on substance. Substantive changes to locked files need a domain reviewer per [CODEOWNERS](CODEOWNERS); typo fixes need one maintainer.

## Licensing

Prose content (`faq/`, `docs/`, `metrics/`, `assets/`) is licensed under [Creative Commons Attribution 4.0 International](LICENSE) (CC BY 4.0). Tooling (`schemas/`, `scripts/`, `.github/`) is licensed under Apache 2.0 to match the portal's source repository. See [NOTICE](NOTICE) for the split.

## Status

Private pre-release. The repository will be made public ahead of the portal's source code, after the initial content set has been reviewed. Nothing here asserts a regulatory status for Cardano, and nothing here is a legal opinion.
