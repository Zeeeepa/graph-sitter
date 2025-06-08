from decorators import decorator_function

@decorator_function
def foo_function():
    print("This is foo_function")

@decorator_function
def foo_bar():
    print("This is foo_bar")

def bar_function():
    print("This is bar_function")

