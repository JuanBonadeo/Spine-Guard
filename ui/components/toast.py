import customtkinter as ctk


TOAST_COLORS = {
    "info": "#007AFF",
    "success": "#30D158",
    "warning": "#FFD60A",
    "error": "#FF453A",
}


class ToastManager:

    def __init__(self, master: ctk.CTk):
        self._master = master
        self._toasts: list[ctk.CTkFrame] = []

    def show(self, message: str, toast_type: str = "info", duration: int = 3000):
        color = TOAST_COLORS.get(toast_type, TOAST_COLORS["info"])

        toast = ctk.CTkFrame(
            self._master,
            corner_radius=10,
            border_width=1,
            border_color=color,
        )

        accent_bar = ctk.CTkFrame(toast, width=4, corner_radius=2, fg_color=color)
        accent_bar.pack(side="left", fill="y", padx=(8, 0), pady=8)

        ctk.CTkLabel(
            toast, text=message,
            font=ctk.CTkFont(size=13),
            wraplength=280,
        ).pack(side="left", padx=12, pady=10)

        close_btn = ctk.CTkButton(
            toast, text="x", width=24, height=24,
            corner_radius=12, font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            command=lambda: self._dismiss(toast),
        )
        close_btn.pack(side="right", padx=(0, 8), pady=8)

        y_offset = 16 + len(self._toasts) * 60
        toast.place(relx=1.0, x=-16, y=y_offset, anchor="ne")
        self._toasts.append(toast)

        self._master.after(duration, lambda: self._dismiss(toast))

    def _dismiss(self, toast: ctk.CTkFrame):
        if toast in self._toasts:
            self._toasts.remove(toast)
            toast.place_forget()
            toast.destroy()
            self._reposition()

    def _reposition(self):
        for i, t in enumerate(self._toasts):
            y_offset = 16 + i * 60
            t.place(relx=1.0, x=-16, y=y_offset, anchor="ne")
