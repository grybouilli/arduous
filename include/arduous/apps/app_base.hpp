#pragma once

#include <arduous/apps/apps_options.hpp>
#include <arduous/utils/json_utils.hpp>
#include <cxxopts.hpp>
#include <ort_utils/ort_session_handler.hpp>

class AppBase {
   public:
    AppBase() = delete;
    AppBase(const cxxopts::ParseResult args) :
        _session_handler{args[MODEL_FILENAME_KEY].as<std::string>(),
                         args[EP_NAME_KEY].as<std::string>(),
                         json_from_filename(args[EP_CONFIG_KEY].as<std::string>()),
                         get_session_config(args),
                         "arduous_app"} {}

    AppBase(const std::string                                   model_filename,
            const std::string                                   ep_name,
            const std::unordered_map<std::string, std::string>& ep_options     = {},
            const std::unordered_map<std::string, std::string>& config_entries = {},
            const std::string                                   log_name       = "arduous_app\n") :
        _session_handler{model_filename, ep_name, ep_options, config_entries, log_name} {}

    virtual ~AppBase() {}

    static auto get_options() {
        cxxopts::Options options{"arduous_offline", "Offline inferences arduous app"};
        auto             adder = options.add_options();
        adder("h,help", "Print usage");
        adder(MODEL_FILENAME_KEY_FULL,
              "File containing the model to load (expected .onnx file)",
              cxxopts::value<std::string>());
        adder(EP_NAME_KEY_FULL, "ONNX Runtime EP name (expected string)", cxxopts::value<std::string>());
        adder(EP_CONFIG_KEY_FULL, "File containing the EP config (expected .json file)", cxxopts::value<std::string>());
        adder(ARGS_FROM_FILE_KEY_FULL,
              "File containing argument values for the app (expected .json file)",
              cxxopts::value<std::string>());
        adder(SESSION_CONFIG_KEY_FULL,
              "File containing the session config entries (expected .json file)",
              cxxopts::value<std::string>()->default_value(""));
        return options;
    }

    static std::pair<size_t, std::vector<std::string>> get_options_from_config_file(cxxopts::ParseResult& args) {
        // load json file
        // loop through expected arguments of args
        // fill in those that are provided by json file
        auto                     args_from_file = json_from_filename(args[ARGS_FROM_FILE_KEY].as<std::string>());
        std::vector<std::string> new_command_line;
        size_t                   new_argc = 0;
        for (const auto [key, value] : args_from_file.items()) {
            const std::string v = value.get<std::string>();
            if (std::find_if(args.arguments().begin(), args.arguments().end(), [key](const auto& kv) {
                    return kv.key() == key;
                }) == args.arguments().end()) {
                new_command_line.push_back(std::format("--{}", key));
                new_command_line.push_back(std::format("{}", v));
                new_argc += 2;
            }
        }
        for (const auto& elem : args.arguments()) {
            new_command_line.push_back(std::format("--{}", elem.key()));
            new_command_line.push_back(std::format("{}", elem.value()));
            new_argc += 2;
        }

        return std::make_pair(new_argc, new_command_line);
    }

    virtual void run() = 0;

   protected:
    static std::unordered_map<std::string, std::string> get_session_config(const cxxopts::ParseResult args) {
        return (args.count(SESSION_CONFIG_KEY) > 0) ? json_from_filename(args[SESSION_CONFIG_KEY].as<std::string>())
                                                          .get<std::unordered_map<std::string, std::string>>()
                                                    : std::unordered_map<std::string, std::string>{};
    }

   protected:
    OrtSessionHandler _session_handler;
};