#!/usr/bin/env python3
"""
Dependency Analysis Script for Codegen to Contexten Migration

This script analyzes all dependencies and references to codegen_app and CodegenApp
throughout the codebase to support the migration strategy.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

@dataclass
class ImportReference:
    file_path: str
    line_number: int
    line_content: str
    import_type: str  # 'direct', 'from', 'usage'
    module_path: str
    symbol_name: str

@dataclass
class FileAnalysis:
    file_path: str
    total_references: int
    import_references: List[ImportReference]
    usage_references: List[ImportReference]
    file_type: str  # 'python', 'markdown', 'yaml', 'json', 'other'

class DependencyAnalyzer:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.results: Dict[str, FileAnalysis] = {}
        
        # Patterns to search for
        self.patterns = {
            'codegen_app_import': re.compile(r'from\s+.*codegen_app.*import\s+.*'),
            'codegen_app_direct': re.compile(r'import\s+.*codegen_app.*'),
            'codegen_app_usage': re.compile(r'codegen_app'),
            'CodegenApp_usage': re.compile(r'CodegenApp'),
            'contexten_app_import': re.compile(r'from\s+.*contexten_app.*import\s+.*'),
            'contexten_app_direct': re.compile(r'import\s+.*contexten_app.*'),
            'ContextenApp_usage': re.compile(r'ContextenApp'),
        }
        
        # File extensions to analyze
        self.file_extensions = {
            '.py': 'python',
            '.md': 'markdown',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.json': 'json',
            '.txt': 'text',
            '.rst': 'restructured_text',
            '.toml': 'toml',
            '.cfg': 'config',
            '.ini': 'config'
        }
    
    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a single file for codegen/contexten references."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return FileAnalysis(
                file_path=str(file_path),
                total_references=0,
                import_references=[],
                usage_references=[],
                file_type='error'
            )
        
        file_type = self.file_extensions.get(file_path.suffix, 'other')
        import_references = []
        usage_references = []
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Check for import statements
            if self.patterns['codegen_app_import'].search(line):
                import_references.append(ImportReference(
                    file_path=str(file_path),
                    line_number=line_num,
                    line_content=line_stripped,
                    import_type='from_import',
                    module_path=self._extract_module_path(line),
                    symbol_name='CodegenApp'
                ))
            
            elif self.patterns['codegen_app_direct'].search(line):
                import_references.append(ImportReference(
                    file_path=str(file_path),
                    line_number=line_num,
                    line_content=line_stripped,
                    import_type='direct_import',
                    module_path=self._extract_module_path(line),
                    symbol_name='codegen_app'
                ))
            
            elif self.patterns['contexten_app_import'].search(line):
                import_references.append(ImportReference(
                    file_path=str(file_path),
                    line_number=line_num,
                    line_content=line_stripped,
                    import_type='from_import_new',
                    module_path=self._extract_module_path(line),
                    symbol_name='ContextenApp'
                ))
            
            # Check for usage references
            if self.patterns['CodegenApp_usage'].search(line) and 'import' not in line:
                usage_references.append(ImportReference(
                    file_path=str(file_path),
                    line_number=line_num,
                    line_content=line_stripped,
                    import_type='usage',
                    module_path='',
                    symbol_name='CodegenApp'
                ))
            
            if self.patterns['codegen_app_usage'].search(line) and 'import' not in line:
                usage_references.append(ImportReference(
                    file_path=str(file_path),
                    line_number=line_num,
                    line_content=line_stripped,
                    import_type='usage',
                    module_path='',
                    symbol_name='codegen_app'
                ))
        
        total_references = len(import_references) + len(usage_references)
        
        return FileAnalysis(
            file_path=str(file_path),
            total_references=total_references,
            import_references=import_references,
            usage_references=usage_references,
            file_type=file_type
        )
    
    def _extract_module_path(self, line: str) -> str:
        """Extract module path from import statement."""
        # Simple regex to extract module path
        match = re.search(r'from\s+([\w.]+)', line)
        if match:
            return match.group(1)
        
        match = re.search(r'import\s+([\w.]+)', line)
        if match:
            return match.group(1)
        
        return ''
    
    def analyze_directory(self, directory: Path = None) -> None:
        """Analyze all files in the directory recursively."""
        if directory is None:
            directory = self.root_path
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix in self.file_extensions:
                # Skip certain directories
                if any(skip in str(file_path) for skip in ['.git', '__pycache__', '.pytest_cache', 'node_modules']):
                    continue
                
                analysis = self.analyze_file(file_path)
                if analysis.total_references > 0:
                    self.results[str(file_path)] = analysis
    
    def generate_summary(self) -> Dict:
        """Generate summary statistics."""
        total_files = len(self.results)
        total_references = sum(analysis.total_references for analysis in self.results.values())
        
        # Group by file type
        by_file_type = defaultdict(int)
        by_import_type = defaultdict(int)
        
        for analysis in self.results.values():
            by_file_type[analysis.file_type] += analysis.total_references
            
            for ref in analysis.import_references:
                by_import_type[ref.import_type] += 1
        
        # Find most referenced files
        most_referenced = sorted(
            self.results.values(),
            key=lambda x: x.total_references,
            reverse=True
        )[:10]
        
        return {
            'total_files_with_references': total_files,
            'total_references': total_references,
            'references_by_file_type': dict(by_file_type),
            'references_by_import_type': dict(by_import_type),
            'most_referenced_files': [
                {
                    'file': analysis.file_path,
                    'references': analysis.total_references
                }
                for analysis in most_referenced
            ]
        }
    
    def generate_migration_plan(self) -> Dict:
        """Generate migration plan based on analysis."""
        migration_plan = {
            'phase_1_internal_updates': [],
            'phase_2_example_updates': [],
            'phase_3_documentation_updates': [],
            'phase_4_external_notifications': []
        }
        
        for analysis in self.results.values():
            file_path = analysis.file_path
            
            if 'src/contexten' in file_path:
                migration_plan['phase_1_internal_updates'].append({
                    'file': file_path,
                    'references': analysis.total_references,
                    'priority': 'high'
                })
            elif 'examples/' in file_path:
                migration_plan['phase_2_example_updates'].append({
                    'file': file_path,
                    'references': analysis.total_references,
                    'priority': 'medium'
                })
            elif any(doc in file_path for doc in ['.md', '.rst', '.txt']):
                migration_plan['phase_3_documentation_updates'].append({
                    'file': file_path,
                    'references': analysis.total_references,
                    'priority': 'low'
                })
            else:
                migration_plan['phase_4_external_notifications'].append({
                    'file': file_path,
                    'references': analysis.total_references,
                    'priority': 'medium'
                })
        
        return migration_plan
    
    def save_results(self, output_file: str = 'dependency_analysis.json'):
        """Save analysis results to JSON file."""
        output_data = {
            'summary': self.generate_summary(),
            'migration_plan': self.generate_migration_plan(),
            'detailed_results': {
                file_path: asdict(analysis)
                for file_path, analysis in self.results.items()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Analysis results saved to {output_file}")
    
    def print_summary(self):
        """Print summary to console."""
        summary = self.generate_summary()
        
        print("=" * 60)
        print("CODEGEN TO CONTEXTEN MIGRATION ANALYSIS")
        print("=" * 60)
        print(f"Total files with references: {summary['total_files_with_references']}")
        print(f"Total references found: {summary['total_references']}")
        print()
        
        print("References by file type:")
        for file_type, count in summary['references_by_file_type'].items():
            print(f"  {file_type}: {count}")
        print()
        
        print("References by import type:")
        for import_type, count in summary['references_by_import_type'].items():
            print(f"  {import_type}: {count}")
        print()
        
        print("Most referenced files:")
        for file_info in summary['most_referenced_files']:
            print(f"  {file_info['file']}: {file_info['references']} references")
        print()
        
        migration_plan = self.generate_migration_plan()
        print("Migration phases:")
        for phase, files in migration_plan.items():
            print(f"  {phase}: {len(files)} files")
        print("=" * 60)

def main():
    """Main function to run the dependency analysis."""
    analyzer = DependencyAnalyzer()
    
    print("Starting dependency analysis...")
    analyzer.analyze_directory()
    
    print("Analysis complete. Generating summary...")
    analyzer.print_summary()
    
    print("Saving detailed results...")
    analyzer.save_results('docs/dependency_analysis.json')
    
    # Generate migration checklist
    migration_plan = analyzer.generate_migration_plan()
    
    checklist_content = """# Migration Checklist

## Phase 1: Internal Updates (High Priority)
"""
    
    for item in migration_plan['phase_1_internal_updates']:
        checklist_content += f"- [ ] Update {item['file']} ({item['references']} references)\n"
    
    checklist_content += """
## Phase 2: Example Updates (Medium Priority)
"""
    
    for item in migration_plan['phase_2_example_updates']:
        checklist_content += f"- [ ] Update {item['file']} ({item['references']} references)\n"
    
    checklist_content += """
## Phase 3: Documentation Updates (Low Priority)
"""
    
    for item in migration_plan['phase_3_documentation_updates']:
        checklist_content += f"- [ ] Update {item['file']} ({item['references']} references)\n"
    
    checklist_content += """
## Phase 4: External Notifications (Medium Priority)
"""
    
    for item in migration_plan['phase_4_external_notifications']:
        checklist_content += f"- [ ] Notify about {item['file']} ({item['references']} references)\n"
    
    with open('docs/migration_checklist.md', 'w') as f:
        f.write(checklist_content)
    
    print("Migration checklist saved to docs/migration_checklist.md")

if __name__ == "__main__":
    main()

