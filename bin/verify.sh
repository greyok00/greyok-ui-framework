#!/usr/bin/env bash
# bin/verify.sh — greyok-ui-framework release checks.
# Exits 0 when everything passes, 1 otherwise.
set -u
cd "$(dirname "$0")/.."

fail=0
pass=0
note() { printf '  ✗ %s\n' "$1"; fail=1; }
ok()   { printf '  ✓ %s\n' "$1"; pass=$((pass+1)); }

# ── 1. CSS brace balance ──────────────────────────────────────────────────────
echo "css: brace balance"
for f in *.css; do
  o=$(tr -cd '{' < "$f" | wc -c); c=$(tr -cd '}' < "$f" | wc -c)
  if [ "$o" -eq "$c" ]; then ok "$f ($o/$c)"; else note "$f unbalanced { $o vs } $c"; fi
done

# ── 2. core freeze + v3 constitution ─────────────────────────────────────────
echo "palette: core tokens freeze vs HEAD"
if git rev-parse HEAD >/dev/null 2>&1; then
  if git diff --quiet HEAD -- tokens.css 2>/dev/null; then
    ok "tokens.css unchanged"
  else
    missing=$(git show HEAD:"tokens.css" 2>/dev/null | grep -E -- '^[[:space:]]*--el-(bg|panel|line|ink|accent|ok|warn|fail|info|live|teal|on-accent|mute|focus-ring|overlay|shadow)[-:]' | sort -u | while IFS= read -r line; do grep -qF -- "$line" tokens.css || echo "$line"; done)
    if [ -z "$missing" ]; then ok "tokens.css: all core color tokens intact (additive only)"; else note "tokens.css lost/changed: $missing"; fi
  fi
else
  echo "  - not a git checkout, skipping freeze check"
fi

echo "themes: v3 constitution"
distinct=$(grep -oE '\[data-theme="[a-z0-9-]+"\]\s*\{' themes.css 2>/dev/null | sed -E 's/\[data-theme="([a-z0-9-]+)".*/\1/' | sort -u | wc -l)
if [ "$distinct" -eq 20 ]; then ok "20 distinct themes in themes.css"; else note "themes.css has $distinct distinct themes (want 20)"; fi
for old in polaroid cockpit-pape console compact casebook agent-paper agent-pulse agent-history terminal swiss bespoke torque umami paper-desk dark-editorial atelier cockpit; do
  if grep -q "\[data-theme=\"$old\"\]" themes.css; then note "old theme '$old' still present"; fi
done
comments=$(grep -o -F '/*' themes.css 2>/dev/null | wc -l)
if [ "$comments" -eq 0 ]; then ok "themes.css comment-free"; else note "themes.css has $comments comment openers"; fi
if grep -q ':root' themes.css; then note "stray :root in themes.css"; else ok "no :root in themes.css"; fi
if [ -s fonts.css ]; then ok "fonts.css present"; else note "fonts.css missing/empty"; fi

# ── 3. JS syntax ─────────────────────────────────────────────────────────────
echo "js: node --check"
for j in elements.js charts.js theme-switcher.js elements-workflow.js; do
  if [ -f "$j" ] && node --check "$j" 2>/dev/null; then ok "$j"; else note "$j failed node --check"; fi
done

# ── 4. demo classes exist in CSS ─────────────────────────────────────────────
echo "demo: class coverage"
css_all=$(cat *.css)
missing_total=0
for page in demo/*.html; do
  for cls in $(grep -o 'class="[^"]*"' "$page" | sed 's/class="//;s/"//' | tr ' ' '\n' | sort -u); do
    case "$cls" in ''|on|sub|open|sel|bar|cell|node|edge|day|dow|head|grid|label|prev|next|track|slide|nav|dots|dot|input|results|row|key|pane|handle|dragging|panel|tab|close|mark|text|add|del|ctx|lvl-*|ok|warn|fail|live|today|center|el-date-toggle) continue;; esac
    if ! grep -q "\.$cls" <<<"$css_all" 2>/dev/null && ! grep -q "\.$cls" *.css demo/*.html 2>/dev/null; then
      note "$page: .$cls not found in any CSS"; missing_total=$((missing_total+1))
    fi
  done
done
[ "$missing_total" -eq 0 ] && ok "all demo classes resolve"

# ── 5. icons referenced by Elements.icon exist in the sprite ─────────────────
echo "icons: sprite coverage"
for name in $(grep -oh "Elements\.icon('\K[a-z-]*" demo/*.html | sort -u) $(grep -oh "icon('\K[a-z-]*" elements.js | sort -u); do
  grep -q "id=\"el-i-$name\"" assets/icons.svg || note "missing icon: el-i-$name"
done

# ── build freshness (themes.css must not be older than any family src) ───────
echo "build: themes.css matches sources"
scratch=$(mktemp)
cp themes.css "$scratch"
python3 tools/build_themes.py "$scratch" >/dev/null 2>&1
if diff -q "$scratch" themes.css >/dev/null 2>&1; then
  ok "themes.css is exactly the build output of themes/src"
else
  note "themes.css STALE — differs from rebuilding themes/src; regenerate with tools/build_themes.py"
fi
rm -f "$scratch"

# ── 6. cascade layer integrity (D-3: wired checkers) ─────────────────────────
echo "layer + site coverage: wired tools"
if out=$(python3 tools/check_layers.py 2>&1); then ok "$out"; else note "$out"; fi
slugs=$(cd demo/sites && ls -d */ 2>/dev/null | tr -d '/')
if [ -n "$slugs" ] && site_out=$(python3 tools/check_sites.py $slugs 2>&1); then
  ok "all 20 sites cover the 63-element inventory"
else
  note "site coverage failed: $(echo "$site_out" | tail -2)"
fi

echo
if [ "$fail" -eq 1 ]; then
  echo "verify: FAILED ($pass passed, see ✗ above)"
  exit 1
fi
echo "verify: OK ($pass checks passed)"
exit 0