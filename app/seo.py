"""SEO page routes, generated from real records plus hand-written editorial.

DESIGN RULE

A page is only generated when both are true:
  1. a real person plausibly types the query, and
  2. the page says something the other pages do not.

That rules out the obvious move of one page per parameter combination.
17,000 near-identical pages is what Google names "scaled content abuse", and
nobody searches for "RSI period 37 threshold 2.5" anyway — it would be zero
traffic bought at the cost of the whole domain's credibility.

Every page here pulls live numbers from the frozen records. Nothing is
invented at render time; when a sweep is rerun, the pages change with it.
"""
from __future__ import annotations

import re
from collections import defaultdict

from app.content import (COMPARISONS, CONCEPTS, FAMILIES, HIGH_DEMAND,
                         MARKET_CONTEXT, POPULAR_PARAMS, QUESTION_FORMS)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


FAMILY_SLUG = {k: slugify(v["label"]) for k, v in FAMILIES.items()}
SLUG_FAMILY = {v: k for k, v in FAMILY_SLUG.items()}


def records_for(records, family=None, market=None, symbol=None):
    out = records
    if family:
        out = [r for r in out if family in r["families"]]
    if market:
        out = [r for r in out if r["market"] == market]
    if symbol:
        out = [r for r in out if symbol in r.get("symbols", [])]
    return [r for r in out if r["status"] == "OK"]


def summarise(rows):
    """Turn a set of records into the numbers a page quotes."""
    scored = [r for r in rows if r["dsr"] is not None]
    if not scored:
        return None
    best = max(scored, key=lambda r: r["dsr"])
    return {
        "n": len(scored),
        "variants": sum(r["trials"] for r in scored),
        "best_dsr": best["dsr"],
        "best_record": best,
        "best_sharpe": max((r["best"] for r in scored if r["best"] is not None),
                           default=None),
        "worst_sharpe": min((r["best"] for r in scored if r["best"] is not None),
                            default=None),
        "any_passed": any(r["dsr"] >= 0.95 for r in scored),
        "limits": [r["limit"] for r in scored if r["limit"] is not None],
        "rows": sorted(scored, key=lambda r: r["id"]),
    }


def all_pages(records):
    """Every generated URL, for the sitemap and the index of pages."""
    pages = []

    for fam, meta in FAMILIES.items():
        slug = FAMILY_SLUG[fam]
        rows = records_for(records, family=fam)
        if not rows:
            continue

        pages.append(("family", f"/strategy/{slug}", meta["label"]))

        for market in sorted({r["market"] for r in rows}):
            pages.append(("family-market", f"/strategy/{slug}/{market.lower()}",
                          f"{meta['label']} on {market}"))

        symbols = sorted({s for r in rows for s in r.get("symbols", [])
                          if s.isupper() and len(s) <= 10})
        for sym in symbols:
            pages.append(("family-symbol",
                          f"/strategy/{slug}/symbol/{sym.lower()}",
                          f"{meta['label']} on {sym}"))

        forms = QUESTION_FORMS if fam in HIGH_DEMAND else QUESTION_FORMS[:2]
        for pattern, title, _q in forms:
            pages.append(("question", "/q/" + pattern.format(slug=slug),
                          title.format(label=meta["label"])))

        for pslug, plabel, _v, _note in POPULAR_PARAMS.get(fam, []):
            pages.append(("parameter", f"/settings/{pslug}", plabel))

    for c in CONCEPTS:
        pages.append(("concept", f"/learn/{c['slug']}", c["title"]))

    for cslug, ctitle, fams, _blurb in COMPARISONS:
        if all(records_for(records, family=f) for f in fams):
            pages.append(("comparison", f"/compare/{cslug}", ctitle))

    return pages


def register(app, records_fn, render):
    """Attach every SEO route to the Flask app."""

    def fam_or_404(slug):
        fam = SLUG_FAMILY.get(slug)
        if not fam:
            from flask import abort
            abort(404)
        return fam

    # ---------------------------------------------------------- family
    @app.get("/strategy/<slug>")
    def seo_family(slug):
        fam = fam_or_404(slug)
        rows = records_for(records_fn(), family=fam)
        if not rows:
            from flask import abort
            abort(404)
        by_market = defaultdict(list)
        for r in rows:
            by_market[r["market"]].append(r)
        return render("seo_family.html",
                      fam=fam, slug=slug, meta=FAMILIES[fam],
                      summary=summarise(rows),
                      by_market={k: summarise(v) for k, v in by_market.items()},
                      market_context=MARKET_CONTEXT,
                      params=POPULAR_PARAMS.get(fam, []),
                      questions=[(p.format(slug=slug), t.format(label=FAMILIES[fam]["label"]))
                                 for p, t, _ in (QUESTION_FORMS if fam in HIGH_DEMAND
                                                 else QUESTION_FORMS[:2])])

    @app.get("/strategy/<slug>/<market>")
    def seo_family_market(slug, market):
        fam = fam_or_404(slug)
        mk = {"crypto": "Crypto", "fx": "FX"}.get(market.lower())
        rows = records_for(records_fn(), family=fam, market=mk) if mk else []
        if not rows:
            from flask import abort
            abort(404)
        return render("seo_family_market.html",
                      fam=fam, slug=slug, meta=FAMILIES[fam], market=mk,
                      context=MARKET_CONTEXT.get(mk, ""),
                      summary=summarise(rows))

    @app.get("/strategy/<slug>/symbol/<sym>")
    def seo_family_symbol(slug, sym):
        fam = fam_or_404(slug)
        symbol = sym.upper()
        rows = records_for(records_fn(), family=fam, symbol=symbol)
        if not rows:
            from flask import abort
            abort(404)
        return render("seo_family_symbol.html",
                      fam=fam, slug=slug, meta=FAMILIES[fam], symbol=symbol,
                      summary=summarise(rows))

    # -------------------------------------------------------- questions
    @app.get("/q/<path:qslug>")
    def seo_question(qslug):
        for fam, meta in FAMILIES.items():
            slug = FAMILY_SLUG[fam]
            forms = QUESTION_FORMS if fam in HIGH_DEMAND else QUESTION_FORMS[:2]
            for pattern, title, question in forms:
                if pattern.format(slug=slug) == qslug:
                    rows = records_for(records_fn(), family=fam)
                    if not rows:
                        continue
                    return render(
                        "seo_question.html",
                        fam=fam, slug=slug, meta=meta,
                        kind=pattern.split("-")[0] if pattern.startswith("does") else pattern,
                        pattern=pattern,
                        title=title.format(label=meta["label"]),
                        question=question.format(label=meta["label"],
                                                 label_l=meta["label"].lower()),
                        summary=summarise(rows))
        from flask import abort
        abort(404)

    # ------------------------------------------------------- parameters
    @app.get("/settings/<pslug>")
    def seo_parameter(pslug):
        for fam, entries in POPULAR_PARAMS.items():
            for s, label, value, note in entries:
                if s == pslug:
                    rows = records_for(records_fn(), family=fam)
                    if not rows:
                        continue
                    return render("seo_parameter.html",
                                  fam=fam, slug=FAMILY_SLUG[fam],
                                  meta=FAMILIES[fam], label=label,
                                  value=value, note=note,
                                  summary=summarise(rows))
        from flask import abort
        abort(404)

    # ---------------------------------------------------------- learn
    @app.get("/learn/<cslug>")
    def seo_concept(cslug):
        for c in CONCEPTS:
            if c["slug"] == cslug:
                related = [x for x in CONCEPTS if x["slug"] in c.get("related", [])]
                return render("seo_concept.html", c=c, related=related)
        from flask import abort
        abort(404)

    @app.get("/learn")
    def seo_learn_index():
        return render("seo_learn_index.html", concepts=CONCEPTS)

    # -------------------------------------------------------- compare
    @app.get("/compare/<cslug>")
    def seo_compare(cslug):
        for s, title, fams, blurb in COMPARISONS:
            if s == cslug:
                sides = []
                for f in fams:
                    rows = records_for(records_fn(), family=f)
                    if rows:
                        sides.append((f, FAMILIES[f], summarise(rows)))
                if len(sides) < 2:
                    continue
                return render("seo_compare.html", title=title, blurb=blurb,
                              sides=sides, slugs=FAMILY_SLUG)
        from flask import abort
        abort(404)

    # ------------------------------------------------------- directory
    @app.get("/strategies")
    def seo_directory():
        recs = records_fn()
        groups = defaultdict(list)
        for kind, url, title in all_pages(recs):
            groups[kind].append((url, title))
        return render("seo_directory.html", groups=dict(groups),
                      total=sum(len(v) for v in groups.values()))
