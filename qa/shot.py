#!/usr/bin/env python3
"""qa/shot.py — one throwaway headless render: shot.py <url> <out.png> [w h] [dpr]"""
import sys, random
from pathlib import Path

def main():
    url, out = sys.argv[1], Path(sys.argv[2])
    rest = sys.argv[3:]
    nums = [a for a in rest if not a.startswith("--")]
    w, h = (int(nums[0]), int(nums[1])) if len(nums) >= 2 else (1440, 2400)
    dpr = float(nums[2]) if len(nums) >= 3 else 1
    nojs = "--nojs" in rest
    from patchright.sync_api import sync_playwright
    pw = browser = None
    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=dpr,
                                java_script_enabled=not nojs)
        if nojs:
            page.route("**/*", lambda r: r.abort() if r.request.resource_type == "script" else r.continue_())
        page.goto(url, wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(700)
        out.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out), full_page=False)
        if nojs:
            hscroll = page.evaluate(
                "document.documentElement.scrollWidth > document.documentElement.clientWidth")
            print("js-off | horizontal scroll:", hscroll)
        else:
            fonts = page.evaluate("Array.from(document.fonts).filter(f=>f.status==='loaded').map(f=>f.family)")
            fam = page.evaluate("getComputedStyle(document.querySelector('main')||document.body).fontFamily")
            print("loaded:", fonts[:8], "| main family:", fam)
    except Exception as e:
        print("shot failed:", type(e).__name__, e)
        return 2
    finally:
        if browser is not None:
            try: browser.close()
            except Exception: pass
        if pw:
            pw.stop()
    return 0

if __name__ == "__main__":
    sys.exit(main())
