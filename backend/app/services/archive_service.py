"""
Archive Service for Writer Assistant.

Provides semantic search functionality over archived stories using ChromaDB.
"""

import logging
import os.path
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

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
        self._enabled = self.db_path is not None and os.path.exists(self.db_path)
        self._embedding_function = None

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
                logger.exception("Failed to initialize ChromaDB client")
                raise

        if self._embedding_function is None:
            try:
                # Initialize embedding function to match ingestion model
                logger.info("Initializing embedding model: all-mpnet-base-v2")
                self._embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-mpnet-base-v2"
                )
            except Exception as e:
                logger.exception("Failed to initialize embedding function")
                raise

        if self._collection is None:
            try:
                self._collection = self._client.get_collection(
                    name=self.collection_name,
                    embedding_function=self._embedding_function
                )
                logger.info(f"Loaded collection: {self.collection_name}")
                logger.info(f"Using embedding model: all-mpnet-base-v2 (768 dimensions)")
            except Exception as e:
                logger.exception(f"Failed to load collection '{self.collection_name}'")
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
            logger.exception("Search failed")
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
            logger.debug(f"Files: {[f['file_name'] for f in file_list]}")
            return file_list

        except Exception as e:
            logger.exception("Failed to get file list")
            raise

    def find_file_by_name(self, file_name: str) -> Optional[str]:
        """
        Find a file path by matching file name (exact or partial).

        Args:
            file_name: File name or pattern to search for

        Returns:
            Full file path if found, None otherwise
        """
        self._ensure_initialized()

        try:
            files = self.get_file_list()

            # Try exact match first
            for file_info in files:
                if file_info['file_name'] == file_name:
                    return file_info['file_path']

            # Try partial match (case-insensitive)
            file_name_lower = file_name.lower()
            for file_info in files:
                if file_name_lower in file_info['file_name'].lower():
                    logger.debug(f"Partial match: '{file_name}' -> '{file_info['file_name']}'")
                    logger.info("Found file by partial name match")
                    return file_info['file_path']

            logger.debug(f"No file found matching: {file_name}")
            logger.warning("No file found matching requested name")
            return None

        except Exception as e:
            logger.exception("Failed to find file by name")
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
                logger.debug(f"No content found for file: {file_path}")
                logger.warning("No content found for requested file")
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

            logger.debug(f"Retrieved content for {file_path} ({len(chunks)} chunks)")
            logger.info(f"Retrieved file content ({len(chunks)} chunks)")
            return content

        except Exception as e:
            logger.exception("Failed to get file content")
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
            logger.exception("Failed to get stats")
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
