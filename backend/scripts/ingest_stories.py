"""
Story Archive Ingestion Script for Writer Assistant.

This script recursively reads story files from specified directories,
chunks them appropriately, and stores them in a ChromaDB vector database
for semantic search and retrieval.

Supports: .html, .txt, .md files
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import hashlib

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.config import Settings as ChromaSettings
from bs4 import BeautifulSoup
import markdown

# Try to import app settings, fallback to defaults if not available
try:
    from app.core.config import settings as app_settings
    DEFAULT_DB_PATH = app_settings.ARCHIVE_DB_PATH
    DEFAULT_COLLECTION = app_settings.ARCHIVE_COLLECTION_NAME
except ImportError:
    DEFAULT_DB_PATH = "./chroma_db"
    DEFAULT_COLLECTION = "story_archive"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StoryDocumentProcessor:
    """Processes story documents for vector database ingestion."""

    SUPPORTED_EXTENSIONS = {'.html', '.txt', '.md'}
    CHUNK_SIZE = 1000  # Characters per chunk
    CHUNK_OVERLAP = 200  # Overlap between chunks

    def __init__(self):
        """Initialize the document processor."""
        pass

    def read_file(self, file_path: Path) -> str:
        """
        Read and extract text content from a file.

        Args:
            file_path: Path to the file

        Returns:
            Extracted text content
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            ext = file_path.suffix.lower()

            if ext == '.html':
                return self._extract_html_text(content)
            elif ext == '.md':
                return self._extract_markdown_text(content)
            elif ext == '.txt':
                return content
            else:
                logger.warning(f"Unsupported file type: {ext}")
                return ""

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return ""

    def _extract_html_text(self, html_content: str) -> str:
        """Extract plain text from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text(separator=' ', strip=True)

    def _extract_markdown_text(self, md_content: str) -> str:
        """Extract plain text from Markdown content."""
        # Convert markdown to HTML first, then extract text
        html = markdown.markdown(md_content)
        return self._extract_html_text(html)

    def chunk_text(self, text: str, file_path: Path) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks for better retrieval.

        Args:
            text: Text content to chunk
            file_path: Source file path

        Returns:
            List of chunk dictionaries with content and metadata
        """
        if not text or len(text.strip()) == 0:
            return []

        chunks = []
        text = text.strip()
        start = 0
        chunk_index = 0

        while start < len(text):
            # Calculate chunk end
            end = start + self.CHUNK_SIZE

            # If this is not the last chunk, try to break at a sentence or paragraph
            if end < len(text):
                # Look for paragraph break first
                paragraph_break = text.rfind('\n\n', start, end)
                if paragraph_break > start:
                    end = paragraph_break
                else:
                    # Look for sentence break
                    for punct in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
                        sentence_break = text.rfind(punct, start, end)
                        if sentence_break > start:
                            end = sentence_break + len(punct)
                            break

            chunk_text = text[start:end].strip()

            if chunk_text:
                # Generate a unique ID for this chunk
                chunk_id = self._generate_chunk_id(file_path, chunk_index)

                chunks.append({
                    'id': chunk_id,
                    'text': chunk_text,
                    'metadata': {
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'chunk_index': chunk_index,
                        'char_start': start,
                        'char_end': end,
                    }
                })
                chunk_index += 1

            # Move start position with overlap
            start = end - self.CHUNK_OVERLAP if end < len(text) else end

            # Avoid infinite loop
            if start <= end - self.CHUNK_OVERLAP:
                start = end

        return chunks

    def _generate_chunk_id(self, file_path: Path, chunk_index: int) -> str:
        """Generate a unique ID for a document chunk."""
        path_str = str(file_path)
        hash_input = f"{path_str}_{chunk_index}"
        return hashlib.md5(hash_input.encode()).hexdigest()


class StoryArchiveIngester:
    """Manages the ingestion of stories into ChromaDB."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH, collection_name: str = DEFAULT_COLLECTION):
        """
        Initialize the archive ingester.

        Args:
            db_path: Path to ChromaDB storage directory
            collection_name: Name of the collection to use
        """
        self.db_path = db_path
        self.collection_name = collection_name
        self.processor = StoryDocumentProcessor()

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Story archive for semantic search"}
        )

        logger.info(f"Initialized ChromaDB at {db_path}")
        logger.info(f"Using collection: {collection_name}")

    def find_story_files(self, directories: List[str], recursive: bool = True) -> List[Path]:
        """
        Find all story files in the given directories.

        Args:
            directories: List of directory paths to search
            recursive: Whether to search recursively

        Returns:
            List of file paths
        """
        files = []

        for directory in directories:
            dir_path = Path(directory)

            if not dir_path.exists():
                logger.warning(f"Directory does not exist: {directory}")
                continue

            if not dir_path.is_dir():
                logger.warning(f"Not a directory: {directory}")
                continue

            # Find files with supported extensions
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"

            for ext in self.processor.SUPPORTED_EXTENSIONS:
                found = list(dir_path.glob(f"{pattern}{ext}"))
                files.extend(found)
                logger.info(f"Found {len(found)} {ext} files in {directory}")

        return sorted(set(files))

    def ingest_files(self, files: List[Path], batch_size: int = 100):
        """
        Ingest a list of files into the vector database.

        Args:
            files: List of file paths to ingest
            batch_size: Number of chunks to add in each batch
        """
        total_files = len(files)
        total_chunks = 0
        failed_files = []

        batch_ids = []
        batch_texts = []
        batch_metadatas = []

        for idx, file_path in enumerate(files, 1):
            logger.info(f"Processing file {idx}/{total_files}: {file_path.name}")

            try:
                # Read and process file
                content = self.processor.read_file(file_path)

                if not content:
                    logger.warning(f"No content extracted from {file_path}")
                    continue

                # Chunk the content
                chunks = self.processor.chunk_text(content, file_path)

                if not chunks:
                    logger.warning(f"No chunks generated from {file_path}")
                    continue

                logger.info(f"Generated {len(chunks)} chunks from {file_path.name}")

                # Add chunks to batch
                for chunk in chunks:
                    batch_ids.append(chunk['id'])
                    batch_texts.append(chunk['text'])
                    batch_metadatas.append(chunk['metadata'])
                    total_chunks += 1

                    # If batch is full, add to collection
                    if len(batch_ids) >= batch_size:
                        self._add_batch(batch_ids, batch_texts, batch_metadatas)
                        batch_ids = []
                        batch_texts = []
                        batch_metadatas = []

            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                failed_files.append(str(file_path))

        # Add remaining items in batch
        if batch_ids:
            self._add_batch(batch_ids, batch_texts, batch_metadatas)

        # Summary
        logger.info("=" * 60)
        logger.info(f"Ingestion complete!")
        logger.info(f"Total files processed: {total_files}")
        logger.info(f"Total chunks created: {total_chunks}")
        logger.info(f"Failed files: {len(failed_files)}")

        if failed_files:
            logger.info("Failed files:")
            for failed in failed_files:
                logger.info(f"  - {failed}")

    def _add_batch(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]):
        """Add a batch of documents to the collection."""
        try:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Added batch of {len(ids)} chunks to collection")
        except Exception as e:
            logger.error(f"Failed to add batch to collection: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        count = self.collection.count()
        return {
            'total_chunks': count,
            'collection_name': self.collection_name,
            'db_path': self.db_path
        }

    def reset_collection(self):
        """Reset (delete and recreate) the collection."""
        logger.warning(f"Resetting collection: {self.collection_name}")
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Story archive for semantic search"}
            )
            logger.info("Collection reset successfully")
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Ingest story files into ChromaDB vector database for semantic search"
    )
    parser.add_argument(
        'directories',
        nargs='+',
        help='Directories containing story files to ingest'
    )
    parser.add_argument(
        '--db-path',
        default=DEFAULT_DB_PATH,
        help=f'Path to ChromaDB storage directory (default: {DEFAULT_DB_PATH})'
    )
    parser.add_argument(
        '--collection',
        default=DEFAULT_COLLECTION,
        help=f'Collection name to use (default: {DEFAULT_COLLECTION})'
    )
    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='Do not search directories recursively'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset the collection before ingestion (deletes existing data)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of chunks to add in each batch (default: 100)'
    )

    args = parser.parse_args()

    # Initialize ingester
    ingester = StoryArchiveIngester(
        db_path=args.db_path,
        collection_name=args.collection
    )

    # Reset if requested
    if args.reset:
        response = input("Are you sure you want to reset the collection? This will delete all existing data. (yes/no): ")
        if response.lower() == 'yes':
            ingester.reset_collection()
        else:
            logger.info("Reset cancelled")
            return

    # Find files
    logger.info("Searching for story files...")
    files = ingester.find_story_files(
        args.directories,
        recursive=not args.no_recursive
    )

    if not files:
        logger.error("No story files found!")
        return

    logger.info(f"Found {len(files)} story files to process")

    # Ingest files
    ingester.ingest_files(files, batch_size=args.batch_size)

    # Print stats
    stats = ingester.get_stats()
    logger.info("=" * 60)
    logger.info("Database Statistics:")
    logger.info(f"  Collection: {stats['collection_name']}")
    logger.info(f"  Total chunks: {stats['total_chunks']}")
    logger.info(f"  Database path: {stats['db_path']}")


if __name__ == '__main__':
    main()
