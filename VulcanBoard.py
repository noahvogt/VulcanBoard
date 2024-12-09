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
import subprocess
import sys

import colorama

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.utils import get_color_from_hex

from util import log, error_exit_gui
from config import get_config_path, ConfigLoader, Config


class VulcanBoardApp(App):
    def build(self):
        config_loader = ConfigLoader(get_config_path())
        config = config_loader.get_config()  # pyright: ignore
        if isinstance(config, str):
            error_exit_gui(config)
        else:
            config: Config = config
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
                        btn = Button(
                            text=defined_button.get("txt", ""),
                            background_color=get_color_from_hex(
                                defined_button.get("bg_color", "aaaaff")
                            ),
                            color=get_color_from_hex(
                                defined_button.get("fg_color", "ffffff")
                            ),
                            font_size=defined_button.get("fontsize", 14),
                            halign="center",
                            valign="middle",
                            background_normal="",
                        )

                        cmd = defined_button.get("cmd", "")
                        # pylint: disable=no-member
                        btn.bind(  # pyright: ignore
                            on_release=lambda _, cmd=cmd: self.execute_command_async(
                                cmd
                            )
                        )
                    else:
                        btn = Button(
                            background_color=get_color_from_hex("cccccc"),
                        )
                    layout.add_widget(btn)

            return layout

    def config_error_exit(self, popup):
        popup.dismiss()
        sys.exit(1)

    def execute_command_async(self, cmd):
        if cmd:
            try:
                subprocess.Popen(  # pylint: disable=consider-using-with
                    cmd, shell=True
                )
                log(f"Executed command: {cmd}")
            except Exception as e:
                log(f"Error executing command: {e}", color="yellow")


if __name__ == "__main__":
    colorama.init()
    VulcanBoardApp().run()
