'use strict';
/* tests/dom_harness.cjs — minimal DOM stub so elements.js can boot under node.
 *
 * The suite is Python-based, but the interactive elements are browser code.
 * This stub implements just enough DOM (classes, dataset, events, a class
 * selector engine) for init() to wire a real fixture tree, so the tests
 * assert behavior, not source text. Scenarios are named on argv and each
 * prints PASS or FAIL; the process exits 1 on any failure.
 */

const EVERY = [];
const HTML_WRITES = [];

class FakeEl {
  constructor(tag, cls) {
    this.tagName = String(tag).toUpperCase();
    this.classes = new Set(cls ? cls.split(/\s+/).filter(Boolean) : []);
    this.children = [];
    this.parent = null;
    this.dataset = {};
    this.attrs = new Set();
    this.style = {};
    this.value = '';
    this.id = '';
    this._text = '';
    this.listeners = {};
    EVERY.push(this);
  }
  get className() { return [...this.classes].join(' '); }
  set className(v) { this.classes = new Set(v.split(/\s+/).filter(Boolean)); }
  get classList() {
    const self = this;
    return {
      add: (...cs) => cs.forEach(c => self.classes.add(c)),
      remove: (...cs) => cs.forEach(c => self.classes.delete(c)),
      toggle: (c, force) => {
        const want = force === undefined ? !self.classes.has(c) : !!force;
        if (want) self.classes.add(c); else self.classes.delete(c);
        return want;
      },
      contains: c => self.classes.has(c)
    };
  }
  get parentElement() { return this.parent; }
  get textContent() {
    if (this.children.length) return this.children.map(c => c.textContent).join('');
    return this._text;
  }
  set textContent(v) {
    this._text = String(v);
    this.children = [];
  }
  get innerHTML() { return ''; }
  set innerHTML(v) {
    HTML_WRITES.push({ el: this, value: v });
    this.children = [];
  }
  hasAttribute(a) { return this.attrs.has(a); }
  appendChild(c) { c.parent = this; this.children.push(c); return c; }
  addEventListener(type, fn) { (this.listeners[type] = this.listeners[type] || []).push(fn); }
  dispatchEvent(ev) {
    (this.listeners[ev.type] || []).slice().forEach(fn => fn.call(this, ev));
    return true;
  }
  click() {
    const self = this;
    // real clicks bubble: delegated handlers (e.g. the datepicker grid) live
    // on an ancestor of the clicked day button
    for (let el = this; el; el = el.parent) {
      el.dispatchEvent({ type: 'click', target: this, currentTarget: el,
        preventDefault() {}, closest: sel => self.closest(sel) });
    }
  }
  focus() {}
  closest(sel) {
    let el = this;
    while (el) {
      if (matchSegment(el, sel)) return el;
      el = el.parent;
    }
    return null;
  }
  descendants() {
    const out = [];
    const walk = n => n.children.forEach(c => { out.push(c); walk(c); });
    walk(this);
    return out;
  }
  querySelectorAll(sel) {
    const tokens = sel.trim().split(/\s+/);
    return [this, ...this.descendants()].filter(el => matchChain(el, tokens));
  }
  querySelector(sel) { return this.querySelectorAll(sel)[0] || null; }
}

function matchSegment(el, seg) {
  return seg.startsWith('.') && el.classes.has(seg.slice(1));
}

function matchChain(el, tokens) {
  if (!matchSegment(el, tokens[tokens.length - 1])) return false;
  if (tokens.length === 1) return true;
  for (let a = el.parent; a; a = a.parent) {
    if (matchChain(a, tokens.slice(0, -1))) return true;
  }
  return false;
}

// ── boot: globals + fixture tree, then elements.js auto-inits on it ─────────
global.window = globalThis;
const doc = new FakeEl('#document');
global.document = {
  readyState: 'complete',
  addEventListener() {},
  createElement: tag => new FakeEl(tag),
  createElementNS: (ns, tag) => new FakeEl(tag),
  getElementById: id => EVERY.find(el => el.id === id) || null,
  querySelectorAll: sel => {
    const tokens = sel.trim().split(/\s+/);
    return EVERY.filter(el => matchChain(el, tokens));
  },
  querySelector: sel => global.document.querySelectorAll(sel)[0] || null
};

function buildDatepicker() {
  const dp = new FakeEl('DIV', 'el-datepicker');
  const head = new FakeEl('DIV', 'head');
  const prev = new FakeEl('BUTTON', 'prev');
  const label = new FakeEl('SPAN', 'label');
  const next = new FakeEl('BUTTON', 'next');
  [prev, label, next].forEach(c => head.appendChild(c));
  const grid = new FakeEl('DIV', 'grid');
  dp.appendChild(head);
  dp.appendChild(grid);
  // owner INPUT, resolved through data-for like the demo's toggle variant
  const owner = new FakeEl('INPUT');
  owner.id = 'date-out';
  dp.attrs.add('data-for');
  dp.dataset.for = 'date-out';
  return { dp, prev, next, label, grid, owner };
}

function buildCodeBlock() {
  const cb = new FakeEl('PRE', 'el-code-block');
  cb.textContent = '<img src=x onerror=alert(1)>';
  return cb;
}

const DP = buildDatepicker();
const CB = buildCodeBlock();
let dateEvents = [];
DP.dp.addEventListener('el:date', ev => dateEvents.push(ev.detail));

require('../elements.js');

// ── helpers ─────────────────────────────────────────────────────────────────
const failures = [];
function assert(cond, msg) {
  if (!cond) failures.push(msg);
  return cond;
}

function navigate(target) {
  for (let i = 0; i < 24; i++) {
    if (DP.label.textContent === target) return true;
    DP.prev.click();
  }
  for (let i = 0; i < 24; i++) {
    if (DP.label.textContent === target) return true;
    DP.next.click();
  }
  return false;
}

function firstDayIndex() {
  const i = DP.grid.children.findIndex(c => c.classes.has('day'));
  return i;
}

// ── scenarios ───────────────────────────────────────────────────────────────
const scenarios = {

  // HIGH: the header row is Sunday-first, so the leading-blank count must be
  // first.getDay(), not the Monday-first (getDay() + 6) % 7.
  'datepicker-alignment': () => {
    assert(navigate('Nov 2026'), 'navigate to Nov 2026');
    // Nov 1 2026 is a Sunday: zero blanks, day 1 sits directly under the
    // first 'S' header at grid index 7 (indices 0-6 are the dow row)
    assert(DP.grid.children[0].textContent === 'S', "first header is 'S'");
    assert(firstDayIndex() === 7,
      `Sunday-start month should have 0 blanks (day 1 at index 7), got ${firstDayIndex()}`);
    assert(DP.grid.children[7].textContent === '1', 'day 1 lands at index 7 in Nov 2026');
    // Dec 1 2026 is a Tuesday (getDay()=2): two blanks, day 1 at index 9
    DP.next.click();
    assert(DP.label.textContent === 'Dec 2026', 'navigate to Dec 2026');
    assert(firstDayIndex() === 9,
      `Tuesday-start month should have 2 blanks (day 1 at index 9), got ${firstDayIndex()}`);
  },

  // HIGH: the stored value is the picked LOCAL calendar date; toISOString()
  // moved it a day back for every UTC+ zone.
  'datepicker-iso': () => {
    assert(navigate('Nov 2026'), 'navigate to Nov 2026');
    const day1 = DP.grid.children.find(c => c.classes.has('day') && c.textContent === '1');
    assert(day1, 'day 1 button rendered');
    day1.click();
    assert(DP.owner.dataset.value === '2026-11-01',
      `picked value should be 2026-11-01 under TZ=Europe/Berlin, got ${DP.owner.dataset.value}`);
    assert(DP.owner.value === '2026-11-01',
      `INPUT value should be 2026-11-01, got ${DP.owner.value}`);
    assert(dateEvents.length === 1 && dateEvents[0].date.getFullYear() === 2026
      && dateEvents[0].date.getMonth() === 10 && dateEvents[0].date.getDate() === 1,
      'el:date fired with the picked local date');
  },

  // MEDIUM (security): a code block shows escaped markup — rebuilding the
  // highlighted lines must never re-parse that text as live HTML.
  'codeblock-no-live-markup': () => {
    const rows = CB.children.filter(c => c.tagName === 'DIV');
    assert(rows.length === 1, `one source line expected, got ${rows.length}`);
    const code = rows[0] && rows[0].children[1];
    assert(code && code.textContent === '<img src=x onerror=alert(1)>',
      'escaped markup is preserved verbatim as text');
    const live = HTML_WRITES.filter(w => w.value.includes('<'));
    assert(live.length === 0,
      `no innerHTML write may carry markup, saw ${live.length}`);
  }
};

let ran = 0;
process.argv.slice(2).forEach(name => {
  const fn = scenarios[name];
  if (!fn) {
    console.error(`unknown scenario: ${name}`);
    process.exitCode = 1;
    return;
  }
  ran++;
  fn();
  console.log(`${failures.length ? 'FAIL' : 'PASS'} ${name}`);
  failures.forEach(f => console.error(`  - ${f}`));
});
if (!ran || failures.length) process.exitCode = 1;
