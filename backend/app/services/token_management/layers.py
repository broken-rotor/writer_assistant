"""
Hierarchical Layer System for Context Manager

Defines the A-E layer hierarchy for token budget allocation and management
in the Writer Assistant's multi-agent storytelling system.
"""

import logging
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class LayerType(Enum):
    """Hierarchical layers for context management."""
    A_STORY = "A_story"           # Story-level context (highest level)
    B_CHAPTER = "B_chapter"       # Chapter-level context
    C_SCENE = "C_scene"           # Scene-level context
    D_CHARACTER = "D_character"   # Character-level context
    E_DIALOGUE = "E_dialogue"     # Dialogue-level context (lowest level)


@dataclass
class LayerConfig:
    """Configuration for a specific layer."""
    layer_type: LayerType
    min_tokens: int
    max_tokens: int
    default_tokens: int
    priority: int  # Higher number = higher priority
    can_borrow: bool = True  # Can borrow tokens from other layers
    can_lend: bool = True    # Can lend tokens to other layers
    parent_layer: Optional[LayerType] = None
    child_layers: Set[LayerType] = field(default_factory=set)
    description: str = ""


@dataclass
class LayerAllocation:
    """Current token allocation for a layer."""
    layer_type: LayerType
    allocated_tokens: int
    used_tokens: int
    reserved_tokens: int
    borrowed_tokens: int
    lent_tokens: int
    
    @property
    def available_tokens(self) -> int:
        """Get available tokens for this layer."""
        return self.allocated_tokens + self.borrowed_tokens - self.used_tokens - self.reserved_tokens - self.lent_tokens
    
    @property
    def utilization(self) -> float:
        """Get utilization percentage (0.0 to 1.0)."""
        total_capacity = self.allocated_tokens + self.borrowed_tokens
        if total_capacity == 0:
            return 0.0
        return (self.used_tokens + self.reserved_tokens + self.lent_tokens) / total_capacity


class LayerHierarchy:
    """
    Manages the hierarchical layer system for token allocation.
    
    This class defines the relationships between layers A-E and provides
    utilities for navigating the hierarchy and managing token flow.
    """
    
    def __init__(self):
        """Initialize the layer hierarchy with default configurations."""
        self._layer_configs = self._create_default_layer_configs()
        self._build_hierarchy_relationships()
    
    def _create_default_layer_configs(self) -> Dict[LayerType, LayerConfig]:
        """Create default layer configurations based on storytelling requirements."""
        configs = {
            LayerType.A_STORY: LayerConfig(
                layer_type=LayerType.A_STORY,
                min_tokens=500,
                max_tokens=2000,
                default_tokens=1000,
                priority=5,
                description="Story-level context including theme, genre, overall narrative arc"
            ),
            LayerType.B_CHAPTER: LayerConfig(
                layer_type=LayerType.B_CHAPTER,
                min_tokens=300,
                max_tokens=1500,
                default_tokens=800,
                priority=4,
                description="Chapter-level context including chapter goals, major events, transitions"
            ),
            LayerType.C_SCENE: LayerConfig(
                layer_type=LayerType.C_SCENE,
                min_tokens=200,
                max_tokens=1000,
                default_tokens=600,
                priority=3,
                description="Scene-level context including setting, atmosphere, immediate goals"
            ),
            LayerType.D_CHARACTER: LayerConfig(
                layer_type=LayerType.D_CHARACTER,
                min_tokens=150,
                max_tokens=800,
                default_tokens=400,
                priority=2,
                description="Character-level context including personality, memories, relationships"
            ),
            LayerType.E_DIALOGUE: LayerConfig(
                layer_type=LayerType.E_DIALOGUE,
                min_tokens=50,
                max_tokens=400,
                default_tokens=200,
                priority=1,
                description="Dialogue-level context including speech patterns, immediate conversation"
            )
        }
        return configs
    
    def _build_hierarchy_relationships(self):
        """Build parent-child relationships between layers."""
        # Define hierarchy: A -> B -> C -> D -> E
        relationships = [
            (LayerType.A_STORY, LayerType.B_CHAPTER),
            (LayerType.B_CHAPTER, LayerType.C_SCENE),
            (LayerType.C_SCENE, LayerType.D_CHARACTER),
            (LayerType.D_CHARACTER, LayerType.E_DIALOGUE)
        ]
        
        for parent, child in relationships:
            self._layer_configs[parent].child_layers.add(child)
            self._layer_configs[child].parent_layer = parent
    
    def get_layer_config(self, layer_type: LayerType) -> LayerConfig:
        """Get configuration for a specific layer."""
        return self._layer_configs[layer_type]
    
    def get_all_layer_configs(self) -> Dict[LayerType, LayerConfig]:
        """Get all layer configurations."""
        return self._layer_configs.copy()
    
    def get_parent_layer(self, layer_type: LayerType) -> Optional[LayerType]:
        """Get the parent layer of the specified layer."""
        return self._layer_configs[layer_type].parent_layer
    
    def get_child_layers(self, layer_type: LayerType) -> Set[LayerType]:
        """Get the child layers of the specified layer."""
        return self._layer_configs[layer_type].child_layers.copy()
    
    def get_ancestor_layers(self, layer_type: LayerType) -> List[LayerType]:
        """Get all ancestor layers (parents, grandparents, etc.) in order from immediate parent to root."""
        ancestors = []
        current = layer_type
        
        while True:
            parent = self.get_parent_layer(current)
            if parent is None:
                break
            ancestors.append(parent)
            current = parent
        
        return ancestors
    
    def get_descendant_layers(self, layer_type: LayerType) -> List[LayerType]:
        """Get all descendant layers (children, grandchildren, etc.) in breadth-first order."""
        descendants = []
        queue = list(self.get_child_layers(layer_type))
        
        while queue:
            current = queue.pop(0)
            descendants.append(current)
            queue.extend(self.get_child_layers(current))
        
        return descendants
    
    def get_layer_path(self, from_layer: LayerType, to_layer: LayerType) -> Optional[List[LayerType]]:
        """
        Get the path between two layers in the hierarchy.
        
        Args:
            from_layer: Starting layer
            to_layer: Target layer
            
        Returns:
            List of layers forming the path, or None if no path exists
        """
        # Get all ancestors and descendants of from_layer
        from_ancestors = self.get_ancestor_layers(from_layer)
        from_descendants = self.get_descendant_layers(from_layer)
        
        # Check if to_layer is an ancestor
        if to_layer in from_ancestors:
            path = [from_layer]
            current = from_layer
            while current != to_layer:
                parent = self.get_parent_layer(current)
                if parent is None:
                    return None
                path.append(parent)
                current = parent
            return path
        
        # Check if to_layer is a descendant
        if to_layer in from_descendants:
            # Build path by traversing down
            path = [from_layer]
            current = from_layer
            
            # This is a simplified approach - for a more complex hierarchy,
            # you might need a more sophisticated pathfinding algorithm
            queue = [(current, [current])]
            visited = {current}
            
            while queue:
                node, node_path = queue.pop(0)
                if node == to_layer:
                    return node_path
                
                for child in self.get_child_layers(node):
                    if child not in visited:
                        visited.add(child)
                        queue.append((child, node_path + [child]))
            
            return None
        
        # Check if they share a common ancestor
        to_ancestors = self.get_ancestor_layers(to_layer)
        common_ancestors = set(from_ancestors) & set(to_ancestors)
        
        if common_ancestors:
            # Find the closest common ancestor
            common_ancestor = None
            for ancestor in from_ancestors:
                if ancestor in common_ancestors:
                    common_ancestor = ancestor
                    break
            
            if common_ancestor:
                # Build path: from_layer -> common_ancestor -> to_layer
                path_up = self.get_layer_path(from_layer, common_ancestor)
                path_down = self.get_layer_path(common_ancestor, to_layer)
                
                if path_up and path_down:
                    # Remove duplicate common ancestor
                    return path_up + path_down[1:]
        
        return None
    
    def get_layers_by_priority(self, descending: bool = True) -> List[LayerType]:
        """Get layers ordered by priority."""
        layers = list(self._layer_configs.keys())
        layers.sort(key=lambda l: self._layer_configs[l].priority, reverse=descending)
        return layers
    
    def calculate_total_default_budget(self) -> int:
        """Calculate the total default token budget across all layers."""
        return sum(config.default_tokens for config in self._layer_configs.values())
    
    def calculate_total_minimum_budget(self) -> int:
        """Calculate the total minimum token budget across all layers."""
        return sum(config.min_tokens for config in self._layer_configs.values())
    
    def calculate_total_maximum_budget(self) -> int:
        """Calculate the total maximum token budget across all layers."""
        return sum(config.max_tokens for config in self._layer_configs.values())
    
    def validate_layer_allocation(self, allocations: Dict[LayerType, int]) -> Dict[str, Any]:
        """
        Validate a proposed layer allocation against constraints.
        
        Args:
            allocations: Dictionary mapping layer types to token allocations
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "total_allocated": sum(allocations.values()),
            "layer_validations": {}
        }
        
        for layer_type, allocation in allocations.items():
            config = self._layer_configs[layer_type]
            layer_result = {
                "valid": True,
                "allocation": allocation,
                "min_tokens": config.min_tokens,
                "max_tokens": config.max_tokens,
                "issues": []
            }
            
            if allocation < config.min_tokens:
                layer_result["valid"] = False
                layer_result["issues"].append(f"Allocation {allocation} below minimum {config.min_tokens}")
                results["errors"].append(f"Layer {layer_type.value}: allocation below minimum")
                results["valid"] = False
            
            if allocation > config.max_tokens:
                layer_result["issues"].append(f"Allocation {allocation} above maximum {config.max_tokens}")
                results["warnings"].append(f"Layer {layer_type.value}: allocation above maximum")
            
            results["layer_validations"][layer_type] = layer_result
        
        return results
    
    def suggest_balanced_allocation(self, total_budget: int) -> Dict[LayerType, int]:
        """
        Suggest a balanced token allocation across layers based on priorities and constraints.
        
        Args:
            total_budget: Total token budget to allocate
            
        Returns:
            Dictionary mapping layer types to suggested allocations
        """
        if total_budget < self.calculate_total_minimum_budget():
            # If budget is too small, allocate minimums and warn
            logger.warning(f"Budget {total_budget} is below minimum required {self.calculate_total_minimum_budget()}")
            return {layer: config.min_tokens for layer, config in self._layer_configs.items()}
        
        # Start with default allocations
        allocations = {layer: config.default_tokens for layer, config in self._layer_configs.items()}
        current_total = sum(allocations.values())
        
        if current_total == total_budget:
            return allocations
        
        # Adjust allocations proportionally
        if current_total < total_budget:
            # We have extra budget to distribute
            extra_budget = total_budget - current_total
            layers_by_priority = self.get_layers_by_priority(descending=True)
            
            # Distribute extra budget to high-priority layers first
            for layer in layers_by_priority:
                config = self._layer_configs[layer]
                current_allocation = allocations[layer]
                max_increase = config.max_tokens - current_allocation
                
                if max_increase > 0 and extra_budget > 0:
                    increase = min(extra_budget, max_increase)
                    allocations[layer] += increase
                    extra_budget -= increase
                
                if extra_budget <= 0:
                    break
        
        elif current_total > total_budget:
            # We need to reduce allocations
            reduction_needed = current_total - total_budget
            layers_by_priority = self.get_layers_by_priority(descending=False)
            
            # Reduce from low-priority layers first
            for layer in layers_by_priority:
                config = self._layer_configs[layer]
                current_allocation = allocations[layer]
                max_reduction = current_allocation - config.min_tokens
                
                if max_reduction > 0 and reduction_needed > 0:
                    reduction = min(reduction_needed, max_reduction)
                    allocations[layer] -= reduction
                    reduction_needed -= reduction
                
                if reduction_needed <= 0:
                    break
        
        return allocations
    
    def get_layer_hierarchy_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the layer hierarchy."""
        return {
            "layers": {
                layer.value: {
                    "config": {
                        "min_tokens": config.min_tokens,
                        "max_tokens": config.max_tokens,
                        "default_tokens": config.default_tokens,
                        "priority": config.priority,
                        "can_borrow": config.can_borrow,
                        "can_lend": config.can_lend,
                        "description": config.description
                    },
                    "relationships": {
                        "parent": config.parent_layer.value if config.parent_layer else None,
                        "children": [child.value for child in config.child_layers]
                    }
                }
                for layer, config in self._layer_configs.items()
            },
            "hierarchy_stats": {
                "total_layers": len(self._layer_configs),
                "total_default_budget": self.calculate_total_default_budget(),
                "total_minimum_budget": self.calculate_total_minimum_budget(),
                "total_maximum_budget": self.calculate_total_maximum_budget(),
                "layers_by_priority": [layer.value for layer in self.get_layers_by_priority()]
            }
        }
