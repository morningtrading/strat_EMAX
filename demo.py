#!/usr/bin/env python3
"""
Demo Python Script
A simple demonstration of various Python features
"""

import random
import datetime
import math

def greet_user(name="World"):
    """Greet a user with a personalized message"""
    return f"Hello, {name}! Welcome to Python!"

def calculate_circle_area(radius):
    """Calculate the area of a circle"""
    return math.pi * radius ** 2

def generate_random_numbers(count=5, min_val=1, max_val=100):
    """Generate a list of random numbers"""
    return [random.randint(min_val, max_val) for _ in range(count)]

def demonstrate_data_structures():
    """Demonstrate various Python data structures"""
    print("\n=== Data Structures Demo ===")
    
    # List
    fruits = ["apple", "banana", "orange", "grape"]
    print(f"Fruits list: {fruits}")
    print(f"First fruit: {fruits[0]}")
    print(f"Last fruit: {fruits[-1]}")
    
    # Dictionary
    person = {
        "name": "Alice",
        "age": 30,
        "city": "New York",
        "hobbies": ["reading", "swimming", "coding"]
    }
    print(f"\nPerson info: {person}")
    print(f"Name: {person['name']}, Age: {person['age']}")
    
    # Set
    unique_numbers = {1, 2, 3, 4, 5, 5, 4, 3, 2, 1}
    print(f"\nUnique numbers set: {unique_numbers}")
    
    # Tuple
    coordinates = (10, 20)
    print(f"Coordinates tuple: {coordinates}")

def demonstrate_loops():
    """Demonstrate different types of loops"""
    print("\n=== Loops Demo ===")
    
    # For loop with range
    print("Counting from 1 to 5:")
    for i in range(1, 6):
        print(f"  {i}")
    
    # For loop with list
    colors = ["red", "green", "blue"]
    print("\nColors:")
    for color in colors:
        print(f"  {color.upper()}")
    
    # While loop
    print("\nCountdown:")
    count = 3
    while count > 0:
        print(f"  {count}...")
        count -= 1
    print("  Blast off!")

def demonstrate_functions():
    """Demonstrate function usage"""
    print("\n=== Functions Demo ===")
    
    # Basic function call
    greeting = greet_user("Python Developer")
    print(greeting)
    
    # Function with default parameter
    default_greeting = greet_user()
    print(default_greeting)
    
    # Mathematical function
    radius = 5
    area = calculate_circle_area(radius)
    print(f"Area of circle with radius {radius}: {area:.2f}")
    
    # Function returning a list
    random_nums = generate_random_numbers(3, 1, 10)
    print(f"Random numbers: {random_nums}")

def demonstrate_file_operations():
    """Demonstrate basic file operations"""
    print("\n=== File Operations Demo ===")
    
    # Write to file
    filename = "demo_output.txt"
    with open(filename, "w", encoding="utf-8") as file:
        file.write("This is a demo file created by Python!\n")
        file.write(f"Created at: {datetime.datetime.now()}\n")
        file.write("Python is awesome! (snake emoji)\n")
    
    print(f"Created file: {filename}")
    
    # Read from file
    with open(filename, "r", encoding="utf-8") as file:
        content = file.read()
        print("File contents:")
        print(content)

def main():
    """Main function to run the demo"""
    print("Python Demo Script")
    print("=" * 30)
    
    # Get current time
    now = datetime.datetime.now()
    print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run demonstrations
    demonstrate_functions()
    demonstrate_data_structures()
    demonstrate_loops()
    demonstrate_file_operations()
    
    print("\n" + "=" * 30)
    print("Demo completed successfully!")

if __name__ == "__main__":
    main()
