"""Editorial content behind the SEO pages.

WHY THIS FILE IS HAND-WRITTEN AND NOT GENERATED

The obvious way to get 17,000 pages is to loop over every parameter
combination and fill a template. Google calls that "scaled content abuse" and
has been deindexing sites for it since March 2024. Worse, nobody searches for
"RSI period 37 threshold 2.5 exit mean_touch" — the traffic would be zero and
the credibility cost permanent.

So pages are only generated where a real person plausibly types the query AND
the page has something specific to say. That means every family needs
hand-written material: what the claim actually is, who sells it, why it sounds
plausible, and what the numbers came back as. The generator combines that
with real per-record data; it never invents prose.

Roughly 400-500 pages come out of this, each with a reason to exist.
"""
from __future__ import annotations

# --------------------------------------------------------------------------
# Per-family editorial. `claim` is what proponents say, in their words.
# `why_plausible` is the strongest honest case for it — stated properly,
# because a page that strawmans the claim convinces nobody.
# `catch` is the specific reason it tends not to survive testing.
# --------------------------------------------------------------------------
FAMILIES = {
    "rsi_reversion": {
        "label": "RSI reversion",
        "aka": ["RSI oversold bounce", "RSI 30/70 strategy", "RSI mean reversion"],
        "claim": "Buy when RSI drops below 30, sell when it rises above 70. "
                 "The market is oversold or overbought and will revert.",
        "why_plausible": "Prices really do oscillate, and after a sharp move "
                         "in one direction a pause or pullback is common. RSI "
                         "measures exactly that kind of stretch, so the signal "
                         "is not arbitrary — it is tracking something real.",
        "catch": "A stretched market can stay stretched. RSI going below 30 "
                 "during a genuine downtrend keeps firing buy signals all the "
                 "way down, and those losses are larger than the gains from "
                 "the bounces that do happen.",
        "sold_as": "the first indicator in almost every trading course",
    },
    "zscore_reversion": {
        "label": "Z-score reversion",
        "aka": ["standard deviation reversion", "statistical mean reversion"],
        "claim": "When price moves more than two standard deviations from its "
                 "moving average, bet on a return to the average.",
        "why_plausible": "This is the cleanest statistical statement of mean "
                         "reversion, and in genuinely range-bound markets it "
                         "describes the behaviour well.",
        "catch": "The standard deviation is computed from the same recent "
                 "window that is trending, so it widens as the trend "
                 "continues. The signal weakens precisely when it would need "
                 "to be strongest.",
        "sold_as": "the quantitative upgrade to RSI",
    },
    "bollinger_touch": {
        "label": "Bollinger band touch",
        "aka": ["Bollinger band bounce", "Bollinger reversal"],
        "claim": "Price touching the lower Bollinger band is a buy; touching "
                 "the upper band is a sell.",
        "why_plausible": "The bands are a volatility envelope, so a touch does "
                         "mark an unusual move relative to recent conditions.",
        "catch": "Bollinger himself said the bands are not a standalone "
                 "signal. In a trend, price walks along a band for long "
                 "stretches, firing signals continuously against the move.",
        "sold_as": "a chart pattern anyone can see at a glance",
    },
    "ma_cross": {
        "label": "Moving average crossover",
        "aka": ["golden cross", "death cross", "50/200 crossover", "EMA cross"],
        "claim": "When a fast moving average crosses above a slow one, the "
                 "trend has turned up. Buy the golden cross, sell the death cross.",
        "why_plausible": "Trends exist, and a crossover is a simple way to "
                         "notice one has changed direction. It is also almost "
                         "impossible to misapply, which is a real virtue.",
        "catch": "A crossover is a lagging confirmation of a move that has "
                 "already happened. In choppy conditions it whipsaws, and the "
                 "cost of the false signals exceeds what the real trends pay.",
        "sold_as": "the single most widely taught rule in technical analysis",
    },
    "donchian_breakout": {
        "label": "Donchian channel breakout",
        "aka": ["turtle trading", "20-day breakout", "channel breakout"],
        "claim": "Buy when price closes above the highest high of the last N "
                 "bars. This is the rule the Turtle Traders used.",
        "why_plausible": "The original Turtle experiment did produce real "
                         "returns, and breakout logic has an honest rationale: "
                         "a new extreme means the previous balance has broken.",
        "catch": "The Turtles traded diversified futures on daily bars in the "
                 "1980s with a full risk framework. Applying the entry rule "
                 "alone to hourly crypto is a different strategy wearing the "
                 "same name.",
        "sold_as": "the strategy that turned beginners into millionaires",
    },
    "atr_breakout": {
        "label": "ATR volatility breakout",
        "aka": ["volatility breakout", "ATR channel"],
        "claim": "When price moves more than N times the average true range "
                 "away from its mean, a real move has begun. Follow it.",
        "why_plausible": "Scaling the threshold by volatility is genuinely "
                         "better than a fixed percentage, because it adapts to "
                         "conditions instead of assuming them.",
        "catch": "Volatility clusters. Large ATR moves arrive together, so the "
                 "signal fires most often in exactly the conditions where "
                 "slippage and spread are worst.",
        "sold_as": "the professional's breakout filter",
    },
    "momentum_roc": {
        "label": "Time-series momentum",
        "aka": ["rate of change strategy", "trend following", "absolute momentum"],
        "claim": "Buy what has been going up over the last N bars and short "
                 "what has been going down.",
        "why_plausible": "Time-series momentum has genuine academic support at "
                         "monthly horizons across asset classes. This is not a "
                         "made-up idea.",
        "catch": "The published evidence is monthly and cross-asset. At hourly "
                 "horizons on two crypto pairs the effect is far smaller and "
                 "the trading costs are far larger.",
        "sold_as": "the one anomaly that academics agree on",
    },
    "vol_regime_momentum": {
        "label": "Volatility-filtered momentum",
        "aka": ["regime filter", "low volatility trend following"],
        "claim": "Momentum works, but only in the right regime. Trade it only "
                 "when volatility is low.",
        "why_plausible": "Regime dependence is real, and filtering does change "
                         "the return distribution in measurable ways.",
        "catch": "Adding a filter adds a parameter, which raises the bar a "
                 "result has to clear. In this registry the filtered version "
                 "did not beat the unfiltered one by enough to justify itself.",
        "sold_as": "the fix for why your trend strategy stopped working",
    },
    "fair_value_gap": {
        "label": "Fair value gap",
        "aka": ["FVG", "imbalance", "ICT fair value gap", "liquidity void"],
        "claim": "A three-bar gap where price moved so fast it left an "
                 "imbalance. Price returns to fill it.",
        "why_plausible": "Rapid moves do leave thin areas in the order book, "
                         "and revisits are common enough to be noticeable.",
        "catch": "Revisits being common is not the same as revisits being "
                 "profitable. Price revisits most levels eventually; the "
                 "question is whether entering there beats entering anywhere "
                 "else, and here it did not.",
        "sold_as": "the core of ICT and smart money concepts",
    },
    "order_block": {
        "label": "Order block",
        "aka": ["OB", "institutional order block", "supply and demand zone"],
        "claim": "The last opposite candle before a strong move marks where "
                 "institutions accumulated. Price returns there and bounces.",
        "why_plausible": "Large participants do work orders at specific levels "
                         "and those levels can matter.",
        "catch": "The definition identifies the level after the move it is "
                 "supposed to have caused. Every strong move has a last "
                 "opposite candle before it, whether or not anything "
                 "institutional happened.",
        "sold_as": "how to trade like the banks",
    },
    "liquidity_sweep": {
        "label": "Liquidity sweep",
        "aka": ["stop hunt", "liquidity grab", "sweep of highs", "turtle soup"],
        "claim": "Price pushes past an obvious high to trigger stops, then "
                 "reverses. Trade against the sweep.",
        "why_plausible": "Stop clusters above prior highs are real, and "
                         "sweeps followed by reversals genuinely happen.",
        "catch": "They also genuinely happen followed by continuation. This is "
                 "the most falsifiable smart-money claim, which is why it is "
                 "worth testing — and it did not survive.",
        "sold_as": "proof that the market is hunting your stops",
    },
    "break_of_structure": {
        "label": "Break of structure",
        "aka": ["BOS", "market structure shift", "CHoCH", "structure break"],
        "claim": "A decisive close beyond a prior swing point signals the "
                 "trend has changed. Trade in the new direction.",
        "why_plausible": "Trends do change and something must mark the change. "
                         "A close beyond a prior extreme is a reasonable marker.",
        "catch": "Only the mechanical version can be tested: which swing "
                 "counts is normally a human judgement, and any rule that "
                 "needs a human to decide what counts cannot be falsified.",
        "sold_as": "the foundation of market structure reading",
    },
    "engulfing": {
        "label": "Engulfing candle",
        "aka": ["bullish engulfing", "bearish engulfing", "engulfing pattern"],
        "claim": "A candle whose body swallows the previous one signals a "
                 "reversal.",
        "why_plausible": "It is the oldest documented candlestick pattern and "
                         "describes a genuine shift in intra-bar control.",
        "catch": "Engulfing candles are extremely common. A pattern that "
                 "appears constantly cannot carry much information, and the "
                 "test confirms it does not.",
        "sold_as": "candlestick pattern trading, taught for three centuries",
    },
    "inside_bar_breakout": {
        "label": "Inside bar breakout",
        "aka": ["NR7", "range contraction", "coiling pattern", "compression"],
        "claim": "A bar inside the previous bar's range means compression. "
                 "Trade the breakout when it resolves.",
        "why_plausible": "Volatility does cluster and quiet periods are "
                         "followed by active ones. The compression is real.",
        "catch": "Compression predicts that a big move is coming. It says "
                 "nothing about the direction, and direction is the entire "
                 "problem.",
        "sold_as": "price action trading without indicators",
    },
    "intraday_seasonality": {
        "label": "Hour-of-day seasonality",
        "aka": ["time of day trading", "session bias", "London open strategy"],
        "claim": "Certain hours of the day are systematically bullish or "
                 "bearish. Trade the session.",
        "why_plausible": "In FX, sessions genuinely differ: London and New "
                         "York open bring real volume changes.",
        "catch": "Calendar effects are the easiest patterns to find by "
                 "accident, because there are only 24 hours to try and "
                 "something always looks best. This is why the multiple-"
                 "testing correction matters most here.",
        "sold_as": "the edge that requires no chart reading",
    },
    "xs_momentum": {
        "label": "Cross-sectional momentum",
        "aka": ["relative strength", "ranking strategy", "long short momentum"],
        "claim": "Rank assets by recent return, buy the strongest and short "
                 "the weakest.",
        "why_plausible": "This has the most serious academic support of "
                         "anything in this registry, across decades and asset "
                         "classes, and it is market-neutral by construction.",
        "catch": "It came closer than anything else here and still did not "
                 "clear the bar. The effect it appears to show is roughly half "
                 "the size this test could reliably detect.",
        "sold_as": "what actual quant funds run",
    },
    "xs_reversal": {
        "label": "Cross-sectional reversal",
        "aka": ["short term reversal", "loser buying", "relative weakness"],
        "claim": "Buy the recent losers and short the recent winners; "
                 "relative performance reverts.",
        "why_plausible": "Short-horizon reversal is documented in equities and "
                         "is the standard competing hypothesis to momentum.",
        "catch": "In this data it was the mirror of momentum and lost by the "
                 "same margin momentum won by, which is close to arithmetic "
                 "rather than evidence.",
        "sold_as": "the contrarian's answer to momentum",
    },
    "xs_vol_scaled_momentum": {
        "label": "Volatility-scaled cross-sectional momentum",
        "aka": ["risk adjusted momentum", "Sharpe ranking"],
        "claim": "Rank by return divided by volatility rather than raw return, "
                 "so the wildest assets do not dominate.",
        "why_plausible": "The refinement is sensible and standard: raw returns "
                         "let the most volatile assets take over the ranking "
                         "regardless of signal quality.",
        "catch": "It scored marginally higher than plain cross-sectional "
                 "momentum, by far too little to call a difference.",
        "sold_as": "the professional refinement of momentum",
    },
    "zscore_continuation": {
        "label": "Z-score continuation",
        "aka": ["statistical trend following"],
        "claim": "When price stretches far from its average, the move has "
                 "power. Follow it rather than fading it.",
        "why_plausible": "It is the exact inverse of mean reversion, and if "
                         "reversion loses money then following should make it.",
        "catch": "Because it is an exact position-wise inversion, its results "
                 "are the arithmetic negative of the reversion test. That is "
                 "an identity, not independent evidence.",
        "sold_as": "the fix for traders tired of catching falling knives",
    },
    "rsi_continuation": {
        "label": "RSI continuation",
        "aka": ["RSI trend following", "RSI momentum"],
        "claim": "High RSI means strength, not exhaustion. Buy strength "
                 "instead of selling it.",
        "why_plausible": "In strong trends RSI does stay elevated for long "
                         "periods, which is the standard complaint about using "
                         "it as a reversal signal.",
        "catch": "Same identity problem as z-score continuation, and the same "
                 "cost drag once the position is actually traded.",
        "sold_as": "the advanced way to read RSI",
    },
    "bollinger_breakout": {
        "label": "Bollinger band breakout",
        "aka": ["band riding", "Bollinger squeeze breakout"],
        "claim": "A close outside the band is a breakout to follow, not a "
                 "reversal to fade.",
        "why_plausible": "Band walks during trends are well documented, and "
                         "this reading is closer to Bollinger's own advice "
                         "than the bounce version.",
        "catch": "The bands widen as volatility rises, so the breakout "
                 "threshold moves away exactly when a move gets going.",
        "sold_as": "how the bands were meant to be used",
    },
}

# --------------------------------------------------------------------------
# Concept pages. These are the highest-value SEO targets in the whole set:
# low competition, high intent, and the registry has first-hand material.
# --------------------------------------------------------------------------
CONCEPTS = [
    {
        "slug": "why-your-backtest-lies",
        "title": "Why your backtest lies",
        "question": "Why do backtests look good and live trading does not?",
        "body": [
            "A backtest is a search. You try a rule, it looks poor, you adjust "
            "the lookback, you change the exit, you try another pair. By the "
            "time something looks good you have run dozens of tests and kept "
            "the best one.",
            "That last step is the problem. The best of fifty random "
            "strategies looks impressive even when all fifty are worthless — "
            "not sometimes, but reliably, as a matter of arithmetic. In this "
            "registry the expected best result from pure luck is computed for "
            "every sweep and printed next to the actual best. In several "
            "cases the real best did not even reach it.",
            "Nothing about this requires anyone to be dishonest. The search "
            "does it on its own, silently, and the only defence is to fix what "
            "you are testing and what counts as passing before you look.",
        ],
        "related": ["deflated-sharpe-ratio", "multiple-testing-in-trading"],
    },
    {
        "slug": "deflated-sharpe-ratio",
        "title": "The Deflated Sharpe Ratio, explained simply",
        "question": "What is the Deflated Sharpe Ratio and how do you use it?",
        "body": [
            "An ordinary Sharpe ratio answers: how much return did this get "
            "for the risk it took? It cannot tell you whether the strategy was "
            "picked out of a thousand candidates, and that changes everything.",
            "The Deflated Sharpe Ratio, from Bailey and López de Prado, "
            "corrects for the search. Given how many variants were tried and "
            "how much their results varied, it asks how likely the best one is "
            "to be real rather than the luckiest. The answer is a probability, "
            "and the usual bar is 0.95.",
            "Two things it needs that people rarely supply: the true number of "
            "trials, including the ones abandoned quietly, and the length of "
            "the track record. Both are fixed in advance and published for "
            "every sweep in this registry.",
        ],
        "related": ["why-your-backtest-lies", "minimum-detectable-edge"],
    },
    {
        "slug": "probability-of-backtest-overfitting",
        "title": "Probability of Backtest Overfitting (PBO)",
        "question": "What is PBO and what does a PBO of 0.5 mean?",
        "body": [
            "PBO asks a blunt question: if you split the history in half, pick "
            "the variant that did best in the first half, and then look at how "
            "it ranked in the second, how often does it land in the bottom "
            "half?",
            "Done across every possible split, that fraction is the "
            "Probability of Backtest Overfitting. At 0.5 the selection "
            "procedure is a coin flip — whatever made a variant look best "
            "in-sample carries no information about the future at all.",
            "A high Deflated Sharpe with a PBO near 0.5 is a specific "
            "warning: the family may have a uniform tilt, but choosing between "
            "its variants is noise. Both numbers appear on every record here.",
        ],
        "related": ["deflated-sharpe-ratio", "why-your-backtest-lies"],
    },
    {
        "slug": "minimum-detectable-edge",
        "title": "The number almost nobody reports",
        "question": "What does it mean when a backtest finds nothing?",
        "body": [
            "\"We tested it and found nothing\" has two completely different "
            "meanings, and most published results do not distinguish them. "
            "Either there was nothing to find, or the test was too blunt to "
            "see what was there.",
            "The minimum detectable edge separates them. It is the smallest "
            "real advantage the test could have caught, given how much data "
            "there was and how many variants were tried. Below it, a genuine "
            "edge would be invisible.",
            "Every record in this registry states its own limit. Several sit "
            "around a Sharpe of 2 to 4 per year — meaning a strategy earning a "
            "perfectly respectable Sharpe of 1 would pass through undetected. "
            "That is a real limitation, and printing it is the difference "
            "between a null result and a claim of proof.",
        ],
        "related": ["deflated-sharpe-ratio", "pre-registration-in-trading"],
    },
    {
        "slug": "pre-registration-in-trading",
        "title": "Pre-registration, borrowed from medicine",
        "question": "What is pre-registration and why does trading need it?",
        "body": [
            "Drug trials must be registered before they run: the hypothesis, "
            "the measure, and what counts as success, all filed publicly in "
            "advance. The reason is that without it, a trial that fails gets "
            "quietly reframed until something looks significant.",
            "Trading research has no such requirement and shows exactly the "
            "symptoms you would predict. Strategies are published when they "
            "work and forgotten when they do not, so the visible record is a "
            "survey of survivors.",
            "This registry applies the medical convention. The search space, "
            "the data, the costs and the passing score are written down, "
            "hashed, and timestamped onto the Bitcoin blockchain before the "
            "data is touched. Anyone can verify the document predates the "
            "result.",
        ],
        "related": ["why-your-backtest-lies", "survivorship-bias-in-crypto"],
    },
    {
        "slug": "survivorship-bias-in-crypto",
        "title": "Survivorship bias in crypto backtests",
        "question": "Why does backtesting today's top coins inflate returns?",
        "body": [
            "Take the twenty largest coins today and backtest them over six "
            "years and you will produce excellent results. Every coin that "
            "died has already been removed from the list, so the sample "
            "contains only the ones that made it.",
            "The size of the effect has been measured. Ammann, Burdorf, Liebi "
            "and Stöckl studied 3,904 coins and found an annualised "
            "survivorship bias of 62.19% for equal-weighted portfolios.",
            "The fix is to rebuild the universe as of each past date, using "
            "only what was known then. This registry ranks by the previous "
            "month's volume and keeps coins in for the months they actually "
            "traded. Across six and a half years, 184 different symbols passed "
            "through 20 slots.",
        ],
        "related": ["pre-registration-in-trading", "why-your-backtest-lies"],
    },
    {
        "slug": "trading-costs-kill-edges",
        "title": "When the signal is real and costs eat it",
        "question": "Why do profitable-looking strategies lose money live?",
        "body": [
            "There is a failure mode that looks identical to having no signal "
            "and is not: the pattern is real, and trading it costs more than "
            "it pays.",
            "Every record here separates the two. Gross return is what the "
            "rule produced before costs; net is what survives 6 basis points "
            "round trip in crypto and 1.5 in FX. Several families showed "
            "positive gross returns and negative net ones.",
            "This is also why higher frequency is not a free improvement. More "
            "bars mean more statistical power and more trades, and more trades "
            "mean the cost term grows faster than the signal does.",
        ],
        "related": ["minimum-detectable-edge", "why-your-backtest-lies"],
    },
    {
        "slug": "multiple-testing-in-trading",
        "title": "Multiple testing, or why 1,000 backtests find nothing",
        "question": "How many strategies can you test before results mean nothing?",
        "body": [
            "Test one strategy at the usual 5% significance level and there is "
            "a one in twenty chance of a false positive. Test a thousand and "
            "you should expect around fifty strategies to look significant "
            "even if every single one is worthless.",
            "Bailey and colleagues put a number on it: with only five years of "
            "data, no more than about forty-five independent configurations "
            "should be tried before you are essentially guaranteed to produce "
            "an in-sample Sharpe of 1 with an expected out-of-sample Sharpe of "
            "zero.",
            "That is why the number of variants is fixed and published before "
            "each sweep in this registry, and why every result is scored "
            "against the expected best under pure luck for that exact count.",
        ],
        "related": ["deflated-sharpe-ratio", "probability-of-backtest-overfitting"],
    },
    {
        "slug": "does-technical-analysis-work",
        "title": "Does technical analysis work?",
        "question": "Does technical analysis actually work?",
        "body": [
            "This registry is a narrow, concrete answer to a question usually "
            "argued in the abstract. Twenty-one families of rule — RSI, moving "
            "average crosses, Bollinger bands, breakouts, order blocks, fair "
            "value gaps, liquidity sweeps — tested across roughly 17,000 "
            "parameter combinations on crypto and FX.",
            "None cleared the bar. The closest was cross-sectional momentum, "
            "which is also the one family with substantial academic support, "
            "and it still fell short.",
            "The honest limits: this covers mechanical rules on price data at "
            "hourly frequency. It does not test discretionary judgement, order "
            "flow, fundamentals, or anything an individual reads from a chart "
            "that cannot be written down. And every test has a detection "
            "floor, stated on each record, below which a real edge would not "
            "have shown up.",
        ],
        "related": ["why-your-backtest-lies", "minimum-detectable-edge"],
    },
    {
        "slug": "is-ict-real",
        "title": "Are ICT and smart money concepts testable?",
        "question": "Do ICT and smart money concepts actually work?",
        "body": [
            "Most smart money material cannot be tested, and that is the "
            "central problem rather than a detail. If a human decides which "
            "order block counts, a failed backtest proves nothing: the answer "
            "will always be that it was implemented wrong.",
            "So only the mechanically definable parts were tested here — fair "
            "value gaps, order blocks, liquidity sweeps and breaks of "
            "structure, each with an exact definition written into the "
            "pre-registration and hashed before the test ran. That way the "
            "objection has to be raised in advance or not at all.",
            "None passed. What that does and does not mean is stated on each "
            "record: it falsifies the mechanical rule, not every possible "
            "discretionary application of the idea. Claiming more than that "
            "would be the same overreach this registry exists to document.",
        ],
        "related": ["does-technical-analysis-work", "pre-registration-in-trading"],
    },
]

# --------------------------------------------------------------------------
# Parameter pages: only settings people actually search for. "RSI 14" gets
# searched; "RSI 37" does not. Generating a page per parameter combination
# would be 17,000 pages of scaled content abuse for zero traffic.
# --------------------------------------------------------------------------
POPULAR_PARAMS = {
    "rsi_reversion": [
        ("rsi-14", "RSI 14", 14, "The default on every charting platform, from "
         "Wilder's original 1978 book."),
        ("rsi-2", "RSI 2", 2, "Larry Connors' short-period variant, marketed "
         "as a mean reversion edge."),
        ("rsi-7", "RSI 7", 7, "The faster setting day traders switch to when "
         "14 feels sluggish."),
        ("rsi-21", "RSI 21", 21, "The slower setting swing traders prefer for "
         "fewer signals."),
    ],
    "ma_cross": [
        ("golden-cross-50-200", "The golden cross (50/200)", 50,
         "The most famous signal in technical analysis, reported in financial "
         "media as market-moving news."),
        ("ma-cross-9-21", "9/21 EMA cross", 9,
         "The intraday pairing taught in most day trading courses."),
        ("ma-cross-20-50", "20/50 MA cross", 20,
         "The swing trading middle ground."),
        ("ma-cross-12-26", "12/26 EMA cross", 12,
         "The MACD periods, used directly as a crossover."),
    ],
    "bollinger_touch": [
        ("bollinger-20-2", "Bollinger 20, 2 standard deviations", 20,
         "Bollinger's own default settings."),
        ("bollinger-10-15", "Bollinger 10, 1.5 standard deviations", 10,
         "The tighter short-term variant."),
    ],
    "donchian_breakout": [
        ("donchian-20", "Donchian 20 (Turtle entry)", 20,
         "The Turtle Traders' short-term system entry."),
        ("donchian-55", "Donchian 55 (Turtle long-term)", 55,
         "The Turtles' long-term system entry."),
    ],
    "momentum_roc": [
        ("momentum-12", "12-period momentum", 12,
         "The classic academic momentum lookback, scaled to hourly bars."),
        ("momentum-24", "24-hour momentum", 24,
         "One full day of trailing return."),
        ("momentum-168", "Weekly momentum", 168,
         "One full week of hourly bars."),
    ],
    "atr_breakout": [
        ("atr-14", "ATR 14", 14, "Wilder's original ATR period, still the "
         "platform default."),
    ],
}

# --------------------------------------------------------------------------
# Comparison pages: head-to-head queries people genuinely type.
# --------------------------------------------------------------------------
COMPARISONS = [
    ("momentum-vs-mean-reversion", "Momentum vs mean reversion",
     ["momentum_roc", "zscore_reversion"],
     "The oldest argument in trading: does a move continue, or snap back? "
     "Both were tested on identical data with identical costs."),
    ("ict-vs-classic-price-action", "ICT vs classic price action",
     ["fair_value_gap", "engulfing"],
     "Smart money concepts against the candlestick patterns they claim to "
     "supersede."),
    ("rsi-vs-bollinger", "RSI vs Bollinger bands",
     ["rsi_reversion", "bollinger_touch"],
     "Two ways to measure the same thing: how stretched is price right now?"),
    ("breakout-vs-reversion", "Breakout vs reversion",
     ["donchian_breakout", "bollinger_touch"],
     "Buy the new high, or fade it? The same price level, two opposite trades."),
    ("trend-following-vs-ranking", "Trend following vs cross-sectional ranking",
     ["momentum_roc", "xs_momentum"],
     "Betting on direction against betting on relative strength — the "
     "difference between asking if an asset goes up and asking which asset "
     "goes up most."),
    ("order-block-vs-support-resistance", "Order blocks vs support and resistance",
     ["order_block", "liquidity_sweep"],
     "Two smart money constructions for the same idea: price remembers levels."),
]

MARKET_CONTEXT = {
    "Crypto": "Bitcoin and Ethereum spot on Binance, hourly bars from 2017. "
              "Costs charged at 6 basis points round trip, which is roughly "
              "what a retail taker pays.",
    "FX": "EURUSD, GBPUSD and USDJPY from Dukascopy tick data aggregated to "
          "hourly bars. Costs charged at 1.5 basis points round trip — major "
          "FX spreads are far tighter than crypto fees, which means a smaller "
          "genuine edge would have survived here.",
}


# --------------------------------------------------------------------------
# Question pages. These carry most of the long-tail traffic because they match
# how people actually type: "does X work", "is X profitable", "X backtest
# results". Each is generated per family, so the content differs on every page
# — the numbers, the claim, the specific catch. A template with only the name
# swapped would be the scaled-content trap; these carry real per-family
# material from FAMILIES above.
# --------------------------------------------------------------------------
QUESTION_FORMS = [
    ("does-{slug}-work", "Does {label} work?",
     "Does {label_l} actually work in real trading?"),
    ("is-{slug}-profitable", "Is {label} profitable?",
     "Is {label_l} profitable after trading costs?"),
    ("{slug}-backtest-results", "{label} backtest results",
     "What do rigorous {label_l} backtest results show?"),
    ("best-{slug}-settings", "Best {label} settings",
     "What are the best settings for {label_l}?"),
    ("{slug}-win-rate", "{label} win rate",
     "What win rate does {label_l} actually achieve?"),
]

# Families worth generating every question form for: the ones with real search
# demand. The rest get the two strongest forms only, because a page nobody
# searches for is a liability rather than an asset.
HIGH_DEMAND = {
    "rsi_reversion", "ma_cross", "bollinger_touch", "donchian_breakout",
    "momentum_roc", "fair_value_gap", "order_block", "liquidity_sweep",
    "break_of_structure", "engulfing", "xs_momentum", "atr_breakout",
    "intraday_seasonality", "inside_bar_breakout",
}
