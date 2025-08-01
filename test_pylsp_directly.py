#!/usr/bin/env python3
"""
Test Python Language Server directly to see if it can detect errors.
"""

import subprocess
import tempfile
import json
from pathlib import Path

def test_pylsp_directly():
    """Test pylsp directly on files with known errors."""
    print("🔍 TESTING PYTHON LANGUAGE SERVER DIRECTLY")
    print("=" * 60)
    
    # Create test file with syntax error
    test_file = Path("direct_pylsp_test.py")
    test_content = '''# Test file with syntax error
def broken_function()  # Missing colon - syntax error
    return "broken"

import non_existent_module  # Import error

undefined_var = some_undefined_variable  # Name error
'''
    test_file.write_text(test_content)
    print(f"✅ Created test file: {test_file}")
    
    try:
        # Test if pylsp is available
        print("\n🔍 Testing if pylsp is available...")
        result = subprocess.run(['pylsp', '--help'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ pylsp is available")
        else:
            print(f"❌ pylsp not available: {result.stderr}")
            return False
        
        # Test pylsp on our file
        print(f"\n🔍 Running pylsp on {test_file}...")
        
        # Create LSP request for diagnostics
        lsp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "textDocument/didOpen",
            "params": {
                "textDocument": {
                    "uri": f"file://{test_file.absolute()}",
                    "languageId": "python",
                    "version": 1,
                    "text": test_content
                }
            }
        }
        
        # Try to communicate with pylsp
        try:
            proc = subprocess.Popen(
                ['pylsp'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send initialize request first
            init_request = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "processId": None,
                    "rootUri": f"file://{Path.cwd()}",
                    "capabilities": {}
                }
            }
            
            init_msg = f"Content-Length: {len(json.dumps(init_request))}\r\n\r\n{json.dumps(init_request)}"
            proc.stdin.write(init_msg)
            proc.stdin.flush()
            
            # Read response (simplified)
            import time
            time.sleep(1)
            
            # Send didOpen request
            open_msg = f"Content-Length: {len(json.dumps(lsp_request))}\r\n\r\n{json.dumps(lsp_request)}"
            proc.stdin.write(open_msg)
            proc.stdin.flush()
            
            time.sleep(2)  # Wait for processing
            
            proc.terminate()
            stdout, stderr = proc.communicate(timeout=5)
            
            print(f"   pylsp stdout: {stdout[:500]}...")
            print(f"   pylsp stderr: {stderr[:500]}...")
            
        except Exception as e:
            print(f"   ❌ Error communicating with pylsp: {e}")
        
        # Test with flake8 directly (simpler)
        print(f"\n🔍 Testing with flake8 directly...")
        try:
            result = subprocess.run(['flake8', str(test_file)], capture_output=True, text=True, timeout=10)
            print(f"   flake8 return code: {result.returncode}")
            print(f"   flake8 stdout: {result.stdout}")
            print(f"   flake8 stderr: {result.stderr}")
            
            if result.stdout:
                errors = result.stdout.strip().split('\n')
                print(f"   ✅ flake8 found {len(errors)} issues:")
                for error in errors[:5]:
                    print(f"      {error}")
            else:
                print("   ⚠️  flake8 found no issues")
                
        except Exception as e:
            print(f"   ❌ Error running flake8: {e}")
        
        # Test with pyflakes directly
        print(f"\n🔍 Testing with pyflakes directly...")
        try:
            result = subprocess.run(['pyflakes', str(test_file)], capture_output=True, text=True, timeout=10)
            print(f"   pyflakes return code: {result.returncode}")
            print(f"   pyflakes stdout: {result.stdout}")
            print(f"   pyflakes stderr: {result.stderr}")
            
            if result.stdout:
                errors = result.stdout.strip().split('\n')
                print(f"   ✅ pyflakes found {len(errors)} issues:")
                for error in errors[:5]:
                    print(f"      {error}")
            else:
                print("   ⚠️  pyflakes found no issues")
                
        except Exception as e:
            print(f"   ❌ Error running pyflakes: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
            print(f"🧹 Cleaned up test file")


def test_python_ast_parsing():
    """Test Python AST parsing for error detection."""
    print("\n🐍 TESTING PYTHON AST PARSING")
    print("=" * 60)
    
    import ast
    
    # Test files with different types of errors
    test_cases = [
        ("syntax_error.py", "def broken()  # missing colon\n    return 'broken'"),
        ("valid_code.py", "def working():\n    return 'working'"),
        ("import_error.py", "import non_existent_module\nprint('hello')"),
    ]
    
    for filename, content in test_cases:
        print(f"\n📄 Testing {filename}...")
        
        try:
            # Try to parse with AST
            tree = ast.parse(content, filename=filename)
            print(f"   ✅ AST parsing: SUCCESS")
            
            # Check for import errors by examining the AST
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        print(f"      Import found: {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    print(f"      ImportFrom found: {node.module}")
            
        except SyntaxError as e:
            print(f"   ❌ AST parsing: SYNTAX ERROR - {e}")
            print(f"      Line {e.lineno}: {e.text}")
        except Exception as e:
            print(f"   ❌ AST parsing: ERROR - {e}")


def main():
    """Test Python language server capabilities."""
    print("🧪 TESTING PYTHON LANGUAGE SERVER CAPABILITIES")
    print("=" * 80)
    
    # Test pylsp directly
    success1 = test_pylsp_directly()
    
    # Test Python AST parsing
    test_python_ast_parsing()
    
    print(f"\n🎯 TESTING SUMMARY:")
    print(f"   Direct pylsp test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    
    return success1


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

