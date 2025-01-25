import yaml
from os import path, getenv, name
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, ListProperty


class DraggableButton(Button):
    """A button that can be dragged."""

    original_pos = ListProperty([0, 0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dragged = False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dragged = True
            self.original_pos = self.pos
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
                self.app.swap_button_positions(dragged_index, target_index)
                break

        # Reset position of dragged button
        dragged_button.pos = dragged_button.original_pos


class ConfigEditorApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_data = {}
        self.current_file = None
        self.selected_button = None

    def load_config_file(self, file_path):
        """Load the configuration file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.config_data = yaml.safe_load(f)
                self.current_file = file_path
                return True
        except Exception as e:
            self.show_popup("Error", f"Failed to load config: {e}")
            return False

    def save_config(self):
        """Save the updated configuration file."""
        if self.current_file:
            try:
                with open(self.current_file, "w", encoding="utf-8") as f:
                    yaml.dump(self.config_data, f)
                self.show_popup("Success", "Configuration saved successfully!")
            except Exception as e:
                self.show_popup("Error", f"Failed to save config: {e}")
        else:
            self.show_popup("Error", "No file loaded to save.")

    def show_popup(self, title, message):
        """Display a popup message."""
        popup_layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        popup_label = Label(text=message)
        popup_close = Button(text="Close", size_hint=(1, 0.3))
        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(popup_close)

        popup = Popup(title=title, content=popup_layout, size_hint=(0.5, 0.5))
        popup_close.bind(on_release=popup.dismiss)
        popup.open()

    def build(self):
        """Build the main UI."""
        root_layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # Top: File Controls
        file_controls = BoxLayout(size_hint_y=0.1, spacing=10)
        load_button = Button(text="Load Config", size_hint_x=0.3)
        save_button = Button(text="Save Config", size_hint_x=0.3)
        file_controls.add_widget(load_button)
        file_controls.add_widget(save_button)
        root_layout.add_widget(file_controls)

        # Middle: Grid Layout for Buttons
        self.grid = DraggableGridLayout(cols=4, spacing=5, padding=5, app=self)
        root_layout.add_widget(self.grid)

        # Bottom: Property Editor
        self.property_editor = BoxLayout(size_hint_y=0.2, spacing=10, padding=5)
        self.property_editor.add_widget(Label(text="Text:"))
        self.text_input = TextInput(hint_text="Button Text")
        self.property_editor.add_widget(self.text_input)

        self.property_editor.add_widget(Label(text="BG Color:"))
        self.color_input = TextInput(hint_text="Hex Color (e.g., #FFFFFF)")
        self.property_editor.add_widget(self.color_input)

        save_changes_button = Button(text="Save Changes", size_hint_x=0.3)
        self.property_editor.add_widget(save_changes_button)
        root_layout.add_widget(self.property_editor)

        # Bindings
        load_button.bind(on_release=self.show_file_chooser)
        save_button.bind(on_release=lambda _: self.save_config())
        save_changes_button.bind(on_release=self.update_button_properties)

        return root_layout

    def show_file_chooser(self, instance):
        """Open a file chooser to load a configuration file."""
        chooser_layout = BoxLayout(
            orientation="vertical", spacing=10, padding=10
        )
        file_chooser = FileChooserIconView(filters=["*.yml", "*.yaml"])
        chooser_layout.add_widget(file_chooser)

        chooser_buttons = BoxLayout(size_hint_y=0.2)
        load_button = Button(text="Load")
        cancel_button = Button(text="Cancel")
        chooser_buttons.add_widget(load_button)
        chooser_buttons.add_widget(cancel_button)
        chooser_layout.add_widget(chooser_buttons)

        popup = Popup(
            title="Load Config File",
            content=chooser_layout,
            size_hint=(0.8, 0.8),
        )
        cancel_button.bind(on_release=popup.dismiss)
        load_button.bind(
            on_release=lambda _: self.load_config_and_refresh(
                file_chooser.selection[0], popup
            )
        )
        popup.open()

    def load_config_and_refresh(self, file_path, popup):
        """Load the configuration and refresh the UI."""
        if self.load_config_file(file_path):
            self.refresh_buttons()
        popup.dismiss()

    def refresh_buttons(self):
        """Refresh the grid with buttons from the configuration."""
        self.grid.clear_widgets()
        if not self.config_data.get("buttons"):
            return

        for button_data in self.config_data["buttons"]:
            btn = DraggableButton(
                text=button_data.get("txt", ""),
                background_color=self.hex_to_rgba(
                    button_data.get("bg_color", "#cccccc")
                ),
            )
            btn.bind(
                on_release=lambda instance, data=button_data: self.select_button(
                    instance, data
                )
            )
            self.grid.add_widget(btn)

    def select_button(self, button, data):
        """Select a button to edit its properties."""
        self.selected_button = data
        self.text_input.text = data.get("txt", "")
        self.color_input.text = data.get("bg_color", "#cccccc")

    def update_button_properties(self, instance):
        """Update the selected button's properties."""
        if not self.selected_button:
            self.show_popup("Error", "No button selected!")
            return

        self.selected_button["txt"] = self.text_input.text
        self.selected_button["bg_color"] = self.color_input.text
        self.refresh_buttons()

    def swap_button_positions(self, index1, index2):
        """Swap button positions in the configuration."""
        (
            self.config_data["buttons"][index1],
            self.config_data["buttons"][index2],
        ) = (
            self.config_data["buttons"][index2],
            self.config_data["buttons"][index1],
        )

    @staticmethod
    def hex_to_rgba(hex_color):
        """Convert hex color to RGBA."""
        hex_color = hex_color.lstrip("#")
        return [int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4)] + [1]


if __name__ == "__main__":
    ConfigEditorApp().run()
