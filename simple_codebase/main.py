
def used_function():
    """This function is used."""
    return "Hello, World!"

def unused_function():
    """This function is never called."""
    return "Goodbye, World!"

class UsedClass:
    def method(self):
        return used_function()

class UnusedClass:
    def method(self):
        return "Never instantiated"

# Usage
obj = UsedClass()
result = obj.method()
print(result)
