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
)
from ui import AutoResizeButton


class VulcanBoardApp(App):
    def build(self):
        self.loop = self.ensure_asyncio_loop_running()
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

            button_map = {
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
                    defined_button = button_map.get((row, col))
                    if defined_button:
                        states = defined_button.get("states", [])
                        print("STATES")
                        print(states)
                        state_id = [0]
                        state = get_state_from_id(states, state_id[0])
                        print("STATE")
                        print(state)

                        btn = AutoResizeButton(
                            text=state.get("txt", ""),
                            background_color=get_color_from_hex(
                                state.get("bg_color", "aaaaff")
                            ),
                            color=get_color_from_hex(
                                state.get("fg_color", "ffffff")
                            ),
                            halign="center",
                            valign="middle",
                            background_normal="",
                        )

                        # pylint: disable=no-member
                        btn.bind(  # pyright: ignore
                            on_release=lambda btn_instance, states=states, state_id=state_id: self.async_task(
                                self.execute_command_async(
                                    states, state_id, btn_instance
                                )
                            )
                        )
                    else:
                        btn = AutoResizeButton(
                            background_color=get_color_from_hex("cccccc"),
                        )
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

    async def execute_command_async(
        self, states: list, state_id: list[int], btn: AutoResizeButton
    ):
        new_state_id = get_state_id_from_exit_code(states, state_id[0])
        try:
            print(states[new_state_id]["cmd"])
            process = await asyncio.create_subprocess_shell(
                states[new_state_id]["cmd"], shell=True
            )
            exit_code = await process.wait()
            print(f"EXIT {exit_code}")
            log(f"Executed command: {states[new_state_id]['cmd']}")
        except Exception as e:
            exit_code = 1
            log(f"Error executing command: {e}", color="yellow")

        if len(states) != 1:
            state_id[0] = exit_code  # pyright: ignore

            Clock.schedule_once(
                lambda _: self.update_button_feedback(
                    states, btn, exit_code  # pyright: ignore
                )
            )

    def update_button_feedback(
        self, states: list, btn: AutoResizeButton, exit_code: int
    ):
        state = get_state_from_id(
            states, get_state_id_from_exit_code(states, exit_code)
        )

        btn.text = state.get("txt", "")
        btn.background_color = get_color_from_hex(
            state.get("bg_color", "cc0000")
        )
        # btn.foreground_color = get_color_from_hex(
        #     state.get("bg_color", "cc0000")
        #         )


def start_asyncio_loop():
    asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    colorama.init()
    VulcanBoardApp().run()
