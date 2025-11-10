import logging

import customtkinter as ctk

from application import Application
from log import setup_logging


def main():
    setup_logging(logging.DEBUG)

    root = ctk.CTk()
    root.focus_force()
    app = Application(root)

    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    root.mainloop()


if __name__ == "__main__":
    main()
