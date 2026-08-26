#!/usr/bin/env python3
"""Analysis of Cardano stake-pool block production and minPoolCost economics.

Consumes analysis/data/koios_dataset.json.gz (produced by the Koios data
fetch workflow on this branch) and prints the tables used in the report.
"""

import gzip
import json
import math
import statistics
from collections import defaultdict

DATA = "analysis/data/koios_dataset.json.gz"
LOVELACE = 1_000_000
EPOCHS_PER_YEAR = 73

with gzip.open(DATA, "rt") as f:
    ds = json.load(f)

meta = ds["meta"]
cur = meta["current_epoch"]
completed = meta["last_completed_epoch"]
hist = meta["history_epochs"]

epoch_info = ds["epoch_info"]
blocks_by_epoch = ds["blocks_by_epoch"]

# --- network-level inputs -------------------------------------------------
total_active_cur = int(epoch_info[str(cur)]["active_stake"])
blk_counts = [int(epoch_info[str(e)]["blk_count"]) for e in hist]
mean_blocks_per_epoch = statistics.mean(blk_counts)

print("== meta ==")
print(json.dumps(meta, indent=2))
print(f"total active stake epoch {cur}: {total_active_cur / LOVELACE / 1e9:.3f}B ADA")
print(f"blocks per epoch over {hist[0]}-{hist[-1]}: mean={mean_blocks_per_epoch:.1f} min={min(blk_counts)} max={max(blk_counts)}")

# --- pool table -----------------------------------------------------------
pools = {}
for p in ds["pool_info"]:
    if p.get("pool_status") != "registered":
        continue
    pid = p["pool_id_bech32"]
    active = int(p.get("active_stake") or 0)
    meta_json = p.get("meta_json") or {}
    pools[pid] = {
        "id": pid,
        "ticker": meta_json.get("ticker") or "",
        "name": meta_json.get("name") or "",
        "active": active,
        "live": int(p.get("live_stake") or 0),
        "pledge": int(p.get("pledge") or 0),
        "fixed_cost": int(p.get("fixed_cost") or 0),
        "margin": float(p.get("margin") or 0.0),
    }

print(f"registered pools: {len(pools)}")
print(f"pool_info rows: {len(ds['pool_info'])}  pool_list rows: {len(ds['pool_list'])}")
status_counts = defaultdict(int)
for p in ds["pool_info"]:
    status_counts[p.get("pool_status")] += 1
print("statuses:", dict(status_counts))

sum_active = sum(p["active"] for p in pools.values())
print(f"sum of registered pools' active stake: {sum_active / LOVELACE / 1e9:.3f}B ADA "
      f"({100 * sum_active / total_active_cur:.2f}% of epoch_info total)")

# actual blocks per pool: mean over history epochs
for p in pools.values():
    counts = [blocks_by_epoch[str(e)].get(p["id"], 0) for e in hist]
    p["blocks_hist"] = counts
    p["blocks_mean"] = statistics.mean(counts)
    p["epochs_with_block"] = sum(1 for c in counts if c > 0)

# expected blocks from active stake share
for p in pools.values():
    p["share"] = p["active"] / total_active_cur if total_active_cur else 0
    p["expected"] = p["share"] * mean_blocks_per_epoch

ranked = sorted(pools.values(), key=lambda p: p["active"], reverse=True)
for i, p in enumerate(ranked, start=1):
    p["rank"] = i

# how much of block production is captured by pools table (sanity)
produced_by_known = 0
produced_total = 0
for e in hist:
    for pid, c in blocks_by_epoch[str(e)].items():
        produced_total += c
        if pid in pools:
            produced_by_known += c
print(f"blocks by currently-registered pools: {produced_by_known}/{produced_total} "
      f"({100 * produced_by_known / produced_total:.2f}%)")

# --- rank table -----------------------------------------------------------
print("\n== rank table ==")
for r in (100, 250, 500, 750, 1000):
    if r <= len(ranked):
        p = ranked[r - 1]
        print(f"rank {r}: {p['ticker'] or '(no ticker)'} | {p['name'][:30]} | "
              f"active {p['active'] / LOVELACE / 1e6:.2f}M ADA | "
              f"exp {p['expected']:.2f} | actual10 {p['blocks_mean']:.2f} "
              f"(epochs with block: {p['epochs_with_block']}/10, hist {p['blocks_hist']}) | "
              f"fee {p['fixed_cost'] / LOVELACE:.0f} | margin {p['margin'] * 100:.2f}%")

# --- buckets --------------------------------------------------------------
print("\n== buckets ==")
buckets = [
    (">=50M", 50e6, float("inf")),
    ("25M-50M", 25e6, 50e6),
    ("10M-25M", 10e6, 25e6),
    ("3M-10M", 3e6, 10e6),
    ("1M-3M", 1e6, 3e6),
    ("500K-1M", 0.5e6, 1e6),
    ("100K-500K", 1e5, 5e5),
    ("10K-100K", 1e4, 1e5),
    ("1K-10K", 1e3, 1e4),
    ("<1K", 0, 1e3),
]
n = len(ranked)
for label, lo, hi in buckets:
    sub = [p for p in ranked if lo <= p["active"] / LOVELACE < hi]
    st = sum(p["active"] for p in sub)
    exp_lo = (lo * LOVELACE / total_active_cur) * mean_blocks_per_epoch
    exp_hi = (hi * LOVELACE / total_active_cur) * mean_blocks_per_epoch if hi != float("inf") else None
    rng = f"{exp_lo:.3f}-{exp_hi:.3f}" if exp_hi else f">={exp_lo:.1f}"
    print(f"{label:>10}: {len(sub):4d} pools ({100 * len(sub) / n:5.2f}%) | "
          f"{100 * st / sum_active:6.3f}% of active stake | exp blocks/epoch {rng}")

# --- concentration --------------------------------------------------------
print("\n== concentration ==")
cum = 0
top_shares = {}
for i, p in enumerate(ranked, start=1):
    cum += p["active"]
    if i in (100, 250, 500, 750, 1000):
        top_shares[i] = cum / sum_active
        print(f"top {i}: {100 * cum / sum_active:.2f}% of registered pools' active stake")

# --- expected-block thresholds --------------------------------------------
print("\n== thresholds ==")
for thr in (10, 5, 3, 1, 0.5, 0.2):
    stake_needed = thr / mean_blocks_per_epoch * total_active_cur
    below = next((p for p in ranked if p["expected"] < thr), None)
    rank_at = below["rank"] if below else None
    print(f"expected {thr:>4} blocks/epoch needs {stake_needed / LOVELACE / 1e6:8.2f}M ADA; "
          f"first pool below: rank {rank_at}")
    npools = sum(1 for p in ranked if p["expected"] >= thr)
    print(f"   pools at/above: {npools}")

print("\n== actual production counts ==")
for thr in (3, 1):
    npools = sum(1 for p in ranked if p["blocks_mean"] >= thr)
    print(f"pools averaging >={thr} actual blocks/epoch over last 10: {npools}")
active_producers = sum(1 for p in ranked if p["epochs_with_block"] > 0)
print(f"registered pools with >=1 block in last 10 epochs: {active_producers}")
per_epoch_producers = [len([1 for pid, c in blocks_by_epoch[str(e)].items() if c > 0]) for e in hist]
print(f"unique producers per epoch: mean {statistics.mean(per_epoch_producers):.0f}, "
      f"min {min(per_epoch_producers)}, max {max(per_epoch_producers)}")

# --- rewards per block (for minPoolCost logic) ----------------------------
# total pool rewards per epoch: use epoch_info total_rewards when present
tr_key = None
for k in ("total_rewards", "tot_rewards"):
    if k in epoch_info[str(hist[-1])]:
        tr_key = k
        break
if tr_key:
    rew = [int(epoch_info[str(e)][tr_key] or 0) for e in hist]
    rpb = [r / b for r, b in zip(rew, blk_counts) if b]
    print(f"\nmean rewards per block (epoch pot / blocks): {statistics.mean(rpb) / LOVELACE:.1f} ADA")

# --- minPoolCost scenarios -------------------------------------------------
print("\n== minPoolCost scenarios (annual, 73 epochs) ==")
for r in (100, 250, 500, 750, 1000):
    if r > len(ranked):
        continue
    p = ranked[r - 1]
    lam = p["blocks_mean"]
    p_reward_emp = p["epochs_with_block"] / len(hist)
    p_reward_poisson = 1 - math.exp(-p["expected"]) if p["expected"] < 50 else 1.0
    for cost in (170, 75):
        annual = EPOCHS_PER_YEAR * p_reward_emp * cost
        print(f"rank {r} ({p['ticker']}): minCost {cost} -> "
              f"annual fixed-fee revenue ~{annual:,.0f} ADA "
              f"(P(reward epoch) emp={p_reward_emp:.2f}, poisson={p_reward_poisson:.2f})")
