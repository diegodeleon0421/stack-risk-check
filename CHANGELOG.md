# Changelog

Notable changes to Stack Risk Check. Accuracy fixes are listed first because they matter most.

The format is loosely [Keep a Changelog](https://keepachangelog.com/). Dates are UTC.

## [0.1.0] — 2026-08-01

First public release of the tool and its severity logic.

### Added
- Stack Risk Check: paste up to 25 technologies, get severity-ranked results with a source link on
  every factual line. Runs entirely client-side.
- Severity classification (`urgent` / `upcoming` / `watch` / `clear` / `unknown`) derived from
  published dates and dated events only.
- Reference implementation in `src/severity.py` with a test suite.
- Sample lifecycle and event data for reproducing results.
- Aliases so common shorthand resolves correctly (`node`, `k8s`, `postgres`, and others).
- Shareable result links containing only the names entered.

### Fixed
These shipped as real bugs and were caught in testing. Each now has a regression test.

- **False match: `jquery-file-upload` resolved to `jquery`** and reported jQuery's lifecycle. A
  loose prefix rule allowed an input longer than the key to match it. Prefix matching is now
  restricted to the key-starts-with-input direction only. This was the most serious class of bug
  the tool can have — a confidently wrong answer.
- **`localstack` returned `unknown`** despite being in the archive. Product-name extraction required
  a capital letter, which excluded lowercase repository names. Archived-repository events now carry
  their repository name directly; the index grew from 765 to 984 products.
- **Negative day counts.** A cached end-of-life date that had since passed displayed as
  `-1 days from today`. Past dates now report as *"reached end of life on «date»"*.
- **Timezone-dependent day counts.** Day arithmetic is now normalised to UTC midnight on both sides
  and floored, so results do not shift with the visitor's timezone or hour of day. Flooring
  understates time remaining, which is the safe direction for a deadline.

### Known limitations
See the [README](README.md#known-limitations). The short version: coverage is weak for business
SaaS, `unknown` means not found rather than safe, and this is not compliance advice.
