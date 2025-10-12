#!/bin/bash
# Start the Writer Assistant API with a local LLM model
#
# Usage: ./start_with_llm.sh /path/to/model.gguf
#
# Optional: Set environment variables before running:
#   N_CTX=8192 N_GPU_LAYERS=-1 ./start_with_llm.sh /path/to/model.gguf

MODEL_PATH="${1}"
N_CTX="${N_CTX:-4096}"
N_GPU_LAYERS="${N_GPU_LAYERS:--1}"
TEMPERATURE="${TEMPERATURE:-0.7}"
MAX_TOKENS="${MAX_TOKENS:-2048}"

if [ -z "$MODEL_PATH" ]; then
    echo "Error: Model path is required"
    echo "Usage: $0 /path/to/model.gguf"
    exit 1
fi

if [ ! -f "$MODEL_PATH" ]; then
    echo "Error: Model file not found: $MODEL_PATH"
    exit 1
fi

echo "Starting Writer Assistant API with local LLM..."
echo "Model: $MODEL_PATH"
echo "Context size: $N_CTX"
echo "GPU layers: $N_GPU_LAYERS"
echo "Temperature: $TEMPERATURE"
echo "Max tokens: $MAX_TOKENS"
echo ""
echo "Server will be available at: http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 -- \
    --model-path "$MODEL_PATH" \
    --n-ctx "$N_CTX" \
    --n-gpu-layers "$N_GPU_LAYERS" \
    --temperature "$TEMPERATURE" \
    --max-tokens "$MAX_TOKENS"
