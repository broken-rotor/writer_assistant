"""
Test Data Generators for Context Management Testing

This module provides realistic test data generators for various story lengths,
character complexities, and context management scenarios to enable comprehensive
testing of the Writer Assistant's context management system.
"""

import random
import string
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.models.context_models import ContextType
from app.services.token_management import LayerType


@dataclass
class ContextItem:
    """Simple context item for backward compatibility."""
    content: str
    element_type: str  # Changed from ContextType to str
    priority: str  # Changed from int to str (high/medium/low)
    layer_type: LayerType
    metadata: Dict[str, Any]


class TokenTestDataGenerator:
    """Generates test data specifically for token management testing."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional seed."""
        if seed is not None:
            random.seed(seed)
    
    def generate_token_stress_test(self, target_tokens: int) -> List[ContextItem]:
        """Generate context items that target a specific token count."""
        items = []
        current_tokens = 0

        while current_tokens < target_tokens:
            remaining = target_tokens - current_tokens
            item_size = min(remaining, random.randint(100, 2000))

            content = self._generate_content(item_size * 4)  # 4 chars ≈ 1 token

            # Map numeric priority to string
            priority_val = random.randint(1, 10)
            if priority_val >= 8:
                priority_str = "high"
            elif priority_val >= 4:
                priority_str = "medium"
            else:
                priority_str = "low"

            item = ContextItem(
                content=content,
                element_type=random.choice(list(ContextType)).value,
                priority=priority_str,
                layer_type=random.choice(list(LayerType)),
                metadata={"generated": True, "target_tokens": item_size}
            )

            items.append(item)
            current_tokens += item_size

        return items
    
    def _generate_content(self, target_length: int) -> str:
        """Generate content of approximately target_length characters."""
        words = ["the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog", "and", "runs", "through", "forest"]
        content = ""
        
        while len(content) < target_length:
            word = random.choice(words)
            content += word + " "
        
        return content[:target_length].strip()


