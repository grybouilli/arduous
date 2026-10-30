#include <arduous/api/arduous_model_io_config.hpp>
#include <arduous/api/arduous_plugin_api.hpp>
#include <arduous/apps/offline_inferences_app.hpp>
#include <arduous/utils/json_utils.hpp>
#include <filesystem>
#include <format>
#include <magic_enum/magic_enum.hpp>
#include <sndfile_wrapper/sndfile_wrapper.hpp>

namespace fs = std::filesystem;

OfflineInferenceApp::OfflineInferenceApp(const cxxopts::ParseResult args) :
    AppBase(args),
    _input_audio_path{args[INPUT_KEY].as<std::string>()},
    _output_audio_path{args[OUTPUT_KEY].as<std::string>()} {
    load_model_config(args[MODEL_TYPE_KEY].as<std::string>(), args[MODEL_CONFIG_KEY].as<std::string>());
}

void OfflineInferenceApp::run() {
    // Open audio file
    SoundFileReader<float, SF_FORMAT_WAV> input_audio{_input_audio_path,
                                                      _model_io_config.sample_rate,
                                                      _model_io_config.audio_in.channels};

    // prepare I/O buffers
    std::vector<float> in_buffer(_model_io_config.audio_in.length, 0.f);
    std::vector<float> output(_model_io_config.audio_out.channels * input_audio.frames(), 0.f);

    arduous::ArduousInputView  model_in_buffer;
    arduous::ArduousOutputView model_out_buffer;

    model_in_buffer.data        = in_buffer.data();
    model_in_buffer.channels    = input_audio.channels();
    model_in_buffer.frames      = 0;
    model_in_buffer.sample_rate = input_audio.sample_rate();
    model_in_buffer.layout      = _model_io_config.audio_in.layout;

    model_out_buffer.data        = output.data();
    model_out_buffer.channels    = _model_io_config.audio_out.channels;
    model_out_buffer.sample_rate = _model_io_config.sample_rate;
    model_out_buffer.layout      = _model_io_config.audio_out.layout;

    // run inferences
    // mesure latencies
    int frame_count = 0;
    while ((model_in_buffer.frames = input_audio.read(in_buffer.data(), _model_io_config.audio_in.length)) > 0) {
        frame_count++;
        if (model_in_buffer.frames < _model_io_config.audio_in.length) {
            std::fill(in_buffer.begin() + model_in_buffer.frames, in_buffer.end(), 0.0f);
            model_in_buffer.frames = _model_io_config.audio_in.length;
        }
        _model->process(model_in_buffer, model_out_buffer);

        // make the buffer point to the next available frame
        model_out_buffer.data += model_out_buffer.layout == arduous::ChannelLayout::Planar
                                     ? model_out_buffer.frames_written / model_out_buffer.channels
                                     : model_out_buffer.frames_written;
    }
    std::cout << std::format("Treated {} frames of length {}\n", frame_count, _model_io_config.audio_in.length);
    // save audio output(s)
    model_out_buffer.data           = output.data();  // point back to the beginning
    model_out_buffer.frames_written = output.size();
    save_audio_output(model_out_buffer);
    // save latencies
}

void OfflineInferenceApp::save_audio_output(const arduous::ArduousOutputView& output) {
    if (output.layout == arduous::ChannelLayout::Planar) {
        const size_t channel_length = output.frames_written / output.channels;
        for (auto channel = 0; channel < output.channels; ++channel) {
            fs::path filename = fs::path(_output_audio_path) / std::format("output_channel_{}.wav", channel);
            SoundFileWriter<float, SF_FORMAT_WAV> writer{filename.c_str(), (int)output.sample_rate, 1};
            writer.write(output.data + channel_length * channel, channel_length);
        }
    } else {
        fs::path                              filename = fs::path(_output_audio_path) / "output.wav";
        SoundFileWriter<float, SF_FORMAT_WAV> writer{filename.c_str(), (int)output.sample_rate, (int)output.channels};
        writer.write(output.data, output.frames_written);
    }
}

void OfflineInferenceApp::load_model_config(const std::string model_type, const std::string path_to_config) {
    auto io_config   = json_from_filename(path_to_config);
    _model_io_config = io_config.get<arduous::ModelIOConfig>();
    _model           = arduous::Factory::create(model_type)(_session_handler.session(), io_config);
}