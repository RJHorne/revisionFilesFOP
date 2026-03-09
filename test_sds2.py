"""
test_sds2.py — Automated tests for the Expanded Student Data System (sds2.py)

This file tests the extended version of the student data system which includes
attendance tracking, degree classifications, at-risk detection, search/filter
functions, module capacity, and more.

HOW TESTING WORKS:
    - Each function starting with "test_" is automatically discovered and run by pytest.
    - We group related tests into classes (e.g. TestStudent, TestModule) for organisation.
    - 'assert' checks a condition is True — if False, the test fails.
    - 'pytest.raises' checks that code correctly raises an error when it should.

HOW TO RUN:
    python3 -m pytest test_sds2.py -v

SPECIAL PYTEST FEATURES USED:
    - capsys: a built-in pytest fixture that captures anything printed with print().
      We use it to check what our code outputs to the terminal.
      Usage: output = capsys.readouterr().out  →  gives us the printed text as a string.
    - setup_method: a method that runs BEFORE each test in a class (like a reset button).
    - teardown_method: a method that runs AFTER each test (for cleaning up).

TIP: Read through these tests alongside sds2.py to see how each feature is expected
     to behave. Tests are a great form of documentation!
"""

# --- Imports ---
import pytest
import os
import csv

# Import all the classes and functions we want to test from sds2.py
from sds2 import (
    Student, Undergraduate, Postgrad,
    AcademicStaff, Module,
    load_academics, load_students, save_student, save_all_students,
    generate_fake_files, load_modules, save_attendance, load_attendance,
    search_students, filter_by_degree, filter_by_classification,
    get_at_risk_students,
)


# ==========================================
# Helper functions
# ==========================================
# These are NOT tests — they are utility functions that make it quicker to
# create common objects so we don't have to type the same thing in every test.

def make_staff():
    """Create and return a simple AcademicStaff object for use in tests."""
    return AcademicStaff("Dr.", "Horne", "Engineering")


def make_module(staff=None, capacity=30):
    """Create and return a Module object.
    If no staff member is provided, one is created automatically.
    'capacity=30' is a default parameter — it's used unless the caller passes a different value."""
    if staff is None:
        staff = make_staff()
    return Module("E101", "Intro", staff, "Monday 9:00 AM", capacity)


# ==========================================
# Student class tests
# ==========================================
# This is the largest test class because Student has many features: creation,
# validation, enrolment, unenrolment, attendance tracking, classification,
# and at-risk detection.

class TestStudent:
    def test_create_student(self):
        """Check a Student is created with all the correct default values."""
        s = Student("Bob", "ECE", 75)
        assert s.name == "Bob"
        assert s.degree == "ECE"
        assert s.grade == 75
        assert s.modules == []      # No modules yet
        assert s.attendance == {}    # Empty dictionary — no attendance records yet

    def test_str(self):
        """Check the __str__ method outputs the expected format."""
        s = Student("Bob", "ECE", 75)
        assert str(s) == "Bob studies ECE (Grade: 75)"

    # --- Validation tests ---
    # These tests check that our class correctly rejects invalid input.
    # Good code should fail early with a clear error message rather than
    # silently accepting bad data.

    def test_missing_name_raises(self):
        """An empty name should raise a ValueError."""
        with pytest.raises(ValueError, match="Missing name"):
            Student("", "ECE", 75)

    def test_invalid_degree_raises(self):
        """A degree code not in the allowed list should raise a ValueError."""
        with pytest.raises(ValueError, match="Invalid degree"):
            Student("Bob", "ART", 75)

    def test_valid_degrees(self):
        """All valid degree codes should be accepted without error."""
        for degree in ["ECE", "BIO", "MECH", "EEE", "COMP"]:
            s = Student("Test", degree, 50)
            assert s.degree == degree

    def test_grade_too_low_raises(self):
        """A grade below 0 should raise a ValueError."""
        with pytest.raises(ValueError, match="Grade must be between 0 and 100"):
            Student("Bob", "ECE", -1)

    def test_grade_too_high_raises(self):
        """A grade above 100 should raise a ValueError."""
        with pytest.raises(ValueError, match="Grade must be between 0 and 100"):
            Student("Bob", "ECE", 101)

    # --- Boundary tests ---
    # "Boundary testing" means testing the exact edge values where behaviour changes.
    # If 0 and 100 are valid, we should check they work correctly.

    def test_grade_boundary_zero(self):
        """Grade of exactly 0 should be accepted (lower boundary)."""
        s = Student("Bob", "ECE", 0)
        assert s.grade == 0

    def test_grade_boundary_hundred(self):
        """Grade of exactly 100 should be accepted (upper boundary)."""
        s = Student("Bob", "ECE", 100)
        assert s.grade == 100

    # --- Enrol / unenrol tests ---
    # These test the bidirectional link: enrolling a student in a module should
    # update BOTH the student's module list AND the module's student list.

    def test_enroll(self):
        """Enrolling should add the module to the student AND the student to the module.
        It should also create an attendance entry for that module code."""
        mod = make_module()
        s = Student("Bob", "ECE", 75)
        s.enroll(mod)
        assert mod in s.modules                 # Student knows about the module
        assert s in mod.enrolled_students       # Module knows about the student
        assert mod.module_code in s.attendance  # Attendance dict has a key for this module

    def test_enroll_duplicate_ignored(self, capsys):
        """Enrolling in the same module twice should be silently ignored.
        capsys captures printed output so we can check the warning message."""
        mod = make_module()
        s = Student("Bob", "ECE", 75)
        s.enroll(mod)
        s.enroll(mod)  # Second time — should be ignored
        assert s.modules.count(mod) == 1             # Only listed once
        assert "already enrolled" in capsys.readouterr().out  # Warning was printed

    def test_unenroll(self):
        """Unenrolling should remove the module from the student and vice versa,
        and also remove the attendance records for that module."""
        mod = make_module()
        s = Student("Bob", "ECE", 75)
        s.enroll(mod)
        s.unenroll(mod)
        assert mod not in s.modules
        assert s not in mod.enrolled_students
        assert mod.module_code not in s.attendance

    def test_unenroll_not_enrolled(self, capsys):
        """Unenrolling from a module the student isn't in should print a warning."""
        mod = make_module()
        s = Student("Bob", "ECE", 75)
        s.unenroll(mod)
        assert "not enrolled" in capsys.readouterr().out

    # --- Attendance tests ---
    # Attendance is tracked as a dictionary: { "module_code": [True, False, True, ...] }
    # Each True/False represents whether the student attended a session.

    def test_record_attendance(self):
        """Recording attendance should append True/False to the module's attendance list."""
        mod = make_module()
        s = Student("Bob", "ECE", 75)
        s.enroll(mod)
        s.record_attendance("E101", True)   # Attended session 1
        s.record_attendance("E101", False)  # Missed session 2
        assert s.attendance["E101"] == [True, False]

    def test_record_attendance_not_enrolled(self, capsys):
        """Recording attendance for a module the student isn't enrolled in
        should print a warning rather than crash."""
        s = Student("Bob", "ECE", 75)
        s.record_attendance("E101", True)
        assert "not enrolled" in capsys.readouterr().out

    def test_attendance_percentage_full(self):
        """100% attendance: attended all 10 sessions."""
        mod = make_module()
        s = Student("Bob", "ECE", 75)
        s.enroll(mod)
        for _ in range(10):
            s.record_attendance("E101", True)
        assert s.get_attendance_percentage("E101") == 100.0

    def test_attendance_percentage_half(self):
        """50% attendance: attended 5 out of 10 sessions."""
        mod = make_module()
        s = Student("Bob", "ECE", 75)
        s.enroll(mod)
        for _ in range(5):
            s.record_attendance("E101", True)
        for _ in range(5):
            s.record_attendance("E101", False)
        assert s.get_attendance_percentage("E101") == 50.0

    def test_attendance_percentage_no_records(self):
        """With no attendance records yet, percentage should be 0.0."""
        mod = make_module()
        s = Student("Bob", "ECE", 75)
        s.enroll(mod)
        assert s.get_attendance_percentage("E101") == 0.0

    def test_attendance_percentage_not_enrolled(self):
        """Checking attendance for a module not enrolled in should return 0.0."""
        s = Student("Bob", "ECE", 75)
        assert s.get_attendance_percentage("E101") == 0.0

    # --- Classification tests ---
    # Degree classification is determined by the student's grade:
    #   70+ = First, 60-69 = 2:1, 50-59 = 2:2, 40-49 = Third, <40 = Fail

    def test_classification_first(self):
        """Grades 70 and above should give a First."""
        assert Student("A", "ECE", 70).get_classification() == "First"
        assert Student("A", "ECE", 100).get_classification() == "First"

    def test_classification_upper_second(self):
        """Grades 60-69 should give an Upper Second (2:1)."""
        assert Student("A", "ECE", 60).get_classification() == "Upper Second (2:1)"
        assert Student("A", "ECE", 69).get_classification() == "Upper Second (2:1)"

    def test_classification_lower_second(self):
        """Grades 50-59 should give a Lower Second (2:2)."""
        assert Student("A", "ECE", 50).get_classification() == "Lower Second (2:2)"
        assert Student("A", "ECE", 59).get_classification() == "Lower Second (2:2)"

    def test_classification_third(self):
        """Grades 40-49 should give a Third."""
        assert Student("A", "ECE", 40).get_classification() == "Third"
        assert Student("A", "ECE", 49).get_classification() == "Third"

    def test_classification_fail(self):
        """Grades below 40 should give a Fail."""
        assert Student("A", "ECE", 0).get_classification() == "Fail"
        assert Student("A", "ECE", 39).get_classification() == "Fail"

    # --- At-risk detection tests ---
    # A student is "at risk" if their grade is below 40 OR if any module
    # has attendance below 50%.

    def test_at_risk_low_grade(self):
        """A student with a grade below 40 should be flagged as at risk."""
        s = Student("Bob", "ECE", 35)
        assert s.is_at_risk() is True

    def test_not_at_risk_good_grade(self):
        """A student with a good grade and no attendance issues is NOT at risk."""
        s = Student("Bob", "ECE", 75)
        assert s.is_at_risk() is False

    def test_at_risk_low_attendance(self):
        """A student with only 25% attendance should be flagged as at risk,
        even if their grade is fine."""
        mod = make_module()
        s = Student("Bob", "ECE", 75)
        s.enroll(mod)
        s.record_attendance("E101", True)    # 1 attended
        s.record_attendance("E101", False)   # 3 missed
        s.record_attendance("E101", False)
        s.record_attendance("E101", False)
        # 25% attendance → at risk
        assert s.is_at_risk() is True

    def test_not_at_risk_good_attendance(self):
        """80% attendance is above the 50% threshold, so NOT at risk."""
        mod = make_module()
        s = Student("Bob", "ECE", 75)
        s.enroll(mod)
        for _ in range(8):
            s.record_attendance("E101", True)
        for _ in range(2):
            s.record_attendance("E101", False)
        assert s.is_at_risk() is False

    # --- Print method tests ---
    # We don't check the exact output — just that the methods run without
    # crashing and include some expected text. capsys captures print output.

    def test_print_timetable(self, capsys):
        """Check that print_timetable runs and includes the student's name."""
        s = Student("Bob", "ECE", 75)
        s.print_timetable()
        output = capsys.readouterr().out
        assert "Timetable for Bob" in output

    def test_print_report(self, capsys):
        """Check that print_report runs and includes key information."""
        s = Student("Bob", "ECE", 75)
        s.print_report()
        output = capsys.readouterr().out
        assert "STUDENT REPORT: Bob" in output
        assert "First" in output  # Grade 75 → First class


# ==========================================
# Undergraduate class tests
# ==========================================
# Undergraduate extends Student with year_of_study and year_in_industry.
# We test both the new attributes and that inheritance from Student still works.

class TestUndergraduate:
    def test_create(self):
        """Check Undergraduate-specific attributes are stored correctly."""
        u = Undergraduate("Alice", "ECE", 85, 2, False)
        assert u.year_of_study == 2
        assert u.year_in_industry is False

    def test_str_no_industry(self):
        """String output for a student without a year in industry."""
        u = Undergraduate("Alice", "ECE", 85, 2, False)
        assert str(u) == "Alice studies ECE (Grade: 85) - Year 2"

    def test_str_with_industry(self):
        """String output should include [Year in Industry] when applicable."""
        u = Undergraduate("Alice", "ECE", 85, 3, True)
        assert "[Year in Industry]" in str(u)

    def test_inherits_from_student(self):
        """Undergraduate should also be recognised as a Student (inheritance)."""
        u = Undergraduate("Alice", "ECE", 85, 2, False)
        assert isinstance(u, Student)

    def test_invalid_year_too_low(self):
        """Year of study 0 is not valid — should raise ValueError."""
        with pytest.raises(ValueError, match="Year of study must be between 1 and 4"):
            Undergraduate("Alice", "ECE", 85, 0, False)

    def test_invalid_year_too_high(self):
        """Year of study 5 is not valid — should raise ValueError."""
        with pytest.raises(ValueError, match="Year of study must be between 1 and 4"):
            Undergraduate("Alice", "ECE", 85, 5, False)


# ==========================================
# Postgrad class tests
# ==========================================

class TestPostgrad:
    def test_create(self):
        """Check thesis_title is stored correctly."""
        p = Postgrad("Charlie", "BIO", 90, "Gene Editing")
        assert p.thesis_title == "Gene Editing"

    def test_str(self):
        """String output should include the thesis title."""
        p = Postgrad("Charlie", "BIO", 90, "Gene Editing")
        assert "Thesis: 'Gene Editing'" in str(p)

    def test_inherits_from_student(self):
        """Postgrad should also be recognised as a Student."""
        p = Postgrad("Charlie", "BIO", 90, "Gene Editing")
        assert isinstance(p, Student)

    def test_empty_thesis_raises(self):
        """A postgrad must have a thesis title — empty string should raise ValueError."""
        with pytest.raises(ValueError, match="Postgrad students must have a thesis title"):
            Postgrad("Charlie", "BIO", 90, "")


# ==========================================
# AcademicStaff class tests
# ==========================================

class TestAcademicStaff:
    def test_create(self):
        """Check all attributes are stored and modules_taught starts empty."""
        a = AcademicStaff("Dr.", "Horne", "Engineering")
        assert a.title == "Dr."
        assert a.name == "Horne"
        assert a.modules_taught == []  # No modules assigned yet

    def test_str(self):
        """Check string representation format."""
        a = AcademicStaff("Prof.", "Smith", "Engineering")
        assert str(a) == "Prof. Smith (Engineering)"

    def test_missing_name_raises(self):
        """Empty name should raise ValueError."""
        with pytest.raises(ValueError, match="Missing name"):
            AcademicStaff("Dr.", "", "Engineering")

    def test_invalid_title_raises(self):
        """Only certain titles (Dr., Prof., Mr., Mrs., Ms.) are valid."""
        with pytest.raises(ValueError, match="Invalid title"):
            AcademicStaff("Sir", "Horne", "Engineering")

    def test_valid_titles(self):
        """All allowed titles should be accepted without error."""
        for title in ["Dr.", "Prof.", "Mr.", "Mrs.", "Ms."]:
            a = AcademicStaff(title, "Test", "Subject")
            assert a.title == title

    def test_assign_module(self):
        """Creating a Module with a staff member should automatically assign it.
        The Module constructor calls staff.assign_module(self) internally."""
        staff = make_staff()
        mod = Module("E101", "Intro", staff, "Monday 9:00 AM")
        assert mod in staff.modules_taught

    def test_assign_module_no_duplicate(self):
        """Assigning the same module twice should not create duplicates."""
        staff = make_staff()
        mod = Module("E101", "Intro", staff, "Monday 9:00 AM")
        staff.assign_module(mod)  # Try to add again
        assert staff.modules_taught.count(mod) == 1

    def test_print_workload(self, capsys):
        """Check that print_workload outputs the staff member's name.
        capsys.readouterr().out gives us whatever was printed to the terminal."""
        staff = make_staff()
        Module("E101", "Intro", staff, "Monday 9:00 AM")
        staff.print_workload()
        output = capsys.readouterr().out
        assert "Workload for Dr. Horne" in output


# ==========================================
# Module class tests
# ==========================================
# Modules have a capacity limit, can calculate average grades and pass rates,
# and track enrolled students.

class TestModule:
    def test_create(self):
        """Check module attributes and that enrolled_students starts empty."""
        staff = make_staff()
        mod = Module("E101", "Intro", staff, "Monday 9:00 AM", 25)
        assert mod.module_code == "E101"
        assert mod.capacity == 25
        assert mod.enrolled_students == []

    def test_str(self):
        """Check string representation of a module."""
        mod = make_module()
        assert str(mod) == "E101: Intro at Monday 9:00 AM"

    def test_missing_code_raises(self):
        """A module must have a code — empty string should raise ValueError."""
        staff = make_staff()
        with pytest.raises(ValueError, match="Module code is required"):
            Module("", "Intro", staff, "Monday 9:00 AM")

    def test_add_student(self):
        """Check that add_student adds the student to the enrolled list."""
        mod = make_module()
        s = Student("Bob", "ECE", 75)
        mod.add_student(s)
        assert s in mod.enrolled_students

    def test_add_student_no_duplicate(self):
        """Adding the same student twice should not create a duplicate entry."""
        mod = make_module()
        s = Student("Bob", "ECE", 75)
        mod.add_student(s)
        mod.add_student(s)
        assert mod.enrolled_students.count(s) == 1

    def test_add_student_over_capacity(self, capsys):
        """When a module is full (capacity reached), additional students should
        be rejected and a warning printed."""
        mod = make_module(capacity=2)  # Only room for 2 students
        s1 = Student("A", "ECE", 70)
        s2 = Student("B", "ECE", 80)
        s3 = Student("C", "ECE", 60)
        mod.add_student(s1)
        mod.add_student(s2)
        mod.add_student(s3)  # This should be rejected — module is full
        assert len(mod.enrolled_students) == 2  # Only 2 students enrolled
        assert "full" in capsys.readouterr().out

    def test_remove_student(self):
        """Check that remove_student takes the student off the module's list."""
        mod = make_module()
        s = Student("Bob", "ECE", 75)
        mod.add_student(s)
        mod.remove_student(s)
        assert s not in mod.enrolled_students

    def test_remove_student_not_enrolled(self):
        """Removing a student who isn't enrolled should not crash."""
        mod = make_module()
        s = Student("Bob", "ECE", 75)
        mod.remove_student(s)  # Should handle gracefully

    # --- Module statistics ---

    def test_average_grade_empty(self):
        """Average grade of a module with no students should be 0.0."""
        mod = make_module()
        assert mod.get_average_grade() == 0.0

    def test_average_grade(self):
        """Average of 60 and 80 should be 70.0."""
        mod = make_module()
        mod.add_student(Student("A", "ECE", 60))
        mod.add_student(Student("B", "ECE", 80))
        assert mod.get_average_grade() == 70.0

    def test_pass_rate_empty(self):
        """Pass rate of a module with no students should be 0.0."""
        mod = make_module()
        assert mod.get_pass_rate() == 0.0

    def test_pass_rate_all_pass(self):
        """If all students have grade >= 40, pass rate should be 100%."""
        mod = make_module()
        mod.add_student(Student("A", "ECE", 50))
        mod.add_student(Student("B", "ECE", 80))
        assert mod.get_pass_rate() == 100.0

    def test_pass_rate_some_fail(self):
        """One student passes (80), one fails (30) → 50% pass rate."""
        mod = make_module()
        mod.add_student(Student("A", "ECE", 30))
        mod.add_student(Student("B", "ECE", 80))
        assert mod.get_pass_rate() == 50.0

    def test_print_class_list(self, capsys):
        """Check that print_class_list outputs module info and student names."""
        mod = make_module()
        mod.add_student(Student("Bob", "ECE", 75))
        mod.print_class_list()
        output = capsys.readouterr().out
        assert "E101: Intro" in output
        assert "Bob" in output


# ==========================================
# Search & filter function tests
# ==========================================
# These test the standalone functions (not class methods) that search and
# filter lists of students. setup_method creates a shared list of students
# that every test in this class can use.

class TestSearchAndFilter:
    def setup_method(self):
        """Create a sample list of students for all search/filter tests to use.
        This runs before EACH test, so every test gets a fresh copy."""
        self.students = [
            Student("Alice", "ECE", 85),
            Student("Bob", "BIO", 45),
            Student("Charlie", "ECE", 35),
            Student("Alicia", "MECH", 62),
            Undergraduate("Dave", "EEE", 72, 2, True),
            Postgrad("Eve", "COMP", 55, "AI Ethics"),
        ]

    # --- Search by name ---

    def test_search_exact(self):
        """Searching for the exact name "Alice" should return 1 result."""
        results = search_students(self.students, "Alice")
        assert len(results) == 1
        assert results[0].name == "Alice"

    def test_search_partial(self):
        """Searching for "ali" should match both "Alice" and "Alicia"
        (partial, case-insensitive matching)."""
        results = search_students(self.students, "ali")
        assert len(results) == 2

    def test_search_case_insensitive(self):
        """Search should work regardless of upper/lower case."""
        results = search_students(self.students, "BOB")
        assert len(results) == 1

    def test_search_no_results(self):
        """Searching for a name that doesn't exist should return an empty list."""
        results = search_students(self.students, "Zoe")
        assert len(results) == 0

    # --- Filter by degree ---

    def test_filter_by_degree(self):
        """Filtering by "ECE" should return Alice and Charlie."""
        results = filter_by_degree(self.students, "ECE")
        assert len(results) == 2

    def test_filter_by_degree_none(self):
        """Filtering by "BIO" should return just Bob."""
        results = filter_by_degree(self.students, "BIO")
        assert len(results) == 1

    # --- Filter by classification ---

    def test_filter_by_classification(self):
        """Students with "First" classification (grade >= 70): Alice (85) and Dave (72)."""
        results = filter_by_classification(self.students, "First")
        assert len(results) == 2

    def test_filter_by_classification_fail(self):
        """Students with "Fail" classification (grade < 40): Charlie (35)."""
        results = filter_by_classification(self.students, "Fail")
        assert len(results) == 1

    # --- At-risk detection ---

    def test_get_at_risk_low_grade(self):
        """Students with grade < 40 should be flagged as at risk.
        Bob (45) is also at risk because grade < 50 triggers the at-risk threshold."""
        at_risk = get_at_risk_students(self.students)
        names = [s.name for s in at_risk]
        assert "Charlie" in names  # Grade 35 → at risk
        assert "Bob" in names      # Grade 45 → at risk

    def test_get_at_risk_good_students_excluded(self):
        """Students with good grades should NOT appear in the at-risk list."""
        at_risk = get_at_risk_students(self.students)
        names = [s.name for s in at_risk]
        assert "Alice" not in names  # Grade 85 → fine
        assert "Dave" not in names   # Grade 72 → fine


# ==========================================
# File I/O tests
# ==========================================
# These tests verify that saving data to CSV files and loading it back
# produces the correct results. We use a temporary folder so that tests
# don't interfere with real data files.

class TestFileIO:
    def setup_method(self):
        """Runs BEFORE each test.
        Creates a temporary folder and moves into it, so all file operations
        happen in an isolated location that won't affect your real files."""
        self.original_dir = os.getcwd()
        self.test_dir = os.path.join(self.original_dir, "test_temp")
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Runs AFTER each test.
        Returns to the original directory and deletes the temporary folder
        and everything inside it. This keeps your workspace clean."""
        os.chdir(self.original_dir)
        for filename in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, filename))
        os.rmdir(self.test_dir)

    # --- Generate fake data ---

    def test_generate_fake_files(self):
        """Check that generate_fake_files() creates all expected CSV files."""
        generate_fake_files()
        assert os.path.exists("academics.csv")
        assert os.path.exists("students.csv")
        assert os.path.exists("modules.csv")
        assert os.path.exists("attendance.csv")

    def test_generate_does_not_overwrite(self):
        """If a file already exists, generate_fake_files() should NOT overwrite it.
        We create a custom file first, then check it's still there afterwards."""
        with open("academics.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Name", "Subject"])
            writer.writerow(["Dr.", "Custom", "Testing"])
        generate_fake_files()
        academics = load_academics()
        assert any(a.name == "Custom" for a in academics)

    # --- Load academics ---

    def test_load_academics(self):
        """Write a CSV with 2 academics, then check load_academics() reads them."""
        with open("academics.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Name", "Subject"])
            writer.writerow(["Dr.", "Horne", "Engineering"])
            writer.writerow(["Prof.", "Smith", "Maths"])
        academics = load_academics()
        assert len(academics) == 2
        assert academics[0].name == "Horne"

    def test_load_academics_file_missing(self):
        """If the file doesn't exist, load_academics() should return [] not crash."""
        assert load_academics() == []

    # --- Save and load students ---

    def test_save_and_load_base_student(self):
        """Save a base Student to CSV and load it back — check data is preserved."""
        with open("students.csv", "w", newline='') as f:
            csv.writer(f).writerow(["Type", "Name", "Degree", "Grade", "Year", "Industry", "Thesis"])
        save_student(Student("Test", "ECE", 60))
        students = load_students()
        assert len(students) == 1
        assert students[0].name == "Test"

    def test_save_and_load_undergraduate(self):
        """Check that an Undergraduate's type and attributes survive save/load."""
        with open("students.csv", "w", newline='') as f:
            csv.writer(f).writerow(["Type", "Name", "Degree", "Grade", "Year", "Industry", "Thesis"])
        save_student(Undergraduate("Alice", "ECE", 85, 2, True))
        students = load_students()
        assert len(students) == 1
        assert isinstance(students[0], Undergraduate)  # Correct subclass
        assert students[0].year_in_industry is True     # Boolean preserved

    def test_save_and_load_postgrad(self):
        """Check that a Postgrad's thesis_title survives save/load."""
        with open("students.csv", "w", newline='') as f:
            csv.writer(f).writerow(["Type", "Name", "Degree", "Grade", "Year", "Industry", "Thesis"])
        save_student(Postgrad("Charlie", "BIO", 90, "Gene Editing"))
        students = load_students()
        assert len(students) == 1
        assert isinstance(students[0], Postgrad)
        assert students[0].thesis_title == "Gene Editing"

    def test_load_students_file_missing(self):
        """Missing file should return an empty list, not crash."""
        assert load_students() == []

    # --- Save all students at once ---

    def test_save_all_students(self):
        """save_all_students writes multiple students to CSV in one go.
        We save 3 students of different types and check they all load back."""
        students = [
            Student("A", "ECE", 70),
            Undergraduate("B", "BIO", 55, 1, False),
            Postgrad("C", "COMP", 80, "Robotics"),
        ]
        save_all_students(students)
        loaded = load_students()
        assert len(loaded) == 3
        assert loaded[0].name == "A"
        assert isinstance(loaded[1], Undergraduate)
        assert isinstance(loaded[2], Postgrad)

    def test_save_all_overwrites(self):
        """save_all_students should REPLACE the file contents, not append.
        After saving [A, B] then saving [C], we should only get [C] back."""
        save_all_students([Student("A", "ECE", 70), Student("B", "BIO", 60)])
        save_all_students([Student("C", "MECH", 50)])  # Overwrites previous
        loaded = load_students()
        assert len(loaded) == 1
        assert loaded[0].name == "C"

    # --- Load modules ---

    def test_load_modules(self):
        """Create CSV files for academics and modules, then check that
        load_modules correctly links each module to its academic staff member."""
        with open("academics.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Name", "Subject"])
            writer.writerow(["Dr.", "Horne", "Engineering"])
        with open("modules.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["ModuleCode", "Name", "AcademicName", "TimeSlot", "Capacity"])
            writer.writerow(["E101", "Intro", "Horne", "Monday 9:00 AM", 30])
        academics = load_academics()
        modules = load_modules(academics)
        assert len(modules) == 1
        assert modules[0].module_code == "E101"
        assert modules[0].academic.name == "Horne"  # Linked to the right staff member

    def test_load_modules_missing_academic_skipped(self):
        """If a module's academic name doesn't match any loaded staff member,
        that module should be skipped (not loaded)."""
        with open("academics.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Name", "Subject"])
            writer.writerow(["Dr.", "Horne", "Engineering"])
        with open("modules.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["ModuleCode", "Name", "AcademicName", "TimeSlot", "Capacity"])
            writer.writerow(["E101", "Intro", "Nobody", "Monday 9:00 AM", 30])
        academics = load_academics()
        modules = load_modules(academics)
        assert len(modules) == 0  # Skipped because "Nobody" isn't a loaded academic

    def test_load_modules_file_missing(self):
        """Missing modules file should return an empty list."""
        assert load_modules([]) == []

    # --- Attendance save/load ---

    def test_save_and_load_attendance(self):
        """Save individual attendance records to CSV, then load them back
        and check they're correctly attached to the right student."""
        with open("attendance.csv", "w", newline='') as f:
            csv.writer(f).writerow(["StudentName", "ModuleCode", "Session", "Present"])
        save_attendance("Alice", "E101", 1, True)
        save_attendance("Alice", "E101", 2, False)
        # Load the attendance back — it should be attached to Alice's attendance dict
        students = [Student("Alice", "ECE", 85)]
        load_attendance(students)
        assert "E101" in students[0].attendance
        assert students[0].attendance["E101"] == [True, False]

    def test_load_attendance_file_missing(self):
        """If the attendance file doesn't exist, load_attendance should not crash
        and should leave the student's attendance dict unchanged."""
        students = [Student("Alice", "ECE", 85)]
        load_attendance(students)  # Should handle missing file gracefully
        assert students[0].attendance == {}
