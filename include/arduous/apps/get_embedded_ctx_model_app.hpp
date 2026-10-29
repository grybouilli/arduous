#pragma once

#include <arduous/apps/app_base.hpp>

#define CTX_OUTPUT_FILENAME      "o"
#define CTX_OUTPUT_FILENAME_LONG "model_ctx_out"
#define CTX_OUTPUT_FILENAME_FULL (CTX_OUTPUT_FILENAME "," CTX_OUTPUT_FILENAME_LONG)

class GetEmbeddedCtxModelApp : public AppBase {
   public:
    GetEmbeddedCtxModelApp() = delete;
    GetEmbeddedCtxModelApp(const cxxopts::ParseResult args) :
        AppBase(args[MODEL_FILENAME_KEY].as<std::string>(),
                args[EP_NAME_KEY].as<std::string>(),
                json_from_filename(args[EP_CONFIG_KEY].as<std::string>()),
                get_session_config(args),
                "arduous_ctx_app"),
        _path_to_ctx{args[CTX_OUTPUT_FILENAME].as<std::string>()} {}

    static auto get_options() {
        auto options = AppBase::get_options();
        auto adder   = options.add_options();
        adder(CTX_OUTPUT_FILENAME_FULL,
              "The output path to which to save the compiled model (exptected .onnx)",
              cxxopts::value<std::string>());
        return options;
    }
    void run() final {
        std::cout << "Model was compiled and saved to " << _path_to_ctx << std::endl;
    }

   private:
    static std::unordered_map<std::string, std::string> get_session_config(const cxxopts::ParseResult args) {
        auto config_entries                                            = AppBase::get_session_config(args);
        config_entries[kOrtSessionOptionEpContextEnable]    = "1";
        config_entries[kOrtSessionOptionEpContextEmbedMode] = "1";
        config_entries[kOrtSessionOptionEpContextFilePath]  = args[CTX_OUTPUT_FILENAME].as<std::string>();

        return config_entries;
    }

    std::string _path_to_ctx;
};