# VulcanBoard

a simple and stable hotkey program for desktop touchscreens.

There are many hotkey solutions and programs like that use either
- physical devices (Elgato StreamDeck) or
- touchscreens (LioranBoard, MacroDeck, StreamPi)

They are often very bloated but lack basic features like asynchronous command execution. They also crash way to often, so especially given their intended use for livestream production that greatly values stability, *VulcanBoard* aims to be a rock-solid alternative.

## Installation

To setup you need to have python3 installed. In addition, to install the dependencies using pip:

    pip install pyyaml kivy

## Project State
It is currently still under heavy development, here are some planned changes:
- add documentation for the configuration and use of VulcanBoard
- display error_exits in a gui window
- add gui window to configure keys
    - add multiple boards to config.yml
    - add edit history cache
- add button merging
- add possibility to choose the font family used for button texts
- add rounded corners
- add fullscreen mode (maybe using a cmdline switch)
- use constants / constant dict for default values
