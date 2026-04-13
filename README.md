# VulcanBoard

A hotkey board for desktop touchscreens.

There are many hotkey solutions and programs that use either
- physical devices (Elgato StreamDeck) or
- touchscreens (LioranBoard, MacroDeck, StreamPi)

They are often very bloated but lack basic features like
- multitouch support for the desktop client
- asynchronous command execution
- a fullscreen mode

They also crash way too often, so *VulcanBoard* aims to be a rock-solid alternative.

## Installation

To setup you need to have python3 installed. In addition, to install the dependencies using pip:

    pip install -r requirements.txt

## Project State & Roadmap

*VulcanBoard* is actively used by the author, hence is in a usable state. Here are some planned or possible future changes:

- add documentation for the configuration and use of VulcanBoard
- add gui window to configure keys
    - add multiple boards to config.yml
    - add edit history cache
    - add internal commands (see api proposal)
- add button merging (meaning a button that takes of the space of otherwise multiple buttons)
- add possibility to choose the font family used for button texts
- add rounded corners for buttons
- use constants / constant dict for default values
- add folders (which is already possible with button states, but kinda hacky)
- add showing an image instead of button text
- http api can control buttons by id (optional or maybe even required?) instead of positition (x, y)
- slaves (other desktop / smartphone clients) can connect via websockets to the master VulcanBoard instance
    - simple permission system: the master can live enable/disable certain buttons for a subset of slaves
- add button trigger in addition to the current http api, probably by specific supported websockets
