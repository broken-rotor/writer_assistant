# Archive Feature Setup Guide

This guide explains how to set up and use the Story Archive feature with ChromaDB vector search.

## Overview

The Archive feature allows you to:
- Ingest existing story files (HTML, TXT, MD) into a searchable vector database
- Perform semantic search across all archived stories
- View matching sections and full file content
- Search by topics, themes, characters, or any natural language query

## Prerequisites

1. Python virtual environment with dependencies installed
2. Story files in HTML, TXT, or MD format

**Note:** The Archive feature is **optional** and disabled by default. You must enable it by configuring the database path.

## Setup Instructions

### 1. Enable the Archive Feature

The archive feature must be explicitly enabled. Choose one of these methods:

**Method A: Environment Variable**
```bash
# Linux/Mac
export ARCHIVE_DB_PATH=./chroma_db

# Windows Command Prompt
set ARCHIVE_DB_PATH=./chroma_db

# Windows PowerShell
$env:ARCHIVE_DB_PATH="./chroma_db"
```

**Method B: .env File (Recommended)**
```bash
cd backend
# Copy example file if it doesn't exist
cp .env.example .env

# Edit .env and add or uncomment:
ARCHIVE_DB_PATH=./chroma_db
ARCHIVE_COLLECTION_NAME=story_archive
```

If `ARCHIVE_DB_PATH` is not set, the archive feature will be disabled and the backend will return a helpful error message.

### 2. Install Dependencies

Install the new dependencies required for the archive feature:

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

This will install:
- `chromadb` - Vector database for semantic search
- `beautifulsoup4` - HTML parsing
- `markdown` - Markdown processing

### 3. Prepare Your Story Files

Organize your story files in directories. The ingestion script will scan recursively by default.

Example structure:
```
my_stories/
├── fantasy/
│   ├── story1.html
│   └── story2.txt
├── scifi/
│   ├── story3.md
│   └── story4.html
└── misc/
    └── story5.txt
```

### 4. Ingest Stories into the Database

Run the ingestion script to process your story files:

```bash
cd backend
python scripts/ingest_stories.py /path/to/your/stories /another/path/to/stories
```

#### Script Options

```bash
# Basic usage - ingest all stories from directory
python scripts/ingest_stories.py /path/to/stories

# Multiple directories
python scripts/ingest_stories.py /path/to/stories1 /path/to/stories2

# Custom database location
python scripts/ingest_stories.py /path/to/stories --db-path ./my_custom_db

# Custom collection name
python scripts/ingest_stories.py /path/to/stories --collection my_stories

# Non-recursive (only top-level files)
python scripts/ingest_stories.py /path/to/stories --no-recursive

# Reset database before ingestion (deletes existing data)
python scripts/ingest_stories.py /path/to/stories --reset

# Custom batch size
python scripts/ingest_stories.py /path/to/stories --batch-size 50
```

#### Example Output

```
INFO - Searching for story files...
INFO - Found 15 .html files in /path/to/stories
INFO - Found 8 .txt files in /path/to/stories
INFO - Found 5 .md files in /path/to/stories
INFO - Found 28 story files to process
INFO - Processing file 1/28: story1.html
INFO - Generated 12 chunks from story1.html
...
INFO - Ingestion complete!
INFO - Total files processed: 28
INFO - Total chunks created: 342
INFO - Failed files: 0
```

### 5. Start the Backend Server

The archive endpoints are automatically available once the server starts:

```bash
cd backend
uvicorn app.main:app --reload
```

The following endpoints will be available:
- `POST /api/v1/archive/search` - Search the archive
- `GET /api/v1/archive/files` - List all files
- `GET /api/v1/archive/files/content` - Get file content
- `GET /api/v1/archive/stats` - Get archive statistics

### 6. Start the Frontend

```bash
cd frontend
npm start
```

Navigate to `http://localhost:4200` and click the "Archive" tab in the navigation.

## Using the Archive Feature

### Semantic Search

The archive uses semantic search, which means it understands the meaning of your queries, not just keywords.

**Example queries:**
- "stories about redemption and forgiveness"
- "scenes with dramatic confrontation"
- "characters struggling with moral dilemmas"
- "descriptions of magical forests"
- "dialogue between mentor and student"

### Search Results

Each result shows:
- **File name and path** - Location of the story file
- **Matching section** - Relevant text excerpt
- **Similarity score** - How well the section matches your query (High/Medium/Low)
- **View Full File** button - Opens the complete story content

### Advanced Options

Click "Advanced Options" to adjust:
- **Maximum Results** - Number of results to return (1-50)

## Database Management

### Database Location

By default, the ChromaDB database is stored at:
```
backend/chroma_db/
```

### Updating the Archive

To add new stories:
```bash
python scripts/ingest_stories.py /path/to/new/stories
```

To completely rebuild the database:
```bash
python scripts/ingest_stories.py /path/to/stories --reset
```

**Warning:** The `--reset` flag will delete all existing data!

### Database Configuration

The database location can be configured in three ways (in order of precedence):

1. **Environment variables** (recommended - add to `.env` file):
```bash
# backend/.env
ARCHIVE_DB_PATH=./chroma_db
ARCHIVE_COLLECTION_NAME=story_archive
```

2. **During ingestion** (via script argument):
```bash
python scripts/ingest_stories.py /path/to/stories --db-path /custom/path --collection custom_collection
```

3. **Default values** (if not specified):
   - Database path: `./chroma_db`
   - Collection name: `story_archive`

**Note:** The ingestion script will automatically use the settings from `.env` if no command-line arguments are provided.

## Troubleshooting

### "Archive feature is not enabled" Error

If you see this error in the frontend:
1. **Enable the feature first** - Set `ARCHIVE_DB_PATH` in your `.env` file or environment
2. **Restart the backend** - The configuration is read at startup
3. **Run the ingestion script** - Create the database with your stories
4. **Verify the database path exists** - Check `backend/chroma_db/` or your custom path
5. **Check backend logs** - Look for initialization errors
6. **Ensure ChromaDB dependencies are installed** - Run `pip install -r requirements.txt`

### No Search Results

If searches return no results:
1. Verify files were ingested successfully
2. Try broader search terms
3. Check that the collection name matches (default: "story_archive")
4. Review ingestion logs for errors

### Performance Issues

For large archives (1000+ files):
1. Increase batch size: `--batch-size 200`
2. Consider using a smaller chunk size (edit `CHUNK_SIZE` in `ingest_stories.py`)
3. Limit search results in the frontend

### Re-ingesting Files

If you need to re-ingest files:
1. Use `--reset` to clear the database first
2. Or delete the `chroma_db` directory manually
3. Run the ingestion script again

## Technical Details

### How It Works

1. **Ingestion**: Story files are split into overlapping chunks (~1000 characters)
2. **Embedding**: Text is converted to 768-dimensional vectors using the `all-mpnet-base-v2` model
3. **Storage**: Chunks, embeddings, and metadata are stored in the vector database
4. **Search**: Queries are converted to vectors using the same model and matched against stored chunks
5. **Retrieval**: Most similar chunks are returned with their source files

### Embedding Model

The archive uses **all-mpnet-base-v2**, a high-quality sentence transformer model:
- **Dimensions**: 768 (vs 384 for the smaller default model)
- **Quality**: Superior semantic understanding compared to lightweight models
- **Size**: ~420MB (downloaded automatically on first use)
- **Performance**: Excellent for semantic search across creative writing
- **Language**: Primarily English with good understanding of literary language

### Chunk Configuration

Default settings (can be modified in `ingest_stories.py`):
- **Chunk Size**: 1000 characters
- **Chunk Overlap**: 200 characters

Overlap ensures context isn't lost at chunk boundaries.

### Supported File Types

- `.html` - HTML documents (text extracted, tags removed)
- `.txt` - Plain text files
- `.md` - Markdown files (converted to text)

## API Reference

### Search Archive
```http
POST /api/v1/archive/search
Content-Type: application/json

{
  "query": "stories about magic",
  "max_results": 10,
  "filter_file_name": "optional_filter.txt"
}
```

### List Files
```http
GET /api/v1/archive/files
```

### Get File Content
```http
GET /api/v1/archive/files/content?file_path=/path/to/file.txt
```

### Get Statistics
```http
GET /api/v1/archive/stats
```

## Next Steps

- Ingest your story archives
- Experiment with different search queries
- Explore semantic relationships between stories
- Use search results to find inspiration for new stories

For questions or issues, refer to the main project documentation.
