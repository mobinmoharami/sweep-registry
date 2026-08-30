#!/usr/bin/env python3
"""Generate the public site from the records that actually exist.

    python build_site.py            # writes site/index.html
    python build_site.py --out /var/www/registry

Reads every sweeps/*/ directory — frozen pre-registration, result.json,
annotations.json — and renders a single self-contained page. No numbers are
typed by hand anywhere in this file; if a record changes, rerun it.
"""
from __future__ import annotations

import argparse
import glob
import html
import json
import os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))

FAMILY_LABEL = {
    "zscore_reversion": "Z-score reversion",
    "rsi_reversion": "RSI reversion",
    "bollinger_touch": "Bollinger touch",
    "zscore_continuation": "Z-score continuation",
    "rsi_continuation": "RSI continuation",
    "bollinger_breakout": "Bollinger breakout",
    "ma_cross": "Moving average cross",
    "donchian_breakout": "Donchian breakout",
    "atr_breakout": "ATR breakout",
    "momentum_roc": "Time-series momentum",
    "vol_regime_momentum": "Volatility-filtered momentum",
    "intraday_seasonality": "Hour-of-day seasonality",
    "fair_value_gap": "Fair value gap",
    "order_block": "Order block",
    "liquidity_sweep": "Liquidity sweep",
    "break_of_structure": "Break of structure",
    "engulfing": "Engulfing candle",
    "inside_bar_breakout": "Inside bar breakout",
    "xs_momentum": "Cross-sectional momentum",
    "xs_reversal": "Cross-sectional reversal",
    "xs_vol_scaled_momentum": "Vol-scaled cross-sectional momentum",
}


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def collect(root: str) -> list[dict]:
    out = []
    for d in sorted(glob.glob(os.path.join(root, "sweeps", "SW-*"))):
        prereg = load(os.path.join(d, "preregistration.frozen.json"))
        if not prereg:
            continue
        result = load(os.path.join(d, "result.json"))
        ann = load(os.path.join(d, "annotations.json")) or {}
        diag = load(os.path.join(d, "diagnostics.json")) or {}
        sha = load(os.path.join(d, "preregistration.sha256")) or {}
        has_ots = os.path.exists(os.path.join(d, "preregistration.sha256.ots"))

        fams = prereg["search_space"]["families"]
        syms = prereg["data"]["symbols"]
        market = "FX" if any(s in ("EURUSD", "GBPUSD", "USDJPY") for s in syms) \
            else "Crypto"
        embargo = prereg.get("planning", {}).get("earliest_run_date")

        status = ann.get("status", "OK")
        if embargo and not result:
            status = "SEALED"

        out.append({
            "id": prereg["sweep_id"],
            "title": prereg["title"],
            "families": fams,
            "label": " + ".join(FAMILY_LABEL.get(f, f) for f in fams),
            "market": market,
            "symbols": syms,
            "trials": prereg["search_space"]["n_trials"],
            "period": f"{prereg['data']['start']} to {prereg['data']['end']}",
            "status": status,
            "reason": ann.get("reason"),
            "confirmatory": ann.get("confirmatory", []),
            "exploratory": ann.get("exploratory", []),
            "notes": ann.get("notes", []),
            "dsr": result.get("deflated_sharpe_ratio") if result else None,
            "best": result.get("best_sharpe_annual") if result else None,
            "null": result.get("expected_max_sharpe_under_null_annual") if result else None,
            "limit": result.get("min_detectable_sharpe_annual") if result else None,
            "pbo": (result.get("pbo") or {}).get("pbo") if result else None,
            "verdict": result.get("verdict") if result else None,
            "z": (diag.get("null_calibration") or {}).get("z_score"),
            "dist": result.get("distribution_annualised") if result else None,
            "n_obs": result.get("n_observations") if result else None,
            "mechanism": diag.get("mechanism"),
            "gross": (diag.get("gross_sharpe_annual") or {}).get("mean"),
            "net": (diag.get("net_sharpe_annual") or {}).get("mean"),
            "breakeven": (diag.get("breakeven_cost_bps") or {}).get("best_variant"),
            "sha": sha.get("preregistration_sha256"),
            "stamped": has_ots,
            "embargo": embargo,
        })
    return out


def esc(x):
    return html.escape(str(x))


def fnum(v, spec="+.2f", dash="\u2014"):
    return format(v, spec) if v is not None else dash


CSS = """
:root{
  --void:#07090d; --deep:#0b0f16; --line:#1c2534;
  --text:#e6ecf5; --mute:#7d8ba3; --dim:#4d5a70;
  --live:#4ade80; --fail:#f97066; --seal:#60a5fa; --gold:#fbbf24;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--void);color:var(--text);
  font:400 16px/1.65 'Inter',system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.mono{font-family:'JetBrains Mono',monospace}
.wrap{max-width:1140px;margin:0 auto;padding:0 28px}
#sky{position:fixed;inset:0;z-index:0;opacity:.55;pointer-events:none}
.above{position:relative;z-index:1}

header{padding:140px 0 88px}
.eyebrow{font:500 11px/1 'JetBrains Mono',monospace;letter-spacing:.28em;
  text-transform:uppercase;color:var(--dim);margin:0 0 30px}
h1{font:200 clamp(46px,8.5vw,104px)/0.96 'Inter',sans-serif;
  letter-spacing:-.045em;margin:0 0 34px}
.glow{background:linear-gradient(180deg,#fff 0%,#8ea3c4 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent}
.lede{font-size:20px;line-height:1.6;color:var(--mute);max-width:44ch;margin:0 0 18px}
.lede b{color:var(--text);font-weight:500}

.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
  gap:1px;background:var(--line);border:1px solid var(--line);margin:72px 0 0}
.metric{background:var(--deep);padding:26px 24px}
.metric b{display:block;font:300 40px/1 'JetBrains Mono',monospace;letter-spacing:-.04em}
.metric b.zero{color:var(--fail)}
.metric span{display:block;margin-top:10px;font:400 11px/1.4 'JetBrains Mono',monospace;
  letter-spacing:.14em;text-transform:uppercase;color:var(--dim)}

section{padding:96px 0;border-top:1px solid var(--line)}
h2{font:500 11px/1 'JetBrains Mono',monospace;letter-spacing:.28em;
  text-transform:uppercase;color:var(--dim);margin:0 0 40px}
h3{font:500 19px/1.35 'Inter',sans-serif;letter-spacing:-.01em;margin:0 0 10px}
p{max-width:62ch}

.pillars{display:grid;gap:44px;grid-template-columns:repeat(auto-fit,minmax(250px,1fr))}
.pillars p{color:var(--mute);font-size:15.5px;margin:0}
.pillars .n{font:400 11px/1 'JetBrains Mono',monospace;color:var(--seal);
  letter-spacing:.2em;display:block;margin-bottom:16px}

.bar{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 26px;align-items:center}
.bar button{font:400 12px/1 'JetBrains Mono',monospace;letter-spacing:.08em;
  padding:10px 16px;border:1px solid var(--line);background:transparent;
  color:var(--mute);cursor:pointer}
.bar button[aria-pressed=true]{border-color:var(--seal);color:var(--seal)}
.bar button:focus-visible{outline:2px solid var(--seal);outline-offset:2px}
.count{margin-left:auto;font:400 12px 'JetBrains Mono',monospace;color:var(--dim)}

table{width:100%;border-collapse:collapse}
thead th{font:500 10px/1 'JetBrains Mono',monospace;letter-spacing:.16em;
  text-transform:uppercase;color:var(--dim);text-align:right;
  padding:0 0 14px;border-bottom:1px solid var(--line);white-space:nowrap}
thead th:nth-child(-n+2){text-align:left}
tbody tr{border-bottom:1px solid var(--line)}
tbody tr:hover{background:#0d121b}
td{padding:15px 0;vertical-align:middle}
.id{font:400 11px/1.8 'JetBrains Mono',monospace;color:var(--dim)}
.nm{padding-right:18px}
.nm a{text-decoration:none;font-weight:450;color:inherit}
.nm a:hover{color:var(--seal)}
.nm .sub{display:block;font:400 11px/1.7 'JetBrains Mono',monospace;color:var(--dim)}
.num{text-align:right;font:400 14px/1.8 'JetBrains Mono',monospace;padding-left:14px}
.num.dim{color:var(--dim)}
.meter{display:flex;align-items:center;gap:9px;justify-content:flex-end;padding-left:14px}
.track{width:56px;height:3px;background:var(--line);position:relative}
.fill{position:absolute;inset:0 auto 0 0;background:var(--dim)}
.fill.hot{background:var(--gold)}
.meter span{font:400 13px 'JetBrains Mono',monospace;min-width:42px;text-align:right}
.res{text-align:right;font:400 11px/1.8 'JetBrains Mono',monospace;
  white-space:nowrap;padding-left:16px;letter-spacing:.05em}
.res.fail{color:var(--dim)}
.res.pass{color:var(--live)}
.res.void{color:var(--fail)}
.res.sealed{color:var(--seal)}

.back{display:inline-block;margin:0 0 40px;font:400 12px 'JetBrains Mono',monospace;
  color:var(--dim);text-decoration:none}
.back:hover{color:var(--seal)}
.rec-head{padding:80px 0 44px}
.rec-head .id{font-size:12px;margin-bottom:20px;display:block}
.rec-head h1{font-size:clamp(30px,4.6vw,50px);margin-bottom:22px}
.badge{display:inline-block;padding:7px 14px;border:1px solid;
  font:400 11px/1 'JetBrains Mono',monospace;letter-spacing:.12em;text-transform:uppercase}
.badge.fail{border-color:var(--line);color:var(--mute)}
.badge.pass{border-color:var(--live);color:var(--live)}
.badge.void{border-color:var(--fail);color:var(--fail)}
.badge.sealed{border-color:var(--seal);color:var(--seal)}

.grid2{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
  grid-template-columns:repeat(auto-fit,minmax(190px,1fr))}
.cell{background:var(--deep);padding:22px}
.cell b{display:block;font:300 27px/1 'JetBrains Mono',monospace;letter-spacing:-.03em}
.cell span{display:block;margin-top:9px;font:400 10px/1.5 'JetBrains Mono',monospace;
  letter-spacing:.14em;text-transform:uppercase;color:var(--dim)}
.cell em{display:block;margin-top:7px;font-style:normal;font-size:12.5px;color:var(--mute)}

.chart{margin:36px 0 0;background:var(--deep);border:1px solid var(--line);padding:28px}
.chart h4{font:500 10px/1 'JetBrains Mono',monospace;letter-spacing:.18em;
  text-transform:uppercase;color:var(--dim);margin:0 0 22px}
.chart figcaption{margin:18px 0 0;font-size:13.5px;color:var(--mute);max-width:70ch}

.block{margin:34px 0 0;padding:22px 24px;background:var(--deep);border:1px solid var(--line)}
.block.confirm{border-left:2px solid var(--seal)}
.block.explore{border-left:2px solid var(--gold)}
.block.void{border-left:2px solid var(--fail)}
.block .tag{font:400 10px/1 'JetBrains Mono',monospace;letter-spacing:.18em;
  text-transform:uppercase;color:var(--dim);margin:0 0 14px}
.block p{margin:0 0 12px;font-size:15px;color:var(--mute)}
.block p:last-child{margin-bottom:0}
.block.confirm p{color:var(--text)}

.hashline{margin:34px 0 0;padding:18px 22px;background:var(--deep);
  border:1px solid var(--line);font:400 11.5px/1.9 'JetBrains Mono',monospace;
  color:var(--dim);word-break:break-all}
.hashline b{color:var(--seal);font-weight:400}

footer{padding:70px 0 110px;border-top:1px solid var(--line);color:var(--dim);font-size:14px}
footer p{max-width:70ch;margin:0 0 14px}

@media(max-width:760px){
  header{padding:88px 0 60px}
  .num.dim,thead th:nth-child(4){display:none}
  section{padding:64px 0}
}
@media(prefers-reduced-motion:reduce){#sky{display:none}html{scroll-behavior:auto}}
"""

SKY = """
(function(){
  var c=document.getElementById('sky');
  if(!c||window.matchMedia('(prefers-reduced-motion:reduce)').matches)return;
  var x=c.getContext('2d'),s=[],w,h;
  function size(){w=c.width=innerWidth;h=c.height=innerHeight;s=[];
    var n=Math.min(180,Math.round(w*h/12000));
    for(var i=0;i<n;i++)s.push({x:Math.random()*w,y:Math.random()*h,
      r:Math.random()*1.1+.2,a:Math.random()*.5+.15,v:Math.random()*.02+.004});}
  function draw(t){x.clearRect(0,0,w,h);
    for(var i=0;i<s.length;i++){var p=s[i];var f=p.a+Math.sin(t*p.v+i)*.18;
      x.beginPath();x.arc(p.x,p.y,p.r,0,6.283);
      x.fillStyle='rgba(180,205,240,'+Math.max(0,f)+')';x.fill();}
    requestAnimationFrame(draw);}
  size();requestAnimationFrame(draw);addEventListener('resize',size);
})();
"""

FOOT = """<p>Every strategy is registered before it is tested, run on public
exchange data, and published whatever the outcome. Nothing here is advice.</p>
<p>A strategy failing this test does not mean no version of it can work, only
that this version, tested this way, did not beat chance by enough to say so.
Each record states the smallest edge it could have detected at all.</p>"""


def bar_chart(best, null, limit):
    if best is None or null is None:
        return ""
    rows = [("Best version found", best, "#e6ecf5"),
            ("What luck alone gives", null, "#4d5a70")]
    if limit is not None:
        rows.append(("Smallest edge visible", limit, "#fbbf24"))
    top = max(abs(v) for _, v, _ in rows) or 1.0
    W, BH, GAP, PAD = 760, 26, 20, 170
    H = len(rows) * (BH + GAP)
    out = []
    for i, (lab, v, col) in enumerate(rows):
        y = i * (BH + GAP)
        w = abs(v) / top * (W - PAD - 70)
        op = "0.9" if i == 0 else "0.55"
        out.append(
            '<text x="0" y="%d" fill="#7d8ba3" font-size="11.5" '
            'font-family="Inter,sans-serif">%s</text>'
            '<rect x="%d" y="%d" width="%.1f" height="%d" fill="%s" opacity="%s"/>'
            '<text x="%.1f" y="%d" fill="%s" font-size="12" '
            'font-family="JetBrains Mono,monospace">%+.2f</text>'
            % (y + 17, lab, PAD, y, w, BH, col, op, PAD + w + 10, y + 17, col, v))
    return ('<figure class="chart"><h4>Result against chance</h4>'
            '<svg viewBox="0 0 %d %d" width="100%%" height="%d" role="img" '
            'aria-label="Best result compared with luck">%s</svg>'
            '<figcaption>If the best version cannot beat what luck alone '
            'produces from the same number of tries, there is nothing there. '
            'The third bar is the smallest real edge this test could have '
            'detected: anything below it is invisible to the test, and that '
            'limit is stated rather than hidden.</figcaption></figure>'
            % (W, H, H, "".join(out)))


def dist_chart(dist):
    if not dist:
        return ""
    keys = ["min", "p05", "p25", "median", "p75", "p95", "max"]
    v = [dist.get(k) for k in keys]
    if any(x is None for x in v):
        return ""
    lo, hi = min(v + [0.0]), max(v + [0.0])
    span = (hi - lo) or 1.0
    W, H, PAD = 760, 116, 34

    def X(t):
        return PAD + (t - lo) / span * (W - 2 * PAD)

    parts = [
        '<line x1="%.1f" y1="49" x2="%.1f" y2="49" stroke="#2b3648" stroke-width="1"/>'
        % (X(v[1]), X(v[5])),
        '<rect x="%.1f" y="34" width="%.1f" height="30" fill="#1c2534"/>'
        % (X(v[2]), max(X(v[4]) - X(v[2]), 1)),
        '<line x1="%.1f" y1="30" x2="%.1f" y2="68" stroke="#e6ecf5" stroke-width="2"/>'
        % (X(v[3]), X(v[3])),
        '<line x1="%.1f" y1="18" x2="%.1f" y2="80" stroke="#f97066" '
        'stroke-width="1" stroke-dasharray="3 3"/>' % (X(0.0), X(0.0)),
        '<text x="%.1f" y="90" fill="#4d5a70" font-size="10" '
        'font-family="JetBrains Mono,monospace" text-anchor="middle">%+.2f</text>'
        % (X(v[0]), v[0]),
        '<text x="%.1f" y="24" fill="#e6ecf5" font-size="10" '
        'font-family="JetBrains Mono,monospace" text-anchor="middle">median %+.2f</text>'
        % (X(v[3]), v[3]),
        '<text x="%.1f" y="90" fill="#4d5a70" font-size="10" '
        'font-family="JetBrains Mono,monospace" text-anchor="middle">%+.2f</text>'
        % (X(v[6]), v[6]),
        '<text x="%.1f" y="108" fill="#f97066" font-size="10" '
        'font-family="JetBrains Mono,monospace" text-anchor="middle">zero</text>'
        % X(0.0),
    ]
    cap = ("Every version tested, worst to best. The box holds the middle half. "
           "Showing only the best bar is how noise gets sold as skill.")
    share = dist.get("share_positive")
    if share is not None:
        cap += " %d%% of versions finished above zero." % round(share * 100)
    return ('<figure class="chart"><h4>Spread across every version</h4>'
            '<svg viewBox="0 0 %d %d" width="100%%" height="%d" role="img" '
            'aria-label="Distribution across all variants">%s</svg>'
            '<figcaption>%s</figcaption></figure>' % (W, H, H, "".join(parts), cap))


def verdict_of(r):
    if r["status"] == "SEALED":
        return "Sealed until " + str(r["embargo"]), "sealed"
    if r["status"] == "VOID":
        return "Void", "void"
    if r["dsr"] is not None and r["dsr"] >= 0.95:
        return "Passed", "pass"
    return "Did not pass", "fail"


def shell(title, body, desc):
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>%s</title><meta name="description" content="%s">'
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@200;400;450;500'
        '&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">'
        '<style>%s</style></head><body><canvas id="sky"></canvas>'
        '<div class="above">%s</div><script>%s</script></body></html>'
        % (esc(title), esc(desc), CSS, body, SKY))


def record_page(r, nav):
    v, vc = verdict_of(r)
    cells = [
        ("Versions tested", "{:,}".format(r["trials"]),
         "every combination, fixed in advance"),
        ("Best version", fnum(r["best"]), "return adjusted for risk, per year"),
        ("Luck alone", fnum(r["null"]), "what the best scores if nothing works"),
        ("Score", fnum(r["dsr"], ".3f"), "has to reach 0.950"),
    ]
    cellhtml = "".join(
        '<div class="cell"><b>%s</b><span>%s</span><em>%s</em></div>'
        % (esc(val), esc(lab), esc(note)) for lab, val, note in cells)

    blocks = []
    if r["reason"]:
        blocks.append('<div class="block void"><p class="tag">Why this record is '
                      'void</p><p>%s</p></div>' % esc(r["reason"]))
    if r["confirmatory"]:
        blocks.append('<div class="block confirm"><p class="tag">What was sealed, '
                      'and the verdict</p>%s</div>'
                      % "".join("<p>%s</p>" % esc(c) for c in r["confirmatory"]))
    if r["exploratory"]:
        blocks.append('<div class="block explore"><p class="tag">Noticed '
                      'afterwards: a hypothesis, not a finding</p>%s</div>'
                      % "".join("<p>%s</p>" % esc(e) for e in r["exploratory"]))
    if r["notes"]:
        blocks.append('<div class="block"><p class="tag">Notes</p>%s</div>'
                      % "".join("<p>%s</p>" % esc(n) for n in r["notes"]))

    hashline = ""
    if r["sha"]:
        mark = "Sealed on the Bitcoin blockchain" if r["stamped"] else "Hashed"
        hashline = ('<div class="hashline"><b>%s</b> before the test ran.<br>'
                    'sha256 %s</div>' % (mark, esc(r["sha"])))

    body = (
        '<div class="wrap"><div class="rec-head">'
        '<a class="back" href="index.html">&larr; All records</a>'
        '<span class="id mono">%s &middot; %s &middot; %s</span>'
        '<h1 class="glow">%s</h1><span class="badge %s">%s</span></div>'
        '<section style="border-top:0;padding-top:20px">'
        '<div class="grid2">%s</div>%s%s%s%s</section>%s'
        '<footer>%s</footer></div>'
        % (esc(r["id"]), esc(r["market"]), esc(r["period"]), esc(r["label"]),
           vc, esc(v), cellhtml,
           bar_chart(r["best"], r["null"], r["limit"]), dist_chart(r["dist"]),
           "".join(blocks), hashline, nav, FOOT))
    return shell("%s \u2014 %s" % (r["id"], r["label"]), body,
                 "%s tested across %s versions. %s."
                 % (r["label"], "{:,}".format(r["trials"]), v))


def index_page(records):
    scored = [r for r in records if r["dsr"] is not None and r["status"] == "OK"]
    cleared = [r for r in scored if r["dsr"] >= 0.95]
    closest = max(scored, key=lambda r: r["dsr"]) if scored else None
    variants = sum(r["trials"] for r in records if r["status"] == "OK")
    stamped = sum(1 for r in records if r["stamped"])
    markets = sorted({r["market"] for r in records})

    rows = []
    for r in sorted(records, key=lambda x: x["id"]):
        v, vc = verdict_of(r)
        if r["dsr"] is not None:
            pct = min(max(r["dsr"] / 0.95, 0), 1) * 100
            hot = " hot" if r["dsr"] >= 0.75 else ""
            meter = ('<div class="meter"><div class="track">'
                     '<div class="fill%s" style="width:%.0f%%"></div></div>'
                     '<span>%s</span></div>' % (hot, pct, fnum(r["dsr"], ".3f")))
        else:
            meter = '<div class="meter"><span>\u2014</span></div>'
        rows.append(
            '<tr data-market="%s"><td class="id">%s</td>'
            '<td class="nm"><a href="%s.html">%s</a>'
            '<span class="sub">%s &middot; %s versions</span></td>'
            '<td class="num">%s</td><td class="num dim">%s</td>'
            '<td>%s</td><td class="res %s">%s</td></tr>'
            % (esc(r["market"]), esc(r["id"]), esc(r["id"]), esc(r["label"]),
               esc(r["market"]), "{:,}".format(r["trials"]),
               fnum(r["best"]), fnum(r["null"]), meter, vc, esc(v)))

    close = ""
    if closest:
        close = (' The closest, <b>%s</b>, reached %.2f against the 0.95 it had '
                 'to beat.' % (esc(closest["label"]), closest["dsr"]))

    filters = ('<button aria-pressed="true" data-f="all">All</button>'
               + "".join('<button aria-pressed="false" data-f="%s">%s</button>'
                         % (esc(m), esc(m)) for m in markets))

    body = (
        '<div class="wrap"><header>'
        '<p class="eyebrow">Pre-registered &middot; Timestamped on Bitcoin &middot; Public</p>'
        '<h1><span class="glow">The strategies<br>that didn\'t work.</span></h1>'
        '<p class="lede">Thousands of trading strategies are sold as if they '
        'work. This is the public record of what happens when they are tested '
        'the way a statistician would test them.</p>'
        '<p class="lede"><b>So far, none have passed.</b>%s</p>'
        '<div class="metrics">'
        '<div class="metric"><b>%d</b><span>Strategy families</span></div>'
        '<div class="metric"><b>%s</b><span>Versions tested</span></div>'
        '<div class="metric"><b class="zero">%d</b><span>Passed</span></div>'
        '<div class="metric"><b>%d</b><span>Sealed on Bitcoin</span></div>'
        '</div></header>'
        '<section><h2>Why this is different</h2><div class="pillars">'
        '<div><span class="n">01</span><h3>Sealed before the test</h3>'
        '<p>What will be tested, and the score it has to beat, are written '
        'down, hashed, and timestamped onto the Bitcoin blockchain before the '
        'data is touched. The story cannot be rewritten once the answer is '
        'known.</p></div>'
        '<div><span class="n">02</span><h3>Luck is measured first</h3>'
        '<p>Test a thousand random strategies and the best will look brilliant '
        'by chance alone. Every result is scored against how good pure luck '
        'would have looked with the same number of tries.</p></div>'
        '<div><span class="n">03</span><h3>Nothing is hidden</h3>'
        '<p>Failures, near misses, and runs that had to be thrown away all stay '
        'on the record with the reason attached. A registry that deletes its '
        'own mistakes is asking not to be believed.</p></div>'
        '</div></section>'
        '<section><h2>The record</h2>'
        '<div class="bar">%s<span class="count" id="count"></span></div>'
        '<table><thead><tr><th>ID</th><th>Strategy</th><th>Best</th>'
        '<th>Luck</th><th>Score</th><th>Result</th></tr></thead>'
        '<tbody id="tb">%s</tbody></table>'
        '<p style="margin-top:28px;color:var(--mute);font-size:14.5px">'
        '<b>Best</b> is the top version\'s return adjusted for risk. '
        '<b>Luck</b> is what that version would have scored if none of them '
        'worked. <b>Score</b> is how likely the result is real rather than '
        'selection, and it has to reach 0.95. Open any row for the full '
        'record.</p></section>'
        '<footer>%s<p style="margin-top:20px" class="mono">Generated %s</p>'
        '</footer></div>'
        '<script>'
        'var tb=document.getElementById("tb"),cnt=document.getElementById("count");'
        'function upd(){var n=0;tb.querySelectorAll("tr").forEach(function(r){'
        'if(r.style.display!=="none")n++;});cnt.textContent=n+" records";}'
        'document.querySelectorAll(".bar button").forEach(function(b){'
        'b.addEventListener("click",function(){var f=b.dataset.f;'
        'document.querySelectorAll(".bar button").forEach(function(o){'
        'o.setAttribute("aria-pressed",String(o===b));});'
        'tb.querySelectorAll("tr").forEach(function(r){'
        'r.style.display=(f==="all"||r.dataset.market===f)?"":"none";});upd();});});'
        'upd();</script>'
        % (close, len(records), "{:,}".format(variants), len(cleared), stamped,
           filters, "".join(rows), FOOT,
           datetime.now(timezone.utc).strftime("%d %b %Y")))

    return shell("The strategies that didn't work", body,
                 "Trading strategies tested properly. Every claim sealed on "
                 "Bitcoin before the test runs, every result published.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "docs"))
    ap.add_argument("--root", default=HERE)
    args = ap.parse_args()

    records = collect(args.root)
    if not records:
        raise SystemExit("no sweeps found under %s/sweeps/" % args.root)

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(index_page(records))

    ordered = sorted(records, key=lambda r: r["id"])
    for i, r in enumerate(ordered):
        nav = []
        if i:
            nav.append('<a class="back" href="%s.html">&larr; %s</a>'
                       % (esc(ordered[i - 1]["id"]), esc(ordered[i - 1]["id"])))
        if i + 1 < len(ordered):
            nav.append('<a class="back" style="float:right" href="%s.html">%s &rarr;</a>'
                       % (esc(ordered[i + 1]["id"]), esc(ordered[i + 1]["id"])))
        pn = ('<section style="padding:30px 0">%s</section>' % "".join(nav)) if nav else ""
        with open(os.path.join(args.out, "%s.html" % r["id"]), "w",
                  encoding="utf-8") as fh:
            fh.write(record_page(r, pn))

    scored = [r for r in records if r["dsr"] is not None and r["status"] == "OK"]
    print("  %d records, %d scored, %d timestamped"
          % (len(records), len(scored),
             sum(1 for r in records if r["stamped"])))
    print("  -> %s/index.html + %d record pages" % (args.out, len(records)))


if __name__ == "__main__":
    main()
