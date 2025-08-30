"""
Production-ready FastAPI backend for comprehensive code analytics using graph-sitter integration.
Provides deep codebase analysis including error detection, dead code analysis, and visualization.
"""

import os
import tempfile
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import math
import logging
from functools import lru_cache
import asyncio
import networkx as nx

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator, ConfigDict
import uvicorn

# Check if graph-sitter is available
try:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.codebase.codebase_analysis import (
        get_codebase_summary,
        get_file_summary,
        get_class_summary,
        get_function_summary,
        get_symbol_summary,
    )
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("graph_sitter_backend")

# Application version
__version__ = "2.0.0"

# Initialize FastAPI app with metadata
app = FastAPI(
    title="Graph-Sitter Code Analytics API",
    description="Comprehensive codebase analysis using graph-sitter",
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for analysis results
analysis_cache: Dict[str, Dict] = {}

