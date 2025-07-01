#!/usr/bin/env python3
"""
Simple test for rset compatibility function without full module dependencies
"""

from typing import List, Dict, Any
from collections import namedtuple


def _convert_rset_to_dicts(cursor, results) -> List[Dict[str, Any]]:
    """
    Convert database result set to list of dictionaries.
    
    This function handles different database drivers that return result sets
    in various formats (tuples, Row objects, etc.) and converts them to
    a standardized dictionary format.
    
    Args:
        cursor: Database cursor object with column description
        results: Result set from cursor.fetchall()
        
    Returns:
        List of dictionaries with column names as keys
    """
    if not results:
        return []
    
    # Try to convert directly if rows support dict conversion (e.g., sqlite3.Row)
    try:
        first_row = results[0]
        if hasattr(first_row, 'keys'):
            # Row object with dict-like interface (e.g., sqlite3.Row)
            return [dict(row) for row in results]
        elif hasattr(first_row, '_asdict'):
            # Named tuple with _asdict method
            return [row._asdict() for row in results]
    except (TypeError, AttributeError):
        pass
    
    # Fallback: use cursor.description to map column names to values
    try:
        if hasattr(cursor, 'description') and cursor.description:
            column_names = [desc[0] for desc in cursor.description]
            return [dict(zip(column_names, row)) for row in results]
    except (TypeError, AttributeError):
        pass
    
    # Last resort: return as-is if conversion fails
    # This maintains backward compatibility but may not be ideal
    return results


class MockCursor:
    """Mock cursor object for testing"""
    def __init__(self, description=None):
        self.description = description


class MockRow:
    """Mock row object that supports dict conversion"""
    def __init__(self, data):
        self._data = data
    
    def keys(self):
        return self._data.keys()
    
    def __getitem__(self, key):
        return self._data[key]
    
    def __iter__(self):
        return iter(self._data.items())


def test_rset_compatibility():
    """Test various result set formats"""
    
    print("🧪 Testing rset compatibility improvements...")
    print("=" * 50)
    
    # Test 1: Empty result set
    print("\n1. Testing empty result set:")
    cursor = MockCursor()
    empty_results = []
    converted = _convert_rset_to_dicts(cursor, empty_results)
    print(f"   Input: {empty_results}")
    print(f"   Output: {converted}")
    assert converted == []
    print("   ✅ PASS")
    
    # Test 2: Row objects with dict-like interface (e.g., sqlite3.Row)
    print("\n2. Testing Row objects with dict interface:")
    cursor = MockCursor()
    row_results = [
        MockRow({'id': 1, 'name': 'test1', 'score': 85.5}),
        MockRow({'id': 2, 'name': 'test2', 'score': 92.0})
    ]
    converted = _convert_rset_to_dicts(cursor, row_results)
    print(f"   Input: Row objects")
    print(f"   Output: {converted}")
    expected = [{'id': 1, 'name': 'test1', 'score': 85.5}, {'id': 2, 'name': 'test2', 'score': 92.0}]
    assert converted == expected
    print("   ✅ PASS")
    
    # Test 3: Tuple results with cursor description (common with many drivers)
    print("\n3. Testing tuple results with cursor description:")
    cursor = MockCursor(description=[
        ('id', 'INTEGER'),
        ('name', 'VARCHAR'),
        ('score', 'FLOAT')
    ])
    tuple_results = [
        (1, 'test1', 85.5),
        (2, 'test2', 92.0)
    ]
    converted = _convert_rset_to_dicts(cursor, tuple_results)
    print(f"   Input: {tuple_results}")
    print(f"   Output: {converted}")
    expected = [{'id': 1, 'name': 'test1', 'score': 85.5}, {'id': 2, 'name': 'test2', 'score': 92.0}]
    assert converted == expected
    print("   ✅ PASS")
    
    # Test 4: Named tuple results
    print("\n4. Testing named tuple results:")
    cursor = MockCursor()
    ResultRow = namedtuple('ResultRow', ['id', 'name', 'score'])
    namedtuple_results = [
        ResultRow(1, 'test1', 85.5),
        ResultRow(2, 'test2', 92.0)
    ]
    converted = _convert_rset_to_dicts(cursor, namedtuple_results)
    print(f"   Input: Named tuples")
    print(f"   Output: {converted}")
    expected = [{'id': 1, 'name': 'test1', 'score': 85.5}, {'id': 2, 'name': 'test2', 'score': 92.0}]
    assert converted == expected
    print("   ✅ PASS")
    
    # Test 5: Fallback case - plain tuples without description
    print("\n5. Testing fallback case (plain tuples, no description):")
    cursor = MockCursor(description=None)
    plain_results = [(1, 'test1', 85.5), (2, 'test2', 92.0)]
    converted = _convert_rset_to_dicts(cursor, plain_results)
    print(f"   Input: {plain_results}")
    print(f"   Output: {converted}")
    # In fallback case, should return as-is
    assert converted == plain_results
    print("   ✅ PASS (fallback behavior)")
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! The rset compatibility improvements work correctly.")
    print("\nKey improvements:")
    print("• ✅ Handles sqlite3.Row objects")
    print("• ✅ Handles named tuples")
    print("• ✅ Handles plain tuples with cursor description")
    print("• ✅ Graceful fallback for unsupported formats")
    print("• ✅ Empty result set handling")


if __name__ == "__main__":
    test_rset_compatibility()
