"""
Archive API endpoints for Writer Assistant.

Provides endpoints for searching and retrieving archived stories.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from app.services.archive_service import get_archive_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class SearchRequest(BaseModel):
    """Request model for archive search."""
    query: str = Field(..., description="Search query text", min_length=1)
    max_results: int = Field(10, description="Maximum number of results to return", ge=1, le=50)
    filter_file_name: Optional[str] = Field(None, description="Optional file name filter")


class SearchResult(BaseModel):
    """Model for a single search result."""
    file_path: str = Field(..., description="Path to the story file")
    file_name: str = Field(..., description="Name of the story file")
    matching_section: str = Field(..., description="Relevant section of text")
    chunk_index: int = Field(..., description="Index of the chunk within the file")
    similarity_score: float = Field(..., description="Similarity score (higher is better)")
    char_start: int = Field(..., description="Character start position in original file")
    char_end: int = Field(..., description="Character end position in original file")


class SearchResponse(BaseModel):
    """Response model for archive search."""
    query: str = Field(..., description="The search query that was executed")
    results: List[SearchResult] = Field(..., description="List of search results")
    total_results: int = Field(..., description="Total number of results returned")


class FileInfo(BaseModel):
    """Model for file information."""
    file_path: str = Field(..., description="Path to the story file")
    file_name: str = Field(..., description="Name of the story file")


class FileListResponse(BaseModel):
    """Response model for file list."""
    files: List[FileInfo] = Field(..., description="List of files in the archive")
    total_files: int = Field(..., description="Total number of files")


class ArchiveStats(BaseModel):
    """Model for archive statistics."""
    total_chunks: int = Field(..., description="Total number of text chunks in the archive")
    total_files: int = Field(..., description="Total number of unique files in the archive")
    collection_name: str = Field(..., description="Name of the ChromaDB collection")
    db_path: str = Field(..., description="Path to the ChromaDB database")


@router.post("/search", response_model=SearchResponse)
async def search_archive(request: SearchRequest):
    """
    Search the story archive using semantic search.

    Returns relevant story sections that match the query semantically.
    """
    try:
        archive_service = get_archive_service()

        # Check if archive is enabled
        if not archive_service.is_enabled():
            raise HTTPException(
                status_code=503,
                detail="Archive feature is not enabled. Please configure ARCHIVE_DB_PATH to enable this feature. See ARCHIVE_SETUP.md for instructions."
            )

        # Build filter if file name is provided
        filter_metadata = None
        if request.filter_file_name:
            filter_metadata = {'file_name': request.filter_file_name}

        # Perform search
        results = archive_service.search(
            query=request.query,
            n_results=request.max_results,
            filter_metadata=filter_metadata
        )

        # Convert to response model
        search_results = [
            SearchResult(
                file_path=result.file_path,
                file_name=result.file_name,
                matching_section=result.chunk_text,
                chunk_index=result.chunk_index,
                similarity_score=result.similarity_score,
                char_start=result.char_start,
                char_end=result.char_end
            )
            for result in results
        ]

        return SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results)
        )

    except HTTPException:
        raise
    except ValueError as e:
        # Handle disabled archive
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Archive search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/files", response_model=FileListResponse)
async def list_files():
    """
    Get a list of all files in the archive.

    Returns a list of unique files that have been indexed.
    """
    try:
        archive_service = get_archive_service()

        # Check if archive is enabled
        if not archive_service.is_enabled():
            raise HTTPException(
                status_code=503,
                detail="Archive feature is not enabled. Please configure ARCHIVE_DB_PATH to enable this feature. See ARCHIVE_SETUP.md for instructions."
            )

        files = archive_service.get_file_list()

        file_infos = [
            FileInfo(
                file_path=file['file_path'],
                file_name=file['file_name']
            )
            for file in files
        ]

        return FileListResponse(
            files=file_infos,
            total_files=len(file_infos)
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.get("/files/content")
async def get_file_content(
    file_path: str = Query(..., description="Path to the file to retrieve")
):
    """
    Retrieve the full content of a specific file from the archive.

    Returns the reconstructed file content from indexed chunks.
    """
    try:
        archive_service = get_archive_service()

        # Check if archive is enabled
        if not archive_service.is_enabled():
            raise HTTPException(
                status_code=503,
                detail="Archive feature is not enabled. Please configure ARCHIVE_DB_PATH to enable this feature. See ARCHIVE_SETUP.md for instructions."
            )

        content = archive_service.get_file_content(file_path)

        if content is None:
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        return {
            "file_path": file_path,
            "content": content
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get file content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve file: {str(e)}")


@router.get("/stats", response_model=ArchiveStats)
async def get_archive_stats():
    """
    Get statistics about the story archive.

    Returns information about the number of files and chunks indexed.
    """
    try:
        archive_service = get_archive_service()

        # Check if archive is enabled
        if not archive_service.is_enabled():
            raise HTTPException(
                status_code=503,
                detail="Archive feature is not enabled. Please configure ARCHIVE_DB_PATH to enable this feature. See ARCHIVE_SETUP.md for instructions."
            )

        stats = archive_service.get_stats()

        return ArchiveStats(
            total_chunks=stats['total_chunks'],
            total_files=stats['total_files'],
            collection_name=stats['collection_name'],
            db_path=stats['db_path']
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get archive stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
