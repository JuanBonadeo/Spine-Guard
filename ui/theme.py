import customtkinter as ctk

DARK = {
    "bg_primary": "#1E1E1E",
    "bg_sidebar": "#171717",
    "bg_card": "#2A2A2A",
    "bg_card_hover": "#333333",
    "bg_input": "#333333",
    "text_primary": "#FFFFFF",
    "text_secondary": "#A0A0A0",
    "text_muted": "#666666",
    "accent": "#007AFF",
    "accent_hover": "#0066D6",
    "success": "#30D158",
    "warning": "#FFD60A",
    "danger": "#FF453A",
    "border": "#3A3A3A",
    "divider": "#2C2C2C",
    "overlay": "#000000",
}

LIGHT = {
    "bg_primary": "#F5F5F7",
    "bg_sidebar": "#E8E8ED",
    "bg_card": "#FFFFFF",
    "bg_card_hover": "#F0F0F0",
    "bg_input": "#FFFFFF",
    "text_primary": "#1D1D1F",
    "text_secondary": "#86868B",
    "text_muted": "#AEAEB2",
    "accent": "#007AFF",
    "accent_hover": "#0056B3",
    "success": "#34C759",
    "warning": "#FF9F0A",
    "danger": "#FF3B30",
    "border": "#D2D2D7",
    "divider": "#E5E5EA",
    "overlay": "#000000",
}


class Theme:
    def __init__(self, mode: str = "dark"):
        self.current = mode
        self.colors = DARK if mode == "dark" else LIGHT

    def get(self, name: str) -> str:
        return self.colors.get(name, "#FF00FF")

    def toggle(self):
        if self.current == "dark":
            self.current = "light"
            self.colors = LIGHT
        else:
            self.current = "dark"
            self.colors = DARK
        ctk.set_appearance_mode(self.current)

    def is_dark(self) -> bool:
        return self.current == "dark"
