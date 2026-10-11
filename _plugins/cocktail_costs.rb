# What a drink costs. Data: _data/cocktails/costs.yml, whose header carries
# the reasoning.
#
# A pour takes the first price that answers: a named bottle, else its generic.
# A named bottle is a point and a generic is a range across its bottles, so a
# drink naming every bottle prints one figure. Only a volume counts: the
# `excluded_units` in costs.yml (dashes, garnishes) are free, except that a
# `(top)` has a declared range in `top_up_ml`, and a counted or weighed pour
# whose generic has a row in `fruit_prices` or `weight_prices` is priced (#748).
# `cost.complete` is false when the unpriced ingredient-sized pours are at
# least as many as the priced ones; the layout then prints no figure.
# Cost is linear in volume, so the figures go into the page as data and
# cocktail-scale.js only multiplies: the resolution lives here alone.

require "date"
require "set"
require_relative "amount"

module HelenTriages
  class CocktailCosts < Jekyll::Generator
    safe true
    priority :normal

    COLLECTIONS = %w[cocktail_recipes cocktail_drafts].freeze

    # An excluded pour is an ingredient, not a flourish, when it is a whole
    # fruit, a weighed solid or a count of something. Only these count against
    # `cost.complete`.
    SUBSTANTIAL = /\A\s*[\d.]+\s*(whole|g|each|cubes?)\b|\Ahalf\z/

    # #748. A pour counted in one of these is priced per PIECE from
    # `fruit_prices`, when its generic has a row there; `half` is half a piece.
    COUNTED = /\A\s*([\d.]+)\s+(whole|each|cubes?)\s*\z/
    WEIGHED = /\A\s*([\d.]+)\s+g\s*\z/

    def generate(site)
      @costs  = site.data.dig("cocktails", "costs")
      @ing    = site.data.dig("cocktails", "ingredients")
      bottles = site.data.dig("cocktails", "bottles")
      return unless @costs && @ing && bottles

      @per_ml   = @ing["measures"]["per_ml"]
      @yields   = @ing["juice_yields"] || {}
      @defaults = @costs["default_bottles"] || {}
      @excluded = (@costs["excluded_units"] || []).to_set
      @ignored  = (@ing["measures"]["ignored_words"] || [])

      # Case-insensitive: the collection spells one bottle several ways, and
      # bottles.yml lists the spellings as aliases of one bottle.
      @alias = {}
      @by_generic = Hash.new { |h, k| h[k] = [] }
      bottles["bottles"].each do |name, b|
        @alias[name.downcase] = name
        Array(b && b["aliases"]).each { |a| @alias[a.to_s.downcase] = name }
        @by_generic[b && b["generic"]] << name
      end

      counted = 0
      COLLECTIONS.each do |key|
        next unless site.collections[key]
        site.collections[key].docs.each do |doc|
          cost = cost_for(doc.data["ingredients"])
          next unless cost
          # Beside the cost, not inside it (#818): only the index's shopping list
          # reads `choices`.
          choices = choices_for(doc.data["ingredients"])
          cost["choices"] = choices unless choices.empty?
          doc.data["cost"] = cost
          counted += 1
        end
      end
      # The resolved rate table, for the shopping list (#820, #817, #818): GBP per
      # litre by generic and by bottle, unrounded, because the list multiplies
      # before it rounds. Resolved here so the browser never re-derives what a
      # generic costs (`generic_rate`).
      generics = (@by_generic.keys + @costs["generics"].keys).compact.uniq
      rates = {
        "generics" => generics.each_with_object({}) do |g, h|
          r = generic_rate(g) and h[g] = r
        end,
        "bottles" => @costs["bottles"].keys.each_with_object({}) do |n, h|
          r = bottle_rate(n) and h[n] = r
        end,
        # #748. GBP per piece and GBP per kilo, as a [lo, hi] pair per generic; a
        # generic absent here has no price.
        "fruit" => (@costs["fruit_prices"] || {}).each_with_object({}) do |(g, f), h|
          r = piece_rate(f) and h[g] = r
        end,
        "weight" => (@costs["weight_prices"] || {}).each_with_object({}) do |(g, w), h|
          r = kilo_rate(w) and h[g] = r
        end
      }
      site.data["cocktails"]["rates"] = rates

      # The log line says how old the prices are (#749). The two-year limit is
      # tests/test_cocktails.py::test_the_price_check_date_is_less_than_two_years_old.
      Jekyll.logger.info "Costs:", "priced #{counted} drinks " \
        "(prices checked #{@costs['checked']}#{checked_age}); " \
        "rates for #{rates['generics'].size} generics, " \
        "#{rates['bottles'].size} bottles"
    end

    private

    # ", N days ago" for the log line, or "" when `checked:` is not a date, so
    # the build does not fall over for it.
    def checked_age
      checked = Date.parse(@costs["checked"].to_s)
      days = (Date.today - checked).to_i
      case days
      when 0 then ", today"
      when 1 then ", 1 day ago"
      else ", #{days} days ago"
      end
    rescue ArgumentError, TypeError
      ""
    end

    # GBP per litre for one declared bottle, or nil if it carries no price.
    def bottle_rate(name)
      c = @costs["bottles"][name]
      return nil unless c && c["gbp"] && c["size_ml"].to_f.positive?
      1000.0 * c["gbp"].to_f / c["size_ml"].to_f
    end

    # [min, max] GBP per PIECE for a `fruit_prices` row, or nil. #748.
    def piece_rate(row)
      return nil unless row.is_a?(Hash) && row["gbp_min"] && row["gbp_max"]
      [row["gbp_min"].to_f, row["gbp_max"].to_f]
    end

    # [min, max] GBP per KILO for a `weight_prices` row, or nil. #748.
    def kilo_rate(row)
      return nil unless row.is_a?(Hash) && row["gbp_per_kg_min"] && row["gbp_per_kg_max"]
      [row["gbp_per_kg_min"].to_f, row["gbp_per_kg_max"].to_f]
    end

    # #748. What a counted or weighed pour of these generics costs, as
    # [min, max] GBP, or nil when the amount is neither or no generic has a row.
    # A list generic spans every member that has a row.
    def solid_cost(amount, generics)
      if amount == "half"
        pieces = 0.5
        table = @costs["fruit_prices"] || {}
        rate_of = ->(row) { piece_rate(row) }
      elsif (m = COUNTED.match(amount))
        pieces = m[1].to_f
        table = @costs["fruit_prices"] || {}
        rate_of = ->(row) { piece_rate(row) }
      elsif (m = WEIGHED.match(amount))
        pieces = m[1].to_f / 1000.0
        table = @costs["weight_prices"] || {}
        rate_of = ->(row) { kilo_rate(row) }
      else
        return nil
      end

      rates = generics.filter_map { |g| rate_of.call(table[g]) }
      return nil if rates.empty?
      [pieces * rates.map(&:first).min, pieces * rates.map(&:last).max]
    end

    # [min, max] GBP per litre for a generic, or nil if nothing prices it.
    # The declared bottles and the generic's own row in costs.yml are unioned,
    # not ranked: a syrup is both a bought bottle and a bag of sugar, and both
    # prices are true. A `default_bottles` entry narrows the bottles to the ones
    # Helen pours for the unqualified category.
    def generic_rate(g)
      names = @defaults[g] || @by_generic[g]
      rates = names.map { |n| bottle_rate(n) }.compact

      e = @costs["generics"][g]
      return rates.empty? ? nil : [rates.min, rates.max] unless e

      # A squeezed juice is priced from the fruit and its yield (#546). Cheap end:
      # cheapest fruit at its best yield. Dear end: dearest fruit at its worst.
      if (fruit_key = e["from_fruit"])
        y = @yields[fruit_key] or return nil
        f = @costs["fruit_prices"][y["fruit"]] or return nil
        rates += [1000.0 * f["gbp_min"].to_f / y["ml_max"].to_f,
                  1000.0 * f["gbp_max"].to_f / y["ml_min"].to_f]
      else
        rates += [e["gbp_per_litre_min"].to_f, e["gbp_per_litre_max"].to_f]
      end

      [rates.min, rates.max]
    end

    # Millilitres for an amount string, or nil when the pour is excluded. `(top)`
    # is handled by the caller, which knows the generic.
    def volume_ml(amount)
      a = amount.to_s.strip
      return nil if @excluded.include?(a)
      number, unit = Amount.parse(a, @ignored)
      return nil if number.nil? || @excluded.include?(unit) || !@per_ml.key?(unit)
      number * @per_ml[unit].to_f
    end

    # Where a pour offers a choice of bottle, and what each would cost (#818,
    # chosen per drink). A choice is two or more resolvable, priced bottles on
    # one pour. The browser only does arithmetic with it:
    #
    #     lo' = drink.lo - choice.lo + choice.bottles[chosen]
    #
    # This repeats part of `cost_for` on purpose; keep the two in step.
    def choices_for(ingredients)
      return [] unless ingredients.is_a?(Array)

      out = []
      ingredients.each do |ing|
        next unless ing.is_a?(Hash)
        amount = ing["amount"].to_s.strip
        generics = Array(ing["generic"]).map(&:to_s)

        if amount == "(top)"
          tops = generics.filter_map { |g| @costs["top_up_ml"][g] }
          next if tops.empty?
          lo_ml = tops.map { |t| t["ml_min"].to_f }.min
          hi_ml = tops.map { |t| t["ml_max"].to_f }.max
        else
          ml = volume_ml(amount) or next
          lo_ml = hi_ml = ml
        end

        names = Array(ing["suggestion"]).map(&:to_s)
                  .filter_map { |s| @alias[s.downcase] }.uniq
        priced = names.filter_map { |n| [n, bottle_rate(n)] if bottle_rate(n) }
        next if priced.length < 2

        bottles = priced.to_h { |n, r| [n, (hi_ml * r / 1000.0).round(4)] }
        out << {
          "generic" => generics.join(" or "),
          "ml_min"  => lo_ml,
          "ml_max"  => hi_ml,
          # What this pour contributes to the drink's range TODAY, so the
          # browser can subtract exactly what it is replacing.
          "lo"      => (lo_ml * priced.map(&:last).min / 1000.0).round(4),
          "hi"      => (hi_ml * priced.map(&:last).max / 1000.0).round(4),
          "bottles" => bottles
        }
      end
      out
    end

    def cost_for(ingredients)
      return nil unless ingredients.is_a?(Array) && !ingredients.empty?

      min = 0.0
      max = 0.0
      priced = 0
      substantial = 0

      ingredients.each do |ing|
        next unless ing.is_a?(Hash)
        amount = ing["amount"].to_s.strip
        generics = Array(ing["generic"]).map(&:to_s)

        # --- how much liquid, if any ---------------------------------------
        if amount == "(top)"
          tops = generics.filter_map { |g| @costs["top_up_ml"][g] }
          next if tops.empty?
          lo_ml = tops.map { |t| t["ml_min"].to_f }.min
          hi_ml = tops.map { |t| t["ml_max"].to_f }.max
        else
          ml = volume_ml(amount)
          if ml.nil?
            # A counted fruit or weighed solid with a price row is a priced pour
            # (#748). It has no millilitres, so it skips the rate arithmetic below.
            if (solid = solid_cost(amount, generics))
              min += solid.first
              max += solid.last
              priced += 1
              next
            end
            # Excluded. Only an ingredient-sized exclusion counts against `complete`;
            # see `substantial < priced` below.
            substantial += 1 if SUBSTANTIAL.match?(amount)
            next
          end
          lo_ml = hi_ml = ml
        end

        # --- at what rate ----------------------------------------------------
        # A named bottle wins: a point price, not a category span.
        sug = Array(ing["suggestion"]).map(&:to_s)
        rates = sug.filter_map { |s| @alias[s.downcase] }
                   .filter_map { |n| bottle_rate(n) }

        if rates.empty?
          # A generic written as a LIST means "either would do" (issue #441),
          # so the span covers both rather than picking one.
          gr = generics.filter_map { |g| generic_rate(g) }
          if gr.empty?
            # Nothing in costs.yml prices this generic: a gap in the data, so it
            # counts against completeness. test_every_priceable_pour_has_a_price
            # keeps there being none.
            substantial += 1
            next
          end
          lo_rate = gr.map(&:first).min
          hi_rate = gr.map(&:last).max
        else
          lo_rate = rates.min
          hi_rate = rates.max
        end

        min += lo_ml * lo_rate / 1000.0
        max += hi_ml * hi_rate / 1000.0
        priced += 1
      end

      return nil if priced.zero?

      {
        "min"      => min.round(2),
        "max"      => max.round(2),
        # The printed form, two decimals always (#1215): a Float drops its
        # trailing zero and Liquid has no printf. `min`/`max` stay numbers for
        # the data attributes, the index's JSON and the shopping list.
        "min_text" => format("%.2f", min),
        "max_text" => format("%.2f", max),
        # True when min and max agree to the penny -- every pour named its
        # bottle, so there is nothing to range over and the page prints one
        # figure. Computed here so the template asks a boolean, not a float.
        "exact"    => (max - min).abs < 0.005,
        # Complete unless the ingredient-sized exclusions are at least as many as
        # the priced pours. A count, because an excluded thing has no value to
        # compare: a punch must not lose its figure to a dozen sugar cubes.
        "complete" => substantial < priced,
        "priced"   => priced,
        "excluded" => substantial,
        "checked"  => @costs["checked"]
      }
    end
  end
end
