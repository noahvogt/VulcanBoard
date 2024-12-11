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

from kivy.uix.button import Button
from kivy.properties import ListProperty  # pylint: disable=no-name-in-module


class AutoResizeButton(Button):
    """A button that adjusts its label font size dynamically."""

    original_pos = ListProperty([0, 0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dragged = False
        # pylint: disable=no-member
        self.bind(  # type: ignore
            size=self.adjust_font_size, text=self.adjust_font_size
        )

    def adjust_font_size(self, *args):
        """Dynamically adjusts font size to fit the button's bounds."""
        if not self.text:
            return

        # Define the minimum and maximum font size
        min_font_size = 10
        max_font_size = min(self.width, self.height) * 0.5

        # Perform a binary search to find the best font size
        best_font_size = min_font_size
        while min_font_size <= max_font_size:
            current_font_size = (min_font_size + max_font_size) // 2
            self.font_size = current_font_size
            self.texture_update()  # Update texture to get new texture_size

            # Check if the text fits within the button's bounds
            if (
                self.texture_size[0] <= self.width * 0.9
                and self.texture_size[1] <= self.height * 0.9
            ):
                best_font_size = current_font_size
                min_font_size = current_font_size + 1
            else:
                max_font_size = current_font_size - 1

        # Apply the best font size
        self.font_size = best_font_size
