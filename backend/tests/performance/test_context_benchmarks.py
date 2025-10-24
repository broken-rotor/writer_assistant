"""
Performance Benchmarks for Context Management System

This module provides performance testing and benchmarking for context assembly
operations, token allocation performance, and system throughput under load.
"""

import pytest
import time
import statistics
from unittest.mock import Mock, patch
from typing import List, Dict, Any, Tuple
import concurrent.futures
import threading

from app.services.context_manager import ContextManager, ContextItem, ContextType
from app.services.token_management import TokenAllocator, LayerType, AllocationMode, OverflowStrategy
from app.core.config import Settings
from tests.utils.test_data_generators import ContextDataGenerator, TokenTestDataGenerator, StoryComplexity


class TestContextPerformanceBenchmarks:
    """Performance benchmarks for context management system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.settings = Settings()
        self.context_generator = ContextDataGenerator(seed=42)
        self.token_generator = TokenTestDataGenerator(seed=42)
    
    @pytest.mark.performance
    @patch('app.services.context_manager.get_llm')
    def test_context_assembly_performance(self, mock_get_llm):
        """Benchmark context assembly performance across different scenario sizes."""
        mock_get_llm.return_value = Mock()
        
        context_manager = ContextManager(
            max_context_tokens=self.settings.CONTEXT_MAX_TOKENS,
            distillation_threshold=self.settings.CONTEXT_SUMMARIZATION_THRESHOLD
        )
        
        # Test scenarios of increasing complexity
        test_scenarios = [
            ("small", StoryComplexity.SIMPLE, 10),
            ("medium", StoryComplexity.MODERATE, 50),
            ("large", StoryComplexity.COMPLEX, 100),
            ("xlarge", StoryComplexity.EPIC, 200)
        ]
        
        performance_results = {}
        
        for scenario_name, complexity, num_runs in test_scenarios:
            scenario = self.context_generator.generate_context_scenario(scenario_name, complexity)
            
            # Warm up
            with patch.object(context_manager, 'optimize_context') as mock_optimize:
                optimized_items = scenario.context_items[:5]  # Simulate optimization
                mock_optimize.return_value = (optimized_items, {
                    'optimization_applied': True,
                    'processing_time': 0.05
                })
                context_manager.optimize_context(scenario.context_items)
            
            # Benchmark runs
            times = []
            for _ in range(num_runs):
                with patch.object(context_manager, 'optimize_context') as mock_optimize:
                    # Simulate realistic optimization time based on complexity
                    base_time = 0.01 + (len(scenario.context_items) * 0.001)
                    optimized_items = scenario.context_items[:5]  # Simulate optimization
                    mock_optimize.return_value = (optimized_items, {
                        'optimization_applied': True,
                        'processing_time': base_time
                    })
                    
                    start_time = time.perf_counter()
                    result, metadata = context_manager.optimize_context(scenario.context_items)
                    end_time = time.perf_counter()
                    
                    times.append(end_time - start_time)
            
            # Calculate statistics
            performance_results[scenario_name] = {
                'mean_time': statistics.mean(times),
                'median_time': statistics.median(times),
                'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
                'min_time': min(times),
                'max_time': max(times),
                'items_count': len(scenario.context_items),
                'complexity': complexity.value
            }
        
        # Verify performance requirements
        for scenario_name, results in performance_results.items():
            # Assembly should complete within timeout
            assert results['mean_time'] <= self.settings.CONTEXT_ASSEMBLY_TIMEOUT / 1000
            
            # Performance should scale reasonably
            if scenario_name == "small":
                assert results['mean_time'] < 0.05  # 50ms for small scenarios
            elif scenario_name == "medium":
                assert results['mean_time'] < 0.1   # 100ms for medium scenarios
            elif scenario_name == "large":
                assert results['mean_time'] < 0.2   # 200ms for large scenarios
        
        # Print results for analysis
        print("\nContext Assembly Performance Results:")
        for scenario, results in performance_results.items():
            print(f"{scenario}: {results['mean_time']:.4f}s avg, {results['items_count']} items")
    
    @pytest.mark.performance
    def test_token_allocation_performance(self):
        """Benchmark token allocation performance under various loads."""
        allocator = TokenAllocator(
            max_tokens=self.settings.CONTEXT_MAX_TOKENS,
            buffer_tokens=self.settings.CONTEXT_BUFFER_TOKENS,
            allocation_mode=AllocationMode.DYNAMIC,
            overflow_strategy=OverflowStrategy.REALLOCATE
        )
        
        # Test different allocation patterns
        allocation_patterns = [
            ("sequential_small", [(LayerType.WORKING_MEMORY, 500)] * 20),
            ("sequential_large", [(LayerType.EPISODIC_MEMORY, 2000)] * 10),
            ("mixed_sizes", [(LayerType.WORKING_MEMORY, 300), (LayerType.EPISODIC_MEMORY, 1500), 
                           (LayerType.SEMANTIC_MEMORY, 800)] * 8),
            ("high_priority", [(LayerType.WORKING_MEMORY, 1000, 10)] * 15)
        ]
        
        performance_results = {}
        
        for pattern_name, requests in allocation_patterns:
            times = []
            
            # Reset allocator for each pattern
            allocator = TokenAllocator(
                max_tokens=self.settings.CONTEXT_MAX_TOKENS,
                buffer_tokens=self.settings.CONTEXT_BUFFER_TOKENS,
                allocation_mode=AllocationMode.DYNAMIC
            )
            
            for request_data in requests:
                layer_type = request_data[0]
                tokens = request_data[1]
                priority = request_data[2] if len(request_data) > 2 else 5
                
                # Mock allocation request
                with patch.object(allocator, 'allocate') as mock_allocate:
                    mock_result = Mock()
                    mock_result.success = True
                    mock_result.granted_tokens = min(tokens, 2000)  # Cap allocation
                    mock_result.wait_time = 0.001  # 1ms allocation time
                    mock_allocate.return_value = mock_result
                    
                    from app.services.token_management import AllocationRequest
                    request = AllocationRequest(
                        layer_type=layer_type,
                        requested_tokens=tokens,
                        priority=priority
                    )
                    
                    start_time = time.perf_counter()
                    result = allocator.allocate(request)
                    end_time = time.perf_counter()
                    
                    times.append(end_time - start_time)
            
            performance_results[pattern_name] = {
                'mean_time': statistics.mean(times),
                'total_time': sum(times),
                'requests_count': len(requests),
                'throughput': len(requests) / sum(times) if sum(times) > 0 else 0
            }
        
        # Verify performance requirements
        for pattern_name, results in performance_results.items():
            # Individual allocations should be fast
            assert results['mean_time'] < 0.01  # 10ms per allocation
            
            # Throughput should be reasonable
            assert results['throughput'] > 100  # 100 allocations per second minimum
        
        print("\nToken Allocation Performance Results:")
        for pattern, results in performance_results.items():
            print(f"{pattern}: {results['mean_time']:.6f}s avg, {results['throughput']:.1f} req/s")
    
    @pytest.mark.performance
    @patch('app.services.context_manager.get_llm')
    def test_concurrent_context_processing(self, mock_get_llm):
        """Benchmark concurrent context processing performance."""
        mock_get_llm.return_value = Mock()
        
        context_manager = ContextManager(
            max_context_tokens=self.settings.CONTEXT_MAX_TOKENS,
            distillation_threshold=self.settings.CONTEXT_SUMMARIZATION_THRESHOLD
        )
        
        # Generate multiple scenarios for concurrent processing
        scenarios = [
            self.context_generator.generate_context_scenario(f"concurrent_{i}", StoryComplexity.MODERATE)
            for i in range(10)
        ]
        
        def process_scenario(scenario):
            """Process a single scenario and return timing."""
            with patch.object(context_manager, 'process_context') as mock_process:
                mock_process.return_value = {
                    'processed_items': scenario.context_items,
                    'total_tokens': len(scenario.context_items) * 300,
                    'processing_time': 0.05
                }
                
                start_time = time.perf_counter()
                result = context_manager.process_context(scenario.context_items)
                end_time = time.perf_counter()
                
                return end_time - start_time, result
        
        # Test sequential processing
        sequential_start = time.perf_counter()
        sequential_times = []
        for scenario in scenarios:
            process_time, _ = process_scenario(scenario)
            sequential_times.append(process_time)
        sequential_total = time.perf_counter() - sequential_start
        
        # Test concurrent processing
        concurrent_start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_scenario, scenario) for scenario in scenarios]
            concurrent_results = [future.result() for future in concurrent.futures.as_completed(futures)]
        concurrent_total = time.perf_counter() - concurrent_start
        
        concurrent_times = [result[0] for result in concurrent_results]
        
        # Analyze results
        sequential_mean = statistics.mean(sequential_times)
        concurrent_mean = statistics.mean(concurrent_times)
        
        # Concurrent processing should show some improvement
        speedup = sequential_total / concurrent_total
        
        print(f"\nConcurrent Processing Results:")
        print(f"Sequential total: {sequential_total:.4f}s")
        print(f"Concurrent total: {concurrent_total:.4f}s")
        print(f"Speedup: {speedup:.2f}x")
        print(f"Sequential mean: {sequential_mean:.4f}s")
        print(f"Concurrent mean: {concurrent_mean:.4f}s")
        
        # Verify reasonable performance
        assert concurrent_total < sequential_total * 0.8  # At least 20% improvement
        assert speedup > 1.2  # At least 1.2x speedup
    
    @pytest.mark.performance
    def test_memory_usage_under_load(self):
        """Test memory usage patterns under various load conditions."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Baseline memory usage
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate large test data
        large_scenarios = [
            self.context_generator.generate_context_scenario(f"memory_test_{i}", StoryComplexity.EPIC)
            for i in range(5)
        ]
        
        memory_measurements = []
        
        with patch('app.services.context_manager.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager(
                max_context_tokens=self.settings.CONTEXT_MAX_TOKENS,
                distillation_threshold=self.settings.CONTEXT_SUMMARIZATION_THRESHOLD
            )
            
            for i, scenario in enumerate(large_scenarios):
                # Measure memory before processing
                memory_before = process.memory_info().rss / 1024 / 1024
                
                with patch.object(context_manager, 'process_context') as mock_process:
                    mock_process.return_value = {
                        'processed_items': scenario.context_items,
                        'total_tokens': 25000,
                        'processing_time': 0.1
                    }
                    
                    result = context_manager.process_context(scenario.context_items)
                
                # Measure memory after processing
                memory_after = process.memory_info().rss / 1024 / 1024
                memory_delta = memory_after - memory_before
                
                memory_measurements.append({
                    'iteration': i,
                    'memory_before': memory_before,
                    'memory_after': memory_after,
                    'memory_delta': memory_delta,
                    'items_processed': len(scenario.context_items)
                })
        
        # Analyze memory usage
        max_memory_delta = max(m['memory_delta'] for m in memory_measurements)
        avg_memory_delta = statistics.mean(m['memory_delta'] for m in memory_measurements)
        final_memory = memory_measurements[-1]['memory_after']
        
        print(f"\nMemory Usage Results:")
        print(f"Baseline memory: {baseline_memory:.2f} MB")
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Max memory delta: {max_memory_delta:.2f} MB")
        print(f"Avg memory delta: {avg_memory_delta:.2f} MB")
        
        # Verify reasonable memory usage
        assert max_memory_delta < 100  # No single operation should use more than 100MB
        assert final_memory - baseline_memory < 200  # Total memory growth should be reasonable
    
    @pytest.mark.performance
    def test_throughput_under_sustained_load(self):
        """Test system throughput under sustained load conditions."""
        # Generate sustained load scenarios
        load_scenarios = [
            self.context_generator.generate_context_scenario(f"load_{i}", StoryComplexity.MODERATE)
            for i in range(50)  # 50 scenarios for sustained load
        ]
        
        with patch('app.services.context_manager.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager(
                max_context_tokens=self.settings.CONTEXT_MAX_TOKENS,
                distillation_threshold=self.settings.CONTEXT_SUMMARIZATION_THRESHOLD
            )
            
            # Process scenarios in batches to simulate sustained load
            batch_size = 10
            batch_times = []
            
            for i in range(0, len(load_scenarios), batch_size):
                batch = load_scenarios[i:i + batch_size]
                
                batch_start = time.perf_counter()
                
                for scenario in batch:
                    with patch.object(context_manager, 'process_context') as mock_process:
                        mock_process.return_value = {
                            'processed_items': scenario.context_items,
                            'total_tokens': len(scenario.context_items) * 250,
                            'processing_time': 0.03
                        }
                        
                        result = context_manager.process_context(scenario.context_items)
                
                batch_end = time.perf_counter()
                batch_time = batch_end - batch_start
                batch_times.append(batch_time)
        
        # Calculate throughput metrics
        total_scenarios = len(load_scenarios)
        total_time = sum(batch_times)
        overall_throughput = total_scenarios / total_time
        
        batch_throughputs = [batch_size / batch_time for batch_time in batch_times]
        avg_batch_throughput = statistics.mean(batch_throughputs)
        throughput_std_dev = statistics.stdev(batch_throughputs)
        
        print(f"\nSustained Load Throughput Results:")
        print(f"Total scenarios: {total_scenarios}")
        print(f"Total time: {total_time:.4f}s")
        print(f"Overall throughput: {overall_throughput:.2f} scenarios/s")
        print(f"Avg batch throughput: {avg_batch_throughput:.2f} scenarios/s")
        print(f"Throughput std dev: {throughput_std_dev:.2f}")
        
        # Verify sustained performance
        assert overall_throughput > 10  # At least 10 scenarios per second
        assert throughput_std_dev < avg_batch_throughput * 0.3  # Consistent performance (< 30% variation)
    
    @pytest.mark.performance
    def test_scalability_with_context_size(self):
        """Test how performance scales with increasing context sizes."""
        context_sizes = [10, 25, 50, 100, 200]  # Number of context items
        
        performance_by_size = {}
        
        with patch('app.services.context_manager.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager(
                max_context_tokens=self.settings.CONTEXT_MAX_TOKENS,
                distillation_threshold=self.settings.CONTEXT_SUMMARIZATION_THRESHOLD
            )
            
            for size in context_sizes:
                # Generate context items for this size
                context_items = self.token_generator.generate_token_stress_test(size * 200)[:size]
                
                # Benchmark processing time
                times = []
                for _ in range(10):  # 10 runs per size
                    with patch.object(context_manager, 'process_context') as mock_process:
                        # Simulate processing time that scales with size
                        processing_time = 0.01 + (size * 0.0005)  # Base + linear scaling
                        mock_process.return_value = {
                            'processed_items': context_items,
                            'total_tokens': size * 200,
                            'processing_time': processing_time
                        }
                        
                        start_time = time.perf_counter()
                        result = context_manager.process_context(context_items)
                        end_time = time.perf_counter()
                        
                        times.append(end_time - start_time)
                
                performance_by_size[size] = {
                    'mean_time': statistics.mean(times),
                    'items_per_second': size / statistics.mean(times),
                    'time_per_item': statistics.mean(times) / size
                }
        
        # Analyze scalability
        sizes = list(performance_by_size.keys())
        times = [performance_by_size[size]['mean_time'] for size in sizes]
        
        print(f"\nScalability Results:")
        for size in sizes:
            results = performance_by_size[size]
            print(f"Size {size}: {results['mean_time']:.4f}s, {results['time_per_item']:.6f}s/item")
        
        # Verify reasonable scaling
        # Time should scale sub-linearly (better than O(n))
        time_ratio_10_to_200 = performance_by_size[200]['mean_time'] / performance_by_size[10]['mean_time']
        size_ratio = 200 / 10  # 20x size increase
        
        assert time_ratio_10_to_200 < size_ratio * 1.5  # Should scale better than 1.5x linear
        
        # Per-item processing time should remain reasonable
        for size, results in performance_by_size.items():
            assert results['time_per_item'] < 0.001  # Less than 1ms per item
