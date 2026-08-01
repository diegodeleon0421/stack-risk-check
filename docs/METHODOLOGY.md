# Methodology

How results are produced, written so you can judge the data rather than trust it.

## How automation is used

Collection, extraction and publishing run automatically once a day. A scheduled job queries public
APIs for new announcements, extracts the product name from each headline, rebuilds the index, runs
a technical audit, and deploys **only if that audit passes**.

**No text in a result is written by a language model.** Every sentence the tool produces is either a
fixed template, a field from a dated record, or a verbatim quote with a link to its source. This is
deliberate: a generated explanation of a compliance-relevant date is a liability, not a feature.

## The three inputs

**1. Version support dates** come from [endoflife.date](https://endoflife.date), an open
community-maintained dataset that cites vendor announcements. Each product's record supplies its
release cycles, release dates, end-of-life dates and LTS flags. This project is a reader of that
dataset and links back to it on every result.

**2. Shutdown and transition announcements** are discovered through the public Hacker News search
API. A headline is archived when it matches a shutdown, end-of-life, deprecation, acquisition,
pricing-change, breach or layoff pattern. Only the headline, date, submitted link and public comment
metadata are stored.

**3. Archived repositories** come from the public GitHub REST API — projects their own maintainers
marked archived, above a popularity threshold, because an abandoned hobby repository is not a vendor
event. This is first-party evidence: the maintainer flipped the switch, with a date.

## Product-name extraction

Headlines are matched against structural patterns (`X is shutting down`, `Sunsetting X`,
`X reaches end of life`, and others), then validated to reject sentence fragments and generic nouns.

Two rules exist because both were learned from real failures:

- **Transitive patterns win.** *"OpenAI is shutting down Atlas"* must yield **Atlas**, not OpenAI.
  A page about the parent company is both wrong and useless.
- **Precision over recall.** Roughly 28% of archived headlines yield a confident product name. The
  rest are discarded rather than guessed at. A smaller correct dataset beats a larger wrong one.

## Matching your input

1. Exact match against a product key
2. Alias lookup (`node` → `nodejs`, `k8s` → `kubernetes`, `postgres` → `postgresql`, …)
3. Slugified match
4. Unique prefix match, **only** in the direction *key-starts-with-input*

Step 4's direction is load-bearing. The reverse — allowing an input longer than the key to match it
— shipped as a bug where `jquery-file-upload` matched `jquery` and reported the wrong lifecycle.
Matching an input to a *different project* is worse than returning nothing, so the looser direction
is gone.

If a version is supplied, it is matched against that product's tracked release cycles. If the
version is unknown, the product-level position is reported **and the report says so**.

## Severity

See the [severity table in the README](../README.md#how-severity-is-calculated) and the reference
implementation in [`src/severity.py`](../src/severity.py).

The rule behind the rules: **severity is derived, never invented.** No scoring model, no weighting,
no "risk score" that cannot be traced back to a published date or a dated event.

## What is deliberately not done

- **Nothing is scanned or discovered.** The tool reports on the versions you type. It has no access
  to your infrastructure and asks for none.
- **No alternatives are recommended.** Where the archive records replacements, they are verbatim
  quotes from named public commenters, linked to the source, ordered only by how often each was
  mentioned. That is a record of what people said, not advice.
- **No severity is assigned to `unknown`.** It stays `unknown`.

## Known biases

- **Coverage follows where announcements happen.** Languages, databases, infrastructure and
  developer tooling are well covered; **business SaaS is badly under-covered**, because its
  shutdowns are announced in customer emails rather than in public.
- **Products that never publish end-of-life dates are invisible** to lifecycle analysis entirely —
  not "clear", simply absent.
- **Absence from the archive means nothing was detected**, not that nothing happened.
- **Dates are re-published**, so they are only as current and correct as the upstream source.

## Corrections

Errors are fixed on report and the underlying record is kept rather than quietly deleted, so the
archive does not develop convenient gaps. False matches are treated as the most serious class of
bug. See [CONTRIBUTING.md](../CONTRIBUTING.md).
