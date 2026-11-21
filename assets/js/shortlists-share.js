// shortlists-share.js: lists as links and links as lists (#1521), as
// HTF.listsShare. MANUAL §8.9. No DOM and no storage: loaded as a <script>,
// and by require() in the tests.
//
// A list's link is the shortlists page with `?shortlist=slug,slug`, then
// `&portions=4,1.5` (what each is stored at, in the same order) and
// `&list=Name`. Slugs, not keys: a slug survives a folder move. A block is
// one "Name: link" line per list, in order. Reading is lenient: a link with
// no portions takes each recipe's default, one with no name is unnamed, and
// a line with no link in it is passed over.

(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = factory();
  } else {
    root.HTF = root.HTF || {};
    root.HTF.listsShare = factory();
  }
})(typeof window !== 'undefined' ? window : this, function () {
  'use strict';

  var SLUG = /^[a-z0-9][a-z0-9-]*$/;

  function slugOf(url) {
    return String(url).replace(/[?#].*$/, '').replace(/\/+$/, '').split('/').pop();
  }

  function number(n) {
    return String(Math.round(Number(n) * 100) / 100);
  }

  // `base` is the shortlists page's own address, with no query.
  function link(base, list) {
    var slugs = list.items.map(function (item) { return slugOf(item.recipe); });
    var portions = list.items.map(function (item) { return number(item.portions); });
    return base + '?shortlist=' + slugs.join(',') +
      (portions.length ? '&portions=' + portions.join(',') : '') +
      '&list=' + encodeURIComponent(list.name);
  }

  function block(base, lists) {
    return lists.map(function (list) { return list.name + ': ' + link(base, list); }).join('\n');
  }

  function decode(text) {
    try {
      return decodeURIComponent(String(text).replace(/\+/g, ' '));
    } catch (e) {
      return String(text);
    }
  }

  function params(query) {
    var out = {};
    String(query).replace(/^[^?]*\?/, '').replace(/#.*$/, '').split('&').forEach(function (pair) {
      var eq = pair.indexOf('=');
      if (eq === -1) return;
      out[decode(pair.slice(0, eq))] = decode(pair.slice(eq + 1));
    });
    return out;
  }

  /* A query string or link as { name, items: [{ slug, portions }] }, or
     null when it carries no `shortlist`. `portions` is null where the link
     gives none. */
  function read(query) {
    var p = params(query);
    if (!Object.prototype.hasOwnProperty.call(p, 'shortlist')) return null;
    var portions = (p.portions || '').split(',');
    var items = [];
    p.shortlist.split(',').forEach(function (raw, i) {
      var slug = raw.trim().toLowerCase();
      if (!SLUG.test(slug) || items.some(function (item) { return item.slug === slug; })) return;
      var n = Number(portions[i]);
      items.push({ slug: slug, portions: portions[i] && isFinite(n) && n > 0 ? n : null });
    });
    return { name: (p.list || '').replace(/\s+/g, ' ').trim(), items: items };
  }

  // Every list a pasted block holds, in its order. A line's own "Name:"
  // names a link that carries no `list`.
  function readBlock(text) {
    var out = [];
    String(text || '').split(/\r?\n/).forEach(function (line) {
      var found = /\S*[?&]shortlist=\S*/.exec(line);
      if (!found) return;
      var list = read(found[0]);
      if (!list) return;
      if (!list.name) list.name = line.slice(0, found.index).replace(/[\s:]+$/, '').trim();
      out.push(list);
    });
    return out;
  }

  return { slugOf: slugOf, link: link, block: block, read: read, readBlock: readBlock };
});
