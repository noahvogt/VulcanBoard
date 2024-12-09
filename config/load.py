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

from dataclasses import dataclass

import yaml

from util import CustomException

from .classes import Config
from .validate import is_valid_hexcolor


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
