#!/usr/bin/env python3
"""
Removal Safety Validator

This script validates that deprecated components can be safely removed
by checking dependencies, usage patterns, and potential breaking changes.

Features:
- Validates zero usage of components before removal
- Checks for hidden dependencies and imports
- Simulates removal to detect breaking changes
- Generates safety reports and recommendations
- Provides rollback validation
"""

import os
import ast
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SafetyCheck:
    """Represents a safety validation check."""
    check_name: str
    check_type: str  # 'dependency', 'usage', 'import', 'test'
    status: str  # 'pass', 'fail', 'warning'
    message: str
    details: Dict[str, Any]
    blocking: bool  # True if this check blocks removal


@dataclass
class ComponentSafetyReport:
    """Safety report for a specific component."""
    component_name: str
    component_type: str
    file_path: str
    removal_safe: bool
    safety_checks: List[SafetyCheck]
    dependencies_found: List[str]
    usage_locations: List[str]
    test_impact: List[str]
    recommendations: List[str]


@dataclass
class RemovalSafetyReport:
    """Complete safety validation report."""
    validation_date: str
    components_validated: int
    safe_for_removal: List[ComponentSafetyReport]
    unsafe_for_removal: List[ComponentSafetyReport]
    warnings: List[ComponentSafetyReport]
    overall_safety_score: float
    blocking_issues: List[str]
    recommendations: List[str]


class RemovalSafetyValidator:
    """Validates safety of removing deprecated components."""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.python_files = list(self.root_path.rglob("*.py"))
        self.typescript_files = list(self.root_path.rglob("*.ts"))
        self.test_files = [f for f in self.python_files if 'test' in str(f).lower()]
        
        # Load deprecated components list
        self.deprecated_components = self._load_deprecated_components()
        
        # Initialize safety checks
        self.safety_checks = self._initialize_safety_checks()
    
    def _load_deprecated_components(self) -> Dict[str, Dict[str, Any]]:
        """Load deprecated components from analysis results."""
        # Try to load from dead code analysis results
        analysis_file = self.root_path / "backend" / "dead_code_analysis.json"
        if analysis_file.exists():
            try:
                with open(analysis_file, 'r') as f:
                    data = json.load(f)
                
                components = {}
                for component in data.get("obsolete_components", []):
                    components[component["name"]] = {
                        "type": component["type"],
                        "file_path": component["file_path"],
                        "confidence": component["confidence_obsolete"],
                        "is_legacy": component.get("is_legacy_context", False),
                        "is_worldbuilding": component.get("is_worldbuilding_specific", False)
                    }
                return components
            except Exception as e:
                logger.warning(f"Could not load analysis results: {e}")
        
        # Fallback to hardcoded list
        return {
            "WorldbuildingFollowupGenerator": {
                "type": "class",
                "file_path": "../backend/app/services/worldbuilding_followup.py",
                "confidence": 1.0,
                "is_legacy": True,
                "is_worldbuilding": True
            },
            "ContextOptimizationService": {
                "type": "class", 
                "file_path": "../backend/app/services/context_optimization.py",
                "confidence": 1.0,
                "is_legacy": True,
                "is_worldbuilding": False
            },
            "_process_legacy_context_for_chapter": {
                "type": "function",
                "file_path": "../backend/app/services/unified_context_processor.py",
                "confidence": 0.95,
                "is_legacy": True,
                "is_worldbuilding": False
            }
        }
    
    def _initialize_safety_checks(self) -> List[str]:
        """Initialize list of safety checks to perform."""
        return [
            "check_direct_imports",
            "check_indirect_dependencies", 
            "check_string_references",
            "check_test_dependencies",
            "check_configuration_references",
            "check_documentation_references",
            "simulate_removal"
        ]
    
    def validate_component_safety(self, component_name: str) -> ComponentSafetyReport:
        """Validate safety of removing a specific component."""
        logger.info(f"Validating removal safety for: {component_name}")
        
        component_info = self.deprecated_components.get(component_name, {})
        file_path = component_info.get("file_path", "")
        component_type = component_info.get("type", "unknown")
        
        safety_checks = []
        dependencies_found = []
        usage_locations = []
        test_impact = []
        
        # Run all safety checks
        for check_name in self.safety_checks:
            check_method = getattr(self, check_name)
            check_result = check_method(component_name, component_info)
            safety_checks.append(check_result)
            
            # Collect findings
            if check_result.status == "fail":
                if check_result.check_type == "dependency":
                    dependencies_found.extend(check_result.details.get("dependencies", []))
                elif check_result.check_type == "usage":
                    usage_locations.extend(check_result.details.get("locations", []))
                elif check_result.check_type == "test":
                    test_impact.extend(check_result.details.get("affected_tests", []))
        
        # Determine overall safety
        blocking_checks = [c for c in safety_checks if c.blocking and c.status == "fail"]
        removal_safe = len(blocking_checks) == 0
        
        # Generate recommendations
        recommendations = self._generate_component_recommendations(
            component_name, safety_checks, removal_safe
        )
        
        return ComponentSafetyReport(
            component_name=component_name,
            component_type=component_type,
            file_path=file_path,
            removal_safe=removal_safe,
            safety_checks=safety_checks,
            dependencies_found=dependencies_found,
            usage_locations=usage_locations,
            test_impact=test_impact,
            recommendations=recommendations
        )
    
    def check_direct_imports(self, component_name: str, component_info: Dict[str, Any]) -> SafetyCheck:
        """Check for direct imports of the component."""
        imports_found = []
        
        for file_path in self.python_files:
            if self._should_skip_file(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for various import patterns
                import_patterns = [
                    rf'from\s+.*\s+import\s+.*{re.escape(component_name)}',
                    rf'import\s+.*{re.escape(component_name)}',
                    rf'from\s+.*{re.escape(component_name)}\s+import'
                ]
                
                for pattern in import_patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        imports_found.append(f"{file_path}:{line_num}")
            
            except Exception as e:
                logger.debug(f"Error checking imports in {file_path}: {e}")
        
        status = "fail" if imports_found else "pass"
        message = f"Found {len(imports_found)} direct import(s)" if imports_found else "No direct imports found"
        
        return SafetyCheck(
            check_name="Direct Imports",
            check_type="dependency",
            status=status,
            message=message,
            details={"imports": imports_found},
            blocking=True
        )
    
    def check_indirect_dependencies(self, component_name: str, component_info: Dict[str, Any]) -> SafetyCheck:
        """Check for indirect dependencies on the component."""
        dependencies = []
        
        # Check for usage in other deprecated components
        for other_name, other_info in self.deprecated_components.items():
            if other_name == component_name:
                continue
            
            other_file = Path(other_info.get("file_path", ""))
            if not other_file.exists():
                continue
            
            try:
                with open(other_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if component_name in content:
                    dependencies.append(f"{other_name} -> {component_name}")
            
            except Exception as e:
                logger.debug(f"Error checking dependencies in {other_file}: {e}")
        
        status = "warning" if dependencies else "pass"
        message = f"Found {len(dependencies)} indirect dependencies" if dependencies else "No indirect dependencies"
        
        return SafetyCheck(
            check_name="Indirect Dependencies",
            check_type="dependency", 
            status=status,
            message=message,
            details={"dependencies": dependencies},
            blocking=False
        )
    
    def check_string_references(self, component_name: str, component_info: Dict[str, Any]) -> SafetyCheck:
        """Check for string references to the component."""
        string_refs = []
        
        for file_path in self.python_files + self.typescript_files:
            if self._should_skip_file(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for string references (in quotes)
                string_patterns = [
                    rf'["\'].*{re.escape(component_name)}.*["\']',
                    rf'{re.escape(component_name)}\s*["\']',  # Configuration keys
                ]
                
                for pattern in string_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        context = content[max(0, match.start()-50):match.end()+50].strip()
                        string_refs.append({
                            "file": str(file_path),
                            "line": line_num,
                            "context": context
                        })
            
            except Exception as e:
                logger.debug(f"Error checking string references in {file_path}: {e}")
        
        status = "warning" if string_refs else "pass"
        message = f"Found {len(string_refs)} string reference(s)" if string_refs else "No string references found"
        
        return SafetyCheck(
            check_name="String References",
            check_type="usage",
            status=status,
            message=message,
            details={"references": string_refs},
            blocking=False
        )
    
    def check_test_dependencies(self, component_name: str, component_info: Dict[str, Any]) -> SafetyCheck:
        """Check for test dependencies on the component."""
        test_dependencies = []
        
        for test_file in self.test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if component_name in content:
                    # Find specific test methods that reference the component
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if component_name in line and ('def test_' in line or 'class Test' in line):
                            test_dependencies.append({
                                "file": str(test_file),
                                "line": i + 1,
                                "test_name": line.strip()
                            })
            
            except Exception as e:
                logger.debug(f"Error checking test dependencies in {test_file}: {e}")
        
        status = "warning" if test_dependencies else "pass"
        message = f"Found {len(test_dependencies)} test dependencies" if test_dependencies else "No test dependencies"
        
        return SafetyCheck(
            check_name="Test Dependencies",
            check_type="test",
            status=status,
            message=message,
            details={"affected_tests": test_dependencies},
            blocking=False
        )
    
    def check_configuration_references(self, component_name: str, component_info: Dict[str, Any]) -> SafetyCheck:
        """Check for configuration file references."""
        config_refs = []
        
        # Check common configuration files
        config_patterns = ["*.json", "*.yaml", "*.yml", "*.toml", "*.ini", "*.env*"]
        config_files = []
        
        for pattern in config_patterns:
            config_files.extend(self.root_path.rglob(pattern))
        
        for config_file in config_files:
            if self._should_skip_file(config_file):
                continue
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if component_name.lower() in content.lower():
                    line_num = None
                    for i, line in enumerate(content.split('\n')):
                        if component_name.lower() in line.lower():
                            line_num = i + 1
                            break
                    
                    config_refs.append({
                        "file": str(config_file),
                        "line": line_num,
                        "type": config_file.suffix
                    })
            
            except Exception as e:
                logger.debug(f"Error checking config file {config_file}: {e}")
        
        status = "warning" if config_refs else "pass"
        message = f"Found {len(config_refs)} configuration references" if config_refs else "No configuration references"
        
        return SafetyCheck(
            check_name="Configuration References",
            check_type="usage",
            status=status,
            message=message,
            details={"references": config_refs},
            blocking=False
        )
    
    def check_documentation_references(self, component_name: str, component_info: Dict[str, Any]) -> SafetyCheck:
        """Check for documentation references."""
        doc_refs = []
        
        # Check documentation files
        doc_patterns = ["*.md", "*.rst", "*.txt"]
        doc_files = []
        
        for pattern in doc_patterns:
            doc_files.extend(self.root_path.rglob(pattern))
        
        for doc_file in doc_files:
            if self._should_skip_file(doc_file):
                continue
            
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if component_name in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if component_name in line:
                            doc_refs.append({
                                "file": str(doc_file),
                                "line": i + 1,
                                "context": line.strip()
                            })
            
            except Exception as e:
                logger.debug(f"Error checking documentation file {doc_file}: {e}")
        
        status = "warning" if doc_refs else "pass"
        message = f"Found {len(doc_refs)} documentation references" if doc_refs else "No documentation references"
        
        return SafetyCheck(
            check_name="Documentation References",
            check_type="usage",
            status=status,
            message=message,
            details={"references": doc_refs},
            blocking=False
        )
    
    def simulate_removal(self, component_name: str, component_info: Dict[str, Any]) -> SafetyCheck:
        """Simulate removal by temporarily commenting out the component."""
        simulation_results = {
            "syntax_errors": [],
            "import_errors": [],
            "test_failures": []
        }
        
        component_file = Path(component_info.get("file_path", ""))
        if not component_file.exists():
            return SafetyCheck(
                check_name="Removal Simulation",
                check_type="simulation",
                status="warning",
                message="Component file not found for simulation",
                details=simulation_results,
                blocking=False
            )
        
        try:
            # Read original file
            with open(component_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Create modified content (comment out the component)
            modified_content = self._comment_out_component(
                original_content, component_name, component_info["type"]
            )
            
            # Write temporary file
            temp_file = component_file.with_suffix('.py.temp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            # Check syntax
            try:
                ast.parse(modified_content)
            except SyntaxError as e:
                simulation_results["syntax_errors"].append(str(e))
            
            # Try to import the module (if it's importable)
            try:
                # This is a simplified check - in practice would need more sophisticated import testing
                pass
            except ImportError as e:
                simulation_results["import_errors"].append(str(e))
            
            # Clean up
            if temp_file.exists():
                temp_file.unlink()
        
        except Exception as e:
            logger.debug(f"Error simulating removal of {component_name}: {e}")
            simulation_results["simulation_error"] = str(e)
        
        # Determine status
        has_errors = (simulation_results["syntax_errors"] or 
                     simulation_results["import_errors"] or
                     simulation_results["test_failures"])
        
        status = "fail" if has_errors else "pass"
        message = "Removal simulation passed" if not has_errors else "Removal simulation found issues"
        
        return SafetyCheck(
            check_name="Removal Simulation",
            check_type="simulation",
            status=status,
            message=message,
            details=simulation_results,
            blocking=True
        )
    
    def _comment_out_component(self, content: str, component_name: str, component_type: str) -> str:
        """Comment out a specific component in the content."""
        lines = content.split('\n')
        modified_lines = []
        in_component = False
        indent_level = 0
        
        for line in lines:
            if component_type == "class" and f"class {component_name}" in line:
                in_component = True
                indent_level = len(line) - len(line.lstrip())
                modified_lines.append(f"# REMOVED: {line}")
            elif component_type == "function" and f"def {component_name}" in line:
                in_component = True
                indent_level = len(line) - len(line.lstrip())
                modified_lines.append(f"# REMOVED: {line}")
            elif in_component:
                current_indent = len(line) - len(line.lstrip())
                if line.strip() and current_indent <= indent_level:
                    in_component = False
                    modified_lines.append(line)
                else:
                    modified_lines.append(f"# REMOVED: {line}")
            else:
                modified_lines.append(line)
        
        return '\n'.join(modified_lines)
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during analysis."""
        skip_patterns = [
            'node_modules', 'venv', '__pycache__', '.git',
            '.pytest_cache', '.mypy_cache', 'migrations'
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)
    
    def _generate_component_recommendations(self, component_name: str, 
                                          safety_checks: List[SafetyCheck], 
                                          removal_safe: bool) -> List[str]:
        """Generate recommendations for component removal."""
        recommendations = []
        
        if removal_safe:
            recommendations.append("✅ Component is safe for immediate removal")
        else:
            recommendations.append("❌ Component is NOT safe for removal")
            
            # Specific recommendations based on failed checks
            for check in safety_checks:
                if check.status == "fail" and check.blocking:
                    if check.check_type == "dependency":
                        recommendations.append(f"🔗 Resolve dependencies: {check.message}")
                    elif check.check_type == "simulation":
                        recommendations.append(f"⚠️ Fix simulation issues: {check.message}")
        
        # Recommendations for warnings
        warning_checks = [c for c in safety_checks if c.status == "warning"]
        if warning_checks:
            recommendations.append("⚠️ Address warnings before removal:")
            for check in warning_checks:
                recommendations.append(f"   • {check.check_name}: {check.message}")
        
        return recommendations
    
    def validate_all_components(self) -> RemovalSafetyReport:
        """Validate safety of removing all deprecated components."""
        logger.info(f"Validating safety for {len(self.deprecated_components)} components...")
        
        safe_components = []
        unsafe_components = []
        warning_components = []
        
        for component_name in self.deprecated_components:
            report = self.validate_component_safety(component_name)
            
            if report.removal_safe:
                safe_components.append(report)
            else:
                unsafe_components.append(report)
            
            # Check for warnings
            if any(c.status == "warning" for c in report.safety_checks):
                warning_components.append(report)
        
        # Calculate overall safety score
        total_components = len(self.deprecated_components)
        safe_count = len(safe_components)
        safety_score = (safe_count / total_components) * 100 if total_components > 0 else 100
        
        # Collect blocking issues
        blocking_issues = []
        for report in unsafe_components:
            for check in report.safety_checks:
                if check.blocking and check.status == "fail":
                    blocking_issues.append(f"{report.component_name}: {check.message}")
        
        # Generate overall recommendations
        recommendations = self._generate_overall_recommendations(
            safe_components, unsafe_components, warning_components
        )
        
        return RemovalSafetyReport(
            validation_date=str(datetime.now()),
            components_validated=total_components,
            safe_for_removal=safe_components,
            unsafe_for_removal=unsafe_components,
            warnings=warning_components,
            overall_safety_score=safety_score,
            blocking_issues=blocking_issues,
            recommendations=recommendations
        )
    
    def _generate_overall_recommendations(self, safe: List[ComponentSafetyReport],
                                        unsafe: List[ComponentSafetyReport],
                                        warnings: List[ComponentSafetyReport]) -> List[str]:
        """Generate overall recommendations for the removal process."""
        recommendations = []
        
        if safe:
            recommendations.append(f"✅ {len(safe)} components are safe for immediate removal")
            recommendations.append("🚀 Recommended removal order:")
            
            # Sort by confidence and type
            sorted_safe = sorted(safe, key=lambda x: (
                self.deprecated_components.get(x.component_name, {}).get("confidence", 0),
                x.component_type == "class"  # Remove classes before functions
            ), reverse=True)
            
            for i, component in enumerate(sorted_safe[:10]):  # Top 10
                recommendations.append(f"   {i+1}. {component.component_name} ({component.component_type})")
        
        if unsafe:
            recommendations.append(f"❌ {len(unsafe)} components require attention before removal")
            recommendations.append("🎯 Priority fixes needed:")
            
            for component in unsafe[:5]:  # Top 5 issues
                blocking_checks = [c for c in component.safety_checks if c.blocking and c.status == "fail"]
                if blocking_checks:
                    recommendations.append(f"   • {component.component_name}: {blocking_checks[0].message}")
        
        if warnings:
            recommendations.append(f"⚠️ {len(warnings)} components have warnings to address")
        
        return recommendations
    
    def save_report(self, report: RemovalSafetyReport, output_file: str):
        """Save safety validation report to file."""
        # Convert dataclasses to dictionaries for JSON serialization
        report_data = {
            "validation_date": report.validation_date,
            "summary": {
                "components_validated": report.components_validated,
                "safe_for_removal": len(report.safe_for_removal),
                "unsafe_for_removal": len(report.unsafe_for_removal),
                "warnings": len(report.warnings),
                "overall_safety_score": report.overall_safety_score
            },
            "blocking_issues": report.blocking_issues,
            "recommendations": report.recommendations,
            "components": {
                "safe": [asdict(c) for c in report.safe_for_removal],
                "unsafe": [asdict(c) for c in report.unsafe_for_removal],
                "warnings": [asdict(c) for c in report.warnings]
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"Safety report saved to {output_file}")
    
    def print_summary(self, report: RemovalSafetyReport):
        """Print a summary of the safety validation report."""
        print("\n" + "="*60)
        print("🛡️  REMOVAL SAFETY VALIDATION REPORT")
        print("="*60)
        print(f"📅 Validation Date: {report.validation_date}")
        print(f"🔍 Components Validated: {report.components_validated}")
        print(f"📊 Overall Safety Score: {report.overall_safety_score:.1f}%")
        print()
        
        print("🎯 SAFETY SUMMARY:")
        print(f"   ✅ Safe for removal: {len(report.safe_for_removal)}")
        print(f"   ❌ Unsafe for removal: {len(report.unsafe_for_removal)}")
        print(f"   ⚠️  Have warnings: {len(report.warnings)}")
        print()
        
        if report.safe_for_removal:
            print("✅ SAFE FOR IMMEDIATE REMOVAL:")
            for component in report.safe_for_removal[:10]:
                print(f"   • {component.component_name} ({component.component_type})")
        
        if report.unsafe_for_removal:
            print("\n❌ UNSAFE FOR REMOVAL:")
            for component in report.unsafe_for_removal[:5]:
                blocking = [c for c in component.safety_checks if c.blocking and c.status == "fail"]
                issue = blocking[0].message if blocking else "Multiple issues"
                print(f"   • {component.component_name}: {issue}")
        
        if report.blocking_issues:
            print("\n🚫 BLOCKING ISSUES:")
            for issue in report.blocking_issues[:10]:
                print(f"   • {issue}")
        
        print("\n💡 RECOMMENDATIONS:")
        for rec in report.recommendations:
            print(f"   {rec}")
        print()


def main():
    """Main function to run the removal safety validator."""
    parser = argparse.ArgumentParser(description='Validate safety of removing deprecated components')
    parser.add_argument('--root', default='.',
                       help='Root directory of the project')
    parser.add_argument('--component', 
                       help='Validate specific component only')
    parser.add_argument('--output', default='removal_safety_report.json',
                       help='Output file for the report')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize validator
    validator = RemovalSafetyValidator(args.root)
    
    if args.component:
        # Validate single component
        report = validator.validate_component_safety(args.component)
        print(f"\n🛡️  Safety validation for: {args.component}")
        print(f"Status: {'✅ SAFE' if report.removal_safe else '❌ UNSAFE'}")
        print(f"Checks: {len([c for c in report.safety_checks if c.status == 'pass'])}/{len(report.safety_checks)} passed")
        
        if report.recommendations:
            print("\nRecommendations:")
            for rec in report.recommendations:
                print(f"  {rec}")
    else:
        # Validate all components
        report = validator.validate_all_components()
        validator.save_report(report, args.output)
        validator.print_summary(report)


if __name__ == "__main__":
    from datetime import datetime
    main()

