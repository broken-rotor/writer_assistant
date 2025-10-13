"""
Archive Service for Writer Assistant.

Provides semantic search functionality over archived stories using ChromaDB.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings

logger = logging.getLogger(__name__)


class ArchiveSearchResult:
    """Represents a single search result from the archive."""

    def __init__(
        self,
        file_path: str,
        file_name: str,
        chunk_text: str,
        chunk_index: int,
        similarity_score: float,
        char_start: int,
        char_end: int
    ):
        self.file_path = file_path
        self.file_name = file_name
        self.chunk_text = chunk_text
        self.chunk_index = chunk_index
        self.similarity_score = similarity_score
        self.char_start = char_start
        self.char_end = char_end

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            'file_path': self.file_path,
            'file_name': self.file_name,
            'matching_section': self.chunk_text,
            'chunk_index': self.chunk_index,
            'similarity_score': self.similarity_score,
            'char_start': self.char_start,
            'char_end': self.char_end
        }


class ArchiveService:
    """Service for searching and retrieving archived stories."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        """
        Initialize the archive service.

        Args:
            db_path: Path to ChromaDB storage directory (defaults to settings.ARCHIVE_DB_PATH)
            collection_name: Name of the collection to query (defaults to settings.ARCHIVE_COLLECTION_NAME)
        """
        self.db_path = db_path if db_path is not None else settings.ARCHIVE_DB_PATH
        self.collection_name = collection_name or settings.ARCHIVE_COLLECTION_NAME
        self._client = None
        self._collection = None
        self._enabled = self.db_path is not None

    def is_enabled(self) -> bool:
        """Check if the archive service is enabled."""
        return self._enabled

    def _ensure_initialized(self):
        """Ensure the ChromaDB client and collection are initialized."""
        if not self._enabled:
            raise ValueError(
                "Archive feature is not enabled. Please set ARCHIVE_DB_PATH environment "
                "variable or configure it in your .env file to enable the story archive feature. "
                "See ARCHIVE_SETUP.md for instructions."
            )

        if self._client is None:
            try:
                self._client = chromadb.PersistentClient(
                    path=self.db_path,
                    settings=ChromaSettings(anonymized_telemetry=False)
                )
                logger.info(f"Connected to ChromaDB at {self.db_path}")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB client: {e}")
                raise

        if self._collection is None:
            try:
                self._collection = self._client.get_collection(
                    name=self.collection_name
                )
                logger.info(f"Loaded collection: {self.collection_name}")
            except Exception as e:
                logger.error(f"Failed to load collection '{self.collection_name}': {e}")
                raise

    def search(
        self,
        query: str,
        n_results: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[ArchiveSearchResult]:
        """
        Search the archive for relevant story sections.

        Args:
            query: Search query text
            n_results: Maximum number of results to return
            filter_metadata: Optional metadata filters (e.g., {'file_name': 'story.txt'})

        Returns:
            List of search results ordered by relevance
        """
        self._ensure_initialized()

        try:
            # Perform semantic search
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata,
                include=['documents', 'metadatas', 'distances']
            )

            # Parse results
            search_results = []

            if results and results['ids'] and len(results['ids']) > 0:
                ids = results['ids'][0]
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]

                for i in range(len(ids)):
                    metadata = metadatas[i]
                    # ChromaDB returns distance (lower is better), convert to similarity score
                    similarity = 1 / (1 + distances[i])

                    result = ArchiveSearchResult(
                        file_path=metadata.get('file_path', ''),
                        file_name=metadata.get('file_name', ''),
                        chunk_text=documents[i],
                        chunk_index=metadata.get('chunk_index', 0),
                        similarity_score=round(similarity, 4),
                        char_start=metadata.get('char_start', 0),
                        char_end=metadata.get('char_end', 0)
                    )
                    search_results.append(result)

            logger.info(f"Search returned {len(search_results)} results for query: '{query}'")
            return search_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def get_file_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of all unique files in the archive.

        Returns:
            List of file information dictionaries
        """
        self._ensure_initialized()

        try:
            # Get all documents from the collection
            results = self._collection.get(
                include=['metadatas']
            )

            # Extract unique files
            files_dict = {}

            if results and results['metadatas']:
                for metadata in results['metadatas']:
                    file_path = metadata.get('file_path', '')
                    file_name = metadata.get('file_name', '')

                    if file_path and file_path not in files_dict:
                        files_dict[file_path] = {
                            'file_path': file_path,
                            'file_name': file_name
                        }

            file_list = sorted(files_dict.values(), key=lambda x: x['file_name'])
            logger.info(f"Retrieved {len(file_list)} unique files from archive")
            return file_list

        except Exception as e:
            logger.error(f"Failed to get file list: {e}")
            raise

    def get_file_content(self, file_path: str) -> Optional[str]:
        """
        Retrieve the full content of a file from the archive.

        Args:
            file_path: Path to the file

        Returns:
            Reconstructed file content or None if not found
        """
        self._ensure_initialized()

        try:
            # Query all chunks for this file
            results = self._collection.get(
                where={'file_path': file_path},
                include=['documents', 'metadatas']
            )

            if not results or not results['documents']:
                logger.warning(f"No content found for file: {file_path}")
                return None

            # Sort chunks by chunk_index
            chunks = []
            for i in range(len(results['documents'])):
                metadata = results['metadatas'][i]
                chunks.append({
                    'index': metadata.get('chunk_index', 0),
                    'text': results['documents'][i]
                })

            chunks.sort(key=lambda x: x['index'])

            # Reconstruct content
            # Note: This is an approximation since overlapping chunks may cause duplication
            content = ' '.join([chunk['text'] for chunk in chunks])

            logger.info(f"Retrieved content for {file_path} ({len(chunks)} chunks)")
            return content

        except Exception as e:
            logger.error(f"Failed to get file content: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the archive.

        Returns:
            Dictionary with archive statistics
        """
        self._ensure_initialized()

        try:
            total_chunks = self._collection.count()
            files = self.get_file_list()

            return {
                'total_chunks': total_chunks,
                'total_files': len(files),
                'collection_name': self.collection_name,
                'db_path': self.db_path
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            raise


# Global archive service instance
_archive_service: Optional[ArchiveService] = None


def get_archive_service(
    db_path: Optional[str] = None,
    collection_name: Optional[str] = None
) -> ArchiveService:
    """
    Get or create the global archive service instance.

    Args:
        db_path: Path to ChromaDB storage directory (defaults to settings.ARCHIVE_DB_PATH)
        collection_name: Name of the collection to query (defaults to settings.ARCHIVE_COLLECTION_NAME)

    Returns:
        ArchiveService instance
    """
    global _archive_service

    if _archive_service is None:
        _archive_service = ArchiveService(db_path=db_path, collection_name=collection_name)

    return _archive_service
