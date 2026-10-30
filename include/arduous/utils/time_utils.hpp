#pragma once

#include <chrono>
/**
 * @brief From gul14 (https://github.com/gul-cpp/gul14/blob/main/include/gul14/time_util.h)
 *
 * @return std::chrono::steady_clock::time_point
 */
inline std::chrono::steady_clock::time_point tic() { return std::chrono::steady_clock::now(); }

/**
 * @brief From gul14 (https://github.com/gul-cpp/gul14/blob/main/include/gul14/time_util.h)
 *
 * @tparam TimeUnitType
 * @param t0
 * @return auto
 */
template <class TimeUnitType = std::chrono::milliseconds>
auto toc(std::chrono::steady_clock::time_point t0) {
    return std::chrono::duration_cast<TimeUnitType>(tic() - t0).count();
}