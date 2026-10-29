#pragma once

#include <nlohmann/json.hpp>
#include <string>

nlohmann::json json_from_filename(const std::string filename);