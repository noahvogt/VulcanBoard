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
from kivy.factory import Factory


def log(message: str, color="green") -> None:
    print(colored("[*] {}".format(message), color))  # pyright: ignore


def get_config_path():
    if name == "nt":
        return path.join(getenv("APPDATA", ""), "VulcanBoard", "config.yml")
    xdg_config_home = getenv("XDG_CONFIG_HOME", path.expanduser("~/.config"))
    return path.join(xdg_config_home, "VulcanBoard", "config.yml")


VALID_HEX_COLORS = list("0123456789abcdef")


def is_valid_hexcolor(hexcolor: str) -> bool:
    if len(hexcolor) != 6:
        return False

    for char in hexcolor.lower():
        if char not in VALID_HEX_COLORS:
            return False

    return True


@dataclass
class Config:
    columns: int
    rows: int
    buttons: list[dict]
    spacing: int
    padding: int


class CustomException(Exception):
    pass


@dataclass
class ConfigLoader:
    config_path: str

    def __post_init__(self) -> None:
        self.columns = 0
        self.rows = 0
        self.buttons = []
        self.padding = 0
        self.spacing = 0

    def get_config(self) -> Config | str:
        try:
            with open(self.config_path, "r", encoding="utf-8") as config_reader:
                yaml_config = yaml.safe_load(config_reader)
                self.columns = yaml_config.get("columns")
                self.rows = yaml_config.get("rows")
                self.buttons = yaml_config.get("buttons")
                self.padding = yaml_config.get("padding", 5)
                self.spacing = yaml_config.get("spacing", 5)
                return self.__interpret_config()
        except (FileNotFoundError, PermissionError, IOError) as error:
            return f"Error: Could not access config file at {self.config_path}. Reason: {error}"
        except (yaml.YAMLError, CustomException) as error:
            return f"Error parsing config file. Reason: {error}"

    def __interpret_config(self) -> Config:
        self.__validate_dimensions()
        self.__validate_buttons()
        self.__validate_styling()

        return Config(
            self.columns, self.rows, self.buttons, self.spacing, self.padding
        )

    def __validate_buttons(self) -> None:
        if not isinstance(self.buttons, list):
            raise CustomException(
                "invalid button config. needs to be a list of dicts."
            )
        for button in self.buttons:
            if not isinstance(button, dict):
                raise CustomException(
                    "invalid button config. needs to be a list of dicts."
                )

            if (
                not isinstance(dimensions := button.get("position", ""), list)
                or (not isinstance(dimensions[0], int))
                or (not isinstance(dimensions[1], int))
                or (0 > dimensions[0] or dimensions[0] > self.rows - 1)
                or (0 > dimensions[1] or dimensions[1] > self.columns - 1)
            ):
                raise CustomException(
                    f"invalid button 'position' subentry: '{dimensions}'"
                )

            for entry in ("txt", "cmd"):
                if not isinstance(result := button.get(entry, ""), str):
                    raise CustomException(
                        f"invalid button '{entry}' subentry: '{result}'"
                    )

            if not isinstance(
                bg_color := button.get("bg_color", "cccccc"), str
            ) or not is_valid_hexcolor(bg_color):
                raise CustomException(
                    f"invalid button 'bg_color' subentry: '{bg_color}'"
                )

            if not isinstance(
                fg_color := button.get("fg_color", "ffffff"), str
            ) or not is_valid_hexcolor(bg_color):
                raise CustomException(
                    f"invalid button 'fg_color' subentry: '{fg_color}'"
                )

            if (
                not isinstance(fontsize := button.get("fontsize", ""), int)
                or 0 > fontsize
            ):
                raise CustomException(
                    f"invalid button 'fontsize' subentry: '{fontsize}'"
                )

    def __validate_dimensions(self) -> None:
        for dimension in (self.columns, self.rows):
            if not isinstance(dimension, int) or (dimension <= 0):
                raise CustomException(f"invalid dimension: {dimension}")

    def __validate_styling(self) -> None:
        for styling in (self.spacing, self.padding):
            if not isinstance(styling, int) or (styling <= 0):
                raise CustomException(f"invalid styling: {styling}")


class VulcanBoardApp(App):
    def build(self):
        config_loader = ConfigLoader(get_config_path())
        config = config_loader.get_config()  # pyright: ignore
        print(type(config))
        print(config)
        if isinstance(config, str):
            popup = Factory.ErrorPopup()
            popup.message.text = config
            popup.open()
            popup.error_exit = lambda: sys.exit(1)
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
        print("wow")
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
