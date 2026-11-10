#pragma once

#include <span>

void peak_normalize(std::span<float> values, const float max_val = 1.f);