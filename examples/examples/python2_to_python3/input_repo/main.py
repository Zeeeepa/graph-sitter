# Python 2 to Python 3 Migration Examples
# This file demonstrates Python 2 syntax converted to Python 3

# Print statement vs. Print function
print("This is Python 3's print function.")
# Python 2 was: print "This is Python 2's print statement."

# Integer division
print("Integer division in Python 3: 5//2 =", 5//2)
print("True division in Python 3: 5/2 =", 5/2)
# Python 2 was: print "Integer division in Python 2: 5/2 =", 5/2

# Unicode strings
unicode_string = "This is a Unicode string in Python 3 (default)."
print("Unicode string in Python 3:", unicode_string)
# Python 2 was: unicode_string = u"This is a Unicode string in Python 2."

# range vs xrange
for i in range(3):  # range behaves like xrange in Python 2
    print("Using range in Python 3:", i)
# Python 2 was: for i in xrange(3):

# Error handling
try:
    raise ValueError("This is an error.")
except ValueError as e:  # 'as' syntax in Python 3
    print("Caught an exception in Python 3:", e)
# Python 2 was: except ValueError, e:

# Iteration over dictionaries
my_dict = {"a": 1, "b": 2}
print("Dictionary keys in Python 3:", list(my_dict.keys()))  # Returns a view in Python 3
# Python 2 was: print "Dictionary keys in Python 2:", my_dict.keys()  # Returned a list

# Input function
# user_input = input("Enter something (Python 3 input): ")
# print("You entered:", user_input)
# Python 2 was: user_input = raw_input("Enter something (Python 2 raw_input): ")

# Itertools changes
import itertools
print("zip in Python 3:", list(zip([1, 2], [3, 4])))
# Python 2 was: print "itertools.izip in Python 2:", list(itertools.izip([1, 2], [3, 4]))

# Advanced Examples

# Metaclasses
class Meta(type):
    def __new__(cls, name, bases, dct):
        print("Creating class", name)
        return super(Meta, cls).__new__(cls, name, bases, dct)

class MyClass(metaclass=Meta):  # Python 3 syntax for metaclasses
    pass
# Python 2 was: class MyClass(object): __metaclass__ = Meta

# Iterators and Generators
class MyIterator(object):
    def __init__(self, limit):
        self.limit = limit
        self.counter = 0

    def __iter__(self):
        return self

    def __next__(self):  # Python 3 iterator method
        if self.counter < self.limit:
            self.counter += 1
            return self.counter
        else:
            raise StopIteration
    
    # For Python 2 compatibility (if needed)
    next = __next__

my_iter = MyIterator(3)
for value in my_iter:
    print("Iterating in Python 3:", value)
# Python 2 was: def next(self): instead of __next__

# Sorting with custom keys
data = [(1, "one"), (3, "three"), (2, "two")]
print("Sorted data in Python 3:", sorted(data, key=lambda x: x[0]))
# Python 2 was: sorted(data, cmp=lambda x, y: cmp(x[0], y[0]))

# File Handling
with open("example.txt", "w", encoding="utf-8") as f:
    f.write("Python 3 file handling with explicit encoding.")
# Python 2 was: with open("example.txt", "w") as f: (no encoding parameter)

# Bytes and Strings
byte_string = b"This is a byte string in Python 3."
text_string = "This is a text string in Python 3."
print("Byte string in Python 3:", byte_string)
print("Text string in Python 3:", text_string)
# Python 2 was: byte_string = "This is a byte string in Python 2." (strings were bytes by default)

# Final note
print("This script demonstrates Python 3 syntax (converted from Python 2 examples).")

