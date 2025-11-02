"""
Service for worldbuilding synchronization and processing.
"""
import re
import logging
from typing import List, Dict, Set, Tuple
from datetime import datetime, UTC

from app.models.worldbuilding_models import (
    ChatMessage, 
    WorldbuildingSyncRequest, 
    WorldbuildingSyncResponse,
    WorldbuildingSyncMetadata
)
from app.services.llm_inference import get_llm

logger = logging.getLogger(__name__)


class WorldbuildingSyncService:
    """Service for processing and synchronizing worldbuilding content from chat messages."""
    
    def __init__(self):
        self.worldbuilding_keywords = {
            'locations': ['world', 'place', 'location', 'city', 'town', 'village', 'kingdom', 'empire', 
                         'country', 'continent', 'planet', 'realm', 'land', 'territory', 'region',
                         'mountain', 'forest', 'desert', 'ocean', 'river', 'lake', 'island'],
            'cultures': ['culture', 'society', 'people', 'tribe', 'clan', 'race', 'species', 'nation',
                        'civilization', 'community', 'group', 'faction', 'organization'],
            'systems': ['magic', 'technology', 'system', 'power', 'ability', 'skill', 'spell',
                       'weapon', 'tool', 'device', 'machine', 'artifact'],
            'governance': ['politics', 'government', 'law', 'rule', 'ruler', 'king', 'queen', 'emperor',
                          'council', 'parliament', 'court', 'nobility', 'authority', 'power'],
            'history': ['history', 'past', 'ancient', 'old', 'legend', 'myth', 'story', 'tale',
                       'war', 'battle', 'conflict', 'event', 'era', 'age', 'period'],
            'religion': ['religion', 'god', 'goddess', 'deity', 'divine', 'sacred', 'holy', 'temple',
                        'church', 'shrine', 'priest', 'faith', 'belief', 'worship'],
            'economics': ['trade', 'commerce', 'economy', 'money', 'currency', 'gold', 'silver',
                         'merchant', 'market', 'goods', 'resources', 'wealth', 'poverty'],
            'language': ['language', 'tongue', 'dialect', 'accent', 'word', 'name', 'writing',
                        'script', 'alphabet', 'communication']
        }
    
    async def sync_worldbuilding(self, request: WorldbuildingSyncRequest) -> WorldbuildingSyncResponse:
        """
        Process chat messages and update worldbuilding content.
        """
        try:
            # Extract worldbuilding information from messages
            extracted_info = self._extract_worldbuilding_from_messages(request.messages)
            
            # Identify topics
            topics = self._identify_worldbuilding_topics(extracted_info)
            
            # Generate updated worldbuilding content
            updated_content = await self._generate_worldbuilding_content(
                request.current_worldbuilding,
                extracted_info,
                topics
            )
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(updated_content, topics)
            
            # Create metadata
            metadata = WorldbuildingSyncMetadata(
                story_id=request.story_id,
                messages_processed=len(request.messages),
                content_length=len(updated_content),
                topics_identified=topics,
                sync_timestamp=datetime.now(UTC).isoformat(),
                quality_score=quality_score
            )
            
            return WorldbuildingSyncResponse(
                success=True,
                updated_worldbuilding=updated_content,
                metadata=metadata,
                errors=[]
            )
            
        except Exception as e:
            logger.error(f"Error in worldbuilding sync: {str(e)}")
            return WorldbuildingSyncResponse(
                success=False,
                updated_worldbuilding=request.current_worldbuilding,
                metadata=WorldbuildingSyncMetadata(
                    story_id=request.story_id,
                    messages_processed=0,
                    content_length=len(request.current_worldbuilding),
                    topics_identified=[],
                    sync_timestamp=datetime.now(UTC).isoformat(),
                    quality_score=0.0
                ),
                errors=[f"Sync failed: {str(e)}"]
            )
    
    def _extract_worldbuilding_from_messages(self, messages: List[ChatMessage]) -> Dict[str, List[str]]:
        """Extract worldbuilding information from chat messages."""
        extracted = {category: [] for category in self.worldbuilding_keywords.keys()}
        
        for message in messages:
            if message.type in ['user', 'assistant']:
                content = message.content.lower()
                
                # Extract sentences that contain worldbuilding keywords
                sentences = re.split(r'[.!?]+', message.content)
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) < 10:  # Skip very short sentences
                        continue
                    
                    sentence_lower = sentence.lower()
                    
                    # Check which categories this sentence belongs to
                    for category, keywords in self.worldbuilding_keywords.items():
                        if any(keyword in sentence_lower for keyword in keywords):
                            # Add timestamp context
                            timestamp = message.timestamp[:10]  # Just the date part
                            extracted[category].append(f"[{timestamp}] {sentence}")
        
        return extracted
    
    def _identify_worldbuilding_topics(self, extracted_info: Dict[str, List[str]]) -> List[str]:
        """Identify the main worldbuilding topics present in the extracted information."""
        topics = []
        
        for category, items in extracted_info.items():
            if items:  # If there are items in this category
                topics.append(category)
        
        return topics
    
    async def _generate_worldbuilding_content(
        self, 
        current_content: str, 
        extracted_info: Dict[str, List[str]], 
        topics: List[str]
    ) -> str:
        """Generate updated worldbuilding content using LLM."""
        
        # If no new information extracted, return current content
        if not any(extracted_info.values()):
            return current_content
        
        # Try to use LLM for intelligent merging
        llm = get_llm()
        if llm:
            try:
                return await self._llm_merge_worldbuilding(llm, current_content, extracted_info, topics)
            except Exception as e:
                logger.warning(f"LLM merge failed, using fallback: {str(e)}")
        
        # Fallback to simple concatenation
        return self._simple_merge_worldbuilding(current_content, extracted_info)
    
    async def _llm_merge_worldbuilding(
        self, 
        llm, 
        current_content: str, 
        extracted_info: Dict[str, List[str]], 
        topics: List[str]
    ) -> str:
        """Use LLM to intelligently merge worldbuilding content."""
        
        # Prepare extracted information for LLM
        extracted_text = ""
        for category, items in extracted_info.items():
            if items:
                extracted_text += f"\n\n{category.upper()}:\n"
                for item in items[:5]:  # Limit to avoid token overflow
                    extracted_text += f"- {item}\n"
        
        system_prompt = """You are a worldbuilding specialist. Your task is to merge new worldbuilding information with existing content.

Guidelines:
1. Preserve all existing worldbuilding information
2. Integrate new information logically and coherently
3. Organize content by categories (locations, cultures, systems, etc.)
4. Remove duplicates and contradictions
5. Keep the content concise but comprehensive
6. Use clear headings and structure

Return only the merged worldbuilding content, no explanations."""
        
        user_prompt = f"""Current Worldbuilding:
{current_content}

New Information to Integrate:
{extracted_text}

Please merge this information into a coherent worldbuilding document."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = llm.chat_completion(messages, max_tokens=2000, temperature=0.3)
        return response.strip()
    
    def _simple_merge_worldbuilding(
        self, 
        current_content: str, 
        extracted_info: Dict[str, List[str]]
    ) -> str:
        """Simple fallback merge without LLM."""
        
        if not current_content.strip():
            # Start fresh
            content_parts = ["# Worldbuilding"]
        else:
            content_parts = [current_content, "\n\n--- Recent Updates ---"]
        
        # Add new information by category
        for category, items in extracted_info.items():
            if items:
                content_parts.append(f"\n\n## {category.title()}")
                for item in items[-3:]:  # Only recent items to avoid bloat
                    content_parts.append(f"- {item}")
        
        return "\n".join(content_parts)
    
    def _calculate_quality_score(self, content: str, topics: List[str]) -> float:
        """Calculate a quality score for the worldbuilding content."""
        if not content.strip():
            return 0.0
        
        score = 0.0
        
        # Base score for having content
        score += 0.3
        
        # Score for topic diversity (more topics = higher score)
        topic_score = min(len(topics) * 0.1, 0.4)
        score += topic_score
        
        # Score for content length (reasonable length gets points)
        length_score = min(len(content) / 1000, 0.2)
        score += length_score
        
        # Score for structure (headings, organization)
        if '#' in content:
            score += 0.1
        
        return min(score, 1.0)

