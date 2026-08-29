"""Sidebar navigation helpers for the ULTRON cockpit UI."""

from __future__ import annotations

import customtkinter as ctk

from ultron.ui.ui_hud_effects import draw_sidebar_icon
from ultron.ui.ui_theme import PALETTE, font

SIDEBAR_SECTIONS = [
    ("CORE", [("dashboard", "core", "Dashboard")]),
    (
        "MONITORING & TOOLS",
        [
            ("system", "pulse", "System Monitor"),
            ("modules", "cube", "Modules"),
            ("integrations", "nodes", "Integrations"),
        ],
    ),
    ("CONFIGURATION", [("security", "shield", "Security"), ("settings", "gear", "Settings")]),
]

SIDEBAR_NAV_ITEMS = [(key, icon) for _section, items in SIDEBAR_SECTIONS for key, icon, _label in items]


def build_sidebar(parent, nav_rows: dict, on_select, on_hover) -> ctk.CTkFrame:
    """Build the labeled sidebar (icon + text rows grouped by section)."""

    bg = "#1C0709"
    sidebar = ctk.CTkFrame(parent, fg_color=bg, corner_radius=0, width=216, border_width=1, border_color=PALETTE["line"])
    sidebar.grid(row=0, column=0, sticky="ns")
    sidebar.grid_propagate(False)

    ctk.CTkLabel(
        sidebar, text="ULTRON MENU", font=font("mono", 9, "bold"), text_color=PALETTE["text_muted"]
    ).pack(anchor="w", padx=20, pady=(24, 12))

    for section_title, items in SIDEBAR_SECTIONS:
        ctk.CTkLabel(
            sidebar, text=section_title, font=font("mono", 8, "bold"), text_color=PALETTE["text_faint"]
        ).pack(anchor="w", padx=20, pady=(14, 6))

        for page_key, icon, label in items:
            row = ctk.CTkFrame(sidebar, fg_color="transparent", corner_radius=6, height=38)
            row.pack(fill="x", padx=10, pady=2)
            row.pack_propagate(False)

            icon_canvas = ctk.CTkCanvas(row, width=32, height=32, bg=bg, highlightthickness=0)
            icon_canvas.place(x=8, rely=0.5, anchor="w")
            text_label = ctk.CTkLabel(
                row, text=label.upper(), font=font("ui", 11), text_color=PALETTE["text_muted"], anchor="w"
            )
            text_label.place(x=46, rely=0.5, anchor="w")

            for widget in (row, icon_canvas, text_label):
                widget.bind("<Button-1>", lambda _event, key=page_key: on_select(key))
                widget.bind("<Enter>", lambda _event, key=page_key: on_hover(key, True))
                widget.bind("<Leave>", lambda _event, key=page_key: on_hover(key, False))

            nav_rows[page_key] = {"row": row, "icon_canvas": icon_canvas, "icon": icon, "label": text_label}

    ctk.CTkLabel(
        sidebar, text="ULTRON v1.0", font=font("mono", 8), text_color=PALETTE["text_faint"]
    ).pack(side="bottom", pady=18)

    return sidebar


def refresh_sidebar(nav_rows: dict, active_page: str, hover_page: str | None = None) -> None:
    """Redraw sidebar rows with the active page highlighted."""

    accent = PALETTE["cyan"]
    for key, entry in nav_rows.items():
        active = key == active_page
        hover = key == hover_page
        row_bg = "#2A0A0F" if active else ("#210D10" if hover else "transparent")
        entry["row"].configure(fg_color=row_bg, border_width=1 if active else 0, border_color=accent)
        entry["icon_canvas"].configure(bg=row_bg if row_bg != "transparent" else "#1C0709")
        draw_sidebar_icon(entry["icon_canvas"], entry["icon"], palette=PALETTE, small=True)
        entry["label"].configure(text_color=accent if (active or hover) else PALETTE["text_muted"])
