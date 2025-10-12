# Environment Variable Configuration

The Writer Assistant backend uses environment variables for all LLM configuration, managed through Pydantic Settings. This provides type validation, default values, automatic .env file loading, and simplifies deployment with standard tools.

## How Configuration Works

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

## Configuration Variables

### Required

- **MODEL_PATH**: Path to your GGUF model file
  - If not set, the server will start without LLM functionality

### Performance Settings

- **LLM_N_CTX**: Context window size (default: 4096)
  - Higher values allow longer prompts but use more memory
  - Common values: 2048, 4096, 8192, 16384, 32768

- **LLM_N_GPU_LAYERS**: Number of layers to offload to GPU (default: -1)
  - `-1`: Offload all layers (full GPU acceleration)
  - `0`: CPU only (no GPU)
  - `1-99`: Offload specified number of layers (hybrid mode)

- **LLM_N_THREADS**: Number of CPU threads (default: auto)
  - Leave empty or unset for automatic detection
  - Set to specific number to limit CPU usage

### Generation Settings

- **LLM_TEMPERATURE**: Sampling temperature (default: 0.7)
  - Range: 0.0-2.0
  - Lower = more deterministic, Higher = more creative
  - Recommended: 0.5-0.9

- **LLM_TOP_P**: Nucleus sampling threshold (default: 0.95)
  - Range: 0.0-1.0
  - Controls diversity of output

- **LLM_TOP_K**: Top-k sampling parameter (default: 40)
  - Limits token selection to top K most likely tokens
  - Higher = more diverse

- **LLM_MAX_TOKENS**: Maximum tokens to generate (default: 2048)
  - Controls maximum length of generated text

- **LLM_REPEAT_PENALTY**: Penalty for repeating tokens (default: 1.1)
  - Values > 1.0 discourage repetition
  - Range: 1.0-2.0

### Debugging

- **LLM_VERBOSE**: Enable verbose model logging (default: false)
  - Set to `true`, `1`, or `yes` to enable
  - Shows detailed model loading and inference information

## Example Configurations

### Balanced (Default)
```bash
MODEL_PATH=/path/to/model.gguf
LLM_N_CTX=4096
LLM_N_GPU_LAYERS=-1
LLM_TEMPERATURE=0.7
```

### High Quality (More deterministic)
```bash
MODEL_PATH=/path/to/model.gguf
LLM_N_CTX=8192
LLM_N_GPU_LAYERS=-1
LLM_TEMPERATURE=0.5
LLM_TOP_P=0.9
LLM_MAX_TOKENS=4096
```

### Creative Writing
```bash
MODEL_PATH=/path/to/model.gguf
LLM_N_CTX=8192
LLM_N_GPU_LAYERS=-1
LLM_TEMPERATURE=0.8
LLM_TOP_P=0.95
LLM_TOP_K=50
```

### CPU Only (No GPU)
```bash
MODEL_PATH=/path/to/model.gguf
LLM_N_CTX=2048
LLM_N_GPU_LAYERS=0
LLM_N_THREADS=8
LLM_TEMPERATURE=0.7
```

### Hybrid (Partial GPU)
```bash
MODEL_PATH=/path/to/model.gguf
LLM_N_CTX=4096
LLM_N_GPU_LAYERS=20  # Offload 20 layers to GPU
LLM_TEMPERATURE=0.7
```

## Migration from Command-Line Arguments

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

## Troubleshooting

### Server starts but LLM not working

Check the startup logs for:
```
INFO:     No MODEL_PATH configured in settings. LLM functionality will not be available.
```

Solution: Set the MODEL_PATH environment variable.

### Validation errors at startup

If you see Pydantic validation errors:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
LLM_TEMPERATURE
  Input should be less than or equal to 2.0 [type=less_than_equal, input_value=5.0, input_type=float]
```

Solution: Check that all LLM configuration values are within valid ranges (see Configuration Variables section).

### Model file not found

Check the startup logs for:
```
ERROR:    Failed to initialize LLM: Model file not found: /path/to/model.gguf
```

Solution: Verify the MODEL_PATH points to an existing GGUF file.

### Out of memory errors

Try reducing:
- `LLM_N_CTX` to 2048 or lower
- `LLM_N_GPU_LAYERS` to a smaller number or 0 (CPU only)

### Slow performance

Try increasing:
- `LLM_N_GPU_LAYERS` to offload more to GPU
- `LLM_N_THREADS` if using CPU

## Using with Docker

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

## Using with systemd

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

## Configuration Validation

The backend performs validation at startup using Pydantic. This ensures:

- **Type Safety**: All values are correct types (int, float, bool, str)
- **Range Validation**: Values are within acceptable ranges
  - `LLM_TEMPERATURE`: 0.0-2.0
  - `LLM_TOP_P`: 0.0-1.0
  - `LLM_TOP_K`: ≥ 1
  - `LLM_MAX_TOKENS`: ≥ 1
  - `LLM_REPEAT_PENALTY`: 1.0-2.0
- **Early Error Detection**: Catch configuration issues before they cause runtime problems

### Checking Configuration

To verify your configuration is valid without starting the server:

```python
from app.core.config import settings
print(f"Model path: {settings.MODEL_PATH}")
print(f"Context size: {settings.LLM_N_CTX}")
print(f"Temperature: {settings.LLM_TEMPERATURE}")
```

If there are validation errors, Pydantic will raise them immediately.
