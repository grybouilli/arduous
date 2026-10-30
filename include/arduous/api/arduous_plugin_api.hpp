/**
 * @file arduous_plugin_api.hpp
 * @brief API definitions for the Arduous plugin interface.
 */
#pragma once

#include <onnxruntime_cxx_api.h>

#include <format>
#include <memory>
#include <nlohmann/json.hpp>
#include <span>
#include <stdexcept>

namespace arduous {

/**
 * @brief Enumeration for channel layout configurations.
 */
enum ChannelLayout { Interleaved, Planar, Total };

NLOHMANN_JSON_SERIALIZE_ENUM(ChannelLayout,
                             {
                                 {ChannelLayout::Planar, "Planar"},
                                 {ChannelLayout::Interleaved, "Interleaved"},
                             })

struct IOAudioConfig {
    int           channels;
    int           length;
    ChannelLayout layout;
};

struct ModelIOConfig {
    IOAudioConfig audio_in;
    IOAudioConfig audio_out;
    int           sample_rate;
};

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(IOAudioConfig, channels, length, layout)
NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(ModelIOConfig, audio_in, audio_out, sample_rate)

/**
 * @brief Structure representing the input view for audio data in an interleaved or planar format.
 */
struct ArduousInputView {
    const float*  data;         ///< Pointer to the interleaved or planar audio data.
    size_t        frames;       ///< Number of audio frames.
    uint32_t      channels;     ///< Number of audio channels.
    uint32_t      sample_rate;  ///< Sample rate of the audio.
    ChannelLayout layout;       ///< Layout of the audio data (Interleaved, Planar, or Total).
};

/**
 * @brief Structure representing the output view for audio data.
 */
struct ArduousOutputView {
    float*   data;             ///< Pointer to the output audio data.
    size_t   capacity_frames;  ///< Maximum capacity of the output buffer in frames.
    size_t   frames_written;   // set by plugin ///< Number of frames that have been written to the output buffer by the
                               // plugin.
    uint32_t channels;         ///< Number of audio channels.
    uint32_t sample_rate;      ///< Sample rate of the output audio.
    ChannelLayout layout;      ///< Layout of the output audio data (Interleaved, Planar, or Total).
};

/**
 * @brief Base class for model processing operations.
 */
class ModelBase {
   public:
    /**
     * @brief Constructor for ModelBase.
     * @param session Reference to the ONNX Runtime session.
     * @param io_config Input/Output configuration.
     */
    ModelBase(Ort::Session& session, const ModelIOConfig io_config) : _session(session), _io_config{io_config} {}

    /**
     * @brief Virtual destructor for polymorphic behavior.
     */
    virtual ~ModelBase() = default;

    /**
     * @brief Processes input audio data according to the model logic.
     * @param input The input view of the audio data.
     * @param output Reference to the output view where results will be written.
     * @return The amount of samples written in output
     */
    [[nodiscard]] int process(const ArduousInputView& in, ArduousOutputView& out) { return do_process(in, out); }
    /**
     * @brief Processes raw audio data directly from a span.
     * @param audio The audio data as a contiguous memory span.
     * @return The amount of samples written in output
     */
    [[nodiscard]] int process(std::span<float> audio) { return do_process(audio); }
    /**
     * @brief Processes raw pointer and sample count for audio data.
     * @param audio Pointer to the audio data.
     * @param samples The number of audio samples.
     * @return The amount of samples written in output
     */
    [[nodiscard]] int process(float* audio, std::size_t n) { return do_process(std::span<float>{audio, n}); }

   protected:
    /**
     * @brief Processing logic to be implemented by derived class
     * @param in
     * @param out
     * @return The amount of samples written in output
     */
    virtual int   do_process(const ArduousInputView& in, ArduousOutputView& out) = 0;

    /**
     * @brief Processes \p audio using \ref _io_config and the other \ref do_process function. Can be overriden.
     * @param audio
     * @return The amount of samples written in output
     */
    virtual int   do_process(std::span<float> audio){
        ArduousInputView in;
        in.channels = _io_config.audio_in.channels;
        in.data     = audio.data();
        in.frames   = _io_config.audio_in.length;
        in.layout   = _io_config.audio_in.layout;
        in.sample_rate = _io_config.sample_rate;

        ArduousOutputView out;
        out.data     = audio.data();
        out.channels = _io_config.audio_out.channels;
        out.layout   = _io_config.audio_out.layout;
        out.sample_rate = _io_config.sample_rate;

        return do_process(in, out);
    }
    Ort::Session& _session;
    ModelIOConfig _io_config;
};

/**
 * @brief ModelBase class that includes CPU memory management capabilities.
 * */
class ModelBaseWithCPUMemory : public ModelBase {
   public:
    /**
     * @brief Constructor for ModelBaseWithCPUMemory.
     * @param session Reference to the ONNX Runtime session.
     * @param io_config Input/Output configuration.
     */
    ModelBaseWithCPUMemory(Ort::Session& session, const ModelIOConfig io_config) :
        ModelBase(session, io_config),
        _memory_info{Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault)},
        _binding{_session} {}

    /**
     * @brief Virtual destructor for polymorphic behavior.
     */
    virtual ~ModelBaseWithCPUMemory() = default;

   protected:
    Ort::MemoryInfo _memory_info;  ///< Memory information for CPU allocation.
    Ort::IoBinding  _binding;      ///< IO Binding for the session.
};

/**
 * @brief Factory class to register and create ModelBase implementations.
 * */
class Factory {
   public:
    /**
     * @brief Type definition for creating a ModelBase instance.
     */
    using Creator = std::function<std::unique_ptr<ModelBase>(Ort::Session& session, const ModelIOConfig io_config)>;

    /**
     * @brief Static map to store model creator functions.
     */
    static auto& map() {
        static std::unordered_map<std::string, Creator> m;
        return m;
    }

    /**
     * @brief Register a new ModelBase implementation.
     * @tparam T The concrete ModelBase class to register.
     * @param name The string name to use for registration.
     */
    template <class T>
    struct Register {
        /**
         * @brief Registers the creator function for type T.
         * @param name The name under which the implementation will be registered.
         */
        explicit Register(const std::string& name) {
            map()[name] = [](Ort::Session& session, const ModelIOConfig io_config) {
                return std::unique_ptr<ModelBase>(std::make_unique<T>(session, io_config));
            };
        }
    };

    /**
     * @brief Retrieves the creator function for a registered model type.
     * @param name The registered name of the model implementation.
     * @return A function that creates an instance of ModelBase or nullptr if not found.
     */
    static Creator create(const std::string& name) {
        auto it = map().find(name);
        return it == map().end() ? nullptr : it->second;
    }
};

}  // namespace arduous