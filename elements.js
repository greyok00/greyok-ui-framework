/**
 * greyok-ui-framework: element behavior wiring.
 *
 * Attaches interactive behavior to .el-* markup: tabs, accordions, toggles,
 * drag and drop, menus, dialogs and drawers, the command palette, toasts,
 * keyboard support and the small input widgets. No network use and no timers
 * beyond toast and copy-button lifetimes; motion respects
 * prefers-reduced-motion. Public surface lives on window.Elements and
 * window.elToast; re-wiring a dynamically added subtree is done by calling
 * window.elInit(root).
 */
(function Elements() {
  'use strict';
  const $  = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
  const on = (el, ev, fn, opts) => el && el.addEventListener(ev, fn, opts);
  const fire = (el, name, detail) => el && el.dispatchEvent(new CustomEvent(name, { detail, bubbles: true }));

  /* Wiring convention: every wireX() marks the nodes it touches with a __wired
     (or hook-specific) expando key, so re-running init() on the same subtree is
     a no-op and dynamically added nodes can be wired individually. */

  /* ── selection surfaces: tabs, accordion, segmented, toggles, tree ───────── */
  function wireTabs(root) {
    ['.el-tabs-h', '.el-tabs-v', '.el-tabs-pill'].forEach(cls => {
      $$(`${cls} [data-target]`, root).forEach(tab => {
        if (tab.__wired) return; tab.__wired = true;
        on(tab, 'click', () => {
          const group = tab.closest(cls);
          $$('[data-target]', group).forEach(t => t.classList.remove('on'));
          tab.classList.add('on');
          const tgt = document.querySelector(tab.dataset.target);
          if (!tgt) return;
          const panels = $$(`.${cls}-panel[data-for="${group.id || ''}"]`, document);
          const groupId = group.id;
          if (groupId) {
            $$(`[data-tabpanel][data-group="${groupId}"]`, document).forEach(p => p.hidden = (p.id !== tab.dataset.target.replace('#', '')));
          }
          fire(tgt, 'el:tab', { tab });
        });
      });
    });
  }
  function wireAccordion(root) {
    $$('.el-accordion', root).forEach(acc => {
      if (acc.__wired) return; acc.__wired = true;
      const exclusive = acc.hasAttribute('data-exclusive');
      $$('details', acc).forEach(d => {
        on(d, 'toggle', () => {
          if (exclusive && d.open) {
            $$('details', acc).forEach(o => { if (o !== d) o.open = false; });
          }
        });
      });
    });
  }
  function wireSegmented(root) {
    $$('.el-segmented', root).forEach(seg => {
      if (seg.__wired) return; seg.__wired = true;
      $$('button', seg).forEach(b => {
        on(b, 'click', () => {
          $$('button', seg).forEach(o => o.classList.remove('on'));
          b.classList.add('on');
          fire(seg, 'el:segmented', { value: b.textContent.trim(), button: b });
        });
      });
    });
  }
  function wireToggles(root) {
    ['.el-toggle', '.el-switch', '.el-check'].forEach(cls => {
      $$(cls, root).forEach(el => {
        if (el.__wired) return; el.__wired = true;
        on(el, 'click', () => {
          el.classList.toggle('on');
          fire(el, 'el:toggle', { on: el.classList.contains('on') });
        });
      });
    });
    $$('.el-radio input[type="radio"]', root).forEach(inp => {
      if (inp.__wired) return; inp.__wired = true;
      on(inp, 'change', () => {
        const name = inp.name;
        $$(`.el-radio input[name="${name}"]`).forEach(o => {
          o.checked = (o === inp);
          o.parentElement.classList.toggle('on', o.checked);
        });
        fire(inp.closest('.el-radio'), 'el:radio', { value: inp.value });
      });
    });
  }
  /* ── drag and drop ── */
  function wireHoverCard(root) {
    $$('.el-hover-card', root).forEach(card => {
      if (card.__wired) return; card.__wired = true;
      on(card, 'click', () => card.classList.toggle('locked'));
    });
  }
  function wireTreeList(root) {
    $$('.el-tree-list .node', root).forEach(node => {
      if (node.__wired) return; node.__wired = true;
      const toggle = $('.toggle', node);
      if (!toggle) return;
      on(toggle, 'click', (e) => {
        e.stopPropagation();
        node.parentElement.classList.toggle('collapsed');
      });
    });
  }
  function wireDragDrop(root) {
    $$('[data-draggable]', root).forEach(el => {
      if (el.__wired) return; el.__wired = true;
      el.draggable = true;
      on(el, 'dragstart', e => {
        el.classList.add('dragging');
        e.dataTransfer.setData('text/plain', el.dataset.dragLabel || el.textContent.trim());
        e.dataTransfer.effectAllowed = 'move';
      });
      on(el, 'dragend', () => el.classList.remove('dragging'));
    });
    $$('[data-target-list]', root).forEach(list => {
      if (list.__wired) return; list.__wired = true;
      on(list, 'dragover', e => {
        e.preventDefault();
        list.classList.add('drop-target');
      });
      on(list, 'dragleave', () => list.classList.remove('drop-target'));
      on(list, 'drop', e => {
        e.preventDefault();
        list.classList.remove('drop-target');
        const dragged = document.querySelector('.dragging');
        if (dragged) {
          list.appendChild(dragged);
          fire(list, 'el:drop', { item: dragged });
        }
      });
    });
  }
  function wireCombobox(root) {
    $$('.el-combobox', root).forEach(cb => {
      if (cb.__wired) return; cb.__wired = true;
      const input = $('input', cb);
      const menu  = $('.menu', cb);
      const opts  = $$('.opt', menu);
      on(input, 'focus', () => cb.classList.add('open'));
      on(input, 'blur', () => setTimeout(() => cb.classList.remove('open'), 120));
      on(input, 'input', () => {
        const q = input.value.toLowerCase();
        opts.forEach(o => {
          o.hidden = !o.textContent.toLowerCase().includes(q);
        });
      });
      opts.forEach(o => on(o, 'click', () => {
        input.value = o.textContent.trim();
        cb.classList.remove('open');
        fire(cb, 'el:select', { value: o.dataset.value || o.textContent.trim() });
      }));
    });
  }
  function wireMultiSelect(root) {
    $$('.el-multi-select', root).forEach(ms => {
      if (ms.__wired) return; ms.__wired = true;
      let input = $('input', ms);
      if (!input) {
        input = document.createElement('input');
        ms.appendChild(input);
      }
      on(input, 'keydown', (e) => {
        if (e.key === 'Enter' && input.value.trim()) {
          e.preventDefault();
          const pill = document.createElement('span');
          pill.className = 'pill';
          pill.appendChild(document.createTextNode(input.value.trim()));
          const x = document.createElement('span');
          x.className = 'x';
          x.setAttribute('aria-label', 'Dismiss');
          x.textContent = '×';
          pill.appendChild(x);
          ms.insertBefore(pill, input);
          input.value = '';
          fire(ms, 'el:add', { value: pill.textContent.replace('×', '').trim() });
        } else if (e.key === 'Backspace' && !input.value) {
          const pills = $$('.pill', ms);
          if (pills.length) pills[pills.length - 1].remove();
        }
      });
      on(ms, 'click', (e) => {
        if (e.target.classList.contains('x')) {
          e.target.parentElement.remove();
          fire(ms, 'el:remove', { value: e.target.parentElement.textContent.replace('×', '').trim() });
        }
      });
    });
  }
  function wireDropdownMenu(root) {
    $$('.el-dropdown-menu', root).forEach(dm => {
      if (dm.__wired) return; dm.__wired = true;
      const trig = $('.trigger', dm);
      const setOpen = (v) => {
        dm.classList.toggle('open', v);
        dm.classList.toggle('is-open', v);
        if (trig) trig.setAttribute('aria-expanded', v ? 'true' : 'false');
        fire(dm, v ? 'el:open' : 'el:close', {});
      };
      on(trig, 'click', (e) => {
        e.stopPropagation();
        setOpen(!dm.classList.contains('open'));
      });
      on(trig, 'keydown', (e) => { if (e.key === 'Escape') setOpen(false); });
      on(document, 'click', (e) => {
        if (!dm.contains(e.target)) setOpen(false);
      });
    });
  }
  function wireContextMenu(root) {
    $$('[data-context-target]', root).forEach(t => {
      if (t.__wired) return; t.__wired = true;
      const menu = document.querySelector(t.dataset.contextTarget);
      if (!menu) return;
      on(t, 'contextmenu', (e) => {
        e.preventDefault();
        menu.style.left = e.clientX + 'px';
        menu.style.top  = e.clientY + 'px';
        menu.classList.add('open');
      });
    });
    $$('.el-context-menu', root).forEach(m => {
      if (m.__wired) return; m.__wired = true;
      on(document, 'click', () => m.classList.remove('open'));
      on(m, 'click', (e) => {
        if (e.target.classList.contains('item')) {
          fire(m, 'el:context', { item: e.target.textContent.trim() });
        }
      });
    });
  }
  function wireTooltip(root) {
    $$('.el-tooltip[data-tip-placement]', root).forEach(t => {
      if (t.__wired) return; t.__wired = true;
      on(t, 'mouseenter', () => {
      });
    });
  }
  function wirePopover(root) {
    $$('.el-popover', root).forEach(p => {
      if (p.__wired) return; p.__wired = true;
      const trig = $(':scope > *:not(.el-pop)', p);
      const setOpen = (v) => {
        p.classList.toggle('is-open', v);
        p.classList.toggle('open', v);
        if (trig) trig.setAttribute('aria-expanded', v ? 'true' : 'false');
        fire(p, v ? 'el:open' : 'el:close', {});
      };
      on(trig, 'click', (e) => {
        e.stopPropagation();
        setOpen(!p.classList.contains('is-open'));
      });
      on(p, 'keydown', e => { if (e.key === 'Escape') setOpen(false); });
    });
    on(document, 'click', () => $$('.el-popover.open').forEach(o => {
      o.classList.remove('open'); o.classList.remove('is-open');
      const trig = $(':scope > *:not(.el-pop)', o);
      if (trig) trig.setAttribute('aria-expanded', 'false');
    }));
  }
  /* ── overlays: modal, drawer, dialog (with shared scrim + focus restore) ── */
  function wireModal(root) {
    $$('[data-modal-open]', root).forEach(btn => {
      if (btn.__wired) return; btn.__wired = true;
      on(btn, 'click', () => {
        const m = document.getElementById(btn.dataset.modalOpen);
        if (m) m.classList.add('open');
      });
    });
    $$('[data-modal-close]', root).forEach(btn => {
      if (btn.__wired) return; btn.__wired = true;
      on(btn, 'click', () => {
        const m = btn.closest('.el-modal-backdrop');
        if (m) m.classList.remove('open');
      });
    });
    $$('.el-modal-backdrop', root).forEach(bd => {
      if (bd.__wired) return; bd.__wired = true;
      on(bd, 'click', (e) => { if (e.target === bd) bd.classList.remove('open'); });
    });
  }
  function wireDrawer(root) {
    $$('[data-drawer-open]', root).forEach(btn => {
      if (btn.__wired) return; btn.__wired = true;
      on(btn, 'click', () => {
        const d = document.getElementById(btn.dataset.drawerOpen);
        if (d) openDrawer(d, btn);
      });
    });
    $$('[data-drawer-close]', root).forEach(btn => {
      if (btn.__wired) return; btn.__wired = true;
      on(btn, 'click', () => closeDrawer(btn.closest('.el-drawer')));
    });
  }
  /* ── overlay core: paired scrim sync + opener bookkeeping (focus returns) ── */
  const openers = new WeakMap();
  /* public APIs accept an element OR an id string (or a selector) */
  function resolveEl(target, cls) {
    if (typeof target !== 'string') return target || null;
    const found = document.getElementById(target) || document.querySelector(target);
    if (found == null) return null;
    return (cls && !found.classList.contains(cls)) ? null : found;
  }
  function restoreFocus(el) {
    const opener = openers.get(el);
    openers.delete(el);
    if (opener && document.contains(opener)) { try { opener.focus(); } catch (e) {} }
  }
  function scrimIds(el) {
    return (el.dataset.scrim || '').trim().split(/\s+/).filter(Boolean);
  }
  function syncScrims(el, open) {
    scrimIds(el).forEach(id => {
      const s = document.getElementById(id);
      if (!s) return;
      s.classList.toggle('is-open', open);
      s.classList.toggle('open', open);
    });
  }
  function closeOverlayPanel(el) {
    if (!el) return;
    if (el.classList.contains('el-drawer')) return closeDrawer(el);
    if (el.classList.contains('el-command')) return closeCommand(el);
    if (el.classList.contains('el-dialog')) return closeDialog(el);
  }
  function openDrawer(drawer, opener) {
    const d = resolveEl(drawer, 'el-drawer');
    if (!d) return;
    if (opener) openers.set(d, opener);
    d.classList.add('open', 'is-open');
    syncScrims(d, true);
    fire(d, 'el:open', {});
  }
  function closeDrawer(drawer) {
    const d = resolveEl(drawer, 'el-drawer');
    if (!d) return;
    if (openers.has(d) && d.contains(document.activeElement)) restoreFocus(d);
    d.classList.remove('open', 'is-open');
    syncScrims(d, false);
    fire(d, 'el:close', {});
  }
  function openDialog(dialog, opener) {
    const d = resolveEl(dialog, 'el-dialog');
    if (!d) return;
    if (opener) openers.set(d, opener);
    if (d.tagName === 'DIALOG' && !d.open) d.showModal();
    d.classList.add('is-open', 'open');
    syncScrims(d, true);
    fire(d, 'el:open', {});
    if (d.tagName !== 'DIALOG') {
      const first = $('[autofocus], input, select, textarea, button', d);
      if (first) first.focus();
    }
  }
  function closeDialog(dialog) {
    const d = resolveEl(dialog, 'el-dialog');
    if (!d) return;
    const native = d.tagName === 'DIALOG' && d.open;
    /* native: UA restores its own pre-open focus after the close event, so our
       opener restore is deferred there (also covers ESC-closed dialogs) */
    if (!native && openers.has(d) && d.contains(document.activeElement)) restoreFocus(d);
    if (native) d.close();
    d.classList.remove('is-open', 'open');
    syncScrims(d, false);
    fire(d, 'el:close', {});
  }
  function wireDialog(root) {
    $$('[data-dialog-open]', root).forEach(btn => {
      if (btn.__wired) return; btn.__wired = true;
      on(btn, 'click', () => {
        const d = document.getElementById(btn.dataset.dialogOpen);
        if (d && d.classList.contains('el-dialog')) openDialog(d, btn);
      });
    });
    $$('[data-dialog-close]', root).forEach(btn => {
      if (btn.__wired) return; btn.__wired = true;
      on(btn, 'click', () => closeDialog(btn.closest('.el-dialog')));
    });
    $$('.el-dialog', root).forEach(d => {
      if (d.__wired) return; d.__wired = true;
      if (d.tagName === 'DIALOG') {
        d.addEventListener('close', () => {
          d.classList.remove('is-open', 'open');
          syncScrims(d, false);
          fire(d, 'el:close', {});
          setTimeout(() => restoreFocus(d), 0);
        });
      }
    });
    $$('.el-scrim[data-dialog-scrim]', root).forEach(s => {
      if (s.__wired) return; s.__wired = true;
      on(s, 'click', e => {
        if (e.target !== s) return;
        const owner = document.querySelector(`[data-scrim~="${s.id}"]`);
        if (owner) closeOverlayPanel(owner);
      });
    });
    on(document, 'keydown', (e) => {
      if (e.key !== 'Escape') return;
      const t = e.target;
      if (t && t.closest && t.closest('.el-menu, .el-popover, .el-drawer')) return;
      const open = $$('.el-dialog.is-open:not(dialog)', document);
      const top = open[open.length - 1];
      if (top) { e.preventDefault(); closeDialog(top); }
    });
  }
  /* ── menu list: [data-menu] trigger → .el-menu surface, arrows + Esc + click-away ── */
  function wireMenu(root) {
    $$('[data-menu]', root).forEach(trig => {
      if (trig.__wired) return; trig.__wired = true;
      const menu = document.getElementById(trig.dataset.menu);
      if (!menu) return;
      const items = () => $$('.el-menu-item:not([hidden]):not([aria-disabled="true"])', menu);
      const setOpen = (v) => {
        menu.classList.toggle('is-open', v);
        menu.classList.toggle('open', v);
        trig.setAttribute('aria-expanded', v ? 'true' : 'false');
        fire(menu, v ? 'el:open' : 'el:close', { trigger: trig });
        if (v && trig.matches(':focus-visible')) {
          const first = items()[0];
          if (first) first.focus();
        }
      };
      on(trig, 'click', (e) => {
        e.stopPropagation();
        setOpen(!menu.classList.contains('is-open'));
      });
      on(trig, 'keydown', (e) => {
        if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setOpen(true); }
        else if (e.key === 'Escape') setOpen(false);
      });
      on(document, 'click', (e) => {
        if (!menu.contains(e.target) && !trig.contains(e.target)) setOpen(false);
      });
      on(menu, 'keydown', (e) => {
        const list = items();
        const idx = list.indexOf(document.activeElement);
        if (e.key === 'ArrowDown') { e.preventDefault(); if (list[(idx + 1) % list.length]) list[(idx + 1) % list.length].focus(); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); if (list[idx <= 0 ? list.length - 1 : idx - 1]) list[idx <= 0 ? list.length - 1 : idx - 1].focus(); }
        else if (e.key === 'Home') { e.preventDefault(); if (list[0]) list[0].focus(); }
        else if (e.key === 'End') { e.preventDefault(); if (list[list.length - 1]) list[list.length - 1].focus(); }
        else if (e.key === 'Escape') { e.preventDefault(); setOpen(false); trig.focus(); }
      });
      on(menu, 'click', (e) => {
        const item = e.target.closest('.el-menu-item');
        if (!item || item.hasAttribute('data-menu-keep-open')) return;
        if (item.hasAttribute('aria-disabled')) return;
        fire(menu, 'el:menu-select', { item, value: item.dataset.value || item.textContent.trim() });
        setOpen(false);
        trig.focus();
      });
    });
  }
  /* ── command palette: type-to-run .el-command, rows are elements ─────────── */
  function openCommand(target, opener) {
    const cmd = resolveEl(target, 'el-command');
    if (!cmd) return;
    if (opener) openers.set(cmd, opener);
    cmd.classList.add('is-open', 'open');
    fire(cmd, 'el:open', {});
    const input = $('.el-command-input', cmd);
    const results = $('.el-command-results', cmd);
    if (results) $$('.el-command-row', results).forEach(r => r.hidden = false);
    if (cmd.__elCommandFilter) cmd.__elCommandFilter('');
    if (input) input.focus();
  }
  function closeCommand(target) {
    const cmd = resolveEl(target, 'el-command');
    if (!cmd) return;
    if (openers.has(cmd) && cmd.contains(document.activeElement)) restoreFocus(cmd);
    cmd.classList.remove('is-open', 'open');
    fire(cmd, 'el:close', {});
  }
  function wireCommand(root) {
    $$('.el-command', root).forEach(cmd => {
      if (cmd.__wired) return; cmd.__wired = true;
      const input = $('.el-command-input', cmd);
      const results = $('.el-command-results', cmd);
      const groups = $$('.el-command-group', cmd);
      const empty = $('.el-command-empty', cmd);
      const rows = () => $$('.el-command-row', results || cmd);
      const visible = () => rows().filter(r => !r.hidden);
      const picked = () => visible().find(r => r.classList.contains('sel'));
      const select = (row) => {
        rows().forEach(r => r.classList.remove('sel'));
        if (row) { row.classList.add('sel'); row.scrollIntoView({ block: 'nearest' }); }
      };
      const run = (row) => {
        if (!row) return;
        fire(cmd, 'el:command', { row, value: row.dataset.value || row.dataset.commandItem || row.textContent.trim() });
        closeCommand(cmd);
      };
      const filter = (q) => {
        q = (q || '').trim().toLowerCase();
        let first = null;
        rows().forEach(r => {
          const hay = (r.dataset.label || r.textContent).trim().toLowerCase();
          const hit = !q || hay.includes(q);
          r.hidden = !hit;
          if (hit && !first) first = r;
        });
        groups.forEach(g => {
          const mine = rows().filter(r => g.contains(r));
          g.hidden = mine.length > 0 && mine.every(r => r.hidden);
        });
        if (empty) empty.hidden = !!first;
        select(first);
      };
      cmd.__elCommandFilter = filter;
      if (input) {
        on(input, 'input', () => filter(input.value));
        on(input, 'keydown', (e) => {
          if (e.key === 'Escape') { e.preventDefault(); closeCommand(cmd); }
          else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            e.preventDefault();
            const rowsV = visible();
            if (!rowsV.length) return;
            const i = rowsV.indexOf(picked());
            const n = e.key === 'ArrowDown' ? Math.min(rowsV.length - 1, i < 0 ? 0 : i + 1) : Math.max(0, i < 0 ? 0 : i - 1);
            select(rowsV[n]);
          } else if (e.key === 'Enter') { e.preventDefault(); run(picked() || visible()[0]); }
        });
      }
      if (results) {
        on(results, 'click', (e) => {
          const row = e.target.closest('.el-command-row');
          if (!row) return;
          run(row);
        });
      }
      on(cmd, 'click', (e) => { if (e.target === cmd) closeCommand(cmd); });
      on(cmd, 'keydown', (e) => {
        if (e.key !== 'Escape' || document.activeElement === input) return;
        e.preventDefault();
        closeCommand(cmd);
      });
    });
    $$('[data-command], [data-command-open]', root).forEach(trig => {
      if (trig.__wired) return; trig.__wired = true;
      on(trig, 'click', () => {
        const ref = trig.dataset.command || trig.dataset.commandOpen;
        const cmd = ref ? document.getElementById(ref) || document.querySelector(ref) : $('.el-command');
        if (cmd) openCommand(cmd, trig);
      });
    });
  }
  /* ── toasts: a single status region, capped region, promise helper ── */
  function ensureToastRegion() {
    let r = $('.el-toast-region');
    if (!r) {
      r = document.createElement('div');
      r.className = 'el-toast-region';
      r.setAttribute('role', 'status');
      r.setAttribute('aria-live', 'polite');
      document.body.appendChild(r);
    }
    return r;
  }
  function dismissToast(t) {
    if (!t || t.__leaving) return;
    t.__leaving = true;
    t.classList.add('is-leaving');
    const gone = () => t.remove();
    t.addEventListener('animationend', gone, { once: true });
    setTimeout(gone, 300);
  }
  function pushToast(msg, variant, opts) {
    opts = opts || {};
    const r = ensureToastRegion();
    /* cap drops the oldest synchronously: dismissToast only animates, it never
       removes on its own, so a dismiss-based loop here would never terminate */
    while (r.children.length > 4 && r.firstElementChild) r.firstElementChild.remove();
    const t = document.createElement('div');
    t.className = `el-toast ${variant || opts.variant || opts.type || ''}`.trim();
    t.setAttribute('role', 'status');
    t.innerHTML = '<span></span><span class="close" aria-label="Dismiss">×</span>';
    $('span', t).textContent = msg == null ? '' : String(msg);
    r.appendChild(t);
    $('.close', t).addEventListener('click', () => dismissToast(t));
    if (opts.duration !== 0) setTimeout(() => dismissToast(t), opts.duration || 4000);
    fire(r, 'el:toast', { msg, variant: variant || opts.variant || opts.type || '' });
    return t;
  }
  window.elToast = { push: pushToast, dismiss: dismissToast };
  function toast(msg, opts) {
    opts = opts || {};
    return pushToast(msg, opts.variant || opts.type || '', opts);
  }
  function toastPromise(promise, opts) {
    opts = opts || {};
    const t = toast(opts.loading || 'Loading…', { duration: 0 });
    const done = (variant, msg) => {
      t.className = `el-toast ${variant}`;
      $('span', t).textContent = msg;
      setTimeout(() => t.remove(), 4000);
    };
    Promise.resolve(promise).then(
      v => done('ok', typeof opts.success === 'function' ? opts.success() : (opts.success || 'Done')),
      err => done('fail', typeof opts.error === 'function' ? opts.error(err) : (opts.error || 'Failed'))
    );
    return promise;
  }
  /* ── data surfaces: pagination, breadcrumb, scroll shadows, table sort ── */
  function wirePagination(root) {
    $$('.el-pagination[data-page-source]', root).forEach(pag => {
      if (pag.__wired) return; pag.__wired = true;
      const list = document.querySelector(pag.dataset.pageSource);
      if (!list) return;
      const items = $$(':scope > *', list);
      const size  = parseInt(pag.dataset.pageSize || '5', 10);
      let page    = 1;
      const total = Math.ceil(items.length / size);
      const render = () => {
        items.forEach((it, i) => {
          it.hidden = !(i >= (page - 1) * size && i < page * size);
        });
        const info = $('.info', pag);
        if (info) info.textContent = `${page} / ${total}`;
      };
      $$('.page', pag).forEach(btn => {
        on(btn, 'click', () => {
          if (btn.classList.contains('disabled')) return;
          const action = btn.dataset.action;
          if (action === 'first') page = 1;
          else if (action === 'prev') page = Math.max(1, page - 1);
          else if (action === 'next') page = Math.min(total, page + 1);
          else if (action === 'last') page = total;
          else page = parseInt(btn.textContent, 10) || 1;
          render();
        });
      });
      render();
    });
  }
  function wireBreadcrumb(root) {
    $$('.el-breadcrumb[data-collapse-after]', root).forEach(bc => {
      if (bc.__wired) return; bc.__wired = true;
      const children = Array.from(bc.children).filter(c => !c.classList.contains('sep'));
      const after = parseInt(bc.dataset.collapseAfter, 10);
      if (children.length <= after + 1) return;
      children.slice(after, -1).forEach(c => c.hidden = true);
      const dots = document.createElement('span');
      dots.className = 'sep';
      dots.textContent = '…';
      children[after - 1].after(dots);
    });
  }
  function wireScrollShadow(root) {
    if (!('IntersectionObserver' in window)) return;
    $$('.el-scroll-shadow', root).forEach(s => {
      if (s.__wired) return; s.__wired = true;
      const top = document.createElement('div');
      const bot = document.createElement('div');
      top.style.cssText = 'position:absolute;top:0;left:0;right:0;height:1px;';
      bot.style.cssText = 'position:absolute;bottom:0;left:0;right:0;height:1px;';
      s.style.position = 'relative';
      s.appendChild(top); s.appendChild(bot);
      const obs = new IntersectionObserver(es => {
        s.dataset.shadowTop  = es.find(e => e.target === top).isIntersecting ? '' : 'on';
        s.dataset.shadowBot  = es.find(e => e.target === bot).isIntersecting ? '' : 'on';
      });
      obs.observe(top); obs.observe(bot);
    });
  }
  function wireChips(root) {
    $$('.el-chip', root).forEach(c => {
      if (c.__wired) return; c.__wired = true;
      on(c, 'click', () => c.classList.toggle('added'));
    });
  }
  function wireTable(root) {
    $$('.el-table', root).forEach(tbl => {
      const ths = $$('thead th', tbl);
      ths.forEach((th, i) => {
        if (th.__wired) return; th.__wired = true;
        on(th, 'click', () => {
          const dir = th.dataset.sortDir === 'asc' ? 'desc' : 'asc';
          ths.forEach(o => o.dataset.sortDir = '');
          th.dataset.sortDir = dir;
          const rows = $$('tbody tr', tbl);
          rows.sort((a, b) => {
            const x = a.children[i].textContent.trim();
            const y = b.children[i].textContent.trim();
            return dir === 'asc' ? x.localeCompare(y) : y.localeCompare(x);
          });
          const tb = $('tbody', tbl);
          rows.forEach(r => tb.appendChild(r));
        });
      });
    });
  }
  function wirePalette(root) {
    $$('.el-palette .input', root).forEach(input => {
      if (input.__wired) return; input.__wired = true;
      const palette = input.closest('.el-palette');
      const store = palette.dataset.recentStore || 'el:palette:recent';
      let recent = [];
      try { recent = JSON.parse(localStorage.getItem(store) || '[]'); } catch (e) {}
      const target = r => $('.label', r) || r.children[1] || r;
      const label = r => (r.dataset.label || target(r).textContent.trim());
      const rows = $$('.row', palette);
      rows.forEach(r => {
        if (recent.includes(label(r))) r.dataset.recent = '';
      });
      const sortRows = (q) => {
        const scored = rows.map(r => {
          const t = label(r).toLowerCase();
          let score = 0;
          if (q) {
            let i = -1;
            for (const ch of q) { i = t.indexOf(ch, i + 1); if (i < 0) { score = -1; break; } score += 1; }
            if (score >= 0 && t.startsWith(q)) score += 10;
            if (recent.includes(label(r))) score += 5;
          } else {
            score = recent.includes(label(r)) ? 5 : 0;
          }
          return { r, score };
        }).filter(s => s.score >= 0);
        scored.sort((a, b) => b.score - a.score);
        return scored.map(s => s.r);
      };
      const highlight = (r, q) => {
        const span = target(r);
        const text = label(r);
        if (!q) { span.textContent = text; return; }
        span.textContent = '';
        const lower = text.toLowerCase();
        let ti = 0, i = -1;
        for (const ch of q) {
          i = lower.indexOf(ch, i + 1);
          if (i < 0) break;
          span.append(document.createTextNode(text.slice(ti, i)));
          const mark = document.createElement('mark');
          mark.textContent = text[i];
          span.append(mark);
          ti = i + 1;
        }
        span.append(document.createTextNode(text.slice(ti)));
      };
      on(input, 'input', () => {
        const q = input.value.trim().toLowerCase();
        const order = sortRows(q);
        rows.forEach(r => r.hidden = !order.includes(r));
        order.forEach(r => {
          if (!r.hidden) { palette.querySelector('.results').appendChild(r); highlight(r, q); }
        });
      });
      on(palette, 'el:run', () => {
        const sel = $('.row.sel', palette) || $$('.row:not([hidden])', palette)[0];
        if (!sel) return;
        const key = label(sel);
        recent = [key].concat(recent.filter(r => r !== key)).slice(0, 5);
        try { localStorage.setItem(store, JSON.stringify(recent)); } catch (e) {}
        sel.dataset.recent = '';
      });
    });
  }
  function wireAnchorNav(root) {
    if (!('IntersectionObserver' in window)) return;
    $$('.el-anchor-nav', root).forEach(nav => {
      const links = $$('a[href^="#"]', nav);
      if (!links.length) return;
      const targets = links.map(l => document.querySelector(l.getAttribute('href'))).filter(Boolean);
      if (!targets.length) return;
      const obs = new IntersectionObserver(es => {
        es.forEach(e => {
          if (e.isIntersecting) {
            links.forEach(l => l.classList.remove('active'));
            const link = links.find(l => l.getAttribute('href') === '#' + e.target.id);
            if (link) link.classList.add('active');
          }
        });
      }, { rootMargin: '-30% 0px -60% 0px' });
      targets.forEach(t => obs.observe(t));
    });
  }
  /* Entry point: wires every behavior under root. Safe to call repeatedly. */
  function init(root) {
    root = root || document;
    wireTabs(root);
    wireAccordion(root);
    wireSegmented(root);
    wireToggles(root);
    wireHoverCard(root);
    wireTreeList(root);
    wireDragDrop(root);
    wireCombobox(root);
    wireMultiSelect(root);
    wireDropdownMenu(root);
    wireContextMenu(root);
    wireTooltip(root);
    wirePopover(root);
    wireModal(root);
    wireDrawer(root);
    wireDialog(root);
    wireMenu(root);
    wireCommand(root);
    wirePagination(root);
    wireBreadcrumb(root);
    wireScrollShadow(root);
    wireChips(root);
    wireTable(root);
    wirePalette(root);
    wireAnchorNav(root);
    wireSignaturePad(root);
    wireAudioWaveform(root);
    wireFileUpload(root);
    wireCodeBlock(root);
    wireKbdInput(root);
    wireRating(root);
    wireProgressAnimate(root);
    wireToastDismiss(root);
    wireToastHooks(root);
    wirePaletteKeyboard(root);
    wireComboboxKeyboard(root);
    wireTabsKeyboard(root);
    wireAccordionKeyboard(root);
    wireTreeListKeyboard(root);
    wireToggleKeyboard(root);
    wireModalKeyboard(root);
    wireDrawerKeyboard(root);
    wireSlider(root);
    wireSearchBar(root);
    wirePrompt(root);
    wireClipboard(root);
    wireDatePicker(root);
    wireCarousel(root);
    wireSplitResizable(root);
    wireSkeletonLoaded(root);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => init());
  } else {
    init();
  }
  /* ── input widgets: canvas, upload, copy, capture hooks ── */
  function wireSignaturePad(root) {
    $$('.el-signature-pad', root).forEach(canvas => {
      if (canvas.__wired) return; canvas.__wired = true;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
      ctx.strokeStyle = getComputedStyle(canvas).getPropertyValue('--el-ink').trim() || '#000';
      ctx.lineWidth = 2; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      let drawing = false, lastX = 0, lastY = 0;
      const start = (x, y) => { drawing = true; lastX = x; lastY = y; };
      const move = (x, y) => {
        if (!drawing) return;
        ctx.beginPath(); ctx.moveTo(lastX, lastY); ctx.lineTo(x, y); ctx.stroke();
        lastX = x; lastY = y;
      };
      const stop = () => { drawing = false; };
      on(canvas, 'pointerdown', e => { canvas.setPointerCapture(e.pointerId); start(e.offsetX, e.offsetY); });
      on(canvas, 'pointermove', e => move(e.offsetX, e.offsetY));
      on(canvas, 'pointerup',   stop);
      on(canvas, 'pointerleave', stop);
      on(canvas, 'dblclick', () => ctx.clearRect(0, 0, canvas.width, canvas.height));
    });
  }
  function wireAudioWaveform(root) {
    $$('.el-audio-waveform', root).forEach(w => {
      if (w.__wired) return; w.__wired = true;
      const bars = $$('.bar', w);
      const total = bars.length;
      let playing = false;
      let pos = 0;
      let timer = null;
      const render = () => {
        bars.forEach((b, i) => b.classList.toggle('played', i < pos));
      };
      on(w, 'click', e => {
        const rect = w.getBoundingClientRect();
        const x = e.clientX - rect.left;
        pos = Math.round((x / rect.width) * total);
        render();
        fire(w, 'el:seek', { position: pos });
      });
      const play = () => {
        playing = true;
        if (timer) clearInterval(timer);
        timer = setInterval(() => {
          if (pos < total) { pos++; render(); }
          else { pause(); }
        }, 120);
      };
      const pause = () => { playing = false; if (timer) clearInterval(timer); };
      on(w, 'dblclick', () => playing ? pause() : play());
    });
  }
  function wireFileUpload(root) {
    $$('.el-file-upload', root).forEach(fu => {
      if (fu.__wired) return; fu.__wired = true;
      const input = document.createElement('input');
      input.type = 'file'; input.multiple = true; input.style.display = 'none';
      fu.appendChild(input);
      on(fu, 'click', () => input.click());
      on(input, 'change', () => {
        const names = Array.from(input.files).map(f => f.name).join(', ');
        if (names) {
          const hint = $('.hint', fu);
          if (hint) hint.textContent = `Selected: ${names}`;
          fire(fu, 'el:upload', { files: input.files });
        }
      });
      ['dragenter', 'dragover'].forEach(ev => on(fu, ev, e => { e.preventDefault(); fu.classList.add('over'); }));
      ['dragleave', 'drop'].forEach(ev => on(fu, ev, e => { e.preventDefault(); fu.classList.remove('over'); }));
      on(fu, 'drop', e => {
        const dt = e.dataTransfer;
        if (dt && dt.files.length) {
          const names = Array.from(dt.files).map(f => f.name).join(', ');
          const hint = $('.hint', fu);
          if (hint) hint.textContent = `Dropped: ${names}`;
          fire(fu, 'el:upload', { files: dt.files });
        }
      });
    });
  }
  function wireCodeBlock(root) {
    $$('.el-code-block', root).forEach(cb => {
      if (cb.__wired) return; cb.__wired = true;
      const text = cb.textContent.replace(/\n$/, '');
      const lines = text.split('\n');
      cb.innerHTML = '';
      lines.forEach((line, i) => {
        const row = document.createElement('div');
        row.style.display = 'flex';
        row.style.gap = 'var(--el-space-3)';
        const num = document.createElement('span');
        num.textContent = (i + 1).toString().padStart(2, ' ');
        num.style.color = 'var(--el-mute)';
        num.style.userSelect = 'none';
        num.style.minWidth = '2ch';
        num.style.textAlign = 'right';
        const code = document.createElement('span');
        code.innerHTML = line || '&nbsp;';
        row.appendChild(num); row.appendChild(code);
        cb.appendChild(row);
      });
      const btn = document.createElement('button');
      btn.textContent = 'Copy';
      btn.className = 'el-codecopy'; /* styling lives on the sheet now */
      cb.classList.add('is-copyable');
      cb.appendChild(btn);
      on(btn, 'click', () => {
        const t = lines.join('\n');
        if (navigator.clipboard) navigator.clipboard.writeText(t);
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = 'Copy', 1200);
        fire(cb, 'el:copy', { text: t });
      });
    });
  }
  function wireKbdInput(root) {
    $$('.el-kbd-input', root).forEach(inp => {
      if (inp.__wired) return; inp.__wired = true;
      on(inp, 'focus', () => inp.value = '');
      on(inp, 'blur', () => { if (!inp.value) inp.value = '⌘K'; });
      on(inp, 'keydown', e => {
        e.preventDefault();
        const parts = [];
        if (e.metaKey || e.ctrlKey) parts.push('⌘');
        if (e.shiftKey) parts.push('⇧');
        if (e.altKey) parts.push('⌥');
        let key = e.key;
        if (key === ' ') key = 'Space';
        else if (key.length === 1) key = key.toUpperCase();
        parts.push(key);
        inp.value = parts.join('+');
        fire(inp, 'el:kbd', { combo: inp.value });
      });
    });
  }
  function wireRating(root) {
    $$('.el-rating', root).forEach(r => {
      if (r.__wired) return; r.__wired = true;
      const stars = $$('.star', r);
      stars.forEach((s, i) => {
        on(s, 'click', () => {
          const on = i + 1;
          stars.forEach((o, j) => o.classList.toggle('on', j < on));
          fire(r, 'el:rate', { value: on });
        });
        on(s, 'mouseenter', () => {
          stars.forEach((o, j) => o.classList.toggle('on', j <= i));
        });
        on(r, 'mouseleave', () => {
          const cur = stars.filter(o => o.classList.contains('on')).length;
          stars.forEach((o, j) => o.classList.toggle('on', j < cur));
        });
      });
    });
  }
  function wireProgressAnimate(root) {
    $$('.el-progress[data-animate-to]', root).forEach(p => {
      if (p.__wired) return; p.__wired = true;
      const fill = $('.fill', p);
      if (!fill) return;
      const target = parseFloat(p.dataset.animateTo);
      const dur = parseInt(p.dataset.animateDuration || '1200', 10);
      fill.style.transition = `width ${dur}ms cubic-bezier(.4,0,.2,1)`;
      requestAnimationFrame(() => fill.style.width = target + '%');
    });
  }
  function wireToastDismiss(root) {
    on(root, 'click', e => {
      if (e.target.classList.contains('close') && e.target.closest('.el-toast')) {
        dismissToast(e.target.closest('.el-toast'));
      }
    });
  }
  function wireToastHooks(root) {
    $$('[data-toast]', root).forEach(btn => {
      /* per-hook guard: the shared __wired key lets earlier wires (dialog/
         drawer close) silently steal toast buttons that carry both */
      if (btn.__toastWired) return; btn.__toastWired = true;
      on(btn, 'click', () => {
        if (btn.hasAttribute('aria-disabled')) return;
        const opts = { duration: btn.dataset.toastDuration !== undefined ? (parseInt(btn.dataset.toastDuration, 10) || 0) : undefined };
        pushToast(btn.dataset.toast, btn.dataset.toastVariant || '', opts);
      });
    });
  }
  /* ── keyboard support: arrow/enter/escape handlers for each surface ── */
  function wirePaletteKeyboard(root) {
    $$('.el-palette', root).forEach(pal => {
      if (pal.__wired) return; pal.__wired = true;
      const input = $('.input', pal);
      if (!input) return;
      on(input, 'keydown', e => {
        const rows = $$('.row:not([hidden])', pal);
        if (!rows.length) return;
        const sel = rows.find(r => r.classList.contains('sel'));
        let idx = rows.indexOf(sel);
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          idx = Math.min(rows.length - 1, (idx < 0 ? 0 : idx + 1));
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          idx = Math.max(0, (idx < 0 ? 0 : idx - 1));
        } else if (e.key === 'Enter') {
          e.preventDefault();
          if (sel) fire(pal, 'el:run', { row: sel });
          return;
        } else return;
        rows.forEach(r => r.classList.remove('sel'));
        rows[idx].classList.add('sel');
        rows[idx].scrollIntoView({ block: 'nearest' });
      });
    });
  }
  function wireComboboxKeyboard(root) {
    $$('.el-combobox', root).forEach(cb => {
      if (cb.__wired) return; cb.__wired = true;
      const input = $('input', cb);
      on(input, 'keydown', e => {
        const opts = $$('.opt:not([hidden])', cb);
        if (!opts.length) return;
        const sel = opts.find(o => o.classList.contains('sel'));
        let idx = opts.indexOf(sel);
        if (e.key === 'ArrowDown') { e.preventDefault(); idx = Math.min(opts.length - 1, (idx < 0 ? 0 : idx + 1)); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); idx = Math.max(0, (idx < 0 ? 0 : idx - 1)); }
        else if (e.key === 'Enter') { e.preventDefault(); if (sel) sel.click(); return; }
        else if (e.key === 'Escape') { cb.classList.remove('open'); return; }
        else return;
        opts.forEach(o => o.classList.remove('sel'));
        opts[idx].classList.add('sel');
      });
    });
  }
  function wireTabsKeyboard(root) {
    ['.el-tabs-h', '.el-tabs-v', '.el-tabs-pill'].forEach(cls => {
      $$(cls, root).forEach(group => {
        if (group.__wired) return; group.__wired = true;
        on(group, 'keydown', e => {
          if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft' && e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
          const tabs = $$('[data-target]', group);
          const cur = tabs.findIndex(t => t.classList.contains('on'));
          let next = cur;
          if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = (cur + 1) % tabs.length;
          else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = (cur - 1 + tabs.length) % tabs.length;
          tabs[next].focus();
          tabs[next].click();
        });
      });
    });
  }
  function wireAccordionKeyboard(root) {
    $$('.el-accordion summary', root).forEach(s => {
      if (s.__wired) return; s.__wired = true;
      s.tabIndex = 0;
      on(s, 'keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          s.parentElement.open = !s.parentElement.open;
        }
      });
    });
  }
  function wireTreeListKeyboard(root) {
    $$('.el-tree-list .node', root).forEach(n => {
      if (n.__wired) return; n.__wired = true;
      const toggle = $('.toggle', n);
      if (!toggle || !toggle.textContent.trim().match(/[▾▸]/)) return;
      n.tabIndex = 0;
      on(n, 'keydown', e => {
        if (e.key === 'ArrowRight') { e.preventDefault(); n.parentElement.classList.remove('collapsed'); }
        else if (e.key === 'ArrowLeft') { e.preventDefault(); n.parentElement.classList.add('collapsed'); }
      });
    });
  }
  function wireToggleKeyboard(root) {
    ['.el-toggle', '.el-switch', '.el-check'].forEach(cls => {
      $$(cls, root).forEach(el => {
        if (el.__wired) return; el.__wired = true;
        el.tabIndex = 0;
        on(el, 'keydown', e => {
          if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            el.click();
          }
        });
      });
    });
  }
  function wireModalKeyboard(root) {
    $$('.el-modal-backdrop', root).forEach(bd => {
      if (bd.__wired) return; bd.__wired = true;
      on(bd, 'keydown', e => {
        if (e.key === 'Escape') {
          e.preventDefault();
          bd.classList.remove('open');
        }
      });
    });
  }
  function wireDrawerKeyboard(root) {
    $$('.el-drawer', root).forEach(d => {
      if (d.__wired) return; d.__wired = true;
      on(d, 'keydown', e => {
        if (e.key === 'Escape') { e.preventDefault(); closeDrawer(d); }
      });
    });
  }
  function wireSlider(root) {
    $$('.el-slider', root).forEach(s => {
      if (s.__wired) return; s.__wired = true;
      const update = () => {
        const val = s.value;
        const min = Number(s.min || 0), max = Number(s.max || 100);
        s.style.setProperty('--el-fill', (100 * (val - min) / (max - min) || 0) + '%');
        const parent = s.parentElement;
        if (parent && parent.classList.contains('el-range')) {
          const out = $('.val', parent);
          if (out) out.textContent = val;
        }
        fire(s, 'el:slide', { value: val });
      };
      on(s, 'input', update);
      update();
    });
  }
  function wireSearchBar(root) {
    $$('.el-search', root).forEach(s => {
      if (s.__wired) return; s.__wired = true;
      on(s, 'keydown', e => {
        if (e.key === 'Enter') {
          e.preventDefault();
          fire(s.closest('.el-search-bar') || s, 'el:search', { query: s.value });
        }
      });
    });
  }
  function wirePrompt(root) {
    $$('.el-prompt', root).forEach(p => {
      if (p.__wired) return; p.__wired = true;
      on(p, 'keydown', e => {
        if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
          e.preventDefault();
          fire(p, 'el:submit', { text: p.value });
          p.value = '';
        }
      });
    });
  }
  function wireClipboard(root) {
    $$('[data-copy]', root).forEach(el => {
      if (el.__wired) return; el.__wired = true;
      el.style.cursor = 'pointer';
      on(el, 'click', () => {
        const text = el.dataset.copy;
        if (navigator.clipboard) {
          navigator.clipboard.writeText(text).then(() => {
            const orig = el.textContent;
            el.textContent = 'Copied!';
            setTimeout(() => el.textContent = orig, 1000);
          });
        }
        fire(el, 'el:copy', { text });
      });
    });
  }
  function wireDatePicker(root) {
    $$('.el-datepicker', root).forEach(dp => {
      if (dp.__wired) return; dp.__wired = true;
      const owner = dp.hasAttribute('data-for') ? document.getElementById(dp.dataset.for) : $('.el-date-toggle', dp.parentElement);
      const label = $('.head .label', dp);
      const grid = $('.grid', dp);
      const prev = $('.head .prev', dp);
      const next = $('.head .next', dp);
      if (!grid || !label || !prev || !next) return;
      let view = new Date();
      view.setDate(1);
      let sel = null;
      const render = () => {
        label.textContent = view.toLocaleString('en', { month: 'short', year: 'numeric' });
        grid.innerHTML = '';
        ['S','M','T','W','T','F','S'].forEach(d => {
          const c = document.createElement('span');
          c.className = 'dow'; c.textContent = d;
          grid.appendChild(c);
        });
        const first = new Date(view.getFullYear(), view.getMonth(), 1);
        const days = new Date(view.getFullYear(), view.getMonth() + 1, 0).getDate();
        for (let i = 0; i < (first.getDay() + 6) % 7; i++) grid.appendChild(document.createElement('span'));
        const today = new Date();
        for (let d = 1; d <= days; d++) {
          const b = document.createElement('button');
          b.type = 'button'; b.className = 'day'; b.textContent = d;
          const dt = new Date(view.getFullYear(), view.getMonth(), d);
          if (dt.toDateString() === today.toDateString()) b.classList.add('today');
          if (sel && dt.toDateString() === sel.toDateString()) b.classList.add('sel');
          grid.appendChild(b);
        }
      };
      const open = (o) => {
        dp.classList.toggle('open', o);
        if (o) (grid.querySelector('.day.sel') || grid.querySelector('.day'))?.focus();
      };
      on(prev, 'click', () => { view.setMonth(view.getMonth() - 1); render(); });
      on(next, 'click', () => { view.setMonth(view.getMonth() + 1); render(); });
      on(grid, 'click', e => {
        const b = e.target.closest('.day');
        if (!b) return;
        sel = new Date(view.getFullYear(), view.getMonth(), parseInt(b.textContent, 10));
        if (owner && owner !== dp) {
          owner.dataset.value = sel.toISOString().slice(0, 10);
          if (owner.tagName === 'INPUT') owner.value = owner.dataset.value;
        }
        fire(dp, 'el:date', { date: sel });
        dp.classList.remove('open');
        render();
      });
      on(grid, 'keydown', e => {
        const days = $$('.day', grid);
        const idx = days.indexOf(document.activeElement);
        let n = idx;
        if (e.key === 'ArrowRight') n = Math.min(days.length - 1, idx + 1);
        else if (e.key === 'ArrowLeft') n = Math.max(0, idx - 1);
        else if (e.key === 'ArrowDown') n = Math.min(days.length - 1, idx + 7);
        else if (e.key === 'ArrowUp') n = Math.max(0, idx - 7);
        else if (e.key === 'Enter') { e.preventDefault(); document.activeElement.click(); return; }
        else if (e.key === 'Escape') { dp.classList.remove('open'); return; }
        else return;
        e.preventDefault();
        if (n >= 0 && days[n]) days[n].focus();
      });
      if (owner && owner !== dp) {
        on(owner, 'click', () => open(!dp.classList.contains('open')));
        on(owner, 'keydown', e => { if (e.key === 'Escape') dp.classList.remove('open'); });
      }
      on(document, 'click', e => { if (!dp.contains(e.target) && !(owner && owner.contains(e.target))) dp.classList.remove('open'); });
      render();
    });
  }
  function wireCarousel(root) {
    $$('.el-carousel', root).forEach(c => {
      if (c.__wired) return; c.__wired = true;
      const track = $('.track', c);
      const dotsBox = $('.dots', c);
      if (!track) return;
      const slides = $$('.slide', track);
      if (!slides.length) return;
      const dots = dotsBox ? slides.map((s, i) => {
        const b = document.createElement('button');
        b.type = 'button';
        b.setAttribute('aria-label', `slide ${i + 1}`);
        on(b, 'click', () => track.scrollTo({ left: s.offsetLeft - track.offsetLeft, behavior: 'smooth' }));
        dotsBox.appendChild(b);
        return b;
      }) : [];
      const cur = () => Math.round(track.scrollLeft / (slides[0].offsetWidth + parseFloat(getComputedStyle(track).columnGap || 0)) || 0);
      const render = () => { const i = cur(); dots.forEach((d, j) => d.classList.toggle('on', j === i)); fire(c, 'el:slide-change', { index: i }); };
      $$('.nav', c).forEach(btn => on(btn, 'click', () => {
        const dirv = btn.dataset.dir === 'prev' ? -1 : 1;
        const i = Math.min(slides.length - 1, Math.max(0, cur() + dirv));
        track.scrollTo({ left: slides[i].offsetLeft - track.offsetLeft, behavior: 'smooth' });
      }));
      on(track, 'scroll', () => { if (dots.length) requestAnimationFrame(render); }, { passive: true });
      if (dots.length) dots[0].classList.add('on');
    });
  }
  function wireSplitResizable(root) {
    $$('.el-split-resizable', root).forEach(sp => {
      if (sp.__wired) return; sp.__wired = true;
      const handle = $('.handle', sp);
      if (!handle) return;
      let down = false;
      const panes = $$('.pane', sp);
      on(handle, 'pointerdown', e => {
        down = true;
        sp.classList.add('dragging');
        handle.setPointerCapture(e.pointerId);
        e.preventDefault();
      });
      on(handle, 'pointermove', e => {
        if (!down) return;
        const rect = sp.getBoundingClientRect();
        const pct = ((e.clientX - rect.left) / rect.width) * 100;
        const min = parseFloat(getComputedStyle(sp).getPropertyValue('--el-split-min')) || 80;
        const maxPct = parseFloat(getComputedStyle(sp).getPropertyValue('--el-split-max')) || 90;
        const clamped = Math.max(min, Math.min(maxPct, pct));
        panes.forEach(p => p.style.width = clamped + '%');
        fire(sp, 'el:resize', { pct: clamped });
      });
      const up = () => { down = false; sp.classList.remove('dragging'); };
      on(handle, 'pointerup', up);
      on(handle, 'pointercancel', up);
    });
  }
  function wireSkeletonLoaded(root) {
    $$('.el-skeleton[data-loaded]', root).forEach(sk => {
      if (sk.__wired) return; sk.__wired = true;
      const ms = parseFloat(getComputedStyle(sk).animationDuration) * 1000 || 200;
      setTimeout(() => sk.remove(), ms + 50);
    });
  }
  // Sprite URL resolves from THIS script's location (root or demo/ both work);
  // a page that inlines the sprite as <svg id="el-icons"> skips the fetch.
  const ICON_SPRITE_URL = (typeof document.currentScript !== 'undefined' && document.currentScript && document.currentScript.src)
    ? new URL('assets/icons.svg', document.currentScript.src).href
    : 'assets/icons.svg';
  function icon(name) {
    const span = document.createElement('span');
    span.className = 'el-icon';
    const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
    use.setAttribute('href', (document.getElementById('el-icons') ? '' : ICON_SPRITE_URL) + '#el-i-' + name);
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.appendChild(use);
    span.appendChild(svg);
    return span;
  }
  function setView(fn) {
    const doc = document;
    const apply = () => { fn(); if (doc.body) doc.body.classList.add('el-view-fade'); };
    if (doc.startViewTransition && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      doc.startViewTransition(apply);
    } else {
      apply();
    }
  }
  window.Elements = {
    toast,
    toastPromise,
    icon,
    setView,
    openDialog,
    closeDialog,
    openDrawer,
    closeDrawer,
    openCommand,
    closeCommand,
    command: {
      open: (id, opener) => openCommand(id || $('.el-command'), opener),
      close: (id) => closeCommand(id || $('.el-command'))
    },
    supportsViewTransition: typeof document.startViewTransition === 'function'
  };
  window.elInit = init;
})();
