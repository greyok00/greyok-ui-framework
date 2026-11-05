#!/usr/bin/env python3
"""open-state proof shots + clipped-open-element census (mobile pass, throwaway)"""
from patchright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8920/demo/sites"
JOBS = [
    ("brutal-stamp", "catalog", "drawer", "m-catalog-430-open-drawer"),
    ("brutal-stamp", "app", "dialog", "m-app-430-open-dialog"),
    ("brutal-stamp", "app", "toast", "m-app-430-toast"),
    ("brutal-index", "catalog", "drawer2", "m-catalog-430-open-drawer"),
    ("brutal-index", "app", "sealdlg", "m-app-430-open-dialog"),
    ("brutal-index", "app", "popover", "m-app-430-open-pop"),
    ("brutal-index", "app", "menu", "m-app-430-open-menu"),
]
OPEN = {
    "drawer": "sc('button[data-drawer-open=reserve-drawer]')",
    "drawer2": "sc('button[data-drawer-open=pull-drawer]')",
    "dialog": "sc('[data-dialog-open=close-dialog]')",
    "toast": "sc('.el-actionbar .actions button')",
    "popover": "dc('.el-popover .el-btn--ghost')",
    "menu": "dc('[data-menu=menu-ledger]')",
}

def run():
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
    for site, page, kind, out in JOBS:
        url = f"{BASE}/{site}/{page}.html"
        for w, h, shot in ((430, 932, True), (360, 800, False)):
            if not shot:
                continue
            ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
            pg = ctx.new_page()
            try:
                pg.goto(url, wait_until="networkidle", timeout=45000)
                pg.wait_for_timeout(300)
                if kind in ("popover", "menu", "sealdlg"):
                    pg.evaluate("document.querySelector(\"%s\").click()" % OPEN[kind][:-1].split("'")[1])
                elif kind == "toast":
                    pg.evaluate("document.querySelector('.el-actionbar .actions button').click()")
                else:
                    pg.click(OPEN[kind].split("'")[1], timeout=4000)
                pg.wait_for_timeout(300)
                hs = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
                clip = pg.evaluate("""() => {
                    let n = 0;
                    for (const el of document.querySelectorAll('.el-drawer .el-btn, .el-dialog .el-btn, .el-dialog .close, .el-pop, .el-menu-item, .el-drawer-head .close, .el-search, .el-input, .el-slider')) {
                        const r = el.getBoundingClientRect();
                        const cs = getComputedStyle(el);
                        if (cs.display === 'none') continue;
                        if (r.right > document.documentElement.clientWidth + 2 && !/(auto|scroll)/.test(cs.overflowX)) n++;
                    }
                    return n;
                }""")
                pg.screenshot(path=f"qa/sites/{site}/{out}.png")
                print(f"[{out} @{w}] hscroll={hs} clipped-open={clip} ({kind})")
            except Exception as e:
                print(f"[{out} @{w}] FAIL {type(e).__name__} {e}")
            finally:
                ctx.close()
    browser.close(); pw.stop()

if __name__ == "__main__":
    run()