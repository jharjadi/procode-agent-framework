"""
Utility functions for external agents.

Common helper functions used across all external agents for
text processing, validation, and response formatting.
"""

import re
from typing import Optional, Dict, Any
from datetime import datetime


def extract_text(message) -> str:
    """
    Extract text content from A2A message.
    
    Args:
        message: A2A message object
        
    Returns:
        Extracted text string
    """
    text = ""
    if message and hasattr(message, 'parts') and message.parts:
        for part in message.parts:
            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                text += part.root.text
            elif hasattr(part, 'text') and part.text:
                text += part.text
            elif isinstance(part, dict) and 'text' in part:
                text += part['text']
    return text.strip()


def extract_location(text: str) -> Optional[str]:
    """
    Extract location from text using simple pattern matching.
    
    Args:
        text: Input text
        
    Returns:
        Extracted location or None
        
    Examples:
        >>> extract_location("What's the weather in Melbourne?")
        "Melbourne"
        >>> extract_location("Show me forecast for Sydney, Australia")
        "Sydney, Australia"
    """
    # Common location patterns
    patterns = [
        r'in\s+([A-Z][a-zA-Z\s,]+?)(?:\?|$|\s+for|\s+today)',
        r'for\s+([A-Z][a-zA-Z\s,]+?)(?:\?|$|\s+today)',
        r'at\s+([A-Z][a-zA-Z\s,]+?)(?:\?|$|\s+today)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            location = match.group(1).strip()
            # Remove trailing punctuation
            location = re.sub(r'[,.\s]+$', '', location)
            return location
    
    return None


def extract_date(text: str) -> Optional[str]:
    """
    Extract date from text using simple pattern matching.
    
    Args:
        text: Input text
        
    Returns:
        Extracted date string or None
        
    Examples:
        >>> extract_date("What's the weather tomorrow?")
        "tomorrow"
        >>> extract_date("Show me forecast for next week")
        "next week"
    """
    # Common date patterns
    date_keywords = [
        'today', 'tomorrow', 'yesterday',
        'next week', 'this week', 'last week',
        'next month', 'this month', 'last month'
    ]
    
    text_lower = text.lower()
    for keyword in date_keywords:
        if keyword in text_lower:
            return keyword
    
    # Try to match specific dates (e.g., "January 15", "15th January")
    date_pattern = r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?\b'
    match = re.search(date_pattern, text, re.IGNORECASE)
    if match:
        return match.group(0)
    
    return None


def format_error(error: Exception, include_type: bool = True) -> str:
    """
    Format error message for user-friendly response.
    
    Args:
        error: Exception object
        include_type: Whether to include error type in message
        
    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    if include_type:
        return f"❌ Error ({error_type}): {error_msg}"
    else:
        return f"❌ {error_msg}"


def create_response(text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create standardized response dictionary.
    
    Args:
        text: Response text
        metadata: Optional metadata to include
        
    Returns:
        Response dictionary
    """
    response = {
        "text": text,
        "timestamp": datetime.now().isoformat()
    }
    
    if metadata:
        response["metadata"] = metadata
    
    return response


def validate_input(text: str, max_length: int = 10000, min_length: int = 1) -> tuple[bool, Optional[str]]:
    """
    Validate user input text.
    
    Args:
        text: Input text to validate
        max_length: Maximum allowed length
        min_length: Minimum required length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "Input text is empty"
    
    text_length = len(text)
    
    if text_length < min_length:
        return False, f"Input text too short (minimum {min_length} characters)"
    
    if text_length > max_length:
        return False, f"Input text too long (maximum {max_length} characters)"
    
    return True, None


def extract_policy_number(text: str) -> Optional[str]:
    """
    Extract insurance policy number from text.
    
    Args:
        text: Input text
        
    Returns:
        Extracted policy number or None
        
    Examples:
        >>> extract_policy_number("Check policy POL-2024-001")
        "POL-2024-001"
        >>> extract_policy_number("My policy number is INS123456")
        "INS123456"
    """
    # Common policy number patterns
    patterns = [
        r'\b(POL-\d{4}-\d{3})\b',  # POL-2024-001
        r'\b(INS\d{6,})\b',         # INS123456
        r'\b(POLICY-\d+)\b',        # POLICY-12345
        r'\b([A-Z]{2,3}\d{6,})\b'   # Generic: AB123456
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    return None


def extract_amount(text: str) -> Optional[float]:
    """
    Extract monetary amount from text.
    
    Args:
        text: Input text
        
    Returns:
        Extracted amount as float or None
        
    Examples:
        >>> extract_amount("Premium is $1,200")
        1200.0
        >>> extract_amount("Coverage of $500,000")
        500000.0
    """
    # Pattern for currency amounts
    pattern = r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
    match = re.search(pattern, text)
    
    if match:
        amount_str = match.group(1).replace(',', '')
        try:
            return float(amount_str)
        except ValueError:
            return None
    
    return None


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def sanitize_text(text: str) -> str:
    """
    Sanitize text by removing potentially harmful content.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def parse_yes_no(text: str) -> Optional[bool]:
    """
    Parse yes/no response from text.
    
    Args:
        text: Input text
        
    Returns:
        True for yes, False for no, None if unclear
    """
    text_lower = text.lower().strip()
    
    yes_patterns = ['yes', 'y', 'yeah', 'yep', 'sure', 'ok', 'okay', 'confirm', 'correct']
    no_patterns = ['no', 'n', 'nope', 'nah', 'cancel', 'incorrect']
    
    if any(pattern in text_lower for pattern in yes_patterns):
        return True
    elif any(pattern in text_lower for pattern in no_patterns):
        return False
    
    return None


def format_list(items: list, prefix: str = "•") -> str:
    """
    Format list of items as bulleted text.
    
    Args:
        items: List of items to format
        prefix: Bullet prefix
        
    Returns:
        Formatted list as string
    """
    if not items:
        return ""
    
    return "\n".join(f"{prefix} {item}" for item in items)


def format_dict(data: Dict[str, Any], indent: int = 0) -> str:
    """
    Format dictionary as readable text.
    
    Args:
        data: Dictionary to format
        indent: Indentation level
        
    Returns:
        Formatted dictionary as string
    """
    lines = []
    indent_str = "  " * indent
    
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{indent_str}{key}:")
            lines.append(format_dict(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{indent_str}{key}:")
            for item in value:
                lines.append(f"{indent_str}  • {item}")
        else:
            lines.append(f"{indent_str}{key}: {value}")
    
    return "\n".join(lines)
