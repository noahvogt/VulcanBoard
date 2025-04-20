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
from .const import (
    DEFAULT_BUTTON_BG_COLOR,
    DEFAULT_BUTTON_FG_COLOR,
    DEFAULT_STATE_ID,
)


@dataclass
class ConfigLoader:
    config_path: str

    def __post_init__(self) -> None:
        self.buttons = []
        self.columns = 0
        self.rows = 0
        self.padding = 0
        self.spacing = 0
        self.borderless = False

    def get_config(self) -> Config | str:
        try:
            with open(self.config_path, "r", encoding="utf-8") as config_reader:
                yaml_config = yaml.safe_load(config_reader)
                self.columns = yaml_config.get("columns")
                self.rows = yaml_config.get("rows")
                self.buttons = yaml_config.get("buttons")
                self.padding = yaml_config.get("padding", 5)
                self.spacing = yaml_config.get("spacing", 5)
                self.borderless = yaml_config.get("borderless", False)
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
            self.columns,
            self.rows,
            self.buttons,
            self.spacing,
            self.padding,
            self.borderless,
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
                    f"invalid 'position' subentry: '{dimensions}'"
                )

            btn_dims = f"button ({dimensions[0]}, {dimensions[1]})"

            if not isinstance(states := button.get("states", ""), list):
                raise CustomException(
                    f"invalid {btn_dims} 'states' subentry: '{states}'"
                )

            if len(states) == 0:
                raise CustomException(
                    f"invalid {btn_dims} 'states' subentry: list cannot be empty"
                )

            if not isinstance(button.get("autostart", False), bool):
                raise CustomException(
                    f"invalid {btn_dims} 'autostart' entry: must be boolean"
                )

            defined_state_ids = set()
            for state in states:
                if not (
                    isinstance(state, dict)
                    or isinstance(state.get("id", None), int)
                    or isinstance(state.get("cmd", None), str)
                    or isinstance(state.get("txt", None), str)
                ):
                    raise CustomException(
                        f"invalid {btn_dims}: invalid state detected"
                    )
                state_id = state.get("id", None)
                if isinstance(state_id, int):
                    if state_id in defined_state_ids:
                        raise CustomException(
                            f"invalid {btn_dims}: tried to define state {state_id} twice"
                        )
                    defined_state_ids.add(state_id)

                for color_pair in ("bg_color", DEFAULT_BUTTON_BG_COLOR), (
                    "fg_color",
                    DEFAULT_BUTTON_FG_COLOR,
                ):
                    if not isinstance(
                        color := state.get(color_pair[0], color_pair[1]),
                        str,
                    ) or not is_valid_hexcolor(color):
                        raise CustomException(
                            f"invalid {btn_dims} '{color_pair[0]}' subentry: '{color}'"
                        )

            if not DEFAULT_STATE_ID in defined_state_ids:
                raise CustomException(
                    f"invalid {btn_dims}: missing default state id '{DEFAULT_STATE_ID}'"
                )

    def __validate_dimensions(self) -> None:
        for dimension in (self.columns, self.rows):
            if not isinstance(dimension, int) or (dimension <= 0):
                raise CustomException(f"invalid dimension: {dimension}")

    def __validate_styling(self) -> None:
        for styling in (self.spacing, self.padding):
            if not isinstance(styling, int) or (styling <= 0):
                raise CustomException(f"invalid styling: {styling}")

        if not isinstance(self.borderless, bool):
            raise CustomException("invalid borderless value, should be boolean")
