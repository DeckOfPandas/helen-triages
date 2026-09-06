# =============================================================================
# HOW MANY UNITS ARE IN A DRINK. Spec: #297. Data: _data/cocktails/abv.yml
# =============================================================================
# Helen, 2026-09-06: "I want the number of units in a drink, not the ABV of the
# drink, i.e. water etc don't matter." Those are two different questions and the
# second one is the one that makes this file short. The ABV of a finished drink
# needs the dilution modelled -- how long it was stirred, how cold the ice was,
# how much of it melted -- and none of that is recorded or knowable. The UNITS
# in a drink need none of it: a UK unit is 10 ml of pure alcohol, water adds
# neither alcohol nor units, and shaking a drink for a minute longer does not
# change how much gin went into it.
#
#   units = sum over pours of (ml x abv / 1000)
#
# THIS IS THE COSTS PLUGIN'S SIBLING and deliberately so. Same two layers, same
# alias map, same exclusion rule, same `default_bottles` ruling. Read
# cocktail_costs.rb first; only the four differences below are interesting.
#
# --- DIFFERENCE 1: WHAT SPOILS AN EXACT FIGURE -------------------------------
# Cost is inexact whenever any pour failed to name its bottle. Units is inexact
# only when a pour that ACTUALLY CONTAINS ALCOHOL failed to name one. The
# distinction is not pedantry -- it is most of the collection. A Tom Collins
# pours a named gin and tops with soda water, and soda water is 0% however
# vaguely it is described, so the total is exact and prints as one figure. Under
# the cost rule that same drink would print a range spanning nothing.
#
# So: a generic fallback on a 0% ingredient costs nothing, and neither does a
# `to top` of soda. Only alcohol can make an alcohol figure uncertain.
#
# --- DIFFERENCE 2: IT DOES NOT SCALE, AND EMITS NO DATA ATTRIBUTES -----------
# Cost writes `data-cost-min`/`max` into the page so cocktail-scale.js can
# multiply them, because a drink made at x4 costs four times as much. Units is
# reported PER SERVING -- Helen, 2026-09-06: "Give units per serving, not total,
# so scaler setting doesn't matter" -- and a serving does not get stronger when
# you make eight of them. The number is therefore inert, the scaler must not
# touch it, and the way to guarantee that is to give it nothing to touch.
#
# --- DIFFERENCE 3: `serves` --------------------------------------------------
# `cocktail-scale.js` says outright that there is no `serves:` field on a drink
# and that it "does not invent one", because x2 means twice what the page says.
# That reasoning is about the SCALER and it still holds. But units per serving
# is a different question, and for a punch that fills a bowl the answer without
# a divisor is a number that reads as a warning rather than a fact.
#
# So `serves:` exists now, Helen's call on 2026-09-06, and it is deliberately
# NARROW: absent on every drink that fills one glass, present only where the
# recipe as written is plainly more than one drink. Absent means 1. The scaler
# still does not read it and still multiplies the recipe as written.
#
# --- DIFFERENCE 4: NO `complete` FLAG ----------------------------------------
# Cost withholds a figure for the Bellini because the pear and the apricots it
# excludes ARE the drink, so the priced remainder is not an approximation of
# anything. Nothing excluded from a UNIT count can do that: the excluded units
# are dashes, leaves, cubes and pinches, and none of them is alcohol in a
# quantity that moves a figure printed to one decimal place. Six dashes of
# Angostura is 0.02 units. A drink is either alcoholic and countable, or it has
# no alcohol in it and 0.0 is the right answer.
# =============================================================================

require "set"

module HelenTriages
  class CocktailUnits < Jekyll::Generator
    safe true
    priority :normal

    COLLECTIONS = %w[cocktail_recipes cocktail_drafts].freeze

    # A UK unit is 10 ml of pure ethanol. `ml * (abv/100) / 10` is the same
    # thing as `ml * abv / 1000`, and the second form is what avoids a rounding
    # step in the middle of a sum.
    ML_PER_UNIT = 1000.0

    def generate(site)
      @abv    = site.data.dig("cocktails", "abv")
      costs   = site.data.dig("cocktails", "costs")
      @ing    = site.data.dig("cocktails", "ingredients")
      bottles = site.data.dig("cocktails", "bottles")
      return unless @abv && costs && @ing && bottles

      @per_ml   = @ing["measures"]["per_ml"]
      @ignored  = @ing["measures"]["ignored_words"] || []

      # THE EXCLUSION RULE AND THE TOP-UP RANGES ARE READ OUT OF costs.yml
      # RATHER THAN RESTATED HERE, which is the same call cocktail_costs.rb
      # made about its own rule living in the data: "so that the rule and the
      # data cannot disagree". They are not price facts -- `dash` is a shape of
      # pour, and how much a `to top` pours is a fact about glasses -- so a
      # future tidy that moves both blocks into ingredients.yml would be right.
      # Until then, one copy read twice beats two copies that drift.
      @excluded = (costs["excluded_units"] || []).to_set
      @top_up   = costs["top_up_ml"] || {}
      @defaults = costs["default_bottles"] || {}

      @non_alcoholic = (@abv["non_alcoholic"] || []).to_set

      @alias = {}
      @by_generic = Hash.new { |h, k| h[k] = [] }
      bottles["bottles"].each do |name, b|
        @alias[name.downcase] = name
        Array(b && b["aliases"]).each { |a| @alias[a.to_s.downcase] = name }
        @by_generic[b && b["generic"]] << name
      end

      counted = 0
      approximate = 0
      COLLECTIONS.each do |key|
        next unless site.collections[key]
        site.collections[key].docs.each do |doc|
          units = units_for(doc.data["ingredients"], doc.data["serves"])
          next unless units
          doc.data["units"] = units
          counted += 1
          approximate += 1 unless units["exact"]
        end
      end
      Jekyll.logger.info "Units:", "counted #{counted} drinks " \
        "(#{approximate} approximate, abv filled #{@abv['filled']})"
    end

    private

    # Percent ABV for one declared bottle, or nil if it carries none.
    def bottle_abv(name)
      row = @abv["bottles"][name]
      row && row["abv"] && row["abv"].to_f
    end

    # Percent ABV for a generic, or nil if nothing gives it one.
    #
    # HELEN'S `default_bottles` RULING DECIDES A CATEGORY WHEN SHE HAS GIVEN
    # ONE, exactly as it decides its price. "London dry gin let's say the
    # default is tanqueray" makes an unqualified gin 43.1% -- a real bottle's
    # strength rather than an average across six gins she would not have poured
    # for it. Absent a ruling, the mean across every bottle declared under the
    # generic, which is the honest reading of not knowing which she reached for.
    #
    # THE MEAN, NOT THE MIDPOINT, and the difference shows up in exactly one
    # place: `rhum agricole blanc` has eight bottles, six of them at 50% and two
    # lower. The midpoint of the extremes would report 45% for a category that
    # is overwhelmingly 50%. The mean follows the shelf.
    def generic_abv(g)
      return 0.0 if @non_alcoholic.include?(g)

      names = @defaults[g] || @by_generic[g]
      vals = names.map { |n| bottle_abv(n) }.compact
      return vals.sum / vals.size unless vals.empty?

      row = @abv["generics"][g]
      row && row["abv"] && row["abv"].to_f
    end

    # Millilitres for an amount string, or nil when the pour does not count.
    # Identical to cocktail_costs.rb's; `to top` is handled by the caller.
    def volume_ml(amount)
      a = amount.to_s.strip
      return nil if @excluded.include?(a)
      m = /\A([\d.]+)\s+(.*)\z/.match(a) or return nil
      unit = m[2].strip
      @ignored.each { |w| unit = unit.sub(/\A#{Regexp.escape(w)}\s+/, "") }
      return nil if @excluded.include?(unit) || !@per_ml.key?(unit)
      m[1].to_f * @per_ml[unit].to_f
    end

    def units_for(ingredients, serves)
      return nil unless ingredients.is_a?(Array) && !ingredients.empty?

      total = 0.0
      exact = true
      pours = 0

      ingredients.each do |ing|
        next unless ing.is_a?(Hash)
        amount = ing["amount"].to_s.strip
        generics = Array(ing["generic"]).map(&:to_s)

        # --- how much liquid, if any ---------------------------------------
        # A `to top` is a declared RANGE, so its midpoint is the best single
        # figure available. It only makes the drink approximate if what is
        # being topped with contains alcohol -- see DIFFERENCE 1 above.
        topped = false
        if amount == "to top"
          tops = generics.filter_map { |g| @top_up[g] }
          next if tops.empty?
          ml = tops.map { |t| (t["ml_min"].to_f + t["ml_max"].to_f) / 2.0 }.max
          topped = true
        else
          ml = volume_ml(amount)
          next if ml.nil?
        end

        # --- at what strength ------------------------------------------------
        # A NAMED BOTTLE WINS, and is the only thing that can be exact.
        sug = Array(ing["suggestion"]).map(&:to_s)
        strengths = sug.filter_map { |s| @alias[s.downcase] }
                       .filter_map { |n| bottle_abv(n) }

        if strengths.empty?
          # A generic written as a LIST means "either would do" (#441), so take
          # the mean of what each could be rather than picking one.
          gs = generics.filter_map { |g| generic_abv(g) }
          next if gs.empty?
          abv = gs.sum / gs.size
          # Only alcohol can spoil the figure. A vague 0% is still 0%.
          exact = false if abv.positive?
        else
          abv = strengths.sum / strengths.size
          exact = false if abv.positive? && strengths.size > 1
        end

        # A topped pour is a range whatever named it, but again only when the
        # thing being poured is alcoholic.
        exact = false if topped && abv.positive?

        total += ml * abv / ML_PER_UNIT
        pours += 1
      end

      return nil if pours.zero?

      # A ZERO IS WITHHELD, AND THE COLLECTION HAS EXACTLY ONE. The Pear,
      # Apricot and Rosemary Bellini's ingredient list contains no alcohol at
      # all -- it tops with SODA WATER and the prosecco its title implies is
      # simply not recorded. 0.0 is the correct sum of what is written down and
      # a wrong answer about the drink, because on a cocktail page "0.0 units"
      # reads as "this is alcohol-free" rather than "we could not find the
      # alcohol".
      #
      # This is the same judgement cocktail_costs.rb makes with `cost_complete`
      # for the same drink, and the one cocktail-scale.js made when it deleted
      # the millilitre box rather than ship a control that lied: a number known
      # to be wrong is worse than no number.
      #
      # IT IS NOT A `complete` FLAG BECAUSE IT DOES NOT NEED TO BE. Cost needs
      # one because a drink can be partly priced; alcohol is binary here -- the
      # collection holds no deliberate mocktails, so a zero is always a gap. The
      # day Helen adds one, saying "no alcohol" should be a deliberate sentence
      # rather than this line falling through to nothing.
      return nil if total.round(1).zero?

      # `serves` is absent on every drink that fills one glass. Absent means 1,
      # and a value below 1 would be a typo rather than a half-serving.
      n = serves.to_i
      n = 1 if n < 1

      {
        # Per serving, and to one decimal place -- Helen, 2026-09-06. A second
        # decimal would be claiming to know a pour to within a fifth of a
        # millilitre of ethanol, which no bar spoon delivers.
        "per_serve" => (total / n).round(1),
        # Kept for tests and for the punches, where the bowl's total is the
        # interesting number even though the page prints the serving.
        "total"     => total.round(1),
        "serves"    => n,
        # True when every alcoholic pour named a bottle whose strength is
        # declared. The layout prints "approx" when this is false.
        "exact"     => exact,
        "pours"     => pours,
        "filled"    => @abv["filled"]
      }
    end
  end
end
