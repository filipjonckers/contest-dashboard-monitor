from tkinter import font


def find_font() -> str:
    common_monospace_fonts = [
        "Consolas",
        "Monaco",
        "DejaVu Sans Mono",
        "Liberation Mono",
        "Source Code Pro",
        "Fira Mono",
        "Ubuntu Mono",
        "Inconsolata",
        "PT Mono",
        "Courier New",
    ]

    available = [f for f in common_monospace_fonts if f in font.families()]
    return available[0] if available else "Courier New"
