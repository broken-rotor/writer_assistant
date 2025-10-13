# Backend Configuration Guide

This document describes all available configuration options for the Writer Assistant backend.

## Configuration Files

### `.env` File

The backend uses environment variables for configuration, loaded from a `.env` file in the `backend/` directory.

Copy `.env.example` to `.env` and customize as needed:
```bash
cp .env.example .env
```

## Configuration Options

### General Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DEBUG` | boolean | `True` | Enable debug mode |
| `SECRET_KEY` | string | `dev-secret-key-change-in-production` | Secret key for security (change in production!) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | integer | `30` | JWT token expiration time |
| `API_V1_STR` | string | `/api/v1` | API version prefix |
| `PROJECT_NAME` | string | `Writer Assistant` | Project name |

### Data Storage

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATA_DIR` | string | `data` | Directory for JSON data files |

### Archive Configuration (ChromaDB)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ARCHIVE_DB_PATH` | string | `./chroma_db` | Path to ChromaDB vector database directory |
| `ARCHIVE_COLLECTION_NAME` | string | `story_archive` | ChromaDB collection name for story archive |

**Example:**
```bash
# Store archive in a custom location
ARCHIVE_DB_PATH=/mnt/data/story_archive_db
ARCHIVE_COLLECTION_NAME=my_stories
```

### LLM Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MODEL_PATH` | string | `None` | Path to GGUF model file (required for LLM features) |

**Example:**
```bash
MODEL_PATH=/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf
```

### LLM Performance Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LLM_N_CTX` | integer | `4096` | Context window size |
| `LLM_N_GPU_LAYERS` | integer | `-1` | GPU layers (-1=all, 0=CPU only) |
| `LLM_N_THREADS` | integer | `None` | CPU threads (None=auto) |
| `LLM_VERBOSE` | boolean | `False` | Enable verbose model logging |

**Example:**
```bash
# Use GPU acceleration with large context
LLM_N_CTX=8192
LLM_N_GPU_LAYERS=33
```

### LLM Generation Settings

| Variable | Type | Default | Range | Description |
|----------|------|---------|-------|-------------|
| `LLM_TEMPERATURE` | float | `0.7` | 0.0-2.0 | Sampling temperature (higher=more creative) |
| `LLM_TOP_P` | float | `0.95` | 0.0-1.0 | Nucleus sampling threshold |
| `LLM_TOP_K` | integer | `40` | ≥1 | Top-k sampling parameter |
| `LLM_MAX_TOKENS` | integer | `2048` | ≥1 | Maximum tokens to generate |
| `LLM_REPEAT_PENALTY` | float | `1.1` | 1.0-2.0 | Penalty for repeating tokens |

**Example:**
```bash
# More creative, longer output
LLM_TEMPERATURE=0.9
LLM_MAX_TOKENS=4096
LLM_REPEAT_PENALTY=1.2
```

### Legacy Settings (Deprecated)

These settings may be removed in future versions:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_CONTEXT_LENGTH` | integer | `4000` | Legacy context length |
| `DEFAULT_TEMPERATURE` | float | `0.7` | Legacy temperature |

## Example .env File

Here's a complete example configuration:

```bash
# General Settings
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Data Storage
DATA_DIR=data

# Archive Configuration (ChromaDB)
ARCHIVE_DB_PATH=./chroma_db
ARCHIVE_COLLECTION_NAME=story_archive

# LLM Configuration
MODEL_PATH=/models/mistral-7b-instruct.gguf

# LLM Performance
LLM_N_CTX=4096
LLM_N_GPU_LAYERS=-1
LLM_VERBOSE=false

# LLM Generation
LLM_TEMPERATURE=0.7
LLM_TOP_P=0.95
LLM_TOP_K=40
LLM_MAX_TOKENS=2048
LLM_REPEAT_PENALTY=1.1
```

## Accessing Configuration in Code

Configuration is accessed through the `settings` object:

```python
from app.core.config import settings

# Access configuration values
db_path = settings.ARCHIVE_DB_PATH
collection_name = settings.ARCHIVE_COLLECTION_NAME
model_path = settings.MODEL_PATH
```

## Configuration Precedence

Configuration values are loaded in the following order (later overrides earlier):

1. **Default values** (defined in `config.py`)
2. **Environment variables** (from `.env` file or system environment)
3. **Runtime overrides** (passed directly to services/functions)

Example:
```python
# Uses settings.ARCHIVE_DB_PATH by default
service = ArchiveService()

# Override at runtime
service = ArchiveService(db_path="/custom/path")
```

## Production Considerations

When deploying to production:

1. **Change SECRET_KEY** to a secure random value
2. **Set DEBUG=False** to disable debug mode
3. **Use absolute paths** for `MODEL_PATH` and `ARCHIVE_DB_PATH`
4. **Secure the .env file** (add to .gitignore, restrict permissions)
5. **Consider using system environment variables** instead of .env file

## Troubleshooting

### Configuration Not Loading

If settings aren't being applied:
1. Check that `.env` file exists in `backend/` directory
2. Verify there are no syntax errors in `.env`
3. Restart the backend server after changes
4. Check logs for configuration warnings

### Archive Database Path Issues

If archive features fail:
1. Ensure `ARCHIVE_DB_PATH` points to a writable directory
2. Create the directory if it doesn't exist
3. Check file permissions
4. Verify the path is relative to the backend directory or use absolute paths

### Model Loading Issues

If LLM features don't work:
1. Verify `MODEL_PATH` points to a valid GGUF file
2. Check file permissions
3. Ensure the model is compatible with llama-cpp-python
4. Review backend logs for specific error messages
