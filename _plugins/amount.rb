# =============================================================================
# ONE READING OF AN `amount:` STRING, FOR EVERY RUBY GENERATOR -- #1199.
# =============================================================================
# `"22.5 ml"` is a number and a unit. Until 2026-10-04 that sentence was written
# out three times, as the same regex retyped in cocktail_costs.rb,
# cocktail_units.rb (twice) and cocktail_card_ingredients.rb, and exercised
# only through rendered-page assertions that each cost a Jekyll build. A bug
# in one copy would have been a wrong price, a wrong unit count or a wrong
# card order -- and with three copies, not necessarily all three at once.
#
# WHAT IS SHARED IS THE SPLIT, NOT THE VERDICT. Each caller still decides for
# itself what an amount is WORTH -- costing returns nil for an excluded unit,
# the card sort returns 0, the volume sum tells a declared non-volume from an
# unreadable one -- because those are three different questions (their own
# headers say why). What they must never disagree about is where the number
# ends and what the unit is called.
#
# THE GRAMMAR, which is the cocktail collections' and deliberately narrower
# than assets/js/shopping-list.js's `parseAmount` (that one also reads food:
# vulgar fractions, ranges, "2 x 400 g tins"):
#
#   "22.5 ml"       -> [22.5, "ml"]
#   "1 heaping oz"  -> [1.0, "oz"]        an ignored word is dropped
#   "2 dashes"      -> [2.0, "dashes"]    the unit AS WRITTEN; nothing is folded
#   "(top)"         -> [nil, "(top)"]     a bare unit with no figure before it
#   "15"            -> [nil, "15"]        a bare number is NOT a quantity here:
#                                         it has no unit, and
#                                         test_every_amount_is_readable_as_a_quantity
#                                         is what keeps one out of the data
#
# tests/fixtures/amounts.json pins it, row by row, against every distinct
# amount in the published collection; tests/test_amount_parser.py runs this
# file over it through scripts/parse_amounts.rb, and tests/js/ reads the same
# rows, so the two languages cannot drift apart on a number.
#
# A PLAIN MODULE, NOT A GENERATOR, required by the three files that use it.
# Jekyll also loads everything in _plugins/ by itself, which is harmless: this
# defines a module and does nothing.
# =============================================================================

module HelenTriages
  module Amount
    NUMBER_THEN_UNIT = /\A([\d.]+)\s+(.*)\z/

    # (number, unit) for an amount string. `ignored` is
    # ingredients.yml's `measures.ignored_words` -- "heaping", "scant" -- which
    # qualify a unit without changing what it is.
    def self.parse(amount, ignored = [])
      a = amount.to_s.strip
      m = NUMBER_THEN_UNIT.match(a)
      return [nil, a] unless m
      unit = m[2].strip
      Array(ignored).each { |w| unit = unit.sub(/\A#{Regexp.escape(w)}\s+/, "") }
      [m[1].to_f, unit]
    end

    # Millilitres, or nil when the amount has no figure or its unit is not a
    # volume. `per_ml` is ingredients.yml's `measures.per_ml`.
    def self.millilitres(amount, per_ml, ignored = [])
      number, unit = parse(amount, ignored)
      return nil unless number && per_ml.key?(unit)
      number * per_ml[unit].to_f
    end
  end
end
