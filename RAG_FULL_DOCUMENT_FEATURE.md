# RAG Full Document Retrieval Feature

## Overview

Enhanced the RAG chat functionality to conditionally retrieve full documents based on query analysis. The system now intelligently decides whether to use chunk-based or full-document retrieval.

## Implementation

### 1. Query Analyzer (`backend/app/services/query_analyzer.py`)

New module that analyzes user queries to determine retrieval strategy.

**Features:**
- **Keyword Detection**: Identifies words indicating need for detailed context
  - Detail indicators: "explain", "elaborate", "summarize", "detailed", "full", etc.
  - Temporal indicators: "throughout", "over time", "progression", "evolution"
  - Scope indicators: "all", "every", "whole", "comprehensive"
  - Analytical indicators: "relationship", "arc", "theme", "analysis"

- **Source Tag Parsing**: Extracts `source:<filename>` tags from queries
  - Example: "What happens in Chapter 3? source:story.txt"
  - Supports multiple sources: "Compare source:chapter1.txt source:chapter2.txt"

- **Follow-up Detection**: Recognizes follow-up questions
  - Keywords: "more", "also", "what else", "continue", "expand"
  - Conversation depth tracking
  - Topic continuity detection

### 2. Archive Service Enhancement (`backend/app/services/archive_service.py`)

**New Method:**
- `find_file_by_name(file_name: str)`: Finds file path by name with fuzzy matching
  - Tries exact match first
  - Falls back to partial case-insensitive match
  - Returns full file path from metadata

### 3. RAG Service Updates (`backend/app/services/rag_service.py`)

**Enhanced `chat()` method with three retrieval modes:**

1. **User-Specified Sources** (Priority 1)
   - When `source:<filename>` tags are detected
   - Retrieves full content of specified files
   - Removes source tags from query before processing

2. **Keyword-Triggered Full Documents** (Priority 2)
   - When detail/scope keywords are detected
   - First retrieves relevant chunks via semantic search
   - Then fetches full documents for top 3 matching files
   - Provides both precision (chunks) and context (full docs)

3. **Standard Chunk Retrieval** (Default)
   - When no indicators for full document retrieval
   - Uses existing chunk-based semantic search
   - Optimal for specific, targeted queries

**New Method:**
- `_build_enhanced_context()`: Builds context from chunks and/or full documents
  - Truncates very long documents (8000 chars per doc)
  - Keeps beginning and end, truncates middle
  - Clearly labels full documents vs excerpts

## Usage Examples

### Example 1: Explicit Source Specification
```
User: "Tell me about the protagonist's journey source:chapter1.txt"
System: Retrieves full content of chapter1.txt
```

### Example 2: Keyword-Triggered Retrieval
```
User: "Explain the character development throughout the story"
System: Detects "explain", "throughout" → retrieves full documents
```

### Example 3: Follow-up Questions
```
User: "Who is the main character?"
Assistant: [answers]
User: "Tell me more about them"
System: Detects follow-up → escalates to full document retrieval
```

### Example 4: Standard Retrieval
```
User: "What color is the house?"
System: No indicators → uses chunk-based retrieval
```

## Query Analysis Logic

```
if source:<filename> tags present:
    → Retrieve specified full documents

elif detail keywords OR follow-up after context:
    → Retrieve relevant chunks THEN full documents

else:
    → Standard chunk-based retrieval
```

## Configuration

### Tunable Parameters

**In `query_analyzer.py`:**
- `DETAIL_KEYWORDS`: List of keywords triggering full document retrieval
- `FOLLOWUP_KEYWORDS`: List of keywords indicating follow-up questions

**In `rag_service.py` (`chat()` method):**
- `n_context_chunks`: Number of chunks to retrieve (default: 5)
- Top 3 results get full document retrieval (line 241)
- `max_doc_length`: 8000 characters per document (line 331)

## Benefits

1. **Context-Aware**: Automatically provides appropriate level of detail
2. **User Control**: Explicit source specification via tags
3. **Efficient**: Only retrieves full documents when needed
4. **Smart Follow-ups**: Recognizes when user needs deeper context
5. **Conversation Continuity**: Tracks conversation depth and topics
6. **Scalable**: Handles large documents with intelligent truncation

## API Compatibility

The changes are **backward compatible**. Existing RAG chat calls work exactly as before:
- No API signature changes
- Existing chunk-based behavior preserved for simple queries
- Enhanced behavior triggers automatically based on query analysis

## Files Modified

1. `backend/app/services/query_analyzer.py` (NEW)
2. `backend/app/services/archive_service.py` (MODIFIED - added `find_file_by_name()`)
3. `backend/app/services/rag_service.py` (MODIFIED - enhanced `chat()` method)

## Testing Recommendations

1. Test `source:<filename>` tag parsing with various file names
2. Test keyword detection with different query patterns
3. Test follow-up question detection in multi-turn conversations
4. Test document truncation with very large files
5. Test fallback behavior when source files are not found
6. Test backward compatibility with existing chunk-based queries
