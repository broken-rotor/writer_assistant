# Migration to Environment Variables

## Summary

The Writer Assistant backend has been updated to use environment variables for LLM configuration instead of command-line arguments. This change simplifies deployment and makes the application more compatible with standard deployment tools (Docker, systemd, Heroku, etc.).

## Changes Made

### 1. Code Changes

#### `app/core/config.py`
- **Added**: All LLM configuration fields to Settings class with Pydantic validation
- **Added**: Field constraints (temperature between 0.0-2.0, etc.)
- **Added**: Comprehensive field descriptions
- **Changed**: Configuration now centralized in Pydantic Settings

#### `app/services/llm_inference.py`
- **Removed**: `add_llm_args()` function for argparse
- **Removed**: `from_args()` class method
- **Added**: `from_settings()` class method that reads from Settings object
- **Changed**: Configuration now comes from Pydantic Settings instead of direct env var reading

#### `app/main.py`
- **Removed**: All argparse-related code
- **Removed**: Command-line argument parsing
- **Changed**: Now uses `LLMInferenceConfig.from_settings(settings)` to initialize LLM
- **Simplified**: Cleaner initialization logic with automatic .env file loading

#### `start_with_llm.sh`
- **Changed**: Now exports environment variables instead of passing command-line args
- **Simplified**: Directly calls `uvicorn` without wrapper scripts
- **Improved**: Better error messages and clearer usage

### 2. Configuration Files

#### `.env.example`
- **Updated**: Added all LLM configuration variables with documentation
- **Added**: Clear comments explaining each variable
- **Added**: Example values and recommended settings

### 3. Documentation

#### `ENV_CONFIG.md` (New)
- Complete guide to using environment variables
- Example configurations for different use cases
- Troubleshooting guide
- Migration guide from command-line arguments

#### `MIGRATION_TO_ENV_VARS.md` (This file)
- Summary of changes
- Migration instructions

### 4. Tests

#### `tests/test_llm_inference.py`
- **Removed**: `TestCommandLineArguments` class
- **Added**: `test_config_from_settings()` - tests Settings object parsing
- **Added**: `test_config_from_settings_minimal()` - tests with only MODEL_PATH
- **Added**: `test_config_from_settings_no_model_path()` - tests None return
- **Added**: `test_config_from_settings_with_verbose()` - tests verbose flag
- **Updated**: All tests now use `Mock(spec=Settings)` pattern

## Environment Variable Mapping

| Old Command-Line Argument | New Environment Variable | Default |
|--------------------------|-------------------------|---------|
| `--model-path` | `MODEL_PATH` | (none) |
| `--n-ctx` | `LLM_N_CTX` | 4096 |
| `--n-gpu-layers` | `LLM_N_GPU_LAYERS` | -1 |
| `--n-threads` | `LLM_N_THREADS` | (auto) |
| `--temperature` | `LLM_TEMPERATURE` | 0.7 |
| `--top-p` | `LLM_TOP_P` | 0.95 |
| `--top-k` | `LLM_TOP_K` | 40 |
| `--max-tokens` | `LLM_MAX_TOKENS` | 2048 |
| `--repeat-penalty` | `LLM_REPEAT_PENALTY` | 1.1 |
| `--verbose` | `LLM_VERBOSE` | false |

## Migration Instructions

### If you were using the shell script:

**Before:**
```bash
./start_with_llm.sh /path/to/model.gguf
N_CTX=8192 ./start_with_llm.sh /path/to/model.gguf
```

**After:**
```bash
./start_with_llm.sh /path/to/model.gguf
LLM_N_CTX=8192 ./start_with_llm.sh /path/to/model.gguf
```

The script now uses `LLM_*` prefixed environment variables instead of unprefixed ones.

### If you were using uvicorn directly with run_server.py:

**Before:**
```bash
python run_server.py --model-path /path/to/model.gguf --n-ctx 8192
```

**After:**
```bash
export MODEL_PATH=/path/to/model.gguf
export LLM_N_CTX=8192
uvicorn app.main:app --reload
```

Or use a `.env` file (recommended):
```bash
# Create .env file
cp .env.example .env
# Edit .env and set MODEL_PATH
uvicorn app.main:app --reload
```

### If you were importing the module programmatically:

**Before:**
```python
import argparse
from app.services.llm_inference import LLMInferenceConfig, initialize_llm, add_llm_args

parser = argparse.ArgumentParser()
add_llm_args(parser)
args = parser.parse_args()
config = LLMInferenceConfig.from_args(args)
initialize_llm(config)
```

**After:**
```python
from app.core.config import settings
from app.services.llm_inference import LLMInferenceConfig, initialize_llm

# Option 1: Use from_settings() with global settings (recommended)
config = LLMInferenceConfig.from_settings(settings)
if config:
    initialize_llm(config)

# Option 2: Create config manually
config = LLMInferenceConfig(
    model_path="/path/to/model.gguf",
    n_ctx=4096,
    n_gpu_layers=-1,
    # ... other settings
)
initialize_llm(config)
```

## Benefits

1. **Simpler deployment**: Standard environment variable configuration
2. **Docker-friendly**: No need for complex command-line argument passing
3. **12-factor app compliance**: Configuration via environment
4. **Easier CI/CD**: Standard approach for most platforms
5. **Better secrets management**: Environment variables are easier to inject securely
6. **No uvicorn conflicts**: Environment variables don't interfere with uvicorn's args
7. **Type validation**: Pydantic automatically validates all configuration values at startup
8. **Better error messages**: Clear validation errors for misconfigured values
9. **Field constraints**: Automatic enforcement of valid ranges (temperature 0.0-2.0, etc.)
10. **Single source of truth**: All configuration centralized in Settings class

## Breaking Changes

⚠️ **This is a breaking change** if you were:
- Using command-line arguments directly with `uvicorn app.main:app --model-path ...`
- Calling `add_llm_args()` or `from_args()` in custom code
- Calling `from_env()` in custom code (changed to `from_settings()`)
- Relying on the `run_server.py` wrapper script (deleted)

## Validation Errors

With Pydantic Settings, invalid configuration values will now cause startup errors:

```python
# Invalid temperature value
export LLM_TEMPERATURE=5.0  # Error: Must be between 0.0 and 2.0

# Invalid type
export LLM_N_CTX=abc  # Error: Input should be a valid integer
```

This helps catch configuration issues early rather than at runtime.

## Testing

Run the test suite to verify everything works:
```bash
cd backend
pytest tests/test_llm_inference.py -v
```

All tests should pass, including the new environment variable tests.

## Rollback Instructions

If you need to rollback to command-line arguments:

1. Revert the changes:
   ```bash
   git revert <commit-hash>
   ```

2. Or manually restore the old behavior by checking out the previous version of:
   - `app/services/llm_inference.py`
   - `app/main.py`
   - `tests/test_llm_inference.py`

## Questions?

See `ENV_CONFIG.md` for detailed usage instructions and examples.
