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
from kivy.properties import ListProperty  # pylint: disable=no-name-in-module

from util import log, error_exit_gui
from config import get_config_path, ConfigLoader, Config


class DraggableButton(Button):
    """A button that can be dragged and adjusts font size dynamically."""

    original_pos = ListProperty([0, 0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dragged = False
        self.bind(size=self.adjust_font_size, text=self.adjust_font_size)

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

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dragged = True
            self.original_pos = self.pos
            self.parent.canvas.remove(self.canvas)
            self.parent.canvas.add(self.canvas)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.dragged:
            self.center = touch.pos
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.dragged:
            self.dragged = False
            self.parent.handle_drop(self, touch)
            return True
        return super().on_touch_up(touch)


class DraggableGridLayout(GridLayout):
    """A grid layout that supports drag-and-drop."""

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app  # Reference to the main app

    def handle_drop(self, dragged_button, touch):
        """Handle the drop of a button."""
        for child in self.children:
            if child.collide_point(*touch.pos) and child != dragged_button:
                # Swap buttons
                dragged_index = self.children.index(dragged_button)
                target_index = self.children.index(child)
                self.children[dragged_index], self.children[target_index] = (
                    self.children[target_index],
                    self.children[dragged_index],
                )

                # Update the config
                print(f"dragged: {dragged_index}")
                print(f"target: {target_index}")
                self.app.swap_button_positions(dragged_index, target_index)
                break

        # Reset position of dragged button
        dragged_button.pos = dragged_button.original_pos


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

            layout = DraggableGridLayout(
                self,
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
                        btn = DraggableButton(
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
                        btn = DraggableButton(
                            background_color=get_color_from_hex("cccccc"),
                        )
                    layout.add_widget(btn)

            return layout

    def swap_button_positions(self, index1, index2):
        pass

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
