# =============================================================================
# WHAT A `makes:` LINE COUNTS -- so the recipe page's scaler can count it too.
# Data: `yields:` in _data/food/scaling.yml
# =============================================================================
# GitHub issue #1286. Henry's Sunday Waffles says "Makes 4–6 waffles" at the
# top and, until this, "~2 portions" under the ingredients -- two lines
# counting different things. Helen, 2026-10-04: "the scaler giving the number
# of items made ... would be clearest to me. Never tell me how many cookies
# are in a portion!!!" and then "Take the midpoint".
#
# THIS FILE ONLY READS THE LINE. It turns the text of `makes:` into what is
# being counted, or into nil. _plugins/food_shopping.rb hangs the answer on
# the document as `page.yield`, _layouts/recipe.html prints the control from
# it, and assets/js/food-scale.js does every sum. No arithmetic here beyond
# the midpoint.
#
# `makes:` IS STILL NEVER READ AS PEOPLE. That rule (food_shopping.rb,
# `portions_for`) is untouched: 950 ml is not 950 portions. What is new is
# that 950 ml is read as 950 ml.
#
# NO JEKYLL IN THIS FILE, ON PURPOSE. It is a plain module, so
# scripts/food_yield.rb can run it over a list of strings and
# tests/test_food_yield.py can check every shape without building the site.
#
# -----------------------------------------------------------------------------
# WHAT COUNTS AS A COUNT -- and each line of this is a ruling of Helen's
# -----------------------------------------------------------------------------
# ONLY THE START OF THE LINE, after an optional `about` / `approx.` word.
# "Plenty for two people" and "Enough for one normal lemon meringue pie" hold
# number words that are NOT the yield's count; "one 8-inch cake" must never
# have its 8 read as one.
#
#   "4–6 waffles, depending on ..."  count 4..6, base 5         thing: waffles
#   "12 fairy cakes"                 count 12                   thing: fairy cakes
#   "64+ tiny macarons"              count 64 ('"64+" can be treated as "64"')
#   "one 8-inch cake"                count 1, a NUMBER WORD     thing: 8-inch cake
#   "1 dozen mince pies"             count 1, thing "dozen mince pies" -- the
#                                    count stays in dozens ('"1 dozen" doubled
#                                    can be "two dozen"')
#   "950 ml", "approx. 75 g"         a MEASURE: scales by whole orders of the
#                                    recipe ("950 ml for one order ... becomes
#                                    1900 ml for 2")
#
# AND WHAT COMES BACK nil, which keeps the portions box exactly as it was:
#   "Some", "I mean, who cares, make double anyway"   no number at the start
#     ('for "some" we can retain the previous guess we made at portions')
#   "about 8", "18"            a count of NOTHING NAMED: there is no word to
#                              put after the box, and "portions" is the one
#                              word it must not be. Reported to Helen.
#   "9 or 16"                  the same, and two answers besides
#   "1.5 litres"               the box is an integer; nothing writes this yet
# =============================================================================

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

      low, high, rest = leading_count(rest, vocab["number_words"] || {})
      return nil if low.nil?

      measure = leading_measure(rest, Array(vocab["measures"]))
      if measure
        # One figure, a whole one. A range of a volume and a decimal litre are
        # shapes nobody has written; they keep the portions box until asked.
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

      # THE NOUN THAT TAKES THE PLURAL IS THE ONE BEFORE "of": "2 large rounds
      # of 4" is rounds. Everything from " of " on is carried along unchanged.
      stem, of, tail = thing.partition(/\s+of\s+/)
      groups = Array(vocab["group_words"]).map { |w| w.to_s.downcase }
      first_word = stem.split(/\s+/).first.to_s.downcase

      base = (low + high) / 2.0
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
        # "2 8-inch cakes" is unreadable -- Helen. The page puts a × between.
        "times" => stem.match?(/\A\d/),
        "box" => box(base)
      }
    end

    # The box is an INTEGER or, where the midpoint lands on a half, a RANGE OF
    # ONE: 4–7 is 5.5 and shows "5–6". Helen: "Midpoints that land on a half
    # can become a range of one." assets/js/food-scale.js `yieldBox` is the
    # same rule for every later value.
    def box(value)
      return value.to_i.to_s if value == value.to_i
      "#{value.floor}–#{value.ceil}"
    end

    # [low, high, remainder] or [nil, nil, text].
    def leading_count(text, number_words)
      range = /\A(#{NUMBER})\s*(?:–|—|-|\s+to\s+)\s*(#{NUMBER})(?=\s|\z)/
      if (m = range.match(text))
        low, high = m[1].to_f, m[2].to_f
        return [low, high, m.post_match.lstrip] if high >= low
      end

      # A NUMBER MUST END AT A SPACE, A `+`, OR THE END. "8-inch cake" opens
      # with a digit and is not a count of anything: the hyphen says so.
      if (m = /\A(#{NUMBER})(\+)?(?=\s|\z)/.match(text))
        n = m[1].to_f
        return [n, n, m.post_match.lstrip]
      end

      number_words.each do |word, value|
        next unless (m = /\A#{Regexp.escape(word.to_s)}(?=\s)\s+/i.match(text))
        return [value.to_f, value.to_f, m.post_match]
      end

      [nil, nil, text]
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
