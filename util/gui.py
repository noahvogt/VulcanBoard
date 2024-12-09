import sys

from kivy.factory import Factory


def error_exit_gui(config) -> None:
    popup = Factory.ErrorPopup()
    popup.message.text = config
    popup.open()
    popup.error_exit = lambda: sys.exit(1)
