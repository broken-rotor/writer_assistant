#!/usr/bin/env python3
"""
Deprecated Component Usage Monitor

This script monitors the usage of deprecated components in production
to track migration progress and identify components safe for removal.

Features:
- Tracks API parameter usage patterns
- Monitors legacy context mode usage
- Generates usage reports and trends
- Alerts when deprecated components are used
- Provides migration progress metrics
"""

import os
import re
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class UsageMetric:
    """Represents usage data for a deprecated component."""
    component_name: str
    component_type: str  # 'parameter', 'class', 'function', 'service'
    usage_count: int
    last_used: Optional[datetime]
    usage_trend: str  # 'increasing', 'decreasing', 'stable'
    clients_using: List[str]
    removal_readiness: str  # 'ready', 'monitor', 'not_ready'


@dataclass
class MonitoringReport:
    """Complete monitoring report for deprecated components."""
    report_date: datetime
    total_components_monitored: int
    ready_for_removal: List[UsageMetric]
    requires_monitoring: List[UsageMetric]
    not_ready_for_removal: List[UsageMetric]
    migration_progress: Dict[str, float]  # percentage by category
    recommendations: List[str]


class DeprecatedUsageMonitor:
    """Monitors usage of deprecated components."""
    
    def __init__(self, log_directory: str = "/var/log/writer_assistant"):
        self.log_directory = Path(log_directory)
        self.deprecated_components = self._load_deprecated_components()
        self.usage_patterns = self._initialize_usage_patterns()
        
    def _load_deprecated_components(self) -> Dict[str, Dict[str, Any]]:
        """Load list of deprecated components from inventory."""
        # In a real implementation, this would load from the inventory file
        return {
            # API Parameters
            "systemPrompts": {
                "type": "parameter",
                "endpoints": ["generate_chapter", "character_feedback", "editor_review", 
                            "rater_feedback", "modify_chapter", "flesh_out"],
                "removal_phase": 3
            },
            "worldbuilding": {
                "type": "parameter", 
                "endpoints": ["generate_chapter", "character_feedback", "editor_review",
                            "rater_feedback", "modify_chapter", "flesh_out"],
                "removal_phase": 3
            },
            "storySummary": {
                "type": "parameter",
                "endpoints": ["generate_chapter", "character_feedback", "editor_review",
                            "rater_feedback", "modify_chapter", "flesh_out"], 
                "removal_phase": 3
            },
            "context_mode_legacy": {
                "type": "parameter",
                "endpoints": ["generate_chapter", "character_feedback", "editor_review",
                            "rater_feedback", "modify_chapter", "flesh_out"],
                "removal_phase": 3
            },
            
            # Services
            "ContextOptimizationService": {
                "type": "service",
                "file": "context_optimization.py",
                "removal_phase": 2
            },
            "WorldbuildingFollowupGenerator": {
                "type": "service", 
                "file": "worldbuilding_followup.py",
                "removal_phase": 1
            },
            "WorldbuildingClassifier": {
                "type": "service",
                "file": "worldbuilding_classifier.py", 
                "removal_phase": 1
            },
            
            # Functions
            "_process_legacy_context_for_chapter": {
                "type": "function",
                "file": "unified_context_processor.py",
                "removal_phase": 2
            },
            "_process_legacy_context_for_character": {
                "type": "function",
                "file": "unified_context_processor.py",
                "removal_phase": 2
            },
            
            # Classes
            "LegacyContextMapping": {
                "type": "class",
                "file": "context_models.py",
                "removal_phase": 4
            }
        }
    
    def _initialize_usage_patterns(self) -> Dict[str, List[str]]:
        """Initialize regex patterns for detecting deprecated component usage."""
        return {
            # API parameter patterns
            "systemPrompts": [
                r'"systemPrompts"\s*:',
                r'systemPrompts\s*=',
                r'system_prompts\s*='
            ],
            "worldbuilding": [
                r'"worldbuilding"\s*:',
                r'worldbuilding\s*=',
                r'worldbuilding\s*:'
            ],
            "storySummary": [
                r'"storySummary"\s*:',
                r'storySummary\s*=',
                r'story_summary\s*='
            ],
            "context_mode_legacy": [
                r'"context_mode"\s*:\s*"legacy"',
                r'context_mode\s*=\s*"legacy"'
            ],
            
            # Service usage patterns
            "ContextOptimizationService": [
                r'ContextOptimizationService\(',
                r'from.*context_optimization.*import',
                r'context_optimization\.ContextOptimizationService'
            ],
            "WorldbuildingFollowupGenerator": [
                r'WorldbuildingFollowupGenerator\(',
                r'from.*worldbuilding_followup.*import'
            ],
            
            # Function call patterns
            "_process_legacy_context_for_chapter": [
                r'_process_legacy_context_for_chapter\(',
                r'\.process_legacy_context_for_chapter\('
            ],
            
            # Class usage patterns
            "LegacyContextMapping": [
                r'LegacyContextMapping\(',
                r'from.*context_models.*import.*LegacyContextMapping'
            ]
        }
    
    def analyze_log_files(self, days_back: int = 7) -> Dict[str, UsageMetric]:
        """Analyze log files for deprecated component usage."""
        logger.info(f"Analyzing log files for the last {days_back} days...")
        
        usage_metrics = {}
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Initialize metrics for all deprecated components
        for component_name, component_info in self.deprecated_components.items():
            usage_metrics[component_name] = UsageMetric(
                component_name=component_name,
                component_type=component_info["type"],
                usage_count=0,
                last_used=None,
                usage_trend="stable",
                clients_using=[],
                removal_readiness="ready"
            )
        
        # Analyze log files (simulated - in real implementation would parse actual logs)
        log_files = self._get_log_files(start_date, end_date)
        
        for log_file in log_files:
            self._analyze_single_log_file(log_file, usage_metrics)
        
        # Calculate trends and readiness
        for metric in usage_metrics.values():
            metric.usage_trend = self._calculate_trend(metric)
            metric.removal_readiness = self._assess_removal_readiness(metric)
        
        return usage_metrics
    
    def _get_log_files(self, start_date: datetime, end_date: datetime) -> List[Path]:
        """Get list of log files within date range."""
        log_files = []
        
        if not self.log_directory.exists():
            logger.warning(f"Log directory {self.log_directory} does not exist")
            return log_files
        
        # Find log files within date range
        for log_file in self.log_directory.glob("*.log"):
            # In real implementation, would check file modification dates
            log_files.append(log_file)
        
        return log_files
    
    def _analyze_single_log_file(self, log_file: Path, usage_metrics: Dict[str, UsageMetric]):
        """Analyze a single log file for deprecated component usage."""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check each deprecated component
            for component_name, patterns in self.usage_patterns.items():
                if component_name not in usage_metrics:
                    continue
                
                metric = usage_metrics[component_name]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        metric.usage_count += 1
                        metric.last_used = datetime.now()  # In real implementation, parse timestamp
                        
                        # Extract client information (simulated)
                        client_id = self._extract_client_id(content, match.start())
                        if client_id and client_id not in metric.clients_using:
                            metric.clients_using.append(client_id)
        
        except Exception as e:
            logger.error(f"Error analyzing log file {log_file}: {e}")
    
    def _extract_client_id(self, content: str, position: int) -> Optional[str]:
        """Extract client ID from log content around the match position."""
        # Simulated client ID extraction
        # In real implementation, would parse actual log format
        return f"client_{hash(content[max(0, position-100):position+100]) % 1000}"
    
    def _calculate_trend(self, metric: UsageMetric) -> str:
        """Calculate usage trend for a component."""
        # Simulated trend calculation
        # In real implementation, would compare with historical data
        if metric.usage_count == 0:
            return "decreasing"
        elif metric.usage_count < 10:
            return "decreasing"
        elif metric.usage_count < 100:
            return "stable"
        else:
            return "increasing"
    
    def _assess_removal_readiness(self, metric: UsageMetric) -> str:
        """Assess if a component is ready for removal."""
        if metric.usage_count == 0:
            return "ready"
        elif metric.usage_count < 10 and metric.usage_trend == "decreasing":
            return "monitor"
        else:
            return "not_ready"
    
    def generate_report(self, usage_metrics: Dict[str, UsageMetric]) -> MonitoringReport:
        """Generate comprehensive monitoring report."""
        ready_for_removal = []
        requires_monitoring = []
        not_ready_for_removal = []
        
        # Categorize components by readiness
        for metric in usage_metrics.values():
            if metric.removal_readiness == "ready":
                ready_for_removal.append(metric)
            elif metric.removal_readiness == "monitor":
                requires_monitoring.append(metric)
            else:
                not_ready_for_removal.append(metric)
        
        # Calculate migration progress by phase
        migration_progress = self._calculate_migration_progress(usage_metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(usage_metrics)
        
        return MonitoringReport(
            report_date=datetime.now(),
            total_components_monitored=len(usage_metrics),
            ready_for_removal=ready_for_removal,
            requires_monitoring=requires_monitoring,
            not_ready_for_removal=not_ready_for_removal,
            migration_progress=migration_progress,
            recommendations=recommendations
        )
    
    def _calculate_migration_progress(self, usage_metrics: Dict[str, UsageMetric]) -> Dict[str, float]:
        """Calculate migration progress by removal phase."""
        phase_totals = defaultdict(int)
        phase_ready = defaultdict(int)
        
        for component_name, metric in usage_metrics.items():
            component_info = self.deprecated_components.get(component_name, {})
            phase = component_info.get("removal_phase", 1)
            
            phase_totals[f"phase_{phase}"] += 1
            if metric.removal_readiness == "ready":
                phase_ready[f"phase_{phase}"] += 1
        
        progress = {}
        for phase, total in phase_totals.items():
            ready = phase_ready.get(phase, 0)
            progress[phase] = (ready / total) * 100 if total > 0 else 100
        
        return progress
    
    def _generate_recommendations(self, usage_metrics: Dict[str, UsageMetric]) -> List[str]:
        """Generate actionable recommendations based on usage data."""
        recommendations = []
        
        # Count components by readiness
        ready_count = sum(1 for m in usage_metrics.values() if m.removal_readiness == "ready")
        monitor_count = sum(1 for m in usage_metrics.values() if m.removal_readiness == "monitor")
        not_ready_count = sum(1 for m in usage_metrics.values() if m.removal_readiness == "not_ready")
        
        if ready_count > 0:
            recommendations.append(f"✅ {ready_count} components are ready for immediate removal")
        
        if monitor_count > 0:
            recommendations.append(f"⚠️ {monitor_count} components require continued monitoring")
        
        if not_ready_count > 0:
            recommendations.append(f"❌ {not_ready_count} components are not ready for removal - focus on client migration")
        
        # Specific recommendations for high-usage components
        high_usage_components = [
            m for m in usage_metrics.values() 
            if m.usage_count > 100 and m.removal_readiness == "not_ready"
        ]
        
        if high_usage_components:
            recommendations.append("🎯 Priority migration targets:")
            for component in high_usage_components[:5]:  # Top 5
                recommendations.append(f"   • {component.component_name}: {component.usage_count} uses by {len(component.clients_using)} clients")
        
        return recommendations
    
    def save_report(self, report: MonitoringReport, output_file: str):
        """Save monitoring report to file."""
        report_data = {
            "report_date": report.report_date.isoformat(),
            "summary": {
                "total_components": report.total_components_monitored,
                "ready_for_removal": len(report.ready_for_removal),
                "requires_monitoring": len(report.requires_monitoring),
                "not_ready": len(report.not_ready_for_removal)
            },
            "migration_progress": report.migration_progress,
            "recommendations": report.recommendations,
            "components": {
                "ready_for_removal": [asdict(m) for m in report.ready_for_removal],
                "requires_monitoring": [asdict(m) for m in report.requires_monitoring],
                "not_ready_for_removal": [asdict(m) for m in report.not_ready_for_removal]
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"Report saved to {output_file}")
    
    def print_summary(self, report: MonitoringReport):
        """Print a summary of the monitoring report."""
        print("\n" + "="*60)
        print("📊 DEPRECATED COMPONENT USAGE REPORT")
        print("="*60)
        print(f"📅 Report Date: {report.report_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Components Monitored: {report.total_components_monitored}")
        print()
        
        print("📈 MIGRATION PROGRESS BY PHASE:")
        for phase, progress in report.migration_progress.items():
            print(f"   {phase.replace('_', ' ').title()}: {progress:.1f}% ready")
        print()
        
        print("🎯 REMOVAL READINESS:")
        print(f"   ✅ Ready for removal: {len(report.ready_for_removal)}")
        print(f"   ⚠️  Requires monitoring: {len(report.requires_monitoring)}")
        print(f"   ❌ Not ready: {len(report.not_ready_for_removal)}")
        print()
        
        if report.ready_for_removal:
            print("✅ READY FOR IMMEDIATE REMOVAL:")
            for metric in report.ready_for_removal[:10]:  # Top 10
                print(f"   • {metric.component_name} ({metric.component_type})")
        
        if report.not_ready_for_removal:
            print("\n❌ HIGH USAGE COMPONENTS (NOT READY):")
            sorted_components = sorted(report.not_ready_for_removal, 
                                     key=lambda x: x.usage_count, reverse=True)
            for metric in sorted_components[:5]:  # Top 5
                print(f"   • {metric.component_name}: {metric.usage_count} uses, {len(metric.clients_using)} clients")
        
        print("\n💡 RECOMMENDATIONS:")
        for rec in report.recommendations:
            print(f"   {rec}")
        print()


def main():
    """Main function to run the deprecated usage monitor."""
    parser = argparse.ArgumentParser(description='Monitor deprecated component usage')
    parser.add_argument('--log-dir', default='/var/log/writer_assistant',
                       help='Directory containing log files')
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days to analyze')
    parser.add_argument('--output', default='deprecated_usage_report.json',
                       help='Output file for the report')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize monitor
    monitor = DeprecatedUsageMonitor(args.log_dir)
    
    # Analyze usage
    usage_metrics = monitor.analyze_log_files(args.days)
    
    # Generate report
    report = monitor.generate_report(usage_metrics)
    
    # Save and display results
    monitor.save_report(report, args.output)
    monitor.print_summary(report)


if __name__ == "__main__":
    main()

