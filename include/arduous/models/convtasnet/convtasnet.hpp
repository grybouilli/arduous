#pragma once

#include <arduous/api/arduous_model_io_config.hpp>
#include <arduous/api/arduous_plugin_api.hpp>
#include <ort_utils/ort_tensor_buffer.hpp>

namespace arduous {

class Convtasnet : public ModelBaseWithCPUMemory {
   public:
    Convtasnet(Ort::Session& session, const ModelIOConfig io_config) :
        ModelBaseWithCPUMemory(session, io_config),
        _input{_memory_info, {1, io_config.audio_in.length}},
        _output{_memory_info, {1, io_config.audio_out.channels, io_config.audio_out.length}} {
        try {
            _binding.BindInput("input", _input.tensor);
            _binding.BindOutput("output", _output.tensor);

            _input_name  = "input";
            _output_name = "output";
        } catch (Ort::Exception& e) {
            _binding.ClearBoundInputs();
            _binding.ClearBoundOutputs();
            _binding.BindInput("x", _input.tensor);
            _binding.BindOutput("y", _output.tensor);

            _input_name  = "x";
            _output_name = "y";
        }
    }

   protected:
    int do_process(const ArduousInputView& input, ArduousOutputView& output) final {
        static const auto output_chunk_length = _output.shape[2];

        _input.copy_from({input.data, input.frames});
        _binding.ClearBoundInputs();
        _binding.ClearBoundOutputs();
        _binding.BindInput(_input_name.c_str(), _input.tensor);
        _binding.BindOutput(_output_name.c_str(), _output.tensor);

        _session.Run(Ort::RunOptions{nullptr}, _binding);

        std::memcpy(output.data, _output.buffer_memory.data(), output_chunk_length * sizeof(float));
        std::memcpy(output.data + output_chunk_length,
                    _output.buffer_memory.data() + output_chunk_length,
                    output_chunk_length * sizeof(float));

        output.frames_written = _output.buffer_memory.size();
        return _output.buffer_memory.size();
    }

   private:
    ort_tensor_buffer<float, 2> _input;
    ort_tensor_buffer<float, 3> _output;

    std::string _input_name;
    std::string _output_name;
};

}  // namespace arduous
