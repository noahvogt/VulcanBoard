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
from os import path, getenv, name
import subprocess
import sys

import yaml
from termcolor import colored
import colorama

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.utils import get_color_from_hex


def error_msg(msg: str):
    print(colored("[*] Error: {}".format(msg), "red"))
    sys.exit(1)


def log(message: str, color="green") -> None:
    print(colored("[*] {}".format(message), color))  # pyright: ignore


def get_config_path():
    if name == "nt":
        return path.join(getenv("APPDATA", ""), "VulcanBoard", "config.yml")
    xdg_config_home = getenv("XDG_CONFIG_HOME", path.expanduser("~/.config"))
    return path.join(xdg_config_home, "VulcanBoard", "config.yml")


def load_config(  # pylint: disable=inconsistent-return-statements
    config_file_path,
):
    try:
        with open(config_file_path, "r", encoding="utf-8") as config_reader:
            return yaml.safe_load(config_reader)
    except (FileNotFoundError, PermissionError, IOError) as error:
        error_msg(
            f"Error: Could not access config file at {config_file_path}. Reason: {error}"
        )
    except yaml.YAMLError as error:
        error_msg(f"Error parsing config file. Reason: {error}")


class VulcanBoardApp(App):
    def build(self) -> GridLayout:
        config = load_config(get_config_path())

        columns = config.get("COLUMNS")
        rows = config.get("ROWS")
        self.validate_dimensions(columns, rows)

        buttons_config = config.get("BUTTONS", [])

        button_map = {
            (btn["button"][0], btn["button"][1]): btn for btn in buttons_config
        }

        layout = GridLayout(cols=columns, rows=rows, spacing=5, padding=5)

        # Populate grid with buttons and placeholders
        for row in range(rows):
            for col in range(columns):
                defined_button = button_map.get((row, col))
                if defined_button:
                    btn = Button(
                        text=defined_button.get("txt", ""),
                        background_color=get_color_from_hex(
                            defined_button.get("color", "ffffff")
                        ),
                        font_size=defined_button.get("fontsize", 14),
                        halign="center",
                        valign="middle",
                        text_size=(
                            None,
                            None,
                        ),  # Enable text alignment within button
                    )

                    # pylint: disable=no-member
                    cmd = defined_button.get("cmd", "")
                    # pylint: disable=no-member
                    btn.bind(  # pyright: ignore
                        on_release=lambda instance, cmd=cmd: self.execute_command_async(
                            cmd
                        )
                    )
                else:
                    btn = Button(
                        background_color=get_color_from_hex("cccccc"),
                    )
                layout.add_widget(btn)

        return layout

    def validate_dimensions(self, columns, rows):
        for dimension in (columns, rows):
            if not isinstance(dimension, int) and (dimension <= 0):
                error_msg(f"invalid dimension: {dimension}")

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
