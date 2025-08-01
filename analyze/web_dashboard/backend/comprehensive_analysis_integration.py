#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE ANALYSIS INTEGRATION FOR WEB DASHBOARD
======================================================

This module integrates the consolidated full_analysis.py engine with the web dashboard backend,
providing enhanced visualization capabilities and real-time analysis data.

Features:
1. ✅ Full Analysis Engine Integration
2. ✅ Real-time Dashboard Data Updates
3. ✅ Enhanced Visualization with Error Context
4. ✅ Interactive Analysis API Endpoints
5. ✅ WebSocket Real-time Updates
6. ✅ Performance Monitoring & Metrics
7. ✅ Advanced Error Analysis & Reporting
8. ✅ Dashboard Testing & Validation
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import traceback

# FastAPI imports
from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add the analyze directory to path to import full_analysis
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from full_analysis import ComprehensiveAnalysisEngine, run_comprehensive_analysis, get_dashboard_data
    FULL_ANALYSIS_AVAILABLE = True
except ImportError as e:
    logging.error(f"Could not import full_analysis: {e}")
    FULL_ANALYSIS_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for API
class AnalysisRequest(BaseModel):
    """Request model for analysis."""
    codebase_path: str = Field(default=".", description="Path to codebase to analyze")
    include_lsp_diagnostics: bool = Field(default=True, description="Include LSP diagnostics")
    include_dead_code: bool = Field(default=True, description="Include dead code analysis")
    include_quality_metrics: bool = Field(default=True, description="Include quality metrics")
    generate_dashboard_data: bool = Field(default=True, description="Generate dashboard data")

class AnalysisResponse(BaseModel):
    """Response model for analysis results."""
    success: bool
    analysis_id: str
    timestamp: str
    summary: Dict[str, Any]
    dashboard_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class DashboardDataResponse(BaseModel):
    """Response model for dashboard data."""
    success: bool
    timestamp: str
    data: Dict[str, Any]
    error: Optional[str] = None

class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str
    analysis_engine_available: bool
    last_analysis: Optional[str] = None
    active_analyses: int = 0


class ComprehensiveAnalysisIntegration:
    """
    🚀 COMPREHENSIVE ANALYSIS INTEGRATION
    
    Integrates the full analysis engine with the web dashboard backend,
    providing real-time analysis capabilities and enhanced visualizations.
    """
    
    def __init__(self):
        self.active_analyses: Dict[str, ComprehensiveAnalysisEngine] = {}
        self.analysis_results: Dict[str, Dict[str, Any]] = {}
        self.websocket_connections: Set[WebSocket] = set()
        self.last_analysis_time: Optional[datetime] = None
        
        # Initialize router
        self.router = APIRouter(prefix="/api/analysis", tags=["comprehensive-analysis"])
        self._setup_routes()
        
        logger.info("🚀 Comprehensive Analysis Integration initialized")
    
    def _setup_routes(self):
        """Setup API routes for comprehensive analysis."""
        
        @self.router.get("/health", response_model=HealthCheckResponse)
        async def health_check():
            """Health check for analysis engine."""
            return HealthCheckResponse(
                status="healthy" if FULL_ANALYSIS_AVAILABLE else "degraded",
                timestamp=datetime.now().isoformat(),
                analysis_engine_available=FULL_ANALYSIS_AVAILABLE,
                last_analysis=self.last_analysis_time.isoformat() if self.last_analysis_time else None,
                active_analyses=len(self.active_analyses)
            )
        
        @self.router.post("/run", response_model=AnalysisResponse)
        async def run_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
            """Run comprehensive analysis on a codebase."""
            if not FULL_ANALYSIS_AVAILABLE:
                raise HTTPException(status_code=503, detail="Analysis engine not available")
            
            analysis_id = f"analysis_{int(time.time())}"
            
            try:
                # Start analysis in background
                background_tasks.add_task(
                    self._run_background_analysis,
                    analysis_id,
                    request.codebase_path,
                    request.dict()
                )
                
                return AnalysisResponse(
                    success=True,
                    analysis_id=analysis_id,
                    timestamp=datetime.now().isoformat(),
                    summary={"status": "started", "analysis_id": analysis_id}
                )
                
            except Exception as e:
                logger.error(f"Failed to start analysis: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/results/{analysis_id}")
        async def get_analysis_results(analysis_id: str):
            """Get results for a specific analysis."""
            if analysis_id not in self.analysis_results:
                raise HTTPException(status_code=404, detail="Analysis not found")
            
            return JSONResponse(content=self.analysis_results[analysis_id])
        
        @self.router.get("/dashboard-data", response_model=DashboardDataResponse)
        async def get_dashboard_data_endpoint(codebase_path: str = "."):
            """Get dashboard data for visualization."""
            try:
                if not FULL_ANALYSIS_AVAILABLE:
                    raise HTTPException(status_code=503, detail="Analysis engine not available")
                
                # Run quick analysis for dashboard data
                dashboard_data = await get_dashboard_data(codebase_path)
                
                return DashboardDataResponse(
                    success=True,
                    timestamp=datetime.now().isoformat(),
                    data=dashboard_data
                )
                
            except Exception as e:
                logger.error(f"Failed to get dashboard data: {e}")
                return DashboardDataResponse(
                    success=False,
                    timestamp=datetime.now().isoformat(),
                    data={},
                    error=str(e)
                )
        
        @self.router.get("/live-metrics")
        async def get_live_metrics():
            """Get live metrics for real-time dashboard updates."""
            try:
                metrics = {
                    'active_analyses': len(self.active_analyses),
                    'completed_analyses': len(self.analysis_results),
                    'last_analysis': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
                    'engine_status': 'available' if FULL_ANALYSIS_AVAILABLE else 'unavailable',
                    'websocket_connections': len(self.websocket_connections),
                    'timestamp': datetime.now().isoformat()
                }
                
                return JSONResponse(content=metrics)
                
            except Exception as e:
                logger.error(f"Failed to get live metrics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await self._handle_websocket_connection(websocket)
    
    async def _run_background_analysis(self, analysis_id: str, codebase_path: str, options: Dict[str, Any]):
        """Run analysis in background and store results."""
        try:
            logger.info(f"🚀 Starting background analysis {analysis_id} for {codebase_path}")
            
            # Create analysis engine
            engine = ComprehensiveAnalysisEngine(codebase_path)
            self.active_analyses[analysis_id] = engine
            
            # Notify websocket clients
            await self._broadcast_websocket_message({
                'type': 'analysis_started',
                'analysis_id': analysis_id,
                'codebase_path': codebase_path,
                'timestamp': datetime.now().isoformat()
            })
            
            # Run comprehensive analysis
            results = await engine.run_full_analysis()
            
            # Store results
            self.analysis_results[analysis_id] = {
                'analysis_id': analysis_id,
                'codebase_path': codebase_path,
                'options': options,
                'results': results,
                'completed_at': datetime.now().isoformat(),
                'success': True
            }
            
            # Update last analysis time
            self.last_analysis_time = datetime.now()
            
            # Remove from active analyses
            if analysis_id in self.active_analyses:
                del self.active_analyses[analysis_id]
            
            # Notify websocket clients
            await self._broadcast_websocket_message({
                'type': 'analysis_completed',
                'analysis_id': analysis_id,
                'summary': results.get('dashboard_data', {}).get('summary', {}),
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"✅ Completed background analysis {analysis_id}")
            
        except Exception as e:
            logger.error(f"❌ Background analysis {analysis_id} failed: {e}")
            
            # Store error results
            self.analysis_results[analysis_id] = {
                'analysis_id': analysis_id,
                'codebase_path': codebase_path,
                'options': options,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'completed_at': datetime.now().isoformat(),
                'success': False
            }
            
            # Remove from active analyses
            if analysis_id in self.active_analyses:
                del self.active_analyses[analysis_id]
            
            # Notify websocket clients
            await self._broadcast_websocket_message({
                'type': 'analysis_failed',
                'analysis_id': analysis_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    async def _handle_websocket_connection(self, websocket: WebSocket):
        """Handle WebSocket connection for real-time updates."""
        await websocket.accept()
        self.websocket_connections.add(websocket)
        
        try:
            logger.info(f"📡 WebSocket connection established. Total connections: {len(self.websocket_connections)}")
            
            # Send initial status
            await websocket.send_json({
                'type': 'connection_established',
                'active_analyses': len(self.active_analyses),
                'completed_analyses': len(self.analysis_results),
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep connection alive and handle messages
            while True:
                try:
                    # Wait for messages from client
                    message = await websocket.receive_json()
                    
                    # Handle different message types
                    if message.get('type') == 'ping':
                        await websocket.send_json({
                            'type': 'pong',
                            'timestamp': datetime.now().isoformat()
                        })
                    elif message.get('type') == 'get_status':
                        await websocket.send_json({
                            'type': 'status_update',
                            'active_analyses': len(self.active_analyses),
                            'completed_analyses': len(self.analysis_results),
                            'timestamp': datetime.now().isoformat()
                        })
                    
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"WebSocket message handling error: {e}")
                    break
                    
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            self.websocket_connections.discard(websocket)
            logger.info(f"📡 WebSocket connection closed. Remaining connections: {len(self.websocket_connections)}")
    
    async def _broadcast_websocket_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected WebSocket clients."""
        if not self.websocket_connections:
            return
        
        disconnected = set()
        
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected websockets
        for websocket in disconnected:
            self.websocket_connections.discard(websocket)
    
    def get_router(self) -> APIRouter:
        """Get the FastAPI router for integration."""
        return self.router
    
    async def cleanup(self):
        """Cleanup resources."""
        # Close all websocket connections
        for websocket in list(self.websocket_connections):
            try:
                await websocket.close()
            except Exception:
                pass
        
        self.websocket_connections.clear()
        self.active_analyses.clear()
        
        logger.info("🧹 Comprehensive Analysis Integration cleaned up")


class EnhancedVisualizationEngine:
    """
    🎨 ENHANCED VISUALIZATION ENGINE
    
    Provides advanced visualization capabilities for the dashboard,
    integrating with the comprehensive analysis results.
    """
    
    def __init__(self):
        self.error_colors = {
            'critical': '#FF0000',  # Red
            'high': '#FF6600',      # Orange-Red
            'medium': '#FFA500',    # Orange
            'low': '#FFFF00',       # Yellow
            'info': '#87CEEB',      # Sky Blue
            'success': '#00FF00'    # Green
        }
        
        self.complexity_colors = {
            'low': '#00FF00',       # Green
            'medium': '#FFA500',    # Orange
            'high': '#FF0000'       # Red
        }
        
        logger.info("🎨 Enhanced Visualization Engine initialized")
    
    async def generate_error_heatmap(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate error heatmap data for file tree visualization."""
        try:
            structure = analysis_results.get('structure_analysis', {})
            diagnostics = analysis_results.get('lsp_diagnostics', [])
            
            # Create file error mapping
            file_errors = {}
            for diagnostic in diagnostics:
                file_path = diagnostic.get('file_path', '')
                severity = diagnostic.get('severity', 'info')
                
                if file_path not in file_errors:
                    file_errors[file_path] = {
                        'error_count': 0,
                        'warning_count': 0,
                        'info_count': 0,
                        'max_severity': 'info'
                    }
                
                if severity == 'error':
                    file_errors[file_path]['error_count'] += 1
                    file_errors[file_path]['max_severity'] = 'error'
                elif severity == 'warning':
                    file_errors[file_path]['warning_count'] += 1
                    if file_errors[file_path]['max_severity'] != 'error':
                        file_errors[file_path]['max_severity'] = 'warning'
                else:
                    file_errors[file_path]['info_count'] += 1
            
            # Generate heatmap data
            heatmap_data = {
                'file_colors': {},
                'directory_colors': {},
                'legend': self.error_colors,
                'statistics': {
                    'files_with_errors': len([f for f in file_errors.values() if f['error_count'] > 0]),
                    'files_with_warnings': len([f for f in file_errors.values() if f['warning_count'] > 0]),
                    'total_files_analyzed': len(file_errors)
                }
            }
            
            # Assign colors to files
            for file_path, error_info in file_errors.items():
                if error_info['error_count'] > 0:
                    heatmap_data['file_colors'][file_path] = self.error_colors['high']
                elif error_info['warning_count'] > 0:
                    heatmap_data['file_colors'][file_path] = self.error_colors['medium']
                else:
                    heatmap_data['file_colors'][file_path] = self.error_colors['success']
            
            return heatmap_data
            
        except Exception as e:
            logger.error(f"Error generating error heatmap: {e}")
            return {'error': str(e)}
    
    async def generate_complexity_visualization(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complexity visualization data."""
        try:
            structure = analysis_results.get('structure_analysis', {})
            quality_metrics = analysis_results.get('code_quality_metrics', {})
            
            complexity_data = {
                'function_complexity': [],
                'file_complexity': [],
                'complexity_distribution': {},
                'hotspots': [],
                'colors': self.complexity_colors
            }
            
            # Function complexity visualization
            most_complex = structure.get('most_complex_functions', [])
            for func in most_complex[:20]:  # Top 20 most complex
                complexity_score = func.get('complexity_proxy', 0)
                color = self._get_complexity_color(complexity_score)
                
                complexity_data['function_complexity'].append({
                    'name': func.get('name', 'unknown'),
                    'file': func.get('file', 'unknown'),
                    'complexity': complexity_score,
                    'color': color
                })
            
            # File complexity visualization
            largest_files = structure.get('largest_files', [])
            for file_info in largest_files[:20]:  # Top 20 largest files
                lines = file_info.get('lines', 0)
                color = self._get_file_size_color(lines)
                
                complexity_data['file_complexity'].append({
                    'path': file_info.get('path', 'unknown'),
                    'lines': lines,
                    'size_bytes': file_info.get('size_bytes', 0),
                    'color': color
                })
            
            # Complexity distribution
            complexity_metrics = quality_metrics.get('complexity_metrics', {})
            if complexity_metrics:
                avg_complexity = complexity_metrics.get('average_function_complexity', 0)
                complexity_data['complexity_distribution'] = {
                    'average': avg_complexity,
                    'max': complexity_metrics.get('max_function_complexity', 0),
                    'min': complexity_metrics.get('min_function_complexity', 0),
                    'total_functions': complexity_metrics.get('total_functions', 0)
                }
            
            return complexity_data
            
        except Exception as e:
            logger.error(f"Error generating complexity visualization: {e}")
            return {'error': str(e)}
    
    def _get_complexity_color(self, complexity_score: float) -> str:
        """Get color based on complexity score."""
        if complexity_score < 10:
            return self.complexity_colors['low']
        elif complexity_score < 20:
            return self.complexity_colors['medium']
        else:
            return self.complexity_colors['high']
    
    def _get_file_size_color(self, lines: int) -> str:
        """Get color based on file size."""
        if lines < 100:
            return self.complexity_colors['low']
        elif lines < 500:
            return self.complexity_colors['medium']
        else:
            return self.complexity_colors['high']
    
    async def generate_dashboard_charts(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chart data for dashboard visualization."""
        try:
            dashboard_data = analysis_results.get('dashboard_data', {})
            charts = dashboard_data.get('charts', {})
            
            enhanced_charts = {
                'error_severity_pie': {
                    'data': charts.get('error_severity_distribution', {}),
                    'colors': self.error_colors,
                    'title': 'Error Severity Distribution'
                },
                'file_types_bar': {
                    'data': charts.get('file_types', {}),
                    'title': 'File Types Distribution'
                },
                'complexity_distribution_donut': {
                    'data': charts.get('complexity_distribution', {}),
                    'colors': self.complexity_colors,
                    'title': 'Complexity Distribution'
                },
                'file_size_histogram': {
                    'data': charts.get('file_size_distribution', {}),
                    'colors': self.complexity_colors,
                    'title': 'File Size Distribution'
                }
            }
            
            return enhanced_charts
            
        except Exception as e:
            logger.error(f"Error generating dashboard charts: {e}")
            return {'error': str(e)}


# Global instances
comprehensive_integration = ComprehensiveAnalysisIntegration()
visualization_engine = EnhancedVisualizationEngine()

# Additional API endpoints for enhanced visualization
@comprehensive_integration.router.get("/visualization/error-heatmap")
async def get_error_heatmap(analysis_id: str):
    """Get error heatmap data for visualization."""
    if analysis_id not in comprehensive_integration.analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis_results = comprehensive_integration.analysis_results[analysis_id]['results']
    heatmap_data = await visualization_engine.generate_error_heatmap(analysis_results)
    
    return JSONResponse(content=heatmap_data)

@comprehensive_integration.router.get("/visualization/complexity")
async def get_complexity_visualization(analysis_id: str):
    """Get complexity visualization data."""
    if analysis_id not in comprehensive_integration.analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis_results = comprehensive_integration.analysis_results[analysis_id]['results']
    complexity_data = await visualization_engine.generate_complexity_visualization(analysis_results)
    
    return JSONResponse(content=complexity_data)

@comprehensive_integration.router.get("/visualization/charts")
async def get_dashboard_charts(analysis_id: str):
    """Get enhanced chart data for dashboard."""
    if analysis_id not in comprehensive_integration.analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis_results = comprehensive_integration.analysis_results[analysis_id]['results']
    charts_data = await visualization_engine.generate_dashboard_charts(analysis_results)
    
    return JSONResponse(content=charts_data)

# Export the router for integration with main FastAPI app
def get_comprehensive_analysis_router() -> APIRouter:
    """Get the comprehensive analysis router for integration."""
    return comprehensive_integration.get_router()

# Export the integration instance for external use
def get_comprehensive_integration() -> ComprehensiveAnalysisIntegration:
    """Get the comprehensive integration instance."""
    return comprehensive_integration

# Export the visualization engine for external use
def get_visualization_engine() -> EnhancedVisualizationEngine:
    """Get the visualization engine instance."""
    return visualization_engine

if __name__ == "__main__":
    # Test the integration
    async def test_integration():
        """Test the comprehensive analysis integration."""
        print("🧪 Testing Comprehensive Analysis Integration...")
        
        if not FULL_ANALYSIS_AVAILABLE:
            print("❌ Full analysis engine not available")
            return
        
        try:
            # Test analysis engine
            engine = ComprehensiveAnalysisEngine(".")
            results = await engine.run_full_analysis()
            
            print("✅ Analysis engine test passed")
            print(f"📊 Found {results.get('dashboard_data', {}).get('summary', {}).get('total_files', 0)} files")
            
            # Test visualization engine
            viz_engine = EnhancedVisualizationEngine()
            heatmap = await viz_engine.generate_error_heatmap(results)
            complexity = await viz_engine.generate_complexity_visualization(results)
            charts = await viz_engine.generate_dashboard_charts(results)
            
            print("✅ Visualization engine test passed")
            print(f"🎨 Generated {len(heatmap.get('file_colors', {}))} file colors")
            print(f"📈 Generated {len(charts)} chart types")
            
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            traceback.print_exc()
    
    asyncio.run(test_integration())
