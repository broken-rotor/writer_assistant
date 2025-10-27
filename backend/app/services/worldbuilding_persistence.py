"""
Persistence service for worldbuilding conversation state.
Handles saving and loading conversation state, topic contexts, and accumulated worldbuilding data.
"""
import json
import os
from typing import Dict, Optional, List
from datetime import datetime, UTC
from app.models.worldbuilding_models import (
    WorldbuildingConversationState, ConversationBranch, TopicContext
)


class WorldbuildingPersistenceService:
    """Service for persisting worldbuilding conversation state."""
    
    def __init__(self, storage_path: str = "data/worldbuilding_conversations"):
        self.storage_path = storage_path
        self._ensure_storage_directory()
    
    def _ensure_storage_directory(self):
        """Ensure the storage directory exists."""
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _get_conversation_file_path(self, story_id: str) -> str:
        """Get the file path for a conversation state."""
        return os.path.join(self.storage_path, f"{story_id}_conversation.json")
    
    def save_conversation_state(self, state: WorldbuildingConversationState) -> bool:
        """Save conversation state to persistent storage."""
        try:
            file_path = self._get_conversation_file_path(state.story_id)
            
            # Convert state to dictionary for JSON serialization
            state_dict = state.model_dump()
            
            # Add metadata
            state_dict['_metadata'] = {
                'saved_at': datetime.now(UTC).isoformat(),
                'version': '1.0'
            }
            
            # Write to file with atomic operation
            temp_path = f"{file_path}.tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            os.rename(temp_path, file_path)
            
            return True
            
        except Exception as e:
            print(f"Error saving conversation state for {state.story_id}: {e}")
            return False
    
    def load_conversation_state(self, story_id: str) -> Optional[WorldbuildingConversationState]:
        """Load conversation state from persistent storage."""
        try:
            file_path = self._get_conversation_file_path(story_id)
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                state_dict = json.load(f)
            
            # Remove metadata before creating model
            state_dict.pop('_metadata', None)
            
            # Create and return state object
            return WorldbuildingConversationState(**state_dict)
            
        except Exception as e:
            print(f"Error loading conversation state for {story_id}: {e}")
            return None
    
    def delete_conversation_state(self, story_id: str) -> bool:
        """Delete conversation state from persistent storage."""
        try:
            file_path = self._get_conversation_file_path(story_id)
            
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return True
            
        except Exception as e:
            print(f"Error deleting conversation state for {story_id}: {e}")
            return False
    
    def list_conversation_states(self) -> List[str]:
        """List all stored conversation state IDs."""
        try:
            if not os.path.exists(self.storage_path):
                return []
            
            story_ids = []
            for filename in os.listdir(self.storage_path):
                if filename.endswith('_conversation.json'):
                    story_id = filename.replace('_conversation.json', '')
                    story_ids.append(story_id)
            
            return story_ids
            
        except Exception as e:
            print(f"Error listing conversation states: {e}")
            return []
    
    def backup_conversation_state(self, story_id: str) -> Optional[str]:
        """Create a backup of conversation state."""
        try:
            state = self.load_conversation_state(story_id)
            if not state:
                return None
            
            # Create backup filename with timestamp
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{story_id}_conversation_backup_{timestamp}.json"
            backup_path = os.path.join(self.storage_path, "backups", backup_filename)
            
            # Ensure backup directory exists
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Save backup
            state_dict = state.model_dump()
            state_dict['_backup_metadata'] = {
                'original_story_id': story_id,
                'backup_created_at': datetime.now(UTC).isoformat(),
                'backup_version': '1.0'
            }
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, indent=2, ensure_ascii=False)
            
            return backup_path
            
        except Exception as e:
            print(f"Error creating backup for {story_id}: {e}")
            return None
    
    def restore_from_backup(self, backup_path: str) -> Optional[str]:
        """Restore conversation state from backup."""
        try:
            if not os.path.exists(backup_path):
                return None
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                state_dict = json.load(f)
            
            # Extract original story ID
            backup_metadata = state_dict.pop('_backup_metadata', {})
            original_story_id = backup_metadata.get('original_story_id')
            
            if not original_story_id:
                return None
            
            # Remove other metadata
            state_dict.pop('_metadata', None)
            
            # Create state object and save
            state = WorldbuildingConversationState(**state_dict)
            
            if self.save_conversation_state(state):
                return original_story_id
            
            return None
            
        except Exception as e:
            print(f"Error restoring from backup {backup_path}: {e}")
            return None
    
    def export_worldbuilding_summary(self, story_id: str) -> Optional[Dict]:
        """Export a summary of worldbuilding content for a story."""
        try:
            state = self.load_conversation_state(story_id)
            if not state:
                return None
            
            current_branch = state.branches.get(state.current_branch_id)
            if not current_branch:
                return None
            
            # Build comprehensive worldbuilding summary
            summary = {
                'story_id': story_id,
                'export_timestamp': datetime.now(UTC).isoformat(),
                'conversation_metadata': {
                    'total_messages': state.total_messages,
                    'current_state': state.current_state,
                    'current_topic': state.current_topic,
                    'conversation_history': state.conversation_history,
                    'created_at': state.created_at,
                    'last_updated': state.last_updated
                },
                'worldbuilding_content': {},
                'topic_summaries': {},
                'overall_progress': 0.0
            }
            
            # Extract content for each topic
            total_completeness = 0.0
            topic_count = 0
            
            for topic, context in current_branch.topic_contexts.items():
                topic_count += 1
                total_completeness += context.completeness_score
                
                summary['worldbuilding_content'][topic] = {
                    'accumulated_content': context.accumulated_content,
                    'key_elements': context.key_elements,
                    'questions_explored': context.questions_asked,
                    'completeness_score': context.completeness_score,
                    'last_updated': context.last_updated
                }
                
                # Create topic summary
                summary['topic_summaries'][topic] = {
                    'element_count': len(context.key_elements),
                    'content_length': len(context.accumulated_content),
                    'questions_count': len(context.questions_asked),
                    'completeness': context.completeness_score,
                    'status': self._get_topic_status(context.completeness_score)
                }
            
            # Calculate overall progress
            if topic_count > 0:
                summary['overall_progress'] = total_completeness / topic_count
            
            # Add accumulated worldbuilding if available
            if state.accumulated_worldbuilding:
                summary['accumulated_worldbuilding'] = state.accumulated_worldbuilding
            
            return summary
            
        except Exception as e:
            print(f"Error exporting worldbuilding summary for {story_id}: {e}")
            return None
    
    def _get_topic_status(self, completeness_score: float) -> str:
        """Get status description based on completeness score."""
        if completeness_score < 0.2:
            return "barely_started"
        elif completeness_score < 0.4:
            return "initial_exploration"
        elif completeness_score < 0.6:
            return "developing"
        elif completeness_score < 0.8:
            return "well_developed"
        else:
            return "comprehensive"
    
    def import_worldbuilding_summary(self, summary_data: Dict) -> Optional[str]:
        """Import worldbuilding summary and create conversation state."""
        try:
            story_id = summary_data.get('story_id')
            if not story_id:
                return None
            
            # Create new conversation state from summary
            now = datetime.now(UTC).isoformat()
            
            # Create topic contexts from summary
            topic_contexts = {}
            for topic, content_data in summary_data.get('worldbuilding_content', {}).items():
                topic_contexts[topic] = TopicContext(
                    topic=topic,
                    accumulated_content=content_data.get('accumulated_content', ''),
                    key_elements=content_data.get('key_elements', []),
                    questions_asked=content_data.get('questions_explored', []),
                    last_updated=content_data.get('last_updated', now),
                    completeness_score=content_data.get('completeness_score', 0.0)
                )
            
            # Create main branch
            main_branch = ConversationBranch(
                branch_id='main',
                branch_name='main',
                created_at=now,
                messages=[],
                current_topic='general',
                topic_contexts=topic_contexts
            )
            
            # Create conversation state
            metadata = summary_data.get('conversation_metadata', {})
            state = WorldbuildingConversationState(
                story_id=story_id,
                current_state=metadata.get('current_state', 'initial'),
                current_branch_id='main',
                current_topic=metadata.get('current_topic', 'general'),
                branches={'main': main_branch},
                accumulated_worldbuilding=summary_data.get('accumulated_worldbuilding', ''),
                topic_priorities={},
                conversation_history=metadata.get('conversation_history', []),
                suggested_topics=[],
                pending_questions=[],
                created_at=metadata.get('created_at', now),
                last_updated=now,
                total_messages=metadata.get('total_messages', 0)
            )
            
            # Save the imported state
            if self.save_conversation_state(state):
                return story_id
            
            return None
            
        except Exception as e:
            print(f"Error importing worldbuilding summary: {e}")
            return None
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """Clean up old backup files."""
        try:
            backup_dir = os.path.join(self.storage_path, "backups")
            if not os.path.exists(backup_dir):
                return 0
            
            cutoff_time = datetime.now(UTC).timestamp() - (days_to_keep * 24 * 60 * 60)
            deleted_count = 0
            
            for filename in os.listdir(backup_dir):
                if filename.endswith('_backup_*.json'):
                    file_path = os.path.join(backup_dir, filename)
                    file_time = os.path.getmtime(file_path)
                    
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            print(f"Error cleaning up old backups: {e}")
            return 0
    
    def get_storage_stats(self) -> Dict:
        """Get statistics about stored conversation data."""
        try:
            stats = {
                'total_conversations': 0,
                'total_size_bytes': 0,
                'oldest_conversation': None,
                'newest_conversation': None,
                'backup_count': 0,
                'backup_size_bytes': 0
            }
            
            # Main conversation files
            if os.path.exists(self.storage_path):
                for filename in os.listdir(self.storage_path):
                    if filename.endswith('_conversation.json'):
                        file_path = os.path.join(self.storage_path, filename)
                        file_size = os.path.getsize(file_path)
                        file_time = os.path.getmtime(file_path)
                        
                        stats['total_conversations'] += 1
                        stats['total_size_bytes'] += file_size
                        
                        if stats['oldest_conversation'] is None or file_time < stats['oldest_conversation']:
                            stats['oldest_conversation'] = file_time
                        
                        if stats['newest_conversation'] is None or file_time > stats['newest_conversation']:
                            stats['newest_conversation'] = file_time
            
            # Backup files
            backup_dir = os.path.join(self.storage_path, "backups")
            if os.path.exists(backup_dir):
                for filename in os.listdir(backup_dir):
                    if filename.endswith('.json'):
                        file_path = os.path.join(backup_dir, filename)
                        file_size = os.path.getsize(file_path)
                        
                        stats['backup_count'] += 1
                        stats['backup_size_bytes'] += file_size
            
            # Convert timestamps to ISO format
            if stats['oldest_conversation']:
                stats['oldest_conversation'] = datetime.fromtimestamp(
                    stats['oldest_conversation'], UTC
                ).isoformat()
            
            if stats['newest_conversation']:
                stats['newest_conversation'] = datetime.fromtimestamp(
                    stats['newest_conversation'], UTC
                ).isoformat()
            
            return stats
            
        except Exception as e:
            print(f"Error getting storage stats: {e}")
            return {}
