"""
Plot Outline Extractor Service for Writer Assistant.

This service extracts chapter-relevant plot outline information from the story's
plot outline and converts it into PlotElement objects for structured context.
"""

import logging
from typing import List, Optional, Dict, Any
import re
import json

from app.models.generation_models import PlotElement

logger = logging.getLogger(__name__)


class PlotOutlineExtractor:
    """Service for extracting chapter-relevant plot outline information."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_chapter_outline_elements(
        self,
        plot_outline_content: Optional[str],
        draft_outline_items: Optional[List[Dict[str, Any]]],
        chapter_number: int,
        story_context: Optional[Dict[str, Any]] = None
    ) -> List[PlotElement]:
        """
        Extract plot outline elements relevant to a specific chapter.
        
        Args:
            plot_outline_content: The main plot outline content string
            draft_outline_items: List of structured outline items from frontend
            chapter_number: The chapter number to extract context for
            story_context: Additional story context for better extraction
            
        Returns:
            List of PlotElement objects with chapter-relevant plot information
        """
        plot_elements = []
        
        try:
            # Extract from structured draft outline items first (preferred)
            if draft_outline_items:
                plot_elements.extend(
                    self._extract_from_draft_items(draft_outline_items, chapter_number)
                )
            
            # Extract from plot outline content as fallback/supplement
            if plot_outline_content:
                plot_elements.extend(
                    self._extract_from_content(plot_outline_content, chapter_number, story_context)
                )
            
            # Remove duplicates and prioritize elements
            plot_elements = self._deduplicate_and_prioritize(plot_elements)
            
            self.logger.info(f"Extracted {len(plot_elements)} plot outline elements for chapter {chapter_number}")
            
        except Exception as e:
            self.logger.error(f"Error extracting plot outline elements: {str(e)}")
            # Return empty list on error to maintain backward compatibility
            
        return plot_elements
    
    def _extract_from_draft_items(
        self, 
        draft_items: List[Dict[str, Any]], 
        chapter_number: int
    ) -> List[PlotElement]:
        """Extract plot elements from structured draft outline items."""
        elements = []
        
        for item in draft_items:
            try:
                # Check if this item is relevant to the current chapter
                if self._is_item_relevant_to_chapter(item, chapter_number):
                    element = PlotElement(
                        id=f"outline_item_{item.get('id', 'unknown')}",
                        type="chapter_outline",
                        content=self._format_outline_item_content(item),
                        priority=self._determine_item_priority(item, chapter_number),
                        tags=self._extract_item_tags(item),
                        metadata={
                            "chapter_number": chapter_number,
                            "source": "draft_outline_item",
                            "item_id": item.get('id'),
                            "item_type": item.get('type', 'unknown'),
                            "order": item.get('order', 0),
                            "outline_summary": item.get('description', '')[:200] + "..." if len(item.get('description', '')) > 200 else item.get('description', '')
                        }
                    )
                    elements.append(element)
                    
            except Exception as e:
                self.logger.warning(f"Error processing draft outline item {item.get('id', 'unknown')}: {str(e)}")
                continue
        
        return elements
    
    def _extract_from_content(
        self, 
        content: str, 
        chapter_number: int,
        story_context: Optional[Dict[str, Any]] = None
    ) -> List[PlotElement]:
        """Extract plot elements from free-form plot outline content."""
        elements = []
        
        try:
            # Split content into logical sections
            sections = self._split_content_into_sections(content)
            
            for i, section in enumerate(sections):
                if self._is_section_relevant_to_chapter(section, chapter_number):
                    element = PlotElement(
                        id=f"content_section_{i}",
                        type="chapter_outline",
                        content=section.strip(),
                        priority=self._determine_content_priority(section, chapter_number),
                        tags=self._extract_content_tags(section),
                        metadata={
                            "chapter_number": chapter_number,
                            "source": "plot_outline_content",
                            "section_index": i,
                            "outline_summary": section[:200] + "..." if len(section) > 200 else section
                        }
                    )
                    elements.append(element)
                    
        except Exception as e:
            self.logger.warning(f"Error extracting from plot outline content: {str(e)}")
        
        return elements
    
    def _is_item_relevant_to_chapter(self, item: Dict[str, Any], chapter_number: int) -> bool:
        """Determine if a draft outline item is relevant to the specified chapter."""
        # Check if item explicitly mentions chapter number
        item_text = f"{item.get('title', '')} {item.get('description', '')}".lower()
        
        # Look for chapter references
        chapter_patterns = [
            rf"chapter\s*{chapter_number}\b",
            rf"ch\s*{chapter_number}\b",
            rf"#{chapter_number}\b"
        ]
        
        for pattern in chapter_patterns:
            if re.search(pattern, item_text, re.IGNORECASE):
                return True
        
        # Check item order/position for sequential relevance
        item_order = item.get('order', 0)
        if item_order > 0:
            # Assume items are roughly sequential with chapters
            # Include items around the chapter number for context
            return abs(item_order - chapter_number) <= 2
        
        # Check item type for general relevance
        item_type = item.get('type', '').lower()
        if item_type in ['chapter', 'scene', 'plot-point']:
            return True
        
        return False
    
    def _is_section_relevant_to_chapter(self, section: str, chapter_number: int) -> bool:
        """Determine if a content section is relevant to the specified chapter."""
        section_lower = section.lower()
        
        # Look for chapter references
        chapter_patterns = [
            rf"chapter\s*{chapter_number}\b",
            rf"ch\s*{chapter_number}\b",
            rf"#{chapter_number}\b"
        ]
        
        for pattern in chapter_patterns:
            if re.search(pattern, section_lower):
                return True
        
        # Look for sequential indicators
        if len(section.strip()) > 50:  # Only consider substantial sections
            return True
        
        return False
    
    def _split_content_into_sections(self, content: str) -> List[str]:
        """Split plot outline content into logical sections."""
        # Split by common section delimiters
        delimiters = [
            r'\n\s*Chapter\s+\d+',
            r'\n\s*Ch\s+\d+',
            r'\n\s*#\d+',
            r'\n\s*\d+\.',
            r'\n\s*-\s*',
            r'\n\n+'
        ]
        
        sections = [content]
        
        for delimiter in delimiters:
            new_sections = []
            for section in sections:
                parts = re.split(delimiter, section, flags=re.IGNORECASE)
                new_sections.extend([part.strip() for part in parts if part.strip()])
            sections = new_sections
        
        # Filter out very short sections
        return [section for section in sections if len(section.strip()) > 20]
    
    def _format_outline_item_content(self, item: Dict[str, Any]) -> str:
        """Format a draft outline item into content for PlotElement."""
        title = item.get('title', '')
        description = item.get('description', '')
        
        if title and description:
            return f"{title}: {description}"
        elif title:
            return title
        elif description:
            return description
        else:
            return "Plot outline item"
    
    def _determine_item_priority(self, item: Dict[str, Any], chapter_number: int) -> str:
        """Determine priority level for a draft outline item."""
        # High priority for items that directly reference the chapter
        item_text = f"{item.get('title', '')} {item.get('description', '')}".lower()
        
        chapter_patterns = [
            rf"chapter\s*{chapter_number}\b",
            rf"ch\s*{chapter_number}\b"
        ]
        
        for pattern in chapter_patterns:
            if re.search(pattern, item_text, re.IGNORECASE):
                return "high"
        
        # Medium priority for items with relevant types
        item_type = item.get('type', '').lower()
        if item_type in ['chapter', 'scene', 'plot-point']:
            return "medium"
        
        return "low"
    
    def _determine_content_priority(self, section: str, chapter_number: int) -> str:
        """Determine priority level for a content section."""
        section_lower = section.lower()
        
        # High priority for sections that directly reference the chapter
        chapter_patterns = [
            rf"chapter\s*{chapter_number}\b",
            rf"ch\s*{chapter_number}\b"
        ]
        
        for pattern in chapter_patterns:
            if re.search(pattern, section_lower):
                return "high"
        
        # Medium priority for substantial sections
        if len(section.strip()) > 100:
            return "medium"
        
        return "low"
    
    def _extract_item_tags(self, item: Dict[str, Any]) -> List[str]:
        """Extract tags from a draft outline item."""
        tags = ["plot_outline", "chapter_context"]
        
        # Add type-based tags
        item_type = item.get('type', '')
        if item_type:
            tags.append(f"type_{item_type}")
        
        # Add order-based tags
        order = item.get('order', 0)
        if order > 0:
            tags.append(f"order_{order}")
        
        return tags
    
    def _extract_content_tags(self, section: str) -> List[str]:
        """Extract tags from a content section."""
        tags = ["plot_outline", "chapter_context", "content_section"]
        
        # Add content-based tags
        section_lower = section.lower()
        
        if "conflict" in section_lower:
            tags.append("conflict")
        if "resolution" in section_lower:
            tags.append("resolution")
        if "character" in section_lower:
            tags.append("character_focus")
        if "scene" in section_lower:
            tags.append("scene")
        
        return tags
    
    def _deduplicate_and_prioritize(self, elements: List[PlotElement]) -> List[PlotElement]:
        """Remove duplicates and prioritize elements."""
        # Remove elements with very similar content
        unique_elements = []
        seen_content = set()
        
        # Sort by priority (high first)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        elements.sort(key=lambda x: priority_order.get(x.priority, 3))
        
        for element in elements:
            # Create a normalized version of content for comparison
            normalized_content = re.sub(r'\s+', ' ', element.content.lower().strip())
            
            # Check for substantial overlap with existing elements
            is_duplicate = False
            for seen in seen_content:
                if self._calculate_similarity(normalized_content, seen) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_elements.append(element)
                seen_content.add(normalized_content)
        
        # Limit to reasonable number of elements
        return unique_elements[:5]  # Max 5 plot outline elements per chapter
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        if not text1 or not text2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0


# Global instance for use throughout the application
plot_outline_extractor = PlotOutlineExtractor()


def get_plot_outline_extractor() -> PlotOutlineExtractor:
    """Get the global plot outline extractor instance."""
    return plot_outline_extractor
