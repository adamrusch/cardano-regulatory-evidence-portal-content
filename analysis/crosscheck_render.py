#!/usr/bin/env python3
"""Render the URLs in analysis/crosscheck_urls.txt with headless Chromium.

cardanoscan.io fronts a Cloudflare JS challenge that blocks plain curl, so
the cross-check fetch renders each page in a real browser context, waits for
the challenge to clear, and saves the resulting DOM.
"""

import pathlib
import sys
import time

from playwright.sync_api import sync_playwright

OUT = pathlib.Path("analysis/data/crosscheck")
URLS = [
    u.strip()
    for u in pathlib.Path("analysis/crosscheck_urls.txt").read_text().splitlines()
    if u.strip()
]

OUT.mkdir(parents=True, exist_ok=True)
for old in OUT.glob("page*"):
    old.unlink()

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"],
    )
    ctx = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1366, "height": 900},
        locale="en-US",
    )
    page = ctx.new_page()
    for i, url in enumerate(URLS, start=1):
        print(f"[{i}] {url}", flush=True)
        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            # Give a Cloudflare challenge time to clear and the app to render.
            for _ in range(12):
                time.sleep(5)
                title = page.title()
                if "just a moment" not in title.lower():
                    break
            time.sleep(5)
            html = page.content()
        except Exception as e:  # noqa: BLE001 - record and continue
            html = f"<!-- fetch failed: {e} -->"
            print(f"  failed: {e}", flush=True)
        (OUT / f"page{i}.html").write_text(html)
        (OUT / f"page{i}.url").write_text(url + "\n")
        print(f"  saved page{i}.html ({len(html)} bytes), title={page.title()!r}", flush=True)
    browser.close()

sys.exit(0)
