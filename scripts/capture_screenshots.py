#!/usr/bin/env python3
"""Capture desktop and mobile screenshots for Estimate and Check pages.
Target dates: Jan 1, Jan 3, Jan 25, Jan 30.
Resolutions:
- Desktop: 1280x800
- Mobile: 390x844 (iPhone 12/13/14 scale)
"""

import os
import sys
from playwright.sync_api import sync_playwright

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../docs/screenshots"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATES = ["2026-01-01", "2026-01-03", "2026-01-25", "2026-01-30"]
BASE_URL = "http://localhost:5174"


def capture_all():
    print(f"Saving screenshots to: {OUTPUT_DIR}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 1. Desktop context
        desktop_context = browser.new_context(viewport={"width": 1280, "height": 800})
        desktop_page = desktop_context.new_page()

        # 2. Mobile context
        mobile_context = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True)
        mobile_page = mobile_context.new_page()

        for d in DATES:
            day_num = d.split("-")[2]

            # --- ESTIMATE PAGE ---
            est_url = f"{BASE_URL}/jan25?date={d}&percentile=75"
            print(f"Capturing Estimate {d}...")

            # Desktop Estimate
            desktop_page.goto(est_url, wait_until="networkidle")
            desktop_page.wait_for_timeout(1000)
            desktop_path = os.path.join(OUTPUT_DIR, f"estimate_jan{day_num}_desktop.png")
            desktop_page.screenshot(path=desktop_path, full_page=True)
            print(f"  -> Saved {desktop_path}")

            # Mobile Estimate
            mobile_page.goto(est_url, wait_until="networkidle")
            mobile_page.wait_for_timeout(1000)
            mobile_path = os.path.join(OUTPUT_DIR, f"estimate_jan{day_num}_mobile.png")
            mobile_page.screenshot(path=mobile_path, full_page=True)
            print(f"  -> Saved {mobile_path}")

            # --- CHECK PAGE ---
            chk_url = f"{BASE_URL}/jan25/check?date={d}&percentile=75"
            print(f"Capturing Check {d}...")

            # Desktop Check
            desktop_page.goto(chk_url, wait_until="networkidle")
            desktop_page.wait_for_timeout(1000)
            desktop_chk_path = os.path.join(OUTPUT_DIR, f"check_jan{day_num}_desktop.png")
            desktop_page.screenshot(path=desktop_chk_path, full_page=True)
            print(f"  -> Saved {desktop_chk_path}")

            # Mobile Check
            mobile_page.goto(chk_url, wait_until="networkidle")
            mobile_page.wait_for_timeout(1000)
            mobile_chk_path = os.path.join(OUTPUT_DIR, f"check_jan{day_num}_mobile.png")
            mobile_page.screenshot(path=mobile_chk_path, full_page=True)
            print(f"  -> Saved {mobile_chk_path}")

        browser.close()
    print("All screenshots successfully captured!")


if __name__ == "__main__":
    capture_all()
