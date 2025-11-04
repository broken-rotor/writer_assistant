"""
Archive API endpoints for Writer Assistant.

Provides endpoints for searching and retrieving archived stories,
plus RAG-based question answering.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.services.archive_service import get_archive_service
from app.services.rag_service import get_rag_service, ChatMessage
from app.models.streaming_models import (
    StreamingStatusEvent,
    StreamingResultEvent,
    StreamingErrorEvent,
    StreamingPhase,
    STREAMING_PHASES
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class SearchRequest(BaseModel):
    """Request model for archive search."""
    query: str = Field(..., description="Search query text", min_length=1)
    max_results: int = Field(
        10,
        description="Maximum number of results to return",
        ge=1,
        le=50)
    filter_file_name: Optional[str] = Field(
        None, description="Optional file name filter")


class SearchResult(BaseModel):
    """Model for a single search result."""
    file_path: str = Field(..., description="Path to the story file")
    file_name: str = Field(..., description="Name of the story file")
    matching_section: str = Field(..., description="Relevant section of text")
    chunk_index: int = Field(...,
                             description="Index of the chunk within the file")
    similarity_score: float = Field(...,
                                    description="Similarity score (higher is better)")
    char_start: int = Field(...,
                            description="Character start position in original file")
    char_end: int = Field(...,
                          description="Character end position in original file")


class SearchResponse(BaseModel):
    """Response model for archive search."""
    query: str = Field(..., description="The search query that was executed")
    results: List[SearchResult] = Field(...,
                                        description="List of search results")
    total_results: int = Field(...,
                               description="Total number of results returned")


class FileInfo(BaseModel):
    """Model for file information."""
    file_path: str = Field(..., description="Path to the story file")
    file_name: str = Field(..., description="Name of the story file")


class FileListResponse(BaseModel):
    """Response model for file list."""
    files: List[FileInfo] = Field(...,
                                  description="List of files in the archive")
    total_files: int = Field(..., description="Total number of files")


class ArchiveStats(BaseModel):
    """Model for archive statistics."""
    total_chunks: int = Field(...,
                              description="Total number of text chunks in the archive")
    total_files: int = Field(...,
                             description="Total number of unique files in the archive")
    collection_name: str = Field(...,
                                 description="Name of the ChromaDB collection")
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
                detail="Archive feature is not enabled. Please configure ARCHIVE_DB_PATH to enable this feature. "
                "See ARCHIVE_SETUP.md for instructions.")

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
                detail="Archive feature is not enabled. Please configure ARCHIVE_DB_PATH to enable this feature. "
                "See ARCHIVE_SETUP.md for instructions.")

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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list files: {
                str(e)}")


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
                detail="Archive feature is not enabled. Please configure ARCHIVE_DB_PATH to enable this feature. "
                "See ARCHIVE_SETUP.md for instructions.")

        content = archive_service.get_file_content(file_path)

        if content is None:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_path}")

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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve file: {str(e)}")


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
                detail="Archive feature is not enabled. Please configure ARCHIVE_DB_PATH to enable this feature. "
                "See ARCHIVE_SETUP.md for instructions.")

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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}")


# ============================================================================
# RAG (Retrieval-Augmented Generation) Endpoints
# ============================================================================

class RAGQueryRequest(BaseModel):
    """Request model for RAG query."""
    question: str = Field(..., description="Question to answer", min_length=1)
    n_context_chunks: int = Field(
        5, description="Number of context chunks to retrieve", ge=1, le=20)
    max_tokens: Optional[int] = Field(
        1024, description="Maximum tokens for answer", ge=50, le=4096)
    temperature: Optional[float] = Field(
        None,
        description="Sampling temperature (uses ENDPOINT_ARCHIVE_SEARCH_TEMPERATURE if not specified)",
        ge=0.0,
        le=1.0)
    filter_file_name: Optional[str] = Field(
        None, description="Optional file name filter")


class RAGChatMessageModel(BaseModel):
    """Model for a chat message."""
    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content", min_length=1)


class RAGChatRequest(BaseModel):
    """Request model for RAG chat."""
    messages: List[RAGChatMessageModel] = Field(
        ..., description="Chat history including current question")
    n_context_chunks: int = Field(
        5, description="Number of context chunks to retrieve", ge=1, le=20)
    max_tokens: Optional[int] = Field(
        1024, description="Maximum tokens for answer", ge=50, le=4096)
    temperature: Optional[float] = Field(
        None,
        description="Sampling temperature (uses ENDPOINT_ARCHIVE_SUMMARIZE_TEMPERATURE if not specified)",
        ge=0.0,
        le=1.0)
    filter_file_name: Optional[str] = Field(
        None, description="Optional file name filter")


class RAGSource(BaseModel):
    """Model for a RAG source/context chunk."""
    file_path: str = Field(..., description="Path to source file")
    file_name: str = Field(..., description="Name of source file")
    matching_section: str = Field(..., description="Relevant text section")
    similarity_score: float = Field(..., description="Similarity score")


class RAGResponse(BaseModel):
    """Response model for RAG queries."""
    query: str = Field(..., description="The question that was asked")
    answer: str = Field(..., description="Generated answer")
    sources: List[RAGSource] = Field(...,
                                     description="Source chunks used for context")
    total_sources: int = Field(..., description="Total number of sources used")
    info_message: Optional[str] = Field(
        None,
        description="Informational message about retrieval status (not included in future prompts)")


class RAGStatusResponse(BaseModel):
    """Response model for RAG status check."""
    archive_enabled: bool = Field(...,
                                  description="Whether archive is enabled")
    llm_enabled: bool = Field(..., description="Whether LLM is configured")
    llm_loading: bool = Field(...,
                              description="Whether LLM is currently loading")
    rag_enabled: bool = Field(..., description="Whether RAG is fully enabled")
    message: str = Field(..., description="Status message")


@router.get("/rag/status", response_model=RAGStatusResponse)
async def get_rag_status():
    """
    Check if RAG (Retrieval-Augmented Generation) feature is enabled.

    Returns status of both archive and LLM components.
    """
    try:
        # Import here to access global state
        from app.main import llm_loading

        archive_service = get_archive_service()
        rag_service = get_rag_service()

        archive_enabled = archive_service.is_enabled()
        llm_enabled = rag_service.llm is not None
        rag_enabled = rag_service.is_enabled()

        if llm_loading:
            message = "LLM is currently loading. Please wait a moment and try again."
        elif rag_enabled:
            message = "RAG feature is fully enabled and ready to use."
        elif not archive_enabled:
            message = "Archive is not enabled. Please configure ARCHIVE_DB_PATH."
        elif not llm_enabled:
            message = "LLM is not configured. Please set MODEL_PATH in your environment."
        else:
            message = "RAG feature is not available."

        return RAGStatusResponse(
            archive_enabled=archive_enabled,
            llm_enabled=llm_enabled,
            llm_loading=llm_loading,
            rag_enabled=rag_enabled,
            message=message
        )

    except Exception as e:
        logger.error(f"Failed to check RAG status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check RAG status: {
                str(e)}")


@router.post("/rag/query", response_model=RAGResponse)
async def rag_query(request: RAGQueryRequest):
    """
    Answer a question using RAG (Retrieval-Augmented Generation).

    Retrieves relevant story sections and uses an LLM to generate an answer
    based on the retrieved context.
    """
    try:
        rag_service = get_rag_service()

        # Check if RAG is enabled
        if not rag_service.is_enabled():
            archive_enabled = rag_service.archive_service.is_enabled()
            llm_enabled = rag_service.llm is not None

            if not archive_enabled:
                detail = "Archive feature is not enabled. Please configure ARCHIVE_DB_PATH."
            elif not llm_enabled:
                detail = "LLM is not configured. Please set MODEL_PATH in your environment."
            else:
                detail = "RAG feature is not available."

            raise HTTPException(status_code=503, detail=detail)

        # Build filter if provided
        filter_metadata = None
        if request.filter_file_name:
            filter_metadata = {'file_name': request.filter_file_name}

        # Perform RAG query
        result = rag_service.query(
            question=request.question,
            n_context_chunks=request.n_context_chunks,
            max_tokens=request.max_tokens,
            temperature=(request.temperature
                         if request.temperature is not None
                         else settings.ENDPOINT_ARCHIVE_SEARCH_TEMPERATURE),
            filter_metadata=filter_metadata)

        # Convert to response model
        sources = [
            RAGSource(
                file_path=source.file_path,
                file_name=source.file_name,
                matching_section=source.chunk_text,
                similarity_score=source.similarity_score
            )
            for source in result.sources
        ]

        return RAGResponse(
            query=result.query,
            answer=result.answer,
            sources=sources,
            total_sources=len(sources),
            info_message=result.info_message
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"RAG query failed: {str(e)}")


@router.post("/rag/query/stream")
async def rag_query_stream(request: RAGQueryRequest):
    """
    Answer a question using RAG with Server-Sent Events streaming for real-time progress updates.

    Retrieves relevant story sections and uses an LLM to generate an answer
    based on the retrieved context, providing progress updates through each phase.
    """

    async def generate_with_updates():
        try:
            # Phase 1: Initializing
            status_event = StreamingStatusEvent(
                phase=StreamingPhase.INITIALIZING,
                message=STREAMING_PHASES[StreamingPhase.INITIALIZING]["message"],
                progress=STREAMING_PHASES[StreamingPhase.INITIALIZING]["progress"]
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            rag_service = get_rag_service()

            # Check if RAG is enabled
            if not rag_service.is_enabled():
                archive_enabled = rag_service.archive_service.is_enabled()
                llm_enabled = rag_service.llm is not None

                if not archive_enabled:
                    detail = "Archive feature is not enabled. Please configure ARCHIVE_DB_PATH."
                elif not llm_enabled:
                    detail = "LLM is not configured. Please set MODEL_PATH in your environment."
                else:
                    detail = "RAG feature is not available."

                error_event = StreamingErrorEvent(message=detail)
                yield f"data: {error_event.model_dump_json()}\n\n"
                return

            # Phase 2: Retrieving
            status_event = StreamingStatusEvent(
                phase=StreamingPhase.RETRIEVING,
                message=STREAMING_PHASES[StreamingPhase.RETRIEVING]["message"],
                progress=STREAMING_PHASES[StreamingPhase.RETRIEVING]["progress"]
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            # Build filter if provided
            filter_metadata = None
            if request.filter_file_name:
                filter_metadata = {'file_name': request.filter_file_name}

            # Retrieve relevant context from archive
            search_results = rag_service.archive_service.search(
                query=request.question,
                n_results=request.n_context_chunks,
                filter_metadata=filter_metadata
            )

            if not search_results:
                # No results found - return early with appropriate message
                result = RAGResponse(
                    query=request.question,
                    answer="I couldn't find any relevant information in the archive to answer your question.",
                    sources=[],
                    total_sources=0,
                    info_message="No relevant content was found in the archive.")

                result_event = StreamingResultEvent(
                    data=result.model_dump(),
                    status="complete"
                )
                yield f"data: {result_event.model_dump_json()}\n\n"
                return

            # Phase 3: Generating
            status_event = StreamingStatusEvent(
                phase=StreamingPhase.GENERATING,
                message=STREAMING_PHASES[StreamingPhase.GENERATING]["message"],
                progress=STREAMING_PHASES[StreamingPhase.GENERATING]["progress"]
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            # Build context from search results
            context = rag_service.build_context(search_results)

            # Create prompt for LLM
            prompt = rag_service.build_rag_prompt(request.question, context)

            # Generate answer using LLM
            answer = rag_service.llm.generate(
                prompt=prompt,
                max_tokens=request.max_tokens or 1024,
                temperature=(request.temperature
                             if request.temperature is not None
                             else settings.ENDPOINT_ARCHIVE_SEARCH_TEMPERATURE),
                stop=[
                    "Question:",
                    "Context:"])

            # Phase 4: Formatting
            status_event = StreamingStatusEvent(
                phase=StreamingPhase.FORMATTING,
                message=STREAMING_PHASES[StreamingPhase.FORMATTING]["message"],
                progress=STREAMING_PHASES[StreamingPhase.FORMATTING]["progress"]
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            # Convert to response model
            sources = [
                RAGSource(
                    file_path=source.file_path,
                    file_name=source.file_name,
                    matching_section=source.chunk_text,
                    similarity_score=source.similarity_score
                )
                for source in search_results
            ]

            response = RAGResponse(
                query=request.question,
                answer=answer,
                sources=sources,
                total_sources=len(sources),
                info_message=None
            )

            # Final result
            result_event = StreamingResultEvent(
                data=response.model_dump(),
                status="complete"
            )
            yield f"data: {result_event.model_dump_json()}\n\n"

        except HTTPException as e:
            error_event = StreamingErrorEvent(message=e.detail)
            yield f"data: {error_event.model_dump_json()}\n\n"
        except ValueError as e:
            error_event = StreamingErrorEvent(message=str(e))
            yield f"data: {error_event.model_dump_json()}\n\n"
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            error_event = StreamingErrorEvent(
                message=f"RAG query failed: {str(e)}")
            yield f"data: {error_event.model_dump_json()}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.post("/rag/chat")
async def rag_chat(request: RAGChatRequest):
    """
    Conduct a multi-turn chat conversation with RAG context using Server-Sent Events streaming.

    Maintains conversation history while retrieving relevant context
    for each user question, providing real-time progress updates.
    """

    async def generate_with_updates():
        try:
            # Phase 1: Initializing
            status_event = StreamingStatusEvent(
                phase=StreamingPhase.INITIALIZING,
                message="Initializing RAG chat session...",
                progress=15
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            rag_service = get_rag_service()

            # Check if RAG is enabled
            if not rag_service.is_enabled():
                archive_enabled = rag_service.archive_service.is_enabled()
                llm_enabled = rag_service.llm is not None

                if not archive_enabled:
                    detail = "Archive feature is not enabled. Please configure ARCHIVE_DB_PATH."
                elif not llm_enabled:
                    detail = "LLM is not configured. Please set MODEL_PATH in your environment."
                else:
                    detail = "RAG feature is not available."

                error_event = StreamingErrorEvent(message=detail)
                yield f"data: {error_event.model_dump_json()}\n\n"
                return

            # Convert Pydantic models to ChatMessage objects
            messages = [
                ChatMessage(role=msg.role, content=msg.content)
                for msg in request.messages
            ]

            # Phase 2: Retrieving
            status_event = StreamingStatusEvent(
                phase=StreamingPhase.RETRIEVING,
                message="Searching for relevant context from conversation...",
                progress=40
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            # Build filter if provided
            filter_metadata = None
            if request.filter_file_name:
                filter_metadata = {'file_name': request.filter_file_name}

            # Phase 3: Generating
            status_event = StreamingStatusEvent(
                phase=StreamingPhase.GENERATING,
                message="Generating contextual response...",
                progress=70
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            # Perform RAG chat
            result = rag_service.chat(
                messages=messages,
                n_context_chunks=request.n_context_chunks,
                max_tokens=request.max_tokens,
                temperature=(request.temperature
                             if request.temperature is not None
                             else settings.ENDPOINT_ARCHIVE_SUMMARIZE_TEMPERATURE),
                filter_metadata=filter_metadata)

            # Phase 4: Formatting
            status_event = StreamingStatusEvent(
                phase=StreamingPhase.FORMATTING,
                message="Formatting chat response and sources...",
                progress=90
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            # Convert to response model
            sources = [
                RAGSource(
                    file_path=source.file_path,
                    file_name=source.file_name,
                    matching_section=source.chunk_text,
                    similarity_score=source.similarity_score
                )
                for source in result.sources
            ]

            response = RAGResponse(
                query=result.query,
                answer=result.answer,
                sources=sources,
                total_sources=len(sources),
                info_message=result.info_message
            )

            # Final result
            result_event = StreamingResultEvent(
                data=response.model_dump(),
                status="complete"
            )
            yield f"data: {result_event.model_dump_json()}\n\n"

        except HTTPException as e:
            error_event = StreamingErrorEvent(message=e.detail)
            yield f"data: {error_event.model_dump_json()}\n\n"
        except ValueError as e:
            error_event = StreamingErrorEvent(message=str(e))
            yield f"data: {error_event.model_dump_json()}\n\n"
        except Exception as e:
            logger.error(f"RAG chat failed: {e}")
            error_event = StreamingErrorEvent(
                message=f"RAG chat failed: {str(e)}")
            yield f"data: {error_event.model_dump_json()}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )
