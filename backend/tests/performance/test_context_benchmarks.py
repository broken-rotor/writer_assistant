"""
Performance benchmarks for context processing during migration.

These tests compare legacy vs structured context processing performance
to ensure the migration doesn't degrade system performance.
"""

import pytest
import time
import statistics
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from app.services.context_optimization import ContextOptimizationService
from app.services.context_manager import ContextManager
from app.services.unified_context_processor import UnifiedContextProcessor
from app.models.context_models import (
    StructuredContextContainer,
    ContextElement,
    ContextType,
    ComposePhase
)
from app.models.generation_models import SystemPrompts, CharacterInfo


class TestContextProcessingBenchmarks:
    """Performance benchmarks for context processing."""
    
    @pytest.fixture
    def legacy_context_data(self):
        """Sample legacy context data for benchmarking."""
        return {
            "system_prompts": SystemPrompts(
                mainPrefix="You are a creative writing assistant",
                mainSuffix="Generate engaging and coherent content",
                characterPrefix="Focus on character development",
                plotPrefix="Maintain narrative consistency"
            ),
            "worldbuilding": "A fantasy world with magic systems, ancient kingdoms, and mystical creatures. " * 50,  # Large content
            "story_summary": "An epic tale of heroes and villains in a world of magic and mystery. " * 30,  # Large content
            "characters": [
                CharacterInfo(
                    name=f"Character_{i}",
                    description=f"A detailed character with complex motivations and background. " * 10,
                    personality=f"Complex personality traits for character {i}"
                ) for i in range(10)  # Multiple characters
            ],
            "plot_point": "A critical moment in the story where everything changes",
            "previous_chapters": [f"Chapter {i} content with detailed narrative. " * 20 for i in range(5)]
        }
    
    @pytest.fixture
    def structured_context_data(self):
        """Sample structured context data for benchmarking."""
        return StructuredContextContainer(
            plot_elements=[
                ContextElement(
                    type=ContextType.PLOT_OUTLINE,
                    content=f"Plot element {i} with detailed narrative structure. " * 10,
                    priority="high" if i < 3 else "medium",
                    tags=[f"plot_{i}", "narrative"],
                    metadata={"chapter": i, "importance": "high" if i < 3 else "medium"}
                ) for i in range(20)  # Many plot elements
            ],
            character_contexts=[
                {
                    "character_id": f"char_{i}",
                    "character_name": f"Character_{i}",
                    "current_state": {
                        "emotion": "determined",
                        "location": f"location_{i}",
                        "goals": [f"goal_{j}" for j in range(3)]
                    },
                    "personality_traits": [f"trait_{j}" for j in range(5)],
                    "relationships": {f"char_{j}": "friendly" for j in range(i)}
                } for i in range(10)  # Multiple characters
            ],
            user_requests=[
                ContextElement(
                    type=ContextType.USER_REQUEST,
                    content=f"User request {i} with specific requirements. " * 5,
                    priority="medium",
                    tags=[f"request_{i}"]
                ) for i in range(5)
            ],
            system_instructions=[
                ContextElement(
                    type=ContextType.SYSTEM_INSTRUCTION,
                    content=f"System instruction {i} for content generation. " * 3,
                    priority="high",
                    tags=["system", f"instruction_{i}"]
                ) for i in range(3)
            ],
            context_metadata={
                "total_elements": 38,  # 20 + 10 + 5 + 3
                "processing_mode": "structured",
                "version": "1.0"
            }
        )
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM to avoid actual inference during benchmarks."""
        with patch('app.services.llm_inference.get_llm') as mock:
            llm_instance = Mock()
            llm_instance.chat_completion.return_value = "Mocked response"
            mock.return_value = llm_instance
            yield llm_instance
    
    def benchmark_function(self, func, *args, iterations: int = 10, **kwargs) -> Dict[str, float]:
        """Benchmark a function and return performance metrics."""
        times = []
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        return {
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "min": min(times),
            "max": max(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0.0,
            "total_time": sum(times),
            "iterations": iterations
        }
    
    def test_legacy_vs_structured_context_processing_speed(self, legacy_context_data, structured_context_data, mock_llm):
        """Compare processing speed between legacy and structured context."""
        # Initialize services
        legacy_service = ContextOptimizationService()
        structured_service = ContextManager()
        unified_processor = UnifiedContextProcessor()
        
        # Benchmark legacy context processing
        def process_legacy():
            return legacy_service.optimize_chapter_generation_context(
                system_prompts=legacy_context_data["system_prompts"],
                worldbuilding=legacy_context_data["worldbuilding"],
                story_summary=legacy_context_data["story_summary"],
                characters=legacy_context_data["characters"],
                plot_point=legacy_context_data["plot_point"],
                previous_chapters=legacy_context_data["previous_chapters"]
            )
        
        # Benchmark structured context processing
        def process_structured():
            return structured_service.assemble_context(
                structured_context=structured_context_data,
                agent_type="writer",
                compose_phase=ComposePhase.CHAPTER_WRITING
            )
        
        # Benchmark unified processor (structured mode)
        def process_unified_structured():
            return unified_processor.process_generate_chapter_context(
                structured_context=structured_context_data,
                context_mode="structured",
                compose_phase=ComposePhase.CHAPTER_WRITING
            )
        
        # Run benchmarks
        legacy_metrics = self.benchmark_function(process_legacy, iterations=5)
        structured_metrics = self.benchmark_function(process_structured, iterations=5)
        unified_metrics = self.benchmark_function(process_unified_structured, iterations=5)
        
        # Print results
        print(f"\n{'='*60}")
        print("CONTEXT PROCESSING PERFORMANCE COMPARISON")
        print(f"{'='*60}")
        print(f"Legacy Context Processing:")
        print(f"  Mean: {legacy_metrics['mean']:.4f}s")
        print(f"  Median: {legacy_metrics['median']:.4f}s")
        print(f"  Min: {legacy_metrics['min']:.4f}s")
        print(f"  Max: {legacy_metrics['max']:.4f}s")
        
        print(f"\nStructured Context Processing:")
        print(f"  Mean: {structured_metrics['mean']:.4f}s")
        print(f"  Median: {structured_metrics['median']:.4f}s")
        print(f"  Min: {structured_metrics['min']:.4f}s")
        print(f"  Max: {structured_metrics['max']:.4f}s")
        
        print(f"\nUnified Processor (Structured):")
        print(f"  Mean: {unified_metrics['mean']:.4f}s")
        print(f"  Median: {unified_metrics['median']:.4f}s")
        print(f"  Min: {unified_metrics['min']:.4f}s")
        print(f"  Max: {unified_metrics['max']:.4f}s")
        
        # Calculate performance ratios
        structured_vs_legacy = structured_metrics['mean'] / legacy_metrics['mean']
        unified_vs_legacy = unified_metrics['mean'] / legacy_metrics['mean']
        
        print(f"\nPerformance Ratios:")
        print(f"  Structured vs Legacy: {structured_vs_legacy:.2f}x")
        print(f"  Unified vs Legacy: {unified_vs_legacy:.2f}x")
        
        # Performance assertions
        assert legacy_metrics['mean'] < 30.0, "Legacy processing should complete within 30 seconds"
        assert structured_metrics['mean'] < 30.0, "Structured processing should complete within 30 seconds"
        assert unified_metrics['mean'] < 30.0, "Unified processing should complete within 30 seconds"
        
        # Structured context should not be significantly slower than legacy
        assert structured_vs_legacy < 2.0, "Structured context should not be more than 2x slower than legacy"
        assert unified_vs_legacy < 2.0, "Unified processor should not be more than 2x slower than legacy"
    
    def test_context_size_scaling_performance(self, mock_llm):
        """Test how performance scales with context size."""
        structured_service = ContextManager()
        
        # Test different context sizes
        sizes = [10, 50, 100, 200]
        results = {}
        
        for size in sizes:
            # Create context with specified number of elements
            large_context = StructuredContextContainer(
                plot_elements=[
                    ContextElement(
                        type=ContextType.PLOT_OUTLINE,
                        content=f"Plot element {i} with content. " * 10,
                        priority="medium"
                    ) for i in range(size)
                ],
                context_metadata={
                    "total_elements": size,
                    "processing_mode": "structured"
                }
            )
            
            def process_large_context():
                return structured_service.assemble_context(
                    structured_context=large_context,
                    agent_type="writer",
                    compose_phase=ComposePhase.CHAPTER_WRITING
                )
            
            metrics = self.benchmark_function(process_large_context, iterations=3)
            results[size] = metrics
        
        # Print scaling results
        print(f"\n{'='*60}")
        print("CONTEXT SIZE SCALING PERFORMANCE")
        print(f"{'='*60}")
        for size, metrics in results.items():
            print(f"Size {size} elements: {metrics['mean']:.4f}s (±{metrics['std_dev']:.4f}s)")
        
        # Check that performance scales reasonably
        for size in sizes:
            assert results[size]['mean'] < 30.0, f"Processing {size} elements should complete within 30 seconds"
        
        # Performance should scale sub-linearly (not worse than linear)
        if len(sizes) >= 2:
            small_size, large_size = sizes[0], sizes[-1]
            small_time, large_time = results[small_size]['mean'], results[large_size]['mean']
            scaling_factor = large_time / small_time
            size_ratio = large_size / small_size
            
            print(f"\nScaling Analysis:")
            print(f"  Size ratio: {size_ratio:.1f}x")
            print(f"  Time ratio: {scaling_factor:.1f}x")
            print(f"  Scaling efficiency: {size_ratio / scaling_factor:.2f}")
            
            # Time should not scale worse than linearly with size
            assert scaling_factor <= size_ratio * 1.5, "Performance should scale better than linear"
    
    def test_memory_efficiency_structured_context(self, structured_context_data, mock_llm):
        """Test memory efficiency of structured context processing."""
        import psutil
        import os
        
        structured_service = ContextManager()
        process = psutil.Process(os.getpid())
        
        # Measure memory before processing
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process context multiple times to test for memory leaks
        for _ in range(10):
            result = structured_service.assemble_context(
                structured_context=structured_context_data,
                agent_type="writer",
                compose_phase=ComposePhase.CHAPTER_WRITING
            )
            
            # Verify result is reasonable size
            assert len(result.system_prompt) > 0
            assert len(result.user_message) > 0
        
        # Measure memory after processing
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        print(f"\n{'='*60}")
        print("MEMORY EFFICIENCY TEST")
        print(f"{'='*60}")
        print(f"Memory before: {memory_before:.2f} MB")
        print(f"Memory after: {memory_after:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100.0, "Memory increase should be less than 100MB"
    
    def test_concurrent_context_processing(self, structured_context_data, mock_llm):
        """Test performance under concurrent context processing."""
        import threading
        import queue
        
        structured_service = ContextManager()
        results_queue = queue.Queue()
        
        def process_context_worker():
            """Worker function for concurrent processing."""
            start_time = time.perf_counter()
            try:
                result = structured_service.assemble_context(
                    structured_context=structured_context_data,
                    agent_type="writer",
                    compose_phase=ComposePhase.CHAPTER_WRITING
                )
                end_time = time.perf_counter()
                results_queue.put({
                    "success": True,
                    "duration": end_time - start_time,
                    "result_size": len(result.system_prompt) + len(result.user_message)
                })
            except Exception as e:
                end_time = time.perf_counter()
                results_queue.put({
                    "success": False,
                    "duration": end_time - start_time,
                    "error": str(e)
                })
        
        # Run concurrent processing
        num_threads = 5
        threads = []
        
        start_time = time.perf_counter()
        
        for _ in range(num_threads):
            thread = threading.Thread(target=process_context_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Analyze results
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        print(f"\n{'='*60}")
        print("CONCURRENT PROCESSING TEST")
        print(f"{'='*60}")
        print(f"Threads: {num_threads}")
        print(f"Total time: {total_time:.4f}s")
        print(f"Successful: {len(successful_results)}")
        print(f"Failed: {len(failed_results)}")
        
        if successful_results:
            durations = [r["duration"] for r in successful_results]
            print(f"Average duration: {statistics.mean(durations):.4f}s")
            print(f"Max duration: {max(durations):.4f}s")
            print(f"Min duration: {min(durations):.4f}s")
        
        # All requests should succeed
        assert len(failed_results) == 0, "All concurrent requests should succeed"
        
        # Total time should be reasonable (not much longer than sequential)
        assert total_time < 60.0, "Concurrent processing should complete within 60 seconds"
        
        # Individual requests should complete within reasonable time
        if successful_results:
            max_duration = max(r["duration"] for r in successful_results)
            assert max_duration < 30.0, "Individual requests should complete within 30 seconds"
    
    def test_context_optimization_effectiveness(self, structured_context_data, mock_llm):
        """Test effectiveness of context optimization/summarization."""
        structured_service = ContextManager()
        
        # Process context with different optimization settings
        def process_with_optimization(max_tokens: int):
            return structured_service.assemble_context(
                structured_context=structured_context_data,
                agent_type="writer",
                compose_phase=ComposePhase.CHAPTER_WRITING,
                max_context_tokens=max_tokens
            )
        
        # Test different token limits
        token_limits = [1000, 2000, 4000, 8000]
        results = {}
        
        for limit in token_limits:
            result = process_with_optimization(limit)
            
            # Estimate token count (rough approximation)
            total_content = result.system_prompt + result.user_message
            estimated_tokens = len(total_content.split()) * 1.3  # Rough token estimation
            
            results[limit] = {
                "estimated_tokens": estimated_tokens,
                "content_length": len(total_content),
                "system_prompt_length": len(result.system_prompt),
                "user_message_length": len(result.user_message)
            }
        
        print(f"\n{'='*60}")
        print("CONTEXT OPTIMIZATION EFFECTIVENESS")
        print(f"{'='*60}")
        for limit, result in results.items():
            print(f"Token limit {limit}:")
            print(f"  Estimated tokens: {result['estimated_tokens']:.0f}")
            print(f"  Content length: {result['content_length']} chars")
            print(f"  Within limit: {'✅' if result['estimated_tokens'] <= limit else '❌'}")
        
        # Verify optimization works
        for limit, result in results.items():
            # Content should generally stay within token limits (with some tolerance)
            assert result['estimated_tokens'] <= limit * 1.2, f"Content should stay near {limit} token limit"
        
        # Smaller limits should produce shorter content
        if len(token_limits) >= 2:
            small_limit = min(token_limits)
            large_limit = max(token_limits)
            
            small_content = results[small_limit]['content_length']
            large_content = results[large_limit]['content_length']
            
            assert small_content <= large_content, "Smaller token limits should produce shorter content"
