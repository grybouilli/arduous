#pragma once

#include <arduous/api/arduous_model_io_config.hpp>
#include <arduous/api/arduous_plugin_api.hpp>
#include <ort_utils/ort_tensor_buffer.hpp>

namespace arduous {

class StreamableConvtasnet : public ModelBaseWithCPUMemory {
   public:
    StreamableConvtasnet(Ort::Session& session, const ModelIOConfig io_config) :
        ModelBaseWithCPUMemory(session, io_config),
        _input{_memory_info, {1, io_config.audio_in.length}},
        _output{_memory_info, {1, io_config.audio_out.channels, io_config.audio_out.length}},
        _input_head_buffer{_memory_info, {1, 1, 32}},
        _tcn_states{_memory_info, {1, 512, 180}},
        _tail_buffer{_memory_info, {1, 2, 32}} {}

   protected:
    int do_process(const ArduousInputView& input, ArduousOutputView& output) final {
        static const auto output_chunk_length = _output.shape[2];

        ort_tensor_buffer<float, 3> next_head_buffer{_memory_info, std::array<int64_t, 3>(_input_head_buffer.shape)};
        ort_tensor_buffer<float, 3> next_tcn_states{_memory_info, std::array<int64_t, 3>(_tcn_states.shape)};
        ort_tensor_buffer<float, 3> next_tail_buffer{_memory_info, std::array<int64_t, 3>(_tail_buffer.shape)};

        _input.copy_from({input.data, input.frames});
        _binding.ClearBoundInputs();
        _binding.ClearBoundOutputs();
        _binding.BindInput("x", _input.tensor);
        _binding.BindInput("audio_states", _input_head_buffer.tensor);
        _binding.BindInput("tcn_states", _tcn_states.tensor);
        _binding.BindInput("tail_states", _tail_buffer.tensor);
        _binding.BindOutput("y", _output.tensor);
        _binding.BindOutput("next_audio_states", next_head_buffer.tensor);
        _binding.BindOutput("next_tcn_states", next_tcn_states.tensor);
        _binding.BindOutput("next_tail_states", next_tail_buffer.tensor);

        _session.Run(Ort::RunOptions{nullptr}, _binding);

        _input_head_buffer.copy_from(next_head_buffer);
        _tcn_states.copy_from(next_tcn_states);
        _tail_buffer.copy_from(next_tail_buffer);

        std::memcpy(output.data, _output.buffer_memory.data(), output_chunk_length * sizeof(float));
        std::memcpy(output.data + output_chunk_length,
                    _output.buffer_memory.data() + output_chunk_length,
                    output_chunk_length * sizeof(float));

        return _output.buffer_memory.size();
    }

   private:
    ort_tensor_buffer<float, 2> _input;
    ort_tensor_buffer<float, 3> _input_head_buffer;
    ort_tensor_buffer<float, 3> _tcn_states;
    ort_tensor_buffer<float, 3> _tail_buffer;
    ort_tensor_buffer<float, 3> _output;
};

}  // namespace arduous
