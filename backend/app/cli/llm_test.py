#!/usr/bin/env python
"""
Simple CLI tool to test local LLM inference.
Usage: python -m app.cli.llm_test --model-path /path/to/model.gguf
"""
import argparse
import sys
import logging
from pathlib import Path

from app.services.llm_inference import (
    LLMInference,
    LLMInferenceConfig,
    add_llm_args
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def interactive_mode(llm: LLMInference):
    """Run an interactive chat session"""
    print("\n=== Interactive LLM Chat ===")
    print("Type 'quit' or 'exit' to end the session")
    print("Type 'clear' to start a new conversation")
    print("=" * 40)

    messages = []

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if user_input.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break

            if user_input.lower() == 'clear':
                messages = []
                print("Conversation cleared.")
                continue

            if not user_input:
                continue

            # Add user message
            messages.append({"role": "user", "content": user_input})

            # Generate response
            print("\nAssistant: ", end="", flush=True)
            try:
                response = llm.chat_completion(messages)
                print(response)

                # Add assistant response to history
                messages.append({"role": "assistant", "content": response})

            except Exception as e:
                logger.error(f"Error generating response: {e}")
                print(f"Error: {e}")
                # Remove the failed user message
                messages.pop()

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


def single_prompt_mode(llm: LLMInference, prompt: str):
    """Generate a single response from a prompt"""
    print(f"\nPrompt: {prompt}\n")
    print("Generating response...\n")

    try:
        response = llm.generate(prompt)
        print(f"Response:\n{response}\n")
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        print(f"Error: {e}")
        sys.exit(1)


def test_generation(llm: LLMInference):
    """Run a simple test to verify the model works"""
    print("\n=== Testing Model ===")

    test_prompts = [
        "What is the capital of France?",
        "Write a haiku about coding.",
        "Explain what a neural network is in one sentence."
    ]

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n--- Test {i}/{len(test_prompts)} ---")
        print(f"Prompt: {prompt}")

        try:
            response = llm.generate(prompt, max_tokens=100)
            print(f"Response: {response}")
        except Exception as e:
            logger.error(f"Error on test {i}: {e}")
            print(f"Error: {e}")

    print("\n=== Tests Complete ===")


def main():
    parser = argparse.ArgumentParser(
        description="Test local LLM inference with llama.cpp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive chat mode
  python -m app.cli.llm_test --model-path /path/to/model.gguf

  # Single prompt
  python -m app.cli.llm_test --model-path /path/to/model.gguf --prompt "Hello, how are you?"

  # Run tests
  python -m app.cli.llm_test --model-path /path/to/model.gguf --test

  # CPU only with custom settings
  python -m app.cli.llm_test --model-path /path/to/model.gguf --n-gpu-layers 0 --temperature 0.8
        """
    )

    # Add LLM arguments
    add_llm_args(parser)

    # Add mode arguments
    mode_group = parser.add_argument_group('Mode')
    mode_group.add_argument(
        '--prompt',
        type=str,
        help='Single prompt to generate from (non-interactive)'
    )
    mode_group.add_argument(
        '--test',
        action='store_true',
        help='Run test prompts instead of interactive mode'
    )
    mode_group.add_argument(
        '--interactive',
        action='store_true',
        help='Force interactive mode (default if no other mode specified)'
    )

    args = parser.parse_args()

    # Validate model path
    if not args.model_path:
        parser.error("--model-path is required")

    # Create config and initialize model
    print(f"\nInitializing model from: {args.model_path}")
    print(f"Settings:")
    print(f"  Context size: {args.n_ctx}")
    print(f"  GPU layers: {args.n_gpu_layers}")
    print(f"  Temperature: {args.temperature}")
    print(f"  Max tokens: {args.max_tokens}")

    try:
        config = LLMInferenceConfig.from_args(args)
        llm = LLMInference(config)
    except Exception as e:
        logger.error(f"Failed to initialize model: {e}")
        print(f"\nError: {e}")
        sys.exit(1)

    # Determine mode and run
    if args.test:
        test_generation(llm)
    elif args.prompt:
        single_prompt_mode(llm, args.prompt)
    else:
        interactive_mode(llm)


if __name__ == "__main__":
    main()
