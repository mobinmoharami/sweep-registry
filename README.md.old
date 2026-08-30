# sweep-registry

A registry of pre-registered strategy sweeps and their results — including,
especially, the ones that found nothing.

## Why

Everything we "know" about markets has passed through a filter: only what
worked got published. A thousand people test a strategy, 999 fail silently,
one succeeds and gets a following — even though statistically that one is
exactly what luck predicts. We built a field that only sees survivors.

This fixes one half of that. The search space, the protocol and the threshold
are written down and hashed **before** the test runs. Then the full result gets
published — the whole distribution, not just the best variant.

## The unit of publication

Not a strategy. A **region of strategy space**.

"RSI 14 didn't work on BTC" is worthless. "The entire mean-reversion family,
2,430 enumerated variants, across three symbols over six years, produced
nothing above a detection limit of 2.4 annualised Sharpe" is a scientific
claim someone can build on.

## Workflow

```bash
pip install numpy requests opentimestamps-client

# 0. get real bars (no API key, no account)
python data/fetch_binance_bulk.py BTCUSDT 1h 2017-08 2026-07
python data/fetch_binance_bulk.py ETHUSDT 1h 2017-08 2026-07
python data/fetch_binance_bulk.py SOLUSDT 1h 2020-08 2026-07

# 1. start a sweep (copies the template WITHOUT its seal)
python new_sweep.py SW-0002
$EDITOR sweeps/SW-0002/preregistration.json

# 2. freeze it — computes the detection limit, hashes, locks
python register.py sweeps/SW-0002

# 3. anchor the hash to Bitcoin. free, no account, only the hash leaves.
ots stamp sweeps/SW-0002/preregistration.sha256

# 4. run every enumerated variant -> returns.npy
python run_sweep.py sweeps/SW-0002

# 5. score it -> result.json + RECORD.md
python finalize.py sweeps/SW-0002

# 6. explain WHY it failed, calibrated against a null -> diagnostics.json
python diagnose.py sweeps/SW-0002 --null 10
```

Step 6 is optional but it is what turns "nothing worked" into a finding.
"No edge" has two very different causes that look identical in net returns:
there is no signal at all, or there is a signal and costs ate it. `diagnose.py`
decomposes every variant into gross returns, cost drag, turnover and market
beta, and says which one you are looking at. It reads the frozen document,
touches no holdout, and changes no verdict.

**Always run it with `--null`.** The instrument has its own bias: on a pure
random walk, with provably no signal, the first version of this diagnostic
reported "signal with inverted sign" and a residual Sharpe of -0.18. That
number was a property of the measurement, not the market — and publishing it
would have meant registering a false discovery in a registry built to prevent
exactly that. `--null` reruns the entire sweep on shuffled versions of the real
returns (same distribution, no serial structure) and reports how far the
observed value sits from what pure noise produces. Under about |z| = 2, claim
nothing.

Step 4 reads the frozen document and takes no arguments of its own. You
cannot quietly widen the search space after seeing a result — that would need
a new sweep id, and the old hash stays on the chain either way.

Step 3 is what separates this from a blog. Without it you cannot prove the
threshold was set before you saw the answer.

## The three numbers that matter

**Expected max Sharpe under the null.** Test 2,430 worthless strategies and
the best will still look good. This says exactly how good, by luck alone.
Anything below it is nothing.

**Detection limit.** The smallest true Sharpe this design could have found,
at 80% power. Without it, "we found nothing" might mean the edge wasn't there
— or that the instrument was too blunt to see it. Almost no published negative
result states this. State it and you are ahead of nearly everyone.

**PBO.** Across every in-sample / out-of-sample split, how often does the
in-sample winner land in the bottom half out of sample? Near 0.5 means the
selection procedure is a noise machine regardless of how good the best
backtest looked.

## Families

Twelve, each swept separately:

| family | what it tests |
|---|---|
| `zscore_reversion` `rsi_reversion` `bollinger_touch` | fade extremes |
| `zscore_continuation` `rsi_continuation` `bollinger_breakout` | follow extremes |
| `ma_cross` | moving average crossover — the most widely sold rule there is |
| `donchian_breakout` | turtle-style channel breakout |
| `atr_breakout` | volatility breakout |
| `momentum_roc` | time-series momentum |
| `vol_regime_momentum` | "it works if you filter for the right regime" |
| `intraday_seasonality` | hour-of-day effects |
| `fair_value_gap` `order_block` `liquidity_sweep` `break_of_structure` | smart money concepts |
| `engulfing` `inside_bar_breakout` | classic price action patterns |

`examples/templates/` has a ready pre-registration per family, and `run_all.sh`
registers, timestamps, runs and scores every one that is not done yet.

**One family per sweep.** Never merge them. Every variant added to a sweep
raises the multiple-testing bar for everything else in it — 1,620 variants put
the detection limit at 4.0 annualised Sharpe, 20,000 pushes it to 4.4. Ten
clean sweeps beat one enormous one, and "test as much as possible" quietly
destroys your ability to detect anything.

**Only mechanically definable concepts are included.** Smart money and price
action ideas are usually traded discretionarily, and that is exactly what makes
most of them untestable: if a human decides which order block "counts", a null
result proves nothing, because the answer will always be that it was
implemented wrong. So the definition is written into the pre-registration and
hashed before the test runs — the objection has to be raised in advance or not
at all. Market structure reading, "context", and anything needing a chosen
higher-timeframe bias are deliberately excluded rather than approximated.

The flip side is stated in every one of those pre-registrations: a null
falsifies the mechanical rule, not every possible discretionary application.
Claiming more than that would be the same overreach this project documents.

Before trusting a new family, run it on a random walk with costs set to zero.
Nothing should show an edge. Every family here passes that check; if one you
add does not, it is reading the future.

## Markets

Crypto (Binance, hourly) and FX (Dukascopy, hourly). Same families, same
protocol, different asset class.

```bash
./fetch_fx.sh                 # EURUSD, GBPUSD, USDJPY — slow, ~1h per pair
bash run_all.sh               # picks up every template not yet scored
```

Seven crypto sweeps over one market and one period are not seven independent
results — they are seven views of one sample. FX has different participants,
different microstructure, and far lower costs (1.5 bps round trip against 6.0),
which means a smaller true edge would survive there. A null in FX is therefore
stronger evidence than a null in crypto, and a pattern appearing in both is the
first evidence that it belongs to markets rather than to one dataset.

**Adding timeframes is not the same as adding markets.** Running the same
families on 5m, 15m, 4h and daily multiplies the search space without adding
independent evidence: same market, same period, more chances to find noise.
It also breaks in both directions — daily leaves ~2,900 bars and no statistical
power, 5m puts costs above any plausible signal. Add a timeframe only to test a
stated prediction ("the effect should be stronger at 4h because costs bite
less"), never to see what turns up.

**Closed markets are handled explicitly.** FX stops from Friday ~22:00 UTC to
Sunday ~22:00 UTC. Those bars are absent and never filled — a filled weekend
bar has zero return and zero range, which mean reversion rules read as signal
and volatility rules read as calm. The engine additionally zeroes the return
across every closure and holds no position through one, so a few Sunday opens
cannot dominate a sweep.

## Cross-sectional sweeps

A different shape of question. The time-series engine asks "should I be long
this asset now"; the cross-sectional one asks "which of these twenty is best
right now" — long the top fraction, short the bottom, rebalanced periodically.

```bash
python data/build_universe.py --top 20 --start 2019-01 --end 2025-06
# then download every symbol the universe ever held
python run_xs_sweep.py sweeps/SW-0029
python finalize.py sweeps/SW-0029
```

Two reasons this matters more than another price rule:

**It cannot inherit a market trend.** A dollar-neutral portfolio is
market-neutral by construction, so the Bitcoin uptrend that contaminated the
time-series crypto results cannot produce a false effect here.

**It is where the published evidence actually is.** Cross-sectional momentum
has real academic support in crypto. A null here is the most informative null
in the registry.

### Survivorship is the whole difficulty

Taking today's top 20 coins and backtesting them over six years invents an edge
that never existed, because every coin that died has been deleted from the
list. Ammann, Burdorf, Liebi and Stockl (SSRN 4287573) measured an annualised
survivorship bias of **62.19%** for equal-weighted crypto portfolios across
3,904 coins.

`build_universe.py` therefore rebuilds membership month by month from the
*previous* month's volume, using Binance's archive — which, unlike Kraken's
export, retains delisted pairs. A coin is held in the months it was genuinely
in the top 20, and dropped when it stopped being. `run_xs_sweep.py` warns
loudly if a symbol the universe selected has no local data, because silently
skipping it puts the bias straight back in.

### A crashed run must not look like a result

`finalize.py` refuses to score a returns matrix where every variant has Sharpe
exactly zero. An all-zero matrix produces DSR = 0.5 and prints "NO EDGE FOUND",
which is indistinguishable from a genuine null — and a record that looks like a
finding but is actually a crashed run is the worst thing this registry could
publish. Three cross-sectional sweeps were scored that way before the guard
existed; they are kept in the registry, marked as void.

If a sweep aborts with that message, check that `active_variants.json` exists
next to `returns.npy`. If it does not, the runner died partway through.

## Two decision rules

`decision_rule.metric` picks what the sweep is actually testing.

**`deflated_sharpe_ratio`** — does the *best* variant beat what selection alone
would produce? Answers "is there a tradable rule in here". Insensitive: over
~8 years and 1,620 variants the detection limit is around 4.0 annualised
Sharpe, so it can only see very large edges.

**`cross_sectional_residual_sharpe_z`** — does the *whole population* of
variants have a mean market-neutral gross Sharpe that shuffled data cannot
produce? Answers "does this family of ideas point anywhere". Pooling every
variant makes it roughly twenty times more sensitive — detection limit around
0.18 — but it says nothing about whether any individual rule is tradable, and
it is scored from `diagnose.py --null`, which `finalize.py` will demand.

Most families will fail the first and can still say something real under the
second. Choose before you freeze, and never after.

## Power before you spend the holdout

Compute the power of a confirmatory test *before* running it. A holdout can be
spent exactly once, and running it underpowered wastes it on a coin flip.

Worked example from SW-0004. The effect under test is 0.336 and the null sd
scales as 1/sqrt(n):

| window | bars | null sd | detection limit | power |
|---|---|---|---|---|
| 12 months | 8,760 | 0.173 | 0.493 | 48% |
| 24 months | 17,520 | 0.123 | 0.348 | 77% |
| 26 months | 19,000 | 0.118 | 0.335 | 80% |

Running it in 2026 would have burned the only independent test available on
something barely better than chance. So the sweep is **frozen now and executed
later**: the claim is hashed and timestamped today, the data arrives in 2027.
That is pre-registration in the medical sense, and `run_sweep.py` enforces it —
set `planning.earliest_run_date` and it refuses to run before that date.

## Mirror families are not an independent test

SW-0003 mirrored SW-0002 exactly: same indicators, same parameters, entries
flipped. Every statistic came back as the precise arithmetic negative of the
original, to four decimal places — gross Sharpe -0.2901 became +0.2901, z of
-5.542 became +5.542. No new information entered. An exact position-wise
inversion is an identity, not a replication.

It was still worth running, and it stays in the registry. Deleting a sweep
because it turned out to be uninformative is the same selective reporting this
project exists to document.

Real independence needs new data. That is what SW-0004 is for.

## Confirmatory vs exploratory

Anything discovered by staring at a finished sweep is exploratory, however
convincing. It becomes a finding only when the same claim is written down in a
fresh pre-registration, hashed, and run again.

```bash
python annotate.py sweeps/SW-0002 \
  --confirmatory "what the frozen document tested, and the verdict" \
  --exploratory  "what was noticed afterwards" \
  --note "caveats, excluded variants, warnings"

python annotate.py sweeps/SW-0029 --status VOID --reason "..."
```

Annotations land in `annotations.json` and render into `RECORD.md` under
headings that mark them as added after the fact. The frozen pre-registration,
its hash and `result.json` are never touched — if they were, the timestamp
would prove nothing.

`annotate_all.sh` applies the annotations decided on 2026-08-01.

## Underpowered tests are still worth registering

SW-0035 tests the one finding that came close, and its own pre-registration
states that it will probably fail to resolve anything. The standard error of an
annualised Sharpe over n bars is sqrt(8760/n), so confirming a true Sharpe of
0.72 at z=2 with 80% power needs roughly 136,000 hourly bars — about 15.6
years. Four years gives around 29%.

Switching to a per-asset information coefficient does not rescue it either: the
implied IC is about 0.008, and asset-periods are not independent because assets
move together.

Registering it anyway, with the limitation stated up front, is the honest move.
The alternative is to quietly pick whichever window makes the result look
decisive. An effect this size may simply not be confirmable by a solo
researcher on public data — and if so, that is itself worth recording.

## Rules that are not negotiable

1. **A frozen pre-registration is never edited.** `register.py` refuses to
   overwrite one, and `finalize.py` refuses to run if the hash has moved.
   Changed your mind? New `sweep_id`. This rule exists to protect you from
   yourself, not to satisfy anyone else.
2. **Publish the whole distribution, not the maximum.** The shape of the
   distribution is what shows whether a result came from noise. It is also
   the one thing a signal seller cannot fake.
3. **Publish the positives with equal prominence.** A registry that only ever
   reports failure is not a reference, it is a campaign — and nobody will cite
   it in ten years.
4. **The holdout stays sealed** until the verdict is written. Not peeked at,
   not summarised, not "just checked quickly."
5. **Report claims, never accuse people.** "This approach was registered on
   this date and returned this" is unfalsifiable and unsueable. "X is a fraud"
   is neither.

## Worked example

`examples/SW-0001-crypto-mean-reversion/` — a frozen pre-registration for a
2,430-variant mean-reversion sweep. Detection limit: 2.38 annualised Sharpe.

Sanity check the machinery on pure noise, where the answer must be "nothing":

```python
import numpy as np
rng = np.random.default_rng(7)
np.savetxt('returns.csv', rng.normal(0, 0.01, (2000, 300)), delimiter=',')
```

The best of those 300 random variants shows an annualised Sharpe of 6.6 —
which looks spectacular until you see that the expected best under pure luck
was 6.4. DSR lands at 0.54, far below the 0.95 threshold. Verdict: no edge.

That gap between "looks spectacular" and "is exactly what luck predicts" is
the entire subject of this project.

## Resources

A 1,620-variant sweep over ~68,000 hourly bars takes about **7 seconds**, with
roughly **550 MB of RAM** and **450 MB of disk**. Returns stream into a
memory-mapped `returns.npy` rather than being assembled in RAM — building the
whole matrix in memory needs several times that and gets killed on a small VPS.

Two things make it fast, both worth preserving if you extend the engine:

- **`returns.npy` is stored as (variant, observation), not the other way
  round.** Writing each variant into a *column* of a row-major memmap touches
  every page of the file on every write. That one detail was 96% of the
  runtime — 206 seconds of the original 213.
- **Indicators are cached per lookback, and the uncapped position series per
  (family, lookback, threshold, exit rule).** Wilder's RSI is recursive;
  recomputing it for all 540 RSI variants instead of the 6 distinct lookbacks
  is pure waste.

If it still gets killed: cut the symbol list, or prune the parameter grid.
Do not "fix" it by silently narrowing the search space after freezing — that
is a new sweep with a new id.

Note the cost of a short symbol: all symbols are aligned to the shortest
history, so adding one that listed recently throws away years of the others.
Weigh that before including it.

## Data provenance

Binance silently rewrites historical klines — their own `updates/` folder
lists the revisions. So "I used BTCUSDT 1h" is not a reproducible claim.
`fetch_binance_bulk.py` verifies every file against Binance's SHA256 and
writes `data/manifest/<SYMBOL>_<INTERVAL>_<MARKET>.json` recording each
file's URL, hash, byte count and download time.

Publish that manifest with every record. Never publish the raw bars —
exchange terms do not permit redistribution, and derived statistics plus a
manifest plus the download script are what let someone else rebuild the
identical dataset anyway.

Gaps are reported, never filled. A missing bar is exchange downtime, which
is information.

## The public site

```bash
python build_site.py            # -> site/index.html
python build_site.py --out /var/www/registry
```

Reads every `sweeps/*/` directory and renders one self-contained page. No
number is typed by hand in the generator — change a record, rerun it.

Writes `index.html` plus one page per record. No number is typed by hand in the
generator: change a record, rerun it.

Every statistical term is renamed for someone who has not read Bailey and Lopez
de Prado. "Best" is the top variant's Sharpe, "Luck" is the expected maximum
under the null, "Score" is the Deflated Sharpe Ratio against its 0.95 bar. Each
record page charts the best result against luck and against the detection floor,
and shows the spread across every variant, because publishing only the maximum
is the exact practice this registry exists to document.

Confirmatory and exploratory findings are visually separated on every record
page: blue for what the sealed document predicted, amber for what was noticed
afterwards. Void records stay visible with their reason attached. A registry
that hides its own mistakes is asking to be disbelieved.

## The web app

The static generator stays for archival copies. The app is the live surface:
same records, plus search, sorting, per-record pages, a public API, and a
submission queue.

```bash
pip install flask
ADMIN_TOKEN=$(openssl rand -hex 16) python app/server.py     # picks a free port
sudo bash app/deploy.sh registry.example.com                 # systemd + nginx
```

The port is not hardcoded. This box runs several projects at once, so both the
app and the deploy script scan 8400-8999 for something free, and the chosen
port is written to `.port` so a restart keeps the same URL. `PORT=8477` forces
one, and the app says so and moves on if it is taken.

Three design decisions worth keeping:

**SQLite, not Postgres.** The registry might receive a few hundred submissions
a year. A separate database service would add operational surface without
adding capability, and backup is copying one file.

**No accounts.** A submitter gets a link, not a password. Nothing to breach.

**Submissions queue; they never auto-publish.** A registry that runs whatever
anyone types fills up with rules like "RSI but with market context", which
cannot be falsified — and one unfalsifiable record devalues every real one. The
review gate is the product, not friction to be removed once there is traffic.

The database is an index and a queue. The authority is still `sweeps/`: frozen
JSON, hashes, OpenTimestamps proofs. Lose `registry.db` and you lose the queue,
not the science.

## Generated pages

Around 300-500 pages beyond the records: one per strategy family, per
family-and-market, per family-and-symbol, plus question pages ("does X work",
"is X profitable"), popular settings ("RSI 14", "the golden cross"),
head-to-head comparisons, and method explainers.

```
app/content.py   hand-written editorial per family: the claim, the honest
                 case for it, and the specific catch
app/seo.py       route generation, driven by the real records
```

**Deliberately not generated: a page per parameter combination.** That would be
17,000 pages, which is exactly what Google names "scaled content abuse" and has
been deindexing sites for since March 2024. It would also be worthless, because
nobody searches for "RSI period 37 threshold 2.5 exit mean_touch" — zero
traffic, bought at the cost of the domain's credibility.

The rule for adding a page: a real person plausibly types the query, AND the
page says something the other pages do not. Every number comes from the frozen
records, so rerunning a sweep updates the pages with it. The full 17,000
combinations stay available through the record pages and the API, just not as
indexed pages.

## Files

| | |
|---|---|
| `register.py` | validate, compute detection limit, freeze, hash |
| `finalize.py` | verify hash, score, emit `result.json` + `RECORD.md` |
| `srlab/stats.py` | expected max Sharpe, DSR, critical Sharpe, detection limit |
| `srlab/pbo.py` | CSCV probability of backtest overfitting |
| `examples/SW-0003-continuation-template.json` | worked cross-sectional pre-registration |
| `srlab/canonical.py` | deterministic JSON hashing |
| `new_sweep.py` | start a sweep from a template, seal not carried over |
| `run_sweep.py` | enumerate + backtest every variant from the frozen doc |
| `diagnose.py` | gross vs net decomposition — mechanism, not just verdict |
| `annotate.py` | post-hoc notes and status, frozen files untouched |
| `build_site.py` | renders a static archival copy of the records |
| `app/server.py` | the live site: records, search, API, submissions |
| `app/db.py` | SQLite queue and votes |
| `app/deploy.sh` | systemd + nginx install |
| `sweep/families.py` | vectorised strategy families |
| `sweep/engine.py` | costs, shifting, turnover, net returns |
| `data/fetch_binance_bulk.py` | crypto: bulk monthly zips + SHA256 manifest |
| `data/fetch_dukascopy.py` | FX: tick data aggregated to bars, weekend-aware |
| `data/fetch_binance.py` | REST fallback, resumable, slower |

## Build order

Registration engine first. Public UI last. A beautiful site with zero records
is worth nothing; an ugly one that has been accumulating pre-registered results
for three years is worth a great deal. The value is in the age of the record,
not the design of the page.
