#!/usr/bin/env python3
"""Reference implementation of Stack Risk Check severity classification.

This is the same logic the live tool runs in the browser, written in Python so it can be read,
tested and disputed. If the tool ever disagrees with this file, the tool has a bug — please open
a false-match report.

The design rule that matters most: **severity is derived, never invented.** Every classification
traces to a published date or a dated event. There is no scoring model, no heuristic "risk score",
and no judgement call. An input we cannot resolve is reported as `unknown`, never as `clear` —
absence of evidence is not evidence of safety, and conflating the two is the single most damaging
mistake a tool like this can make.

Run the tests:  python3 -m unittest src.severity_test
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

# Windows chosen to match how teams actually plan: a quarter is "schedule it now", a year is
# "put it on the roadmap", beyond that is routine.
UPCOMING_DAYS = 90
WATCH_DAYS = 365

SEVERITIES = ("urgent", "upcoming", "watch", "clear", "unknown")

# Event categories that mean the product itself is ending, not just one release.
TERMINAL_EVENTS = {"shutdown", "eol"}
# Event categories that raise concern without being terminal.
RISK_EVENTS = {"acquired", "breach", "pricehike", "layoff"}


@dataclass
class Result:
    query: str
    severity: str
    product: str | None = None
    version: str | None = None
    eol_date: str | None = None
    days_remaining: int | None = None
    facts: list[str] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    source: str | None = None


def days_until(eol: str, today: date | None = None) -> int:
    """Whole days from today until `eol`, in UTC terms.

    Deliberately floored rather than rounded: understating time remaining is the safe direction to
    be wrong about a compliance deadline.
    """
    today = today or datetime.utcnow().date()
    return (date.fromisoformat(eol) - today).days


def classify(product: dict | None, version: str | None, query: str,
             today: date | None = None) -> Result:
    """Classify one technology.

    `product` is a record from the index (see data/sample-lifecycles.json for the shape), or None
    when the input could not be resolved.
    """
    today = today or datetime.utcnow().date()

    if product is None:
        return Result(query=query, severity="unknown", version=version, facts=[
            "Not found in the dataset. This means nothing was found — not that it is safe."])

    name = product.get("product", "").replace("-", " ")
    events = product.get("events", [])
    res = Result(query=query, severity="clear", product=name, version=version,
                 source=product.get("source"), events=events)

    cycle = None
    if version:
        for c in product.get("cycles", []):
            if str(c.get("cycle")) == str(version):
                cycle = c
                break

    if cycle:
        eol = cycle.get("eol_date")
        if cycle.get("dead"):
            res.severity = "urgent"
            res.eol_date = eol
            res.days_remaining = days_until(eol, today) if eol else None
            res.facts.append(
                f"{name} {version} passed end of life on {eol} and no longer receives "
                f"security patches.")
        elif eol:
            n = days_until(eol, today)
            res.eol_date, res.days_remaining = eol, n
            if n < 0:
                res.severity = "urgent"
                res.facts.append(f"{name} {version} reached end of life on {eol}.")
            elif n <= UPCOMING_DAYS:
                res.severity = "upcoming"
                res.facts.append(f"{name} {version} loses support on {eol} — {n} days remaining.")
            elif n <= WATCH_DAYS:
                res.severity = "watch"
                res.facts.append(f"{name} {version} loses support on {eol} — {n} days remaining.")
            else:
                res.severity = "clear"
                res.facts.append(f"{name} {version} is supported until {eol} ({n} days).")
        else:
            res.facts.append(f"{name} {version} has no published end-of-life date.")
    else:
        # No version given, or a version we do not track: report the product-level position.
        nxt = product.get("next_eol")
        if version:
            res.facts.append(
                f"Version {version} is not in the tracked release list for {name}; the "
                f"product-level position is reported instead.")
        if nxt:
            n = days_until(nxt, today)
            res.eol_date, res.days_remaining = nxt, n
            if n < 0:
                res.severity = "urgent"
                res.facts.append(
                    f"{name} {product.get('next_eol_cycle')} reached end of life on {nxt}.")
            elif n <= UPCOMING_DAYS:
                res.severity = "upcoming"
            elif n <= WATCH_DAYS:
                res.severity = "watch"
            else:
                res.severity = "clear"
            if n >= 0:
                res.facts.append(
                    f"The next {name} release to lose support is "
                    f"{product.get('next_eol_cycle')} on {nxt} — {n} days remaining.")
        elif not product.get("cycles") and not events:
            res.severity = "unknown"
            res.facts.append("No lifecycle data and no recorded events for this product.")
        else:
            res.facts.append(f"No upcoming end-of-life date is published for {name}.")

    # Recorded events can only ever RAISE severity, never lower it.
    categories = {e.get("category") for e in events}
    if categories & TERMINAL_EVENTS:
        res.severity = "urgent"
        res.facts.append(
            "A shutdown or archival event is on record for this product — see the linked sources.")
    elif (categories & RISK_EVENTS) and res.severity == "clear":
        res.severity = "watch"
        res.facts.append(
            "An acquisition, breach or pricing-change event is on record for this product.")

    return res


if __name__ == "__main__":
    import json
    import pathlib

    data = json.loads((pathlib.Path(__file__).parent.parent /
                       "data" / "sample-lifecycles.json").read_text())
    index = {p["product"]: p for p in data["products"]}
    for q, ver in [("python", "3.9"), ("postgresql", "14"), ("kubernetes", "1.28"),
                   ("nodejs", "18"), ("frobnicator", None)]:
        r = classify(index.get(q), ver, f"{q} {ver or ''}".strip())
        print(f"[{r.severity:<8}] {r.query:<20} {r.facts[0] if r.facts else ''}")
