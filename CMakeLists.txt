cmake_minimum_required(VERSION 3.21.0)

project(arduous
    VERSION 1.0.0
    DESCRIPTION "A pack of programs to run neural audio DSPs"
    HOMEPAGE_URL "https://github.com/grybouilli/arduous"
    LANGUAGES CXX C
)

set(CMAKE_CXX_STANDARD 23)

include(cmake/FetchFetchContent.cmake)
include(cmake/Fetch_ort_utils.cmake)
include(cmake/Fetch_nlohmann_json.cmake)
include(cmake/Fetch_cxxopts.cmake)
include(cmake/Fetch_sndfile_wrapper.cmake)
include(cmake/App_factory.cmake)

arduous_create_new_app(offline_inferences OfflineInferenceApp offline_inferences_app)
arduous_create_new_app(get_embedded_ctx GetEmbeddedCtxModelApp get_embedded_ctx_model_app)
