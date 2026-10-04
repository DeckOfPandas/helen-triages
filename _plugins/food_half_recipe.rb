# =============================================================================
# CAN THIS RECIPE BE MADE BY HALVES? -- the judge for the scaler's x½ step.
# Data: `half_recipe:` in _data/food/scaling.yml
# =============================================================================
# GitHub issue #1286. A `makes:` recipe is scaled in whole recipes -- x1, x2,
# x3. Helen, 2026-10-04, asked whether it could go below one: "Half a recipe
# would be great where the numbers aren't insane! Can we judge that?" And the
# shape: "not having half recipes in between integers, just between 0 and 1".
#
# So there is ONE extra step, x½, and a recipe gets it only if halving every
# figure on the page gives something a person could act on. THE BUILD DECIDES,
# here, once; the page carries the answer as `data-half-recipe` and the
# browser never judges anything.
#
# -----------------------------------------------------------------------------
# THE RULE -- conservative: one line that will not halve refuses the recipe
# -----------------------------------------------------------------------------
# An ingredient with NO number in its amount, or no amount, does not scale and
# so cannot object. Otherwise, by its unit:
#
#   a WEIGHT, VOLUME or LENGTH (`divisible_units`)   always halves: the scaler
#       already prints 31 g and 313 ml.
#   a SPOON, CUP or IMPERIAL measure (`quarter_units`)   halves if the amount
#       is a multiple of a quarter, because an eighth is the smallest fraction
#       the page has a glyph for: ¼ tsp -> ⅛ tsp is fine, ⅛ tsp -> 0.06 tsp is
#       not.
#   a CUP (`half_units`)   halves only if the amount is a multiple of a HALF,
#       so it never goes below a quarter cup. Helen, on "⅞ cups whole milk":
#       "Please take the half step off the waffles."
#   a BY-EYE measure (`half_step_measures`: handful, pinch ...)   always: it
#       has its own rule and never prints less than a half.
#   anything else is a COUNT of things -- "3" eggs, "2 large", "1 sprig",
#       "2 x 400 g cans" -- and halves only if the count is EVEN, or the thing
#       is on the `halvable` list (half a lemon is a real thing; half an egg
#       is not).
#
# AND THE YIELD has to halve too: half of what one recipe makes must be at
# least one of it. "one 8-inch cake", "1 jar", "1 dozen mince pies" and
# "1 litre" are refused; "5 waffles" halves to "2–3". A recipe that keeps the
# portions box halves only an EVEN number of portions.
#
# NO JEKYLL IN THIS FILE, for the reason _plugins/food_yield.rb gives:
# scripts/food_yield.rb runs it over JSON, and tests/test_food_yield.py checks
# it without a build.
#
# THIS READS AMOUNTS, which _plugins/food_shopping.rb's header says the build
# does not do. It still does no arithmetic that reaches the page: the one
# thing computed here is a yes or a no. The number is read by the smallest
# rule that answers "is it even / is it a quarter" -- not a second amount
# parser for anyone else to use (#1199).
# =============================================================================

module HelenTriages
  module HalfRecipe
    VULGAR = {
      "½" => 0.5, "⅓" => 1.0 / 3, "⅔" => 2.0 / 3, "¼" => 0.25, "¾" => 0.75,
      "⅛" => 0.125, "⅜" => 0.375, "⅝" => 0.625, "⅞" => 0.875
    }.freeze
    ONE = "(\\d+(?:\\.\\d+)?)?([#{VULGAR.keys.join}])?"
    AMOUNT = /\A\s*~?\s*#{ONE}(?:\s*(?:–|—|-|\s+to\s+)\s*#{ONE})?\s*(.*?)\s*\z/m

    module_function

    # @param groups   [Array]  the recipe's `ingredient_groups`
    # @param made     [Hash, nil] FoodYield.parse's reading of `makes:`
    # @param portions [Integer, nil] what the portions box would start at
    # @param vocab    [Hash]   `half_recipe:` from _data/food/scaling.yml
    # @param by_eye   [Array]  `half_step_measures` from the same file
    # @return [Hash] {"ok" => true/false, "why" => the line that decided it}
    def judge(groups, made, portions, vocab, by_eye)
      vocab ||= {}
      verdict = yield_halves(made, portions)
      return verdict unless verdict["ok"]

      Array(groups).each do |group|
        next unless group.is_a?(Hash)
        Array(group["items"]).each do |item|
          next unless item.is_a?(Hash) && !item["incidental"]
          amount = item["amount"].to_s
          next if amount.strip.empty?
          why = objection(amount, item["item"].to_s, vocab, Array(by_eye))
          return { "ok" => false, "why" => "#{amount} #{item['item']}: #{why}" } if why
        end
      end
      { "ok" => true, "why" => verdict["why"] }
    end

    def yield_halves(made, portions)
      if made
        half = made["base"].to_f / 2
        thing = made["kind"] == "measure" ? made["unit"] : made["stem"]
        if half < 1
          return { "ok" => false, "why" => "the yield is #{made['box']} #{thing}: half is less than one" }
        end
        return { "ok" => true, "why" => "the yield halves (#{made['box']} #{thing})" }
      end
      if portions.to_i.positive?
        if portions.to_i.odd?
          return { "ok" => false, "why" => "#{portions} portions: an odd number does not halve" }
        end
        return { "ok" => true, "why" => "#{portions} portions halves" }
      end
      { "ok" => false, "why" => "no yield to halve" }
    end

    # nil when the amount halves; otherwise why it does not.
    def objection(amount, name, vocab, by_eye)
      m = AMOUNT.match(amount)
      low = number(m[1], m[2])
      return nil if low.nil?                       # no number: it does not scale
      high = number(m[3], m[4])
      numbers = [low, high].compact

      # A bracket restates the quantity ("1 tbsp (6 g)"); it is not the unit.
      unit = m[5].to_s.sub(/\s*\(.*\z/m, "").downcase
      words = unit.split(/[\s-]+/)
      packaged = words.first == "x" || words.first == "×"

      unless packaged
        return nil if (words & list(vocab, "divisible_units")).any?
        return nil if words.any? { |w| by_eye.include?(w) || by_eye.include?(w.sub(/e?s\z/, "")) }
        if (words & list(vocab, "half_units")).any?
          return nil if numbers.all? { |n| whole?(n * 2) }
          return "half of it is less than a quarter cup, or not a quarter at all"
        end
        if (words & list(vocab, "quarter_units")).any?
          return nil if numbers.all? { |n| whole?(n * 4) }
          return "half of it is smaller than an eighth, or is not a fraction the page can print"
        end
      end

      return nil if numbers.all? { |n| whole?(n / 2) }
      halvable = list(vocab, "halvable")
      head = (unit + " " + name.split(/[,(]/).first.to_s).downcase
      if halvable.any? { |w| head.match?(/(?<![a-z])#{Regexp.escape(w)}(?:e?s)?(?![a-z])/) }
        return nil if numbers.all? { |n| whole?(n * 2) }
      end
      "a count that does not halve to a whole number"
    end

    def number(digits, fraction)
      return nil if digits.nil? && fraction.nil?
      digits.to_f + (fraction ? VULGAR[fraction] : 0)
    end

    def whole?(n)
      (n - n.round).abs < 1e-9
    end

    def list(vocab, key)
      Array(vocab[key]).map { |w| w.to_s.downcase }
    end
  end
end
