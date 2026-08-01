# Contributing

The most valuable contribution to this project is **telling it when it is wrong.**

A tool that reports software support status is worth exactly as much as its accuracy. A confidently
wrong answer is worse than no answer, because someone may act on it. So corrections are treated as
higher priority than features.

## What is most useful, in order

1. **False matches** — the tool resolved your input to the wrong product, or reported dates that do
   not match the vendor's own notice. **This is the most serious class of bug.** A shipped example:
   `jquery-file-upload` matched jQuery and reported jQuery's lifecycle. Please report these even if
   you are not certain.
2. **Missing technologies** — something you actually run that the tool does not recognise. Include
   how you would naturally type it, since alias handling is often the real gap.
3. **Logic disputes** — cases where you think the severity rules in
   [`src/severity.py`](src/severity.py) produce the wrong answer. Disagreement about where the
   90/365-day boundaries sit is legitimate and worth arguing.
4. **Bugs** — anything else.

## Reporting

Use the issue templates. They ask for what you typed, what you got, and what you expected — those
three things resolve most reports immediately.

If you are reporting a false match, a link to the vendor's own end-of-life page is the single most
helpful thing you can include.

## Code changes

The severity classifier is the part most worth scrutiny. If you change it:

```bash
cd src && python3 -m unittest severity_test -v
```

All tests must pass. Please add a test for whatever you changed — two of the existing tests are
regressions from bugs found in real use, and that is the standard.

Keep the design rules intact:

- **Severity is derived, never invented.** No scoring models, no heuristic risk numbers. Every
  classification must trace to a published date or a dated event.
- **`unknown` must never be reported as `clear`.** Absence of evidence is not evidence of safety.
- **Recorded events can raise severity, never lower it.**
- **Understate time remaining rather than overstate it** when rounding.

## Data corrections

If a *date* is wrong, it is most likely wrong at the source. Please report it to
[endoflife.date](https://github.com/endoflife-date/endoflife.date) — they maintain the lifecycle
data and deserve both the correction and the credit. Open an issue here too if the tool is
misrepresenting data that is correct upstream.

## Scope

This repository covers the tool, its severity logic, and sample data. The full event archive, the
collection pipeline, and the hosted service are not part of it. Issues about the tool's accuracy
and behaviour are in scope; requests to open-source the archive are not.

## Conduct

Be straightforward and assume good faith. Reports that a result is wrong are welcome and will not be
argued with reflexively — if you are right, the fix ships and the changelog says so.
