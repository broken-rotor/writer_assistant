#!/usr/bin/env python3
"""
Dead Code Analysis Tool for Writer Assistant Migration

This script analyzes the codebase to identify potentially obsolete components
that can be removed during the migration from monolithic to structured context API.

Features:
- Identifies unused imports, classes, and functions
- Maps dependencies between components
- Analyzes context mode usage patterns
- Generates removal recommendations
"""

import os
import ast
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import argparse


@dataclass
class ComponentInfo:
    """Information about a code component."""
    name: str
    type: str  # 'class', 'function', 'import', 'variable'
    file_path: str
    line_number: int
    dependencies: List[str]
    used_by: List[str]
    is_legacy_context: bool = False
    is_worldbuilding_specific: bool = False
    confidence_obsolete: float = 0.0  # 0.0 = keep, 1.0 = definitely remove


@dataclass
class AnalysisResult:
    """Results of dead code analysis."""
    obsolete_components: List[ComponentInfo]
    dependency_map: Dict[str, List[str]]
    usage_patterns: Dict[str, int]
    recommendations: List[str]
    total_files_analyzed: int
    potential_savings: Dict[str, int]  # lines of code, files, etc.


class DeadCodeAnalyzer:
    """Analyzes codebase for dead code and obsolete components."""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.components: Dict[str, ComponentInfo] = {}
        self.imports_map: Dict[str, Set[str]] = defaultdict(set)
        self.usage_map: Dict[str, Set[str]] = defaultdict(set)
        
        # Patterns for identifying legacy context components
        self.legacy_patterns = [
            r'systemPrompts?',
            r'worldbuilding',
            r'storySummary',
            r'context_optimization',
            r'ContextOptimization',
            r'legacy.*context',
            r'monolithic.*context'
        ]
        
        # Worldbuilding-specific patterns
        self.worldbuilding_patterns = [
            r'worldbuilding_.*',
            r'Worldbuilding.*',
            r'WorldBuilding.*'
        ]
    
    def analyze(self) -> AnalysisResult:
        """Perform comprehensive dead code analysis."""
        print("🔍 Starting dead code analysis...")
        
        # Analyze Python files
        python_files = list(self.root_path.rglob("*.py"))
        typescript_files = list(self.root_path.rglob("*.ts"))
        
        print(f"📁 Found {len(python_files)} Python files and {len(typescript_files)} TypeScript files")
        
        # Analyze each file
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue
            self._analyze_python_file(file_path)
        
        for file_path in typescript_files:
            if self._should_skip_file(file_path):
                continue
            self._analyze_typescript_file(file_path)
        
        # Build dependency map
        dependency_map = self._build_dependency_map()
        
        # Identify obsolete components
        obsolete_components = self._identify_obsolete_components()
        
        # Analyze usage patterns
        usage_patterns = self._analyze_usage_patterns()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(obsolete_components)
        
        # Calculate potential savings
        potential_savings = self._calculate_potential_savings(obsolete_components)
        
        return AnalysisResult(
            obsolete_components=obsolete_components,
            dependency_map=dependency_map,
            usage_patterns=usage_patterns,
            recommendations=recommendations,
            total_files_analyzed=len(python_files) + len(typescript_files),
            potential_savings=potential_savings
        )
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during analysis."""
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
        return any(pattern in path_str for pattern in skip_patterns)
    
    def _analyze_python_file(self, file_path: Path):
        """Analyze a Python file for components and dependencies."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self._process_class(node, file_path)
                elif isinstance(node, ast.FunctionDef):
                    self._process_function(node, file_path)
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    self._process_import(node, file_path)
        
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
    
    def _analyze_typescript_file(self, file_path: Path):
        """Analyze a TypeScript file for components and dependencies."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple regex-based analysis for TypeScript
            # Look for class definitions
            class_matches = re.finditer(r'export\s+class\s+(\w+)', content)
            for match in class_matches:
                class_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                self._add_component(class_name, 'class', file_path, line_num)
            
            # Look for function definitions
            func_matches = re.finditer(r'export\s+function\s+(\w+)', content)
            for match in func_matches:
                func_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                self._add_component(func_name, 'function', file_path, line_num)
            
            # Look for imports
            import_matches = re.finditer(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', content)
            for match in import_matches:
                import_path = match.group(1)
                self.imports_map[str(file_path)].add(import_path)
        
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
    
    def _process_class(self, node: ast.ClassDef, file_path: Path):
        """Process a class definition."""
        self._add_component(node.name, 'class', file_path, node.lineno)
    
    def _process_function(self, node: ast.FunctionDef, file_path: Path):
        """Process a function definition."""
        self._add_component(node.name, 'function', file_path, node.lineno)
    
    def _process_import(self, node: ast.Import | ast.ImportFrom, file_path: Path):
        """Process an import statement."""
        if isinstance(node, ast.Import):
            for alias in node.names:
                self.imports_map[str(file_path)].add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            self.imports_map[str(file_path)].add(node.module)
    
    def _add_component(self, name: str, comp_type: str, file_path: Path, line_num: int):
        """Add a component to the analysis."""
        component_key = f"{file_path}:{name}"
        
        # Check if component is legacy context related
        is_legacy = any(re.search(pattern, name, re.IGNORECASE) for pattern in self.legacy_patterns)
        
        # Check if component is worldbuilding specific
        is_worldbuilding = any(re.search(pattern, name, re.IGNORECASE) for pattern in self.worldbuilding_patterns)
        
        component = ComponentInfo(
            name=name,
            type=comp_type,
            file_path=str(file_path),
            line_number=line_num,
            dependencies=[],
            used_by=[],
            is_legacy_context=is_legacy,
            is_worldbuilding_specific=is_worldbuilding
        )
        
        self.components[component_key] = component
    
    def _build_dependency_map(self) -> Dict[str, List[str]]:
        """Build a map of dependencies between components."""
        dependency_map = {}
        
        for file_path, imports in self.imports_map.items():
            dependency_map[file_path] = list(imports)
        
        return dependency_map
    
    def _identify_obsolete_components(self) -> List[ComponentInfo]:
        """Identify components that are likely obsolete."""
        obsolete = []
        
        for component in self.components.values():
            confidence = 0.0
            
            # High confidence for legacy context components
            if component.is_legacy_context:
                confidence += 0.7
            
            # Medium confidence for worldbuilding components
            if component.is_worldbuilding_specific:
                confidence += 0.5
            
            # Check for specific obsolete services
            obsolete_services = [
                'ContextOptimizationService',
                'context_optimization',
                'worldbuilding_classifier',
                'worldbuilding_prompts',
                'worldbuilding_followup'
            ]
            
            if any(service in component.name.lower() or service in component.file_path.lower() 
                   for service in obsolete_services):
                confidence += 0.8
            
            # Adjust confidence based on usage
            if len(component.used_by) == 0:
                confidence += 0.3
            elif len(component.used_by) < 3:
                confidence += 0.1
            
            component.confidence_obsolete = min(confidence, 1.0)
            
            # Consider obsolete if confidence > 0.6
            if component.confidence_obsolete > 0.6:
                obsolete.append(component)
        
        return sorted(obsolete, key=lambda x: x.confidence_obsolete, reverse=True)
    
    def _analyze_usage_patterns(self) -> Dict[str, int]:
        """Analyze usage patterns of different context modes."""
        patterns = {
            'legacy_context_usage': 0,
            'structured_context_usage': 0,
            'hybrid_context_usage': 0,
            'worldbuilding_services': 0
        }
        
        for file_path in self.root_path.rglob("*.py"):
            if self._should_skip_file(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Count usage patterns
                if re.search(r'systemPrompts|worldbuilding|storySummary', content):
                    patterns['legacy_context_usage'] += 1
                
                if re.search(r'StructuredContext|structured_context', content):
                    patterns['structured_context_usage'] += 1
                
                if re.search(r'hybrid.*context|context.*hybrid', content, re.IGNORECASE):
                    patterns['hybrid_context_usage'] += 1
                
                if re.search(r'worldbuilding_.*\.py|Worldbuilding.*Service', content):
                    patterns['worldbuilding_services'] += 1
            
            except Exception:
                continue
        
        return patterns
    
    def _generate_recommendations(self, obsolete_components: List[ComponentInfo]) -> List[str]:
        """Generate removal recommendations."""
        recommendations = []
        
        # Group by file for easier removal
        files_to_remove = set()
        services_to_remove = set()
        
        for component in obsolete_components:
            if component.confidence_obsolete > 0.9:
                if 'service' in component.file_path.lower():
                    services_to_remove.add(component.file_path)
                
                if component.confidence_obsolete == 1.0:
                    files_to_remove.add(component.file_path)
        
        if services_to_remove:
            recommendations.append(f"🔥 Remove {len(services_to_remove)} obsolete service files")
        
        if files_to_remove:
            recommendations.append(f"🗑️  Remove {len(files_to_remove)} completely obsolete files")
        
        # Specific recommendations
        high_confidence = [c for c in obsolete_components if c.confidence_obsolete > 0.8]
        if high_confidence:
            recommendations.append(f"⚠️  Review {len(high_confidence)} high-confidence obsolete components")
        
        recommendations.append("📝 Update API endpoints to remove legacy context parameters")
        recommendations.append("🧹 Clean up imports and dependencies after component removal")
        recommendations.append("🧪 Update tests to use structured context patterns")
        
        return recommendations
    
    def _calculate_potential_savings(self, obsolete_components: List[ComponentInfo]) -> Dict[str, int]:
        """Calculate potential code savings from removing obsolete components."""
        savings = {
            'files': 0,
            'lines_of_code': 0,
            'components': len(obsolete_components)
        }
        
        files_to_remove = set()
        
        for component in obsolete_components:
            if component.confidence_obsolete > 0.9:
                files_to_remove.add(component.file_path)
        
        savings['files'] = len(files_to_remove)
        
        # Estimate lines of code
        for file_path in files_to_remove:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    savings['lines_of_code'] += len(f.readlines())
            except Exception:
                continue
        
        return savings


def main():
    """Main entry point for the dead code analyzer."""
    parser = argparse.ArgumentParser(description='Analyze codebase for dead code and obsolete components')
    parser.add_argument('--root', default='.', help='Root directory to analyze')
    parser.add_argument('--output', default='dead_code_analysis.json', help='Output file for results')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    analyzer = DeadCodeAnalyzer(args.root)
    result = analyzer.analyze()
    
    # Save results to JSON
    with open(args.output, 'w') as f:
        json.dump(asdict(result), f, indent=2, default=str)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 DEAD CODE ANALYSIS SUMMARY")
    print("="*60)
    print(f"📁 Files analyzed: {result.total_files_analyzed}")
    print(f"🗑️  Obsolete components found: {len(result.obsolete_components)}")
    print(f"💾 Potential savings: {result.potential_savings['files']} files, {result.potential_savings['lines_of_code']} lines")
    
    print("\n🎯 TOP OBSOLETE COMPONENTS:")
    for component in result.obsolete_components[:10]:
        print(f"  • {component.name} ({component.type}) - {component.confidence_obsolete:.1%} confidence")
        print(f"    📍 {component.file_path}:{component.line_number}")
    
    print("\n📋 RECOMMENDATIONS:")
    for rec in result.recommendations:
        print(f"  {rec}")
    
    print(f"\n💾 Full results saved to: {args.output}")


if __name__ == "__main__":
    main()
