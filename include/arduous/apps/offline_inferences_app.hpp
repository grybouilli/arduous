#pragma once

#include <arduous/api/arduous_plugin_api.hpp>
#include <arduous/apps/app_base.hpp>
#include <arduous/apps/offline_inference_options.hpp>
#include <cxxopts.hpp>
#include <nlohmann/json.hpp>
#include <ort_utils/ort_utils.hpp>
#include <string>

class OfflineInferenceApp : public AppBase {
    using json = nlohmann::json;

   public:
    OfflineInferenceApp() = delete;
    explicit OfflineInferenceApp(const cxxopts::ParseResult args);

    static auto get_options() {
        auto options = AppBase::get_options();
        auto adder   = options.add_options();

        adder(MODEL_TYPE_KEY_FULL, "The type of model to run (expected string)", cxxopts::value<std::string>());
        adder(INPUT_KEY_FULL, "The input audio path (expected .wav file)", cxxopts::value<std::string>())(
            OUTPUT_KEY_FULL,
            "The output path (expected folder path)",
            cxxopts::value<std::string>());
        adder(MODEL_CONFIG_KEY_FULL,
              "File containing the model I/O config entries (expected .json file)",
              cxxopts::value<std::string>());
        return options;
    }
    void run() final;

   private:
    void load_model_config(const std::string model_type, const std::string path_to_config);

    void save_audio_output(const arduous::ArduousOutputView& output);

   private:
    std::unique_ptr<arduous::ModelBase> _model;
    arduous::ModelIOConfig              _model_io_config;
    std::string                         _input_audio_path;
    std::string                         _output_audio_path;
    std::string                         _output_latencies_path;
};