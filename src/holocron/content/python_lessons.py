"""Built-in Python programming lessons.

A progressive curriculum covering Python fundamentals to advanced topics.
"""

from holocron.content.loader import Lesson, LessonCategory, LessonLoader


# =============================================================================
# Fundamentals - Lesson 1: Variables and Data Types
# =============================================================================

LESSON_VARIABLES = Lesson(
    lesson_id="python.fundamentals.variables",
    domain_id="python-programming",
    title="Variables and Data Types",
    description="Learn how Python stores and manipulates different types of data.",
    category=LessonCategory.FUNDAMENTALS,
    difficulty=1,
    estimated_minutes=15,
    tags=["variables", "types", "basics"],
    content='''
# Variables and Data Types in Python

Variables are containers for storing data values. Python is dynamically typed,
meaning you don't need to declare the type of a variable.

## Creating Variables

```python
# String - text data
name = "Alice"
greeting = 'Hello, World!'

# Integer - whole numbers
age = 25
year = 2024

# Float - decimal numbers
price = 19.99
pi = 3.14159

# Boolean - True or False
is_student = True
has_license = False
```

## Checking Types

Use the `type()` function to see what type a variable is:

```python
print(type(name))      # <class 'str'>
print(type(age))       # <class 'int'>
print(type(price))     # <class 'float'>
print(type(is_student)) # <class 'bool'>
```

## Type Conversion

Convert between types using built-in functions:

```python
# String to integer
num_str = "42"
num_int = int(num_str)  # 42

# Integer to string
count = 100
count_str = str(count)  # "100"

# Integer to float
whole = 5
decimal = float(whole)  # 5.0
```

## Variable Naming Rules

1. Must start with a letter or underscore
2. Can contain letters, numbers, and underscores
3. Case-sensitive (`name` and `Name` are different)
4. Cannot be a Python keyword

```python
# Good names
user_name = "Bob"
total_count = 42
_private = "hidden"

# Bad names (will cause errors)
# 2nd_place = "silver"  # Can't start with number
# my-var = 10           # Can't use hyphens
# class = "Math"        # 'class' is a keyword
```

## Multiple Assignment

Assign multiple variables at once:

```python
# Multiple values
x, y, z = 1, 2, 3

# Same value to multiple variables
a = b = c = 0
```
''',
)

# =============================================================================
# Fundamentals - Lesson 2: Lists and Collections
# =============================================================================

LESSON_LISTS = Lesson(
    lesson_id="python.fundamentals.lists",
    domain_id="python-programming",
    title="Lists and Collections",
    description="Master Python's list data structure for storing ordered collections.",
    category=LessonCategory.FUNDAMENTALS,
    difficulty=2,
    estimated_minutes=20,
    prerequisites=["python.fundamentals.variables"],
    tags=["lists", "collections", "indexing"],
    content='''
# Lists in Python

Lists are ordered, mutable collections that can hold items of any type.

## Creating Lists

```python
# Empty list
empty = []

# List of numbers
numbers = [1, 2, 3, 4, 5]

# List of strings
fruits = ["apple", "banana", "cherry"]

# Mixed types
mixed = [1, "hello", 3.14, True]
```

## Accessing Elements

Use indexing (starting from 0) to access elements:

```python
fruits = ["apple", "banana", "cherry", "date"]

print(fruits[0])   # "apple" (first element)
print(fruits[2])   # "cherry" (third element)
print(fruits[-1])  # "date" (last element)
print(fruits[-2])  # "cherry" (second to last)
```

## Slicing Lists

Extract portions of a list:

```python
numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

print(numbers[2:5])   # [2, 3, 4] (index 2 to 4)
print(numbers[:3])    # [0, 1, 2] (first 3)
print(numbers[7:])    # [7, 8, 9] (from index 7 to end)
print(numbers[::2])   # [0, 2, 4, 6, 8] (every 2nd element)
```

## Modifying Lists

```python
fruits = ["apple", "banana", "cherry"]

# Change an element
fruits[1] = "blueberry"  # ["apple", "blueberry", "cherry"]

# Add elements
fruits.append("date")     # Add to end
fruits.insert(1, "apricot")  # Insert at index 1

# Remove elements
fruits.remove("cherry")   # Remove by value
popped = fruits.pop()     # Remove and return last item
del fruits[0]             # Remove by index
```

## List Operations

```python
# Length
len(fruits)  # Number of elements

# Check membership
"apple" in fruits  # True or False

# Concatenate
combined = [1, 2] + [3, 4]  # [1, 2, 3, 4]

# Repeat
repeated = [0] * 3  # [0, 0, 0]

# Sort
numbers.sort()           # Sort in place
sorted_nums = sorted(numbers)  # Return new sorted list

# Reverse
numbers.reverse()        # Reverse in place
```

## List Comprehensions

A concise way to create lists:

```python
# Traditional way
squares = []
for x in range(5):
    squares.append(x ** 2)

# List comprehension
squares = [x ** 2 for x in range(5)]  # [0, 1, 4, 9, 16]

# With condition
evens = [x for x in range(10) if x % 2 == 0]  # [0, 2, 4, 6, 8]
```
''',
)

# =============================================================================
# Fundamentals - Lesson 3: Control Flow
# =============================================================================

LESSON_CONTROL_FLOW = Lesson(
    lesson_id="python.fundamentals.control_flow",
    domain_id="python-programming",
    title="Control Flow: If, Loops, and Logic",
    description="Learn to control program execution with conditions and loops.",
    category=LessonCategory.FUNDAMENTALS,
    difficulty=2,
    estimated_minutes=25,
    prerequisites=["python.fundamentals.variables"],
    tags=["if", "loops", "for", "while", "conditions"],
    content='''
# Control Flow in Python

Control flow statements determine which code runs and when.

## If Statements

Make decisions based on conditions:

```python
age = 18

if age >= 18:
    print("You are an adult")
elif age >= 13:
    print("You are a teenager")
else:
    print("You are a child")
```

## Comparison Operators

```python
x == y   # Equal
x != y   # Not equal
x < y    # Less than
x > y    # Greater than
x <= y   # Less than or equal
x >= y   # Greater than or equal
```

## Logical Operators

Combine conditions:

```python
age = 25
has_license = True

# AND - both must be true
if age >= 18 and has_license:
    print("Can drive")

# OR - at least one must be true
if age < 13 or age > 65:
    print("Discount applies")

# NOT - inverts the condition
if not has_license:
    print("Cannot drive")
```

## For Loops

Iterate over sequences:

```python
# Loop through a list
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)

# Loop with range
for i in range(5):      # 0, 1, 2, 3, 4
    print(i)

for i in range(2, 6):   # 2, 3, 4, 5
    print(i)

for i in range(0, 10, 2):  # 0, 2, 4, 6, 8 (step of 2)
    print(i)

# Loop with index
for i, fruit in enumerate(fruits):
    print(f"{i}: {fruit}")
```

## While Loops

Repeat while a condition is true:

```python
count = 0
while count < 5:
    print(count)
    count += 1  # Don't forget to update!

# With break
while True:
    user_input = input("Enter 'quit' to exit: ")
    if user_input == "quit":
        break
    print(f"You entered: {user_input}")
```

## Loop Control

```python
# break - exit the loop entirely
for i in range(10):
    if i == 5:
        break
    print(i)  # Prints 0, 1, 2, 3, 4

# continue - skip to next iteration
for i in range(5):
    if i == 2:
        continue
    print(i)  # Prints 0, 1, 3, 4

# pass - do nothing (placeholder)
for i in range(5):
    if i == 2:
        pass  # TODO: handle this case
    print(i)
```

## Nested Loops

```python
# Multiplication table
for i in range(1, 4):
    for j in range(1, 4):
        print(f"{i} x {j} = {i * j}")
```
''',
)

# =============================================================================
# Fundamentals - Lesson 4: Functions
# =============================================================================

LESSON_FUNCTIONS = Lesson(
    lesson_id="python.fundamentals.functions",
    domain_id="python-programming",
    title="Functions",
    description="Create reusable blocks of code with functions.",
    category=LessonCategory.FUNDAMENTALS,
    difficulty=3,
    estimated_minutes=25,
    prerequisites=["python.fundamentals.control_flow"],
    tags=["functions", "def", "parameters", "return"],
    content='''
# Functions in Python

Functions are reusable blocks of code that perform specific tasks.

## Defining Functions

```python
def greet():
    print("Hello, World!")

# Call the function
greet()  # Output: Hello, World!
```

## Parameters and Arguments

```python
def greet(name):
    print(f"Hello, {name}!")

greet("Alice")  # Output: Hello, Alice!
greet("Bob")    # Output: Hello, Bob!
```

## Multiple Parameters

```python
def add(a, b):
    return a + b

result = add(3, 5)  # result = 8
```

## Default Parameters

```python
def greet(name, greeting="Hello"):
    print(f"{greeting}, {name}!")

greet("Alice")              # Hello, Alice!
greet("Bob", "Hi")          # Hi, Bob!
greet("Charlie", greeting="Hey")  # Hey, Charlie!
```

## Return Values

```python
def square(x):
    return x ** 2

result = square(4)  # result = 16

# Multiple return values
def get_stats(numbers):
    return min(numbers), max(numbers), sum(numbers)

minimum, maximum, total = get_stats([1, 2, 3, 4, 5])
```

## Variable Arguments

```python
# *args - variable positional arguments
def add_all(*numbers):
    return sum(numbers)

add_all(1, 2, 3)      # 6
add_all(1, 2, 3, 4, 5)  # 15

# **kwargs - variable keyword arguments
def print_info(**kwargs):
    for key, value in kwargs.items():
        print(f"{key}: {value}")

print_info(name="Alice", age=25, city="NYC")
```

## Scope

```python
global_var = "I'm global"

def my_function():
    local_var = "I'm local"
    print(global_var)   # Can access global
    print(local_var)    # Can access local

my_function()
# print(local_var)  # Error! local_var not accessible here
```

## Lambda Functions

Short, anonymous functions:

```python
# Regular function
def square(x):
    return x ** 2

# Lambda equivalent
square = lambda x: x ** 2

# Common use: with map, filter, sorted
numbers = [1, 2, 3, 4, 5]
squared = list(map(lambda x: x ** 2, numbers))
evens = list(filter(lambda x: x % 2 == 0, numbers))
```

## Docstrings

Document your functions:

```python
def calculate_area(length, width):
    """
    Calculate the area of a rectangle.

    Args:
        length: The length of the rectangle
        width: The width of the rectangle

    Returns:
        The area of the rectangle
    """
    return length * width
```
''',
)

# =============================================================================
# Intermediate - Lesson 5: Dictionaries
# =============================================================================

LESSON_DICTIONARIES = Lesson(
    lesson_id="python.intermediate.dictionaries",
    domain_id="python-programming",
    title="Dictionaries",
    description="Store and access data using key-value pairs.",
    category=LessonCategory.INTERMEDIATE,
    difficulty=4,
    estimated_minutes=20,
    prerequisites=["python.fundamentals.lists"],
    tags=["dictionaries", "dict", "key-value", "mapping"],
    content='''
# Dictionaries in Python

Dictionaries store data as key-value pairs, allowing fast lookups.

## Creating Dictionaries

```python
# Empty dictionary
empty = {}

# Dictionary with data
person = {
    "name": "Alice",
    "age": 25,
    "city": "New York"
}

# Using dict() constructor
person = dict(name="Alice", age=25, city="New York")
```

## Accessing Values

```python
person = {"name": "Alice", "age": 25}

# Using square brackets
print(person["name"])  # "Alice"

# Using get() - safer, returns None if key missing
print(person.get("name"))      # "Alice"
print(person.get("email"))     # None
print(person.get("email", "N/A"))  # "N/A" (default value)
```

## Modifying Dictionaries

```python
person = {"name": "Alice", "age": 25}

# Add or update
person["email"] = "alice@example.com"  # Add new key
person["age"] = 26                      # Update existing

# Update multiple at once
person.update({"city": "NYC", "country": "USA"})

# Remove items
del person["email"]              # Remove by key
age = person.pop("age")          # Remove and return value
person.clear()                   # Remove all items
```

## Dictionary Operations

```python
person = {"name": "Alice", "age": 25, "city": "NYC"}

# Get all keys, values, or items
person.keys()    # dict_keys(['name', 'age', 'city'])
person.values()  # dict_values(['Alice', 25, 'NYC'])
person.items()   # dict_items([('name', 'Alice'), ...])

# Check if key exists
"name" in person    # True
"email" in person   # False

# Length
len(person)  # 3
```

## Iterating Over Dictionaries

```python
person = {"name": "Alice", "age": 25, "city": "NYC"}

# Loop through keys
for key in person:
    print(key)

# Loop through values
for value in person.values():
    print(value)

# Loop through key-value pairs
for key, value in person.items():
    print(f"{key}: {value}")
```

## Dictionary Comprehensions

```python
# Create dictionary from list
numbers = [1, 2, 3, 4, 5]
squares = {x: x**2 for x in numbers}
# {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}

# With condition
even_squares = {x: x**2 for x in numbers if x % 2 == 0}
# {2: 4, 4: 16}
```

## Nested Dictionaries

```python
employees = {
    "emp1": {
        "name": "Alice",
        "department": "Engineering"
    },
    "emp2": {
        "name": "Bob",
        "department": "Marketing"
    }
}

# Access nested values
print(employees["emp1"]["name"])  # "Alice"
```
''',
)

# =============================================================================
# Intermediate - Lesson 6: Classes and Objects
# =============================================================================

LESSON_CLASSES = Lesson(
    lesson_id="python.intermediate.classes",
    domain_id="python-programming",
    title="Classes and Object-Oriented Programming",
    description="Learn to create your own types using classes.",
    category=LessonCategory.INTERMEDIATE,
    difficulty=5,
    estimated_minutes=30,
    prerequisites=["python.fundamentals.functions"],
    tags=["classes", "oop", "objects", "methods"],
    content='''
# Classes and Objects in Python

Object-Oriented Programming (OOP) lets you create custom types
that bundle data and behavior together.

## Defining a Class

```python
class Dog:
    # Class attribute (shared by all instances)
    species = "Canis familiaris"

    # Constructor (initializer)
    def __init__(self, name, age):
        # Instance attributes (unique to each instance)
        self.name = name
        self.age = age

    # Instance method
    def bark(self):
        print(f"{self.name} says Woof!")

    def describe(self):
        return f"{self.name} is {self.age} years old"
```

## Creating Objects (Instances)

```python
# Create instances
buddy = Dog("Buddy", 3)
max = Dog("Max", 5)

# Access attributes
print(buddy.name)      # "Buddy"
print(max.age)         # 5
print(buddy.species)   # "Canis familiaris"

# Call methods
buddy.bark()           # "Buddy says Woof!"
print(max.describe())  # "Max is 5 years old"
```

## The self Parameter

`self` refers to the current instance. It's automatically passed
when calling methods on an object.

```python
class Counter:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1

    def get_count(self):
        return self.count

counter = Counter()
counter.increment()
counter.increment()
print(counter.get_count())  # 2
```

## Inheritance

Create a new class based on an existing one:

```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        pass  # To be overridden

class Dog(Animal):
    def speak(self):
        return f"{self.name} says Woof!"

class Cat(Animal):
    def speak(self):
        return f"{self.name} says Meow!"

dog = Dog("Buddy")
cat = Cat("Whiskers")
print(dog.speak())  # "Buddy says Woof!"
print(cat.speak())  # "Whiskers says Meow!"
```

## Special Methods (Dunder Methods)

```python
class Book:
    def __init__(self, title, pages):
        self.title = title
        self.pages = pages

    def __str__(self):
        return f"{self.title}"

    def __repr__(self):
        return f"Book('{self.title}', {self.pages})"

    def __len__(self):
        return self.pages

    def __eq__(self, other):
        return self.title == other.title

book = Book("Python 101", 300)
print(book)        # "Python 101" (uses __str__)
print(repr(book))  # "Book('Python 101', 300)"
print(len(book))   # 300
```

## Properties

Control access to attributes:

```python
class Circle:
    def __init__(self, radius):
        self._radius = radius

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        if value < 0:
            raise ValueError("Radius cannot be negative")
        self._radius = value

    @property
    def area(self):
        return 3.14159 * self._radius ** 2

circle = Circle(5)
print(circle.radius)  # 5
print(circle.area)    # 78.54...
circle.radius = 10    # Uses setter
```
''',
)

# =============================================================================
# Register all lessons
# =============================================================================

def register_python_lessons():
    """Register all Python programming lessons."""
    lessons = [
        LESSON_VARIABLES,
        LESSON_LISTS,
        LESSON_CONTROL_FLOW,
        LESSON_FUNCTIONS,
        LESSON_DICTIONARIES,
        LESSON_CLASSES,
    ]
    for lesson in lessons:
        LessonLoader.register_builtin(lesson)


# Auto-register when module is imported
register_python_lessons()
