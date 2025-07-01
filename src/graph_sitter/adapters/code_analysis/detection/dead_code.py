"""
🗑️ Dead Code Detection

Consolidated dead code detection from all existing tools.
"""

from typing import List, Dict, Any


class DeadCodeDetector:
    """Detector for unused/dead code"""
    
    def find_dead_code(self, codebase) -> List[str]:
        """Find dead code in codebase"""
        dead_code = []
        
        try:
            if hasattr(codebase, 'functions'):
                for function in codebase.functions:
                    if hasattr(function, 'usages') and len(function.usages) == 0:
                        dead_code.append(f"function:{function.name}")
            
            if hasattr(codebase, 'classes'):
                for cls in codebase.classes:
                    if hasattr(cls, 'usages') and len(cls.usages) == 0:
                        dead_code.append(f"class:{cls.name}")
        
        except Exception:
            # Handle errors gracefully
            pass
        
        return dead_code


def find_dead_code(codebase) -> List[str]:
    """Find dead code in codebase"""
    detector = DeadCodeDetector()
    return detector.find_dead_code(codebase)

