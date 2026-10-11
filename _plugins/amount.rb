# One reading of an `amount:` string for every Ruby generator (#1199). What
# is shared is the split into number and unit; each caller still decides what
# an amount is worth. The grammar is the cocktail collections', narrower than
# the JavaScript `parseAmount` that also reads food amounts:
#
#   "22.5 ml"       -> [22.5, "ml"]
#   "1 heaping oz"  -> [1.0, "oz"]        an ignored word is dropped
#   "2 dashes"      -> [2.0, "dashes"]    the unit as written
#   "(top)"         -> [nil, "(top)"]     a bare unit
#   "15"            -> [nil, "15"]        a bare number is not a quantity
#
# tests/fixtures/amounts.json pins it; tests/test_amount_parser.py runs this
# file over it through scripts/parse_amounts.rb. A plain module, required by
# the three generators that use it; Jekyll loading it too is harmless.

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
