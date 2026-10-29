#ifndef APP_CLASS_HEADER
#error "You need to specify your App class prototype file in APP_CLASS_HEADER"
#endif // !APP_CLASS_HEADER

#ifndef APP_CLASS_NAME
#error "You need to specify your App class name in APP_CLASS_NAME"
#endif  // !APP_CLASS_NAME

#include APP_CLASS_HEADER
#include <cxxopts.hpp>
#include <iostream>

int main(int argc, const char* const* argv) {
    auto options = APP_CLASS_NAME::get_options();
    auto args    = options.parse(argc, argv);

    if (args.count("help")) {
        std::cout << options.help() << std::endl;
        return 0;
    }
    APP_CLASS_NAME app(args);

    app.run();
}