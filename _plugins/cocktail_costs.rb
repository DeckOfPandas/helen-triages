# =============================================================================
# WHAT A DRINK COSTS. The arithmetic, in one place. Data: _data/cocktails/costs.yml
# =============================================================================
# Helen, 2026-09-05: "I want to add approximate costings to my cocktails, which
# I expect means adding costs to each bottle in our dictionary." It does mean
# that, and it means more than that: only 247 of the collection's 685 pours name
# a bottle at all, and the four most-poured ingredients she owns -- lime juice
# (58 pours), lemon juice (34), cane sugar syrup 2:1 (32), pineapple juice (15)
# -- will never be bottles. So there are two layers and a pour takes the first
# that answers. costs.yml's header carries the reasoning; this file carries only
# the sums.
#
# WHY A BUILD-TIME PLUGIN AND NOT LIQUID. Resolving a pour means walking the
# bottle alias map (twelve spellings collapse to five bottles), falling back
# through a generic to a fruit price and a juice yield, and spanning a min/max
# across however many bottles sit under a category. Liquid can express none of
# that without a `for` loop per pour per drink, and `_layouts/cocktail.html` is
# already 900 lines. Ruby also gets this run ONCE per drink at build rather than
# once per render.
#
# WHY THE NUMBERS ALSO GO INTO THE PAGE AS DATA. Cost is LINEAR IN VOLUME, so a
# drink scaled x4 costs exactly 4x. That is the whole reason the scaler does not
# need any of the logic above -- `cocktail-scale.js` multiplies one number it is
# handed. Two implementations of this resolution would have drifted the first
# time a bottle was renamed; one implementation and a multiplication cannot.
#
# THE RANGE IS NOT DECORATION AND IT IS NOT AN ERROR BAR. Helen chose a range
# over a single figure, and it falls out of the data rather than being invented:
# `London dry gin` is Beefeater at GBP 18 and Anchor Junipiero at GBP 38, and a
# Martini made with either is the same drink. A pour that NAMES its bottle is a
# point, so a drink naming every bottle prints one figure. That is correct
# output, not a missing range.
#
# WHAT IS DELIBERATELY NOT COUNTED. Helen, asked directly whether dashes,
# garnishes, muddled fruit and ice/salt/sugar should count: "None of these come
# into the estimated cost. I'm catering for family, not running a bar." So a
# pour counts only if its unit is a VOLUME -- 585 of 685 are -- and the excluded
# list lives in costs.yml rather than here, so that the rule and the data cannot
# disagree.
#
#   THE ONE EXCEPTION IS `to top`, and she asked for it: "We can calculate top
#   volumes, well, slightly, can't we." A counted unit everywhere else, but a
#   splash of champagne is the dearest thing in the seven glasses that take one.
#   `top_up_ml` gives it a declared range. See costs.yml.
#
# `cost_complete` IS THE HONEST HALF OF THE EXCLUSION RULE. The rule is right
# for 123 of 124 drinks and wrong for one: the Pear, Apricot and Rosemary
# Bellini is a pear, four apricots, 75 g of sugar and 25 g of honey cooked into
# a syrup, and every one of those is weighed or counted. Costed by the rule it
# comes to 7p, which is not an approximation of anything. So a drink whose
# excluded pours are INGREDIENTS rather than flourishes is marked incomplete and
# the layout declines to print a figure for it. A number known to be wrong is
# worse than no number -- the same judgement `cocktail-scale.js` made when it
# deleted the millilitre box rather than fixing it.
# =============================================================================

require "set"

module HelenTriages
  class CocktailCosts < Jekyll::Generator
    # Runs after the drinks exist and before anything renders.
    safe true
    priority :normal

    COLLECTIONS = %w[cocktail_recipes cocktail_drafts].freeze

    # An excluded pour is a real INGREDIENT, not a flourish, when it is a whole
    # fruit, a weighed solid or a count of something. A dash of bitters and a
    # mint leaf are flourishes; four apricots are lunch. Only these mark a drink
    # incomplete -- see the `cost_complete` note above.
    SUBSTANTIAL = /\A\s*[\d.]+\s*(whole|g|each|cubes?)\b|\Ahalf\z/

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

      # THE ALIAS MAP IS CASE-INSENSITIVE because bottles.yml says it is:
      # "Matching is case-insensitive; add the spelling, do not add a second
      # bottle." The shopping list's own survey found `Woodford's Reserve` and
      # `Woodford’s Reserve` differing by an apostrophe and El Dorado 3 written
      # five ways, so this is load-bearing rather than defensive.
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
          doc.data["cost"] = cost
          counted += 1
        end
      end
      # THE RESOLVED RATE TABLE, FOR THE SHOPPING LIST — #820, #817, #818.
      #
      # A shopping list totals by GENERIC across every shortlisted drink, which
      # is a figure no drink's own `cost` contains: `drink.cost` is one glass of
      # one drink, and the list wants "420 ml of London dry gin, £11.34–£14.70".
      #
      # RESOLVED HERE RATHER THAN IN JAVASCRIPT, deliberately, and it is the
      # same division that keeps `cocktail-scale.js` ignorant of prices. Every
      # rule about what a generic costs lives in `generic_rate` above — the
      # union of declared bottles and the generic's own row, `default_bottles`
      # narrowing it where Helen has ruled, a squeezed juice priced from the
      # fruit and the yield. Re-deriving any of that in the browser would be a
      # second copy to keep in step, and the browser only needs the answer.
      # So the JS multiplies millilitres by a number and does nothing else.
      #
      # BOTTLES TOO, because #818 lets Helen pick one per drink: choosing
      # Tanqueray for a `London dry gin` line collapses that line's range onto
      # one rate, and the browser cannot work out a bottle's rate from a price
      # and a size it does not have.
      #
      # GBP PER LITRE, unrounded. Rounding is a display decision and the list
      # multiplies before it rounds; rounding here would compound across a
      # dozen lines.
      generics = (@by_generic.keys + @costs["generics"].keys).compact.uniq
      rates = {
        "generics" => generics.each_with_object({}) do |g, h|
          r = generic_rate(g) and h[g] = r
        end,
        "bottles" => @costs["bottles"].keys.each_with_object({}) do |n, h|
          r = bottle_rate(n) and h[n] = r
        end
      }
      site.data["cocktails"]["rates"] = rates

      Jekyll.logger.info "Costs:", "priced #{counted} drinks " \
        "(prices checked #{@costs['checked']}); " \
        "rates for #{rates['generics'].size} generics, " \
        "#{rates['bottles'].size} bottles"
    end

    private

    # GBP per litre for one declared bottle, or nil if it carries no price.
    def bottle_rate(name)
      c = @costs["bottles"][name]
      return nil unless c && c["gbp"] && c["size_ml"].to_f.positive?
      1000.0 * c["gbp"].to_f / c["size_ml"].to_f
    end

    # [min, max] GBP per litre for a generic, or nil if nothing prices it.
    #
    # BOTH SOURCES ARE UNIONED, NOT RANKED, and that was a correction. The first
    # version let declared bottles WIN and forbade a fallback beside them, on
    # the reasoning that two figures for one generic is two truths. A test
    # written to enforce that immediately found the case that disproves it:
    # `cane sugar syrup 2:1` is Monin Pure Cane Sugar at about GBP 10 a litre
    # AND two bags of sugar at about 90p a litre, and BOTH are true -- you
    # either buy it or you make it. Ranking them would have priced 34 pours,
    # the third most-poured thing in the collection, an order of magnitude out
    # in whichever direction the rule happened to pick.
    #
    # So a generic spans everything that could fill it. For `London dry gin`
    # that is six bottles and no fallback; for a syrup it is the jar and the
    # pan. This is the same reasoning that made the range a range in the first
    # place, applied one level down.
    # HELEN'S DEFAULTS NARROW THE SET, WHEN SHE HAS GIVEN ONE. `default_bottles`
    # says which bottles a category is priced FROM -- "London dry gin let's say
    # the default is tanqueray" -- so the range stops spanning six gins she owns
    # but would not pour for an unqualified `London dry gin`. Absent a ruling the
    # set is every bottle under the generic, which is the right default: breadth
    # is an admission of not knowing, and it should persist until she narrows it.
    def generic_rate(g)
      names = @defaults[g] || @by_generic[g]
      rates = names.map { |n| bottle_rate(n) }.compact

      e = @costs["generics"][g]
      return rates.empty? ? nil : [rates.min, rates.max] unless e

      # A squeezed juice is priced from the fruit and the yield, so that #546's
      # figures are read rather than restated. Cheap end: cheapest fruit at its
      # BEST yield. Dear end: dearest fruit at its worst. Both ranges are real
      # and multiplying them out is what makes limes GBP 6-15 a litre.
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

    # Millilitres for an amount string, or nil when the pour is free under
    # Helen's rule. `to top` is handled by the caller, which knows the generic.
    def volume_ml(amount)
      a = amount.to_s.strip
      return nil if @excluded.include?(a)
      m = /\A([\d.]+)\s+(.*)\z/.match(a) or return nil
      unit = m[2].strip
      @ignored.each { |w| unit = unit.sub(/\A#{Regexp.escape(w)}\s+/, "") }
      return nil if @excluded.include?(unit) || !@per_ml.key?(unit)
      m[1].to_f * @per_ml[unit].to_f
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
        if amount == "to top"
          tops = generics.filter_map { |g| @costs["top_up_ml"][g] }
          next if tops.empty?
          lo_ml = tops.map { |t| t["ml_min"].to_f }.min
          hi_ml = tops.map { |t| t["ml_max"].to_f }.max
        else
          ml = volume_ml(amount)
          if ml.nil?
            # Excluded. Only an INGREDIENT-sized exclusion is even a candidate
            # for spoiling the total; see `substantial >= priced` below.
            substantial += 1 if SUBSTANTIAL.match?(amount)
            next
          end
          lo_ml = hi_ml = ml
        end

        # --- at what rate ----------------------------------------------------
        # A NAMED BOTTLE WINS. `suggestion` is what Helen reaches for, so it is
        # a point price and not a category span.
        sug = Array(ing["suggestion"]).map(&:to_s)
        rates = sug.filter_map { |s| @alias[s.downcase] }
                   .filter_map { |n| bottle_rate(n) }

        if rates.empty?
          # A generic written as a LIST means "either would do" (issue #441),
          # so the span covers both rather than picking one.
          gr = generics.filter_map { |g| generic_rate(g) }
          if gr.empty?
            # Nothing in costs.yml prices this generic. That is a gap in the
            # data rather than a deliberate exclusion, so it counts against
            # completeness outright. There are none today and
            # test_every_priceable_pour_has_a_price keeps it that way.
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
        # True when min and max agree to the penny -- every pour named its
        # bottle, so there is nothing to range over and the page prints one
        # figure. Computed here so the template asks a boolean, not a float.
        "exact"    => (max - min).abs < 0.005,
        # COMPLETE UNLESS THE EXCLUDED PART OUTWEIGHS THE PRICED PART, and the
        # threshold is a count rather than a value because the excluded things
        # have no value to compare with -- that is what excluded means.
        #
        # THE FIRST VERSION SUPPRESSED ANY DRINK WITH A SUBSTANTIAL EXCLUSION
        # AND THAT WAS WRONG: it hid 11 of 124, including five punches whose
        # only sin was a dozen sugar cubes (about 7p against a GBP 12 bowl).
        # Losing a good number to protect against a rounding error is the same
        # trade in reverse. Two drinks fail this test and both deserve to --
        # the Bellini (2 priced, 4 excluded: a pear, four apricots, 75 g sugar,
        # 25 g honey) and the Caipirinha (1 priced, 2 excluded: half a lime and
        # 20 g of palm sugar). In both, what is missing IS the drink.
        "complete" => substantial < priced,
        "priced"   => priced,
        "excluded" => substantial,
        "checked"  => @costs["checked"]
      }
    end
  end
end
