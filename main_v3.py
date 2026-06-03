import customtkinter as ctk
from app import SpineGuardApp


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = SpineGuardApp()
    app.mainloop()


if __name__ == "__main__":
    main()
