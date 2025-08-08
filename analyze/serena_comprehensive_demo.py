"""
Comprehensive Serena LSP Integration Demo

This script demonstrates all Serena capabilities integrated into graph-sitter,
showing how to use each feature with practical examples.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Add the parent directory to the path so we can import graph_sitter
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph_sitter import Codebase
from graph_sitter.extensions.serena import SerenaConfig, SerenaCapability


def create_demo_project() -> str:
    """Create a demo project for testing Serena capabilities."""
    temp_dir = tempfile.mkdtemp(prefix="serena_demo_")
    project_path = Path(temp_dir)
    
    # Create main.py
    main_py = project_path / "main.py"
    main_py.write_text('''"""
Main module for the demo application.
"""

import os
import sys
from typing import List, Dict, Optional
from utils import calculate_total, format_currency
from models import User, Product


class ShoppingCart:
    """A shopping cart implementation."""
    
    def __init__(self, user: User):
        self.user = user
        self.items: List[Product] = []
        self.discount_rate = 0.0
    
    def add_item(self, product: Product, quantity: int = 1) -> None:
        """Add a product to the cart."""
        for _ in range(quantity):
            self.items.append(product)
    
    def remove_item(self, product: Product) -> bool:
        """Remove a product from the cart."""
        if product in self.items:
            self.items.remove(product)
            return True
        return False
    
    def get_total(self) -> float:
        """Calculate the total price of items in the cart."""
        subtotal = calculate_total([item.price for item in self.items])
        discount = subtotal * self.discount_rate
        return subtotal - discount
    
    def apply_discount(self, rate: float) -> None:
        """Apply a discount to the cart."""
        if 0 <= rate <= 1:
            self.discount_rate = rate
    
    def checkout(self) -> Dict[str, Any]:
        """Process the checkout."""
        total = self.get_total()
        return {
            'user': self.user.name,
            'items': len(self.items),
            'total': total,
            'formatted_total': format_currency(total)
        }


def main():
    """Main function."""
    user = User("John Doe", "john@example.com")
    cart = ShoppingCart(user)
    
    # Add some products
    product1 = Product("Laptop", 999.99)
    product2 = Product("Mouse", 29.99)
    
    cart.add_item(product1)
    cart.add_item(product2, 2)
    cart.apply_discount(0.1)  # 10% discount
    
    result = cart.checkout()
    print(f"Checkout result: {result}")


if __name__ == "__main__":
    main()
''')
    
    # Create utils.py
    utils_py = project_path / "utils.py"
    utils_py.write_text('''"""
Utility functions for the demo application.
"""

from typing import List, Union


def calculate_total(prices: List[float]) -> float:
    """Calculate the total of a list of prices."""
    return sum(prices)


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format an amount as currency."""
    if currency == "USD":
        return f"${amount:.2f}"
    elif currency == "EUR":
        return f"€{amount:.2f}"
    else:
        return f"{amount:.2f} {currency}"


def validate_email(email: str) -> bool:
    """Validate an email address."""
    return "@" in email and "." in email


def calculate_tax(amount: float, rate: float = 0.08) -> float:
    """Calculate tax on an amount."""
    return amount * rate


def apply_bulk_discount(prices: List[float], threshold: int = 5) -> List[float]:
    """Apply bulk discount if there are enough items."""
    if len(prices) >= threshold:
        return [price * 0.9 for price in prices]  # 10% discount
    return prices
''')
    
    # Create models.py
    models_py = project_path / "models.py"
    models_py.write_text('''"""
Data models for the demo application.
"""

from dataclasses import dataclass
from typing import Optional
from utils import validate_email


@dataclass
class User:
    """User model."""
    name: str
    email: str
    age: Optional[int] = None
    
    def __post_init__(self):
        if not validate_email(self.email):
            raise ValueError(f"Invalid email: {self.email}")
    
    def is_adult(self) -> bool:
        """Check if user is an adult."""
        return self.age is not None and self.age >= 18


@dataclass
class Product:
    """Product model."""
    name: str
    price: float
    category: str = "general"
    in_stock: bool = True
    
    def __post_init__(self):
        if self.price < 0:
            raise ValueError("Price cannot be negative")
    
    def apply_discount(self, percentage: float) -> float:
        """Apply discount and return new price."""
        if 0 <= percentage <= 100:
            return self.price * (1 - percentage / 100)
        return self.price
    
    def get_display_name(self) -> str:
        """Get display name for the product."""
        status = "In Stock" if self.in_stock else "Out of Stock"
        return f"{self.name} - {status}"


@dataclass
class Order:
    """Order model."""
    user: User
    products: list[Product]
    total: float
    status: str = "pending"
    
    def mark_completed(self) -> None:
        """Mark order as completed."""
        self.status = "completed"
    
    def cancel(self) -> None:
        """Cancel the order."""
        self.status = "cancelled"
''')
    
    # Create tests directory
    tests_dir = project_path / "tests"
    tests_dir.mkdir()
    
    # Create test_main.py
    test_main_py = tests_dir / "test_main.py"
    test_main_py.write_text('''"""
Tests for the main module.
"""

import unittest
from main import ShoppingCart
from models import User, Product


class TestShoppingCart(unittest.TestCase):
    """Test cases for ShoppingCart."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.user = User("Test User", "test@example.com")
        self.cart = ShoppingCart(self.user)
        self.product = Product("Test Product", 10.0)
    
    def test_add_item(self):
        """Test adding items to cart."""
        self.cart.add_item(self.product)
        self.assertEqual(len(self.cart.items), 1)
    
    def test_remove_item(self):
        """Test removing items from cart."""
        self.cart.add_item(self.product)
        result = self.cart.remove_item(self.product)
        self.assertTrue(result)
        self.assertEqual(len(self.cart.items), 0)
    
    def test_get_total(self):
        """Test calculating cart total."""
        self.cart.add_item(self.product, 2)
        total = self.cart.get_total()
        self.assertEqual(total, 20.0)
    
    def test_apply_discount(self):
        """Test applying discount."""
        self.cart.add_item(self.product, 2)
        self.cart.apply_discount(0.1)  # 10% discount
        total = self.cart.get_total()
        self.assertEqual(total, 18.0)


if __name__ == "__main__":
    unittest.main()
''')
    
    return str(project_path)


def demo_intelligence_features(codebase: Codebase):
    """Demonstrate code intelligence features."""
    print("🧠 Code Intelligence Features")
    print("=" * 50)
    
    # Test completions
    print("1. Code Completions:")
    completions = codebase.get_completions("main.py", 20, 10)
    if completions:
        print(f"   Found {len(completions)} completions:")
        for comp in completions[:5]:  # Show first 5
            print(f"   - {comp.get('label', 'N/A')}: {comp.get('detail', 'N/A')}")
    else:
        print("   No completions available (expected in demo mode)")
    
    # Test hover info
    print("\n2. Hover Information:")
    hover = codebase.get_hover_info("main.py", 15, 5)
    if hover:
        print(f"   Symbol: {hover.get('symbolName', 'N/A')}")
        print(f"   Type: {hover.get('symbolType', 'N/A')}")
        print(f"   Documentation: {hover.get('documentation', 'N/A')[:100]}...")
    else:
        print("   No hover information available (expected in demo mode)")
    
    # Test signature help
    print("\n3. Signature Help:")
    signature = codebase.get_signature_help("main.py", 25, 20)
    if signature:
        print(f"   Function: {signature.get('functionName', 'N/A')}")
        params = signature.get('parameters', [])
        if params:
            print(f"   Parameters: {len(params)} parameters")
            active = signature.get('activeParameter', 0)
            print(f"   Active parameter: {active}")
    else:
        print("   No signature help available (expected in demo mode)")


def demo_refactoring_features(codebase: Codebase):
    """Demonstrate refactoring features."""
    print("\n🔧 Refactoring Features")
    print("=" * 50)
    
    # Test rename symbol
    print("1. Rename Symbol (Preview):")
    rename_result = codebase.rename_symbol("main.py", 10, 5, "NewShoppingCart", preview=True)
    if rename_result.get('success'):
        changes = rename_result.get('changes', [])
        print(f"   Would rename symbol in {len(changes)} locations")
        for change in changes[:3]:  # Show first 3
            print(f"   - {change.get('file', 'N/A')}: {change.get('type', 'N/A')}")
    else:
        print(f"   Rename failed: {rename_result.get('error', 'Unknown error')}")
    
    # Test extract method
    print("\n2. Extract Method:")
    extract_result = codebase.extract_method("main.py", 35, 40, "calculate_discounted_total")
    if extract_result.get('success'):
        changes = extract_result.get('changes', [])
        print(f"   Method extraction would affect {len(changes)} locations")
    else:
        print(f"   Extract method failed: {extract_result.get('error', 'Unknown error')}")
    
    # Test extract variable
    print("\n3. Extract Variable:")
    extract_var_result = codebase.extract_variable("main.py", 30, 15, "item_count")
    if extract_var_result.get('success'):
        print("   Variable extraction successful")
    else:
        print(f"   Extract variable failed: {extract_var_result.get('error', 'Unknown error')}")


def demo_code_actions(codebase: Codebase):
    """Demonstrate code actions and quick fixes."""
    print("\n⚡ Code Actions & Quick Fixes")
    print("=" * 50)
    
    # Test get code actions
    print("1. Available Code Actions:")
    actions = codebase.get_code_actions("main.py", 1, 10)
    if actions:
        print(f"   Found {len(actions)} available actions:")
        for action in actions[:5]:  # Show first 5
            print(f"   - {action.get('title', 'N/A')}: {action.get('description', 'N/A')}")
    else:
        print("   No code actions available (expected in demo mode)")
    
    # Test organize imports
    print("\n2. Organize Imports:")
    organize_result = codebase.organize_imports("main.py")
    if organize_result.get('success'):
        changes = organize_result.get('changes', [])
        print(f"   Import organization would make {len(changes)} changes")
    else:
        print(f"   Organize imports failed: {organize_result.get('error', 'Unknown error')}")
    
    # Test apply code action
    print("\n3. Apply Code Action:")
    if actions:
        first_action = actions[0]
        action_id = first_action.get('id', 'test_action')
        apply_result = codebase.apply_code_action(action_id, "main.py")
        if apply_result.get('success'):
            print(f"   Applied action '{action_id}' successfully")
        else:
            print(f"   Apply action failed: {apply_result.get('error', 'Unknown error')}")
    else:
        print("   No actions to apply")


def demo_generation_features(codebase: Codebase):
    """Demonstrate code generation features."""
    print("\n🏗️ Code Generation Features")
    print("=" * 50)
    
    # Test generate boilerplate
    print("1. Generate Boilerplate:")
    boilerplate_result = codebase.generate_boilerplate("class", {
        "class_name": "PaymentProcessor",
        "base_class": "BaseProcessor"
    })
    if boilerplate_result.get('success'):
        code = boilerplate_result.get('generated_code', '')
        print(f"   Generated boilerplate ({len(code)} characters)")
        print(f"   Preview: {code[:100]}...")
    else:
        print(f"   Boilerplate generation failed: {boilerplate_result.get('error', 'Unknown error')}")
    
    # Test generate tests
    print("\n2. Generate Tests:")
    test_result = codebase.generate_tests("calculate_total", ["unit", "edge_cases"])
    if test_result.get('success'):
        tests = test_result.get('generated_tests', [])
        print(f"   Generated {len(tests)} test cases")
        for i, test in enumerate(tests[:3]):  # Show first 3
            print(f"   Test {i+1}: {test[:50]}...")
    else:
        print(f"   Test generation failed: {test_result.get('error', 'Unknown error')}")
    
    # Test generate documentation
    print("\n3. Generate Documentation:")
    doc_result = codebase.generate_documentation("ShoppingCart.add_item")
    if doc_result.get('success'):
        docs = doc_result.get('generated_docs', '')
        print(f"   Generated documentation ({len(docs)} characters)")
        print(f"   Preview: {docs[:100]}...")
    else:
        print(f"   Documentation generation failed: {doc_result.get('error', 'Unknown error')}")


def demo_search_features(codebase: Codebase):
    """Demonstrate search features."""
    print("\n🔍 Search Features")
    print("=" * 50)
    
    # Test semantic search
    print("1. Semantic Search:")
    search_results = codebase.semantic_search("functions that calculate totals")
    if search_results:
        print(f"   Found {len(search_results)} results:")
        for result in search_results[:5]:  # Show first 5
            file = result.get('file', 'N/A')
            line = result.get('line', 'N/A')
            match = result.get('match', 'N/A')
            score = result.get('score', 0)
            print(f"   - {file}:{line} (score: {score:.2f}): {match[:50]}...")
    else:
        print("   No search results found (expected in demo mode)")
    
    # Test find code patterns
    print("\n2. Find Code Patterns:")
    pattern_results = codebase.find_code_patterns("def.*calculate.*", suggest_improvements=True)
    if pattern_results:
        print(f"   Found {len(pattern_results)} pattern matches:")
        for result in pattern_results[:3]:  # Show first 3
            file = result.get('file', 'N/A')
            pattern = result.get('pattern', 'N/A')
            improvements = result.get('improvements', [])
            print(f"   - {file}: Pattern '{pattern}'")
            if improvements:
                print(f"     Suggestion: {improvements[0]}")
    else:
        print("   No pattern matches found (expected in demo mode)")
    
    # Test find similar code
    print("\n3. Find Similar Code:")
    reference_code = "def calculate_total(prices): return sum(prices)"
    similar_results = codebase.find_similar_code(reference_code, 0.7)
    if similar_results:
        print(f"   Found {len(similar_results)} similar code blocks:")
        for result in similar_results[:3]:  # Show first 3
            file = result.get('file', 'N/A')
            similarity = result.get('similarity', 0)
            print(f"   - {file} (similarity: {similarity:.2f})")
    else:
        print("   No similar code found (expected in demo mode)")


def demo_symbol_intelligence(codebase: Codebase):
    """Demonstrate symbol intelligence features."""
    print("\n🎨 Symbol Intelligence")
    print("=" * 50)
    
    # Test get symbol context
    print("1. Symbol Context:")
    context = codebase.get_symbol_context("ShoppingCart", include_dependencies=True)
    if context:
        symbol_type = context.get('type', 'N/A')
        file = context.get('file', 'N/A')
        dependencies = context.get('dependencies', [])
        usages = context.get('usages', [])
        
        print(f"   Symbol: ShoppingCart")
        print(f"   Type: {symbol_type}")
        print(f"   File: {file}")
        print(f"   Dependencies: {len(dependencies)} items")
        print(f"   Usages: {len(usages)} locations")
    else:
        print("   No symbol context available (expected in demo mode)")
    
    # Test analyze symbol impact
    print("\n2. Symbol Impact Analysis:")
    impact = codebase.analyze_symbol_impact("calculate_total", "rename")
    if impact:
        impact_level = impact.get('impact_level', 'N/A')
        affected_files = impact.get('affected_files', [])
        recommendations = impact.get('recommendations', [])
        
        print(f"   Impact level: {impact_level}")
        print(f"   Affected files: {len(affected_files)} files")
        if recommendations:
            print("   Recommendations:")
            for rec in recommendations[:3]:  # Show first 3
                print(f"   - {rec}")
    else:
        print("   No impact analysis available (expected in demo mode)")


def demo_realtime_features(codebase: Codebase):
    """Demonstrate real-time analysis features."""
    print("\n⚡ Real-time Analysis")
    print("=" * 50)
    
    # Test enable real-time analysis
    print("1. Enable Real-time Analysis:")
    success = codebase.enable_realtime_analysis(["*.py", "*.ts"], auto_refresh=True)
    if success:
        print("   Real-time analysis enabled successfully")
    else:
        print("   Failed to enable real-time analysis (expected in demo mode)")
    
    # Test disable real-time analysis
    print("\n2. Disable Real-time Analysis:")
    success = codebase.disable_realtime_analysis()
    if success:
        print("   Real-time analysis disabled successfully")
    else:
        print("   Failed to disable real-time analysis")


def demo_status_and_utilities(codebase: Codebase):
    """Demonstrate status and utility features."""
    print("\n🔧 Status & Utilities")
    print("=" * 50)
    
    # Test get Serena status
    print("1. Serena Status:")
    status = codebase.get_serena_status()
    
    enabled = status.get('enabled', False)
    print(f"   Serena enabled: {enabled}")
    
    if enabled:
        capabilities = status.get('enabled_capabilities', [])
        active_capabilities = status.get('active_capabilities', [])
        realtime = status.get('realtime_analysis', False)
        
        print(f"   Enabled capabilities: {len(capabilities)} capabilities")
        print(f"   Active capabilities: {len(active_capabilities)} capabilities")
        print(f"   Real-time analysis: {realtime}")
        
        # Show capability details
        capability_details = status.get('capability_details', {})
        if capability_details:
            print("   Capability status:")
            for cap_name, cap_status in capability_details.items():
                initialized = cap_status.get('initialized', False)
                print(f"   - {cap_name}: {'✓' if initialized else '✗'}")
    else:
        error = status.get('error', 'Unknown error')
        print(f"   Error: {error}")


def main():
    """Main demo function."""
    print("🚀 Serena LSP Integration - Comprehensive Demo")
    print("=" * 60)
    
    # Create demo project
    print("Setting up demo project...")
    project_path = create_demo_project()
    print(f"Demo project created at: {project_path}")
    
    try:
        # Initialize codebase with Serena integration
        print("\nInitializing codebase with Serena integration...")
        codebase = Codebase(project_path)
        
        # Import Serena integration (this adds methods to Codebase)
        try:
            from graph_sitter.extensions.serena.auto_init import _initialized
            if _initialized:
                print("✅ Serena integration loaded successfully!")
            else:
                print("⚠️  Serena integration not fully loaded, continuing with demo...")
        except ImportError:
            print("⚠️  Serena integration not available, showing expected behavior...")
        
        print(f"\nAnalyzing codebase: {len(codebase.files)} files found")
        
        # Run all demos
        demo_intelligence_features(codebase)
        demo_refactoring_features(codebase)
        demo_code_actions(codebase)
        demo_generation_features(codebase)
        demo_search_features(codebase)
        demo_symbol_intelligence(codebase)
        demo_realtime_features(codebase)
        demo_status_and_utilities(codebase)
        
        print("\n🎉 Demo completed successfully!")
        print("\nNote: Many features show 'expected in demo mode' because they require")
        print("actual LSP servers and AI services to be fully functional.")
        print("In a real environment, these features would provide rich, interactive")
        print("code intelligence, refactoring, and generation capabilities.")
        
        # Cleanup
        print(f"\nCleaning up demo project at: {project_path}")
        codebase.shutdown_serena()
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up temporary directory
        import shutil
        try:
            shutil.rmtree(project_path)
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")


if __name__ == "__main__":
    main()

