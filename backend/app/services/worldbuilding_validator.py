"""
Validation service for worldbuilding content.
Provides comprehensive validation and sanitization for worldbuilding data.
"""
import re
import html
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationRule:
    """Represents a validation rule."""
    name: str
    description: str
    severity: str  # 'error', 'warning', 'info'
    validator_func: callable


@dataclass
class ValidationResult:
    """Result of validation check."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    sanitized_content: Optional[str] = None


class WorldbuildingValidator:
    """Comprehensive validator for worldbuilding content."""

    def __init__(self):
        self.max_content_length = 10000
        self.min_content_length = 10
        self.max_topic_sections = 20
        self.profanity_words = self._load_profanity_list()
        self.validation_rules = self._initialize_validation_rules()

    def _load_profanity_list(self) -> List[str]:
        """Load profanity word list for content filtering."""
        # Basic profanity list - in production, this could be loaded from a file
        return [
            'damn', 'hell', 'shit', 'fuck', 'bitch', 'ass', 'bastard',
            'crap', 'piss', 'cock', 'dick', 'pussy', 'whore', 'slut'
        ]

    def _initialize_validation_rules(self) -> List[ValidationRule]:
        """Initialize validation rules."""
        return [
            ValidationRule(
                name="length_check",
                description="Check content length limits",
                severity="error",
                validator_func=self._validate_length
            ),
            ValidationRule(
                name="structure_check",
                description="Check content structure and organization",
                severity="warning",
                validator_func=self._validate_structure
            ),
            ValidationRule(
                name="security_check",
                description="Check for security vulnerabilities",
                severity="error",
                validator_func=self._validate_security
            ),
            ValidationRule(
                name="profanity_check",
                description="Check for inappropriate content",
                severity="warning",
                validator_func=self._validate_profanity
            ),
            ValidationRule(
                name="encoding_check",
                description="Check for encoding issues",
                severity="error",
                validator_func=self._validate_encoding
            ),
            ValidationRule(
                name="format_check",
                description="Check content formatting",
                severity="info",
                validator_func=self._validate_format
            )
        ]

    def validate_content(self, content: str, strict: bool = False) -> ValidationResult:
        """
        Validate worldbuilding content comprehensively.

        Args:
            content: Content to validate
            strict: Whether to apply strict validation rules

        Returns:
            ValidationResult with validation status and details
        """
        errors = []
        warnings = []
        suggestions = []

        # Run all validation rules
        for rule in self.validation_rules:
            try:
                rule_result = rule.validator_func(content, strict)

                if rule.severity == "error":
                    errors.extend(rule_result.get('errors', []))
                elif rule.severity == "warning":
                    warnings.extend(rule_result.get('warnings', []))

                suggestions.extend(rule_result.get('suggestions', []))

            except Exception as e:
                logger.error(f"Error running validation rule {rule.name}: {str(e)}")
                if strict:
                    errors.append(f"Validation rule {rule.name} failed: {str(e)}")

        # Sanitize content
        sanitized_content = self.sanitize_content(content)

        # Determine if content is valid
        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            sanitized_content=sanitized_content
        )

    def _validate_length(self, content: str, strict: bool) -> Dict:
        """Validate content length."""
        errors = []
        warnings = []
        suggestions = []

        content_length = len(content.strip())

        if content_length == 0:
            errors.append("Content cannot be empty")
        elif content_length < self.min_content_length:
            if strict:
                errors.append(f"Content too short (minimum {self.min_content_length} characters)")
            else:
                warnings.append(f"Content is quite short (minimum {self.min_content_length} characters recommended)")
        elif content_length > self.max_content_length:
            errors.append(f"Content too long (maximum {self.max_content_length} characters)")

        if content_length < 100:
            suggestions.append("Consider adding more detail to make your worldbuilding more immersive")

        return {
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions
        }

    def _validate_structure(self, content: str, strict: bool) -> Dict:
        """Validate content structure."""
        errors = []
        warnings = []
        suggestions = []

        # Check for topic headers
        headers = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)

        if len(headers) == 0:
            suggestions.append("Consider organizing content with topic headers (## Topic Name)")
        elif len(headers) > self.max_topic_sections:
            warnings.append(f"Too many topic sections ({len(headers)}). Consider consolidating.")

        # Check for paragraph structure
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        if len(paragraphs) < 2 and len(content.strip()) > 200:
            suggestions.append("Consider breaking content into paragraphs for better readability")

        # Check for very long paragraphs
        long_paragraphs = [p for p in paragraphs if len(p) > 1000]
        if long_paragraphs:
            suggestions.append("Some paragraphs are very long. Consider breaking them up.")

        # Check for duplicate headers
        if len(headers) != len(set(headers)):
            warnings.append("Duplicate topic headers found. Consider merging or renaming.")

        return {
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions
        }

    def _validate_security(self, content: str, strict: bool) -> Dict:
        """Validate content for security issues."""
        errors = []
        warnings = []
        suggestions = []

        # Check for script injection
        script_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'onclick\s*='
        ]

        for pattern in script_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                errors.append(f"Potentially dangerous content detected: {pattern}")

        # Check for SQL injection patterns
        sql_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+.*\s+set'
        ]

        for pattern in sql_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                warnings.append(f"Potential SQL injection pattern detected: {pattern}")

        # Check for excessive HTML tags
        html_tags = re.findall(r'<[^>]+>', content)
        if len(html_tags) > 10:
            warnings.append("Content contains many HTML tags. Consider using plain text.")

        return {
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions
        }

    def _validate_profanity(self, content: str, strict: bool) -> Dict:
        """Validate content for inappropriate language."""
        errors = []
        warnings = []
        suggestions = []

        content_lower = content.lower()
        found_profanity = []

        for word in self.profanity_words:
            if word in content_lower:
                found_profanity.append(word)

        if found_profanity:
            if strict:
                errors.append(f"Inappropriate language detected: {', '.join(found_profanity)}")
            else:
                warnings.append(f"Potentially inappropriate language detected: {', '.join(found_profanity)}")

            suggestions.append("Consider using alternative language for broader audience appeal")

        return {
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions
        }

    def _validate_encoding(self, content: str, strict: bool) -> Dict:
        """Validate content encoding."""
        errors = []
        warnings = []
        suggestions = []

        try:
            # Try to encode/decode to check for encoding issues
            content.encode('utf-8').decode('utf-8')
        except UnicodeError as e:
            errors.append(f"Encoding error: {str(e)}")

        # Check for unusual characters that might cause issues
        unusual_chars = re.findall(r'[^\x00-\x7F\u00A0-\u024F\u1E00-\u1EFF]', content)
        if unusual_chars:
            unique_chars = list(set(unusual_chars))
            if len(unique_chars) > 5:
                warnings.append(f"Content contains unusual characters: {', '.join(unique_chars[:5])}...")
            else:
                warnings.append(f"Content contains unusual characters: {', '.join(unique_chars)}")

        return {
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions
        }

    def _validate_format(self, content: str, strict: bool) -> Dict:
        """Validate content formatting."""
        errors = []
        warnings = []
        suggestions = []

        # Check for consistent header formatting
        headers = re.findall(r'^(#+)\s+(.+)$', content, re.MULTILINE)
        header_levels = [len(h[0]) for h in headers]

        if header_levels:
            # Check for skipped header levels (e.g., # then ###)
            for i in range(1, len(header_levels)):
                if header_levels[i] > header_levels[i - 1] + 1:
                    suggestions.append("Consider using consistent header levels (don't skip levels)")
                    break

        # Check for inconsistent line endings
        if '\r\n' in content and '\n' in content.replace('\r\n', ''):
            warnings.append("Mixed line endings detected. Consider using consistent line endings.")

        # Check for excessive whitespace
        if re.search(r'\n\s*\n\s*\n\s*\n', content):
            suggestions.append("Consider reducing excessive blank lines for better formatting")

        # Check for trailing whitespace
        lines_with_trailing_space = [i for i, line in enumerate(content.split('\n'))
                                     if line.endswith(' ') or line.endswith('\t')]
        if lines_with_trailing_space:
            suggestions.append("Consider removing trailing whitespace from lines")

        return {
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions
        }

    def sanitize_content(self, content: str) -> str:
        """Sanitize content by removing/escaping dangerous elements."""

        # First remove dangerous content before HTML escaping
        sanitized = content

        # Remove script tags and their content
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)

        # Remove dangerous attributes
        dangerous_attrs = ['onload', 'onerror', 'onclick', 'onmouseover', 'onfocus']
        for attr in dangerous_attrs:
            sanitized = re.sub(rf'{attr}\s*=\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)

        # Remove javascript: and data: URLs
        sanitized = re.sub(r'javascript:[^"\'\s]*', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'data:text/html[^"\'\s]*', '', sanitized, flags=re.IGNORECASE)

        # HTML escape dangerous characters (after removing dangerous content)
        sanitized = html.escape(sanitized)

        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)
        sanitized = re.sub(r'\n\s*\n\s*\n+', '\n\n', sanitized)

        # Remove trailing whitespace from lines
        sanitized = '\n'.join(line.rstrip() for line in sanitized.split('\n'))

        return sanitized.strip()

    def get_content_statistics(self, content: str) -> Dict:
        """Get statistics about the content."""

        lines = content.split('\n')
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        headers = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
        words = len(content.split())

        return {
            'character_count': len(content),
            'word_count': words,
            'line_count': len(lines),
            'paragraph_count': len(paragraphs),
            'header_count': len(headers),
            'average_paragraph_length': sum(len(p) for p in paragraphs) / len(paragraphs) if paragraphs else 0,
            'topics_identified': headers,
            'estimated_reading_time_minutes': max(1, words // 200)  # Assume 200 words per minute
        }

    def suggest_improvements(self, content: str) -> List[str]:
        """Generate improvement suggestions for content."""

        suggestions = []
        stats = self.get_content_statistics(content)

        # Length-based suggestions
        if stats['word_count'] < 50:
            suggestions.append("Consider expanding your worldbuilding with more details and descriptions")
        elif stats['word_count'] > 2000:
            suggestions.append("Consider organizing this extensive content into multiple sections or documents")

        # Structure suggestions
        if stats['header_count'] == 0:
            suggestions.append("Add topic headers (## Topic Name) to organize your worldbuilding")
        elif stats['header_count'] > 10:
            suggestions.append("Consider consolidating some topics to improve organization")

        if stats['paragraph_count'] < 3 and stats['word_count'] > 100:
            suggestions.append("Break your content into multiple paragraphs for better readability")

        # Content depth suggestions
        if stats['average_paragraph_length'] < 50:
            suggestions.append("Consider adding more detail to each section")
        elif stats['average_paragraph_length'] > 500:
            suggestions.append("Consider breaking long paragraphs into smaller, more digestible sections")

        # Topic coverage suggestions
        common_topics = ['geography', 'culture', 'history', 'politics', 'magic', 'technology']
        mentioned_topics = [topic for topic in common_topics
                            if any(topic in header.lower() for header in stats['topics_identified'])]

        if len(mentioned_topics) < 3:
            missing_topics = [topic for topic in common_topics if topic not in mentioned_topics]
            suggestions.append(f"Consider adding sections about: {', '.join(missing_topics[:3])}")

        return suggestions
