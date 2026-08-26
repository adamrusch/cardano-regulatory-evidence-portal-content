# Cardano stake-pool block production and economic viability

An empirical analysis of block production and operator economics across the
full stake distribution, conducted for the minPoolCost policy question
(PCP-006: reduce minPoolCost from 170 ada to 75 ada; on-chain governance
action open for voting until September 1, 2026).

## Data provenance

| Item | Value |
| --- | --- |
| Data retrieval (UTC) | 2026-08-26, 03:23:52 – 03:51:12 |
| Current (incomplete) epoch | 651 |
| Latest completed epoch used | 650 |
| Historical window for actual production | epochs 641–650 (10 completed epochs) |
| Pools retrieved | 6,161 registrations total: 2,900 `registered`, 3,259 `retired`, 2 `retiring` |
| Pools analyzed | the 2,900 with status `registered` |
| Primary source | Koios API v1, `https://api.koios.rest/api/v1` |
| Endpoints | `/tip`, `/epoch_info`, `/epoch_params`, `/totals`, `/pool_list` (offset-paginated to exhaustion), `/pool_info` (POST, batches of 50), `/blocks?epoch_no=eq.N` (offset-paginated to exhaustion, one call set per epoch 641–650) |
| Documentation | <https://api.koios.rest/> (Koios API v1 reference) |

**How the data was fetched.** The sandbox this analysis runs in sits behind an
egress proxy that blocks every Cardano API host that was tried
(`api.koios.rest`, `pooltool.io`, `api.pooltool.io`, `cexplorer.io`,
`adastat.net`, `api.dune.com`, and others — all refused at the proxy with
policy 403s). Rather than substituting stale data, the dataset was retrieved
by a GitHub Actions workflow on this branch
(`.github/workflows/koios-data-fetch.yml` running `analysis/koios_fetch.py`),
since GitHub-hosted runners have ordinary internet egress. The raw snapshot is
committed as `analysis/data/koios_dataset.json.gz` and every number below is
reproducible from it with `analysis/analyze.py`.

**PoolTool as fallback.** PoolTool's public data feed (the
`data.pooltool.io` S3 bucket, e.g.
`https://s3-us-west-2.amazonaws.com/data.pooltool.io/stats/stats.json`) was
reachable and its network-tip feed is current — it independently confirmed
epoch 651 and the chain tip at retrieval time. Its pool-level aggregates
(`stats/livestake.json`, `stats/tickers.json`), however, carry Last-Modified
dates of March 2026 and were therefore **not** used. All pool-level data below
is Koios, from one internally consistent retrieval.

**Completeness checks.** The 2,900 registered pools' active stake sums to
21.567B ada, 100.00% of the epoch-651 total active stake reported
independently by `/epoch_info` (21.568B). The pools in the dataset account for
211,964 of the 211,987 blocks produced in epochs 641–650 (99.99%); the
remainder belongs to pools that retired during the window.

## Expected block production: formula and inputs

Cardano mainnet runs with decentralisation `d = 0` (confirmed from
`/epoch_params`), so all blocks are made by stake pools. Leader election is
proportional to the pool's share of the epoch's active-stake snapshot:

```
expected blocks per epoch = (pool active stake / total active stake) × B
```

Inputs from the dataset:

- Total active stake, epoch 651: **21.568B ada** (`/epoch_info`).
- B = mean blocks actually produced per epoch over epochs 641–650:
  **21,198.7** (range 20,817–21,478). The theoretical ceiling is
  432,000 slots × active-slot coefficient 0.05 = 21,600; the chain realizes
  ≈98.1% of it (missed slots, height battles).

At the current totals, **one expected block per epoch corresponds to ≈1.02M
ada of active stake** — the folk rule of "1M ada ≈ 1 block/epoch" still holds
almost exactly.

Ranking methodology: all 2,900 registered pools ranked by `active_stake`
descending from `/pool_info` — the leader-election ("mark") snapshot in force
for the current epoch 651, which is the most recent fully determined stake
value. Actual production is the mean over epochs 641–650 of per-pool block
counts aggregated from the raw `/blocks` list of each epoch (no sampling).

## The five representative ranks

| Rank | Pool | Active stake | Expected blocks/epoch | Actual blocks/epoch (mean, epochs 641–650) | Declared fixed cost | Margin |
| --- | --- | --- | --- | --- | --- | --- |
| 100 | NORTH — #1 Nordic Pool (`pool12t3…f0lx`) | 64.84M ada | 63.7 | 57.9 (blocks in 10/10 epochs) | 340 ada | 0.0% |
| 250 | OCEA2 — ADA Ocean Two (`pool1ctz…66vs`) | 33.72M ada | 33.2 | 35.0 (10/10) | 500 ada | 3.9% |
| 500 | no ticker registered (`pool1s7d…uf5m`) | 10.40M ada | 10.2 | 11.0 (10/10) | 340 ada | 3.0% |
| 750 | ARTZ — ARTZ Pool (`pool127x…wgjg`) | 2.38M ada | 2.3 | 2.1 (10/10; per-epoch counts 1,1,3,5,1,1,3,1,3,2) | 340 ada | 2.0% |
| 1000 | HUNNY — HUNNY pool (`pool1la0…zt35`) | 0.65M ada | 0.64 | 0.7 (6/10; counts 1,0,0,0,2,1,1,1,0,1) | 170 ada | 0.0% |

Expected and actual production agree well at every rank (differences are
within ordinary leader-election variance plus stake drift over the window),
which is the internal consistency check on the whole dataset.

## Full distribution by active stake

All 2,900 registered pools, epoch-651 active stake:

| Active stake | Pools | % of pools | % of active stake | Expected blocks/epoch |
| --- | --- | --- | --- | --- |
| ≥50M ada | 169 | 5.8% | 52.2% | ≥49 |
| 25M–50M | 165 | 5.7% | 26.8% | 24.6–49.1 |
| 10M–25M | 171 | 5.9% | 12.9% | 9.8–24.6 |
| 3M–10M | 209 | 7.2% | 5.5% | 2.9–9.8 |
| 1M–3M | 213 | 7.3% | 1.7% | 0.98–2.9 |
| 500K–1M | 129 | 4.4% | 0.42% | 0.49–0.98 |
| 100K–500K | 278 | 9.6% | 0.32% | 0.10–0.49 |
| 10K–100K | 314 | 10.8% | 0.06% | 0.01–0.10 |
| 1K–10K | 392 | 13.5% | 0.006% | ~0.001–0.01 |
| <1K ada | 860 | 29.7% | 0.001% | <0.001 |

More than half of all registered pools (54%, the bottom three buckets) hold
under 100K ada and are statistically expected to produce at most a couple of
blocks **per year**.

Cumulative concentration of active stake:

| Top N pools | Share of active stake |
| --- | --- |
| 100 | 34.2% |
| 250 | 67.4% |
| 500 | 91.7% |
| 750 | 97.9% |
| 1,000 | 99.5% |

## Where block production thins out

Rank and stake levels at each expected-production threshold (current totals):

| Expected blocks/epoch | Active stake required | Pools at/above | First pool below is rank |
| --- | --- | --- | --- |
| 10 | 10.2M ada | 503 | 504 |
| 5 | 5.1M ada | 619 | 620 |
| 3 | 3.05M ada | 708 | 709 |
| 1 | 1.02M ada | 916 | 917 |
| 0.5 | 0.51M ada | 1,053 | 1,054 |
| 0.2 | 0.20M ada | 1,210 | 1,211 |

Measured against **actual** production over epochs 641–650:

- 700 pools averaged ≥3 blocks/epoch (vs. 708 expected-based — near-perfect agreement).
- 877 pools averaged ≥1 block/epoch (vs. 916 expected-based).
- 1,217 registered pools produced at least one block somewhere in the 10 epochs.
- A mean of 937 distinct pools produced blocks in any single epoch (range 903–972).

Reliability of a reward-producing epoch by rank band (share of the last 10
epochs with ≥1 block, band averages):

| Rank band | P(reward epoch) | Mean blocks/epoch |
| --- | --- | --- |
| 501–750 | 0.94 | 5.2 |
| 751–1,000 | 0.55 | 1.0 |
| 1,001–1,250 | 0.23 | 0.56 |
| 1,251–1,500 | 0.03 | 0.04 |

Block production becomes **intermittent** (routine zero-block epochs) at
roughly rank 780–800, around 1.5–2M ada of active stake, and becomes
**rare** below roughly rank 1,100 (~0.35M ada).

Classification of all 2,900 registered pools (transparent, production-based
categories over epochs 641–650):

| Category | Definition | Pools |
| --- | --- | --- |
| Highly reliable producer | ≥10 blocks/epoch mean, blocks in 10/10 epochs | 497 |
| Reliable | ≥3 blocks/epoch mean, blocks in ≥9/10 epochs | 192 |
| Marginal / high variance | 1–3 blocks/epoch mean | 177 |
| Intermittent | >0 but <1 block/epoch mean | 340 |
| Not producing | 0 blocks in all 10 epochs | 1,683 |

## minPoolCost economics: 170 ada vs. 75 ada

Mechanics (per Cardano reward rules): a pool receives rewards for an epoch
only if it produced at least one block in it. From the pool's epoch reward
pot, the declared fixed cost (≥ minPoolCost) is paid to the operator first —
capped by the pot itself — then the margin percentage of the remainder, and
delegators receive the rest. In epochs with zero blocks there is no pot and
therefore no fee. Over epochs 641–650 the network reward pot averaged
**268.9 ada per block** (epoch total pool rewards ÷ epoch blocks, from
`/epoch_info`), so a single block's pot comfortably covers a 170-ada fee.

Annual fixed-fee revenue **if the pool charges the minimum**, using each
pool's empirical reward-epoch frequency over the last 10 epochs and 73
epochs/year (revenue = 73 × P(reward epoch) × minimum fee — *not* 73 × fee):

| Rank | P(reward epoch), empirical | Annual fee revenue @170 | @75 | Difference |
| --- | --- | --- | --- | --- |
| 100 | 1.0 | 12,410 ada | 5,475 ada | −6,935 ada |
| 250 | 1.0 | 12,410 ada | 5,475 ada | −6,935 ada |
| 500 | 1.0 | 12,410 ada | 5,475 ada | −6,935 ada |
| 750 | 1.0 | 12,410 ada | 5,475 ada | −6,935 ada |
| 1,000 | 0.6 | 7,446 ada | 3,285 ada | −4,161 ada |

(For a pool at rank 1,000's stake, the Poisson model P(≥1 block) =
1 − e^−0.64 = 0.47 brackets the empirical 0.6 — six reward epochs out of ten
is one epoch of good luck above expectation.)

Margin revenue is separate and much smaller for small pools: at rank 750
(margin 2%, ~2.1 blocks/epoch) roughly 800 ada/year; at rank 1,000
(margin 0%) zero. Only mid-size and larger pools earn material margin income
(rank 250 at 3.9% margin: ~27,000 ada/year).

**The crucial caveat: the minimum is not what most pools actually charge.**
Declared fixed costs among the 2,900 registered pools: 1,903 declare 340 ada
(the pre-October-2023 minimum, never lowered after PCP-001), 507 declare
exactly 170 ada, 301 declare 345 ada, and the median declared cost is 340 ada
in *every* rank band from 1–100 down to 1,001–1,250. Lowering the floor
from 170 to 75 therefore does not by itself cut anyone's revenue; it widens
the *choice set*. Its real effect is competitive: it lets a small pool lower
its fee to stop the fee from consuming its delegators' rewards.

That delegator-side effect is where the change bites, because the fixed fee
is a regressive share of a small pool's reward pot:

| Rank | Mean pot/epoch | Fee share of pot @170 | @75 | Implied delegator ROS @170 | @75 |
| --- | --- | --- | --- | --- | --- |
| 100 | 15,569 ada | 1.1% | 0.5% | ~1.73%/yr | ~1.74%/yr |
| 500 | 2,958 ada | 5.7% | 2.5% | ~1.90%/yr | ~1.96%/yr |
| 750 | 565 ada | 30% | 13% | ~1.19%/yr | ~1.47%/yr |
| 1,000 | 188 ada | 63%* | 28%* | ~0.97%/yr | ~1.60%/yr |

\* averaged over reward epochs; in a single-block epoch the fee takes 170 of
a ~269-ada pot. ROS figures assume the pool charges the minimum and use each
pool's actual margin.

At ranks 100–500 the change is invisible to delegators (≤0.06 percentage
points of ROS). At rank 750 it lifts delegator returns by ~0.3 points; at
rank 1,000 it roughly cuts the fee drag in half and moves delegator ROS from
~1.0% to ~1.6% — from clearly uncompetitive to within sight of the large-pool
~1.7–1.9% range.

## Profitability, stated carefully

No on-chain field reveals a pool's real operating costs, so pools are not
declared "profitable" here; the classification table above describes
production reliability only. For orientation, if an operator's all-in annual
cost is **C ada**, fee-revenue-only break-even at the current 170-ada minimum
requires P(reward epoch) ≥ C / 12,410:

| Assumed annual operating cost | Break-even P(reward epoch) @170 | Approx. rank needed | @75 minimum |
| --- | --- | --- | --- |
| 2,000 ada | 0.16 | ~1,250 | 0.37 → ~1,050 |
| 5,000 ada | 0.40 | ~1,100 | 0.91 → ~800 |
| 12,500 ada | ~1.0 and fee alone still short | ~750 (fee ≈ cost) | unattainable from the minimum fee alone |

These are sensitive to the cost assumption (shown across a 6× range) and to
the ada/fiat rate, which this analysis does not assert. The direction is
robust: **under either minimum, fixed-fee revenue alone does not fund a
professionally operated pool below roughly rank 800–1,000**, and lowering the
minimum reduces, not increases, guaranteed operator revenue for pools that
currently charge it.

## Answers to the critical questions

1. **How many pools meaningfully participate in block production?** About
   900–950 in any given epoch (mean 937 distinct producers per epoch,
   epochs 641–650); 1,217 of 2,900 registered pools made at least one block
   across the 10-epoch window. Roughly 58% of registered pools produced
   nothing at all in 10 epochs.
2. **Where does production become intermittent?** Around rank 780–800
   (~1.5–2M ada active stake) pools start seeing routine zero-block epochs;
   the 751–1,000 band averages a reward epoch only 55% of the time.
3. **Production at the five ranks:** rank 100 ≈ 58 blocks/epoch, rank 250
   ≈ 35, rank 500 ≈ 11, rank 750 ≈ 2 (still every epoch), rank 1,000 ≈ 0.7
   (blocks in 6 of 10 epochs). See the rank table.
4. **Pools averaging ≥3 blocks/epoch:** 700 measured (708 by expected stake
   share).
5. **Pools averaging ≥1 block/epoch:** 877 measured (916 by expected stake
   share).
6. **How much does 170→75 change small-pool economics?** For operators it
   *removes up to 6,935 ada/year of guaranteed revenue* for pools that charge
   the minimum every reward epoch, and less for intermittent producers
   (−4,161 ada/year at rank 1,000). For delegators of small pools it is a
   material improvement: at rank 1,000 the fee's share of the reward pot
   falls from ~63% to ~28% of an average reward epoch, roughly doubling
   member ROS from ~1.0% to ~1.6%.
7. **Does it materially help pools near ranks 500/750/1,000?** Rank 500:
   no — the fee is already a small share of a 3,000-ada pot, and delegator
   ROS moves by 0.06 points. Rank 750: modestly — delegator ROS +0.3 points.
   Rank 1,000: yes, on the delegator-attractiveness margin — it is the one
   band where the fee currently dominates the reward pot. But it helps only
   pools that *choose* to charge less, at the direct cost of their own fee
   income; it cannot make a 0.65M-ada pool produce more than ~0.6 blocks per
   epoch.
8. **Fee or stake — which is the binding constraint?** Stake. The reward pot
   of a rank-1,000 pool is ~188 ada per epoch and of a rank-1,250 pool
   effectively nil, no matter how the pot is split. minPoolCost changes the
   *division* of small pots (and thereby small pools' ability to compete for
   delegation on ROS); it does not change the pot. The binding constraint on
   small-pool viability is insufficient delegated stake and therefore
   insufficient block-production opportunity — 1,683 registered pools had no
   blocks at all in 10 epochs, and no fee parameter reaches them.

## Reproducibility

- Dataset snapshot: `analysis/data/koios_dataset.json.gz` (this branch),
  retrieved 2026-08-26 03:23–03:51 UTC by workflow run
  [#32926278978](https://github.com/adamrusch/cardano-regulatory-evidence-portal-content/actions/runs/32926278978).
- Fetcher: `analysis/koios_fetch.py`; analysis: `analysis/analyze.py`.
- Koios API v1 documentation: <https://api.koios.rest/>.
- PoolTool feed checked as fallback: `https://s3-us-west-2.amazonaws.com/data.pooltool.io/stats/stats.json`
  (current; used for corroboration only) and `stats/livestake.json` /
  `stats/tickers.json` (stale as of March 2026; not used). PoolTool backend
  reference: <https://github.com/PoolTool-io/PoolToolBackend-DB>,
  <https://github.com/papacarp/pooltool.io>.
- minPoolCost policy context: [PCP-006 forum thread](https://forum.cardano.org/t/pcp-006-minpoolcost-cerkoryn/153833),
  [Intersect announcement](https://intersectmbo.org/news/lowering-minpoolcost-and-completing-smart-contract-capacity-increases),
  [cardano.org news](https://cardano.org/news/2026-08-03-lowering-minpoolcost/).
  The 170-ada minimum has applied since epoch 445 (October 2023, PCP-001).

No historical IOG census figures were used for any primary number; every
result above derives from the epoch-641–651 Koios retrieval described in the
provenance table.
