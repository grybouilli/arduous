
#include <fstream>
#include <nlohmann/json.hpp>
#include <string>

nlohmann::json json_from_filename(const std::string filename) {
    std::ifstream f(filename);
    return nlohmann::json::parse(f,
                                 /* callback */ nullptr,
                                 /* allow exceptions */ true,
                                 /* ignore_comments */ true);
}