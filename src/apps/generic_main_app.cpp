#ifndef APP_CLASS_HEADER
#error "You need to specify your App class prototype file in APP_CLASS_HEADER"
#endif  // !APP_CLASS_HEADER

#ifndef APP_CLASS_NAME
#error "You need to specify your App class name in APP_CLASS_NAME"
#endif  // !APP_CLASS_NAME

#include APP_CLASS_HEADER
#include <arduous/models/models_registry.hpp>
#include <cxxopts.hpp>
#include <iostream>

int main(int argc, const char* const* argv) {
    auto options = APP_CLASS_NAME::get_options();
    auto args    = options.parse(argc, argv);
    std::cout << "first parse done" << std::endl;
    if (args.count("help")) {
        std::cout << options.help() << std::endl;
        return 0;
    }

    if (args.count(ARGS_FROM_FILE_KEY)) {
        auto [new_argc, std_new_argv] = AppBase::get_options_from_config_file(args);
        std_new_argv.insert(std_new_argv.begin(), argv[0]);
        new_argc++;

        std::vector<const char*> new_argv;
        new_argv.reserve(std_new_argv.size());
        for (const auto& s : std_new_argv) new_argv.push_back(s.c_str());
        for (const auto e : new_argv) {
            std::cout << e << " ";
        }

        std::cout << std::endl;
        args = options.parse(new_argc, new_argv.data());
    }
    APP_CLASS_NAME app(args);

    app.run();
}