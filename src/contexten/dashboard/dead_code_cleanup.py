"""
Dead Code Cleanup Script
Based on the comprehensive analysis from PR #141
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DeadCodeCleaner:
    """
    Safe dead code cleanup based on comprehensive analysis
    """
    
    def __init__(self, project_root: str, backup_dir: str = None):
        self.project_root = Path(project_root)
        self.backup_dir = Path(backup_dir) if backup_dir else self.project_root / "dead_code_backup"
        self.cleanup_log = []
        
    def create_backup(self, files_to_backup: List[str]):
        """Create backup of files before deletion"""
        try:
            self.backup_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_subdir = self.backup_dir / f"backup_{timestamp}"
            backup_subdir.mkdir(exist_ok=True)
            
            for file_path in files_to_backup:
                source = self.project_root / file_path
                if source.exists():
                    # Preserve directory structure in backup
                    relative_path = Path(file_path)
                    backup_path = backup_subdir / relative_path
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    shutil.copy2(source, backup_path)
                    logger.info(f"Backed up: {file_path}")
            
            return backup_subdir
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise
    
    def safe_remove_files(self, files_to_remove: List[str], create_backup: bool = True):
        """Safely remove files with backup"""
        try:
            if create_backup:
                backup_location = self.create_backup(files_to_remove)
                logger.info(f"Backup created at: {backup_location}")
            
            removed_files = []
            for file_path in files_to_remove:
                source = self.project_root / file_path
                if source.exists():
                    source.unlink()
                    removed_files.append(file_path)
                    logger.info(f"Removed: {file_path}")
                    
                    self.cleanup_log.append({
                        "action": "removed",
                        "file": file_path,
                        "timestamp": datetime.now().isoformat()
                    })
            
            return removed_files
            
        except Exception as e:
            logger.error(f"Error removing files: {e}")
            raise
    
    def cleanup_phase_1_safe_removals(self):
        """
        Phase 1: Safe removals (Low Risk)
        Based on PR #141 analysis
        """
        safe_files = [
            # Prompt files - unused prompt templates
            "src/contexten/agents/tools/relace_edit_prompts.py",
            "src/contexten/agents/tools/semantic_edit_prompts.py",
            
            # Render utilities - unused rendering
            "src/contexten/cli/commands/run/render.py",
            
            # Duplicate orchestration - remove duplicate
            "src/contexten/orchestration/prefect_client.py"
        ]
        
        logger.info("Starting Phase 1: Safe removals")
        existing_files = [f for f in safe_files if (self.project_root / f).exists()]
        
        if existing_files:
            removed = self.safe_remove_files(existing_files)
            logger.info(f"Phase 1 complete. Removed {len(removed)} files.")
            return removed
        else:
            logger.info("Phase 1: No files to remove")
            return []
    
    def cleanup_phase_2_extension_cleanup(self):
        """
        Phase 2: Extension cleanup (Medium Risk)
        Remove duplicates and unused extensions
        """
        extension_files = [
            # Linear duplicates - old implementations
            "src/contexten/extensions/linear/linearevents.py",  # If superseded by new version
            "src/contexten/extensions/linear/webhook_processor.py",  # If duplicate
            
            # GitHub duplicates - consolidate components
            "src/contexten/extensions/github/events/manager.py",  # If duplicate
            "src/contexten/extensions/github/webhook/processor.py",  # If duplicate
            
            # Experimental extensions - review necessity
            "src/contexten/extensions/modal/base.py",
            "src/contexten/extensions/modal/request_util.py",
        ]
        
        logger.info("Starting Phase 2: Extension cleanup")
        existing_files = [f for f in extension_files if (self.project_root / f).exists()]
        
        if existing_files:
            # More careful approach - ask for confirmation
            logger.warning(f"Phase 2 will remove {len(existing_files)} extension files")
            logger.warning("These may impact functionality. Proceed with caution.")
            
            removed = self.safe_remove_files(existing_files)
            logger.info(f"Phase 2 complete. Removed {len(removed)} files.")
            return removed
        else:
            logger.info("Phase 2: No files to remove")
            return []
    
    def validate_agent_tools(self):
        """
        Validate that essential agent tools are NOT removed
        These were incorrectly flagged as dead code in previous analysis
        """
        essential_tools = [
            "src/contexten/agents/tools/edit_file.py",
            "src/contexten/agents/tools/view_file.py",
            "src/contexten/agents/tools/move_symbol.py",
            "src/contexten/agents/tools/link_annotation.py",
            "src/contexten/agents/langchain/utils/custom_tool_node.py",
            "src/contexten/agents/tools/commit.py",
            "src/contexten/agents/tools/create_file.py",
            "src/contexten/agents/tools/delete_file.py",
            "src/contexten/agents/tools/list_directory.py",
            "src/contexten/agents/tools/rename_file.py",
            "src/contexten/agents/tools/run_codemod.py",
            "src/contexten/agents/tools/github/create_pr.py",
            "src/contexten/agents/tools/github/create_pr_comment.py",
            "src/contexten/agents/tools/github/create_pr_review_comment.py",
            "src/contexten/agents/tools/github/search.py"
        ]
        
        missing_tools = []
        for tool_path in essential_tools:
            if not (self.project_root / tool_path).exists():
                missing_tools.append(tool_path)
        
        if missing_tools:
            logger.error("CRITICAL: Essential agent tools are missing!")
            logger.error("Missing tools:")
            for tool in missing_tools:
                logger.error(f"  - {tool}")
            logger.error("These tools are essential for agent functionality!")
            return False
        else:
            logger.info("✅ All essential agent tools are present")
            return True
    
    def analyze_import_usage(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze if a file is imported or used elsewhere
        """
        try:
            file_path = Path(file_path)
            module_name = file_path.stem
            
            # Search for imports of this module
            import_patterns = [
                f"from {module_name} import",
                f"import {module_name}",
                f"from .{module_name} import",
                f"from ..{module_name} import"
            ]
            
            usage_found = False
            usage_locations = []
            
            # Search through all Python files
            for py_file in self.project_root.rglob("*.py"):
                if py_file == file_path:
                    continue
                
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for pattern in import_patterns:
                        if pattern in content:
                            usage_found = True
                            usage_locations.append(str(py_file))
                            break
                            
                except Exception as e:
                    logger.warning(f"Could not read {py_file}: {e}")
            
            return {
                "file": str(file_path),
                "usage_found": usage_found,
                "usage_locations": usage_locations,
                "confidence": "high" if not usage_found else "low"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing import usage for {file_path}: {e}")
            return {"error": str(e)}
    
    def generate_cleanup_report(self) -> Dict[str, Any]:
        """Generate comprehensive cleanup report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "backup_location": str(self.backup_dir),
            "cleanup_log": self.cleanup_log,
            "essential_tools_validated": self.validate_agent_tools(),
            "recommendations": [
                "Always test functionality after cleanup",
                "Keep backups for at least 30 days",
                "Monitor for any broken imports or functionality",
                "Run comprehensive tests after cleanup"
            ]
        }
        
        return report
    
    def save_cleanup_report(self, report: Dict[str, Any]):
        """Save cleanup report to file"""
        try:
            report_file = self.project_root / "dead_code_cleanup_report.json"
            import json
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Cleanup report saved to: {report_file}")
            
        except Exception as e:
            logger.error(f"Error saving cleanup report: {e}")

def main():
    """Main cleanup function"""
    logging.basicConfig(level=logging.INFO)
    
    # Initialize cleaner
    project_root = os.getcwd()  # Assume running from project root
    cleaner = DeadCodeCleaner(project_root)
    
    logger.info("Starting dead code cleanup based on PR #141 analysis")
    
    # Validate essential tools first
    if not cleaner.validate_agent_tools():
        logger.error("Essential agent tools validation failed. Aborting cleanup.")
        return
    
    # Phase 1: Safe removals
    logger.info("=" * 50)
    phase1_removed = cleaner.cleanup_phase_1_safe_removals()
    
    # Phase 2: Extension cleanup (with caution)
    logger.info("=" * 50)
    logger.warning("Phase 2 requires manual confirmation due to medium risk")
    response = input("Proceed with Phase 2 extension cleanup? (y/N): ")
    
    if response.lower() == 'y':
        phase2_removed = cleaner.cleanup_phase_2_extension_cleanup()
    else:
        logger.info("Phase 2 skipped by user")
        phase2_removed = []
    
    # Generate and save report
    logger.info("=" * 50)
    report = cleaner.generate_cleanup_report()
    cleaner.save_cleanup_report(report)
    
    # Summary
    total_removed = len(phase1_removed) + len(phase2_removed)
    logger.info(f"Cleanup complete. Total files removed: {total_removed}")
    logger.info(f"Phase 1 (safe): {len(phase1_removed)} files")
    logger.info(f"Phase 2 (extensions): {len(phase2_removed)} files")
    logger.info(f"Backup location: {cleaner.backup_dir}")
    
    if total_removed > 0:
        logger.info("IMPORTANT: Test all functionality after cleanup!")
        logger.info("If issues arise, restore from backup directory")

if __name__ == "__main__":
    main()

