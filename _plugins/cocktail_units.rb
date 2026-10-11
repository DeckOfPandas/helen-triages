# UK units and millilitres in a drink (#297, #1121). Data: _data/cocktails/abv.yml.
#
#   units = sum over pours of (ml x abv / 1000)
#
# Dilution is not modelled: water adds no alcohol. The sibling of
# cocktail_costs.rb (same alias map, exclusions and `default_bottles`), except:
# - only a pour that contains alcohol can make the figure inexact.
# - units are per serving, so the figure does not scale and the page carries
#   no data attribute for the scaler to touch. `serves:` absent means 1.
# - a generic in ingredients.yml's `bitters:` list never counts (#1012).
# - a category's strength is one figure, not a range: `generic_abv` (#1016).
# `page.volume` is a separate key from `page.units` because the two withhold
# independently; both spend the same `top_up_ml`.

require "set"
require_relative "amount"

module HelenTriages
  class CocktailUnits < Jekyll::Generator
    safe true
    priority :normal

    COLLECTIONS = %w[cocktail_recipes cocktail_drafts].freeze

    # A UK unit is 10 ml of pure ethanol, so units = ml * abv / 1000 with abv in
    # percent.
    ML_PER_UNIT = 1000.0

    def generate(site)
      @abv    = site.data.dig("cocktails", "abv")
      costs   = site.data.dig("cocktails", "costs")
      @ing    = site.data.dig("cocktails", "ingredients")
      bottles = site.data.dig("cocktails", "bottles")
      return unless @abv && costs && @ing && bottles

      @per_ml   = @ing["measures"]["per_ml"]
      @ignored  = @ing["measures"]["ignored_words"] || []

      # The exclusion rule and the top-up ranges are read from costs.yml, not
      # restated, so this file and cocktail_costs.rb cannot disagree.
      @excluded = (costs["excluded_units"] || []).to_set
      @top_up   = costs["top_up_ml"] || {}
      @defaults = costs["default_bottles"] || {}

      # Glass capacities and fill rules (#1179), read only by `fitted_top_ml`.
      # With no glasses.yml every top falls back to its house range.
      glasses   = site.data.dig("cocktails", "glasses") || {}
      @icons    = glasses["icons"] || {}
      @survey_only = glasses["survey_only_types"] || {}
      @typical  = glasses["typical_ml"] || {}
      @fit      = glasses["fit_rules"]

      @non_alcoholic = (@abv["non_alcoholic"] || []).to_set
      @bitters = (@ing["bitters"] || []).to_set

      # Units declared not to be a volume. A different list from `excluded_units`
      # above, which is costing's: this one answers "is this pour deliberately
      # outside a volume, or is it a gap?".
      @non_volumetric = ((@ing["measures"] || {})["non_volumetric"] || []).to_set

      @alias = {}
      @by_generic = Hash.new { |h, k| h[k] = [] }
      bottles["bottles"].each do |name, b|
        @alias[name.downcase] = name
        Array(b && b["aliases"]).each { |a| @alias[a.to_s.downcase] = name }
        @by_generic[b && b["generic"]] << name
      end

      counted = 0
      approximate = 0
      measured = 0
      withheld = 0
      from_glass = 0
      from_range = 0
      COLLECTIONS.each do |key|
        next unless site.collections[key]
        site.collections[key].docs.each do |doc|
          # Asked once per drink and handed to both sums, so the unit count and the
          # volume cannot disagree about what the top pours.
          fitted = fitted_top_ml(doc.data)

          units = units_for(doc.data["ingredients"], doc.data["serves"], fitted)
          if units
            doc.data["units"] = units
            counted += 1
            approximate += 1 unless units["exact"]
          end

          volume = volume_for(doc.data["ingredients"], doc.data["serves"], fitted)
          if volume
            if volume["top_ml"]
              volume["top_from"] = fitted ? "glass" : "range"
              fitted ? from_glass += 1 : from_range += 1
            end
            # The dilution family the method reads as, for
            # scripts/glass_fit_report.py -- one reading of a method, here,
            # rather than a second one in Python.
            volume["method_family"] = method_family(doc.data["method"])
            # What was never shaken or stirred, for the same reader -- #1244.
            after, aside = added_after_ml(doc.data)
            volume["after_ml"] = tidy_ml(after) if after.positive?
            volume["aside_ml"] = tidy_ml(aside) if aside.positive?
            doc.data["volume"] = volume
            measured += 1
          else
            withheld += 1
          end
        end
      end
      Jekyll.logger.info "Units:", "counted #{counted} drinks " \
        "(#{approximate} approximate, abv filled #{@abv['filled']})"
      Jekyll.logger.info "Tops:", "#{from_glass} sized from the glass, " \
        "#{from_range} from the house range (no glass, no serve, or no room)"
      # `withheld` is expected to be non-zero: see `volume_for`.
      Jekyll.logger.info "Volume:", "measured #{measured} drinks " \
        "(#{withheld} withheld -- the excluded pours ARE the drink)"
    end

    private

    # Percent ABV for one declared bottle, or nil if it carries none.
    def bottle_abv(name)
      row = @abv["bottles"][name]
      row && row["abv"] && row["abv"].to_f
    end

    # Percent ABV for a generic, or nil if nothing gives it one. A
    # `default_bottles` entry in costs.yml decides the category (two bottles are
    # averaged). Without one it is the mode of the declared bottles (#1016). The
    # mean is a last resort that keeps a page building:
    # test_every_bottled_generic_resolves_to_one_strength fails when a category
    # has no single mode and no default.
    def generic_abv(g)
      return 0.0 if @non_alcoholic.include?(g)

      if @defaults[g]
        vals = @defaults[g].map { |n| bottle_abv(n) }.compact
        return vals.sum / vals.size unless vals.empty?
      else
        vals = @by_generic[g].map { |n| bottle_abv(n) }.compact
        unless vals.empty?
          mode = self.class.unique_mode(vals)
          return mode || vals.sum / vals.size
        end
      end

      row = @abv["generics"][g]
      row && row["abv"] && row["abv"].to_f
    end

    # The single most common value, or nil when there is none -- a tie at the
    # top, or (the same thing) every value different. A class method so the
    # test can ask the plugin's own question rather than re-implementing it.
    def self.unique_mode(vals)
      counts = vals.tally
      top = counts.values.max
      winners = counts.select { |_, c| c == top }.keys
      winners.size == 1 ? winners.first : nil
    end

    # Millilitres for an amount string, or nil when the pour does not count.
    # Identical to cocktail_costs.rb's; `to top` is handled by the caller.
    def volume_ml(amount)
      a = amount.to_s.strip
      return nil if @excluded.include?(a)
      number, unit = Amount.parse(a, @ignored)
      return nil if number.nil? || @excluded.include?(unit) || !@per_ml.key?(unit)
      number * @per_ml[unit].to_f
    end

    # (number, unit) for an amount string: `[52.5, "ml"]`, `[1, "whole"]`,
    # `[nil, "(top)"]` for a bare unit. `volume_for` needs the unit and not only
    # `volume_ml`'s nil, to tell a declared non-volume from an unreadable amount.
    def unit_named(amount)
      Amount.parse(amount, @ignored)
    end

    # What a `(top)` pours: `fitted`, the glass's answer (#1179), or else the
    # midpoint of the range costs.yml `top_up_ml` declares. Nil when no range is
    # declared, even if `fitted` is given: an undeclared topper stays a gap
    # (test_top_up_volumes_cover_every_to_top_pour). One expression for
    # `units_for` and `volume_for`, so the two cannot disagree. `.max` across a
    # list generic: "either would do" (#441), and the largest top fills the glass.
    def top_up_ml(generics, fitted = nil)
      tops = Array(generics).filter_map { |g| @top_up[g] }
      return nil if tops.empty?
      return fitted if fitted
      tops.map { |t| (t["ml_min"].to_f + t["ml_max"].to_f) / 2.0 }.max
    end

    # What a `(top)` pours, from the glass it is poured into (#1179): the glass
    # to its wash line, less the room the serving ice takes, less the build once
    # shaking or stirring has watered it. Figures are glasses.yml `typical_ml`
    # (the median) and the low end of each `fit_rules` range, the same reading
    # scripts/glass_fit_report.py takes. Rounded to 5 ml. The first glass listed
    # is the glass. Nil, so the house midpoint stands, when there is no
    # `serve.ice`, no surveyed glass, a punch bowl, `serves:` above 1, more than
    # one `(top)`, or a build that already fills the glass.
    def fitted_top_ml(data)
      return nil unless @fit
      ingredients = data["ingredients"]
      return nil unless ingredients.is_a?(Array)
      return nil if data["serves"].to_i > 1

      serve = data["serve"]
      return nil unless serve.is_a?(Hash) && serve["ice"]
      ice = serve["ice"].to_s

      glass = Array(data["glass"]).first.to_s.downcase
      key = glass_key(glass)
      return nil if key.nil? || key == "punch-bowl"
      stats = @typical[key] or return nil

      tops = 0
      build = 0.0
      ingredients.each do |ing|
        next unless ing.is_a?(Hash)
        number, unit = unit_named(ing["amount"].to_s.strip)
        if unit == "(top)"
          tops += 1
        elsif number && @per_ml.key?(unit)
          build += number * @per_ml[unit].to_f
        end
      end
      return nil unless tops == 1

      family = method_family(data["method"])
      room = glass_room(stats["median"].to_f, ice, family, key, serve["fill"])
      # Only what went through the shaker is watered -- `added_after_ml`.
      after, aside = added_after_ml(data)
      top = room - (served_ml(build - after - aside, family) + after)
      rounded = (top / 5.0).round * 5
      rounded.positive? ? rounded.to_f : nil
    end

    # The key `typical_ml` files a glass under: its icon, or a
    # `survey_only_types` entry where one drawing has two sizes.
    def glass_key(glass)
      @survey_only.each do |key, spec|
        return key if Array(spec && spec["spellings"]).include?(glass)
      end
      @icons[glass]
    end

    # The dilution family a method reads as; first match wins. A heuristic over
    # the method's verbs. scripts/glass_fit_report.py reads this answer off the
    # built page as `data-method-family` and must not keep its own. Blend first
    # (a frozen drink may be shaken too). A short shake, a whip, or a shake
    # "with a few" pieces of ice anywhere in its sentence is the light one. A
    # shake whose every mention is `dry` gets its own family. A pitcher filled
    # with ice and stirred is a stir.
    def method_family(steps)
      text = Array(steps).map { |s| s.to_s.downcase }.join(" ")
      return "blended" if text.include?("blend")
      return "short_shake" if text.match?(/short shake|whip|shake\b[^.]*\bwith (a few|three)/)
      return "shake" if text.match?(/(?<!dry )shake/)
      return "dry_shake_only" if text.include?("dry shake")
      return "stir" if text.match?(/stir[^.]*with ice|pitcher[^.]*ice/)
      return "swizzle" if text.include?("swizzle")
      "build"
    end

    # What was never shaken (#1244): [after, aside] in millilitres, for the
    # glass-fit question only. The volume the page prints is untouched.
    #   after -- in the glass, undiluted: an `as: "float"` amount, or one a step
    #            holds back ("Shake all ingredients other than the champagne").
    #   aside -- not in the glass: an `as: "shell"` rum.
    # An amount held back and never mentioned again still counts as in the glass.
    # A method's name is shorter than the generic ("the sherry"), so an amount is
    # held back when either string contains the other.
    def added_after_ml(data)
      ingredients = data["ingredients"]
      return [0.0, 0.0] unless ingredients.is_a?(Array)

      steps = Array(data["method"]).map do |s|
        (s.is_a?(Hash) ? s["step"] : s).to_s.downcase
      end
      held = []
      steps.each_with_index do |step, index|
        m = /other than (.*?)(?: with |\.|\z)/.match(step) or next
        m[1].split(/,| and /).each do |phrase|
          phrase = phrase.strip.sub(/\Athe /, "").sub(/\Arest of the /, "")
          held << [phrase, index] unless phrase.empty?
        end
      end

      after = 0.0
      aside = 0.0
      ingredients.each do |ing|
        next unless ing.is_a?(Hash)
        number, unit = unit_named(ing["amount"].to_s.strip)
        next unless number && @per_ml.key?(unit)
        ml = number * @per_ml[unit].to_f

        case ing["as"].to_s
        when "float"
          after += ml
          next
        when "shell"
          aside += ml
          next
        end

        generics = Array(ing["generic"]).map { |g| g.to_s.downcase }
                                        .reject(&:empty?)
        hit = held.find do |phrase, _|
          generics.any? { |g| g.include?(phrase) || phrase.include?(g) }
        end
        next unless hit

        after += ml
      end
      [after, aside]
    end

    # Millilitres of drink a glass of this capacity takes, on the forgiving
    # end. The same sum as `room` in scripts/glass_fit_report.py, which keeps
    # its own because it asks it of three capacities (min, median, max) and
    # this asks it of one.
    def glass_room(capacity, ice, family, key, fill)
      return capacity if family == "blended"
      stemmed = Array(@fit["stemmed"]).include?(key)
      wash = capacity * @fit["washline"][stemmed ? "stemmed" : "tumbler"].to_f
      if @fit["ice_space"].key?(ice)
        space = @fit["ice_space"][ice]["low"].to_f
        space *= @fit["half_fill"].to_f if fill.to_s == "half"
        return wash * (1 - space)
      end
      return wash - @fit["large_cube_ml"]["low"].to_f if ice == "large cube"
      wash
    end

    # What the build becomes in the glass, on the forgiving end.
    def served_ml(build, family)
      return build * @fit["blended_multiplier"]["low"].to_f if family == "blended"
      build * (1 + @fit["dilution"][family]["low"].to_f)
    end

    # One decimal place, and an Integer where the figure is whole: Liquid prints
    # the Float 90.0 as "90.0" and the page wants "90 ml".
    def tidy_ml(ml)
      v = ml.round(1)
      v == v.to_i ? v.to_i : v
    end

    # How much liquid is in a drink (#1121). `total_ml` is the recipe as written
    # and the scaler multiplies it; `serve_ml` is one glass. Computed here, where
    # every amount is already parsed, so the browser does no volume arithmetic of
    # its own. A unit in `measures.non_volumetric` is skipped. A `(top)` takes
    # `top_up_ml`. Returns nil, because the figure would be wrong and not merely
    # rough, when the excluded pours are the drink (the test cocktail_costs.rb
    # applies for `cost.complete`), when an amount cannot be read, or when a
    # topper has no declared range.

    # `serve_ml` divides the whole total by `serves:`, top included, which is
    # wrong for a topped punch: a top fills one glass. No topped drink declares
    # `serves:`; tests/test_rendered_pages.py::test_no_topped_drink_is_also_a_punch
    # keeps it so.
    def volume_for(ingredients, serves, fitted = nil)
      return nil unless ingredients.is_a?(Array) && !ingredients.empty?

      total = 0.0
      top = nil
      pours = 0
      substantial = 0

      ingredients.each do |ing|
        next unless ing.is_a?(Hash)
        amount = ing["amount"].to_s.strip
        number, unit = unit_named(amount)

        # A topper with no declared range withholds the whole figure: a missing top
        # is most of the drink. (`units_for` skips such a pour instead.)
        if unit == "(top)"
          topped = top_up_ml(Array(ing["generic"]).map(&:to_s), fitted)
          return nil if topped.nil?
          total += topped
          top = (top || 0.0) + topped
          pours += 1
          next
        end

        if number && @per_ml.key?(unit)
          total += number * @per_ml[unit].to_f
          pours += 1
          next
        end

        if @non_volumetric.include?(unit)
          # An ingredient-sized exclusion; see `substantial < pours` below.
          substantial += 1 if CocktailCosts::SUBSTANTIAL.match?(amount)
          next
        end

        # Neither a volume nor a declared non-volume: a gap, not a zero
        # (test_every_amount_is_readable_as_a_quantity, #571).
        return nil
      end

      return nil if pours.zero?
      return nil unless substantial < pours

      n = serves.to_i
      n = 1 if n < 1

      {
        # How much of the total is a `(top)`, or nil on a drink with none.
        # Unprinted: scripts/glass_fit_report.py takes it back out of the
        # total to judge the build on its own.
        "top_ml"   => top && tidy_ml(top),
        # The recipe as written. The scaler multiplies this and nothing else.
        "total_ml" => tidy_ml(total),
        # One glass, and the figure the units line prints beside a per-serving
        # unit count. `serves` is absent on every drink that fills one glass.
        "serve_ml" => tidy_ml(total / n),
        "serves"   => n,
        "pours"    => pours
      }
    end

    def units_for(ingredients, serves, fitted = nil)
      return nil unless ingredients.is_a?(Array) && !ingredients.empty?

      total = 0.0
      exact = true
      pours = 0

      ingredients.each do |ing|
        next unless ing.is_a?(Hash)
        amount = ing["amount"].to_s.strip
        generics = Array(ing["generic"]).map(&:to_s)

        # Bitters never count (#1012). Skipped on the generic, before the amount is
        # parsed, so a bitters in millilitres is excluded too.
        next if !generics.empty? && generics.all? { |g| @bitters.include?(g) }

        # How much liquid, if any. A `(top)` is an estimate, and makes the drink
        # approximate only if what tops it contains alcohol.
        topped = false
        if amount == "(top)"
          ml = top_up_ml(generics, fitted)
          next if ml.nil?
          topped = true
        else
          ml = volume_ml(amount)
          next if ml.nil?
        end

        # At what strength. A named bottle wins, and is the only thing that can be
        # exact.
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

      # A zero is withheld: the collection holds no deliberate mocktails, so 0.0
      # means the alcohol is not recorded, and "0.0 units" would read as
      # alcohol-free.
      return nil if total.round(1).zero?

      # `serves` is absent on every drink that fills one glass. Absent means 1,
      # and a value below 1 would be a typo rather than a half-serving.
      n = serves.to_i
      n = 1 if n < 1

      {
        # Per serving, to one decimal place.
        "per_serve" => (total / n).round(1),
        # Kept for tests and for the punches, where the bowl's total is the
        # interesting number even though the page prints the serving.
        "total"     => total.round(1),
        "serves"    => n,
        # True when every alcoholic pour named a bottle whose strength is declared.
        # No template reads it.
        "exact"     => exact,
        "pours"     => pours,
        "filled"    => @abv["filled"]
      }
    end
  end
end
