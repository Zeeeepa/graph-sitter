#!/usr/bin/env python3
"""Valid Python code with no errors."""

def add_numbers(a, b):
    """Add two numbers together."""
    return a + b

def multiply_numbers(x, y):
    """Multiply two numbers."""
    return x * y

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, value):
        self.result += value
        return self.result
    
    def get_result(self):
        return self.result

def main():
    calc = Calculator()
    calc.add(5)
    calc.add(3)
    print(f"Result: {calc.get_result()}")

if __name__ == "__main__":
    main()
