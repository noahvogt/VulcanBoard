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

## Core Concepts

VulcanBoard is built around a few powerful concepts that make it highly flexible:

- **Stateful & Stateless Buttons**: A button can have one or multiple states. A stateless button has only a single state (usually `id: 0`) and always executes the same command. A stateful button has multiple states (e.g., `id: 0`, `id: 1`, `id: 2`), allowing it to toggle between different behaviors.
- **Dynamic Appearance**: Each state of a button can define its own `txt` (label), `cmd` (command to execute), `bg_color`, and `fg_color`. When the state changes, the button visually updates to reflect its new state.
- **State Transitions via Exit Codes**: By default, VulcanBoard automatically cycles to the next state (or back to `0`) when a button is pressed. However, you can use `follow_up_state: exit_code` so that the executed command's exit code determines the new state of the button. This is incredibly useful for integrating with external scripts that check status (e.g., returning exit code `2` to switch the button to state `2`).
- **Autostart**: Buttons can have `autostart: true`, meaning their default command is executed immediately when VulcanBoard launches. This is useful for fetching the initial status of external systems (like lights or projectors) and setting the button state accordingly.
- **Affects Buttons**: A button can specify an `affects_buttons` array (a list of `[x, y]` coordinates). When pressed, it can force other buttons to update their states or trigger their commands, allowing you to create complex radio-button-like groups or master switches.
- **HTTP API**: VulcanBoard exposes a local REST API (by default on port 8080) that allows external tools (like Home Assistant) to read and change button states. You can interact with the API using `x` and `y` coordinates or an optional unique `id` for each button.
    - `GET /get_states?id=my_btn` (returns available states)
    - `GET /get_current_state?id=my_btn` (returns the current active state id)
    - `POST /set_state?id=my_btn&state=2` (forces the button to change to state 2)

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
