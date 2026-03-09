"""
sds.py — Student Data System

A command-line application that manages student and academic staff records.
Demonstrates core Python concepts:
    - Classes and inheritance (OOP)
    - File I/O with CSV files
    - External libraries (requests, cowsay, faker)
    - Command-line arguments with sys.argv
    - Error handling with try/except
    - List operations and sorting with lambda functions

HOW TO RUN:
    python3 sds.py add         — Add a new student interactively
    python3 sds.py list        — List all students
    python3 sds.py academics   — List academic staff
    python3 sds.py demo        — Run a demonstration of the system
"""

# --- Standard Library Imports ---
# These come built-in with Python — no need to install them.

import sys      # sys.argv lets us read command-line arguments
import csv      # csv module lets us read/write CSV (comma-separated values) files
import os       # os module lets us check if files exist, work with file paths, etc.
import random   # random module lets us generate random numbers and make random choices

# --- External Libraries ---
# These must be installed separately (e.g. pip install requests cowsay faker).
# They add functionality that isn't built into Python.

import requests     # requests lets us make HTTP requests (e.g. fetch data from the internet)
import cowsay       # cowsay prints fun ASCII art messages
from faker import Faker  # Faker generates realistic fake data (names, jobs, etc.)

# ==========================================
# PART 1: OOP Models (Classes & Inheritance)
# ==========================================
# OOP (Object-Oriented Programming) lets us model real-world things as "objects".
# A "class" is a blueprint for creating objects. For example, the Student class
# defines what every student looks like (name, degree, grade) and what they can
# do (enroll in modules, print their timetable).


class Student:
    """Represents a student in the system.
    This is the BASE class — Undergraduate and Postgrad inherit from it."""

    def __init__(self, name, degree, grade):
        """__init__ is the CONSTRUCTOR — it runs automatically when you create
        a new Student object, e.g. Student("Bob", "ECE", 75).
        'self' refers to the object being created."""

        # Validation: check inputs are sensible before storing them
        if not name:
            raise ValueError("Missing name")
        if degree not in ["ECE", "BIO", "MECH", "EEE", "COMP"]:
            raise ValueError("Invalid degree")

        # Store the data as instance attributes (self.xxx)
        # These belong to THIS specific student object
        self.name = name
        self.degree = degree
        self.grade = grade
        self.modules = []  # Empty list — student starts with no modules

    def enroll(self, module):
        """Enrol this student in a module.
        This creates a TWO-WAY link: the student knows about the module,
        and the module knows about the student."""
        self.modules.append(module)      # Add module to student's list
        module.add_student(self)         # Add student to module's list

    def print_timetable(self):
        """Print the student's timetable, sorted by time slot.
        sorted() with a lambda function sorts modules by their time_slot attribute.
        A lambda is just a small inline function: lambda m: m.time_slot means
        "for each module m, use m.time_slot as the sorting key"."""
        print(f"\n--- Timetable for {self.name} ---")
        if not self.modules:
            print("No modules enrolled.")
        for mod in sorted(self.modules, key=lambda m: m.time_slot):
            print(f"{mod.time_slot}: {mod.name} (Taught by: {mod.academic.title} {mod.academic.name})")
        print("-----------------------------------")
        
        # Using the requests library to fetch data from the internet (API call).
        # We search the iTunes API for a study song related to their degree.
        # try/except ensures that if the request fails (e.g. no internet),
        # the program doesn't crash — it just silently moves on.
        try:
            url = f"https://itunes.apple.com/search?entity=song&limit=1&term={self.degree}+study"
            response = requests.get(url)       # Send an HTTP GET request
            song_data = response.json()        # Parse the JSON response into a dictionary
            
            if song_data["results"]:
                track = song_data["results"][0]["trackName"]
                artist = song_data["results"][0]["artistName"]
                print(f"🎵 Recommended Study Song: '{track}' by {artist}")
        except Exception:
            # If the computer is offline or the API fails, just skip this feature
            pass

    def __str__(self):
        """__str__ is called when you use str(student) or print(student).
        It defines the "human-readable" representation of the object."""
        return f"{self.name} studies {self.degree} (Grade: {self.grade})"


class Undergraduate(Student):
    """Represents an undergraduate student.
    'Undergraduate(Student)' means this class INHERITS from Student.
    It gets all of Student's attributes and methods automatically,
    plus its own extra ones (year_of_study, year_in_industry)."""

    def __init__(self, name, degree, grade, year_of_study, year_in_industry):
        # super().__init__(...) calls the PARENT class (Student) constructor.
        # This sets up name, degree, grade, and modules for us.
        super().__init__(name, degree, grade)
        self.year_of_study = year_of_study
        self.year_in_industry = year_in_industry
        
    def __str__(self):
        """Override the parent's __str__ to include year info.
        super().__str__() calls the Student version first, then we add to it."""
        industry_text = " [Year in Industry]" if self.year_in_industry else ""
        return f"{super().__str__()} - Year {self.year_of_study}{industry_text}"


class Postgrad(Student):
    """Represents a postgraduate student. Inherits from Student and adds a thesis title."""

    def __init__(self, name, degree, grade, thesis_title):
        super().__init__(name, degree, grade)
        self.thesis_title = thesis_title

    def __str__(self):
        return f"{super().__str__()} - Thesis: '{self.thesis_title}'"


class AcademicStaff:
    """Represents a member of academic staff.
    This is NOT a subclass of Student — staff and students are different things."""

    def __init__(self, title, name, subject):
        if not name:
            raise ValueError("Missing name")
        self.title = title
        self.name = name
        self.subject = subject

    def __str__(self):
        return f"{self.title} {self.name} ({self.subject})"


class Module:
    """Represents a taught module (e.g. "Fundamentals of Programming").
    Each module has one academic staff member and a list of enrolled students."""

    def __init__(self, module_code, name, academic, time_slot):
        self.module_code = module_code
        self.name = name
        self.academic = academic           # An AcademicStaff object
        self.time_slot = time_slot
        self.enrolled_students = []        # Empty list — no students yet

    def add_student(self, student):
        """Add a student to this module, but only if they're not already enrolled.
        'not in' checks whether the student is already in the list."""
        if student not in self.enrolled_students:
            self.enrolled_students.append(student)

    def __str__(self):
        return f"{self.module_code}: {self.name} at {self.time_slot}"


# ==========================================
# PART 2: File I/O & Fake Data Generation
# ==========================================
# This section handles reading from and writing to CSV files.
# CSV (Comma-Separated Values) is a simple text format for storing tabular data.
# Each row is a line of text, and columns are separated by commas.
# Example:  Name,Degree,Grade
#           Alice,ECE,85
#           Bob,BIO,72


def generate_fake_files():
    """Create sample CSV files with fake data if they don't already exist.
    Uses the Faker library to generate realistic random names and job titles."""

    # Faker() creates a fake data generator object
    fake = Faker()
    degrees = ["ECE", "BIO", "MECH", "EEE", "COMP"]
    
    # os.path.exists() checks if a file already exists — we don't want to
    # overwrite data the user might have added
    if not os.path.exists("academics.csv"):
        # 'w' mode = write (creates a new file or overwrites an existing one)
        # newline='' prevents extra blank lines on Windows
        with open("academics.csv", "w", newline='') as file:
            writer = csv.writer(file)
            # First row is the header — column names
            writer.writerow(["Title", "Name", "Subject"])
            # Manual entries
            writer.writerow(["Dr.", "Horne", "Biomedical Engineering"])
            writer.writerow(["Prof.", "Smith", "Engineering"])
            
            # Generate 3 random academics using Faker
            # _ is used as the loop variable when we don't need the value
            for _ in range(3):
                writer.writerow(["Dr.", fake.last_name(), fake.job()])
        print("Created academics.csv with fake data.")

    if not os.path.exists("students.csv"):
        with open("students.csv", "w", newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Type", "Name", "Degree", "Grade", "Year", "Industry", "Thesis"])
            
            # One manual entry for our demo
            writer.writerow(["Undergrad", "Alice", "ECE", 85, 2, "False", "N/A"])
            
            # Generate 10 random students
            for _ in range(10):
                name = fake.first_name()            # Random first name
                degree = random.choice(degrees)     # Pick a random degree from the list
                grade = random.randint(40, 100)      # Random integer between 40 and 100
                
                # Randomly decide if this student is an Undergrad or Postgrad
                student_type = random.choice(["Undergrad", "Postgrad"])
                
                if student_type == "Undergrad":
                    year = random.randint(1, 4)
                    yin = random.choice(["True", "False"])
                    writer.writerow(["Undergrad", name, degree, grade, year, yin, "N/A"])
                else:  # Postgrad
                    thesis = fake.catch_phrase()  # Generate a random thesis-like title
                    writer.writerow(["Postgrad", name, degree, grade, "N/A", "N/A", thesis])
        print("Created students.csv with bulk fake data.")


def load_academics():
    """Read academics.csv and return a list of AcademicStaff objects.
    If the file doesn't exist, returns an empty list (no crash)."""
    academics = []
    try:
        with open("academics.csv", "r") as file:
            reader = csv.reader(file)       # csv.reader reads each row as a list of strings
            next(reader)                     # Skip the header row (column names)
            for row in reader:
                # row is a list like ["Dr.", "Horne", "Biomedical Engineering"]
                # row[0] = title, row[1] = name, row[2] = subject
                academics.append(AcademicStaff(row[0], row[1], row[2]))
    except FileNotFoundError:
        # If the file doesn't exist yet, just return the empty list
        pass
    return academics


def save_student(student):
    """Append a single student to students.csv.
    'a' mode = append (adds to end of file without overwriting).
    isinstance() checks which type/subclass the student is so we can
    save the right columns."""
    with open("students.csv", "a", newline='') as file:
        writer = csv.writer(file)
        # Check the student's type to decide what data to write
        # We must check Undergraduate/Postgrad BEFORE Student because
        # isinstance(undergraduate, Student) is also True (inheritance!)
        if isinstance(student, Undergraduate):
            writer.writerow(["Undergrad", student.name, student.degree, student.grade, student.year_of_study, student.year_in_industry])
        elif isinstance(student, Postgrad):
            writer.writerow(["Postgrad", student.name, student.degree, student.grade, "N/A", "N/A", student.thesis_title])
        else:
            writer.writerow(["Base", student.name, student.degree, student.grade, "N/A", "N/A", "N/A"])


def load_students():
    """Read students.csv and return a list of Student/Undergraduate/Postgrad objects.
    Each row's first column ("Type") tells us which class to create."""
    students = []
    try:
        with open("students.csv", "r") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            for row in reader:
                # row[0] is the student type, row[1] is name, row[2] is degree, etc.
                if row[0] == "Undergrad":
                    # int() converts strings to integers (CSV stores everything as text)
                    # row[5] == 'True' converts the string "True"/"False" to a boolean
                    students.append(Undergraduate(row[1], row[2], int(row[3]), int(row[4]), row[5] == 'True'))
                elif row[0] == "Postgrad":
                    students.append(Postgrad(row[1], row[2], int(row[3]), row[6]))
                else:
                    students.append(Student(row[1], row[2], int(row[3])))
    except FileNotFoundError:
        pass
    return students

# ==========================================
# PART 3: Main Execution & Demonstration
# ==========================================
# This section contains the main() function which is the entry point of our program.
# It uses sys.argv to determine what the user wants to do.
# sys.argv is a list of command-line arguments:
#   python3 sds.py list  →  sys.argv = ["sds.py", "list"]
#   sys.argv[0] = the script name, sys.argv[1] = the first argument


def main():
    # First, make sure our data files exist (creates them with fake data if not)
    generate_fake_files()
    
    # Check that the user provided a command
    if len(sys.argv) < 2:
        print("Too few arguments. Use 'add', 'list', 'academics', or 'demo'.")
        sys.exit()  # Exit the program immediately
        
    # .lower() converts to lowercase so "LIST", "List", and "list" all work
    mode = sys.argv[1].lower()
    
    if mode == "add":
        # --- Add a new student interactively ---
        # input() pauses the program and waits for the user to type something
        name = input("Name: ")
        degree = input("Degree (ECE, BIO, MECH, EEE, COMP): ")
        grade = int(input("Grade: "))  # int() converts the typed string to a number
        
        new_student = Student(name, degree, grade)
        save_student(new_student)
        
        # cowsay.cow() prints a fun ASCII cow with a message — from the cowsay library
        cowsay.cow(f"Success! Saved {name} to the database.")
        
    elif mode == "list":
        # --- List all students sorted alphabetically ---
        print("\n--- Student Roster ---")
        students = load_students()
        # sorted() returns a new sorted list. The lambda tells it to sort by name.
        for s in sorted(students, key=lambda s: s.name):
            print(s)  # This calls the __str__ method of each student
            
    elif mode == "academics":
        # --- List all academic staff ---
        print("\n--- Academic Staff ---")
        academics = load_academics()
        for a in academics:
            print(a)
            
    elif mode == "demo":
        # --- Run a full demonstration of the system ---
        print("\n--- Running System Demonstration ---")
        academics = load_academics()
        students = load_students()
        
        # next() with a generator expression finds the first matching item.
        # This is a compact way to search a list. The second argument (None)
        # is returned if no match is found, preventing an error.
        dr_horne = next((a for a in academics if a.name == "Horne"), None)
        alice = next((s for s in students if s.name == "Alice"), None)
        
        if dr_horne and alice:
            # Create a module and enrol Alice in it
            fop_module = Module("EENG4101", "Fundamentals of Programming", dr_horne, "Monday 10:00 AM")
            alice.enroll(fop_module)
            alice.print_timetable()
        else:
            print("Required data missing for demo.")


# This block only runs when the file is executed directly (python3 sds.py),
# NOT when it's imported by another file (e.g. the test file).
# This is a very common Python pattern.
if __name__ == "__main__":
    main()
