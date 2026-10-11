# Can this recipe be made by halves? The judge for the scaler's x½ step
# (#1286). Data: `half_recipe:` in _data/food/scaling.yml. The build decides;
# the page carries the answer as `data-half-recipe`. One line that will not
# halve refuses the recipe. An amount with no number cannot object. Otherwise:
#   `divisible_units` (weight, volume, length)   always halves
#   `quarter_units` (spoons, imperial)   if the amount is a multiple of a
#       quarter: an eighth is the smallest fraction the page can print
#   `half_units` (cups)   if a multiple of a half: never below a quarter cup
#   a by-eye measure (handful, pinch)   always
#   anything else is a count   only if even, or the thing is `halvable`
# The yield must halve to at least one; a portions box needs an even number.
# No Jekyll here: scripts/food_yield.rb and tests/test_food_yield.py run it
# without a build. The amount reading below answers "is it even / a quarter"
# and is not a second amount parser for anyone else (#1199).

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
      # `half_recipe.by_eye_also` names by-eye measures that are not in
      # `half_step_measures` (handful). Added here and not by the callers,
      # because there are two: _plugins/food_shopping.rb and
      # scripts/food_yield.rb.
      by_eye = Array(by_eye) + Array(vocab["by_eye_also"]).map(&:to_s)
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
