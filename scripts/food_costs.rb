# frozen_string_literal: true

# Ask _plugins/food_costs.rb which rate an ingredient name gets, without
# building the site. tests/test_food_costs.py runs this (#1458). Reads files in
# this repository, writes nothing.
#
#   ruby scripts/food_costs.rb "plain flour" "chicken stock" "[lemon curd](x)"
#
# Prints one JSON object: each argument and its rate (null where nothing
# matches). An argument shaped like a markdown link is treated as a
# cross-recipe link, as _plugins/food_shopping.rb marks one.

require "json"
require "yaml"

root = File.expand_path("..", __dir__)
module Jekyll
  class Generator
    def self.safe(*); end
    def self.priority(*); end
  end
end
module HelenTriages
  class FoodShopping
    COLLECTIONS = [].freeze
  end
end
require File.join(root, "_plugins", "food_costs.rb")

data = YAML.safe_load(File.read(File.join(root, "_data", "food", "costs.yml"), encoding: "utf-8"))
patterns = HelenTriages::FoodCosts.table(data)

out = {}
ARGV.each do |text|
  text = text.dup.force_encoding("utf-8")
  row = text.match?(/\A\[[^\]]+\]\(/) ? { "name" => text, "link" => true } : { "name" => text }
  out[text] = HelenTriages::FoodCosts.rate_for(row, patterns)
end
puts JSON.generate(out)
