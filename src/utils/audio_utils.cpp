#include <algorithm>
#include <span>

void peak_normalize(std::span<float> values, const float max_val) {
    if (values.empty()) {
        return;
    }

    const auto seq_max_val = *std::ranges::max_element(values);

    std::ranges::for_each(values, [seq_max_val, max_val](auto& value) { value = max_val * (value / seq_max_val); });
}