#!/usr/bin/env python3
"""Extract the VENDOR from an event title, and reject everything that isn't a real product.

This is the quality gate for the whole corpus. The failure mode it exists to prevent: general HN
news ("NIMBYs aren't just shutting down housing") producing a page titled "NIMBYs alternatives"
listing "Leaf Blowers". Thin, wrong pages get the whole domain deindexed, which would destroy the
90-day channel test before it starts.

Bias: precision over recall. A smaller correct corpus beats a large wrong one, and the cron adds
~100 events/month forever.
"""
from __future__ import annotations

import re

# "Parent is shutting down Product" — the page must be about the PRODUCT that died, not its owner.
# A page titled "OpenAI alternatives" because OpenAI killed Atlas is both wrong and unrankable.
# These run FIRST and their group 2 wins.
TRANSITIVE = [
    r"^.{2,34}?\s+(?:is|are)\s+shutting\s+down\s+(?:its\s+|the\s+)?(.{2,42}?)$",
    r"^.{2,34}?\s+(?:will\s+)?shut(?:s)?\s+down\s+(?:its\s+|the\s+)?(.{2,42}?)$",
    r"^.{2,34}?\s+is\s+(?:discontinuing|deprecating|sunsetting|killing|retiring)\s+(?:its\s+|the\s+)?(.{2,42}?)$",
    r"^.{2,34}?\s+(?:announces|announced)\s+end\s+of\s+life\s+for\s+(.{2,42}?)$",
]

# Structural patterns. Group 1 is the vendor.
PATTERNS = [
    r"^(.{2,42}?)\s+(?:is|are|will\s+be)\s+shutting\s+down",
    r"^(.{2,42}?)\s+(?:is|are)\s+(?:being\s+)?(?:discontinued|deprecated|sunset)",
    r"^(.{2,42}?)\s+shuts?\s+down",
    r"^(.{2,42}?)\s+(?:has|have)\s+shut\s+down",
    r"^(.{2,42}?)\s+will\s+shut\s+down",
    r"^(.{2,42}?)\s+is\s+winding\s+down",
    r"^(.{2,42}?)\s+(?:has\s+been|is\s+being|to\s+be)\s+acquired",
    r"^(.{2,42}?)\s+(?:is|are)\s+raising\s+prices",
    r"^(.{2,42}?)\s+price\s+increase",
    r"^(.{2,42}?)\s+end\s+of\s+life",
    r"^(.{2,42}?)\s+reaches\s+end\s+of\s+life",
    r"^Sunsetting\s+(.{2,42}?)$",
    r"^Winding\s+[Dd]own\s+(.{2,42}?)$",
    r"^Deprecating\s+(.{2,42}?)$",
    r"^Shutting\s+down\s+(.{2,42}?)$",
    r"^(.{2,42}?)\s+is\s+shutting\s+down",
    r"^(.{2,42}?)\s+is\s+no\s+longer",
]

# Titles that are news/politics/hardware/media, not a software vendor event.
REJECT_TITLE = re.compile(
    r"(?i)\b(nimby|housing|congress|senate|court|lawsuit|election|climate|vaccine|hospital"
    r"|university|college|school|church|museum|newspaper|magazine|radio|broadcast|podcast"
    r"|restaurant|airline|hotel|casino|mall|store\b|retailer|factory|plant\b|mine\b|refinery"
    r"|nuclear|pipeline|highway|bridge|airport|stadium|theater|cinema|band\b|album|movie|film"
    r"|game\ studio|publisher|bank\b|credit\ union|insurer|pharmacy|clinic|charity|nonprofit"
    r"|foundation|association|federation|ministry|agency|department|bureau|county|city\ of)\b"
)

# Vendor strings that are generic nouns or sentence fragments, not products.
REJECT_VENDOR = re.compile(
    r"(?i)^(the|a|an|this|that|these|those|it|they|we|i|my|our|his|her|its|some|many|most|all"
    r"|every|another|other|more|less|new|old|big|small|major|minor|several|two|three|why|how"
    r"|what|when|where|who|which|after|before|now|today|tomorrow|yesterday|company|companies"
    r"|startup|startups|business|businesses|service|services|product|products|app|apps|site"
    r"|sites|website|websites|platform|platforms|tool|tools|team|teams|people|users|customers"
    r"|employees|workers|jobs|job|market|markets|industry|government|state|federal|police"
    r"|americans|users\ of|half|one|part|much|many\ of)$"
)

CLEAN = re.compile(r"^[\"'“‘\(\[]+|[\"'”’\)\]\.,;:!\?]+$")


def _validate(vendor: str) -> str | None:
    vendor = CLEAN.sub("", vendor.strip())
    vendor = re.sub(r"\s+", " ", vendor)
    if not (2 <= len(vendor) <= 42):
        return None
    if REJECT_VENDOR.match(vendor):
        return None
    words = vendor.split()
    if len(words) > 4:
        return None
    if not (any(w[:1].isupper() for w in words) or "." in vendor):
        return None
    if words[0].islower() and "." not in words[0]:
        return None
    # Sentence fragments that survived: verbs and connectives never start a product name.
    if re.match(r"(?i)^(why|how|what|when|after|before|announces|announced|will|has|have|is|are)\b", vendor):
        return None
    return vendor


def extract(title: str) -> str | None:
    """Return a confident vendor name, or None. None is the common and correct answer."""
    if REJECT_TITLE.search(title):
        return None
    for pattern in TRANSITIVE:
        m = re.search(pattern, title, re.I)
        if m:
            vendor = _validate(m.group(1))
            if vendor:
                return vendor
    for pattern in PATTERNS:
        m = re.search(pattern, title, re.I)
        if not m:
            continue
        vendor = _validate(m.group(1))
        if vendor:
            return vendor
    return None


def slug(vendor: str) -> str:
    s = re.sub(r"[^\w\s.-]", "", vendor.lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-.")
    return re.sub(r"-{2,}", "-", s)


if __name__ == "__main__":
    import json
    import pathlib

    rows = [json.loads(l) for l in (pathlib.Path(__file__).parent / "events.jsonl").open()]
    hits = [(r, extract(r["title"])) for r in rows]
    ok = [(r, v) for r, v in hits if v]
    print(f"{len(ok)} of {len(rows)} events yielded a confident vendor ({len(ok)*100//len(rows)}%)\n")
    for r, v in ok[:30]:
        print(f"  {v:<28} <- {r['title'][:66]}")
