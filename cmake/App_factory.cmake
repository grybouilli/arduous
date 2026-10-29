function(arduous_create_new_app app_name app_class_name app_base_file)
    set(${app_name}_BIN ${app_name})
    add_executable(${${app_name}_BIN}
        ${CMAKE_SOURCE_DIR}/src/apps/generic_main_app.cpp
        ${CMAKE_SOURCE_DIR}/src/apps/${app_base_file}.cpp
        ${CMAKE_SOURCE_DIR}/src/utils/json_utils.cpp
    )

    target_compile_definitions(${${app_name}_BIN}
        PRIVATE
        APP_CLASS_HEADER=<arduous/apps/${app_base_file}.hpp>
        APP_CLASS_NAME=${app_class_name}
    )

    target_link_libraries(${${app_name}_BIN}
        PRIVATE ort_utils
        PRIVATE nlohmann_json::nlohmann_json
        PRIVATE cxxopts::cxxopts
        PRIVATE sndfile_wrapper
    )

    target_include_directories(${${app_name}_BIN}
        PRIVATE include
    )
endfunction()
