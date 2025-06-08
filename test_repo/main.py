
def hello_world():
    """A simple greeting function."""
    print("Hello, World!")
    return "success"

class Calculator:
    def add(self, a, b):
        return a + b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
