"""
Shared utility functions for AI generation endpoints.
"""
import json
import re

from app.models.request_context import RequestContext, CharacterDetails


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


def parse_json_array_response(text: str) -> list:
    """Try to extract JSON array from LLM response"""
    # Try to find JSON array in code blocks
    json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find raw JSON array
    json_match = re.search(r'\[.*\]', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None

def get_character_details(request_context: RequestContext, character_name: str) -> CharacterDetails:
    characters = [c for c in request_context.characters if c.name == character_name]
    if not characters:
        raise ValueError(f"Character {character_name} not found in request_context")
    elif len(characters) > 1:
        raise ValueError(f"Duplicate character name {character_name}")
    return characters[0]