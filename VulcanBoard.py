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
import colorama

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
    def build(self):
        self.loop = self.ensure_asyncio_loop_running()
        self.button_grid = {}
        self.button_config_map = {}
        self.icon = "icon.jpg"
        config_loader = ConfigLoader(get_config_path())
        config = config_loader.get_config()  # pyright: ignore
        if isinstance(config, str):
            error_exit_gui(config)
        else:
            config: Config = config

            Window.borderless = config.borderless
            kvConfig.set("kivy", "window_icon", "icon.ico")
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

                        # pylint: disable=no-member
                        btn.bind(  # pyright: ignore
                            on_release=lambda btn_instance, button=defined_button: self.async_task(
                                self.execute_command_async(button, btn_instance)
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

            return layout

    def async_task(self, coroutine):
        asyncio.run_coroutine_threadsafe(coroutine, self.loop)

    def ensure_asyncio_loop_running(self):
        if hasattr(self, "loop"):
            return self.loop  # Already created

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
        while follow_up_state_loop:
            state = get_state_from_id(states, btn.state_id)
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
                if isinstance(
                    follow_up_state := state.get("follow_up_state"), int
                ):
                    follow_up_state_loop = True
                    exit_code = follow_up_state

                Clock.schedule_once(
                    lambda _: self.update_button_feedback(
                        states, btn, exit_code  # pyright: ignore
                    )
                )
                affects_buttons = button.get("affects_buttons", None)
                if affects_buttons:
                    for affected_btn_dims in affects_buttons:
                        btn_pos = (affected_btn_dims[0], affected_btn_dims[1])
                        affected_button = self.button_grid[btn_pos]
                        Clock.schedule_once(
                            lambda _, btn_pos=btn_pos, affected_button=affected_button: self.update_button_feedback(
                                self.button_config_map[btn_pos]["states"],
                                affected_button,
                                exit_code,  # pyright: ignore
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


def start_asyncio_loop():
    asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    colorama.init()
    VulcanBoardApp().run()
