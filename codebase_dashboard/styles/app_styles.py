"""
Application Styles

Global styles and theme configuration for the dashboard.
"""

def get_app_styles() -> dict:
    """Get global application styles."""
    return {
        "font_family": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "line_height": "1.5",
        "color": "var(--gray-12)",
        "background": "var(--gray-1)",
    }
