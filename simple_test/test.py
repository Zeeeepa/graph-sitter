def hello_world():
    """A simple test function."""
    print("Hello, World!")
    return "success"

class TestClass:
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value

if __name__ == "__main__":
    hello_world()
    test = TestClass()
    print(test.get_value())
