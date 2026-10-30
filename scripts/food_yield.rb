# frozen_string_literal: true

# Ask the build's two yield readers a question without building the site, which
# is the only other way to ask them. tests/test_food_yield.py runs this (#1286).
# Reads files in this repository (plus the one JSON file named), writes nothing.
#
#   ruby scripts/food_yield.rb "4–6 waffles, depending on your waffle iron" "950 ml"
#
# Prints one JSON object: each argument, and what _plugins/food_yield.rb makes
# of it under the vocabulary in _data/food/scaling.yml (null where the line
# does not open with a count of something named).
#
#   ruby scripts/food_yield.rb --half tmp/recipes.json
#
# Takes a JSON list of {"key", "makes", "serves", "ingredient_groups"} and prints per key {"made": ..., "half": {"ok": ...,
# "why": "..."}}: _plugins/food_half_recipe.rb's verdict on a half step.

require "json"
require "yaml"

root = File.expand_path("..", __dir__)
require File.join(root, "_plugins", "food_yield.rb")
require File.join(root, "_plugins", "food_half_recipe.rb")

scaling = YAML.safe_load(
  File.read(File.join(root, "_data", "food", "scaling.yml"), encoding: "utf-8")
)
vocab = scaling["yields"]

out = {}
if ARGV[0] == "--half"
  abort "usage: ruby scripts/food_yield.rb --half <file.json>" unless ARGV.length == 2
  JSON.parse(File.read(ARGV[1], encoding: "utf-8")).each do |recipe|
    stated = recipe["serves"].to_s[/\A\s*(\d+)/, 1]
    makes = recipe["makes"].to_s
    made = stated || makes.strip.empty? ? nil : HelenTriages::FoodYield.parse(makes, vocab)
    portions = stated ? stated.to_i : nil
    out[recipe["key"]] = {
      "made" => made,
      "half" => HelenTriages::HalfRecipe.judge(
        recipe["ingredient_groups"], made, portions,
        scaling["half_recipe"], scaling["half_step_measures"]
      )
    }
  end
else
  ARGV.each do |text|
    text = text.dup.force_encoding("utf-8")
    out[text] = HelenTriages::FoodYield.parse(text, vocab)
  end
end
puts JSON.generate(out)
