# What a `makes:` line counts, so the recipe page's scaler can count it too
# (#1286). Data: `yields:` in _data/food/scaling.yml.
#
# This file only reads the line: _plugins/food_shopping.rb hangs the answer on
# the document as `page.made`, and assets/js/food-scale.js does every sum. No
# Jekyll here, so scripts/food_yield.rb and tests/test_food_yield.py can run it
# without a build. Only the start of the line is read, after an optional
# `about` / `approx.` word:
#   "4–6 waffles, depending..."  count, base 4: a range starts from its lower end
#   "64+ tiny macarons"          count 64, and the `+` is kept
#   "one 8-inch cake"            count 1, a number word; the 8 is never the count
#   "1 dozen mince pies"         count 1 of "dozen mince pies"
#   "950 ml", "approx. 75 g"     a measure: scales by whole recipes
#   "Some", "about 8", "9 or 16", "1.5 litres"   nil: the portions box stays

module HelenTriages
  module FoodYield
    NUMBER = /\d+(?:\.\d+)?/

    # Where the THING ends: a comma, a bracket, a dash, a semicolon, or an
    # alternative. "4–6 waffles, depending on your waffle iron" is waffles;
    # "1 large jar, or several small ones" is a large jar.
    THING_END = /\s*(?:,|\(|;|\s—\s|\s-\s|\sor\s)/

    module_function

    # @param text  [String] the recipe's `makes:` value
    # @param vocab [Hash]   `yields:` from _data/food/scaling.yml
    # @return [Hash, nil] string keys, ready for Liquid; nil when the line
    #         does not open with a count of something named
    def parse(text, vocab)
      vocab ||= {}
      rest = text.to_s.strip
      return nil if rest.empty?

      prefix = ""
      approx = Array(vocab["approx_words"]).map(&:to_s).sort_by { |w| -w.length }
      unless approx.empty?
        pattern = /\A(#{approx.map { |w| Regexp.escape(w) }.join("|")})(?=\s)\s+/i
        if (m = pattern.match(rest))
          prefix = m[1]
          rest = m.post_match
        end
      end

      low, high, rest, plus = leading_count(rest, vocab["number_words"] || {})
      return nil if low.nil?

      measure = leading_measure(rest, Array(vocab["measures"]))
      if measure
        # One figure, a whole one. A range of a volume or a decimal litre returns
        # nil and keeps the portions box.
        return nil unless low == high && low == low.to_i && low >= 1
        return {
          "kind" => "measure", "base" => low.to_i, "low" => low.to_i,
          "high" => low.to_i, "prefix" => prefix, "unit" => measure,
          "box" => low.to_i.to_s
        }
      end

      return nil unless low == low.to_i && high == high.to_i && low >= 1

      # "9 or 16" names nothing: what follows the number is another number.
      return nil if rest.match?(/\Aor\b/i)
      thing = rest.split(THING_END, 2).first.to_s.strip
      return nil if thing.empty?

      # The noun that takes the plural is the one before "of": "2 large rounds
      # of 4" is rounds. Everything from " of " on is carried along unchanged.
      stem, of, tail = thing.partition(/\s+of\s+/)
      groups = Array(vocab["group_words"]).map { |w| w.to_s.downcase }
      first_word = stem.split(/\s+/).first.to_s.downcase

      # The lower end of a range, never its midpoint.
      base = low
      {
        "kind" => "count",
        "base" => (base == base.to_i ? base.to_i : base),
        "low" => low.to_i, "high" => high.to_i,
        "prefix" => prefix,
        "stem" => stem, "rest" => of + tail,
        # `dozen mince pies` does not change with the number: it is the dozen
        # that is counted, and "dozen" has no plural after a number.
        "invariable" => groups.include?(first_word),
        # Written for exactly one ("one 8-inch cake") or for several ("12
        # fairy cakes"): which way the noun has to move when the number does.
        "singular" => (low == 1 && high == 1),
        # "2 8-inch cakes" is unreadable, so the page puts a × between.
        "times" => stem.match?(/\A\d/),
        # "64+": at least this many. The mark stays on the figure as it scales.
        "plus" => plus,
        "box" => box(base) + (plus ? "+" : "")
      }
    end

    # The box is an integer or, where a figure lands on a half, a range of one:
    # 5.5 shows "5–6". No `makes:` line starts on a half; assets/js/food-scale.js
    # `yieldBox` applies the same rule to half a recipe of an odd count.
    def box(value)
      return value.to_i.to_s if value == value.to_i
      "#{value.floor}–#{value.ceil}"
    end

    # [low, high, remainder, plus] or [nil, nil, text, false].
    def leading_count(text, number_words)
      range = /\A(#{NUMBER})\s*(?:–|—|-|\s+to\s+)\s*(#{NUMBER})(?=\s|\z)/
      if (m = range.match(text))
        low, high = m[1].to_f, m[2].to_f
        return [low, high, m.post_match.lstrip, false] if high >= low
      end

      # A number must end at a space, a `+`, or the end: "8-inch cake" opens
      # with a digit and is not a count of anything.
      if (m = /\A(#{NUMBER})(\+)?(?=\s|\z)/.match(text))
        n = m[1].to_f
        return [n, n, m.post_match.lstrip, !m[2].nil?]
      end

      number_words.each do |word, value|
        next unless (m = /\A#{Regexp.escape(word.to_s)}(?=\s)\s+/i.match(text))
        return [value.to_f, value.to_f, m.post_match, false]
      end

      [nil, nil, text, false]
    end

    # The unit as written, if the line's count is of a declared measure.
    def leading_measure(text, measures)
      sorted = measures.map(&:to_s).sort_by { |w| -w.length }
      return nil if sorted.empty?
      m = /\A(#{sorted.map { |w| Regexp.escape(w) }.join("|")})(?![A-Za-z])/i.match(text)
      m && m[1]
    end
  end
end
