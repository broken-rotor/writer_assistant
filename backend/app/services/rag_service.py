"""
RAG (Retrieval-Augmented Generation) Service for Story Archive.

Combines semantic search with LLM-powered question answering to enable
natural language queries over archived stories.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.services.archive_service import ArchiveService, ArchiveSearchResult
from app.services.llm_inference import LLMInference, get_llm

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Represents a message in the chat history."""
    role: str  # 'user' or 'assistant'
    content: str


@dataclass
class RAGResponse:
    """Response from RAG query with context and answer."""
    query: str
    answer: str
    sources: List[ArchiveSearchResult]
    context_used: str


class RAGService:
    """
    Service for RAG-based question answering over story archives.

    Combines vector search (retrieval) with LLM generation to answer
    questions about archived stories.
    """

    def __init__(
        self,
        archive_service: ArchiveService,
        llm: Optional[LLMInference] = None
    ):
        """
        Initialize the RAG service.

        Args:
            archive_service: ArchiveService for retrieving relevant content
            llm: LLMInference instance for generating answers (uses global if None)
        """
        self.archive_service = archive_service
        self._llm = llm

    @property
    def llm(self) -> Optional[LLMInference]:
        """Get LLM instance (lazy load from global)."""
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    def is_enabled(self) -> bool:
        """Check if RAG service is fully enabled (archive + LLM)."""
        return self.archive_service.is_enabled() and self.llm is not None

    def query(
        self,
        question: str,
        n_context_chunks: int = 5,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> RAGResponse:
        """
        Answer a question using RAG (Retrieval-Augmented Generation).

        Args:
            question: The question to answer
            n_context_chunks: Number of relevant chunks to retrieve for context
            max_tokens: Maximum tokens for LLM response
            temperature: Sampling temperature for LLM
            filter_metadata: Optional metadata filters for retrieval

        Returns:
            RAGResponse with answer and sources

        Raises:
            ValueError: If archive or LLM is not enabled
            RuntimeError: If query fails
        """
        if not self.archive_service.is_enabled():
            raise ValueError(
                "Archive service is not enabled. Please configure ARCHIVE_DB_PATH."
            )

        if self.llm is None:
            raise ValueError(
                "LLM is not configured. Please set MODEL_PATH in your environment."
            )

        try:
            # Step 1: Retrieve relevant context from archive
            logger.info(f"Retrieving context for question: {question}")
            search_results = self.archive_service.search(
                query=question,
                n_results=n_context_chunks,
                filter_metadata=filter_metadata
            )

            if not search_results:
                return RAGResponse(
                    query=question,
                    answer="I couldn't find any relevant information in the archive to answer your question.",
                    sources=[],
                    context_used=""
                )

            # Step 2: Build context from search results
            context = self._build_context(search_results)

            # Step 3: Create prompt for LLM
            prompt = self._build_rag_prompt(question, context)

            # Step 4: Generate answer using LLM
            logger.info(f"Generating answer with {len(search_results)} context chunks")
            answer = self.llm.generate(
                prompt=prompt,
                max_tokens=max_tokens or 1024,
                temperature=temperature if temperature is not None else 0.3,
                stop=["Question:", "Context:"]
            )

            return RAGResponse(
                query=question,
                answer=answer,
                sources=search_results,
                context_used=context
            )

        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            raise RuntimeError(f"Failed to process RAG query: {str(e)}")

    def chat(
        self,
        messages: List[ChatMessage],
        n_context_chunks: int = 5,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> RAGResponse:
        """
        Conduct a multi-turn chat conversation with RAG context.

        Args:
            messages: List of chat messages (history + current question)
            n_context_chunks: Number of relevant chunks to retrieve
            max_tokens: Maximum tokens for LLM response
            temperature: Sampling temperature for LLM
            filter_metadata: Optional metadata filters for retrieval

        Returns:
            RAGResponse with answer and sources

        Raises:
            ValueError: If archive or LLM is not enabled
            RuntimeError: If chat fails
        """
        if not self.archive_service.is_enabled():
            raise ValueError(
                "Archive service is not enabled. Please configure ARCHIVE_DB_PATH."
            )

        if self.llm is None:
            raise ValueError(
                "LLM is not configured. Please set MODEL_PATH in your environment."
            )

        if not messages:
            raise ValueError("Messages list cannot be empty")

        try:
            # Get the latest user message for retrieval
            user_messages = [m for m in messages if m.role == "user"]
            if not user_messages:
                raise ValueError("No user messages found")

            latest_question = user_messages[-1].content

            # Step 1: Retrieve relevant context
            logger.info(f"Retrieving context for chat question: {latest_question}")
            search_results = self.archive_service.search(
                query=latest_question,
                n_results=n_context_chunks,
                filter_metadata=filter_metadata
            )

            # Step 2: Build context
            context = self._build_context(search_results) if search_results else ""

            # Step 3: Build chat messages with context
            chat_messages = self._build_chat_messages(messages, context)

            # Step 4: Generate response using chat completion
            logger.info(f"Generating chat response with {len(search_results)} context chunks")
            answer = self.llm.chat_completion(
                messages=chat_messages,
                max_tokens=max_tokens or 1024,
                temperature=temperature if temperature is not None else 0.4
            )

            return RAGResponse(
                query=latest_question,
                answer=answer,
                sources=search_results,
                context_used=context
            )

        except Exception as e:
            logger.error(f"RAG chat failed: {e}")
            raise RuntimeError(f"Failed to process RAG chat: {str(e)}")

    def _build_context(self, search_results: List[ArchiveSearchResult]) -> str:
        """
        Build context string from search results.

        Args:
            search_results: List of search results from archive

        Returns:
            Formatted context string
        """
        context_parts = []
        for i, result in enumerate(search_results, 1):
            context_parts.append(
                f"[Source {i}: {result.file_name}]\n{result.chunk_text}\n"
            )

        return "\n".join(context_parts)

    def _build_rag_prompt(self, question: str, context: str) -> str:
        """
        Build a RAG prompt for single-turn question answering.

        Args:
            question: User's question
            context: Retrieved context from archive

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a helpful assistant that answers questions about stories based on provided context. Use the context below to answer the question. If the context doesn't contain enough information to answer the question, say so clearly.

Context:
{context}

Question: {question}

Answer: """
        return prompt

    def _build_chat_messages(
        self,
        messages: List[ChatMessage],
        context: str
    ) -> List[Dict[str, str]]:
        """
        Build chat messages list with context injection.

        Args:
            messages: Chat history
            context: Retrieved context from archive

        Returns:
            List of message dicts for chat completion
        """
        # Build system message with context
        system_message = {
            "role": "system",
            "content": f"""You are a helpful assistant that answers questions about stories. You have access to relevant story excerpts provided as context.

Use the following context to answer questions:

{context}

If the context doesn't contain enough information to fully answer a question, acknowledge this and provide what information you can from the available context."""
        }

        # Convert ChatMessage objects to dicts
        chat_messages = [system_message]
        for msg in messages:
            chat_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        return chat_messages


# Global RAG service instance
_rag_service: Optional[RAGService] = None


def get_rag_service(
    archive_service: Optional[ArchiveService] = None,
    llm: Optional[LLMInference] = None
) -> RAGService:
    """
    Get or create the global RAG service instance.

    Args:
        archive_service: ArchiveService instance (creates new if None)
        llm: LLMInference instance (uses global if None)

    Returns:
        RAGService instance
    """
    global _rag_service

    if _rag_service is None:
        from app.services.archive_service import get_archive_service

        if archive_service is None:
            archive_service = get_archive_service()

        _rag_service = RAGService(
            archive_service=archive_service,
            llm=llm
        )

    return _rag_service
