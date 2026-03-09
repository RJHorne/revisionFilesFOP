"""
test_sds.py — Automated tests for the Student Data System (sds.py)

HOW TESTING WORKS:
    - We write small functions called "tests" that check if our code behaves correctly.
    - Each test creates objects, calls methods, and uses 'assert' to verify the result.
    - If every assert passes, the test passes. If any assert fails, the test fails.

HOW TO RUN:
    python3 -m pytest test_sds.py -v

    The -v flag means "verbose" — it shows each test name and whether it passed or failed.

KEY CONCEPTS USED:
    - assert: checks that a condition is True. If it's False, the test fails.
    - pytest.raises: checks that a specific error (exception) is raised.
    - isinstance(): checks if an object is an instance of a particular class (useful for
      testing inheritance — e.g. an Undergraduate should also be a Student).
    - setup_method / teardown_method: special methods that run before/after EACH test
      in a class, used here to create and clean up temporary test folders.
"""

# --- Imports ---
# pytest is the testing framework we use to run and organise our tests
import pytest

# os lets us work with the file system (creating folders, changing directory, etc.)
import os

# csv lets us read and write CSV files (comma-separated values)
import csv

# We import everything we want to test from sds.py
from sds import (
    Student, Undergraduate, Postgrad,
    AcademicStaff, Module,
    load_academics, load_students, save_student, generate_fake_files,
)


# ==========================================
# Student class tests
# ==========================================
# Each class groups related tests together. pytest finds any method starting
# with "test_" inside a class starting with "Test" and runs it as a test.

class TestStudent:
    def test_create_student(self):
        """Check that a Student object is created with the correct attributes."""
        s = Student("Bob", "ECE", 75)
        assert s.name == "Bob"
        assert s.degree == "ECE"
        assert s.grade == 75
        assert s.modules == []  # New student should have no modules yet

    def test_str(self):
        """Check that converting a Student to a string gives the expected format.
        This tests the __str__ method of the Student class."""
        s = Student("Bob", "ECE", 75)
        assert str(s) == "Bob studies ECE (Grade: 75)"

    def test_missing_name_raises(self):
        """Check that creating a Student with an empty name raises a ValueError.
        'with pytest.raises(ValueError)' means: "the code inside this block
        SHOULD raise a ValueError — if it doesn't, the test fails."
        The 'match' parameter checks that the error message contains "Missing name"."""
        with pytest.raises(ValueError, match="Missing name"):
            Student("", "ECE", 75)

    def test_invalid_degree_raises(self):
        """Check that an invalid degree code raises a ValueError."""
        with pytest.raises(ValueError, match="Invalid degree"):
            Student("Bob", "ART", 75)

    def test_valid_degrees(self):
        """Check that all valid degree codes are accepted without error.
        We use a for loop to test multiple values efficiently."""
        for degree in ["ECE", "BIO", "MECH", "EEE", "COMP"]:
            s = Student("Test", degree, 50)
            assert s.degree == degree

    def test_enroll(self):
        """Check that enrolling a student in a module updates both the student's
        module list AND the module's enrolled_students list (bidirectional link)."""
        staff = AcademicStaff("Dr.", "Horne", "Engineering")
        mod = Module("E101", "Intro", staff, "Monday 9:00 AM")
        s = Student("Bob", "ECE", 75)
        s.enroll(mod)
        assert mod in s.modules            # Module appears in student's list
        assert s in mod.enrolled_students  # Student appears in module's list


# ==========================================
# Undergraduate class tests
# ==========================================
# Undergraduate inherits from Student, so we test the extra attributes
# (year_of_study, year_in_industry) as well as checking inheritance works.

class TestUndergraduate:
    def test_create_undergraduate(self):
        """Check that Undergraduate-specific attributes are stored correctly."""
        u = Undergraduate("Alice", "ECE", 85, 2, False)
        assert u.name == "Alice"          # Inherited from Student
        assert u.year_of_study == 2       # Undergraduate-specific
        assert u.year_in_industry is False

    def test_str_no_industry(self):
        """Check string output for a student WITHOUT a year in industry."""
        u = Undergraduate("Alice", "ECE", 85, 2, False)
        assert str(u) == "Alice studies ECE (Grade: 85) - Year 2"

    def test_str_with_industry(self):
        """Check string output for a student WITH a year in industry."""
        u = Undergraduate("Alice", "ECE", 85, 3, True)
        assert str(u) == "Alice studies ECE (Grade: 85) - Year 3 [Year in Industry]"

    def test_inherits_from_student(self):
        """Verify that Undergraduate is a subclass of Student.
        isinstance(u, Student) returns True because Undergraduate inherits from Student."""
        u = Undergraduate("Alice", "ECE", 85, 2, False)
        assert isinstance(u, Student)


# ==========================================
# Postgrad class tests
# ==========================================

class TestPostgrad:
    def test_create_postgrad(self):
        """Check that a Postgrad stores the thesis_title correctly."""
        p = Postgrad("Charlie", "BIO", 90, "Gene Editing")
        assert p.name == "Charlie"
        assert p.thesis_title == "Gene Editing"

    def test_str(self):
        """Check the string representation includes the thesis title."""
        p = Postgrad("Charlie", "BIO", 90, "Gene Editing")
        assert str(p) == "Charlie studies BIO (Grade: 90) - Thesis: 'Gene Editing'"

    def test_inherits_from_student(self):
        """Verify that Postgrad is also a Student (via inheritance)."""
        p = Postgrad("Charlie", "BIO", 90, "Gene Editing")
        assert isinstance(p, Student)


# ==========================================
# AcademicStaff class tests
# ==========================================

class TestAcademicStaff:
    def test_create_staff(self):
        """Check that an AcademicStaff object stores all its attributes."""
        a = AcademicStaff("Dr.", "Horne", "Biomedical Engineering")
        assert a.title == "Dr."
        assert a.name == "Horne"
        assert a.subject == "Biomedical Engineering"

    def test_str(self):
        """Check the string representation of a staff member."""
        a = AcademicStaff("Prof.", "Smith", "Engineering")
        assert str(a) == "Prof. Smith (Engineering)"

    def test_missing_name_raises(self):
        """Check that creating staff with an empty name raises an error."""
        with pytest.raises(ValueError, match="Missing name"):
            AcademicStaff("Dr.", "", "Engineering")


# ==========================================
# Module class tests
# ==========================================

class TestModule:
    def test_create_module(self):
        """Check that a Module is created with the correct attributes."""
        staff = AcademicStaff("Dr.", "Horne", "Engineering")
        mod = Module("E101", "Intro", staff, "Monday 9:00 AM")
        assert mod.module_code == "E101"
        assert mod.name == "Intro"
        assert mod.academic is staff          # 'is' checks it's the exact same object
        assert mod.enrolled_students == []    # No students enrolled yet

    def test_str(self):
        """Check the string representation of a module."""
        staff = AcademicStaff("Dr.", "Horne", "Engineering")
        mod = Module("E101", "Intro", staff, "Monday 9:00 AM")
        assert str(mod) == "E101: Intro at Monday 9:00 AM"

    def test_add_student(self):
        """Check that add_student puts a student into the enrolled list."""
        staff = AcademicStaff("Dr.", "Horne", "Engineering")
        mod = Module("E101", "Intro", staff, "Monday 9:00 AM")
        s = Student("Bob", "ECE", 75)
        mod.add_student(s)
        assert s in mod.enrolled_students

    def test_add_student_no_duplicates(self):
        """Check that adding the same student twice doesn't create a duplicate.
        .count(s) returns how many times s appears in the list — should be 1."""
        staff = AcademicStaff("Dr.", "Horne", "Engineering")
        mod = Module("E101", "Intro", staff, "Monday 9:00 AM")
        s = Student("Bob", "ECE", 75)
        mod.add_student(s)
        mod.add_student(s)  # Try adding again
        assert mod.enrolled_students.count(s) == 1


# ==========================================
# File I/O tests
# ==========================================
# These tests check that saving to and loading from CSV files works correctly.
# Because we don't want to mess up real data files, we create a temporary
# folder for each test and clean it up afterwards.

class TestFileIO:
    def setup_method(self):
        """Runs BEFORE each test method in this class.
        - Saves our current directory so we can return to it later.
        - Creates a fresh temporary folder called 'test_temp'.
        - Changes into that folder so all file operations happen there."""
        self.original_dir = os.getcwd()                             # Remember where we are
        self.test_dir = os.path.join(self.original_dir, "test_temp")
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)                              # Create the temp folder
        os.chdir(self.test_dir)                                     # Move into it

    def teardown_method(self):
        """Runs AFTER each test method in this class.
        - Goes back to the original directory.
        - Deletes all files in the temp folder, then removes the folder itself.
        This ensures each test starts with a clean slate."""
        os.chdir(self.original_dir)                                 # Go back to original dir
        for filename in os.listdir(self.test_dir):                  # Delete every file
            os.remove(os.path.join(self.test_dir, filename))
        os.rmdir(self.test_dir)                                     # Remove the now-empty folder

    def test_generate_fake_files(self):
        """Check that generate_fake_files() creates the expected CSV files."""
        generate_fake_files()
        assert os.path.exists("academics.csv")
        assert os.path.exists("students.csv")

    def test_generate_does_not_overwrite(self):
        """Check that generate_fake_files() does NOT overwrite an existing file.
        We create a custom academics.csv first, then call generate_fake_files().
        Our custom data should still be there."""
        with open("academics.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Name", "Subject"])
            writer.writerow(["Dr.", "Custom", "Testing"])
        generate_fake_files()
        academics = load_academics()
        # any() returns True if at least one academic has the name "Custom"
        assert any(a.name == "Custom" for a in academics)

    def test_load_academics(self):
        """Check that load_academics() correctly reads staff from a CSV file.
        We manually write a CSV, then check that load_academics() returns
        the right AcademicStaff objects."""
        with open("academics.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Name", "Subject"])           # Header row
            writer.writerow(["Dr.", "Horne", "Biomedical Engineering"])  # Data row
        academics = load_academics()
        assert len(academics) == 1
        assert academics[0].name == "Horne"

    def test_load_academics_file_missing(self):
        """Check that load_academics() returns an empty list if the file doesn't exist,
        rather than crashing with a FileNotFoundError."""
        academics = load_academics()
        assert academics == []

    def test_save_and_load_base_student(self):
        """Check that saving a base Student to CSV and loading it back works.
        We create the CSV header first, save a student, then load and verify."""
        with open("students.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Type", "Name", "Degree", "Grade", "Year", "Industry", "Thesis"])
        s = Student("Test", "ECE", 60)
        save_student(s)
        students = load_students()
        assert len(students) == 1
        assert students[0].name == "Test"

    def test_save_and_load_undergraduate(self):
        """Check that an Undergraduate survives the save/load round-trip.
        After loading, the object should be an Undergraduate (not just a Student)
        and year_in_industry should be preserved."""
        with open("students.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Type", "Name", "Degree", "Grade", "Year", "Industry", "Thesis"])
        u = Undergraduate("Alice", "ECE", 85, 2, True)
        save_student(u)
        students = load_students()
        assert len(students) == 1
        assert isinstance(students[0], Undergraduate)   # Should be the right subclass
        assert students[0].year_in_industry is True      # Boolean should be preserved

    def test_save_and_load_postgrad(self):
        """Check that a Postgrad survives the save/load round-trip,
        including its thesis_title."""
        with open("students.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Type", "Name", "Degree", "Grade", "Year", "Industry", "Thesis"])
        p = Postgrad("Charlie", "BIO", 90, "Gene Editing")
        save_student(p)
        students = load_students()
        assert len(students) == 1
        assert isinstance(students[0], Postgrad)
        assert students[0].thesis_title == "Gene Editing"

    def test_load_students_file_missing(self):
        """Check that load_students() returns an empty list if the file doesn't exist."""
        students = load_students()
        assert students == []
