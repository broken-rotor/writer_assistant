#!/usr/bin/env python3
"""
Dependency Mapper for Writer Assistant Migration

This script maps dependencies between components to understand the impact
of removing obsolete code during the migration to structured context API.

Features:
- Maps import relationships between files
- Identifies circular dependencies
- Calculates dependency impact scores
- Generates safe removal order recommendations
"""

import os
import ast
import re
import json
import networkx as nx
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import argparse


@dataclass
class DependencyInfo:
    """Information about a dependency relationship."""
    source_file: str
    target_file: str
    import_type: str  # 'direct', 'from', 'relative'
    imported_names: List[str]
    line_number: int
    is_critical: bool = False  # True if removing target would break source


@dataclass
class ComponentDependency:
    """Dependency information for a specific component."""
    component_name: str
    file_path: str
    depends_on: List[str]  # Components this depends on
    used_by: List[str]    # Components that depend on this
    impact_score: float   # 0.0 = low impact, 1.0 = high impact
    removal_risk: str     # 'low', 'medium', 'high'


@dataclass
class DependencyAnalysisResult:
    """Results of dependency analysis."""
    dependency_graph: Dict[str, List[str]]
    component_dependencies: List[ComponentDependency]
    circular_dependencies: List[List[str]]
    removal_order: List[str]
    high_impact_components: List[str]
    safe_to_remove: List[str]


class DependencyMapper:
    """Maps and analyzes dependencies between code components."""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.dependencies: List[DependencyInfo] = []
        self.graph = nx.DiGraph()
        
        # Critical components that should not be removed
        self.critical_components = {
            'context_manager.py',
            'unified_context_processor.py',
            'main.py',
            'api.py',
            '__init__.py'
        }
        
        # Legacy components identified for removal
        self.legacy_components = {
            'context_optimization.py',
            'worldbuilding_classifier.py',
            'worldbuilding_prompts.py',
            'worldbuilding_followup.py',
            'worldbuilding_state_machine.py',
            'worldbuilding_sync.py',
            'worldbuilding_validator.py',
            'worldbuilding_persistence.py'
        }
    
    def analyze(self) -> DependencyAnalysisResult:
        """Perform comprehensive dependency analysis."""
        print("🔍 Starting dependency analysis...")
        
        # Find all Python files
        python_files = list(self.root_path.rglob("*.py"))
        python_files = [f for f in python_files if self._should_analyze_file(f)]
        
        print(f"📁 Analyzing {len(python_files)} Python files")
        
        # Build dependency graph
        for file_path in python_files:
            self._analyze_file_dependencies(file_path)
        
        # Build NetworkX graph for analysis
        self._build_networkx_graph()
        
        # Analyze component dependencies
        component_dependencies = self._analyze_component_dependencies()
        
        # Find circular dependencies
        circular_deps = self._find_circular_dependencies()
        
        # Calculate removal order
        removal_order = self._calculate_removal_order()
        
        # Identify high impact and safe components
        high_impact = self._identify_high_impact_components()
        safe_to_remove = self._identify_safe_to_remove()
        
        # Build dependency graph dict
        dependency_graph = {}
        for dep in self.dependencies:
            if dep.source_file not in dependency_graph:
                dependency_graph[dep.source_file] = []
            dependency_graph[dep.source_file].append(dep.target_file)
        
        return DependencyAnalysisResult(
            dependency_graph=dependency_graph,
            component_dependencies=component_dependencies,
            circular_dependencies=circular_deps,
            removal_order=removal_order,
            high_impact_components=high_impact,
            safe_to_remove=safe_to_remove
        )
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed."""
        skip_patterns = [
            'node_modules',
            'venv',
            '__pycache__',
            '.git',
            'test_',
            '.spec.',
            '.test.',
            'migrations'
        ]
        
        path_str = str(file_path)
        return not any(pattern in path_str for pattern in skip_patterns)
    
    def _analyze_file_dependencies(self, file_path: Path):
        """Analyze dependencies for a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self._process_import(node, file_path)
                elif isinstance(node, ast.ImportFrom):
                    self._process_import_from(node, file_path)
        
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
    
    def _process_import(self, node: ast.Import, source_file: Path):
        """Process a direct import statement."""
        for alias in node.names:
            target_file = self._resolve_import_path(alias.name, source_file)
            if target_file:
                dep = DependencyInfo(
                    source_file=str(source_file),
                    target_file=target_file,
                    import_type='direct',
                    imported_names=[alias.name],
                    line_number=node.lineno,
                    is_critical=self._is_critical_dependency(alias.name)
                )
                self.dependencies.append(dep)
    
    def _process_import_from(self, node: ast.ImportFrom, source_file: Path):
        """Process a from...import statement."""
        if not node.module:
            return
        
        target_file = self._resolve_import_path(node.module, source_file)
        if target_file:
            imported_names = [alias.name for alias in node.names]
            dep = DependencyInfo(
                source_file=str(source_file),
                target_file=target_file,
                import_type='from',
                imported_names=imported_names,
                line_number=node.lineno,
                is_critical=self._is_critical_dependency(node.module)
            )
            self.dependencies.append(dep)
    
    def _resolve_import_path(self, import_name: str, source_file: Path) -> Optional[str]:
        """Resolve an import to an actual file path."""
        # Handle relative imports
        if import_name.startswith('.'):
            base_dir = source_file.parent
            parts = import_name.lstrip('.').split('.')
            target_path = base_dir
            for part in parts:
                if part:
                    target_path = target_path / part
            
            # Try .py file
            py_file = target_path.with_suffix('.py')
            if py_file.exists():
                return str(py_file)
            
            # Try __init__.py in directory
            init_file = target_path / '__init__.py'
            if init_file.exists():
                return str(init_file)
        
        # Handle absolute imports within the project
        if import_name.startswith('app.') or import_name.startswith('backend.app.'):
            # Remove backend. prefix if present
            clean_name = import_name.replace('backend.', '')
            parts = clean_name.split('.')
            
            # Start from backend directory
            target_path = self.root_path / 'backend'
            for part in parts:
                target_path = target_path / part
            
            # Try .py file
            py_file = target_path.with_suffix('.py')
            if py_file.exists():
                return str(py_file)
            
            # Try __init__.py in directory
            init_file = target_path / '__init__.py'
            if init_file.exists():
                return str(init_file)
        
        return None
    
    def _is_critical_dependency(self, import_name: str) -> bool:
        """Check if a dependency is critical (removing it would break things)."""
        critical_patterns = [
            'fastapi',
            'pydantic',
            'langchain',
            'context_manager',
            'unified_context_processor'
        ]
        
        return any(pattern in import_name.lower() for pattern in critical_patterns)
    
    def _build_networkx_graph(self):
        """Build NetworkX graph from dependencies."""
        for dep in self.dependencies:
            self.graph.add_edge(dep.source_file, dep.target_file)
    
    def _analyze_component_dependencies(self) -> List[ComponentDependency]:
        """Analyze dependencies for each component."""
        component_deps = []
        
        # Group dependencies by file
        file_deps = defaultdict(lambda: {'depends_on': set(), 'used_by': set()})
        
        for dep in self.dependencies:
            file_deps[dep.source_file]['depends_on'].add(dep.target_file)
            file_deps[dep.target_file]['used_by'].add(dep.source_file)
        
        # Calculate impact scores and risk levels
        for file_path, deps in file_deps.items():
            file_name = Path(file_path).name
            
            # Calculate impact score based on usage
            used_by_count = len(deps['used_by'])
            depends_on_count = len(deps['depends_on'])
            
            # Higher score = higher impact if removed
            impact_score = min(used_by_count * 0.1, 1.0)
            
            # Determine removal risk
            if file_name in self.critical_components:
                risk = 'high'
                impact_score = 1.0
            elif used_by_count > 5:
                risk = 'high'
            elif used_by_count > 2:
                risk = 'medium'
            else:
                risk = 'low'
            
            # Lower risk for legacy components
            if file_name in self.legacy_components:
                risk = 'low'
                impact_score *= 0.5
            
            component_dep = ComponentDependency(
                component_name=file_name,
                file_path=file_path,
                depends_on=list(deps['depends_on']),
                used_by=list(deps['used_by']),
                impact_score=impact_score,
                removal_risk=risk
            )
            component_deps.append(component_dep)
        
        return sorted(component_deps, key=lambda x: x.impact_score, reverse=True)
    
    def _find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in the graph."""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except Exception:
            return []
    
    def _calculate_removal_order(self) -> List[str]:
        """Calculate safe order for removing components."""
        removal_order = []
        
        # Start with components that have no dependents (leaf nodes)
        remaining_nodes = set(self.graph.nodes())
        
        while remaining_nodes:
            # Find nodes with no incoming edges from remaining nodes
            leaf_nodes = []
            for node in remaining_nodes:
                incoming = [pred for pred in self.graph.predecessors(node) 
                           if pred in remaining_nodes]
                if not incoming:
                    leaf_nodes.append(node)
            
            if not leaf_nodes:
                # Handle circular dependencies - pick the one with lowest impact
                leaf_nodes = [min(remaining_nodes, 
                                key=lambda x: len(list(self.graph.predecessors(x))))]
            
            # Sort leaf nodes by priority (legacy components first)
            leaf_nodes.sort(key=lambda x: (
                Path(x).name not in self.legacy_components,  # Legacy first
                len(list(self.graph.predecessors(x)))        # Then by dependency count
            ))
            
            # Add to removal order and remove from graph
            for node in leaf_nodes:
                if Path(node).name in self.legacy_components:
                    removal_order.append(node)
                remaining_nodes.remove(node)
        
        return removal_order
    
    def _identify_high_impact_components(self) -> List[str]:
        """Identify components that would have high impact if removed."""
        high_impact = []
        
        for node in self.graph.nodes():
            # Count how many components depend on this one
            dependents = list(self.graph.predecessors(node))
            
            if len(dependents) > 3:  # Arbitrary threshold
                high_impact.append(node)
        
        return high_impact
    
    def _identify_safe_to_remove(self) -> List[str]:
        """Identify components that are safe to remove."""
        safe_to_remove = []
        
        for node in self.graph.nodes():
            file_name = Path(node).name
            
            # Safe if it's a legacy component with few dependents
            if file_name in self.legacy_components:
                dependents = list(self.graph.predecessors(node))
                if len(dependents) <= 2:  # Few or no dependents
                    safe_to_remove.append(node)
        
        return safe_to_remove


def main():
    """Main entry point for the dependency mapper."""
    parser = argparse.ArgumentParser(description='Map dependencies between code components')
    parser.add_argument('--root', default='.', help='Root directory to analyze')
    parser.add_argument('--output', default='dependency_analysis.json', help='Output file for results')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    mapper = DependencyMapper(args.root)
    result = mapper.analyze()
    
    # Save results to JSON
    with open(args.output, 'w') as f:
        json.dump(asdict(result), f, indent=2, default=str)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 DEPENDENCY ANALYSIS SUMMARY")
    print("="*60)
    print(f"📁 Components analyzed: {len(result.component_dependencies)}")
    print(f"🔗 Dependencies found: {len(result.dependency_graph)}")
    print(f"🔄 Circular dependencies: {len(result.circular_dependencies)}")
    print(f"⚠️  High impact components: {len(result.high_impact_components)}")
    print(f"✅ Safe to remove: {len(result.safe_to_remove)}")
    
    print("\n🎯 HIGH IMPACT COMPONENTS (careful removal required):")
    for component in result.high_impact_components[:10]:
        print(f"  • {Path(component).name}")
    
    print("\n✅ SAFE TO REMOVE (low impact):")
    for component in result.safe_to_remove[:10]:
        print(f"  • {Path(component).name}")
    
    if result.circular_dependencies:
        print("\n🔄 CIRCULAR DEPENDENCIES DETECTED:")
        for cycle in result.circular_dependencies[:5]:
            cycle_names = [Path(f).name for f in cycle]
            print(f"  • {' → '.join(cycle_names)}")
    
    print(f"\n💾 Full results saved to: {args.output}")


if __name__ == "__main__":
    main()
