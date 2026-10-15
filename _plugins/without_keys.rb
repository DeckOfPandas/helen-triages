# `{{ data | without_keys: "sources,note" }}`: the data with those keys removed
# at every depth, for a page that embeds a data file as JSON for its script.
#
# A page ships only what its script reads. Fields written for Helen (a source
# note, an unresolved safety flag) are not for a reader's view-source, and a
# key dropped here is one nobody has to remember to keep tidy in the data
# (#1387). The data file itself is never changed.

module HelenTriages
  module WithoutKeys
    def self.strip(value, keys)
      case value
      when Hash
        value.each_with_object({}) do |(k, v), out|
          out[k] = strip(v, keys) unless keys.include?(k.to_s)
        end
      when Array
        value.map { |v| strip(v, keys) }
      else
        value
      end
    end

    def without_keys(input, names)
      HelenTriages::WithoutKeys.strip(input, names.to_s.split(",").map(&:strip))
    end
  end
end

Liquid::Template.register_filter(HelenTriages::WithoutKeys)
