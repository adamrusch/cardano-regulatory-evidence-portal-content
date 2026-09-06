#!/usr/bin/env python3
"""Fetch the complete current Cardano DRep voting-power dataset from Koios.

Runs inside GitHub Actions (which has unrestricted egress) and writes a
gzipped JSON dataset used to rank DReps by voting power.

Endpoints used (Koios API v1, https://api.koios.rest/api/v1):
  GET  /tip                        chain tip, current epoch
  GET  /drep_epoch_summary         per-epoch DRep totals (amount, drep count)
  GET  /drep_list                  all DReps, paginated (offset/limit)
  POST /drep_info                  registration/active state and voting power,
                                   batches of 50
  POST /drep_metadata              CIP-119 off-chain metadata (givenName),
                                   batches of 50

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
OUT = "analysis/data/koios_drep_dataset.json.gz"
SLEEP = 0.12


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
    print(f"tip: epoch {current_epoch}, block {tip['block_no']}", flush=True)

    epoch_summary = {}
    for e in (current_epoch - 1, current_epoch):
        rows = req(f"/drep_epoch_summary?epoch_no=eq.{e}")
        if rows:
            epoch_summary[str(e)] = rows[0]
    print(f"drep_epoch_summary: {list(epoch_summary)}", flush=True)

    print("drep_list ...", flush=True)
    drep_list = paged("/drep_list?limit={limit}&offset={offset}")
    print(f"drep_list: {len(drep_list)} rows", flush=True)

    ids = [d["drep_id"] for d in drep_list]
    drep_info = []
    for i in range(0, len(ids), 50):
        chunk = ids[i : i + 50]
        drep_info.extend(req("/drep_info", {"_drep_ids": chunk}))
        if (i // 50) % 20 == 0:
            print(f"  drep_info {i + len(chunk)}/{len(ids)}", flush=True)
    print(f"drep_info: {len(drep_info)} rows", flush=True)

    # Metadata only for DReps that are currently registered (names for ranking).
    reg_ids = [d["drep_id"] for d in drep_info if d.get("registered")]
    drep_metadata = []
    for i in range(0, len(reg_ids), 50):
        chunk = reg_ids[i : i + 50]
        try:
            drep_metadata.extend(req("/drep_metadata", {"_drep_ids": chunk}))
        except RuntimeError:
            print(f"  metadata batch at {i} failed; continuing", flush=True)
        if (i // 50) % 20 == 0:
            print(f"  drep_metadata {i + len(chunk)}/{len(reg_ids)}", flush=True)
    print(f"drep_metadata: {len(drep_metadata)} rows", flush=True)

    dataset = {
        "meta": {
            "retrieved_at_utc": retrieved_at,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": "Koios API v1 (https://api.koios.rest/api/v1)",
            "runner": "github-actions",
            "current_epoch": current_epoch,
            "endpoints": [
                "/tip",
                "/drep_epoch_summary",
                "/drep_list (paginated)",
                "/drep_info (POST, batches of 50)",
                "/drep_metadata (POST, batches of 50, registered DReps only)",
            ],
        },
        "tip": tip,
        "drep_epoch_summary": epoch_summary,
        "drep_list": drep_list,
        "drep_info": drep_info,
        "drep_metadata": drep_metadata,
    }

    with gzip.open(OUT, "wt") as f:
        json.dump(dataset, f)
    print(f"wrote {OUT}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
