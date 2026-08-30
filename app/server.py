#!/usr/bin/env python3
"""The registry web app.

    pip install flask
    python app/server.py                    # http://127.0.0.1:8080
    ADMIN_TOKEN=... python app/server.py

Serves the records from disk and accepts strategy submissions into a review
queue. The frozen pre-registrations, their hashes and OpenTimestamps proofs
remain the authority; this is a reading and submission surface over them.

Submissions are queued, never auto-published. A registry that runs whatever
anyone types would fill with rules like "RSI but with market context", which
cannot be falsified and would make every result here worthless. The reviewer
gate is the point, not friction to be removed later.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

from flask import (Flask, abort, jsonify, redirect, render_template,
                   request, url_for)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from app import db, seo, verify                       # noqa: E402
from build_site import FAMILY_LABEL, collect          # noqa: E402

DB_PATH = os.environ.get("REGISTRY_DB", os.path.join(ROOT, "registry.db"))
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
PORT_FILE = os.path.join(ROOT, ".port")


def free_port(preferred: int | None = None) -> int:
    """Find a port that is actually free.

    This VPS runs several projects at once, so a fixed default will eventually
    collide with something already listening. Preference order: whatever PORT
    says, then the port used last time (so restarts keep the same URL), then a
    scan of the 8400-8999 range, then whatever the OS hands out.
    """
    import socket

    def works(p: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("0.0.0.0", p))
                return True
            except OSError:
                return False

    candidates = []
    if preferred:
        candidates.append(preferred)
    if os.path.exists(PORT_FILE):
        try:
            candidates.append(int(open(PORT_FILE).read().strip()))
        except ValueError:
            pass
    candidates += list(range(8400, 9000))

    for p in candidates:
        if 1024 < p < 65536 and works(p):
            return p

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", 0))
        return s.getsockname()[1]

app = Flask(__name__, template_folder=os.path.join(HERE, "templates"))
conn = db.connect(DB_PATH)

_cache: dict = {"records": None, "at": 0.0}


def records(force: bool = False):
    """Records are read from disk and cached briefly. Rerunning a sweep should
    show up without a restart, but every request re-walking the tree is waste."""
    import time
    if force or _cache["records"] is None or time.time() - _cache["at"] > 30:
        _cache["records"] = collect(ROOT)
        _cache["at"] = time.time()
    return _cache["records"]


def verdict_of(r):
    if r["status"] == "SEALED":
        return "Sealed until " + str(r["embargo"]), "sealed"
    if r["status"] == "VOID":
        return "Void", "void"
    if r["dsr"] is not None and r["dsr"] >= 0.95:
        return "Passed", "pass"
    return "Did not pass", "fail"


def enrich(r):
    v, cls = verdict_of(r)
    d = dict(r)
    d["verdict_text"] = v
    d["verdict_class"] = cls
    return d


def is_admin() -> bool:
    if not ADMIN_TOKEN:
        return False
    given = request.headers.get("X-Admin-Token") or request.args.get("admin", "")
    return given == ADMIN_TOKEN


def voter_id() -> str:
    """Coarse identity for one-vote-per-person, without accounts or tracking."""
    import hashlib
    raw = (request.headers.get("X-Forwarded-For", request.remote_addr or "")
           + request.headers.get("User-Agent", ""))
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


# ---------------------------------------------------------------- pages
GROUPS = [
    ("Mean reversion", {"zscore_reversion", "rsi_reversion", "bollinger_touch"}),
    ("Trend and breakout", {"zscore_continuation", "rsi_continuation",
                            "bollinger_breakout", "ma_cross", "donchian_breakout",
                            "atr_breakout", "momentum_roc", "vol_regime_momentum"}),
    ("Price action and smart money", {"fair_value_gap", "order_block",
                                      "liquidity_sweep", "break_of_structure",
                                      "engulfing", "inside_bar_breakout"}),
    ("Cross-sectional", {"xs_momentum", "xs_reversal", "xs_vol_scaled_momentum"}),
    ("Calendar", {"intraday_seasonality"}),
]


def grouped(recs):
    """Group by strategy category. A flat list of 34 identical verdicts reads
    as noise; grouped, it reads as a survey with coverage."""
    out, seen = [], set()
    for name, fams in GROUPS:
        rows = [r for r in recs if set(r["families"]) & fams]
        if rows:
            out.append((name, sorted(rows, key=lambda r: r["id"])))
            seen |= {r["id"] for r in rows}
    rest = [r for r in recs if r["id"] not in seen]
    if rest:
        out.append(("Other", sorted(rest, key=lambda r: r["id"])))
    return out


@app.get("/")
def index():
    recs = [enrich(r) for r in records()]
    scored = [r for r in recs if r["dsr"] is not None and r["status"] == "OK"]
    closest = max(scored, key=lambda r: r["dsr"]) if scored else None
    return render_template(
        "index.html",
        records=sorted(recs, key=lambda r: r["id"]),
        groups=grouped(recs),
        scatter=sorted(scored, key=lambda r: r["dsr"]),
        markets=sorted({r["market"] for r in recs}),
        n_records=len(recs),
        n_variants=sum(r["trials"] for r in recs if r["status"] == "OK"),
        n_passed=sum(1 for r in scored if r["dsr"] >= 0.95),
        n_stamped=sum(1 for r in recs if r["stamped"]),
        n_markets=len({r["market"] for r in recs}),
        closest=closest,
        queued=db.counts(conn).get("queued", 0),
    )


@app.get("/record/<sweep_id>")
def record(sweep_id):
    for r in records():
        if r["id"] == sweep_id:
            ordered = sorted(records(), key=lambda x: x["id"])
            i = [x["id"] for x in ordered].index(sweep_id)
            return render_template(
                "record.html", r=enrich(r),
                prev=ordered[i - 1] if i else None,
                next=ordered[i + 1] if i + 1 < len(ordered) else None)
    abort(404)


@app.get("/submit")
def submit_form():
    return render_template("submit.html",
                           families=sorted(FAMILY_LABEL.items()))


@app.post("/submit")
def submit_post():
    f = request.form
    name = (f.get("name") or "").strip()
    definition = (f.get("definition") or "").strip()
    if len(name) < 3 or len(definition) < 60:
        return render_template(
            "submit.html", families=sorted(FAMILY_LABEL.items()),
            error=("A name and a mechanical definition of at least 60 "
                   "characters are required. If the rule cannot be written "
                   "down precisely enough for someone else to implement it "
                   "identically, it cannot be tested."),
            form=f), 400

    params = {}
    for line in (f.get("parameters") or "").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            vals = [x.strip() for x in v.split(",") if x.strip()]
            if k.strip() and vals:
                params[k.strip()] = vals

    res = db.submit(conn,
                    name=name,
                    family=(f.get("family") or "custom").strip(),
                    definition=definition,
                    parameters=params,
                    market=(f.get("market") or "Crypto").strip(),
                    rationale=(f.get("rationale") or "").strip() or None,
                    email=(f.get("email") or "").strip() or None)
    return redirect(url_for("submitted", token=res["token"]))


@app.get("/submitted/<token>")
def submitted(token):
    row = db.by_token(conn, token)
    if not row:
        abort(404)
    return render_template("submitted.html", s=row,
                           params=json.loads(row["parameters"]))


@app.get("/queue")
def queue_page():
    rows = db.queue(conn)
    return render_template("queue.html", rows=rows, admin=is_admin(),
                           counts=db.counts(conn))


@app.post("/queue/<int:sub_id>/vote")
def vote(sub_id):
    ok = db.vote(conn, sub_id, voter_id())
    return jsonify({"ok": ok})


@app.post("/queue/<int:sub_id>/status")
def review(sub_id):
    if not is_admin():
        abort(403)
    db.set_status(conn, sub_id,
                  request.form.get("status", "queued"),
                  request.form.get("note") or None,
                  request.form.get("sweep_id") or None)
    return redirect(url_for("queue_page", admin=request.args.get("admin", "")))


@app.get("/method")
def method():
    return render_template("method.html")


# ---------------------------------------------------------------- api
@app.get("/api/records")
def api_records():
    return jsonify([enrich(r) for r in records()])


@app.get("/api/records/<sweep_id>")
def api_record(sweep_id):
    for r in records():
        if r["id"] == sweep_id:
            return jsonify(enrich(r))
    abort(404)


@app.get("/api/stats")
def api_stats():
    recs = records()
    scored = [r for r in recs if r["dsr"] is not None and r["status"] == "OK"]
    return jsonify({
        "records": len(recs),
        "variants": sum(r["trials"] for r in recs if r["status"] == "OK"),
        "passed": sum(1 for r in scored if r["dsr"] >= 0.95),
        "timestamped": sum(1 for r in recs if r["stamped"]),
        "submissions": db.counts(conn),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })


@app.get("/chain")
def chain_page():
    entries = verify.build_chain(ROOT)
    return render_template("chain.html", entries=list(reversed(entries)),
                           summary=verify.chain_summary(entries))


@app.get("/chain/<sweep_id>")
def chain_entry(sweep_id):
    entries = verify.build_chain(ROOT)
    for i, e in enumerate(entries):
        if e["sweep_id"] == sweep_id:
            return render_template(
                "chain_entry.html", e=e,
                prev=entries[i - 1] if i else None,
                next=entries[i + 1] if i + 1 < len(entries) else None,
                summary=verify.chain_summary(entries))
    abort(404)


@app.get("/api/chain")
def api_chain():
    entries = verify.build_chain(ROOT)
    return jsonify({"summary": verify.chain_summary(entries),
                    "entries": entries})


@app.get("/sitemap.xml")
def sitemap():
    from flask import Response
    base = request.url_root.rstrip("/")
    urls = [f"{base}/", f"{base}/method", f"{base}/submit", f"{base}/queue",
            f"{base}/strategies", f"{base}/learn", f"{base}/chain"]
    urls += [f"{base}/record/{r['id']}" for r in records()]
    urls += [base + path for _kind, path, _title in seo.all_pages(records())]
    body = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + "".join(f"<url><loc>{u}</loc></url>" for u in urls)
            + "</urlset>")
    return Response(body, mimetype="application/xml")


@app.get("/robots.txt")
def robots():
    from flask import Response
    return Response(
        f"User-agent: *\nAllow: /\nSitemap: {request.url_root}sitemap.xml\n",
        mimetype="text/plain")


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


seo.register(app, records, render_template)


if __name__ == "__main__":
    env_port = os.environ.get("PORT")
    port = free_port(int(env_port) if env_port else None)

    if env_port and port != int(env_port):
        print(f"  ! port {env_port} is in use — using {port} instead")

    try:
        with open(PORT_FILE, "w") as fh:
            fh.write(str(port))
    except OSError:
        pass

    if not ADMIN_TOKEN:
        print("  ! ADMIN_TOKEN not set, review controls are disabled.")
        print("    ADMIN_TOKEN=$(openssl rand -hex 16) python app/server.py")

    print(f"  {len(records())} records loaded from {ROOT}/sweeps/")
    print(f"  {len(seo.all_pages(records()))} generated pages")
    print(f"  database: {DB_PATH}")
    print()
    print(f"  http://127.0.0.1:{port}")
    if ADMIN_TOKEN:
        print(f"  queue:  http://127.0.0.1:{port}/queue?admin={ADMIN_TOKEN}")
    print()
    app.run(host="0.0.0.0", port=port, debug=False)
