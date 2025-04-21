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
    ERROR_SINK_STATE_ID,
)
from .state import get_state_ids


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
        buttons_that_affect_others = set()
        button_grid = {}
        for button in self.buttons:
            if not isinstance(button, dict):
                raise CustomException(
                    "invalid button config. needs to be a list of dicts."
                )

            dimensions = button.get("position", "")
            if not self.is_valid_dimension(dimensions):
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
            to_follow_up_state_ids = set()
            for state in states:
                if not (
                    isinstance(state, dict)
                    and isinstance(state_id := state.get("id", None), int)
                ):
                    raise CustomException(
                        f"invalid {btn_dims}: invalid state id detected"
                    )
                state_id = state.get("id", None)
                if isinstance(state_id, int):
                    if state_id in defined_state_ids:
                        raise CustomException(
                            f"invalid {btn_dims}: tried to define state "
                            + f"'{state_id}' twice"
                        )
                    defined_state_ids.add(state_id)

                for string in ("cmd", "txt"):
                    if not isinstance(state.get(string, ""), str):
                        raise CustomException(
                            f"invalid {btn_dims}: invalid '{string}' subentry "
                            + f"for state id '{state_id}': must be a string"
                        )

                for color_pair in ("bg_color", DEFAULT_BUTTON_BG_COLOR), (
                    "fg_color",
                    DEFAULT_BUTTON_FG_COLOR,
                ):
                    if not isinstance(
                        color := state.get(color_pair[0], color_pair[1]),
                        str,
                    ) or not is_valid_hexcolor(color):
                        raise CustomException(
                            f"invalid {btn_dims}: '{color_pair[0]}' subentry "
                            + f"for state '{state_id}': '{color}'"
                        )

                follow_up_state = state.get("follow_up_state", 0)
                if not isinstance(follow_up_state, int):
                    raise CustomException(
                        f"invalid {btn_dims}: 'follow_up_state' subentry for"
                        + f" state '{state_id}': must be int"
                    )
                to_follow_up_state_ids.add(follow_up_state)

            button_grid[(dimensions[0], dimensions[1])] = button

            affects_buttons = button.get("affects_buttons", None)
            if isinstance(affects_buttons, list):
                if len(affects_buttons) == 0:
                    raise CustomException(
                        f"invalid {btn_dims}: 'affects_buttons' entry: must be"
                        + "a non-empty list"
                    )

            if affects_buttons:
                for affected_button_dimension in affects_buttons:
                    if not self.is_valid_dimension(affected_button_dimension):
                        raise CustomException(
                            f"invalid {btn_dims}: 'affects_buttons' entry: "
                            + "invalid dimensions: "
                            + f"'{affected_button_dimension}'"
                        )
                buttons_that_affect_others.add(str(dimensions))

            if not DEFAULT_STATE_ID in defined_state_ids:
                raise CustomException(
                    f"invalid {btn_dims}: missing default state id "
                    + f"'{DEFAULT_STATE_ID}'"
                )
            if (len(defined_state_ids) > 1) and (
                not ERROR_SINK_STATE_ID in defined_state_ids
            ):
                raise CustomException(
                    f"invalid {btn_dims}: missing error sink state id "
                    + f"'{ERROR_SINK_STATE_ID}' for unstateless button"
                )

            for follow_up_state_id in to_follow_up_state_ids:
                if follow_up_state_id not in defined_state_ids:
                    raise CustomException(
                        f"invalid {btn_dims}: invalid 'follow_up_state' "
                        + f"subentry found: state '{follow_up_state_id}' does "
                        + "not exist"
                    )

        for btn_dims in buttons_that_affect_others:
            row = int(btn_dims[btn_dims.find("[") + 1 : btn_dims.find(",")])
            col = int(btn_dims[btn_dims.find(" ") + 1 : btn_dims.find("]")])
            button_dimensions = (row, col)

            button = button_grid[button_dimensions]
            affects_buttons = button["affects_buttons"]
            ids = []
            ids.append(get_state_ids(button["states"]))
            for affected_btn_dims in affects_buttons:
                try:
                    affected_button = button_grid[
                        (affected_btn_dims[0], affected_btn_dims[1])
                    ]
                except KeyError as e:
                    raise CustomException(
                        f"invalid button ({row}, {col}): 'affects_buttons' "
                        + "buttons must be defined"
                    ) from e
                ids.append(get_state_ids(affected_button["states"]))

            for id_listing in ids[1:]:
                if len(id_listing) == 1:
                    raise CustomException(
                        f"invalid button ({row}, {col}): 'affects_buttons' "
                        + "buttons cannot be stateless"
                    )
                if id_listing != ids[0]:
                    raise CustomException(
                        f"invalid button ({row}, {col}): 'affects_buttons' "
                        + "buttons must have the same state id's"
                    )

    def is_valid_dimension(self, dimensions):
        return not (
            not isinstance(dimensions, list)
            or (not isinstance(dimensions[0], int))
            or (not isinstance(dimensions[1], int))
            or (0 > dimensions[0] or dimensions[0] > self.rows - 1)
            or (0 > dimensions[1] or dimensions[1] > self.columns - 1)
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
