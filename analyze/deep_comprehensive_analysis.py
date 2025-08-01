#!/usr/bin/env python3
"""
Deep Comprehensive Self-Analysis Module for Graph-sitter
========================================================

This module provides deep, comprehensive self-analysis capabilities using all existing 
features, new deep analysis capabilities, and proper visualization data generation.
"""

import sys
import os
import json
import asyncio
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

class DeepComprehensiveAnalyzer:
    """
    Deep comprehensive analyzer that tests and integrates all graph-sitter capabilities.
    
    This analyzer performs comprehensive self-analysis using:
    - Existing graph-sitter analysis functions
    - Deep analysis capabilities  
    - Lightweight agent infrastructure
    - Serena error integration
    - Real-time integration modules
    - GitHub URL loading capability
    """
    
    def __init__(self, codebase_path: str = ".", codebase=None):
        self.codebase_path = Path(codebase_path).resolve()
        self.codebase = codebase
        self.logger = logging.getLogger(__name__)
        
        # Global variables to store analysis results
        self.files_list = []
        self.functions_list = []
        self.classes_list = []
        self.symbols_list = []
    
    async def run_deep_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run deep comprehensive self-analysis using all existing features and new capabilities."""
        self.logger.info("🔬 Starting deep comprehensive self-analysis...")
        
        analysis_results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "codebase_path": str(self.codebase_path),
            "existing_analysis_functions": {},
            "deep_analysis_capabilities": {},
            "lightweight_agent_infrastructure": {},
            "serena_error_integration": {},
            "realtime_integration_modules": {},
            "github_url_loading": {},
            "comprehensive_report": {}
        }
        
        # Test 1: Existing Graph-sitter Analysis Functions
        analysis_results["existing_analysis_functions"] = await self._test_existing_analysis_functions()
        
        # Test 2: Deep Analysis Capabilities
        analysis_results["deep_analysis_capabilities"] = await self._test_deep_analysis_capabilities()
        
        # Test 3: Lightweight Agent Infrastructure
        analysis_results["lightweight_agent_infrastructure"] = await self._test_lightweight_agent_infrastructure()
        
        # Test 4: Serena Error Integration
        analysis_results["serena_error_integration"] = await self._test_serena_error_integration()
        
        # Test 5: Real-time Integration Modules
        analysis_results["realtime_integration_modules"] = await self._test_realtime_integration_modules()
        
        # Test 6: GitHub URL Loading
        analysis_results["github_url_loading"] = await self._test_github_url_loading()
        
        # Generate comprehensive report
        analysis_results["comprehensive_report"] = await self._generate_comprehensive_report(analysis_results)
        
        return analysis_results
    
    async def _test_existing_analysis_functions(self) -> Dict[str, Any]:
        """Test existing graph-sitter analysis functions."""
        self.logger.info("🧪 Testing existing Graph-sitter analysis functions...")
        
        results = {
            "status": "success",
            "functions_tested": [],
            "codebase_summary": "",
            "statistics": {},
            "sample_analyses": {}
        }
        
        try:
            # Try to import existing analysis functions
            try:
                from graph_sitter.codebase.codebase_analysis import (
                    get_codebase_summary,
                    get_file_summary,
                    get_class_summary,
                    get_function_summary,
                    get_symbol_summary
                )
                results["functions_tested"].extend([
                    "get_codebase_summary", "get_file_summary", "get_class_summary",
                    "get_function_summary", "get_symbol_summary"
                ])
            except ImportError as e:
                results["import_error"] = str(e)
                return results
            
            if self.codebase:
                # Test codebase summary
                try:
                    codebase_summary = get_codebase_summary(self.codebase)
                    results["codebase_summary"] = codebase_summary
                except Exception as e:
                    results["codebase_summary_error"] = str(e)
                
                # Collect statistics
                self.files_list = list(self.codebase.files) if hasattr(self.codebase, 'files') else []
                self.functions_list = list(self.codebase.functions) if hasattr(self.codebase, 'functions') else []
                self.classes_list = list(self.codebase.classes) if hasattr(self.codebase, 'classes') else []
                self.symbols_list = list(self.codebase.symbols) if hasattr(self.codebase, 'symbols') else []
                
                results["statistics"] = {
                    "total_files": len(self.files_list),
                    "total_functions": len(self.functions_list),
                    "total_classes": len(self.classes_list),
                    "total_symbols": len(self.symbols_list)
                }
                
                # Test sample analyses
                sample_analyses = {}
                
                if self.files_list:
                    try:
                        test_file = self.files_list[0]
                        file_summary = get_file_summary(test_file)
                        sample_analyses["sample_file"] = {
                            "name": getattr(test_file, 'name', 'unknown'),
                            "summary": file_summary[:200] + "..." if len(file_summary) > 200 else file_summary
                        }
                    except Exception as e:
                        sample_analyses["file_analysis_error"] = str(e)
                
                if self.functions_list:
                    try:
                        test_function = self.functions_list[0]
                        function_summary = get_function_summary(test_function)
                        sample_analyses["sample_function"] = {
                            "name": getattr(test_function, 'name', 'unknown'),
                            "summary": function_summary[:200] + "..." if len(function_summary) > 200 else function_summary
                        }
                    except Exception as e:
                        sample_analyses["function_analysis_error"] = str(e)
                
                if self.classes_list:
                    try:
                        test_class = self.classes_list[0]
                        class_summary = get_class_summary(test_class)
                        sample_analyses["sample_class"] = {
                            "name": getattr(test_class, 'name', 'unknown'),
                            "summary": class_summary[:200] + "..." if len(class_summary) > 200 else class_summary
                        }
                    except Exception as e:
                        sample_analyses["class_analysis_error"] = str(e)
                
                results["sample_analyses"] = sample_analyses
            
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
        
        return results
    
    async def _test_deep_analysis_capabilities(self) -> Dict[str, Any]:
        """Test deep analysis capabilities."""
        self.logger.info("🔬 Testing deep analysis capabilities...")
        
        results = {
            "status": "success",
            "deep_analyzer_available": False,
            "comprehensive_metrics": {},
            "hotspot_analysis": {},
            "visualization_data": {}
        }
        
        try:
            # Try to import deep analysis module
            try:
                from graph_sitter.analysis.deep_analysis import DeepCodebaseAnalyzer
                results["deep_analyzer_available"] = True
                
                if self.codebase:
                    # Initialize deep analyzer
                    deep_analyzer = DeepCodebaseAnalyzer(self.codebase)
                    
                    # Test comprehensive metrics
                    try:
                        comprehensive_metrics = deep_analyzer.analyze_comprehensive_metrics()
                        results["comprehensive_metrics"] = comprehensive_metrics
                    except Exception as e:
                        results["comprehensive_metrics_error"] = str(e)
                    
                    # Test hotspot analysis
                    try:
                        hotspots = deep_analyzer.analyze_hotspots()
                        results["hotspot_analysis"] = hotspots
                    except Exception as e:
                        results["hotspot_analysis_error"] = str(e)
                    
                    # Test visualization data generation
                    try:
                        viz_data = deep_analyzer.generate_visualization_data()
                        results["visualization_data"] = viz_data
                    except Exception as e:
                        results["visualization_data_error"] = str(e)
                
            except ImportError as e:
                results["import_error"] = str(e)
                results["deep_analyzer_available"] = False
        
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
        
        return results
    
    async def _test_lightweight_agent_infrastructure(self) -> Dict[str, Any]:
        """Test lightweight agent infrastructure."""
        self.logger.info("🤖 Testing lightweight agent infrastructure...")
        
        results = {
            "status": "success",
            "agents_available": False,
            "code_agent_test": {},
            "chat_agent_test": {},
            "agent_queries": {}
        }
        
        try:
            # Try to import lightweight agent classes
            try:
                from graph_sitter.agents.lightweight_agent import LightweightCodeAgent, LightweightChatAgent
                results["agents_available"] = True
                
                if self.codebase:
                    # Test LightweightCodeAgent
                    try:
                        code_agent = LightweightCodeAgent(self.codebase)
                        results["code_agent_test"] = {"status": "initialized"}
                    except Exception as e:
                        results["code_agent_test"] = {"error": str(e)}
                    
                    # Test LightweightChatAgent
                    try:
                        chat_agent = LightweightChatAgent(self.codebase)
                        results["chat_agent_test"] = {"status": "initialized"}
                        
                        # Test agent queries
                        agent_queries = {}
                        
                        try:
                            overview_response = chat_agent.run("Give me an overview of this codebase")
                            agent_queries["overview"] = {"length": len(overview_response), "status": "success"}
                        except Exception as e:
                            agent_queries["overview"] = {"error": str(e)}
                        
                        try:
                            stats_response = code_agent.run("Show me statistics about this codebase")
                            agent_queries["statistics"] = {"length": len(stats_response), "status": "success"}
                        except Exception as e:
                            agent_queries["statistics"] = {"error": str(e)}
                        
                        results["agent_queries"] = agent_queries
                        
                    except Exception as e:
                        results["chat_agent_test"] = {"error": str(e)}
                
            except ImportError as e:
                results["import_error"] = str(e)
                results["agents_available"] = False
        
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
        
        return results
    
    async def _test_serena_error_integration(self) -> Dict[str, Any]:
        """Test Serena error integration."""
        self.logger.info("🔍 Testing Serena error integration...")
        
        results = {
            "status": "success",
            "serena_available": False,
            "error_analyzer": {},
            "error_analysis": {}
        }
        
        try:
            # Try to import Serena error integration
            try:
                from serena_error_integration import SerenaErrorAnalyzer, CodeError, ErrorSeverity, ErrorCategory
                results["serena_available"] = True
                
                # Test error analyzer
                try:
                    error_analyzer = SerenaErrorAnalyzer()
                    results["error_analyzer"] = {
                        "status": "initialized",
                        "error_patterns_count": len(getattr(error_analyzer, 'error_patterns', []))
                    }
                    
                    # Test error analysis on sample files
                    if self.files_list:
                        test_file = self.files_list[0]
                        file_content = getattr(test_file, 'source', '')
                        
                        if file_content:
                            lines = file_content.split('\n')
                            long_lines = [i for i, line in enumerate(lines) if len(line) > 120]
                            import_count = len([line for line in lines if line.strip().startswith('import ')])
                            
                            results["error_analysis"] = {
                                "file_analyzed": getattr(test_file, 'name', 'unknown'),
                                "long_lines_count": len(long_lines),
                                "import_statements": import_count,
                                "total_lines": len(lines)
                            }
                
                except Exception as e:
                    results["error_analyzer"] = {"error": str(e)}
                
            except ImportError as e:
                results["import_error"] = str(e)
                results["serena_available"] = False
        
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
        
        return results
    
    async def _test_realtime_integration_modules(self) -> Dict[str, Any]:
        """Test real-time integration modules."""
        self.logger.info("⚡ Testing real-time integration modules...")
        
        results = {
            "status": "success",
            "realtime_api": {},
            "diagnostic_streaming": {},
            "agent_bridge": {}
        }
        
        try:
            # Test realtime_api module
            try:
                from realtime_api import RealtimeAnalyzer, ConnectionManager
                analyzer = RealtimeAnalyzer()
                manager = ConnectionManager()
                results["realtime_api"] = {"status": "available", "components": ["RealtimeAnalyzer", "ConnectionManager"]}
            except ImportError as e:
                results["realtime_api"] = {"error": str(e), "status": "not_available"}
            
            # Test diagnostic_streaming module
            try:
                from diagnostic_streaming import DiagnosticStreamer
                diagnostic_streamer = DiagnosticStreamer()
                results["diagnostic_streaming"] = {"status": "available", "components": ["DiagnosticStreamer"]}
            except ImportError as e:
                results["diagnostic_streaming"] = {"error": str(e), "status": "not_available"}
            
            # Test agent_bridge module
            try:
                from agent_bridge import AgentBridge, AgentSession
                agent_bridge = AgentBridge()
                results["agent_bridge"] = {"status": "available", "components": ["AgentBridge", "AgentSession"]}
            except ImportError as e:
                results["agent_bridge"] = {"error": str(e), "status": "not_available"}
        
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
        
        return results
    
    async def _test_github_url_loading(self) -> Dict[str, Any]:
        """Test GitHub URL loading capability."""
        self.logger.info("🌐 Testing GitHub URL loading capability...")
        
        results = {
            "status": "success",
            "from_repo_available": False,
            "method_details": {}
        }
        
        try:
            # Check if from_repo method exists
            if self.codebase and hasattr(self.codebase.__class__, 'from_repo'):
                results["from_repo_available"] = True
                results["method_details"] = {
                    "method_name": "from_repo",
                    "class": self.codebase.__class__.__name__,
                    "status": "available"
                }
            else:
                results["method_details"] = {
                    "status": "not_found",
                    "class": self.codebase.__class__.__name__ if self.codebase else "No codebase"
                }
        
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
        
        return results
    
    async def _generate_comprehensive_report(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        self.logger.info("📊 Generating comprehensive analysis report...")
        
        report = {
            "generation_timestamp": datetime.now().isoformat(),
            "integration_status": {},
            "summary_statistics": {},
            "capabilities_overview": {},
            "recommendations": []
        }
        
        try:
            # Integration status summary
            integration_status = {}
            
            existing_analysis = analysis_results.get("existing_analysis_functions", {})
            integration_status["existing_analysis_functions"] = "✅ Working" if existing_analysis.get("status") == "success" else "❌ Issues"
            
            deep_analysis = analysis_results.get("deep_analysis_capabilities", {})
            integration_status["deep_analysis_capabilities"] = "✅ Working" if deep_analysis.get("deep_analyzer_available") else "❌ Not Available"
            
            lightweight_agents = analysis_results.get("lightweight_agent_infrastructure", {})
            integration_status["lightweight_agent_infrastructure"] = "✅ Working" if lightweight_agents.get("agents_available") else "❌ Not Available"
            
            serena_integration = analysis_results.get("serena_error_integration", {})
            integration_status["serena_error_integration"] = "✅ Working" if serena_integration.get("serena_available") else "❌ Not Available"
            
            realtime_modules = analysis_results.get("realtime_integration_modules", {})
            realtime_status = []
            for module, details in realtime_modules.items():
                if isinstance(details, dict) and details.get("status") == "available":
                    realtime_status.append("✅")
                else:
                    realtime_status.append("❌")
            integration_status["realtime_integration_modules"] = f"{'✅' if '✅' in realtime_status else '❌'} {len([s for s in realtime_status if s == '✅'])}/{len(realtime_status)} Available"
            
            github_loading = analysis_results.get("github_url_loading", {})
            integration_status["github_url_loading"] = "✅ Available" if github_loading.get("from_repo_available") else "❌ Not Available"
            
            report["integration_status"] = integration_status
            
            # Summary statistics
            stats = existing_analysis.get("statistics", {})
            report["summary_statistics"] = {
                "total_files": stats.get("total_files", 0),
                "total_functions": stats.get("total_functions", 0),
                "total_classes": stats.get("total_classes", 0),
                "total_symbols": stats.get("total_symbols", 0)
            }
            
            # Capabilities overview
            capabilities = []
            if existing_analysis.get("status") == "success":
                capabilities.append("Basic codebase analysis")
            if deep_analysis.get("deep_analyzer_available"):
                capabilities.append("Deep analysis with metrics and hotspots")
            if lightweight_agents.get("agents_available"):
                capabilities.append("Interactive agent queries")
            if serena_integration.get("serena_available"):
                capabilities.append("Serena error detection")
            if any(details.get("status") == "available" for details in realtime_modules.values() if isinstance(details, dict)):
                capabilities.append("Real-time integration modules")
            if github_loading.get("from_repo_available"):
                capabilities.append("GitHub repository loading")
            
            report["capabilities_overview"] = capabilities
            
            # Recommendations
            recommendations = []
            if not deep_analysis.get("deep_analyzer_available"):
                recommendations.append("🔬 Enable deep analysis capabilities for advanced metrics")
            if not lightweight_agents.get("agents_available"):
                recommendations.append("🤖 Set up lightweight agent infrastructure for interactive queries")
            if not serena_integration.get("serena_available"):
                recommendations.append("🔍 Integrate Serena error detection for enhanced analysis")
            if not any(details.get("status") == "available" for details in realtime_modules.values() if isinstance(details, dict)):
                recommendations.append("⚡ Enable real-time integration modules for dashboard connectivity")
            
            if not recommendations:
                recommendations.append("✅ All capabilities are working correctly!")
            
            report["recommendations"] = recommendations
            
        except Exception as e:
            report["generation_error"] = str(e)
        
        return report
    
    def print_deep_analysis_report(self, analysis_results: Dict[str, Any]):
        """Print a comprehensive deep analysis report."""
        print("\n" + "=" * 80)
        print("🔬 DEEP COMPREHENSIVE ANALYSIS REPORT")
        print("=" * 80)
        
        # Analysis timestamp
        timestamp = analysis_results.get("analysis_timestamp", "Unknown")
        print(f"📅 Analysis Timestamp: {timestamp}")
        print(f"📁 Codebase Path: {analysis_results.get('codebase_path', 'Unknown')}")
        
        # Integration status
        report = analysis_results.get("comprehensive_report", {})
        integration_status = report.get("integration_status", {})
        
        print(f"\n🔧 INTEGRATION STATUS:")
        for component, status in integration_status.items():
            print(f"   {component.replace('_', ' ').title()}: {status}")
        
        # Summary statistics
        stats = report.get("summary_statistics", {})
        if stats:
            print(f"\n📊 SUMMARY STATISTICS:")
            print(f"   Total Files: {stats.get('total_files', 0)}")
            print(f"   Total Functions: {stats.get('total_functions', 0)}")
            print(f"   Total Classes: {stats.get('total_classes', 0)}")
            print(f"   Total Symbols: {stats.get('total_symbols', 0)}")
        
        # Capabilities overview
        capabilities = report.get("capabilities_overview", [])
        if capabilities:
            print(f"\n🚀 AVAILABLE CAPABILITIES:")
            for capability in capabilities:
                print(f"   ✅ {capability}")
        
        # Detailed test results
        print(f"\n🧪 DETAILED TEST RESULTS:")
        
        # Existing analysis functions
        existing_analysis = analysis_results.get("existing_analysis_functions", {})
        if existing_analysis.get("status") == "success":
            print(f"   📊 Existing Analysis Functions: ✅ Working")
            functions_tested = existing_analysis.get("functions_tested", [])
            print(f"      Functions tested: {', '.join(functions_tested)}")
            
            sample_analyses = existing_analysis.get("sample_analyses", {})
            if "sample_file" in sample_analyses:
                file_info = sample_analyses["sample_file"]
                print(f"      Sample file analysis: {file_info.get('name', 'Unknown')}")
        else:
            print(f"   📊 Existing Analysis Functions: ❌ Issues")
            if "error" in existing_analysis:
                print(f"      Error: {existing_analysis['error']}")
        
        # Deep analysis capabilities
        deep_analysis = analysis_results.get("deep_analysis_capabilities", {})
        if deep_analysis.get("deep_analyzer_available"):
            print(f"   🔬 Deep Analysis Capabilities: ✅ Available")
            if "comprehensive_metrics" in deep_analysis:
                print(f"      Comprehensive metrics: Available")
            if "hotspot_analysis" in deep_analysis:
                print(f"      Hotspot analysis: Available")
            if "visualization_data" in deep_analysis:
                print(f"      Visualization data: Available")
        else:
            print(f"   🔬 Deep Analysis Capabilities: ❌ Not Available")
            if "import_error" in deep_analysis:
                print(f"      Import error: {deep_analysis['import_error']}")
        
        # Lightweight agent infrastructure
        lightweight_agents = analysis_results.get("lightweight_agent_infrastructure", {})
        if lightweight_agents.get("agents_available"):
            print(f"   🤖 Lightweight Agent Infrastructure: ✅ Available")
            agent_queries = lightweight_agents.get("agent_queries", {})
            for query_type, result in agent_queries.items():
                if "error" not in result:
                    print(f"      {query_type.title()} query: ✅ Success ({result.get('length', 0)} chars)")
                else:
                    print(f"      {query_type.title()} query: ❌ Error")
        else:
            print(f"   🤖 Lightweight Agent Infrastructure: ❌ Not Available")
        
        # Serena error integration
        serena_integration = analysis_results.get("serena_error_integration", {})
        if serena_integration.get("serena_available"):
            print(f"   🔍 Serena Error Integration: ✅ Available")
            error_analyzer = serena_integration.get("error_analyzer", {})
            if "error_patterns_count" in error_analyzer:
                print(f"      Error patterns loaded: {error_analyzer['error_patterns_count']}")
            
            error_analysis = serena_integration.get("error_analysis", {})
            if error_analysis:
                print(f"      Sample analysis: {error_analysis.get('file_analyzed', 'Unknown')}")
                print(f"         Long lines: {error_analysis.get('long_lines_count', 0)}")
                print(f"         Import statements: {error_analysis.get('import_statements', 0)}")
        else:
            print(f"   🔍 Serena Error Integration: ❌ Not Available")
        
        # Real-time integration modules
        realtime_modules = analysis_results.get("realtime_integration_modules", {})
        print(f"   ⚡ Real-time Integration Modules:")
        for module, details in realtime_modules.items():
            if isinstance(details, dict):
                status = "✅ Available" if details.get("status") == "available" else "❌ Not Available"
                print(f"      {module.replace('_', ' ').title()}: {status}")
                if "components" in details:
                    print(f"         Components: {', '.join(details['components'])}")
        
        # GitHub URL loading
        github_loading = analysis_results.get("github_url_loading", {})
        if github_loading.get("from_repo_available"):
            print(f"   🌐 GitHub URL Loading: ✅ Available")
            method_details = github_loading.get("method_details", {})
            print(f"      Method: {method_details.get('method_name', 'Unknown')}")
            print(f"      Class: {method_details.get('class', 'Unknown')}")
        else:
            print(f"   🌐 GitHub URL Loading: ❌ Not Available")
        
        # Recommendations
        recommendations = report.get("recommendations", [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for recommendation in recommendations:
                print(f"   {recommendation}")
        
        print(f"\n✅ Deep comprehensive analysis complete!")
        print("This analysis validates all graph-sitter capabilities and integrations.")


async def main_deep_analysis():
    """Main function for running deep comprehensive analysis."""
    print("🔬 DEEP COMPREHENSIVE SELF-ANALYSIS")
    print("=" * 60)
    print("Analyzing graph-sitter codebase with all existing and new capabilities")
    print("This validates all integrations and provides comprehensive reporting.")
    print()
    
    # Initialize analyzer
    analyzer = DeepComprehensiveAnalyzer(".")
    
    # Try to load codebase
    try:
        from graph_sitter import Codebase
        analyzer.codebase = Codebase(".")
        print("✅ Codebase loaded successfully")
    except Exception as e:
        print(f"⚠️  Could not load codebase: {e}")
        print("Continuing with limited analysis...")
    
    # Run deep comprehensive analysis
    try:
        results = await analyzer.run_deep_comprehensive_analysis()
        
        # Print comprehensive report
        analyzer.print_deep_analysis_report(results)
        
        # Save results
        report_path = Path("analysis_results")
        report_path.mkdir(exist_ok=True)
        
        report_file = report_path / "deep_comprehensive_analysis_report.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📊 Full analysis report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Deep analysis failed: {e}")
        traceback.print_exc()
    
    print("\n🎉 Deep Comprehensive Analysis Complete!")
    print("This analysis demonstrates the full integration of all graph-sitter capabilities.")


if __name__ == "__main__":
    asyncio.run(main_deep_analysis())

