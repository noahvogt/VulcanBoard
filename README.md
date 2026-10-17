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
- **Positions**: Buttons are placed with `position: [row, col]`, counted from `0` at the top left. The same `[row, col]` pairs are used in `affects_buttons` and as `x` (row) and `y` (column) in the HTTP API.
- **State Transitions via Exit Codes**: For a stateful button, the exit code of the executed command determines the new state of the button (e.g., `exit 2` switches the button to state `2`). There is no implicit cycling, so a simple toggle uses commands like `exit 1` in state `0` and `exit 0` in state `1`. An exit code without a matching state switches the button to state `1`, the error sink state, which every stateful button must define. This is incredibly useful for integrating with external scripts that check status.
- **Follow-up States**: With `follow_up_state` (a state id or `exit_code`), the command of the resulting state is executed right away as well. `follow_up_execute_states` limits this to a list of state ids. This is useful for status queries that run once and then show the result.
- **Autostart**: Buttons can have `autostart: true`, meaning their default command is executed immediately when VulcanBoard launches. This is useful for fetching the initial status of external systems (like lights or projectors) and setting the button state accordingly.
- **Affects Buttons**: A button can specify an `affects_buttons` array (a list of `[row, col]` positions). After its command has run, the affected buttons are switched to the same resulting state, which allows you to create radio-button-like groups or master switches. The affected buttons must be stateful and define the same state ids as the button itself.
- **HTTP API**: VulcanBoard exposes a local REST API (by default on port 8080, configurable with `api_port`) that allows external tools (like Home Assistant) to read and change button states. You can address a button with `x` (row) and `y` (column) or with its optional unique `id`.
    - `GET /get_states?id=my_btn` (returns available states)
    - `GET /get_current_state?id=my_btn` (returns the current active state id)
    - `POST /set_state?id=my_btn&state=2` (changes the displayed state of the button to state 2; the command is not executed and `affects_buttons` is not applied)

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
