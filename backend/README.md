# Writer Assistant Backend Configuration Guide

This document provides comprehensive documentation of all configuration options available in the Writer Assistant backend. All settings are defined in `app/core/config.py` and can be configured via environment variables in the `.env` file.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration Overview](#configuration-overview)
3. [Core Settings](#core-settings)
4. [LLM Configuration](#llm-configuration)
5. [Context Management Configuration](#context-management-configuration)
6. [Endpoint-Specific Generation Settings](#endpoint-specific-generation-settings)
7. [Context Priority Settings](#context-priority-settings)
8. [Archive Configuration](#archive-configuration)
9. [Deployment Examples](#deployment-examples)
10. [Configuration Examples](#configuration-examples)
11. [Troubleshooting](#troubleshooting)
12. [Migration Notes](#migration-notes)

## Quick Start

### Option 1: Using the start script (recommended)

```bash
# Simple usage - pass model path as argument
./start_with_llm.sh /path/to/model.gguf

# With custom settings
LLM_N_CTX=8192 LLM_N_GPU_LAYERS=35 ./start_with_llm.sh /path/to/model.gguf
```

### Option 2: Using a .env file

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your model path:
   ```bash
   MODEL_PATH=/path/to/your/model.gguf
   ```

3. Start the server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Option 3: Export environment variables manually

```bash
export MODEL_PATH=/path/to/model.gguf
export LLM_N_CTX=8192
export LLM_N_GPU_LAYERS=-1

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration Overview

The backend uses Pydantic Settings for configuration management, which loads values from:
1. Default values (defined in code)
2. Environment variables (from `.env` file or system environment)
3. Runtime overrides (passed directly to services)

### How Configuration Works

The backend uses Pydantic Settings (`app.core.config.Settings`) to manage all configuration:

1. **Environment Variables**: Set via shell exports or .env file
2. **Pydantic Validation**: Automatic type checking and constraint validation
3. **LLM Initialization**: `LLMInferenceConfig.from_settings(settings)` reads validated config
4. **Error Handling**: Invalid values cause startup errors with clear messages

### Validation Examples

```bash
# ✅ Valid configuration
export LLM_TEMPERATURE=0.7    # OK: Between 0.0 and 2.0
export LLM_N_CTX=8192         # OK: Valid integer

# ❌ Invalid configuration (will fail at startup)
export LLM_TEMPERATURE=5.0    # Error: Must be <= 2.0
export LLM_N_CTX=abc          # Error: Must be integer
export LLM_TOP_P=1.5          # Error: Must be <= 1.0
```

## Core Settings

### API Configuration

| Setting | Type | Default | Description | Usage |
|---------|------|---------|-------------|-------|
| `API_V1_STR` | string | `/api/v1` | API version prefix for all endpoints | Used by FastAPI router to prefix all API routes |
| `DEBUG` | boolean | `True` | Enable debug mode with verbose logging | Controls FastAPI debug mode and detailed error responses |

## LLM Configuration

### Basic LLM Settings

| Setting | Type | Default | Description | Usage |
|---------|------|---------|-------------|-------|
| `MODEL_PATH` | string | `None` | Path to GGUF model file | **Required** for all AI generation features. Points to the local LLM model file |

### LLM Performance Settings

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `LLM_N_CTX` | integer | `4096` | ≥1024 | Context window size for the LLM | Determines maximum tokens the model can process at once |
| `LLM_N_GPU_LAYERS` | integer | `-1` | -1 to model layers | Number of GPU layers to use | -1=all layers on GPU, 0=CPU only, >0=specific layer count |
| `LLM_N_THREADS` | integer | `None` | ≥1 | CPU threads for inference | None=auto-detect, otherwise specific thread count |
| `LLM_VERBOSE` | boolean | `False` | - | Enable verbose model logging | Shows detailed llama.cpp inference logs |

### LLM Generation Settings

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `LLM_TEMPERATURE` | float | `0.7` | 0.0-2.0 | Sampling temperature | Controls randomness: 0.0=deterministic, higher=more creative |
| `LLM_TOP_P` | float | `0.95` | 0.0-1.0 | Nucleus sampling threshold | Cumulative probability cutoff for token selection |
| `LLM_TOP_K` | integer | `40` | ≥1 | Top-k sampling parameter | Limits token selection to top K most likely tokens |
| `LLM_MAX_TOKENS` | integer | `2048` | ≥1 | Maximum tokens to generate | Default limit for generation, can be overridden per endpoint |
| `LLM_REPEAT_PENALTY` | float | `1.1` | 1.0-2.0 | Penalty for repeating tokens | Reduces repetition: 1.0=no penalty, higher=more penalty |

## Archive Configuration (ChromaDB)

| Setting | Type | Default | Description | Usage |
|---------|------|---------|-------------|-------|
| `ARCHIVE_DB_PATH` | string | `None` | Path to ChromaDB vector database | If None, archive features are disabled. Points to persistent ChromaDB storage |
| `ARCHIVE_COLLECTION_NAME` | string | `story_archive` | ChromaDB collection name | Name of the collection within ChromaDB for story storage |

## Context Management Configuration

### Core Context Settings

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `CONTEXT_MAX_TOKENS` | integer | `32000` | 1000-100000 | Maximum context window size | Total available tokens for context assembly |
| `CONTEXT_BUFFER_TOKENS` | integer | `2000` | 100-10000 | Reserved tokens for generation | Tokens reserved for model output, subtracted from max |

### Context Layer Token Allocation

The context system uses a layered approach with specific token allocations:

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `CONTEXT_LAYER_A_TOKENS` | integer | `2000` | 100-10000 | System instructions layer | Core system prompts and instructions (1-2k tokens) |
| `CONTEXT_LAYER_B_TOKENS` | integer | `0` | 0-5000 | Immediate instructions layer | Currently included in Layer A, reserved for future use |
| `CONTEXT_LAYER_C_TOKENS` | integer | `13000` | 1000-25000 | Recent story segment layer | Most recent story content (10-15k tokens) |
| `CONTEXT_LAYER_D_TOKENS` | integer | `5000` | 500-10000 | Character/scene data layer | Character details and scene information (2-5k tokens) |
| `CONTEXT_LAYER_E_TOKENS` | integer | `10000` | 1000-20000 | Plot/world summary layer | Plot summaries and world-building (5-10k tokens) |

### Context Management Performance

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `CONTEXT_SUMMARIZATION_THRESHOLD` | integer | `25000` | 1000-100000 | Token threshold for summarization | When context exceeds this, triggers summarization |
| `CONTEXT_ASSEMBLY_TIMEOUT` | integer | `100` | 10-10000 | Context assembly timeout (ms) | Maximum time allowed for context assembly |

### Context Management Features

| Setting | Type | Default | Description | Usage |
|---------|------|---------|-------------|-------|
| `CONTEXT_ENABLE_RAG` | boolean | `True` | Enable RAG-based content retrieval | Enables semantic search and retrieval for context |
| `CONTEXT_ENABLE_MONITORING` | boolean | `True` | Enable context analytics/monitoring | Tracks context usage and performance metrics |
| `CONTEXT_ENABLE_CACHING` | boolean | `True` | Enable context assembly caching | Caches assembled contexts for performance |

### Context Optimization Settings

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `CONTEXT_MIN_PRIORITY_THRESHOLD` | float | `0.1` | 0.0-1.0 | Minimum priority for content inclusion | Content below this priority is excluded |
| `CONTEXT_OVERFLOW_STRATEGY` | string | `reallocate` | - | Token overflow handling strategy | Options: reject, truncate, borrow, reallocate |
| `CONTEXT_ALLOCATION_MODE` | string | `dynamic` | - | Token allocation mode | Options: static, dynamic, adaptive |

## Endpoint-Specific Generation Settings

Each API endpoint can have customized generation parameters:

### Character Feedback Endpoint

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `ENDPOINT_CHARACTER_FEEDBACK_TEMPERATURE` | float | `0.8` | 0.0-2.0 | Temperature for character feedback | Higher for more varied character responses |
| `ENDPOINT_CHARACTER_FEEDBACK_MAX_TOKENS` | integer | `800` | 100-5000 | Max tokens for character feedback | Limits length of character feedback responses |

### Editor Review Endpoint

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `ENDPOINT_EDITOR_REVIEW_TEMPERATURE` | float | `0.6` | 0.0-2.0 | Temperature for editor reviews | Lower for more consistent editorial feedback |
| `ENDPOINT_EDITOR_REVIEW_MAX_TOKENS` | integer | `800` | 100-5000 | Max tokens for editor reviews | Limits length of editorial feedback |

### Flesh Out Endpoint

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `ENDPOINT_FLESH_OUT_TEMPERATURE` | float | `0.8` | 0.0-2.0 | Temperature for flesh out generation | Higher for creative expansion of content |
| `ENDPOINT_FLESH_OUT_MAX_TOKENS` | integer | `600` | 100-5000 | Max tokens for flesh out | Limits length of content expansion |

### Generate Chapter Endpoint

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `ENDPOINT_GENERATE_CHAPTER_TEMPERATURE` | float | `0.8` | 0.0-2.0 | Temperature for chapter generation | Balanced creativity for story chapters |
| `ENDPOINT_GENERATE_CHAPTER_MAX_TOKENS` | integer | `2000` | 500-10000 | Max tokens for chapter generation | Controls chapter length |

### Generate Character Details Endpoint

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `ENDPOINT_GENERATE_CHARACTER_DETAILS_TEMPERATURE` | float | `0.7` | 0.0-2.0 | Temperature for character details | Moderate creativity for character development |
| `ENDPOINT_GENERATE_CHARACTER_DETAILS_MAX_TOKENS` | integer | `1000` | 100-5000 | Max tokens for character details | Controls detail length |

### Modify Chapter Endpoint

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `ENDPOINT_MODIFY_CHAPTER_TEMPERATURE` | float | `0.7` | 0.0-2.0 | Temperature for chapter modification | Balanced for consistent modifications |
| `ENDPOINT_MODIFY_CHAPTER_MAX_TOKENS` | integer | `2500` | 500-10000 | Max tokens for chapter modification | Allows for substantial chapter changes |

### Rater Feedback Endpoint

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `ENDPOINT_RATER_FEEDBACK_TEMPERATURE` | float | `0.7` | 0.0-2.0 | Temperature for rater feedback | Balanced for consistent rating feedback |
| `ENDPOINT_RATER_FEEDBACK_MAX_TOKENS` | integer | `600` | 100-5000 | Max tokens for rater feedback | Limits feedback length |

### Archive Endpoints

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `ENDPOINT_ARCHIVE_SEARCH_TEMPERATURE` | float | `0.3` | 0.0-1.0 | Temperature for archive search | Low for consistent search results |
| `ENDPOINT_ARCHIVE_SUMMARIZE_TEMPERATURE` | float | `0.4` | 0.0-1.0 | Temperature for archive summarization | Low for consistent summaries |

## Context Processing Priority Settings

### Content Type Priorities

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `CONTEXT_PRIORITY_PLOT_HIGH` | float | `0.8` | 0.0-1.0 | Priority for high-priority plot elements | Critical plot points get high priority |
| `CONTEXT_PRIORITY_PLOT_MEDIUM` | float | `0.5` | 0.0-1.0 | Priority for medium-priority plot elements | Standard plot elements |
| `CONTEXT_PRIORITY_PLOT_LOW` | float | `0.2` | 0.0-1.0 | Priority for low-priority plot elements | Background plot information |
| `CONTEXT_PRIORITY_CHARACTER` | float | `0.7` | 0.0-1.0 | Priority for character context | Character information priority |

### User Request Priorities

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `CONTEXT_PRIORITY_USER_HIGH` | float | `0.8` | 0.0-1.0 | Priority for high-priority user requests | Critical user instructions |
| `CONTEXT_PRIORITY_USER_MEDIUM` | float | `0.5` | 0.0-1.0 | Priority for medium-priority user requests | Standard user requests |
| `CONTEXT_PRIORITY_USER_LOW` | float | `0.2` | 0.0-1.0 | Priority for low-priority user requests | Optional user preferences |

### System Instruction Priorities

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `CONTEXT_PRIORITY_SYSTEM_HIGH` | float | `0.8` | 0.0-1.0 | Priority for high-priority system instructions | Core system behavior |
| `CONTEXT_PRIORITY_SYSTEM_MEDIUM` | float | `0.5` | 0.0-1.0 | Priority for medium-priority system instructions | Standard system guidance |
| `CONTEXT_PRIORITY_SYSTEM_LOW` | float | `0.2` | 0.0-1.0 | Priority for low-priority system instructions | Optional system hints |
| `CONTEXT_HIGH_PRIORITY_THRESHOLD` | float | `0.7` | 0.0-1.0 | Threshold for high priority classification | Elements above this are high priority |

## Context Adapter Priority Settings

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `CONTEXT_ADAPTER_SYSTEM_PREFIX_PRIORITY` | float | `1.0` | 0.0-1.0 | Priority for system prompt prefix | Opening system instructions |
| `CONTEXT_ADAPTER_SYSTEM_SUFFIX_PRIORITY` | float | `1.0` | 0.0-1.0 | Priority for system prompt suffix | Closing system instructions |
| `CONTEXT_ADAPTER_WRITING_ASSISTANT_PRIORITY` | float | `0.8` | 0.0-1.0 | Priority for writing assistant prompt | Writing-specific instructions |
| `CONTEXT_ADAPTER_WRITING_EDITOR_PRIORITY` | float | `0.8` | 0.0-1.0 | Priority for writing editor prompt | Editing-specific instructions |
| `CONTEXT_ADAPTER_CHARACTER_PROMPT_PRIORITY` | float | `0.7` | 0.0-1.0 | Priority for character prompt | Character-specific instructions |
| `CONTEXT_ADAPTER_RATER_PROMPT_PRIORITY` | float | `0.8` | 0.0-1.0 | Priority for rater prompt | Rating-specific instructions |
| `CONTEXT_ADAPTER_EDITOR_PROMPT_PRIORITY` | float | `0.8` | 0.0-1.0 | Priority for editor prompt | Editor-specific instructions |
| `CONTEXT_ADAPTER_INSTRUCTION_PRIORITY` | float | `0.9` | 0.0-1.0 | Priority for general instructions | General instruction priority |
| `CONTEXT_ADAPTER_OUTPUT_PRIORITY` | float | `0.6` | 0.0-1.0 | Priority for output elements | Generated content priority |

## Context Distillation Temperature Settings

These settings control the temperature used when summarizing different types of content:

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `DISTILLATION_GENERAL_TEMPERATURE` | float | `0.3` | 0.0-1.0 | General distillation temperature | Default for content summarization |
| `DISTILLATION_PLOT_SUMMARY_TEMPERATURE` | float | `0.3` | 0.0-1.0 | Plot summary distillation temperature | Low for consistent plot summaries |
| `DISTILLATION_CHARACTER_SUMMARY_TEMPERATURE` | float | `0.3` | 0.0-1.0 | Character summary distillation temperature | Low for consistent character summaries |
| `DISTILLATION_SCENE_SUMMARY_TEMPERATURE` | float | `0.3` | 0.0-1.0 | Scene summary distillation temperature | Low for consistent scene summaries |
| `DISTILLATION_DIALOGUE_SUMMARY_TEMPERATURE` | float | `0.4` | 0.0-1.0 | Dialogue summary distillation temperature | Slightly higher for emotional nuance |
| `DISTILLATION_FEEDBACK_SUMMARY_TEMPERATURE` | float | `0.2` | 0.0-1.0 | Feedback summary distillation temperature | Very low for consistency |
| `DISTILLATION_SYSTEM_PROMPT_TEMPERATURE` | float | `0.1` | 0.0-1.0 | System prompt distillation temperature | Very low for consistency |
| `DISTILLATION_CONVERSATION_TEMPERATURE` | float | `0.3` | 0.0-1.0 | Conversation flow distillation temperature | Low for consistent flow |

## RAG Service Settings

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `RAG_DEFAULT_TEMPERATURE` | float | `0.3` | 0.0-1.0 | Default temperature for RAG operations | Low for consistent retrieval |
| `RAG_SUMMARIZATION_TEMPERATURE` | float | `0.4` | 0.0-1.0 | Temperature for RAG summarization | Slightly higher for summary variety |

## Phase Validation Settings

These settings control the validation logic for story phases:

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `VALIDATION_PHASE_TRANSITION_THRESHOLD` | float | `0.7` | 0.0-1.0 | Threshold for valid phase transitions | Minimum score for phase advancement |
| `VALIDATION_OUTLINE_MIN_WORD_RATIO` | float | `50.0` | 1.0-1000.0 | Minimum word count ratio for outlines | Outline length validation |
| `VALIDATION_CHAPTER_MIN_WORD_RATIO` | float | `500.0` | 1.0-5000.0 | Minimum word count ratio for chapters | Chapter length validation |
| `VALIDATION_SUMMARY_MIN_WORD_RATIO` | float | `200.0` | 1.0-2000.0 | Minimum word count ratio for summaries | Summary length validation |

### Validation Scoring

| Setting | Type | Default | Range | Description | Usage |
|---------|------|---------|-------|-------------|-------|
| `VALIDATION_CONFLICT_PRESENT_SCORE` | float | `1.0` | 0.0-1.0 | Score when conflict is present | Full score for conflict presence |
| `VALIDATION_CONFLICT_ABSENT_SCORE` | float | `0.3` | 0.0-1.0 | Score when conflict is absent | Reduced score for missing conflict |
| `VALIDATION_CHARACTERS_PRESENT_SCORE` | float | `1.0` | 0.0-1.0 | Score when characters are present | Full score for character presence |
| `VALIDATION_CHARACTERS_ABSENT_SCORE` | float | `0.2` | 0.0-1.0 | Score when characters are absent | Low score for missing characters |
| `VALIDATION_DIALOGUE_PRESENT_SCORE` | float | `1.0` | 0.0-1.0 | Score when dialogue is present | Full score for dialogue presence |
| `VALIDATION_DIALOGUE_ABSENT_SCORE` | float | `0.7` | 0.0-1.0 | Score when dialogue is absent | Moderate score (dialogue optional) |
| `VALIDATION_COMPLETION_SCORE` | float | `1.0` | 0.0-1.0 | Score for completion validation | Full score for completed content |
| `VALIDATION_INCOMPLETE_SCORE` | float | `0.5` | 0.0-1.0 | Score for incomplete validation | Moderate score for incomplete content |

## Deployment Examples

### Using with Docker

Set environment variables in Dockerfile:
```dockerfile
ENV MODEL_PATH=/models/your-model.gguf
ENV LLM_N_CTX=4096
ENV LLM_N_GPU_LAYERS=-1
```

Or pass at runtime:
```bash
docker run -e MODEL_PATH=/models/model.gguf -e LLM_N_CTX=8192 writer-assistant
```

Or use a .env file:
```bash
docker run --env-file .env writer-assistant
```

### Using with systemd

Create a service file with environment variables:

```ini
[Service]
Environment="MODEL_PATH=/path/to/model.gguf"
Environment="LLM_N_CTX=8192"
Environment="LLM_N_GPU_LAYERS=-1"
ExecStart=/usr/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
WorkingDirectory=/path/to/backend
```

Or load from a .env file:
```ini
[Service]
EnvironmentFile=/path/to/backend/.env
ExecStart=/usr/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
WorkingDirectory=/path/to/backend
```

## Configuration Examples

### Basic Development Setup

```bash
# .env file for development
DEBUG=True
MODEL_PATH=/models/mistral-7b-instruct.gguf
LLM_N_CTX=4096
LLM_N_GPU_LAYERS=-1
```

### Production Setup

```bash
# .env file for production
DEBUG=False
MODEL_PATH=/production/models/large-model.gguf
LLM_N_CTX=8192
LLM_N_GPU_LAYERS=40
CONTEXT_MAX_TOKENS=64000
ARCHIVE_DB_PATH=/data/story_archive
```

### CPU-Only Setup

```bash
# .env file for CPU-only deployment
MODEL_PATH=/models/small-model.gguf
LLM_N_GPU_LAYERS=0
LLM_N_THREADS=8
LLM_N_CTX=2048
```

### High-Creativity Setup

```bash
# .env file for creative writing
LLM_TEMPERATURE=0.9
ENDPOINT_GENERATE_CHAPTER_TEMPERATURE=0.9
ENDPOINT_CHARACTER_FEEDBACK_TEMPERATURE=0.9
LLM_TOP_P=0.9
LLM_REPEAT_PENALTY=1.2
```

## Configuration Validation

The system includes automatic validation:

1. **Layer Token Validation**: Ensures total layer tokens don't exceed available tokens
2. **Range Validation**: Pydantic validates all numeric ranges
3. **Type Validation**: Ensures correct data types for all settings

## Accessing Configuration in Code

```python
from app.core.config import settings

# Access any setting
model_path = settings.MODEL_PATH
temperature = settings.LLM_TEMPERATURE
max_tokens = settings.ENDPOINT_GENERATE_CHAPTER_MAX_TOKENS
```

## Troubleshooting

### Common Issues

#### Server starts but LLM not working

Check the startup logs for:
```
INFO:     No MODEL_PATH configured in settings. LLM functionality will not be available.
```

**Solution**: Set the MODEL_PATH environment variable.

#### Validation errors at startup

If you see Pydantic validation errors:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
LLM_TEMPERATURE
  Input should be less than or equal to 2.0 [type=less_than_equal, input_value=5.0, input_type=float]
```

**Solution**: Check that all LLM configuration values are within valid ranges (see Configuration Variables section).

#### Model file not found

Check the startup logs for:
```
ERROR:    Failed to initialize LLM: Model file not found: /path/to/model.gguf
```

**Solution**: Verify the MODEL_PATH points to an existing GGUF file.

#### Out of memory errors

Try reducing:
- `LLM_N_CTX` to 2048 or lower
- `LLM_N_GPU_LAYERS` to a smaller number or 0 (CPU only)

#### Slow performance

Try increasing:
- `LLM_N_GPU_LAYERS` to offload more to GPU
- `LLM_N_THREADS` if using CPU

#### Configuration Not Loading

If settings aren't being applied:
1. Check that `.env` file exists in `backend/` directory
2. Verify there are no syntax errors in `.env`
3. Restart the backend server after changes
4. Check logs for configuration warnings

#### Archive Database Path Issues

If archive features fail:
1. Ensure `ARCHIVE_DB_PATH` points to a writable directory
2. Create the directory if it doesn't exist
3. Check file permissions
4. Verify the path is relative to the backend directory or use absolute paths

### Additional Troubleshooting

1. **Model Loading Fails**: Check `MODEL_PATH` points to valid GGUF file
2. **Context Assembly Timeout**: Increase `CONTEXT_ASSEMBLY_TIMEOUT`
3. **Memory Issues**: Reduce `CONTEXT_MAX_TOKENS` or layer allocations
4. **Archive Features Disabled**: Set `ARCHIVE_DB_PATH` to enable
5. **Token Allocation Error**: Ensure layer tokens sum doesn't exceed max tokens minus buffer

### Performance Tuning

1. **GPU Memory**: Adjust `LLM_N_GPU_LAYERS` based on VRAM
2. **Context Size**: Balance `LLM_N_CTX` with `CONTEXT_MAX_TOKENS`
3. **Generation Speed**: Lower `LLM_MAX_TOKENS` for faster responses
4. **Quality vs Speed**: Adjust temperature settings per endpoint

### Configuration Validation

The backend performs validation at startup using Pydantic. This ensures:

- **Type Safety**: All values are correct types (int, float, bool, str)
- **Range Validation**: Values are within acceptable ranges
  - `LLM_TEMPERATURE`: 0.0-2.0
  - `LLM_TOP_P`: 0.0-1.0
  - `LLM_TOP_K`: ≥ 1
  - `LLM_MAX_TOKENS`: ≥ 1
  - `LLM_REPEAT_PENALTY`: 1.0-2.0
- **Early Error Detection**: Catch configuration issues before they cause runtime problems

#### Checking Configuration

To verify your configuration is valid without starting the server:

```python
from app.core.config import settings
print(f"Model path: {settings.MODEL_PATH}")
print(f"Context size: {settings.LLM_N_CTX}")
print(f"Temperature: {settings.LLM_TEMPERATURE}")
```

If there are validation errors, Pydantic will raise them immediately.

## Migration Notes

### From Older Versions

If upgrading from older versions, note that some settings from the original `CONFIGURATION.md` are not implemented:
- `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `PROJECT_NAME`, `DATA_DIR` are not used in the current codebase
- Legacy settings like `MAX_CONTEXT_LENGTH` and `DEFAULT_TEMPERATURE` have been replaced by the new context management system

### From Command-Line Arguments

If you were previously using command-line arguments, here's the mapping:

| Old Argument | New Environment Variable |
|-------------|-------------------------|
| `--model-path` | `MODEL_PATH` |
| `--n-ctx` | `LLM_N_CTX` |
| `--n-gpu-layers` | `LLM_N_GPU_LAYERS` |
| `--n-threads` | `LLM_N_THREADS` |
| `--temperature` | `LLM_TEMPERATURE` |
| `--top-p` | `LLM_TOP_P` |
| `--top-k` | `LLM_TOP_K` |
| `--max-tokens` | `LLM_MAX_TOKENS` |
| `--repeat-penalty` | `LLM_REPEAT_PENALTY` |
| `--verbose` | `LLM_VERBOSE` |

### Configuration Precedence

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

### Production Considerations

When deploying to production:

1. **Set DEBUG=False** to disable debug mode
2. **Use absolute paths** for `MODEL_PATH` and `ARCHIVE_DB_PATH`
3. **Secure the .env file** (add to .gitignore, restrict permissions)
4. **Consider using system environment variables** instead of .env file

### Accessing Configuration in Code

Configuration is accessed through the `settings` object:

```python
from app.core.config import settings

# Access configuration values
db_path = settings.ARCHIVE_DB_PATH
collection_name = settings.ARCHIVE_COLLECTION_NAME
model_path = settings.MODEL_PATH
```

## Common Issues and Troubleshooting

### Frontend Worldbuilding Sync Errors

**Issue**: Frontend shows error "Backend sync failed, falling back to local sync: Not Found"

**Cause**: The backend server is not running or not accessible at the expected URL.

**Solution**:
1. Verify the backend server is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. If not running, start the server:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Test the worldbuilding endpoint specifically:
   ```bash
   curl http://localhost:8000/api/v1/worldbuilding/status/test
   ```

**Note**: The frontend will automatically fall back to local sync when the backend is unavailable, so the application will continue to work, but you'll see this error in the console logs.
