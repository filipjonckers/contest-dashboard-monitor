import logging

import customtkinter as ctk

from src.contest_scoreboard_monitor.application import Application
from src.contest_scoreboard_monitor.log import setup_logging
from src.contest_scoreboard_monitor.userconfig import load_user_config


def main():
    setup_logging(logging.INFO)
    load_user_config()

    root = ctk.CTk()
    root.focus_force()
    app = Application(root)

    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    root.mainloop()


if __name__ == "__main__":
    main()
