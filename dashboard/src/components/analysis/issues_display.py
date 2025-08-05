"""
Issues Display Component

Comprehensive issues display with filtering, categorization, and detailed issue context.
Shows all detected issues with severity badges, search, and detailed modal views.
"""

import reflex as rx
from typing import Dict, Any, List
from ...state.app_state import AppState
from ...styles.theme import COLORS, SPACING, COMPONENT_STYLES
from ...utils.formatters import format_issue_severity, format_issue_type, format_file_path
from ..common.issue_card import issue_card
from ..common.issue_modal import issue_modal


class IssuesState(rx.State):
    """State for issues display interactions."""
    
    search_query: str = ""
    selected_issue: Dict[str, Any] = {}
    show_issue_modal: bool = False
    
    def update_search(self, query: str):
        """Update the search query and filter issues."""
        self.search_query = query.lower()
        self._apply_filters()
    
    def set_severity_filter(self, severity: str):
        """Set the severity filter."""
        AppState.filter_issues(severity=severity)
    
    def set_type_filter(self, issue_type: str):
        """Set the issue type filter."""
        AppState.filter_issues(issue_type=issue_type)
    
    def show_issue_details(self, issue: Dict[str, Any]):
        """Show detailed issue modal."""
        self.selected_issue = issue
        self.show_issue_modal = True
    
    def close_issue_modal(self):
        """Close the issue details modal."""
        self.show_issue_modal = False
        self.selected_issue = {}
    
    def _apply_filters(self):
        """Apply search filter to issues."""
        if not self.search_query:
            AppState.filtered_issues = AppState.all_issues.copy()
            return
        
        filtered = []
        for issue in AppState.all_issues:
            # Search in message, file path, function name
            searchable_text = " ".join([
                issue.get("message", ""),
                issue.get("file_path", ""),
                issue.get("function_name", ""),
                issue.get("class_name", ""),
                format_issue_type(issue.get("type", ""))
            ]).lower()
            
            if self.search_query in searchable_text:
                filtered.append(issue)
        
        AppState.filtered_issues = filtered
    
    @property
    def issue_type_options(self) -> List[str]:
        """Get available issue type options."""
        types = set()
        for issue in AppState.all_issues:
            types.add(issue.get("type", "unknown"))
        return ["all"] + sorted(list(types))
    
    @property
    def issues_by_severity(self) -> Dict[str, int]:
        """Get issue counts by severity."""
        counts = {"critical": 0, "major": 0, "minor": 0}
        for issue in AppState.filtered_issues:
            severity = issue.get("severity", "minor")
            if severity in counts:
                counts[severity] += 1
        return counts


def issues_display() -> rx.Component:
    """Main issues display component."""
    return rx.vstack(
        # Issues header with summary
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading(
                        "Code Issues",
                        size="lg",
                        color=COLORS["gray"]["900"]
                    ),
                    
                    rx.hstack(
                        _create_severity_summary("critical", IssuesState.issues_by_severity["critical"]),
                        _create_severity_summary("major", IssuesState.issues_by_severity["major"]),
                        _create_severity_summary("minor", IssuesState.issues_by_severity["minor"]),
                        spacing=SPACING["md"]
                    ),
                    
                    justify="between",
                    align="center",
                    width="100%"
                ),
                
                rx.text(
                    f"Found {len(AppState.filtered_issues)} issues in your codebase. Use filters below to focus on specific types or severities.",
                    color=COLORS["gray"]["600"],
                    size="sm"
                ),
                
                spacing=SPACING["sm"]
            ),
            
            **COMPONENT_STYLES["card"],
            margin_bottom=SPACING["lg"]
        ),
        
        # Filters and controls
        rx.box(
            rx.hstack(
                # Search bar
                rx.hstack(
                    rx.icon(tag="search", size="sm", color=COLORS["gray"]["500"]),
                    rx.input(
                        placeholder="Search issues by message, file, or function...",
                        value=IssuesState.search_query,
                        on_change=IssuesState.update_search,
                        style=COMPONENT_STYLES["input"],
                        width="400px"
                    ),
                    spacing=SPACING["sm"],
                    align="center"
                ),
                
                # Filters
                rx.hstack(
                    rx.select(
                        ["all", "critical", "major", "minor"],
                        value=AppState.issue_filter_severity,
                        on_change=IssuesState.set_severity_filter,
                        placeholder="Filter by severity",
                        size="sm"
                    ),
                    
                    rx.select(
                        IssuesState.issue_type_options,
                        value=AppState.issue_filter_type,
                        on_change=IssuesState.set_type_filter,
                        placeholder="Filter by type",
                        size="sm"
                    ),
                    
                    rx.button(
                        rx.icon(tag="refresh", size="sm"),
                        "Reset Filters",
                        on_click=lambda: [
                            IssuesState.update_search(""),
                            IssuesState.set_severity_filter("all"),
                            IssuesState.set_type_filter("all")
                        ],
                        style=COMPONENT_STYLES["button_secondary"],
                        size="sm"
                    ),
                    
                    spacing=SPACING["md"]
                ),
                
                justify="between",
                align="center",
                width="100%"
            ),
            
            **COMPONENT_STYLES["card"],
            margin_bottom=SPACING["lg"]
        ),
        
        # Issues list
        rx.box(
            rx.cond(
                len(AppState.filtered_issues) > 0,
                rx.vstack(
                    *[
                        issue_card(
                            issue=issue,
                            on_click=lambda i=issue: IssuesState.show_issue_details(i)
                        )
                        for issue in AppState.filtered_issues
                    ],
                    spacing=SPACING["md"],
                    width="100%"
                ),
                
                # Empty state
                rx.vstack(
                    rx.icon(
                        tag="check_circle",
                        size="3xl",
                        color=COLORS["success"]["500"]
                    ),
                    rx.heading(
                        "No Issues Found",
                        size="lg",
                        color=COLORS["gray"]["700"]
                    ),
                    rx.text(
                        "Great! No issues match your current filters, or your codebase is clean.",
                        color=COLORS["gray"]["500"],
                        text_align="center"
                    ),
                    spacing=SPACING["md"],
                    align="center",
                    padding=SPACING["3xl"]
                )
            ),
            
            **COMPONENT_STYLES["card"],
            min_height="400px"
        ),
        
        # Issue details modal
        issue_modal(
            issue=IssuesState.selected_issue,
            is_open=IssuesState.show_issue_modal,
            on_close=IssuesState.close_issue_modal
        ),
        
        spacing="0",
        width="100%"
    )


def _create_severity_summary(severity: str, count: int) -> rx.Component:
    """Create a severity summary badge."""
    severity_info = format_issue_severity(severity)
    
    return rx.hstack(
        rx.text(
            severity_info["icon"],
            font_size="1.1em"
        ),
        rx.vstack(
            rx.text(
                str(count),
                font_weight="700",
                color=severity_info["color"],
                margin="0"
            ),
            rx.text(
                severity_info["label"],
                color=COLORS["gray"]["600"],
                size="sm",
                margin="0"
            ),
            spacing="0",
            align="start"
        ),
        
        spacing=SPACING["sm"],
        align="center",
        padding=SPACING["sm"],
        background=severity_info["bg_color"],
        border=f"1px solid {severity_info['border_color']}",
        border_radius="8px"
    )

