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
from dataclasses import dataclass

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


def is_valid_hexcolor(hexcolor: str) -> bool:
    if len(hexcolor) != 6:
        return False

    valid_hex_chars = list("012345789abcdef")
    for char in hexcolor.lower():
        if char not in valid_hex_chars:
            return False

    return True


@dataclass
class Config:
    columns: int
    rows: int
    buttons: list[dict]


@dataclass
class ConfigLoader:
    def __interpret_config(self, yaml_config) -> Config:
        columns = yaml_config.get("columns")
        rows = yaml_config.get("rows")
        self.__validate_dimensions(columns, rows)

        buttons = yaml_config.get("buttons")
        self.__validate_buttons(buttons, rows, columns)

        return Config(columns, rows, buttons)

    def __validate_buttons(self, buttons, rows, columns) -> None:
        if not isinstance(buttons, list):
            error_msg("invalid button config. needs to be a list of dicts.")
        for button in buttons:
            if not isinstance(button, dict):
                error_msg("invalid button config. needs to be a list of dicts.")

            if (
                not isinstance(dimensions := button.get("button", ""), list)
                or (not isinstance(dimensions[0], int))
                or (not isinstance(dimensions[1], int))
                or (0 > dimensions[0] or dimensions[0] > rows - 1)
                or (0 > dimensions[1] or dimensions[1] > columns - 1)
            ):
                error_msg(f"invalid button 'button' subentry: '{dimensions}'")

            for entry in ("txt", "cmd"):
                if not isinstance(result := button.get(entry, ""), str):
                    error_msg(f"invalid button '{entry}' subentry: '{result}'")

            if not isinstance(
                bg_color := button.get("bg_color", "cccccc"), str
            ) or not is_valid_hexcolor(bg_color):
                error_msg(f"invalid button 'bg_color' subentry: '{bg_color}'")

            if not isinstance(
                fg_color := button.get("fg_color", "ffffff"), str
            ) or not is_valid_hexcolor(bg_color):
                error_msg(f"invalid button 'fg_color' subentry: '{fg_color}'")

            if (
                not isinstance(fontsize := button.get("fontsize", ""), int)
                or 0 > fontsize
            ):
                error_msg(f"invalid button 'fontsize' subentry: '{fontsize}'")

    def __validate_dimensions(self, columns, rows) -> None:
        for dimension in (columns, rows):
            if not isinstance(dimension, int) and (dimension <= 0):
                error_msg(f"invalid dimension: {dimension}")

    def load_config(  # pylint: disable=inconsistent-return-statements
        self,
        config_file_path,
    ) -> Config:
        try:
            with open(config_file_path, "r", encoding="utf-8") as config_reader:
                read_config = yaml.safe_load(config_reader)
                return self.__interpret_config(read_config)
        except (FileNotFoundError, PermissionError, IOError) as error:
            error_msg(
                f"Error: Could not access config file at {config_file_path}. Reason: {error}"
            )
        except yaml.YAMLError as error:
            error_msg(f"Error parsing config file. Reason: {error}")


class VulcanBoardApp(App):
    def build(self) -> GridLayout:
        config_loader = ConfigLoader()
        config = config_loader.load_config(get_config_path())

        button_map = {
            (btn["button"][0], btn["button"][1]): btn for btn in config.buttons
        }

        layout = GridLayout(
            cols=config.columns, rows=config.rows, spacing=5, padding=5
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
                        text_size=(
                            None,
                            None,
                        ),  # Enable text alignment within button
                        background_normal="",
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
