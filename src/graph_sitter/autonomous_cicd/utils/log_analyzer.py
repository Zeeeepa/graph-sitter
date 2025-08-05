"""Log analysis utility for error detection and pattern recognition."""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class LogAnalyzer:
    """Utility for parsing and analyzing log content."""

    def __init__(self):
        # Common log patterns
        self.timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}',  # ISO format
            r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',      # US format
            r'\w{3} \d{2} \d{2}:\d{2}:\d{2}',            # Syslog format
        ]
        
        self.log_level_patterns = [
            r'\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\b',
            r'\b(debug|info|warn|warning|error|fatal|critical)\b',
        ]

    def parse_logs(self, log_content: str) -> List[Dict[str, Any]]:
        """
        Parse log content into structured entries.
        
        Args:
            log_content: Raw log content
            
        Returns:
            List of parsed log entries
        """
        lines = log_content.split('\n')
        entries = []
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            
            entry = self._parse_log_line(line, i)
            if entry:
                entries.append(entry)
        
        return entries

    def _parse_log_line(self, line: str, line_number: int) -> Optional[Dict[str, Any]]:
        """Parse a single log line."""
        entry = {
            "line_number": line_number,
            "raw_line": line,
            "timestamp": None,
            "level": None,
            "message": line,
            "component": None,
            "thread": None,
        }
        
        # Extract timestamp
        timestamp = self._extract_timestamp(line)
        if timestamp:
            entry["timestamp"] = timestamp
        
        # Extract log level
        level = self._extract_log_level(line)
        if level:
            entry["level"] = level
        
        # Extract component/logger name
        component = self._extract_component(line)
        if component:
            entry["component"] = component
        
        # Extract thread information
        thread = self._extract_thread(line)
        if thread:
            entry["thread"] = thread
        
        # Clean up message (remove timestamp, level, etc.)
        entry["message"] = self._clean_message(line, entry)
        
        return entry

    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from log line."""
        for pattern in self.timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(0)
        return None

    def _extract_log_level(self, line: str) -> Optional[str]:
        """Extract log level from log line."""
        for pattern in self.log_level_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(0).upper()
        return None

    def _extract_component(self, line: str) -> Optional[str]:
        """Extract component/logger name from log line."""
        # Look for patterns like [component] or component:
        patterns = [
            r'\[([^\]]+)\]',
            r'(\w+):',
            r'(\w+\.\w+)',  # dotted names like module.class
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                component = match.group(1)
                # Filter out common non-component matches
                if component not in ['INFO', 'ERROR', 'DEBUG', 'WARN', 'WARNING']:
                    return component
        
        return None

    def _extract_thread(self, line: str) -> Optional[str]:
        """Extract thread information from log line."""
        # Look for thread patterns
        patterns = [
            r'Thread-(\d+)',
            r'thread-(\d+)',
            r'\[(\d+)\]',  # Thread ID in brackets
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(0)
        
        return None

    def _clean_message(self, line: str, entry: Dict[str, Any]) -> str:
        """Clean the message by removing extracted metadata."""
        message = line
        
        # Remove timestamp
        if entry["timestamp"]:
            message = message.replace(entry["timestamp"], "").strip()
        
        # Remove log level
        if entry["level"]:
            message = re.sub(rf'\b{entry["level"]}\b', "", message, flags=re.IGNORECASE).strip()
        
        # Remove component
        if entry["component"]:
            message = message.replace(f'[{entry["component"]}]', "").strip()
            message = message.replace(f'{entry["component"]}:', "").strip()
        
        # Remove thread
        if entry["thread"]:
            message = message.replace(entry["thread"], "").strip()
        
        # Clean up extra whitespace and separators
        message = re.sub(r'\s+', ' ', message).strip()
        message = re.sub(r'^[-:\s]+', '', message).strip()
        
        return message

    def extract_stack_traces(self, log_content: str) -> List[Dict[str, Any]]:
        """
        Extract stack traces from log content.
        
        Args:
            log_content: Raw log content
            
        Returns:
            List of stack trace information
        """
        stack_traces = []
        lines = log_content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for stack trace indicators
            if self._is_stack_trace_start(line):
                stack_trace = self._extract_stack_trace(lines, i)
                if stack_trace:
                    stack_traces.append(stack_trace)
                    i = stack_trace["end_line"]
            
            i += 1
        
        return stack_traces

    def _is_stack_trace_start(self, line: str) -> bool:
        """Check if line indicates start of a stack trace."""
        indicators = [
            "Traceback (most recent call last):",
            "Exception in thread",
            "Caused by:",
            "at ",  # Java stack traces
            "  File ",  # Python stack traces
        ]
        
        return any(indicator in line for indicator in indicators)

    def _extract_stack_trace(self, lines: List[str], start_line: int) -> Optional[Dict[str, Any]]:
        """Extract a complete stack trace starting from the given line."""
        stack_trace_lines = []
        current_line = start_line
        
        # Extract the stack trace
        while current_line < len(lines):
            line = lines[current_line]
            
            # Check if this line is part of the stack trace
            if (line.strip().startswith("at ") or 
                line.strip().startswith("File ") or
                line.strip().startswith("  ") or
                "Exception" in line or
                "Error" in line):
                stack_trace_lines.append(line)
            elif stack_trace_lines and not line.strip():
                # Empty line might be part of stack trace
                stack_trace_lines.append(line)
            elif stack_trace_lines:
                # End of stack trace
                break
            
            current_line += 1
        
        if not stack_trace_lines:
            return None
        
        # Parse the stack trace
        exception_type = None
        exception_message = None
        
        # Look for exception type and message
        for line in stack_trace_lines:
            if "Exception" in line or "Error" in line:
                parts = line.split(":", 1)
                if len(parts) >= 2:
                    exception_type = parts[0].strip()
                    exception_message = parts[1].strip()
                    break
        
        return {
            "start_line": start_line,
            "end_line": current_line,
            "lines": stack_trace_lines,
            "exception_type": exception_type,
            "exception_message": exception_message,
            "full_trace": "\n".join(stack_trace_lines)
        }

    def analyze_error_patterns(self, log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze log entries for error patterns and trends.
        
        Args:
            log_entries: Parsed log entries
            
        Returns:
            Analysis results
        """
        analysis = {
            "total_entries": len(log_entries),
            "error_count": 0,
            "warning_count": 0,
            "error_patterns": {},
            "time_distribution": {},
            "component_errors": {},
            "common_errors": []
        }
        
        error_messages = []
        
        for entry in log_entries:
            level = entry.get("level", "").upper()
            
            if level in ["ERROR", "FATAL", "CRITICAL"]:
                analysis["error_count"] += 1
                error_messages.append(entry["message"])
                
                # Track component errors
                component = entry.get("component", "unknown")
                if component not in analysis["component_errors"]:
                    analysis["component_errors"][component] = 0
                analysis["component_errors"][component] += 1
                
            elif level in ["WARN", "WARNING"]:
                analysis["warning_count"] += 1
            
            # Time distribution (if timestamp available)
            timestamp = entry.get("timestamp")
            if timestamp:
                try:
                    # Extract hour for distribution
                    hour = self._extract_hour_from_timestamp(timestamp)
                    if hour is not None:
                        if hour not in analysis["time_distribution"]:
                            analysis["time_distribution"][hour] = 0
                        analysis["time_distribution"][hour] += 1
                except:
                    pass
        
        # Find common error patterns
        analysis["common_errors"] = self._find_common_error_patterns(error_messages)
        
        return analysis

    def _extract_hour_from_timestamp(self, timestamp: str) -> Optional[int]:
        """Extract hour from timestamp string."""
        # Try to parse common timestamp formats
        time_patterns = [
            r'(\d{2}):\d{2}:\d{2}',  # HH:MM:SS
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, timestamp)
            if match:
                return int(match.group(1))
        
        return None

    def _find_common_error_patterns(self, error_messages: List[str]) -> List[Dict[str, Any]]:
        """Find common patterns in error messages."""
        if not error_messages:
            return []
        
        # Group similar error messages
        pattern_groups = {}
        
        for message in error_messages:
            # Normalize the message for pattern matching
            normalized = self._normalize_error_message(message)
            
            if normalized not in pattern_groups:
                pattern_groups[normalized] = {
                    "pattern": normalized,
                    "count": 0,
                    "examples": []
                }
            
            pattern_groups[normalized]["count"] += 1
            if len(pattern_groups[normalized]["examples"]) < 3:
                pattern_groups[normalized]["examples"].append(message)
        
        # Sort by frequency and return top patterns
        common_patterns = sorted(
            pattern_groups.values(),
            key=lambda x: x["count"],
            reverse=True
        )
        
        return common_patterns[:10]  # Top 10 patterns

    def _normalize_error_message(self, message: str) -> str:
        """Normalize error message for pattern matching."""
        # Remove specific values that might vary
        normalized = message
        
        # Replace numbers with placeholder
        normalized = re.sub(r'\b\d+\b', 'NUMBER', normalized)
        
        # Replace file paths with placeholder
        normalized = re.sub(r'/[^\s]+', 'PATH', normalized)
        
        # Replace URLs with placeholder
        normalized = re.sub(r'https?://[^\s]+', 'URL', normalized)
        
        # Replace UUIDs with placeholder
        normalized = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', 'UUID', normalized, flags=re.IGNORECASE)
        
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized

    def search_logs(
        self,
        log_entries: List[Dict[str, Any]],
        query: str,
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search log entries for specific patterns.
        
        Args:
            log_entries: Parsed log entries
            query: Search query (can be regex)
            case_sensitive: Whether search is case sensitive
            
        Returns:
            Matching log entries
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        
        try:
            pattern = re.compile(query, flags)
        except re.error:
            # If regex is invalid, treat as literal string
            pattern = re.compile(re.escape(query), flags)
        
        matching_entries = []
        
        for entry in log_entries:
            # Search in message and raw line
            if (pattern.search(entry["message"]) or 
                pattern.search(entry["raw_line"])):
                matching_entries.append(entry)
        
        return matching_entries

