#!/usr/bin/env python3

# Copyright © 2024 Noah Vogt <noah@noahvogt.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=invalid-name
import threading
import sys
import asyncio
import time
import colorama
import uvicorn
from fastapi import FastAPI, HTTPException

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.utils import get_color_from_hex
from kivy.config import Config as kvConfig
from kivy.core.window import Window
from kivy.clock import Clock

from util import log, error_exit_gui
from config import (
    get_config_path,
    ConfigLoader,
    Config,
    get_state_from_id,
    get_state_id_from_exit_code,
    DEFAULT_BUTTON_BG_COLOR,
    DEFAULT_BUTTON_FG_COLOR,
    EMPTY_BUTTON_BG_COLOR,
    DEFAULT_STATE_ID,
    ERROR_SINK_STATE_ID,
)
from ui import AutoResizeButton


class VulcanBoardApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_touch_time = 0  # For debounce handling

    def build(self):
        self.loop = self.ensure_asyncio_loop_running()
        self.button_grid = {}
        self.button_config_map = {}
        self.icon = "icon.png"
        config_loader = ConfigLoader(get_config_path())
        config = config_loader.get_config()  # pyright: ignore

        if isinstance(config, str):
            error_exit_gui(config)
        else:
            config: Config = config

            Window.borderless = config.borderless
            if config.set_window_pos:
                Window.left = config.window_pos_x
                Window.top = config.window_pos_y
            if config.use_auto_fullscreen_mode:
                Window.fullscreen = "auto"

            kvConfig.set("kivy", "exit_on_escape", "0")

            self.button_config_map = {
                (btn["position"][0], btn["position"][1]): btn
                for btn in config.buttons
            }

            layout = GridLayout(
                cols=config.columns,
                rows=config.rows,
                spacing=config.spacing,
                padding=config.padding,
            )

            # Populate grid with buttons and placeholders
            for row in range(config.rows):
                for col in range(config.columns):
                    defined_button = self.button_config_map.get((row, col))
                    if defined_button:
                        states = defined_button.get("states", [])
                        state = get_state_from_id(states, DEFAULT_STATE_ID)

                        btn = AutoResizeButton(
                            text=state.get("txt", ""),
                            background_color=get_color_from_hex(
                                state.get("bg_color", DEFAULT_BUTTON_BG_COLOR)
                            ),
                            color=get_color_from_hex(
                                state.get("fg_color", DEFAULT_BUTTON_FG_COLOR)
                            ),
                            halign="center",
                            valign="middle",
                            background_normal="",
                            state_id=DEFAULT_STATE_ID,
                        )

                        if defined_button.get("autostart", False):
                            self.async_task(
                                self.execute_command_async(defined_button, btn)
                            )

                        # Use debounce wrapper instead of raw on_release to
                        # avoid double execution on single taps on touchscreens
                        btn.bind(  # pyright: ignore pylint: disable=no-member
                            on_release=lambda btn_instance, button=defined_button: self.on_button_pressed_once(
                                button, btn_instance
                            )
                        )

                    else:
                        btn = AutoResizeButton(
                            background_color=get_color_from_hex(
                                EMPTY_BUTTON_BG_COLOR
                            ),
                        )
                    self.button_grid[(row, col)] = btn
                    layout.add_widget(btn)

            self.api_app = FastAPI(title="VulcanBoard API")
            self._setup_api_routes()

            uvicorn_config = uvicorn.Config(
                app=self.api_app,
                host="0.0.0.0",
                port=config.api_port,
                log_level="info",
            )
            server = uvicorn.Server(uvicorn_config)
            self.async_task(server.serve())

            return layout

    def on_button_pressed_once(self, button, btn_instance):
        now = time.time()
        if now - self.last_touch_time > 0.3:  # 300 ms debounce
            self.last_touch_time = now
            self.async_task(self.execute_command_async(button, btn_instance))

    def async_task(self, coroutine):
        asyncio.run_coroutine_threadsafe(coroutine, self.loop)

    def ensure_asyncio_loop_running(self):
        if hasattr(self, "loop"):
            return self.loop

        loop = asyncio.new_event_loop()

        def run_loop():
            asyncio.set_event_loop(loop)
            loop.run_forever()

        threading.Thread(target=run_loop, daemon=True).start()
        return loop

    def config_error_exit(self, popup):
        popup.dismiss()
        sys.exit(1)

    async def execute_command_async(self, button: dict, btn: AutoResizeButton):
        follow_up_state_loop = True
        states = button["states"]
        current_state_id = btn.state_id
        while follow_up_state_loop:
            state = get_state_from_id(states, current_state_id)
            follow_up_state_loop = False

            try:
                process = await asyncio.create_subprocess_shell(
                    state["cmd"], shell=True
                )
                exit_code = await process.wait()
                log(f"Executed command: {state['cmd']}")
            except Exception as e:
                exit_code = ERROR_SINK_STATE_ID
                log(f"Error executing command: {e}", color="yellow")

            if len(states) != 1:
                follow_up_state = state.get("follow_up_state")
                if isinstance(follow_up_state, int):
                    follow_up_state_loop = True
                    exit_code = follow_up_state
                elif follow_up_state == "exit_code":
                    follow_up_state_loop = True

                if follow_up_state_loop:
                    current_state_id = get_state_id_from_exit_code(
                        states, exit_code
                    )
                    follow_up_execute_states = state.get(
                        "follow_up_execute_states"
                    )
                    if (
                        follow_up_execute_states is not None
                        and current_state_id not in follow_up_execute_states
                    ):
                        follow_up_state_loop = False

                Clock.schedule_once(
                    lambda _, ec=exit_code: self.update_button_feedback(
                        states, btn, ec
                    )
                )
                affects_buttons = button.get("affects_buttons", None)
                if affects_buttons:
                    for affected_btn_dims in affects_buttons:
                        btn_pos = (affected_btn_dims[0], affected_btn_dims[1])
                        affected_button = self.button_grid[btn_pos]
                        Clock.schedule_once(
                            lambda _, btn_pos=btn_pos, affected_button=affected_button, ec=exit_code: self.update_button_feedback(
                                self.button_config_map[btn_pos]["states"],
                                affected_button,
                                ec,
                            )
                        )

    def update_button_feedback(
        self, states: list, btn: AutoResizeButton, exit_code: int
    ):
        state_id = get_state_id_from_exit_code(states, exit_code)
        state = get_state_from_id(states, state_id)

        btn.text = state.get("txt", "")
        btn.state_id = state_id
        btn.background_color = get_color_from_hex(
            state.get("bg_color", DEFAULT_BUTTON_BG_COLOR)
        )
        btn.color = get_color_from_hex(
            state.get("fg_color", DEFAULT_BUTTON_FG_COLOR)
        )

    def update_button_state_from_api(
        self, dt, row: int, col: int, state_id: int
    ):
        btn = self.button_grid.get((row, col))
        btn_config = self.button_config_map.get((row, col))
        if not btn or not btn_config:
            return

        states = btn_config.get("states", [])
        state = get_state_from_id(states, state_id)

        btn.text = state.get("txt", "")
        btn.state_id = state_id
        btn.background_color = get_color_from_hex(
            state.get("bg_color", DEFAULT_BUTTON_BG_COLOR)
        )
        btn.color = get_color_from_hex(
            state.get("fg_color", DEFAULT_BUTTON_FG_COLOR)
        )

    def _setup_api_routes(self):
        @self.api_app.get("/get_states")
        def get_states(x: int, y: int):
            btn_config = self.button_config_map.get((x, y))
            if not btn_config:
                raise HTTPException(status_code=404, detail="Button not found")
            return {"states": btn_config.get("states", [])}

        @self.api_app.get("/get_current_state")
        def get_current_state(x: int, y: int):
            btn = self.button_grid.get((x, y))
            if not btn:
                raise HTTPException(status_code=404, detail="Button not found")
            return {"state_id": getattr(btn, "state_id", DEFAULT_STATE_ID)}

        @self.api_app.get("/set_state")
        @self.api_app.post("/set_state")
        def set_state(x: int, y: int, state: int):
            btn_config = self.button_config_map.get((x, y))
            btn = self.button_grid.get((x, y))
            if not btn_config or not btn:
                raise HTTPException(status_code=404, detail="Button not found")

            states = btn_config.get("states", [])
            valid_state = None
            for s in states:
                if s.get("id", DEFAULT_STATE_ID) == state:
                    valid_state = s
                    break
            if not valid_state:
                raise HTTPException(
                    status_code=400,
                    detail=f"State {state} not found for this button",
                )

            Clock.schedule_once(
                lambda dt: self.update_button_state_from_api(dt, x, y, state)
            )
            return {"status": "success", "state_id": state}


def start_asyncio_loop():
    asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    colorama.init()
    VulcanBoardApp().run()
