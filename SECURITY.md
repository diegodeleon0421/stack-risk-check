# Security Policy

## Reporting a vulnerability

Please report security issues privately using GitHub's
[private vulnerability reporting](../../security/advisories/new) rather than opening a public issue.

You should get an acknowledgement within a few days. This is a single-person project, so please do
not expect a same-day response — but you will get one.

## Scope

**In scope**

- The hosted tool at `https://shutdown-radar.pages.dev`
- Any issue where the tool could cause a visitor's browser to execute untrusted content
- Any way the site could leak visitor data — the tool is specifically designed so that what you
  type never leaves your browser, and a flaw in that guarantee is a genuine vulnerability
- Code in this repository

**Out of scope**

- Reports that a support date or severity result is *incorrect* — those are accuracy bugs, not
  security issues. Please use the [false-match template](../../issues/new?template=false-match.yml)
- Missing security headers with no demonstrated impact
- Findings from automated scanners without a working proof of concept
- Denial of service against a free static site
- Social engineering

## What this project stores

Deliberately very little, which limits what a breach could expose:

- The check runs client-side. **Technologies entered into the tool are never transmitted.**
- No cookies, no localStorage, no fingerprinting, no advertising, no cross-site identifiers.
- Anonymous counters only: that an event happened and on which page. No visitor identifier exists,
  by design.
- Email addresses are stored **only** for people who explicitly submitted the alerts form, and are
  never sold, shared, or used for anything but the emails they asked for.

## Safe harbour

If you make a good-faith effort to comply with this policy while researching an issue, this project
will not pursue action against you. Please do not access or modify data belonging to others, and
please give a reasonable window to fix an issue before disclosing it publicly.
