#!/usr/bin/env python3
"""Fetch a complete current Cardano stake-pool dataset from Koios.

Runs inside GitHub Actions (which has unrestricted egress) and writes a single
gzipped JSON dataset used by the stake-pool block-production analysis.

Endpoints used (Koios API v1, https://api.koios.rest/api/v1):
  GET  /tip                       chain tip, current epoch
  GET  /epoch_info?_epoch_no=N    per-epoch totals (active stake, block count)
  GET  /epoch_params?_epoch_no=N  protocol parameters (min_pool_cost, k, a0, ...)
  GET  /totals?_epoch_no=N        supply/treasury/reserves
  GET  /pool_list                 all pools, paginated (offset/limit)
  POST /pool_info                 pool details in batches of 50
  GET  /blocks?epoch_no=eq.N      every block of an epoch, paginated; aggregated
                                  here to per-pool block counts per epoch

Docs: https://api.koios.rest/  (Koios API v1)
"""

import gzip
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

BASE = "https://api.koios.rest/api/v1"
OUT = "analysis/data/koios_dataset.json.gz"
HISTORY_EPOCHS = 10  # completed epochs used for the actual-production average
SLEEP = 0.12  # stay well under the public-tier rate limit


def req(path, payload=None, retries=5):
    url = BASE + path
    for attempt in range(retries):
        try:
            if payload is None:
                r = urllib.request.Request(url, headers={"Accept": "application/json"})
            else:
                r = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode(),
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
            with urllib.request.urlopen(r, timeout=90) as resp:
                data = json.loads(resp.read().decode())
            time.sleep(SLEEP)
            return data
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            wait = 2**attempt
            print(f"  retry {attempt + 1} for {path}: {e} (sleeping {wait}s)", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"giving up on {path}")


def paged(path_fmt, page_size=1000):
    """Follow PostgREST offset pagination until a short page is returned."""
    rows = []
    offset = 0
    while True:
        page = req(path_fmt.format(limit=page_size, offset=offset))
        rows.extend(page)
        print(f"  {path_fmt.split('?')[0]} offset {offset}: +{len(page)} rows", flush=True)
        if len(page) < page_size:
            return rows
        offset += page_size


def main():
    retrieved_at = datetime.now(timezone.utc).isoformat()
    print(f"retrieval start {retrieved_at}", flush=True)

    tip = req("/tip")[0]
    current_epoch = tip["epoch_no"]
    last_completed = current_epoch - 1
    hist_epochs = list(range(last_completed - HISTORY_EPOCHS + 1, last_completed + 1))
    print(f"tip: epoch {current_epoch}, block {tip['block_no']}", flush=True)

    epoch_info = {}
    for e in hist_epochs + [current_epoch]:
        rows = req(f"/epoch_info?_epoch_no={e}&_include_next_epoch=false")
        if rows:
            epoch_info[str(e)] = rows[0]
    print(f"epoch_info for {len(epoch_info)} epochs", flush=True)

    epoch_params = {}
    for e in [last_completed, current_epoch]:
        rows = req(f"/epoch_params?_epoch_no={e}")
        if rows:
            epoch_params[str(e)] = rows[0]

    totals = req(f"/totals?_epoch_no={current_epoch}")

    print("pool_list ...", flush=True)
    pool_list = paged("/pool_list?limit={limit}&offset={offset}")
    print(f"pool_list: {len(pool_list)} rows", flush=True)

    ids = [p["pool_id_bech32"] for p in pool_list]
    pool_info = []
    for i in range(0, len(ids), 50):
        chunk = ids[i : i + 50]
        pool_info.extend(req("/pool_info", {"_pool_bech32_ids": chunk}))
        if (i // 50) % 10 == 0:
            print(f"  pool_info {i + len(chunk)}/{len(ids)}", flush=True)
    print(f"pool_info: {len(pool_info)} rows", flush=True)

    # Per-pool block counts for each completed history epoch, aggregated from
    # the raw block list so no pool is missed.
    blocks_by_epoch = {}
    for e in hist_epochs:
        counts = {}
        rows = paged(f"/blocks?epoch_no=eq.{e}&select=pool&limit={{limit}}&offset={{offset}}")
        for row in rows:
            pool = row.get("pool") or "__no_pool__"
            counts[pool] = counts.get(pool, 0) + 1
        blocks_by_epoch[str(e)] = counts
        print(f"blocks epoch {e}: {sum(counts.values())} blocks, {len(counts)} producers", flush=True)

    dataset = {
        "meta": {
            "retrieved_at_utc": retrieved_at,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": "Koios API v1 (https://api.koios.rest/api/v1)",
            "runner": "github-actions",
            "current_epoch": current_epoch,
            "last_completed_epoch": last_completed,
            "history_epochs": hist_epochs,
            "endpoints": [
                "/tip",
                "/epoch_info",
                "/epoch_params",
                "/totals",
                "/pool_list (paginated)",
                "/pool_info (POST, batches of 50)",
                "/blocks?epoch_no=eq.N (paginated, aggregated to per-pool counts)",
            ],
        },
        "tip": tip,
        "epoch_info": epoch_info,
        "epoch_params": epoch_params,
        "totals": totals,
        "pool_list": pool_list,
        "pool_info": pool_info,
        "blocks_by_epoch": blocks_by_epoch,
    }

    with gzip.open(OUT, "wt") as f:
        json.dump(dataset, f)
    print(f"wrote {OUT}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
