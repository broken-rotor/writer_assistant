# Archive Feature - Quick Start

## TL;DR

The Story Archive feature is **optional** and **disabled by default**. It provides two modes:
- **Search Mode**: Semantic search through your archived stories
- **Chat Mode (RAG)**: AI-powered Q&A about your stories (requires LLM configuration)

Here's how to enable it:

### Enable Archive Feature

1. **Create/edit `.env` file**:
   ```bash
   cd backend
   # Add this line to .env file:
   ARCHIVE_DB_PATH=./chroma_db
   ```

2. **Install dependencies**:
   ```bash
   pip install chromadb beautifulsoup4 markdown
   ```

3. **Ingest your stories**:
   ```bash
   python scripts/ingest_stories.py /path/to/your/stories
   ```

4. **Restart backend**:
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Use the Archive tab** in the frontend!

### Enable RAG/Chat Mode (Optional)

To enable AI-powered Q&A about your stories:

1. **Install LLM library**:
   ```bash
   pip install llama-cpp-python
   ```

2. **Download a model** (GGUF format):
   - Recommended: Mistral 7B Instruct or Llama 3.2 3B
   - Place in `backend/models/` directory

3. **Configure LLM in `.env`**:
   ```bash
   MODEL_PATH=./models/your-model.gguf
   ```

4. **Restart backend** and use the **Chat (RAG)** tab!

For detailed RAG setup and usage, see [RAG_FEATURE.md](RAG_FEATURE.md).

## Without Configuration

If you don't configure `ARCHIVE_DB_PATH`:
- The backend will start normally
- The Archive tab will show: "Archive feature is not enabled"
- All other features work as usual
- No ChromaDB dependencies required

## Example .env Configuration

```bash
# Optional: Enable archive feature
ARCHIVE_DB_PATH=./chroma_db
ARCHIVE_COLLECTION_NAME=story_archive

# Optional: LLM configuration
# MODEL_PATH=/path/to/model.gguf
```

## Full Documentation

See [ARCHIVE_SETUP.md](ARCHIVE_SETUP.md) for complete setup instructions.
