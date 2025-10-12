# Local LLM Inference with llama.cpp

This document explains how to use the local LLM inference capabilities in the Writer Assistant backend.

## Installation

1. Install llama-cpp-python:

```bash
pip install llama-cpp-python
```

For GPU support (CUDA):
```bash
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python
```

For GPU support (Metal/M1/M2 Mac):
```bash
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python
```

2. Download a GGUF model file. Popular sources:
   - [TheBloke on HuggingFace](https://huggingface.co/TheBloke) - Many quantized models
   - [HuggingFace Model Hub](https://huggingface.co/models?library=gguf) - Official GGUF models

## Quick Start

### Interactive Chat

```bash
python -m app.cli.llm_test --model-path /path/to/model.gguf
```

### Single Prompt

```bash
python -m app.cli.llm_test --model-path /path/to/model.gguf --prompt "Write a story about a detective"
```

### Run Tests

```bash
python -m app.cli.llm_test --model-path /path/to/model.gguf --test
```

## Configuration Options

### Context and Performance

- `--n-ctx`: Context window size (default: 4096)
  - Larger values allow longer conversations but use more memory
  - Example: `--n-ctx 8192`

- `--n-gpu-layers`: Number of layers to offload to GPU (default: -1 for all)
  - Use `-1` to offload all layers to GPU
  - Use `0` for CPU-only inference
  - Use a specific number to partially offload
  - Example: `--n-gpu-layers 32`

- `--n-threads`: Number of CPU threads (default: auto)
  - Only relevant when using CPU
  - Example: `--n-threads 8`

### Generation Parameters

- `--temperature`: Sampling temperature (default: 0.7)
  - Lower values (0.1-0.5) = more focused and deterministic
  - Higher values (0.8-1.5) = more creative and random
  - Example: `--temperature 0.9`

- `--top-p`: Nucleus sampling (default: 0.95)
  - Controls diversity via cumulative probability
  - Example: `--top-p 0.9`

- `--top-k`: Top-k sampling (default: 40)
  - Limits vocabulary to top k most likely tokens
  - Example: `--top-k 50`

- `--max-tokens`: Maximum tokens to generate (default: 2048)
  - Example: `--max-tokens 1024`

- `--repeat-penalty`: Penalty for repeating tokens (default: 1.1)
  - Higher values reduce repetition
  - Example: `--repeat-penalty 1.2`

## Programmatic Usage

### Basic Usage

```python
from app.services.llm_inference import LLMInference, LLMInferenceConfig

# Create configuration
config = LLMInferenceConfig(
    model_path="/path/to/model.gguf",
    n_ctx=4096,
    n_gpu_layers=-1,
    temperature=0.7,
    max_tokens=2048
)

# Initialize model
llm = LLMInference(config)

# Generate text
response = llm.generate("Write a story about a detective")
print(response)
```

### Chat Completion

```python
messages = [
    {"role": "system", "content": "You are a creative writing assistant."},
    {"role": "user", "content": "Write a haiku about coding"}
]

response = llm.chat_completion(messages)
print(response)
```

### Custom Generation Parameters

```python
response = llm.generate(
    prompt="Continue this story...",
    max_tokens=500,
    temperature=0.9,
    top_p=0.95,
    stop=["Chapter", "END"]
)
```

### Singleton Pattern (Recommended for FastAPI)

```python
from app.services.llm_inference import initialize_llm, get_llm

# Initialize once at startup
config = LLMInferenceConfig(model_path="/path/to/model.gguf")
initialize_llm(config)

# Access anywhere in your application
llm = get_llm()
if llm:
    response = llm.generate("Your prompt here")
```

## Integration with FastAPI

You can initialize the LLM when starting your FastAPI server:

```python
# In app/main.py

from app.services.llm_inference import initialize_llm, LLMInferenceConfig
import argparse
import sys

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--model-path', type=str, help='Path to GGUF model')
args, unknown = parser.parse_known_args()

# Initialize LLM if model path provided
if args.model_path:
    config = LLMInferenceConfig(model_path=args.model_path)
    initialize_llm(config)
    print(f"LLM initialized with model: {args.model_path}")

# Then in your endpoints:
from app.services.llm_inference import get_llm

@router.post("/generate")
async def generate_text(prompt: str):
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized")

    response = llm.generate(prompt)
    return {"response": response}
```

## Starting the Server with a Model

```bash
cd backend
uvicorn app.main:app --reload -- --model-path /path/to/model.gguf
```

Or with custom settings:

```bash
uvicorn app.main:app --reload -- \
    --model-path /path/to/model.gguf \
    --n-gpu-layers -1 \
    --temperature 0.8 \
    --max-tokens 2048
```

## Recommended Models

### For Creative Writing (Story Generation)
- **Mistral-7B-Instruct** - Good balance of quality and speed
- **Llama-2-13B** - Higher quality, slower
- **Neural-Chat-7B** - Optimized for dialogue
- **OpenHermes-2.5-Mistral-7B** - Great for creative tasks

### For Fast Responses
- **TinyLlama-1.1B** - Very fast, lower quality
- **Phi-2** - Good quality/speed tradeoff

### For Best Quality
- **Mixtral-8x7B** - State-of-the-art open source
- **Llama-2-70B** - Highest quality (requires significant resources)

## Performance Tips

1. **GPU Acceleration**: Always use GPU if available (`--n-gpu-layers -1`)
2. **Context Size**: Use only what you need - larger contexts use more memory
3. **Quantization**: Use smaller quantization (Q4, Q5) for faster inference
4. **Batch Size**: For multiple requests, consider batching
5. **Model Size**: Start with 7B models, scale up as needed

## Troubleshooting

### "Model file not found"
- Ensure the path to your GGUF file is correct
- Use absolute paths if relative paths don't work

### "Out of memory"
- Reduce `--n-ctx` (context size)
- Reduce `--n-gpu-layers` to offload fewer layers
- Use a smaller model or lower quantization

### Slow inference
- Enable GPU acceleration with `--n-gpu-layers -1`
- Use a smaller model (7B instead of 13B)
- Use higher quantization (Q4 instead of Q8)
- Increase `--n-threads` for CPU inference

### Import error for llama-cpp-python
- Install with: `pip install llama-cpp-python`
- For GPU support, see installation instructions above

## Example Command Lines

### High Quality Creative Writing
```bash
python -m app.cli.llm_test \
    --model-path models/mistral-7b-instruct-v0.2.Q5_K_M.gguf \
    --n-ctx 8192 \
    --temperature 0.85 \
    --top-p 0.95 \
    --max-tokens 2048 \
    --repeat-penalty 1.15
```

### Fast Testing (CPU Only)
```bash
python -m app.cli.llm_test \
    --model-path models/tinyllama-1.1b-chat.Q4_K_M.gguf \
    --n-ctx 2048 \
    --n-gpu-layers 0 \
    --temperature 0.7 \
    --max-tokens 512
```

### Balanced Production Use
```bash
python -m app.cli.llm_test \
    --model-path models/neural-chat-7b-v3.Q5_K_M.gguf \
    --n-ctx 4096 \
    --n-gpu-layers -1 \
    --temperature 0.75 \
    --max-tokens 1024
```

## Next Steps

- Integrate LLM inference into the AI generation endpoints (ai_generation.py)
- Implement streaming responses for better UX
- Add caching for frequently used prompts
- Set up model management and switching
- Implement rate limiting and queuing for production use
