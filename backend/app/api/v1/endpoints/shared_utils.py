"""
Shared utility functions for AI generation endpoints.
"""
import json
import re


def parse_json_response(text: str) -> dict:
    """Try to extract JSON from LLM response"""
    # Try to find JSON in code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find raw JSON
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def parse_list_response(text: str, key: str) -> list:
    """Extract a list from LLM response"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    # Filter out lines that are just section headers
    return [line.lstrip('- ').lstrip('* ').lstrip('1234567890. ')
            for line in lines if line and not line.endswith(':')][:10]
