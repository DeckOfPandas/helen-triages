# What each food shopping-list ingredient costs, as rates (#1458, DECISIONS
# §8.2). Data: _data/food/costs.yml, whose researched units name a food in
# _data/food/price_research.yml. Runs after _plugins/food_shopping.rb and
# adds a `rate` to each row of `doc.data["shopping"]`; food/index.html emits
# the rates only behind `site.show_costs`.
#
# The matching rule is aisles.yml's: the longest whole-word keyword in the
# folded name wins. A rate is GBP per base unit (g, ml, each, pack, or a named
# unit), so the browser multiplies a total by it and holds no matching rule.
# A cross-recipe link is never priced; a fruit row is priced by its fruit.

require "date"

module HelenTriages
  module FoodCosts
    module_function

    BASE = { "kg" => ["g", 1000.0], "l" => ["ml", 1000.0] }.freeze

    def fold(text)
      text.to_s.gsub("’", "'").strip.downcase.gsub(/\s+/, " ")
    end

    # [[pattern, rate]], longest keyword first. `rate` is {"free" => true}, or
    # a hash of base unit => [low, high] per one of it. `research` is
    # price_research.yml, which a unit written as a food's name reads from.
    def table(data, research = nil)
      foods = (research || {})["foods"] || {}
      rows = []
      Array(data["free"]).each { |word| rows << [fold(word), { "free" => true }] }
      (data["prices"] || {}).each do |word, row|
        rows << [fold(word), rate_from(row, foods, word)]
      end
      rows.sort_by! { |word, _| [-word.length, word] }
      rows.map do |word, rate|
        [/(?<![a-z0-9])#{plural_pattern(word)}(?![a-z0-9])/, rate, word]
      end
    end

    # A keyword also matches its plural (s, es, y to ies, f to ves), so
    # costs.yml writes the singular only. A plural written as its own row is
    # longer, so it still wins over its singular.
    def plural_pattern(word)
      forms = [word, "#{word}s", "#{word}es"]
      forms << "#{word[0..-2]}ies" if word.match?(/[^aeiou]y\z/)
      forms << "#{word[0..-2]}ves" if word.end_with?("f")
      "(?:#{forms.map { |form| Regexp.escape(form) }.join('|')})"
    end

    def rate_from(row, foods = {}, word = nil)
      rate = {}
      row.each do |unit, range|
        next if unit == "confidence"
        range = researched(foods, range, unit, word)[0..1] if range.is_a?(String)
        base, per = BASE[unit] || [unit, 1.0]
        rate[base] = range.map { |price| (price.to_f / per).round(8) }
      end
      rate
    end

    # [low, high, confidence] for one food's prices in one unit (MANUAL §8.2):
    # the middle 50% of 6+, the range of 3-5, both of 2, the one price twice.
    # Rounded to the penny before a base-unit rate is taken from it.
    def researched(foods, food, unit, word = nil)
      entry = foods[food]
      prices = entry.is_a?(Hash) ? entry[unit] : nil
      unless prices.is_a?(Array) && !prices.empty?
        raise ArgumentError, "costs.yml #{word}: #{unit} names #{food.inspect}, " \
                             "which price_research.yml has no #{unit} prices for"
      end
      vals = prices.map { |p| Float(p.to_s.split(" ", 2).first) }.sort
      lo, hi = vals.length >= 6 ? [quartile(vals, 1), quartile(vals, 3)] : [vals.first, vals.last]
      [lo.round(2), hi.round(2), confidence(vals, entry["thin"])]
    end

    # Inclusive quartile, as Excel's QUARTILE.INC and Python's
    # statistics.quantiles(method="inclusive"): linear between sorted values.
    def quartile(sorted, q)
      pos = (sorted.length - 1) * q / 4.0
      low = pos.floor
      return sorted[low] if low + 1 >= sorted.length
      sorted[low] + (sorted[low + 1] - sorted[low]) * (pos - low)
    end

    def confidence(vals, thin)
      return "low" if thin || vals.length < 2
      vals.length >= 4 && vals.max <= 2 * vals.min ? "high" : "medium"
    end

    # The rate for one shopping row, or nil where nothing matches.
    def rate_for(row, patterns)
      return nil if row["link"]
      key = fold(row["fruit"] || row["name"])
      patterns.each do |pattern, rate, _word|
        return rate if pattern.match?(key)
      end
      nil
    end
  end

  class FoodCostsGenerator < Jekyll::Generator
    safe true
    priority :low

    def generate(site)
      data = site.data.dig("food", "costs")
      return unless data

      patterns = FoodCosts.table(data, site.data.dig("food", "price_research"))
      names = {}
      FoodShopping::COLLECTIONS.each do |key|
        next unless site.collections[key]
        site.collections[key].docs.each do |doc|
          Array(doc.data["shopping"]).each do |row|
            rate = FoodCosts.rate_for(row, patterns)
            row["rate"] = rate if rate
            names[FoodCosts.fold(row["name"])] = !rate.nil? unless row["link"]
          end
        end
      end

      checked = Date.parse(data["checked"].to_s) rescue nil
      age = checked ? "checked #{data['checked']}, #{(Date.today - checked).to_i} days ago" : "no checked date"
      Jekyll.logger.info "Food costs:",
        "#{names.values.count(true)} of #{names.size} ingredient names priced; #{age}"
    end
  end
end
