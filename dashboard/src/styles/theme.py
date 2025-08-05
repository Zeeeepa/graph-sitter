"""
Theme and Styling Configuration

Defines the global theme, colors, and styling for the dashboard.
"""

import reflex as rx
from typing import Dict, Any

# Color palette
COLORS = {
    # Primary colors
    "primary": {
        "50": "#eff6ff",
        "100": "#dbeafe",
        "200": "#bfdbfe", 
        "300": "#93c5fd",
        "400": "#60a5fa",
        "500": "#3b82f6",
        "600": "#2563eb",
        "700": "#1d4ed8",
        "800": "#1e40af",
        "900": "#1e3a8a",
    },
    
    # Status colors
    "success": {
        "50": "#f0fdf4",
        "100": "#dcfce7",
        "200": "#bbf7d0",
        "300": "#86efac", 
        "400": "#4ade80",
        "500": "#22c55e",
        "600": "#16a34a",
        "700": "#15803d",
        "800": "#166534",
        "900": "#14532d",
    },
    
    "warning": {
        "50": "#fffbeb",
        "100": "#fef3c7",
        "200": "#fde68a",
        "300": "#fcd34d",
        "400": "#fbbf24", 
        "500": "#f59e0b",
        "600": "#d97706",
        "700": "#b45309",
        "800": "#92400e",
        "900": "#78350f",
    },
    
    "error": {
        "50": "#fef2f2",
        "100": "#fee2e2",
        "200": "#fecaca",
        "300": "#fca5a5",
        "400": "#f87171",
        "500": "#ef4444",
        "600": "#dc2626",
        "700": "#b91c1c",
        "800": "#991b1b",
        "900": "#7f1d1d",
    },
    
    # Neutral colors
    "gray": {
        "50": "#f9fafb",
        "100": "#f3f4f6",
        "200": "#e5e7eb",
        "300": "#d1d5db",
        "400": "#9ca3af",
        "500": "#6b7280",
        "600": "#4b5563",
        "700": "#374151",
        "800": "#1f2937",
        "900": "#111827",
    }
}

# Typography
FONTS = {
    "primary": "Inter, system-ui, sans-serif",
    "mono": "JetBrains Mono, Consolas, Monaco, monospace"
}

# Spacing scale
SPACING = {
    "xs": "0.25rem",
    "sm": "0.5rem", 
    "md": "1rem",
    "lg": "1.5rem",
    "xl": "2rem",
    "2xl": "3rem",
    "3xl": "4rem"
}

# Border radius
RADIUS = {
    "sm": "0.25rem",
    "md": "0.375rem",
    "lg": "0.5rem",
    "xl": "0.75rem",
    "2xl": "1rem"
}

# Shadows
SHADOWS = {
    "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    "md": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
    "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
    "xl": "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)"
}

# Component styles
COMPONENT_STYLES: Dict[str, Dict[str, Any]] = {
    "card": {
        "background": "white",
        "border": f"1px solid {COLORS['gray']['200']}",
        "border_radius": RADIUS["lg"],
        "box_shadow": SHADOWS["sm"],
        "padding": SPACING["lg"]
    },
    
    "button_primary": {
        "background": COLORS["primary"]["600"],
        "color": "white",
        "border": "none",
        "border_radius": RADIUS["md"],
        "padding": f"{SPACING['sm']} {SPACING['lg']}",
        "font_weight": "500",
        "cursor": "pointer",
        "_hover": {
            "background": COLORS["primary"]["700"]
        }
    },
    
    "button_secondary": {
        "background": "white",
        "color": COLORS["gray"]["700"],
        "border": f"1px solid {COLORS['gray']['300']}",
        "border_radius": RADIUS["md"],
        "padding": f"{SPACING['sm']} {SPACING['lg']}",
        "font_weight": "500",
        "cursor": "pointer",
        "_hover": {
            "background": COLORS["gray"]["50"]
        }
    },
    
    "input": {
        "border": f"1px solid {COLORS['gray']['300']}",
        "border_radius": RADIUS["md"],
        "padding": f"{SPACING['sm']} {SPACING['md']}",
        "font_size": "0.875rem",
        "_focus": {
            "outline": "none",
            "border_color": COLORS["primary"]["500"],
            "box_shadow": f"0 0 0 3px {COLORS['primary']['100']}"
        }
    },
    
    "badge_critical": {
        "background": COLORS["error"]["100"],
        "color": COLORS["error"]["800"],
        "border": f"1px solid {COLORS['error']['200']}",
        "border_radius": RADIUS["md"],
        "padding": f"{SPACING['xs']} {SPACING['sm']}",
        "font_size": "0.75rem",
        "font_weight": "500"
    },
    
    "badge_major": {
        "background": COLORS["warning"]["100"],
        "color": COLORS["warning"]["800"],
        "border": f"1px solid {COLORS['warning']['200']}",
        "border_radius": RADIUS["md"],
        "padding": f"{SPACING['xs']} {SPACING['sm']}",
        "font_size": "0.75rem",
        "font_weight": "500"
    },
    
    "badge_minor": {
        "background": COLORS["warning"]["50"],
        "color": COLORS["warning"]["700"],
        "border": f"1px solid {COLORS['warning']['200']}",
        "border_radius": RADIUS["md"],
        "padding": f"{SPACING['xs']} {SPACING['sm']}",
        "font_size": "0.75rem",
        "font_weight": "500"
    }
}

# Global theme styles
theme_styles = {
    "font_family": FONTS["primary"],
    "background": COLORS["gray"]["50"],
    "color": COLORS["gray"]["900"],
    "line_height": "1.5"
}
