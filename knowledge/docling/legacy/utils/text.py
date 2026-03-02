"""
Text processing utilities for the Zoocari chatbot.

Provides shared functions for text cleaning and sanitization.
"""

import html
import re


def strip_markdown(text: str) -> str:
    """
    Remove markdown formatting from text for TTS processing.

    Removes:
    - Bold (**text**)
    - Italic (*text*)
    - Headers (# ## ### etc.)
    - Links [text](url)

    Args:
        text: Text containing markdown formatting

    Returns:
        Plain text with markdown removed
    """
    result = text
    result = re.sub(r'\*\*([^*]+)\*\*', r'\1', result)  # Remove bold
    result = re.sub(r'\*([^*]+)\*', r'\1', result)  # Remove italic
    result = re.sub(r'#{1,6}\s*', '', result)  # Remove headers
    result = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', result)  # Remove links
    return result.strip()


def sanitize_html(text: str) -> str:
    """
    Sanitize text for safe HTML rendering.

    Escapes HTML special characters to prevent XSS attacks
    when rendering user input with unsafe_allow_html=True.

    Args:
        text: User-provided text that may contain HTML

    Returns:
        Escaped text safe for HTML rendering
    """
    return html.escape(text)


def load_css_file(filepath: str) -> str:
    """
    Load CSS content from a file for Streamlit injection.

    Args:
        filepath: Path to the CSS file

    Returns:
        CSS content wrapped in style tags

    Raises:
        FileNotFoundError: If the CSS file doesn't exist
    """
    with open(filepath, 'r') as f:
        css_content = f.read()
    return f"<style>\n{css_content}\n</style>"
