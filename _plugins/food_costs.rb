# What each food shopping-list ingredient costs, as rates (#1458, DECISIONS
# §8.2). Data: _data/food/costs.yml. Runs after _plugins/food_shopping.rb and
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
    # a hash of base unit => [low, high] per one of it.
    def table(data)
      rows = []
      Array(data["free"]).each { |word| rows << [fold(word), { "free" => true }] }
      (data["prices"] || {}).each do |word, row|
        rows << [fold(word), rate_from(row)]
      end
      rows.sort_by! { |word, _| [-word.length, word] }
      rows.map do |word, rate|
        [/(?<![a-z0-9])#{Regexp.escape(word)}(?![a-z0-9])/, rate, word]
      end
    end

    def rate_from(row)
      rate = {}
      row.each do |unit, range|
        next if unit == "confidence"
        base, per = BASE[unit] || [unit, 1.0]
        rate[base] = range.map { |price| (price.to_f / per).round(8) }
      end
      rate
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

      patterns = FoodCosts.table(data)
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
