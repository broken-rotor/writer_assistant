"""
Context State Manager for Writer Assistant API.

This service handles context state serialization and deserialization for
client-side persistence. The server remains completely stateless - all context
state is returned to the client and sent back on subsequent requests.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass
import uuid
import base64
import gzip

from app.models.context_models import (
    StructuredContextContainer,
    BaseContextElement,
    ContextProcessingConfig,
    AgentType,
    ComposePhase
)

logger = logging.getLogger(__name__)


@dataclass
class ContextState:
    """Represents context state that can be serialized for client-side storage."""

    state_id: str
    story_id: Optional[str]
    created_at: datetime
    last_updated: datetime
    context_container: StructuredContextContainer
    processing_history: List[Dict[str, Any]]
    state_metadata: Dict[str, Any]
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            'state_id': self.state_id,
            'story_id': self.story_id,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'context_container': self.context_container.model_dump(),
            'processing_history': self.processing_history,
            'state_metadata': self.state_metadata,
            'version': self.version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextState':
        """Create state from dictionary."""
        return cls(
            state_id=data['state_id'],
            story_id=data.get('story_id'),
            created_at=datetime.fromisoformat(data['created_at']),
            last_updated=datetime.fromisoformat(data['last_updated']),
            context_container=StructuredContextContainer(**data['context_container']),
            processing_history=data.get('processing_history', []),
            state_metadata=data.get('state_metadata', {}),
            version=data.get('version', '1.0')
        )


class ContextStateManager:
    """
    Stateless service for context state serialization and management.

    This service provides:
    - Context state serialization for client-side storage
    - Context state deserialization from client requests
    - Context state compression and optimization
    - Processing history management
    """

    def __init__(
        self,
        max_processing_history: int = 50,
        enable_compression: bool = True,
        compression_threshold: int = 1000  # bytes
    ):
        """
        Initialize the context state manager.

        Args:
            max_processing_history: Maximum processing history entries per state
            enable_compression: Whether to compress serialized state
            compression_threshold: Minimum size in bytes to trigger compression
        """
        self.max_processing_history = max_processing_history
        self.enable_compression = enable_compression
        self.compression_threshold = compression_threshold

        logger.info(
            f"ContextStateManager initialized: compression={enable_compression}, history_limit={max_processing_history}")

    def create_initial_state(
        self,
        story_id: Optional[str] = None,
        initial_context: Optional[StructuredContextContainer] = None,
        state_metadata: Optional[Dict[str, Any]] = None
    ) -> ContextState:
        """
        Create a new context state.

        Args:
            story_id: Optional story ID for the state
            initial_context: Initial context container
            state_metadata: Additional state metadata

        Returns:
            ContextState object
        """
        state_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Create initial context container if not provided
        if initial_context is None:
            initial_context = StructuredContextContainer()

        state = ContextState(
            state_id=state_id,
            story_id=story_id,
            created_at=now,
            last_updated=now,
            context_container=initial_context,
            processing_history=[],
            state_metadata=state_metadata or {}
        )

        logger.debug(f"Created context state {state_id} for story {story_id}")
        return state

    def serialize_state(self, state: ContextState) -> str:
        """
        Serialize context state to string for client-side storage.

        Args:
            state: ContextState to serialize

        Returns:
            Serialized state string (base64 encoded, optionally compressed)
        """
        try:
            # Convert to JSON
            state_dict = state.to_dict()
            json_str = json.dumps(state_dict, separators=(',', ':'))
            json_bytes = json_str.encode('utf-8')

            # Compress if enabled and above threshold
            if self.enable_compression and len(json_bytes) > self.compression_threshold:
                compressed_bytes = gzip.compress(json_bytes)
                # Add compression marker
                final_bytes = b'GZIP:' + compressed_bytes
                logger.debug(f"Compressed state {state.state_id}: {len(json_bytes)} -> {len(compressed_bytes)} bytes")
            else:
                final_bytes = json_bytes

            # Base64 encode for safe transmission
            encoded = base64.b64encode(final_bytes).decode('ascii')
            return encoded

        except Exception as e:
            logger.error(f"Error serializing context state {state.state_id}: {e}")
            raise

    def deserialize_state(self, serialized_state: str) -> ContextState:
        """
        Deserialize context state from client-provided string.

        Args:
            serialized_state: Serialized state string from client

        Returns:
            ContextState object
        """
        try:
            # Base64 decode
            decoded_bytes = base64.b64decode(serialized_state.encode('ascii'))

            # Check for compression marker
            if decoded_bytes.startswith(b'GZIP:'):
                # Decompress
                compressed_bytes = decoded_bytes[5:]  # Remove 'GZIP:' marker
                json_bytes = gzip.decompress(compressed_bytes)
                logger.debug(f"Decompressed state: {len(compressed_bytes)} -> {len(json_bytes)} bytes")
            else:
                json_bytes = decoded_bytes

            # Parse JSON
            json_str = json_bytes.decode('utf-8')
            state_dict = json.loads(json_str)

            # Create ContextState object
            state = ContextState.from_dict(state_dict)
            logger.debug(f"Deserialized context state {state.state_id}")
            return state

        except Exception as e:
            logger.error(f"Error deserializing context state: {e}")
            raise

    def update_state_context(
        self,
        state: ContextState,
        context_container: StructuredContextContainer,
        processing_metadata: Optional[Dict[str, Any]] = None
    ) -> ContextState:
        """
        Update the context container in a state (returns new state).

        Args:
            state: Current context state
            context_container: Updated context container
            processing_metadata: Metadata about the processing operation

        Returns:
            Updated ContextState object
        """
        # Update context container
        state.context_container = context_container
        state.last_updated = datetime.now(timezone.utc)

        # Add processing history entry
        if processing_metadata:
            history_entry = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'operation': 'context_update',
                'metadata': processing_metadata
            }
            state.processing_history.append(history_entry)

            # Limit history size
            if len(state.processing_history) > self.max_processing_history:
                state.processing_history = state.processing_history[-self.max_processing_history:]

        logger.debug(f"Updated context for state {state.state_id}")
        return state

    def add_processing_history(
        self,
        state: ContextState,
        operation: str,
        metadata: Dict[str, Any]
    ) -> ContextState:
        """
        Add a processing history entry to a state (returns new state).

        Args:
            state: Current context state
            operation: Operation name
            metadata: Operation metadata

        Returns:
            Updated ContextState object
        """
        history_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'operation': operation,
            'metadata': metadata
        }

        state.processing_history.append(history_entry)

        # Limit history size
        if len(state.processing_history) > self.max_processing_history:
            state.processing_history = state.processing_history[-self.max_processing_history:]

        state.last_updated = datetime.now(timezone.utc)

        logger.debug(f"Added processing history to state {state.state_id}: {operation}")
        return state

    def compress_state(self, state_data: bytes) -> bytes:
        """
        Compress state data for transmission.

        Args:
            state_data: Raw state data bytes

        Returns:
            Compressed data bytes
        """
        if len(state_data) > self.compression_threshold:
            return gzip.compress(state_data)
        return state_data

    def decompress_state(self, compressed_data: bytes) -> bytes:
        """
        Decompress state data from client.

        Args:
            compressed_data: Compressed data bytes

        Returns:
            Decompressed data bytes
        """
        try:
            return gzip.decompress(compressed_data)
        except gzip.BadGzipFile:
            # Data wasn't compressed
            return compressed_data


# Global state manager instance
_context_state_manager = None


def get_context_state_manager() -> ContextStateManager:
    """Get the global context state manager instance."""
    global _context_state_manager
    if _context_state_manager is None:
        _context_state_manager = ContextStateManager()
    return _context_state_manager
