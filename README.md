<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![project_license][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/grybouilli/arduous">
    <!-- <img src="images/logo.png" alt="Logo" width="80" height="80"> -->
  </a>

<h3 align="center">ARDUOUS : AndRoiD aUdiO neUral dSp </h3>

  <p align="center">
    A set of apps for real-time neural audio processing on Android using liboboe and ONNX RT 
    <br />
    <a href="https://github.com/grybouilli/arduous"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/grybouilli/arduous">View Demo</a>
    &middot;
    <a href="https://github.com/grybouilli/arduous/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/grybouilli/arduous/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#dependencies">Dependencies</a></li>
        <li><a href="#building">Building</a></li>
        <li><a href="#running">Running</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

<!-- [![Product Name Screen Shot][product-screenshot]](https://example.com) -->

In this repo, you'll find :

* offline inference app based on ONNX Runtime to run neural dsps;
* small api to implement your own models for the apps;
* an app to export onnx models with embedded onnx runtime context;
* (to be implemented) an app that runs neural dsps in real-time, using [liboboe](github.com/google/oboe)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started
### Dependencies

Needed:
* CMake 
* [Android NDK (tested with version r27d)](https://developer.android.com/ndk/downloads?hl=fr)
* adb (to export to your Android device)

  
Fetched by cmake :
* [Oboe v1.9.0](github.com/google/oboe)
* [ONNX Runtime v1.24.2](https://github.com/csukuangfj/onnxruntime-libs/releases/download/v1.24.2/)
* Qualcomm AI Engine Direct SDK: [latest release](https://www.qualcomm.com/developer/software/qualcomm-ai-engine-direct-sdk)
* [nlohmann/json](https://github.com/nlohmann/json)

### Building
After installing the android ndk at `/path/to/ndk`, you clone the repo and build with cmake :
```sh
git clone https://github.com/grybouilli/arduous
cmake -B build -DCMAKE_TOOLCHAIN_FILE=/path/to/ndk/build/cmake/android.toolchain.cmake [-DONNX_USE_QNN=ON] [-DANDROID_ABI=arm64-v8a] [-GNinja] .
cmake --build build
```
Or you can build and deploy all at once with:
```bash
python script/deploy.py
```
You need to have your phone plugged and ready to use with adb for this script. Look at the section [Running](#running) for more info on that.

Notes : 
* The option `-DONNX_USE_QNN=ON` will make cmake fetch a version of onnx that supports QNN EP ; note that this means the only available EPs will be QNN and CPU. To use QNN with accelerators, push the
* The option `-DANDROID_ABI=arm64-v8a` ensures the built binary will be 64 bits. When not specified, Android ndk might default to 32-bit build.  
### Running

To be able to run binaries on your phone you need ADB. Then:

* Enable the developers options on your Android device. 
* Connect it to your computer and allow adb in the developer's options. 
On your laptop, run:
```sh
adb kill-server
adb start-server
adb devices 
# at this point, you might get prompted on your android device to allow your machine 
```
Then, run the [deploy.py script](scripts/deploy.py). You can now run the arduous apps on your phone with:
```bash
adb shell 
> device:/ $ cd /data/local/tmp/arduous # the folder /data/local/tmp is hidden, auto complete doesn't work
> device:/data/local/tmp/arduous: $ source ./setup.sh
> device:/data/local/tmp/arduous: $ ./get_embedded_ctx --help
```

Usage : 
```shell
Usage:
  get_embedded_ctx [OPTION...]

  -h, --help                Print usage
  -m, --model_filename arg  File containing the model to load (expected 
                            .onnx file)
  -e, --ep_name arg         ONNX Runtime EP name (expected string)
  -c, --ep_config arg       File containing the EP config (expected .json 
                            file)
  -a, --args_from_file arg  File containing argument values for the app 
                            (expected .json file)
  -s, --session_config arg  File containing the session config entries 
                            (expected .json file) (default: "")
  -o, --model_ctx_out arg   The output path to which to save the compiled 
                            model (exptected .onnx)
```

Usage : 
```shell
Usage:
  offline_inferences [OPTION...]

  -h, --help                Print usage
  -m, --model_filename arg  File containing the model to load (expected 
                            .onnx file)
  -e, --ep_name arg         ONNX Runtime EP name (expected string)
  -c, --ep_config arg       File containing the EP config (expected .json 
                            file)
  -a, --args_from_file arg  File containing argument values for the app 
                            (expected .json file)
  -s, --session_config arg  File containing the session config entries 
                            (expected .json file) (default: "")
  -t, --model_type arg      The type of model to run (expected string)
  -i, --input arg           The input audio path (expected .wav file)
  -o, --output arg          The output path (expected folder path)
  -C, --model_config arg    File containing the model I/O config entries 
                            (expected .json file)
```

<!-- ROADMAP -->
## Roadmap
- [x] Finish README.md
- [x] Improve latency
- [x] Implement Second-Order Lowpass 
- [x] Implement modular interface for pluggable inference engine interfaces
- [ ] Try other inference engines
    - [ ] RTNeural
    - [ ] TF Lite
    - [ ] Executorch
    - [ ] ncnn
    - [ ] MNN
- [ ] Streaming app
  - [ ] Command line
  - [ ] With UI
- [ ] ConvTasNet
  - [x] Offline implementation
  - [x] Streaming implementation
  - [ ] Benchmark 
    - [x] Latency
    - [ ] NPU Utilization
    - [x] SI-SDR
    - [ ] Generate graphs

See the [open issues](https://github.com/grybouilli/arduous/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Top contributors:

<a href="https://github.com/grybouilli/arduous/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=grybouilli/arduous" alt="contrib.rocks image" />
</a>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.md` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Nicolas Gry - grybouilli at outlook.fr - nicolas.gry at inria.fr

Project Link: [https://github.com/grybouilli/arduous](https://github.com/grybouilli/arduous)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/grybouilli/arduous.svg?style=for-the-badge
[contributors-url]: https://github.com/grybouilli/arduous/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/grybouilli/arduous.svg?style=for-the-badge
[forks-url]: https://github.com/grybouilli/arduous/network/members
[stars-shield]: https://img.shields.io/github/stars/grybouilli/arduous.svg?style=for-the-badge
[stars-url]: https://github.com/grybouilli/arduous/stargazers
[issues-shield]: https://img.shields.io/github/issues/grybouilli/arduous.svg?style=for-the-badge
[issues-url]: https://github.com/grybouilli/arduous/issues
[license-shield]: https://img.shields.io/github/license/grybouilli/arduous.svg?style=for-the-badge
[license-url]: https://github.com/grybouilli/arduous/blob/main/LICENSE.md
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/nicolas-gry
[product-screenshot]: images/screenshot.png
