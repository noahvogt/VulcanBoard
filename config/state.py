# Copyright © 2025 Noah Vogt <noah@noahvogt.com>

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

from .const import ERROR_SINK_STATE_ID


def get_state_from_id(states: list, state_id: int) -> dict:
    for state in states:
        possible_id = state.get("id", None)
        if isinstance(possible_id, int):
            if possible_id == state_id:
                return state

    return {}


def contains_id(states: list, state_id: int) -> bool:
    found_id = False
    for found_states in states:
        if found_states["id"] == state_id:
            found_id = True
            break

    return found_id


def get_state_id_from_exit_code(states: list, exit_code: int) -> int:
    if not contains_id(states, exit_code):
        exit_code = ERROR_SINK_STATE_ID

    return exit_code


def get_state_ids(states: list) -> list:
    output = set()
    for state in states:
        possible_id = state.get("id", None)
        if isinstance(possible_id, int):
            output.add(possible_id)

    return list(output)
