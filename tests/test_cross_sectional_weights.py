
import numpy as np, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sweep.cross_sectional import CrossSectionalRunner

N_ASSETS, N_LIVE = 184, 21

def runner():
    rng = np.random.default_rng(7)
    prices = 100*np.exp(np.cumsum(rng.normal(0,.01,(50,N_ASSETS)),axis=0))
    member = np.zeros((50,N_ASSETS),bool); member[:,:N_LIVE]=True
    return CrossSectionalRunner(prices,member,6.0)

def weights(frac, rule):
    v = dict(family="xs_momentum", lookback=10, entry_threshold=frac,
             exit_rule=rule, holding_cap_bars=4)
    return runner()._target_weights(30, v, N_ASSETS)

fails = 0
def check(name, cond):
    global fails
    print(("PASS  " if cond else "FAIL  ") + name)
    if not cond: fails += 1

w = weights(0.2, "long_short")
check("no weight outside universe", not np.any(w[N_LIVE:]))
check("dollar neutral", abs(w.sum()) < 1e-12)
check("gross exposure 2.0", np.isclose(np.abs(w).sum(), 2.0))
check("legs equal and non-empty", (w>0).sum() == (w<0).sum() > 0)

w = weights(0.9, "long_short")
check("wide frac: still neutral", abs(w.sum()) < 1e-12)
check("wide frac: gross 2.0", np.isclose(np.abs(w).sum(), 2.0))
check("wide frac: no overlap", (w>0).sum() + (w<0).sum() <= N_LIVE)

w = weights(0.2, "mean_touch")
check("long only: no shorts", np.all(w >= 0))
check("long only: inside universe", not np.any(w[N_LIVE:]))
check("long only: gross 2.0", np.isclose(np.abs(w).sum(), 2.0))

print()
print("ALL PASS" if fails == 0 else str(fails) + " FAILURES")
sys.exit(1 if fails else 0)
