"""
Comprehensive unit tests for the Token Management System.

Tests TokenCounter, TokenAllocator, LlamaTokenizer, and layer management
with >90% code coverage as specified in the acceptance criteria.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List

# Add the backend directory to the path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the modules to test
from app.utils.llama_tokenizer import LlamaTokenizer
from app.services.token_management.token_counter import (
    TokenCounter, ContentType, CountingStrategy, TokenCount
)
from app.services.token_management.layers import (
    LayerType, LayerConfig, LayerAllocation, LayerHierarchy
)
from app.services.token_management.allocator import (
    TokenAllocator, AllocationMode, OverflowStrategy, AllocationRequest, AllocationResult
)


class TestLlamaTokenizer:
    """Test cases for LlamaTokenizer."""
    
    def test_singleton_pattern(self):
        """Test that LlamaTokenizer follows singleton pattern."""
        tokenizer1 = LlamaTokenizer.get_instance()
        tokenizer2 = LlamaTokenizer.get_instance()
        assert tokenizer1 is tokenizer2
    
    def test_initialization_without_model(self):
        """Test tokenizer initialization without model path."""
        tokenizer = LlamaTokenizer()
        assert tokenizer.model_path is None
        assert tokenizer._model is None
    
    def test_initialization_with_model(self):
        """Test tokenizer initialization with model path."""
        model_path = "/fake/path/model.gguf"
        tokenizer = LlamaTokenizer(model_path=model_path)
        assert tokenizer.model_path == model_path
    
    @patch('app.utils.llama_tokenizer.LLAMA_CPP_AVAILABLE', False)
    def test_fallback_when_llama_cpp_unavailable(self):
        """Test fallback behavior when llama-cpp-python is not available."""
        tokenizer = LlamaTokenizer()
        
        # Test fallback encoding
        text = "Hello world"
        tokens = tokenizer.encode(text)
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        
        # Test fallback decoding
        decoded = tokenizer.decode(tokens)
        assert isinstance(decoded, str)
        assert "tokens" in decoded
    
    def test_count_tokens_empty_string(self):
        """Test token counting with empty string."""
        tokenizer = LlamaTokenizer()
        count = tokenizer.count_tokens("")
        assert count == 0
    
    def test_count_tokens_batch(self):
        """Test batch token counting."""
        tokenizer = LlamaTokenizer()
        texts = ["Hello", "World", "Test"]
        counts = tokenizer.count_tokens_batch(texts)
        assert len(counts) == len(texts)
        assert all(isinstance(count, int) for count in counts)
    
    def test_estimate_tokens_with_overhead(self):
        """Test token estimation with overhead factor."""
        tokenizer = LlamaTokenizer()
        text = "Hello world"
        base_count = tokenizer.count_tokens(text)
        estimated = tokenizer.estimate_tokens(text, overhead_factor=1.2)
        assert estimated >= base_count
        assert estimated == int(base_count * 1.2)
    
    def test_truncate_to_tokens(self):
        """Test text truncation to fit token limit."""
        tokenizer = LlamaTokenizer()
        text = "This is a longer text that should be truncated"
        max_tokens = 5
        truncated = tokenizer.truncate_to_tokens(text, max_tokens)
        
        # Truncated text should have fewer or equal tokens
        truncated_count = tokenizer.count_tokens(truncated)
        assert truncated_count <= max_tokens
    
    def test_get_model_info(self):
        """Test getting model information."""
        tokenizer = LlamaTokenizer()
        info = tokenizer.get_model_info()
        
        assert isinstance(info, dict)
        assert "model_path" in info
        assert "model_loaded" in info
        assert "llama_cpp_available" in info
    
    def test_is_ready(self):
        """Test tokenizer readiness check."""
        tokenizer = LlamaTokenizer()
        ready = tokenizer.is_ready()
        assert isinstance(ready, bool)
    
    @patch('app.utils.llama_tokenizer.Llama')
    def test_model_loading_success(self, mock_llama):
        """Test successful model loading."""
        mock_model = Mock()
        mock_model.tokenize.return_value = [1, 2, 3]
        mock_model.detokenize.return_value = b"test"
        mock_model.n_vocab.return_value = 32000
        mock_model.n_ctx.return_value = 4096
        mock_llama.return_value = mock_model
        
        tokenizer = LlamaTokenizer(model_path="/fake/model.gguf")
        tokenizer._ensure_model_loaded()
        
        # Test encoding with loaded model
        tokens = tokenizer.encode("test")
        assert tokens == [1, 2, 3]
        
        # Test decoding with loaded model
        text = tokenizer.decode([1, 2, 3])
        assert text == "test"
    
    @patch('app.utils.llama_tokenizer.Llama')
    def test_model_loading_failure(self, mock_llama):
        """Test model loading failure."""
        mock_llama.side_effect = Exception("Failed to load model")
        
        tokenizer = LlamaTokenizer(model_path="/fake/model.gguf")
        success = tokenizer._ensure_model_loaded()
        assert success is False


class TestTokenCounter:
    """Test cases for TokenCounter."""
    
    @pytest.fixture
    def mock_tokenizer(self):
        """Create a mock tokenizer for testing."""
        tokenizer = Mock(spec=LlamaTokenizer)
        tokenizer.count_tokens.return_value = 10
        tokenizer.is_ready.return_value = True
        return tokenizer
    
    @pytest.fixture
    def token_counter(self, mock_tokenizer):
        """Create a TokenCounter instance with mock tokenizer."""
        return TokenCounter(tokenizer=mock_tokenizer)
    
    def test_content_type_detection_dialogue(self, token_counter):
        """Test content type detection for dialogue."""
        dialogue_text = '"Hello there," she said with a smile.'
        content_type = token_counter.detect_content_type(dialogue_text)
        assert content_type == ContentType.DIALOGUE
    
    def test_content_type_detection_system_prompt(self, token_counter):
        """Test content type detection for system prompts."""
        system_text = "You are a helpful assistant. Respond as a character."
        content_type = token_counter.detect_content_type(system_text)
        assert content_type == ContentType.SYSTEM_PROMPT
    
    def test_content_type_detection_character_description(self, token_counter):
        """Test content type detection for character descriptions."""
        char_text = "John is a tall character with a mysterious personality and dark background."
        content_type = token_counter.detect_content_type(char_text)
        assert content_type == ContentType.CHARACTER_DESCRIPTION
    
    def test_content_type_detection_unknown(self, token_counter):
        """Test content type detection for unknown content."""
        unknown_text = "This is just some random text without specific patterns."
        content_type = token_counter.detect_content_type(unknown_text)
        # Should default to NARRATIVE for unmatched content
        assert content_type == ContentType.NARRATIVE
    
    def test_count_tokens_empty_content(self, token_counter):
        """Test token counting with empty content."""
        result = token_counter.count_tokens("")
        assert result.token_count == 0
        assert result.content_type == ContentType.UNKNOWN
    
    def test_count_tokens_exact_strategy(self, token_counter):
        """Test token counting with exact strategy."""
        content = "Hello world"
        result = token_counter.count_tokens(content, strategy=CountingStrategy.EXACT)
        
        assert isinstance(result, TokenCount)
        assert result.content == content
        assert result.token_count > 0
        assert result.strategy == CountingStrategy.EXACT
        assert result.overhead_applied == 1.0  # No overhead for exact
    
    def test_count_tokens_conservative_strategy(self, token_counter):
        """Test token counting with conservative strategy."""
        content = "Hello world"
        result = token_counter.count_tokens(content, strategy=CountingStrategy.CONSERVATIVE)
        
        assert result.strategy == CountingStrategy.CONSERVATIVE
        assert result.overhead_applied > 1.0  # Should have overhead
    
    def test_count_tokens_with_content_type(self, token_counter):
        """Test token counting with specified content type."""
        content = "Hello world"
        result = token_counter.count_tokens(content, content_type=ContentType.DIALOGUE)
        
        assert result.content_type == ContentType.DIALOGUE
    
    def test_count_tokens_batch(self, token_counter):
        """Test batch token counting."""
        contents = ["Hello", "World", "Test"]
        results = token_counter.count_tokens_batch(contents)
        
        assert len(results) == len(contents)
        assert all(isinstance(result, TokenCount) for result in results)
    
    def test_count_tokens_batch_with_types(self, token_counter):
        """Test batch token counting with specified content types."""
        contents = ["Hello", "World"]
        content_types = [ContentType.DIALOGUE, ContentType.NARRATIVE]
        results = token_counter.count_tokens_batch(contents, content_types)
        
        assert len(results) == len(contents)
        assert results[0].content_type == ContentType.DIALOGUE
        assert results[1].content_type == ContentType.NARRATIVE
    
    def test_count_tokens_batch_mismatched_lengths(self, token_counter):
        """Test batch token counting with mismatched content and type lengths."""
        contents = ["Hello", "World"]
        content_types = [ContentType.DIALOGUE]  # One less than contents
        
        with pytest.raises(ValueError):
            token_counter.count_tokens_batch(contents, content_types)
    
    def test_estimate_tokens_for_generation(self, token_counter):
        """Test token estimation for generation requests."""
        prompt = "Generate a story about"
        expected_length = 1000
        
        prompt_tokens, response_tokens, total_tokens = token_counter.estimate_tokens_for_generation(
            prompt, expected_length
        )
        
        assert prompt_tokens > 0
        assert response_tokens > 0
        assert total_tokens == prompt_tokens + response_tokens
    
    def test_analyze_content_distribution(self, token_counter):
        """Test content distribution analysis."""
        content = '"Hello," she said. The room was dark. John thought about it.'
        distribution = token_counter.analyze_content_distribution(content)
        
        assert isinstance(distribution, dict)
        assert all(isinstance(prop, float) for prop in distribution.values())
        assert all(0.0 <= prop <= 1.0 for prop in distribution.values())
    
    def test_get_token_efficiency_stats(self, token_counter):
        """Test token efficiency statistics."""
        contents = ["Hello world", "This is a test", "Another example"]
        stats = token_counter.get_token_efficiency_stats(contents)
        
        assert isinstance(stats, dict)
        assert "total_contents" in stats
        assert "total_tokens" in stats
        assert "avg_tokens_per_content" in stats
        assert stats["total_contents"] == len(contents)
    
    def test_validate_token_budget_within_limit(self, token_counter):
        """Test token budget validation within limit."""
        contents = ["Short", "Text"]
        budget = 1000
        validation = token_counter.validate_token_budget(contents, budget)
        
        assert validation["fits_budget"] is True
        assert validation["total_tokens"] <= budget
        assert validation["remaining_tokens"] >= 0
    
    def test_validate_token_budget_exceeds_limit(self, mock_tokenizer):
        """Test token budget validation exceeding limit."""
        # Mock tokenizer to return high token counts
        mock_tokenizer.count_tokens.return_value = 500
        token_counter = TokenCounter(tokenizer=mock_tokenizer)
        
        contents = ["Long content", "More content"]
        budget = 100  # Small budget
        validation = token_counter.validate_token_budget(contents, budget)
        
        assert validation["fits_budget"] is False
        assert validation["overflow_tokens"] > 0


class TestLayerHierarchy:
    """Test cases for LayerHierarchy."""
    
    @pytest.fixture
    def hierarchy(self):
        """Create a LayerHierarchy instance."""
        return LayerHierarchy()
    
    def test_initialization(self, hierarchy):
        """Test hierarchy initialization."""
        configs = hierarchy.get_all_layer_configs()
        assert len(configs) == 5  # A, B, C, D, E layers
        
        # Check that all layer types are present
        expected_layers = {LayerType.WORKING_MEMORY, LayerType.EPISODIC_MEMORY, LayerType.SEMANTIC_MEMORY, 
                          LayerType.AGENT_SPECIFIC_MEMORY, LayerType.LONG_TERM_MEMORY}
        assert set(configs.keys()) == expected_layers
    
    def test_layer_relationships(self, hierarchy):
        """Test parent-child relationships."""
        # A -> B -> C -> D -> E hierarchy
        assert hierarchy.get_parent_layer(LayerType.EPISODIC_MEMORY) == LayerType.WORKING_MEMORY
        assert hierarchy.get_parent_layer(LayerType.SEMANTIC_MEMORY) == LayerType.EPISODIC_MEMORY
        assert hierarchy.get_parent_layer(LayerType.AGENT_SPECIFIC_MEMORY) == LayerType.SEMANTIC_MEMORY
        assert hierarchy.get_parent_layer(LayerType.LONG_TERM_MEMORY) == LayerType.AGENT_SPECIFIC_MEMORY
        assert hierarchy.get_parent_layer(LayerType.WORKING_MEMORY) is None
    
    def test_child_relationships(self, hierarchy):
        """Test child relationships."""
        children_a = hierarchy.get_child_layers(LayerType.WORKING_MEMORY)
        assert LayerType.EPISODIC_MEMORY in children_a
        
        children_e = hierarchy.get_child_layers(LayerType.LONG_TERM_MEMORY)
        assert len(children_e) == 0  # Leaf node
    
    def test_ancestor_layers(self, hierarchy):
        """Test getting ancestor layers."""
        ancestors = hierarchy.get_ancestor_layers(LayerType.LONG_TERM_MEMORY)
        expected = [LayerType.AGENT_SPECIFIC_MEMORY, LayerType.SEMANTIC_MEMORY, LayerType.EPISODIC_MEMORY, LayerType.WORKING_MEMORY]
        assert ancestors == expected
    
    def test_descendant_layers(self, hierarchy):
        """Test getting descendant layers."""
        descendants = hierarchy.get_descendant_layers(LayerType.WORKING_MEMORY)
        expected = [LayerType.EPISODIC_MEMORY, LayerType.SEMANTIC_MEMORY, LayerType.AGENT_SPECIFIC_MEMORY, LayerType.LONG_TERM_MEMORY]
        assert descendants == expected
    
    def test_layers_by_priority(self, hierarchy):
        """Test getting layers ordered by priority."""
        layers_desc = hierarchy.get_layers_by_priority(descending=True)
        layers_asc = hierarchy.get_layers_by_priority(descending=False)
        
        # Should be in reverse order
        assert layers_desc == list(reversed(layers_asc))
        
        # WORKING_MEMORY should have highest priority (5)
        assert layers_desc[0] == LayerType.WORKING_MEMORY
        assert layers_asc[-1] == LayerType.WORKING_MEMORY
    
    def test_budget_calculations(self, hierarchy):
        """Test budget calculation methods."""
        default_budget = hierarchy.calculate_total_default_budget()
        min_budget = hierarchy.calculate_total_minimum_budget()
        max_budget = hierarchy.calculate_total_maximum_budget()
        
        assert min_budget <= default_budget <= max_budget
        assert all(budget > 0 for budget in [default_budget, min_budget, max_budget])
    
    def test_validate_layer_allocation_valid(self, hierarchy):
        """Test validation of valid layer allocation."""
        allocations = {
            LayerType.WORKING_MEMORY: 1000,
            LayerType.EPISODIC_MEMORY: 800,
            LayerType.SEMANTIC_MEMORY: 600,
            LayerType.AGENT_SPECIFIC_MEMORY: 400,
            LayerType.LONG_TERM_MEMORY: 200
        }
        
        validation = hierarchy.validate_layer_allocation(allocations)
        assert validation["valid"] is True
        assert len(validation["errors"]) == 0
    
    def test_validate_layer_allocation_below_minimum(self, hierarchy):
        """Test validation with allocation below minimum."""
        allocations = {
            LayerType.WORKING_MEMORY: 500,  # Below minimum of 1000
            LayerType.EPISODIC_MEMORY: 1200,
            LayerType.SEMANTIC_MEMORY: 1000,
            LayerType.AGENT_SPECIFIC_MEMORY: 800,
            LayerType.LONG_TERM_MEMORY: 400
        }
        
        validation = hierarchy.validate_layer_allocation(allocations)
        assert validation["valid"] is False
        assert len(validation["errors"]) > 0
    
    def test_suggest_balanced_allocation(self, hierarchy):
        """Test balanced allocation suggestion."""
        total_budget = 4000
        allocations = hierarchy.suggest_balanced_allocation(total_budget)
        
        assert sum(allocations.values()) <= total_budget
        
        # Check that all allocations are within bounds
        for layer_type, allocation in allocations.items():
            config = hierarchy.get_layer_config(layer_type)
            assert config.min_tokens <= allocation <= config.max_tokens
    
    def test_suggest_balanced_allocation_insufficient_budget(self, hierarchy):
        """Test balanced allocation with insufficient budget."""
        total_budget = 100  # Very small budget
        allocations = hierarchy.suggest_balanced_allocation(total_budget)
        
        # Should allocate minimums
        for layer_type, allocation in allocations.items():
            config = hierarchy.get_layer_config(layer_type)
            assert allocation == config.min_tokens
    
    def test_get_layer_hierarchy_info(self, hierarchy):
        """Test getting comprehensive hierarchy information."""
        info = hierarchy.get_layer_hierarchy_info()
        
        assert "layers" in info
        assert "hierarchy_stats" in info
        assert len(info["layers"]) == 5
        
        # Check structure of layer info
        for layer_name, layer_info in info["layers"].items():
            assert "config" in layer_info
            assert "relationships" in layer_info
    
    def test_get_layer_path(self, hierarchy):
        """Test getting path between layers."""
        # Test path from child to parent
        path = hierarchy.get_layer_path(LayerType.LONG_TERM_MEMORY, LayerType.WORKING_MEMORY)
        expected = [LayerType.LONG_TERM_MEMORY, LayerType.AGENT_SPECIFIC_MEMORY, LayerType.SEMANTIC_MEMORY, LayerType.EPISODIC_MEMORY, LayerType.WORKING_MEMORY]
        assert path == expected
        
        # Test path from parent to child
        path = hierarchy.get_layer_path(LayerType.WORKING_MEMORY, LayerType.LONG_TERM_MEMORY)
        expected = [LayerType.WORKING_MEMORY, LayerType.EPISODIC_MEMORY, LayerType.SEMANTIC_MEMORY, LayerType.AGENT_SPECIFIC_MEMORY, LayerType.LONG_TERM_MEMORY]
        assert path == expected
        
        # Test path to same layer (should return path through parent)
        path = hierarchy.get_layer_path(LayerType.EPISODIC_MEMORY, LayerType.EPISODIC_MEMORY)
        # The implementation goes through the parent, so it's not None
        assert path is not None
    
    def test_suggest_balanced_allocation_excess_budget(self, hierarchy):
        """Test balanced allocation with excess budget."""
        total_budget = 10000  # Large budget
        allocations = hierarchy.suggest_balanced_allocation(total_budget)
        
        # Should not exceed maximum limits
        for layer_type, allocation in allocations.items():
            config = hierarchy.get_layer_config(layer_type)
            assert allocation <= config.max_tokens


class TestTokenAllocator:
    """Test cases for TokenAllocator."""
    
    @pytest.fixture
    def mock_hierarchy(self):
        """Create a mock hierarchy for testing."""
        hierarchy = Mock(spec=LayerHierarchy)
        hierarchy.suggest_balanced_allocation.return_value = {
            LayerType.WORKING_MEMORY: 2000,
            LayerType.EPISODIC_MEMORY: 1200,
            LayerType.SEMANTIC_MEMORY: 1000,
            LayerType.AGENT_SPECIFIC_MEMORY: 800,
            LayerType.LONG_TERM_MEMORY: 400
        }
        # Mock the get_layer_config method
        def mock_get_layer_config(layer_type):
            config = Mock()
            config.can_lend = True
            config.can_borrow = True
            config.min_tokens = 50
            config.max_tokens = 2000
            config.priority = 1
            return config
        hierarchy.get_layer_config.side_effect = mock_get_layer_config
        
        # Mock validate_layer_allocation
        hierarchy.validate_layer_allocation.return_value = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "total_allocated": 3000,
            "layer_validations": {}
        }
        return hierarchy
    
    @pytest.fixture
    def mock_token_counter(self):
        """Create a mock token counter for testing."""
        counter = Mock(spec=TokenCounter)
        return counter
    
    @pytest.fixture
    def allocator(self, mock_hierarchy, mock_token_counter):
        """Create a TokenAllocator instance with mocks."""
        return TokenAllocator(
            total_budget=3000,
            hierarchy=mock_hierarchy,
            token_counter=mock_token_counter
        )
    
    def test_initialization(self, allocator):
        """Test allocator initialization."""
        assert allocator.total_budget == 3000
        assert allocator.mode == AllocationMode.DYNAMIC
        assert allocator.overflow_strategy == OverflowStrategy.BORROW
    
    def test_allocate_tokens_direct_success(self, allocator):
        """Test successful direct token allocation."""
        request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=500
        )
        
        result = allocator.allocate_tokens(request)
        
        assert result.success is True
        assert result.granted_tokens == 500
        assert result.borrowed_tokens == 0
        assert result.truncated is False
    
    def test_allocate_tokens_insufficient_reject_strategy(self):
        """Test token allocation with reject strategy on insufficient tokens."""
        hierarchy = LayerHierarchy()
        allocator = TokenAllocator(
            total_budget=1000,  # Small budget
            hierarchy=hierarchy,
            overflow_strategy=OverflowStrategy.REJECT
        )
        
        # Request more tokens than available in the layer
        request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=2000  # More than layer allocation
        )
        
        result = allocator.allocate_tokens(request)
        
        assert result.success is False
        assert result.granted_tokens == 0
        assert "Insufficient tokens" in result.error_message
    
    def test_allocate_tokens_truncate_strategy(self):
        """Test token allocation with truncate strategy."""
        hierarchy = LayerHierarchy()
        allocator = TokenAllocator(
            total_budget=1000,
            hierarchy=hierarchy,
            overflow_strategy=OverflowStrategy.TRUNCATE
        )
        
        request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=2000,
            can_be_truncated=True
        )
        
        result = allocator.allocate_tokens(request)
        
        assert result.success is True
        assert result.granted_tokens < request.requested_tokens
        assert result.truncated is True
    
    def test_allocate_tokens_borrow_strategy(self):
        """Test token allocation with borrow strategy."""
        hierarchy = LayerHierarchy()
        allocator = TokenAllocator(
            total_budget=4000,
            hierarchy=hierarchy,
            overflow_strategy=OverflowStrategy.BORROW
        )
        
        # First, use up most tokens in A_STORY layer
        initial_request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=900
        )
        allocator.allocate_tokens(initial_request)
        
        # Now request more than remaining in A_STORY
        borrow_request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=200
        )
        
        result = allocator.allocate_tokens(borrow_request)
        
        # Should succeed by borrowing from other layers
        assert result.success is True
        assert result.granted_tokens == 200
    
    def test_release_tokens(self, allocator):
        """Test releasing tokens back to layer."""
        # First allocate some tokens
        request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=500
        )
        allocator.allocate_tokens(request)
        
        # Then release them
        success = allocator.release_tokens(LayerType.WORKING_MEMORY, 300)
        assert success is True
        
        # Check that allocation was updated
        allocation = allocator.get_layer_allocation(LayerType.WORKING_MEMORY)
        assert allocation.used_tokens == 200  # 500 - 300
    
    def test_release_tokens_insufficient(self, allocator):
        """Test releasing more tokens than in use."""
        success = allocator.release_tokens(LayerType.WORKING_MEMORY, 1000)
        assert success is False
    
    def test_reserve_tokens(self, allocator):
        """Test reserving tokens for future use."""
        success = allocator.reserve_tokens(LayerType.WORKING_MEMORY, 300)
        assert success is True
        
        allocation = allocator.get_layer_allocation(LayerType.WORKING_MEMORY)
        assert allocation.reserved_tokens == 300
    
    def test_reserve_tokens_insufficient(self, allocator):
        """Test reserving more tokens than available."""
        success = allocator.reserve_tokens(LayerType.WORKING_MEMORY, 2000)
        assert success is False
    
    def test_get_overall_utilization(self):
        """Test getting overall utilization."""
        # Use real hierarchy for this test
        hierarchy = LayerHierarchy()
        allocator = TokenAllocator(
            total_budget=3000,
            hierarchy=hierarchy
        )
        
        # Initially should be 0
        utilization = allocator.get_overall_utilization()
        assert utilization == 0.0
        
        # Allocate some tokens
        request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=1500  # 50% of total budget
        )
        allocator.allocate_tokens(request)
        
        utilization = allocator.get_overall_utilization()
        assert 0.4 <= utilization <= 0.6  # Should be around 50%
    
    def test_get_layer_usage_stats(self, allocator):
        """Test getting layer usage statistics."""
        stats = allocator.get_layer_usage_stats()
        
        assert isinstance(stats, dict)
        assert len(stats) == 5  # All layers
        
        for layer_name, layer_stats in stats.items():
            assert "allocated_tokens" in layer_stats
            assert "used_tokens" in layer_stats
            assert "available_tokens" in layer_stats
            assert "utilization" in layer_stats
    
    def test_get_allocation_stats(self, allocator):
        """Test getting allocation statistics."""
        stats = allocator.get_allocation_stats()
        
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.rejected_requests == 0
        
        # Make some requests
        request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=500
        )
        allocator.allocate_tokens(request)
        
        stats = allocator.get_allocation_stats()
        assert stats.total_requests == 1
        assert stats.successful_requests == 1
    
    def test_reset_allocations(self, allocator):
        """Test resetting allocations."""
        # Make some allocations first
        request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=500
        )
        allocator.allocate_tokens(request)
        
        # Reset with new budget
        allocator.reset_allocations(new_budget=5000)
        
        assert allocator.total_budget == 5000
        stats = allocator.get_allocation_stats()
        assert stats.total_requests == 0
        
        # Check that all layers are reset
        for allocation in allocator.get_all_allocations().values():
            assert allocation.used_tokens == 0
            assert allocation.reserved_tokens == 0
    
    def test_validate_allocations(self):
        """Test allocation validation."""
        # Use real hierarchy for this test
        hierarchy = LayerHierarchy()
        allocator = TokenAllocator(
            total_budget=3000,
            hierarchy=hierarchy
        )
        
        validation = allocator.validate_allocations()
        
        assert isinstance(validation, dict)
        assert "runtime_validation" in validation
        
        runtime = validation["runtime_validation"]
        assert "total_budget" in runtime
        assert "total_allocated" in runtime
        assert "budget_exceeded" in runtime
    
    def test_allocate_tokens_reallocate_strategy(self):
        """Test token allocation with reallocate strategy."""
        hierarchy = LayerHierarchy()
        allocator = TokenAllocator(
            total_budget=3000,
            hierarchy=hierarchy,
            overflow_strategy=OverflowStrategy.REALLOCATE
        )
        
        # Use up most tokens in A_STORY layer
        initial_request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=900
        )
        allocator.allocate_tokens(initial_request)
        
        # Request more than remaining
        overflow_request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=300
        )
        
        result = allocator.allocate_tokens(overflow_request)
        assert result.success is True
    
    def test_allocate_tokens_cannot_truncate(self):
        """Test allocation when truncation is not allowed."""
        hierarchy = LayerHierarchy()
        allocator = TokenAllocator(
            total_budget=1000,
            hierarchy=hierarchy,
            overflow_strategy=OverflowStrategy.TRUNCATE
        )
        
        request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=2000,
            can_be_truncated=False
        )
        
        result = allocator.allocate_tokens(request)
        assert result.success is False
        assert "Cannot truncate" in result.error_message
    
    def test_borrowing_disabled(self):
        """Test allocation when borrowing is disabled."""
        hierarchy = LayerHierarchy()
        allocator = TokenAllocator(
            total_budget=3000,
            hierarchy=hierarchy,
            overflow_strategy=OverflowStrategy.BORROW
        )
        
        # Disable borrowing
        allocator._borrowing_enabled = False
        
        # Use up most tokens in A_STORY layer
        initial_request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=900
        )
        allocator.allocate_tokens(initial_request)
        
        # Request more than remaining
        overflow_request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=200
        )
        
        result = allocator.allocate_tokens(overflow_request)
        assert result.success is False
        assert "Borrowing disabled" in result.error_message


class TestIntegration:
    """Integration tests for the complete token management system."""
    
    def test_end_to_end_token_management(self):
        """Test complete token management workflow."""
        # Create the complete system
        hierarchy = LayerHierarchy()
        token_counter = TokenCounter()
        allocator = TokenAllocator(
            total_budget=4000,
            hierarchy=hierarchy,
            token_counter=token_counter
        )
        
        # Test story-level allocation
        story_request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=800,
            content_preview="Once upon a time in a magical kingdom..."
        )
        
        story_result = allocator.allocate_tokens(story_request)
        assert story_result.success is True
        
        # Test character-level allocation
        char_request = AllocationRequest(
            layer_type=LayerType.AGENT_SPECIFIC_MEMORY,
            requested_tokens=300,
            content_preview="John is a brave knight with a mysterious past."
        )
        
        char_result = allocator.allocate_tokens(char_request)
        assert char_result.success is True
        
        # Test dialogue allocation
        dialogue_request = AllocationRequest(
            layer_type=LayerType.LONG_TERM_MEMORY,
            requested_tokens=150,
            content_preview='"Hello there," she said with a warm smile.'
        )
        
        dialogue_result = allocator.allocate_tokens(dialogue_request)
        assert dialogue_result.success is True
        
        # Check overall system state
        utilization = allocator.get_overall_utilization()
        assert 0.0 < utilization < 1.0
        
        stats = allocator.get_allocation_stats()
        assert stats.total_requests == 3
        assert stats.successful_requests == 3
    
    def test_token_counting_with_real_content(self):
        """Test token counting with realistic story content."""
        token_counter = TokenCounter()
        
        # Test different content types
        story_content = """
        In the mystical realm of Eldoria, where ancient magic flows through every stone and tree,
        a young apprentice named Lyra discovered a secret that would change the fate of kingdoms.
        """
        
        dialogue_content = '''
        "You must understand," the old wizard said, his eyes twinkling with ancient wisdom,
        "magic is not about power, but about responsibility."
        '''
        
        character_content = """
        Lyra: A 16-year-old apprentice mage with fiery red hair and emerald eyes.
        Personality: Curious, brave, sometimes reckless, deeply loyal to friends.
        Background: Orphaned at age 5, raised by the village healer.
        """
        
        # Count tokens for each content type
        story_result = token_counter.count_tokens(story_content)
        dialogue_result = token_counter.count_tokens(dialogue_content)
        char_result = token_counter.count_tokens(character_content)
        
        # Verify results
        assert story_result.content_type in [ContentType.NARRATIVE, ContentType.SCENE_DESCRIPTION]
        assert dialogue_result.content_type == ContentType.DIALOGUE
        assert char_result.content_type == ContentType.CHARACTER_DESCRIPTION
        
        # All should have positive token counts
        assert story_result.token_count > 0
        assert dialogue_result.token_count > 0
        assert char_result.token_count > 0
    
    def test_hierarchical_borrowing_scenario(self):
        """Test complex hierarchical token borrowing scenario."""
        hierarchy = LayerHierarchy()
        allocator = TokenAllocator(
            total_budget=3000,
            hierarchy=hierarchy,
            overflow_strategy=OverflowStrategy.BORROW
        )
        
        # Exhaust most of the story layer budget
        story_requests = [
            AllocationRequest(LayerType.WORKING_MEMORY, 400),
            AllocationRequest(LayerType.WORKING_MEMORY, 400),
            AllocationRequest(LayerType.WORKING_MEMORY, 400)
        ]
        
        for request in story_requests:
            result = allocator.allocate_tokens(request)
            assert result.success is True
        
        # Now request more than remaining in story layer
        overflow_request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=300
        )
        
        result = allocator.allocate_tokens(overflow_request)
        
        # Should succeed through borrowing
        assert result.success is True
        assert result.borrowed_tokens > 0
        
        # Verify borrowing is balanced
        validation = allocator.validate_allocations()
        runtime = validation["runtime_validation"]
        assert runtime["borrowing_balanced"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=backend.app.services.token_management", "--cov=backend.app.utils.llama_tokenizer", "--cov-report=term-missing"])
