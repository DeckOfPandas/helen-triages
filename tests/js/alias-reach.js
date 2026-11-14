// Which alias keys in _data/food/ingredient_words.yml no ingredient string can
// reach (#1480). Run by tests/test_food_alias_reach.py, not by `node --test`.
//
// Argument: a JSON file holding {vocabulary, strings}. Every string goes
// through ingredient-search.js's own buildMasterList with the aliases taken
// out, which leaves exactly what applyAlias would be handed. A key none of
// those equals (folded, lowercase) can never fire. Prints {dead, entries}.
'use strict';

const fs = require('fs');
const path = require('path');
const search = require(path.join(__dirname, '..', '..', 'assets', 'js', 'ingredient-search.js'));

const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const vocabulary = Object.assign({}, input.vocabulary, { aliases: {} });
const entries = search.create(vocabulary).buildMasterList(input.strings);
const key = (s) => search.fold(String(s).toLowerCase());
const reached = new Set(entries.map(key));
const dead = Object.keys(input.vocabulary.aliases || {})
  .filter((alias) => !reached.has(key(alias)))
  .sort();

process.stdout.write(JSON.stringify({ dead: dead, entries: entries.length }));
