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

# ── 2. palette freeze (vs git HEAD; skipped outside a git checkout) ──────────
echo "palette: freeze vs HEAD"
if git rev-parse HEAD >/dev/null 2>&1; then
  for f in tokens.css themes.css; do
    if git diff --quiet HEAD -- "$f" 2>/dev/null; then
      ok "$f unchanged"
    else
      # allow new content; every historical --el-<color> declaration must survive verbatim
      missing=$(git show HEAD:"$f" 2>/dev/null | grep -E -- '--el-(bg|panel|line|ink|accent|ok|warn|fail|info|live|teal|on-accent|mute|focus-ring|overlay|shadow)[-:]' | sort -u | while IFS= read -r line; do grep -qF -- "$line" "$f" || echo "$line"; done)
      if [ -z "$missing" ]; then ok "$f: all frozen color tokens intact"; else note "$f lost/changed: $missing"; fi
    fi
  done
else
  echo "  - not a git checkout, skipping freeze check"
fi

# ── 3. JS syntax ─────────────────────────────────────────────────────────────
echo "js: node --check"
for j in elements.js charts.js theme-switcher.js; do
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
ok "icon check done"

echo
if [ "$fail" -eq 1 ]; then
  echo "verify: FAILED ($pass passed, see ✗ above)"
  exit 1
fi
echo "verify: OK ($pass checks passed)"
exit 0