#!/usr/bin/env python3
"""
Log Search CLI Tool

Provides powerful search capabilities over structured JSON logs.
Implements total machine observability for hypervelocity development.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class LogSearcher:
    """Search and filter structured JSON logs."""
    
    def __init__(self, log_dir: str = "logs/structured"):
        """
        Initialize log searcher.
        
        Args:
            log_dir: Directory containing log files
        """
        self.log_dir = Path(log_dir)
    
    def search(
        self,
        query: Optional[str] = None,
        level: Optional[str] = None,
        logger: Optional[str] = None,
        event_type: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        limit: int = 100,
        tail: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search logs with filters.
        
        Args:
            query: Text to search in message
            level: Filter by log level
            logger: Filter by logger name
            event_type: Filter by event type
            since: Show logs since this time (e.g., "1h", "30m", "2024-01-01")
            until: Show logs until this time
            limit: Maximum number of results
            tail: Show most recent logs first
            
        Returns:
            List of matching log entries
        """
        results = []
        
        # Parse time filters
        since_dt = self._parse_time(since) if since else None
        until_dt = self._parse_time(until) if until else None
        
        # Find all log files
        log_files = sorted(self.log_dir.glob("*.jsonl"))
        
        if tail:
            log_files = reversed(log_files)
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    
                    if tail:
                        lines = reversed(lines)
                    
                    for line in lines:
                        if len(results) >= limit:
                            return results
                        
                        try:
                            log_entry = json.loads(line)
                            
                            # Apply filters
                            if not self._matches_filters(
                                log_entry,
                                query=query,
                                level=level,
                                logger=logger,
                                event_type=event_type,
                                since_dt=since_dt,
                                until_dt=until_dt
                            ):
                                continue
                            
                            results.append(log_entry)
                        
                        except json.JSONDecodeError:
                            continue
            
            except Exception as e:
                print(f"Error reading {log_file}: {e}", file=sys.stderr)
        
        return results
    
    def _matches_filters(
        self,
        log_entry: Dict[str, Any],
        query: Optional[str],
        level: Optional[str],
        logger: Optional[str],
        event_type: Optional[str],
        since_dt: Optional[datetime],
        until_dt: Optional[datetime]
    ) -> bool:
        """Check if log entry matches all filters."""
        
        # Text query
        if query and query.lower() not in log_entry.get("message", "").lower():
            return False
        
        # Level filter
        if level and log_entry.get("level", "").upper() != level.upper():
            return False
        
        # Logger filter
        if logger and log_entry.get("logger", "") != logger:
            return False
        
        # Event type filter
        if event_type and log_entry.get("event_type", "") != event_type:
            return False
        
        # Time filters
        if since_dt or until_dt:
            try:
                log_time = datetime.fromisoformat(log_entry.get("timestamp", ""))
                if since_dt and log_time < since_dt:
                    return False
                if until_dt and log_time > until_dt:
                    return False
            except (ValueError, TypeError):
                pass
        
        return True
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string to datetime."""
        # Relative time (e.g., "1h", "30m", "2d")
        if time_str[-1] in ['h', 'm', 'd']:
            unit = time_str[-1]
            value = int(time_str[:-1])
            
            if unit == 'h':
                delta = timedelta(hours=value)
            elif unit == 'm':
                delta = timedelta(minutes=value)
            elif unit == 'd':
                delta = timedelta(days=value)
            
            return datetime.utcnow() - delta
        
        # Absolute time
        return datetime.fromisoformat(time_str)
    
    def format_output(
        self,
        results: List[Dict[str, Any]],
        format: str = "pretty"
    ) -> str:
        """
        Format search results.
        
        Args:
            results: List of log entries
            format: Output format (pretty, json, compact)
            
        Returns:
            Formatted output string
        """
        if format == "json":
            return json.dumps(results, indent=2)
        
        elif format == "compact":
            lines = []
            for entry in results:
                timestamp = entry.get("timestamp", "")[:19]
                level = entry.get("level", "INFO")
                message = entry.get("message", "")
                lines.append(f"{timestamp} {level:8s} {message}")
            return "\n".join(lines)
        
        else:  # pretty
            lines = []
            for entry in results:
                lines.append("=" * 80)
                lines.append(f"Timestamp: {entry.get('timestamp', '')}")
                lines.append(f"Level:     {entry.get('level', '')}")
                lines.append(f"Logger:    {entry.get('logger', '')}")
                lines.append(f"Message:   {entry.get('message', '')}")
                
                # Show additional fields
                for key, value in entry.items():
                    if key not in ['timestamp', 'level', 'logger', 'message']:
                        lines.append(f"{key:10s} {value}")
                
                lines.append("")
            
            return "\n".join(lines)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Search structured JSON logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for errors in the last hour
  %(prog)s --level error --since 1h
  
  # Search for agent executions
  %(prog)s --event-type agent_execution
  
  # Search for specific text
  %(prog)s --query "ticket created"
  
  # Show last 50 logs
  %(prog)s --tail --limit 50
  
  # Combine filters
  %(prog)s --level error --logger core.agent_router --since 30m
        """
    )
    
    parser.add_argument(
        "--query", "-q",
        help="Search text in log messages"
    )
    parser.add_argument(
        "--level", "-l",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Filter by log level"
    )
    parser.add_argument(
        "--logger",
        help="Filter by logger name"
    )
    parser.add_argument(
        "--event-type", "-e",
        help="Filter by event type"
    )
    parser.add_argument(
        "--since", "-s",
        help="Show logs since (e.g., 1h, 30m, 2d, or ISO date)"
    )
    parser.add_argument(
        "--until", "-u",
        help="Show logs until (ISO date)"
    )
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=100,
        help="Maximum number of results (default: 100)"
    )
    parser.add_argument(
        "--tail", "-t",
        action="store_true",
        help="Show most recent logs first"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["pretty", "json", "compact"],
        default="pretty",
        help="Output format (default: pretty)"
    )
    parser.add_argument(
        "--log-dir",
        default="logs/structured",
        help="Log directory (default: logs/structured)"
    )
    
    args = parser.parse_args()
    
    # Create searcher
    searcher = LogSearcher(log_dir=args.log_dir)
    
    # Search logs
    results = searcher.search(
        query=args.query,
        level=args.level,
        logger=args.logger,
        event_type=args.event_type,
        since=args.since,
        until=args.until,
        limit=args.limit,
        tail=args.tail
    )
    
    # Format and print results
    if not results:
        print("No matching logs found.", file=sys.stderr)
        sys.exit(1)
    
    output = searcher.format_output(results, format=args.format)
    print(output)
    
    # Print summary
    print(f"\n{len(results)} log entries found.", file=sys.stderr)


if __name__ == "__main__":
    main()
