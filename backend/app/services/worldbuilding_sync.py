"""
Backend service for worldbuilding synchronization.
Handles conversion between chat conversations and worldbuilding summaries.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, UTC
import logging

from app.models.worldbuilding_models import (
    WorldbuildingConversationState, WorldbuildingChatContext,
    TopicContext, WorldbuildingTopic
)
from app.models.generation_models import ConversationMessage
from app.services.worldbuilding_state_machine import WorldbuildingStateMachine
from app.services.worldbuilding_classifier import WorldbuildingTopicClassifier
from app.services.worldbuilding_persistence import WorldbuildingPersistenceService
from app.services.worldbuilding_validator import WorldbuildingValidator

logger = logging.getLogger(__name__)


class WorldbuildingSyncService:
    """Service for synchronizing worldbuilding data between chat and summary formats."""
    
    def __init__(
        self,
        state_machine: Optional[WorldbuildingStateMachine] = None,
        classifier: Optional[WorldbuildingTopicClassifier] = None,
        persistence: Optional[WorldbuildingPersistenceService] = None,
        validator: Optional[WorldbuildingValidator] = None
    ):
        self.state_machine = state_machine or WorldbuildingStateMachine()
        self.classifier = classifier or WorldbuildingTopicClassifier()
        self.persistence = persistence or WorldbuildingPersistenceService()
        self.validator = validator or WorldbuildingValidator()
        
        # Configuration
        self.max_summary_length = 5000
        self.min_content_threshold = 50
        self.topic_weight_factors = {
            'geography': 1.2,
            'culture': 1.1,
            'magic_system': 1.3,
            'politics': 1.0,
            'history': 1.1,
            'technology': 1.0,
            'economy': 0.9,
            'religion': 1.0,
            'characters': 1.2,
            'languages': 0.8,
            'conflicts': 1.1,
            'organizations': 1.0,
            'general': 0.7
        }
    
    async def sync_conversation_to_worldbuilding(
        self,
        story_id: str,
        messages: List[ConversationMessage],
        current_worldbuilding: str = ""
    ) -> Tuple[str, Dict]:
        """
        Convert conversation messages to worldbuilding summary.
        
        Args:
            story_id: Story identifier
            messages: List of conversation messages
            current_worldbuilding: Existing worldbuilding content
            
        Returns:
            Tuple of (updated_worldbuilding, sync_metadata)
        """
        try:
            logger.info(f"Starting worldbuilding sync for story {story_id}")
            
            # Get or create conversation state
            conversation_state = self.state_machine.get_or_create_conversation_state(story_id)
            
            # Process messages and extract worldbuilding content
            extracted_content = await self._extract_worldbuilding_content(
                messages, conversation_state
            )
            
            # Merge with existing worldbuilding
            updated_worldbuilding = self._merge_worldbuilding_content(
                current_worldbuilding, extracted_content
            )
            
            # Generate sync metadata
            sync_metadata = {
                'story_id': story_id,
                'messages_processed': len(messages),
                'content_length': len(updated_worldbuilding),
                'topics_identified': list(extracted_content.keys()),
                'sync_timestamp': datetime.now(UTC).isoformat(),
                'quality_score': self._calculate_quality_score(extracted_content)
            }
            
            # Store sync result
            await self._store_sync_result(story_id, updated_worldbuilding, sync_metadata)
            
            logger.info(f"Worldbuilding sync completed for story {story_id}")
            return updated_worldbuilding, sync_metadata
            
        except Exception as e:
            logger.error(f"Error syncing worldbuilding for story {story_id}: {str(e)}")
            raise
    
    async def _extract_worldbuilding_content(
        self,
        messages: List[ConversationMessage],
        conversation_state: WorldbuildingConversationState
    ) -> Dict[WorldbuildingTopic, str]:
        """Extract worldbuilding content organized by topic."""
        
        topic_content = {}
        
        for message in messages:
            if message.role not in ['user', 'assistant']:
                continue
                
            # Classify message topic
            classification = self.classifier.classify_message(
                message.content, conversation_state.current_topic
            )
            
            primary_topic = classification.primary_topic
            
            # Extract relevant content based on message type
            if message.role == 'user':
                content = self._extract_user_worldbuilding(message.content)
            else:  # assistant
                content = self._extract_assistant_worldbuilding(message.content)
            
            if content and len(content) >= self.min_content_threshold:
                if primary_topic not in topic_content:
                    topic_content[primary_topic] = []
                
                topic_content[primary_topic].append({
                    'content': content,
                    'timestamp': message.timestamp,
                    'confidence': classification.confidence,
                    'message_type': message.role
                })
        
        # Convert to structured summaries
        structured_content = {}
        for topic, content_list in topic_content.items():
            structured_content[topic] = self._create_topic_summary(topic, content_list)
        
        return structured_content
    
    def _extract_user_worldbuilding(self, content: str) -> str:
        """Extract worldbuilding information from user messages."""
        # User messages are typically direct worldbuilding input
        # Filter out questions and focus on descriptive content
        
        sentences = content.split('.')
        worldbuilding_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Skip questions
            if sentence.endswith('?'):
                continue
                
            # Skip very short sentences
            if len(sentence) < 20:
                continue
                
            # Look for descriptive content
            descriptive_indicators = [
                'is', 'are', 'has', 'have', 'contains', 'features',
                'located', 'known for', 'characterized by', 'consists of',
                'rule', 'rules', 'governed', 'controlled', 'led by',
                'called', 'named', 'divided into', 'made up of',
                'built', 'constructed', 'established', 'founded'
            ]
            
            if any(indicator in sentence.lower() for indicator in descriptive_indicators):
                worldbuilding_sentences.append(sentence)
        
        return '. '.join(worldbuilding_sentences)
    
    def _extract_assistant_worldbuilding(self, content: str) -> str:
        """Extract worldbuilding insights from assistant messages."""
        # Assistant messages may contain worldbuilding suggestions and expansions
        
        sentences = content.split('.')
        worldbuilding_sentences = []
        
        worldbuilding_keywords = [
            'world', 'setting', 'location', 'culture', 'society', 'history',
            'magic', 'technology', 'politics', 'religion', 'geography',
            'species', 'kingdom', 'empire', 'city', 'customs', 'traditions'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 30:
                continue
                
            # Check for worldbuilding keywords
            if any(keyword in sentence.lower() for keyword in worldbuilding_keywords):
                # Avoid meta-commentary about worldbuilding
                meta_phrases = [
                    'let\'s explore', 'you could', 'consider', 'what if',
                    'tell me more', 'would you like', 'how about'
                ]
                
                if not any(phrase in sentence.lower() for phrase in meta_phrases):
                    worldbuilding_sentences.append(sentence)
        
        return '. '.join(worldbuilding_sentences)
    
    def _create_topic_summary(self, topic: WorldbuildingTopic, content_list: List[Dict]) -> str:
        """Create a structured summary for a specific topic."""
        
        if not content_list:
            return ""
        
        # Sort by timestamp and confidence
        sorted_content = sorted(
            content_list,
            key=lambda x: (x['timestamp'], x['confidence']),
            reverse=True
        )
        
        # Combine content with deduplication
        combined_content = []
        seen_content = set()
        
        for item in sorted_content:
            content = item['content'].strip()
            if content and content not in seen_content:
                combined_content.append(content)
                seen_content.add(content)
        
        # Create topic header
        topic_name = topic.replace('_', ' ').title()
        summary = f"## {topic_name}\n\n"
        
        # Add content
        summary += '\n\n'.join(combined_content)
        
        return summary
    
    def _merge_worldbuilding_content(
        self,
        existing: str,
        extracted: Dict[WorldbuildingTopic, str]
    ) -> str:
        """Merge existing worldbuilding with newly extracted content."""
        
        if not extracted:
            return existing
        
        if not existing.strip():
            # No existing content, create new structure
            return self._create_structured_worldbuilding(extracted)
        
        # Parse existing content to identify topics
        existing_topics = self._parse_existing_topics(existing)
        
        # Merge topics
        merged_topics = existing_topics.copy()
        for topic, content in extracted.items():
            if topic in merged_topics:
                # Merge with existing topic content
                merged_topics[topic] = self._merge_topic_content(
                    merged_topics[topic], content
                )
            else:
                # Add new topic
                merged_topics[topic] = content
        
        # Reconstruct worldbuilding
        return self._create_structured_worldbuilding(merged_topics)
    
    def _parse_existing_topics(self, existing: str) -> Dict[WorldbuildingTopic, str]:
        """Parse existing worldbuilding content to identify topics."""
        
        topics = {}
        current_topic = None
        current_content = []
        
        lines = existing.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check for topic headers
            if line.startswith('##'):
                # Save previous topic
                if current_topic and current_content:
                    topics[current_topic] = '\n'.join(current_content)
                
                # Start new topic
                topic_name = line.replace('##', '').strip().lower().replace(' ', '_')
                
                # Map to known topics
                for known_topic in WorldbuildingTopic.__args__:
                    if known_topic.replace('_', ' ') in topic_name:
                        current_topic = known_topic
                        break
                else:
                    current_topic = 'general'
                
                current_content = []
            
            elif line and current_topic:
                current_content.append(line)
        
        # Save last topic
        if current_topic and current_content:
            topics[current_topic] = '\n'.join(current_content)
        
        return topics
    
    def _merge_topic_content(self, existing: str, new: str) -> str:
        """Merge content for a specific topic."""
        
        if not new.strip():
            return existing
        
        if not existing.strip():
            return new
        
        # Simple merge - append new content with separator
        return f"{existing}\n\n--- Recent Updates ---\n{new}"
    
    def _create_structured_worldbuilding(self, topics: Dict[WorldbuildingTopic, str]) -> str:
        """Create structured worldbuilding content from topics."""
        
        if not topics:
            return ""
        
        # Order topics by importance
        topic_order = [
            'geography', 'culture', 'history', 'politics', 'magic_system',
            'technology', 'religion', 'characters', 'organizations',
            'conflicts', 'economy', 'languages', 'general'
        ]
        
        sections = []
        
        for topic in topic_order:
            if topic in topics and topics[topic].strip():
                sections.append(topics[topic])
        
        # Add any remaining topics
        for topic, content in topics.items():
            if topic not in topic_order and content.strip():
                sections.append(content)
        
        result = '\n\n'.join(sections)
        
        # Truncate if too long
        if len(result) > self.max_summary_length:
            result = result[:self.max_summary_length - 50] + '\n\n[Content truncated...]'
        
        return result
    
    def _calculate_quality_score(self, extracted_content: Dict[WorldbuildingTopic, str]) -> float:
        """Calculate quality score for extracted worldbuilding content."""
        
        if not extracted_content:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for topic, content in extracted_content.items():
            if not content.strip():
                continue
                
            # Base score from content length
            length_score = min(len(content) / 500, 1.0)
            
            # Topic importance weight
            weight = self.topic_weight_factors.get(topic, 1.0)
            
            # Content structure score (presence of headers, organization)
            structure_score = 0.5
            if '##' in content:
                structure_score += 0.3
            if len(content.split('\n\n')) > 1:
                structure_score += 0.2
            
            topic_score = (length_score * 0.7 + structure_score * 0.3) * weight
            
            total_score += topic_score
            total_weight += weight
        
        return min(total_score / total_weight if total_weight > 0 else 0.0, 1.0)
    
    async def _store_sync_result(
        self,
        story_id: str,
        worldbuilding: str,
        metadata: Dict
    ) -> None:
        """Store sync result for future reference."""
        
        try:
            sync_record = {
                'story_id': story_id,
                'worldbuilding_content': worldbuilding,
                'metadata': metadata,
                'created_at': datetime.now(UTC).isoformat()
            }
            
            # Store using persistence service
            await self.persistence.store_sync_record(story_id, sync_record)
            
        except Exception as e:
            logger.error(f"Failed to store sync result for story {story_id}: {str(e)}")
            # Don't raise - sync can continue without storage
    
    async def get_sync_history(self, story_id: str, limit: int = 10) -> List[Dict]:
        """Get sync history for a story."""
        
        try:
            return await self.persistence.get_sync_history(story_id, limit)
        except Exception as e:
            logger.error(f"Failed to get sync history for story {story_id}: {str(e)}")
            return []
    
    def validate_worldbuilding_content(self, content: str, strict: bool = False) -> Tuple[bool, List[str]]:
        """Validate worldbuilding content and return errors if any."""
        
        validation_result = self.validator.validate_content(content, strict=strict)
        
        # Combine errors and warnings for backward compatibility
        all_issues = validation_result.errors.copy()
        if strict:
            all_issues.extend(validation_result.warnings)
        
        return validation_result.is_valid, all_issues
    
    def get_content_suggestions(self, content: str) -> List[str]:
        """Get improvement suggestions for worldbuilding content."""
        return self.validator.suggest_improvements(content)
    
    def sanitize_worldbuilding_content(self, content: str) -> str:
        """Sanitize worldbuilding content for security."""
        return self.validator.sanitize_content(content)
