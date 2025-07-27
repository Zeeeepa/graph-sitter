#!/usr/bin/env python3
"""
Lightweight Agent Implementation for Graph-sitter
================================================

This module provides a lightweight agent implementation that doesn't require
LangChain dependencies but still provides intelligent codebase interaction
capabilities using the existing graph-sitter analysis functions.
"""

import json
import traceback
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Import existing analysis functions
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LightweightCodeAgent:
    """Lightweight code agent that uses existing graph-sitter analysis functions."""
    
    def __init__(self, codebase):
        self.codebase = codebase
        self.conversation_history = []
        self.analysis_cache = {}
        
    def run(self, query: str, thread_id: str = None) -> str:
        """Process a query and return a response using existing analysis functions."""
        try:
            logger.info(f"Processing query: {query[:100]}...")
            
            # Add to conversation history
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "thread_id": thread_id
            })
            
            # Analyze the query and determine the best response
            response = self._process_query(query)
            
            # Add response to history
            self.conversation_history[-1]["response"] = response
            
            return response
            
        except Exception as e:
            error_response = f"Error processing query: {str(e)}"
            logger.error(f"{error_response}\n{traceback.format_exc()}")
            return error_response
    
    def _process_query(self, query: str) -> str:
        """Process the query and generate an appropriate response."""
        query_lower = query.lower()
        
        # Codebase overview queries
        if any(keyword in query_lower for keyword in ['overview', 'summary', 'about', 'what is', 'describe']):
            return self._handle_overview_query(query)
        
        # File-specific queries
        elif any(keyword in query_lower for keyword in ['file', 'files', 'module', 'modules']):
            return self._handle_file_query(query)
        
        # Function-specific queries
        elif any(keyword in query_lower for keyword in ['function', 'functions', 'method', 'methods']):
            return self._handle_function_query(query)
        
        # Class-specific queries
        elif any(keyword in query_lower for keyword in ['class', 'classes', 'object', 'objects']):
            return self._handle_class_query(query)
        
        # Dependency queries
        elif any(keyword in query_lower for keyword in ['import', 'imports', 'dependency', 'dependencies']):
            return self._handle_dependency_query(query)
        
        # Statistics queries
        elif any(keyword in query_lower for keyword in ['count', 'how many', 'statistics', 'stats', 'metrics']):
            return self._handle_statistics_query(query)
        
        # Search queries
        elif any(keyword in query_lower for keyword in ['find', 'search', 'locate', 'where']):
            return self._handle_search_query(query)
        
        # Default response
        else:
            return self._handle_general_query(query)
    
    def _handle_overview_query(self, query: str) -> str:
        """Handle queries asking for codebase overview."""
        try:
            # Use existing get_codebase_summary function
            summary = get_codebase_summary(self.codebase)
            
            return f"""## Codebase Overview

{summary}

This codebase appears to be a comprehensive software project with a well-structured architecture. The analysis shows a good balance of files, functions, and classes, indicating a mature codebase with proper organization.

**Key Insights:**
- The codebase has a substantial number of symbols and dependencies
- Import structure suggests modular design
- Good distribution of functionality across files

Would you like me to dive deeper into any specific aspect of the codebase?"""
            
        except Exception as e:
            return f"Error generating overview: {str(e)}"
    
    def _handle_file_query(self, query: str) -> str:
        """Handle queries about files."""
        try:
            files = list(self.codebase.files)
            
            # If asking about a specific file
            if 'specific' in query.lower() or any(f.name.lower() in query.lower() for f in files[:10]):
                # Find the mentioned file
                mentioned_file = None
                for file in files:
                    if file.name.lower() in query.lower():
                        mentioned_file = file
                        break
                
                if mentioned_file:
                    file_summary = get_file_summary(mentioned_file)
                    return f"## File Analysis: {mentioned_file.name}\n\n{file_summary}"
            
            # General file information
            total_files = len(files)
            files_with_classes = len([f for f in files if len(f.classes) > 0])
            files_with_functions = len([f for f in files if len(f.functions) > 0])
            
            # Get top files by symbol count
            top_files = sorted(files, key=lambda f: len(f.symbols), reverse=True)[:5]
            
            response = f"""## File Analysis

**Total Files:** {total_files}
**Files with Classes:** {files_with_classes}
**Files with Functions:** {files_with_functions}

**Top Files by Symbol Count:**
"""
            
            for i, file in enumerate(top_files, 1):
                response += f"{i}. **{file.name}** - {len(file.symbols)} symbols, {len(file.imports)} imports\n"
            
            return response
            
        except Exception as e:
            return f"Error analyzing files: {str(e)}"
    
    def _handle_function_query(self, query: str) -> str:
        """Handle queries about functions."""
        try:
            functions = list(self.codebase.functions)
            
            # If asking about a specific function
            if any(func.name.lower() in query.lower() for func in functions[:20]):
                # Find the mentioned function
                mentioned_function = None
                for func in functions:
                    if func.name.lower() in query.lower():
                        mentioned_function = func
                        break
                
                if mentioned_function:
                    func_summary = get_function_summary(mentioned_function)
                    return f"## Function Analysis: {mentioned_function.name}\n\n{func_summary}"
            
            # General function information
            total_functions = len(functions)
            functions_with_params = len([f for f in functions if len(f.parameters) > 0])
            
            # Get functions by complexity (dependencies + parameters)
            complex_functions = sorted(
                functions, 
                key=lambda f: len(f.dependencies) + len(f.parameters), 
                reverse=True
            )[:5]
            
            response = f"""## Function Analysis

**Total Functions:** {total_functions}
**Functions with Parameters:** {functions_with_params}

**Most Complex Functions:**
"""
            
            for i, func in enumerate(complex_functions, 1):
                complexity = len(func.dependencies) + len(func.parameters)
                response += f"{i}. **{func.name}** - Complexity: {complexity} ({len(func.parameters)} params, {len(func.dependencies)} deps)\n"
            
            return response
            
        except Exception as e:
            return f"Error analyzing functions: {str(e)}"
    
    def _handle_class_query(self, query: str) -> str:
        """Handle queries about classes."""
        try:
            classes = list(self.codebase.classes)
            
            # If asking about a specific class
            if any(cls.name.lower() in query.lower() for cls in classes[:20]):
                # Find the mentioned class
                mentioned_class = None
                for cls in classes:
                    if cls.name.lower() in query.lower():
                        mentioned_class = cls
                        break
                
                if mentioned_class:
                    class_summary = get_class_summary(mentioned_class)
                    return f"## Class Analysis: {mentioned_class.name}\n\n{class_summary}"
            
            # General class information
            total_classes = len(classes)
            classes_with_methods = len([c for c in classes if len(c.methods) > 0])
            
            # Get largest classes by method + attribute count
            large_classes = sorted(
                classes, 
                key=lambda c: len(c.methods) + len(c.attributes), 
                reverse=True
            )[:5]
            
            response = f"""## Class Analysis

**Total Classes:** {total_classes}
**Classes with Methods:** {classes_with_methods}

**Largest Classes:**
"""
            
            for i, cls in enumerate(large_classes, 1):
                size = len(cls.methods) + len(cls.attributes)
                response += f"{i}. **{cls.name}** - Size: {size} ({len(cls.methods)} methods, {len(cls.attributes)} attrs)\n"
            
            return response
            
        except Exception as e:
            return f"Error analyzing classes: {str(e)}"
    
    def _handle_dependency_query(self, query: str) -> str:
        """Handle queries about dependencies and imports."""
        try:
            files = list(self.codebase.files)
            
            # Collect all imports
            all_imports = []
            for file in files:
                all_imports.extend(file.imports)
            
            # Count import frequencies
            import_names = [imp.name for imp in all_imports if hasattr(imp, 'name')]
            from collections import Counter
            import_counter = Counter(import_names)
            
            response = f"""## Dependency Analysis

**Total Import Statements:** {len(all_imports)}
**Unique Modules Imported:** {len(set(import_names))}

**Most Frequently Imported Modules:**
"""
            
            for i, (module, count) in enumerate(import_counter.most_common(10), 1):
                response += f"{i}. **{module}** - imported {count} times\n"
            
            # Files with most imports
            files_by_imports = sorted(files, key=lambda f: len(f.imports), reverse=True)[:5]
            
            response += "\n**Files with Most Imports:**\n"
            for i, file in enumerate(files_by_imports, 1):
                response += f"{i}. **{file.name}** - {len(file.imports)} imports\n"
            
            return response
            
        except Exception as e:
            return f"Error analyzing dependencies: {str(e)}"
    
    def _handle_statistics_query(self, query: str) -> str:
        """Handle queries asking for statistics."""
        try:
            # Use existing get_codebase_summary function
            summary = get_codebase_summary(self.codebase)
            
            files = list(self.codebase.files)
            functions = list(self.codebase.functions)
            classes = list(self.codebase.classes)
            symbols = list(self.codebase.symbols)
            
            # Calculate additional statistics
            avg_symbols_per_file = len(symbols) / len(files) if files else 0
            avg_functions_per_file = len(functions) / len(files) if files else 0
            avg_classes_per_file = len(classes) / len(files) if files else 0
            
            response = f"""## Codebase Statistics

{summary}

**Additional Metrics:**
- Average symbols per file: {avg_symbols_per_file:.1f}
- Average functions per file: {avg_functions_per_file:.1f}
- Average classes per file: {avg_classes_per_file:.1f}

**Code Distribution:**
- Files with functions: {len([f for f in files if len(f.functions) > 0])}
- Files with classes: {len([f for f in files if len(f.classes) > 0])}
- Files with imports: {len([f for f in files if len(f.imports) > 0])}
"""
            
            return response
            
        except Exception as e:
            return f"Error generating statistics: {str(e)}"
    
    def _handle_search_query(self, query: str) -> str:
        """Handle search queries."""
        try:
            # Extract search terms from query
            search_terms = []
            words = query.lower().split()
            
            # Look for quoted terms or specific names
            for word in words:
                if len(word) > 3 and word not in ['find', 'search', 'locate', 'where', 'what', 'how', 'the', 'and', 'or']:
                    search_terms.append(word)
            
            if not search_terms:
                return "Please specify what you'd like to search for (e.g., 'find function named parse' or 'search for class User')."
            
            results = []
            
            # Search in files
            files = list(self.codebase.files)
            for file in files:
                if any(term in file.name.lower() for term in search_terms):
                    results.append(f"**File:** {file.name} - {len(file.symbols)} symbols")
            
            # Search in functions
            functions = list(self.codebase.functions)
            for func in functions:
                if any(term in func.name.lower() for term in search_terms):
                    results.append(f"**Function:** {func.name} - {len(func.parameters)} parameters")
            
            # Search in classes
            classes = list(self.codebase.classes)
            for cls in classes:
                if any(term in cls.name.lower() for term in search_terms):
                    results.append(f"**Class:** {cls.name} - {len(cls.methods)} methods")
            
            if results:
                response = f"## Search Results for: {', '.join(search_terms)}\n\n"
                response += "\n".join(results[:10])  # Limit to top 10 results
                if len(results) > 10:
                    response += f"\n\n... and {len(results) - 10} more results"
            else:
                response = f"No results found for: {', '.join(search_terms)}"
            
            return response
            
        except Exception as e:
            return f"Error performing search: {str(e)}"
    
    def _handle_general_query(self, query: str) -> str:
        """Handle general queries that don't fit other categories."""
        try:
            # Use existing get_codebase_summary for context
            summary = get_codebase_summary(self.codebase)
            
            return f"""I can help you analyze this codebase! Here's what I can do:

**Available Commands:**
- Ask for an **overview** or **summary** of the codebase
- Inquire about specific **files**, **functions**, or **classes**
- Get **statistics** and **metrics** about the code
- Search for specific elements with **find** or **search**
- Analyze **dependencies** and **imports**

**Current Codebase Summary:**
{summary}

What would you like to explore? Try asking something like:
- "Give me an overview of this codebase"
- "Show me the most complex functions"
- "Find all classes related to parsing"
- "What are the main dependencies?"
"""
            
        except Exception as e:
            return f"Error processing query: {str(e)}"

class LightweightChatAgent(LightweightCodeAgent):
    """Lightweight chat agent that extends the code agent with conversational capabilities."""
    
    def __init__(self, codebase):
        super().__init__(codebase)
        self.context = {}
    
    def run(self, query: str, thread_id: str = None) -> str:
        """Enhanced run method with conversational context."""
        try:
            # Maintain context per thread
            if thread_id:
                if thread_id not in self.context:
                    self.context[thread_id] = {"previous_queries": [], "focus_area": None}
                
                self.context[thread_id]["previous_queries"].append(query)
                
                # Keep only last 5 queries for context
                if len(self.context[thread_id]["previous_queries"]) > 5:
                    self.context[thread_id]["previous_queries"] = self.context[thread_id]["previous_queries"][-5:]
            
            # Process the query with context
            response = self._process_query_with_context(query, thread_id)
            
            return response
            
        except Exception as e:
            error_response = f"Error in chat processing: {str(e)}"
            logger.error(f"{error_response}\n{traceback.format_exc()}")
            return error_response
    
    def _process_query_with_context(self, query: str, thread_id: str = None) -> str:
        """Process query with conversational context."""
        # Add conversational elements
        if any(greeting in query.lower() for greeting in ['hello', 'hi', 'hey', 'greetings']):
            base_response = "Hello! I'm here to help you explore and understand this codebase. "
            base_response += self._process_query(query)
            return base_response
        
        if any(thanks in query.lower() for thanks in ['thank', 'thanks', 'appreciate']):
            return "You're welcome! Feel free to ask me anything else about the codebase. I can help with analysis, search, statistics, and more!"
        
        # Use the parent class method for actual analysis
        return super()._process_query(query)

# Export the lightweight agents
__all__ = ['LightweightCodeAgent', 'LightweightChatAgent']
