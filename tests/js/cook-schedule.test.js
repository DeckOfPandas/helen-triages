// =============================================================================
// Tests for assets/js/cook-schedule.js — the arithmetic behind the cook timer
// (food/reference/timings/), no DOM required.
//
// Run from the repo root, with the local Node runtime. No arguments — Node's
// test runner auto-discovers *.test.js files from the current directory;
// passing this file's directory explicitly does NOT work the same way:
//
//   .node-runtime/node/bin/node --test
//
// See tests/js/ingredient-search.test.js for why not the system node.
//
// WHY THIS FILE EXISTS AT ALL. This is the only place on the site where a
// wrong number ruins a meal: it decides what time a joint goes into the oven
// so that dinner is ready when you said it would be. Until cook-schedule.js
// was split out of cook-timer.js, none of it was checked by anything.
//
// Fixtures below are hand-built, not the real _data/food/cooking_methods.yml,
// so each test is self-contained and readable — what's being checked doesn't
// depend on what's currently in the data file. (tests/test_reference_data.py
// guards the data itself, including that every `relative` row can find a base.)
// The extraction was separately proved behaviour-identical by replaying the
// real data through a stub-DOM harness either side of it; these tests are the
// permanent record.
//
// THREE TESTS ONCE PINNED BEHAVIOUR THAT WAS WRONG, and none do now. They were
// written during a refactor whose whole point was to change nothing, so each
// oddity found on the way was recorded here rather than quietly corrected — a
// behaviour change hidden inside a refactor is what makes refactors dangerous.
// All three were then fixed in their own commits, and each of those tests now
// asserts the corrected behaviour and says when it changed:
//
//   hhmm    emitted a singular "min" against house style          (2026-08-15)
//   clock   said "the day before" however far back it wrapped     (2026-08-15)
//   resolve dropped flat_add_max from by_doneness' upper bound    (#245)
//
// Kept as a list rather than deleted because the PATTERN is the useful part:
// extracting a module is when you find out what it actually does, and the
// discipline is to write the oddity down, ship the refactor, then fix it
// separately. If you pin something new here, add it to this list so the next
// person can tell a deliberate record from an accident.
// =============================================================================
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const CS = require('../../assets/js/cook-schedule.js');

// --- fixtures ---------------------------------------------------------------

const RATE = {
  id: 'standard', name: 'Standard constant roast', shape: 'rate', group: 'G',
  rate_min: 40, rate_max: 50, flat_add: 20
};

const RATE_WITH_MAX = {
  id: 'lowslow', name: 'Low and slow', shape: 'rate', group: 'G',
  rate_min: 55, rate_max: 75, flat_add: 10, flat_add_max: 15
};

// Same job as RATE_WITH_MAX above, but for the by_doneness shape (GitHub
// issue #245): the two branches are meant to agree on the flat_add_max /
// flat_add / 0 fallback chain, so this fixture mirrors that one rather than
// inventing a new shape for the same check.
const BY_DONENESS_WITH_MAX = {
  id: 'haunch', name: 'Haunch, high heat then reduce', shape: 'by_doneness', group: 'G',
  by_doneness: {
    rare: { rate_min: 55, rate_max: 75, flat_add: 10, flat_add_max: 15 }
  }
};

const TOTAL = {
  id: 'spatch', name: 'Spatchcocked', shape: 'total', group: 'G',
  total_min: 40, total_max: 40
};

const STAGED = {
  id: 'simmer_roast', name: 'Simmer then roast', shape: 'staged', group: 'G',
  stages: [
    { name: 'simmer', rate_min: 45, rate_max: 45 },
    { name: 'roast', rate_min: 15, rate_max: 20 }
  ]
};

const BY_DONENESS = {
  id: 'rib', name: 'Rib roast', shape: 'by_doneness', group: 'G',
  by_doneness: {
    rare: { rate_min: 40, rate_max: 40, flat_add: 20 },
    medium: { rate_min: 50, rate_max: 50, flat_add: 25 }
  }
};

const RELATIVE_SAME = {
  id: 'glazed', name: 'Glazed', shape: 'relative', group: 'G',
  relative_to: 'Same as plain equivalent'
};

const RELATIVE_PLUS = {
  id: 'boneless', name: 'Boneless', shape: 'relative', group: 'G',
  relative_to: 'Add ~10% to time vs. same-weight bone-in'
};

const DISPUTED = {
  id: 'duck_spatch', name: 'Spatchcocked duck', shape: 'disputed', group: 'G',
  timing: '~20–60 min/kg — genuinely conflicting sources, see note'
};

const UNPARSED = {
  id: 'prose', name: 'By feel', shape: 'unparsed', group: 'G',
  timing: 'Until the juices run clear'
};

const TEMPS = {
  poultry: {
    chicken: { endpoint: '75°C' }        // no rest_min: chicken publishes none
  },
  beef: {
    tender: {
      rest_min: 15,
      doneness: {
        rare: { out_at: '48–50°C' },
        medium: { out_at: '57–60°C' }
      }
    },
    brisket: { target: '95°C', rest_min: 30 }
  }
};

// --- rounding and duration formatting ---------------------------------------
// Helen: "let's round cooking times to the nearest 5 mins to preserve sanity."
// The rounding is load-bearing, not cosmetic: the clock arithmetic rounds with
// the same function, so a printed duration can never disagree with the times
// printed either side of it.

test('round5 rounds to the nearest five minutes, both directions', () => {
  assert.strictEqual(CS.round5(97), 95);
  assert.strictEqual(CS.round5(98), 100);
  assert.strictEqual(CS.round5(0), 0);
});

test('hhmm: under an hour is minutes alone, with no "0 hrs"', () => {
  assert.strictEqual(CS.hhmm(44), '45 mins');
  assert.strictEqual(CS.hhmm(0), '0 mins');
});

test('hhmm: a whole number of hours drops the minutes, and pluralises past one', () => {
  assert.strictEqual(CS.hhmm(60), '1 hr');
  assert.strictEqual(CS.hhmm(120), '2 hrs');
  // 62 rounds down to 60 first, so it is a whole hour by the time it prints.
  assert.strictEqual(CS.hhmm(62), '1 hr');
});

test('hhmm: hours and minutes together, and the tail is always "mins"', () => {
  // The singular "min" was a real house-style violation (HANDOVER §5: a
  // numeric quantity is "mins" in both the metadata and prose registers).
  // Found by the refactor that extracted this module, fixed straight after it
  // rather than inside it -- a behaviour change hidden in a commit claiming to
  // make none is how a refactor stops being safe.
  assert.strictEqual(CS.hhmm(125), '2 hrs 5 mins');
  assert.strictEqual(CS.hhmm(85), '1 hr 25 mins');
});

test('span collapses to a single figure when the ends round together', () => {
  // 95 and 97 are one answer once you have decided five minutes is the
  // resolution; "1 hr 35 mins – 1 hr 35 mins" would be the arithmetic showing.
  assert.strictEqual(CS.span(95, 97), '1 hr 35 mins');
});

test('span prints both ends when they genuinely differ', () => {
  assert.strictEqual(CS.span(60, 120), '1 hr – 2 hrs');
});

// --- clock arithmetic -------------------------------------------------------
// Minutes-from-midnight in, "HH:MM" out. This is where time bugs live.

test('clock zero-pads both halves', () => {
  assert.strictEqual(CS.clock(0), '00:00');
  assert.strictEqual(CS.clock(9 * 60 + 5), '09:05');
  assert.strictEqual(CS.clock(23 * 60 + 59), '23:59');
});

test('clock wraps backwards over midnight rather than printing a negative time', () => {
  // A 6 kg turkey for a 1pm lunch genuinely does start the night before, and
  // "-45:00" instead of "22:15 (the day before)" is a bug you would only
  // notice at Christmas.
  assert.strictEqual(CS.clock(-110), '22:10 (the day before)');
  assert.strictEqual(CS.clock(-1), '23:59 (the day before)');
});

test('clock COUNTS the days it wraps back, rather than saying "the day before" once', () => {
  // This was a real bug, found by the refactor that extracted this module and
  // fixed straight after it. The loop assigned the label on every pass instead
  // of counting, so anything more than 24 hours back was under-reported by a
  // whole day -- and the page's own inputs reach it: 13.2 kg of brisket at the
  // low-and-slow rate is a 29-43½ hour cook, which crosses midnight twice.
  assert.strictEqual(CS.clock(-1500), '23:00 (2 days before)');
  assert.strictEqual(CS.clock(-2880), '00:00 (2 days before)');
  assert.strictEqual(CS.clock(-2881), '23:59 (3 days before)');
  // The one-day case keeps its English rather than becoming "(1 days before)".
  assert.strictEqual(CS.clock(-1440), '00:00 (the day before)');
});

test('parseClock reads what an <input type=time> gives, and rejects the rest', () => {
  assert.strictEqual(CS.parseClock('14:00'), 840);
  assert.strictEqual(CS.parseClock('00:30'), 30);
  assert.strictEqual(CS.parseClock('9:05'), 545);   // single-digit hour
  assert.strictEqual(CS.parseClock(' 14:00 '), 840); // trimmed
});

test('parseClock returns null — not 0, not NaN — when there is no time at all', () => {
  // The empty case is the DEFAULT state of the page: the serving time is
  // optional on purpose, and null is what tells the renderer to leave clock
  // times off entirely. A 0 here would silently schedule everything for
  // midnight.
  assert.strictEqual(CS.parseClock(''), null);
  assert.strictEqual(CS.parseClock(null), null);
  assert.strictEqual(CS.parseClock(undefined), null);
  assert.strictEqual(CS.parseClock('nonsense'), null);
  assert.strictEqual(CS.parseClock('2pm'), null);
});

// --- resolve: one branch per shape ------------------------------------------
// _data/food/cooking_methods.yml's header documents seven shape values. Each
// gets its own test, INCLUDING the two that refuse: a calculator that averaged
// a disputed row into a confident serving time would be worse than one that
// declined, so a test proving a refusal is still a refusal is worth as much as
// one proving a number.

test('rate: minutes per kg plus the flat addition', () => {
  const r = CS.resolve(RATE, 2, 'rare', [RATE]);
  assert.strictEqual(r.ok, true);
  assert.strictEqual(r.lo, 40 * 2 + 20);
  assert.strictEqual(r.hi, 50 * 2 + 20);
});

test('rate: flat_add_max applies to the upper end when the data states one', () => {
  const r = CS.resolve(RATE_WITH_MAX, 2, 'rare', [RATE_WITH_MAX]);
  assert.strictEqual(r.lo, 55 * 2 + 10);
  assert.strictEqual(r.hi, 75 * 2 + 15);
});

test('rate: a missing flat_add is nothing, not NaN', () => {
  const bare = { shape: 'rate', rate_min: 30, rate_max: 30 };
  const r = CS.resolve(bare, 1.5, 'rare', [bare]);
  assert.strictEqual(r.lo, 45);
  assert.strictEqual(r.hi, 45);
});

test('total: a fixed time that ignores the weight box, and says so', () => {
  const light = CS.resolve(TOTAL, 0.4, 'rare', [TOTAL]);
  const heavy = CS.resolve(TOTAL, 9, 'rare', [TOTAL]);
  assert.deepStrictEqual([light.lo, light.hi], [40, 40]);
  assert.deepStrictEqual([heavy.lo, heavy.hi], [40, 40]);
  // The aside is the only thing stopping this reading as a bug on screen.
  assert.match(light.aside, /doesn't change this one/);
});

test('staged: two rates in sequence, summed AND reported stage by stage', () => {
  const r = CS.resolve(STAGED, 2, 'rare', [STAGED]);
  assert.strictEqual(r.lo, 45 * 2 + 15 * 2);   // 120
  assert.strictEqual(r.hi, 45 * 2 + 20 * 2);   // 130
  assert.deepStrictEqual(r.stages, [
    { name: 'simmer', lo: 90, hi: 90 },
    { name: 'roast', lo: 30, hi: 40 }
  ]);
});

test('by_doneness: the rate for the level you asked for', () => {
  const r = CS.resolve(BY_DONENESS, 2, 'medium', [BY_DONENESS]);
  assert.strictEqual(r.lo, 50 * 2 + 25);
  assert.strictEqual(r.hi, 50 * 2 + 25);
  assert.match(r.aside, /showing medium/);
});

test('by_doneness: an unknown level falls back to rare rather than producing NaN', () => {
  // The page only ever asks for "rare" today, but the fallback is what keeps a
  // future doneness control from silently returning NaN minutes.
  const r = CS.resolve(BY_DONENESS, 2, 'blue', [BY_DONENESS]);
  assert.strictEqual(r.lo, 40 * 2 + 20);
});

test('by_doneness: flat_add_max applies to the upper end when the data states one', () => {
  // GitHub issue #245. This used to add flat_add to BOTH ends and never look
  // at flat_add_max, so an asymmetric upper bound was silently dropped — the
  // same fixture as RATE_WITH_MAX above, on the by_doneness shape, because
  // the two branches are meant to agree and this is the case that would have
  // caught the divergence. Not theoretical: venison's haunch
  // (haunch_high_heat_start_then_reduce in _data/food/cooking_methods.yml,
  // mirrored by BY_DONENESS_WITH_MAX) is a live by_doneness row with
  // flat_add on both its levels, and is the row most likely to gain an
  // asymmetric flat_add_max next.
  const r = CS.resolve(BY_DONENESS_WITH_MAX, 1, 'rare', [BY_DONENESS_WITH_MAX]);
  assert.strictEqual(r.lo, 55 + 10);
  assert.strictEqual(r.hi, 75 + 15);
});

test('by_doneness: underscores in the level become spaces in the aside', () => {
  const wd = {
    shape: 'by_doneness',
    by_doneness: { well_done: { rate_min: 60, rate_max: 60 }, rare: { rate_min: 40, rate_max: 40 } }
  };
  assert.match(CS.resolve(wd, 1, 'well_done', [wd]).aside, /showing well done\./);
});

// --- relative: borrowing another row's timing --------------------------------

test('baseFor picks the first plain `rate` row in the same group', () => {
  const all = [DISPUTED, RATE, RATE_WITH_MAX, RELATIVE_SAME];
  assert.strictEqual(CS.baseFor(RELATIVE_SAME, all), RATE);
});

test('baseFor ignores rate rows belonging to a different group', () => {
  const otherGroup = Object.assign({}, RATE, { group: 'OTHER' });
  assert.strictEqual(CS.baseFor(RELATIVE_SAME, [otherGroup]), null);
});

test('relative: "same as plain equivalent" borrows the base timing unchanged', () => {
  const all = [RATE, RELATIVE_SAME];
  const r = CS.resolve(RELATIVE_SAME, 2, 'rare', all);
  const base = CS.resolve(RATE, 2, 'rare', all);
  assert.strictEqual(r.ok, true);
  assert.strictEqual(r.lo, base.lo);
  assert.strictEqual(r.hi, base.hi);
  // The row it borrowed from is NAMED: a number you can't trace is a number
  // you can't check.
  assert.match(r.aside, /Standard constant roast/);
  assert.doesNotMatch(r.aside, /plus/);
});

test('relative: "add ~10%" multiplies the base, and says by how much', () => {
  const all = [RATE, RELATIVE_PLUS];
  const r = CS.resolve(RELATIVE_PLUS, 2, 'rare', all);
  assert.ok(Math.abs(r.lo - 100 * 1.1) < 1e-9);
  assert.ok(Math.abs(r.hi - 120 * 1.1) < 1e-9);
  assert.match(r.aside, /plus 10%/);
});

test('relative: no base row in the group means it declines rather than guesses', () => {
  // test_relative_methods_can_find_a_base in tests/test_reference_data.py stops
  // the real data ever reaching this branch; this is the JS side holding the
  // line anyway.
  const r = CS.resolve(RELATIVE_SAME, 2, 'rare', [RELATIVE_SAME]);
  assert.strictEqual(r.ok, false);
  assert.strictEqual(r.why, RELATIVE_SAME.relative_to);
});

// --- the two that refuse -----------------------------------------------------

test('disputed: declines, and hands back the conflicting range and the reason', () => {
  const r = CS.resolve(DISPUTED, 2, 'rare', [DISPUTED]);
  assert.strictEqual(r.ok, false);
  assert.strictEqual(r.lo, undefined);
  assert.strictEqual(r.hi, undefined);
  assert.match(r.why, /Sources genuinely disagree/);
  assert.match(r.why, /20–60 min\/kg/);      // the row's own wording, quoted
  assert.match(r.why, /Use a thermometer/);
});

test('unparsed: declines, quoting the original prose rather than parsing it', () => {
  const r = CS.resolve(UNPARSED, 2, 'rare', [UNPARSED]);
  assert.strictEqual(r.ok, false);
  assert.match(r.why, /No formula in the data/);
  assert.match(r.why, /Until the juices run clear/);
});

test('an unrecognised shape declines too — it never falls through to a number', () => {
  // The default branch is the one that catches a shape nobody has written a
  // rule for yet. Silence would be the dangerous answer here.
  const r = CS.resolve({ shape: 'something_new', timing: 'who knows' }, 2, 'rare', []);
  assert.strictEqual(r.ok, false);
});

// --- ordering ---------------------------------------------------------------

test('orderMethods sorts by the lower bound, shortest first', () => {
  const all = [STAGED, TOTAL, RATE];
  const names = CS.orderMethods(all, 2, 'rare').map((m) => m.name);
  assert.deepStrictEqual(names, ['Spatchcocked', 'Standard constant roast', 'Simmer then roast']);
});

test('orderMethods sinks the rows that decline to the bottom, alphabetically', () => {
  // An unanswerable row has no lower bound to rank on, and at the top of a
  // table of times it would read as the fastest.
  const all = [UNPARSED, DISPUTED, RATE];
  const names = CS.orderMethods(all, 2, 'rare').map((m) => m.name);
  assert.deepStrictEqual(names, ['Standard constant roast', 'By feel', 'Spatchcocked duck']);
});

test('orderMethods returns a new array and leaves the caller\'s alone', () => {
  const all = [STAGED, TOTAL, RATE];
  const copy = all.slice();
  CS.orderMethods(all, 2, 'rare');
  assert.deepStrictEqual(all, copy);
});

// --- working backwards from the plate ----------------------------------------
// The whole point of the page. Everything below is minutes from midnight;
// negatives are the previous day and are clock()'s problem, not this function's.

test('scheduleBack: rest comes off the serving time, cooking off that', () => {
  const s = CS.scheduleBack(100, 130, CS.parseClock('14:00'), 20);
  assert.strictEqual(CS.clock(s.outAt), '13:40');
  assert.strictEqual(CS.clock(s.inAt), '11:30');
  assert.strictEqual(CS.clock(s.restUntil), '14:00');
});

test('scheduleBack: the LONGER estimate drives the start time', () => {
  // Being ready early and holding is recoverable; being late is not. So `inAt`
  // is the serving time minus the longest cook, and the quicker end is the
  // afterthought in brackets, not the headline.
  const s = CS.scheduleBack(100, 130, 840, 20);
  assert.ok(s.inAt < s.inAtQuicker);
  assert.strictEqual(CS.clock(s.inAtQuicker), '12:00');
  assert.strictEqual(s.hasRange, true);
});

test('scheduleBack: no range to show when the two ends round together', () => {
  // Same five-minute rounding as the printed duration, so a card can never say
  // "1 hr 35 mins" above two start times that differ by two minutes.
  const s = CS.scheduleBack(95, 97, 840, 0);
  assert.strictEqual(s.hasRange, false);
  assert.strictEqual(s.inAt, s.inAtQuicker);
});

test('scheduleBack: zero or missing rest leaves the out time on the plate', () => {
  assert.strictEqual(CS.scheduleBack(60, 60, 840, 0).outAt, 840);
  assert.strictEqual(CS.scheduleBack(60, 60, 840).outAt, 840);
});

test('scheduleBack: eating at 00:30 means going in the PREVIOUS DAY', () => {
  // The midnight wrap, explicitly. 00:30 minus a 20 minute rest minus a two
  // hour cook is 22:10 yesterday, not a negative number and not 22:10 today.
  const s = CS.scheduleBack(120, 120, CS.parseClock('00:30'), 20);
  assert.strictEqual(s.inAt, -110);
  assert.strictEqual(CS.clock(s.inAt), '22:10 (the day before)');
  assert.strictEqual(CS.clock(s.outAt), '00:10');
  assert.strictEqual(CS.clock(s.restUntil), '00:30');
});

test('scheduleBack: a cook longer than a day still returns a real number of minutes', () => {
  // 43 hours of brisket for a 2pm Sunday lunch starts on Friday evening, and
  // this asserts the ARITHMETIC only: -1720 minutes. Turning that into words
  // is clock()'s job, and it used to under-report anything past 24 hours as
  // "the day before" — fixed, and covered by clock()'s own day-counting test
  // above rather than restated here.
  const s = CS.scheduleBack(43 * 60, 43 * 60, 840, 20);
  assert.strictEqual(s.inAt, 820 - 43 * 60);
});

test('scheduleBack never consults the clock, so "in the past" is not its question', () => {
  // Nothing here knows what time it is now — deliberately. The same inputs give
  // the same answer whenever they are asked, which is the only reason any of
  // this is testable. A start time that has already gone is a comparison the
  // page would have to make against a `now` it injects; today it makes none,
  // and simply prints a time that may already have passed.
  const a = CS.scheduleBack(120, 120, 840, 20);
  const b = CS.scheduleBack(120, 120, 840, 20);
  assert.deepStrictEqual(a, b);
});

// --- the temperature and rest lookups ----------------------------------------
// `temps` is injected, not required: the page serialises internal_temperatures
// .yml into the document and this module has no business knowing that.

test('finishingTemp follows a dotted ref to an endpoint', () => {
  assert.strictEqual(CS.finishingTemp(TEMPS, 'poultry.chicken'), '75°C');
});

test('finishingTemp falls back to a target when there is no endpoint', () => {
  assert.strictEqual(CS.finishingTemp(TEMPS, 'beef.brisket'), '95°C');
});

test('finishingTemp on a doneness table shows the FIRST level, and names it', () => {
  // The page can only show one doneness at a time; the card links out to the
  // rest of the spectrum rather than pretending this is the only answer.
  assert.strictEqual(CS.finishingTemp(TEMPS, 'beef.tender'), '48–50°C (rare)');
});

test('finishingTemp returns null rather than throwing on a missing or bad ref', () => {
  assert.strictEqual(CS.finishingTemp(TEMPS, null), null);
  assert.strictEqual(CS.finishingTemp(TEMPS, ''), null);
  assert.strictEqual(CS.finishingTemp(TEMPS, 'beef.nosuchcut'), null);
  assert.strictEqual(CS.finishingTemp(TEMPS, 'no.such.path.at.all'), null);
});

test('statedRest reads a published rest time, and null when none is published', () => {
  assert.strictEqual(CS.statedRest(TEMPS, 'beef.tender'), 15);
  assert.strictEqual(CS.statedRest(TEMPS, 'poultry.chicken'), null);
  assert.strictEqual(CS.statedRest(TEMPS, 'beef.nosuchcut'), null);
});

test('restFor marks a cited figure as stated and a fallback as not', () => {
  // The distinction is the whole point: chicken, turkey, duck and ham publish
  // no rest time, and the page must not present a working default with the same
  // confidence as a figure someone wrote down. The fallback is injected so that
  // policy stays with the page.
  assert.deepStrictEqual(CS.restFor(TEMPS, 'beef.tender', 20), { mins: 15, stated: true });
  assert.deepStrictEqual(CS.restFor(TEMPS, 'poultry.chicken', 20), { mins: 20, stated: false });
  assert.deepStrictEqual(CS.restFor(TEMPS, null, 20), { mins: 20, stated: false });
});

test('restFor treats a stated rest of zero as stated, not as missing', () => {
  const temps = { fish: { fillet: { rest_min: 0 } } };
  assert.deepStrictEqual(CS.restFor(temps, 'fish.fillet', 20), { mins: 0, stated: true });
});

// --- the protein dropdown ----------------------------------------------------

test('proteinOrder sorts by the label you read, not by the data file\'s key order', () => {
  const methods = {
    turkey: { label: 'Turkey' },
    beef: { label: 'Beef' },
    ham: { label: 'Ham (gammon)' }
  };
  assert.deepStrictEqual(CS.proteinOrder(methods), ['beef', 'ham', 'turkey']);
});

// =============================================================================
// EVERY DONENESS LEVEL IS REACHABLE — GitHub issue #246
// =============================================================================
//
// The timings page hard-wired `doneness` to "rare" and shipped no control, so
// the medium rates in cooking_methods.yml could not be displayed by anything:
// real, sourced data that no reader could reach. resolve() now returns every
// level alongside the requested one, and the page renders them all.
//
// These assert the WHOLE SET, not just that medium exists. A test that only
// checked `levels.length > 0` would pass on a resolve() that returned the
// requested level twice.

test('by_doneness: resolve returns every level, not only the one asked for', () => {
  const r = CS.resolve(BY_DONENESS, 2, 'rare', [BY_DONENESS]);
  assert.deepStrictEqual(
    r.levels.map((l) => l.name),
    Object.keys(BY_DONENESS.by_doneness),
    'levels must name every doneness the data declares, in the data order'
  );
});

test('by_doneness: each level carries its OWN figures, not the requested one repeated', () => {
  const r = CS.resolve(BY_DONENESS, 2, 'rare', [BY_DONENESS]);
  const seen = new Set(r.levels.map((l) => l.lo + '-' + l.hi));
  assert.strictEqual(
    seen.size, r.levels.length,
    'two levels resolved to identical figures. The fixture states different ' +
    'rates per level, so this means every level was computed from the ' +
    'requested one -- the exact bug that made medium unreachable.'
  );
  r.levels.forEach((lv) => {
    const d = BY_DONENESS.by_doneness[lv.name];
    assert.strictEqual(lv.lo, d.rate_min * 2 + (d.flat_add || 0));
    assert.strictEqual(lv.hi, d.rate_max * 2 + (d.flat_add_max || d.flat_add || 0));
  });
});

test('by_doneness: flat_add_max is honoured per level, not just on the asked-for one', () => {
  // The #245 bug (an asymmetric upper bound silently dropped) would otherwise
  // be free to reappear inside `levels` while resolve's own lo/hi stayed right.
  const r = CS.resolve(BY_DONENESS_WITH_MAX, 1, 'rare', [BY_DONENESS_WITH_MAX]);
  r.levels.forEach((lv) => {
    const d = BY_DONENESS_WITH_MAX.by_doneness[lv.name];
    if (d.flat_add_max) {
      assert.strictEqual(lv.hi, d.rate_max * 1 + d.flat_add_max);
      assert.notStrictEqual(lv.hi, d.rate_max * 1 + (d.flat_add || 0));
    }
  });
});

test('a shape without doneness has no levels, so the page renders one figure', () => {
  const r = CS.resolve(RATE_WITH_MAX, 2, 'rare', [RATE_WITH_MAX]);
  assert.strictEqual(r.levels, undefined);
});
