"""
sds2.py — Student Data System (Expanded Version)

An extended command-line application that manages students, academic staff,
modules, attendance, and statistics. Builds upon sds.py with many additional
features while using the same core Python concepts:

    - Classes and inheritance (OOP)
    - Input validation (raising ValueError for bad data)
    - File I/O with CSV files (reading, writing, appending)
    - External libraries (requests, cowsay, faker)
    - Command-line arguments with sys.argv
    - Searching and filtering lists
    - Calculating statistics (averages, pass rates)
    - Dictionaries for attendance tracking

HOW TO RUN:
    python3 sds2.py help       — Show all available commands
    python3 sds2.py list       — List all students
    python3 sds2.py dashboard  — Show summary dashboard
    python3 sds2.py demo       — Run a full demonstration
"""

# --- Standard Library Imports ---
# These come built-in with Python — no installation needed.

import sys      # sys.argv gives us command-line arguments, sys.exit() stops the program
import csv      # csv module for reading/writing CSV files
import os       # os module for checking if files exist (os.path.exists)
import random   # random module for generating random numbers and choices

# --- External Libraries ---
# These must be installed separately with pip (e.g. pip install requests cowsay faker).

import requests     # For making HTTP requests to web APIs
import cowsay       # For fun ASCII art messages
from faker import Faker  # For generating realistic fake data (names, jobs, etc.)


# ==========================================
# PART 1: OOP Models (Classes & Inheritance)
# ==========================================

class Student:
    def __init__(self, name, degree, grade):
        if not name:
            raise ValueError("Missing name")
        if degree not in ["ECE", "BIO", "MECH", "EEE", "COMP"]:
            raise ValueError("Invalid degree")
        if not (0 <= grade <= 100):
            raise ValueError("Grade must be between 0 and 100")

        self.name = name
        self.degree = degree
        self.grade = grade
        self.modules = []
        self.attendance = {}  # { module_code: [True, False, True, ...] }

    def enroll(self, module):
        if module in self.modules:
            print(f"{self.name} is already enrolled in {module.name}.")
            return
        self.modules.append(module)
        self.attendance[module.module_code] = []
        module.add_student(self)

    def unenroll(self, module):
        if module not in self.modules:
            print(f"{self.name} is not enrolled in {module.name}.")
            return
        self.modules.remove(module)
        del self.attendance[module.module_code]
        module.remove_student(self)

    def record_attendance(self, module_code, present):
        if module_code not in self.attendance:
            print(f"{self.name} is not enrolled in module {module_code}.")
            return
        self.attendance[module_code].append(present)

    def get_attendance_percentage(self, module_code):
        if module_code not in self.attendance:
            return 0.0
        records = self.attendance[module_code]
        if len(records) == 0:
            return 0.0
        total_present = 0
        for r in records:
            if r:
                total_present += 1
        return (total_present / len(records)) * 100

    def get_classification(self):
        if self.grade >= 70:
            return "First"
        elif self.grade >= 60:
            return "Upper Second (2:1)"
        elif self.grade >= 50:
            return "Lower Second (2:2)"
        elif self.grade >= 40:
            return "Third"
        else:
            return "Fail"

    def is_at_risk(self):
        # A student is "at risk" if their grade is below 50
        # or any module attendance is below 50%
        if self.grade < 50:
            return True
        for code in self.attendance:
            if len(self.attendance[code]) > 0:
                if self.get_attendance_percentage(code) < 50.0:
                    return True
        return False

    def print_timetable(self):
        print(f"\n--- Timetable for {self.name} ---")
        if not self.modules:
            print("No modules enrolled.")
        for mod in sorted(self.modules, key=lambda m: m.time_slot):
            print(f"  {mod.time_slot}: {mod.name} (Taught by: {mod.academic.title} {mod.academic.name})")
        print("-----------------------------------")

        try:
            url = f"https://itunes.apple.com/search?entity=song&limit=1&term={self.degree}+study"
            response = requests.get(url)
            song_data = response.json()
            if song_data["results"]:
                track = song_data["results"][0]["trackName"]
                artist = song_data["results"][0]["artistName"]
                print(f"🎵 Recommended Study Song: '{track}' by {artist}")
        except Exception:
            pass

    def print_report(self):
        print(f"\n{'='*50}")
        print(f"  STUDENT REPORT: {self.name}")
        print(f"{'='*50}")
        print(f"  Degree:          {self.degree}")
        print(f"  Grade:           {self.grade}%")
        print(f"  Classification:  {self.get_classification()}")
        print(f"  At Risk:         {'YES ⚠️' if self.is_at_risk() else 'No'}")
        print(f"  Modules ({len(self.modules)}):")
        if not self.modules:
            print(f"    (none)")
        for mod in self.modules:
            att = self.get_attendance_percentage(mod.module_code)
            sessions = len(self.attendance.get(mod.module_code, []))
            print(f"    - {mod.module_code}: {mod.name} (Attendance: {att:.0f}% over {sessions} sessions)")
        print(f"{'='*50}")

    def __str__(self):
        return f"{self.name} studies {self.degree} (Grade: {self.grade})"


class Undergraduate(Student):
    def __init__(self, name, degree, grade, year_of_study, year_in_industry):
        super().__init__(name, degree, grade)
        if not (1 <= year_of_study <= 4):
            raise ValueError("Year of study must be between 1 and 4")
        self.year_of_study = year_of_study
        self.year_in_industry = year_in_industry

    def __str__(self):
        industry_text = " [Year in Industry]" if self.year_in_industry else ""
        return f"{super().__str__()} - Year {self.year_of_study}{industry_text}"


class Postgrad(Student):
    def __init__(self, name, degree, grade, thesis_title):
        super().__init__(name, degree, grade)
        if not thesis_title:
            raise ValueError("Postgrad students must have a thesis title")
        self.thesis_title = thesis_title

    def __str__(self):
        return f"{super().__str__()} - Thesis: '{self.thesis_title}'"


class AcademicStaff:
    def __init__(self, title, name, subject):
        if not name:
            raise ValueError("Missing name")
        if title not in ["Dr.", "Prof.", "Mr.", "Mrs.", "Ms."]:
            raise ValueError("Invalid title")
        self.title = title
        self.name = name
        self.subject = subject
        self.modules_taught = []

    def assign_module(self, module):
        if module not in self.modules_taught:
            self.modules_taught.append(module)

    def print_workload(self):
        print(f"\n--- Workload for {self.title} {self.name} ---")
        total_students = 0
        for mod in self.modules_taught:
            count = len(mod.enrolled_students)
            total_students += count
            print(f"  {mod.module_code}: {mod.name} ({count} students)")
        print(f"  Total modules: {len(self.modules_taught)}")
        print(f"  Total students: {total_students}")
        print("-------------------------------------------")

    def __str__(self):
        return f"{self.title} {self.name} ({self.subject})"


class Module:
    def __init__(self, module_code, name, academic, time_slot, capacity=30):
        if not module_code:
            raise ValueError("Module code is required")
        self.module_code = module_code
        self.name = name
        self.academic = academic
        self.time_slot = time_slot
        self.capacity = capacity
        self.enrolled_students = []
        # Link back to the academic
        academic.assign_module(self)

    def add_student(self, student):
        if student in self.enrolled_students:
            return
        if len(self.enrolled_students) >= self.capacity:
            print(f"Cannot add {student.name}: {self.name} is full ({self.capacity}/{self.capacity}).")
            return
        self.enrolled_students.append(student)

    def remove_student(self, student):
        if student in self.enrolled_students:
            self.enrolled_students.remove(student)

    def get_average_grade(self):
        if len(self.enrolled_students) == 0:
            return 0.0
        total = 0
        for s in self.enrolled_students:
            total += s.grade
        return total / len(self.enrolled_students)

    def get_pass_rate(self):
        if len(self.enrolled_students) == 0:
            return 0.0
        passed = 0
        for s in self.enrolled_students:
            if s.grade >= 40:
                passed += 1
        return (passed / len(self.enrolled_students)) * 100

    def print_class_list(self):
        print(f"\n--- {self.module_code}: {self.name} ---")
        print(f"  Taught by: {self.academic.title} {self.academic.name}")
        print(f"  Time: {self.time_slot}")
        print(f"  Capacity: {len(self.enrolled_students)}/{self.capacity}")
        print(f"  Average Grade: {self.get_average_grade():.1f}%")
        print(f"  Pass Rate: {self.get_pass_rate():.1f}%")
        print(f"  Students:")
        if not self.enrolled_students:
            print(f"    (none)")
        for s in sorted(self.enrolled_students, key=lambda s: s.name):
            print(f"    - {s.name} ({s.degree}, Grade: {s.grade})")
        print("-------------------------------------------")

    def __str__(self):
        return f"{self.module_code}: {self.name} at {self.time_slot}"


# ==========================================
# PART 2: File I/O & Fake Data Generation
# ==========================================

def generate_fake_files():
    fake = Faker()
    degrees = ["ECE", "BIO", "MECH", "EEE", "COMP"]

    if not os.path.exists("academics.csv"):
        with open("academics.csv", "w", newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Title", "Name", "Subject"])
            writer.writerow(["Dr.", "Horne", "Biomedical Engineering"])
            writer.writerow(["Prof.", "Smith", "Engineering"])
            for _ in range(3):
                writer.writerow(["Dr.", fake.last_name(), fake.job()])
        print("Created academics.csv with fake data.")

    if not os.path.exists("students.csv"):
        with open("students.csv", "w", newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Type", "Name", "Degree", "Grade", "Year", "Industry", "Thesis"])
            writer.writerow(["Undergrad", "Alice", "ECE", 85, 2, "False", "N/A"])
            for _ in range(10):
                name = fake.first_name()
                degree = random.choice(degrees)
                grade = random.randint(25, 100)  # Some students might fail!
                student_type = random.choice(["Undergrad", "Postgrad"])
                if student_type == "Undergrad":
                    year = random.randint(1, 4)
                    yin = random.choice(["True", "False"])
                    writer.writerow(["Undergrad", name, degree, grade, year, yin, "N/A"])
                else:
                    thesis = fake.catch_phrase()
                    writer.writerow(["Postgrad", name, degree, grade, "N/A", "N/A", thesis])
        print("Created students.csv with bulk fake data.")

    if not os.path.exists("modules.csv"):
        with open("modules.csv", "w", newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["ModuleCode", "Name", "AcademicName", "TimeSlot", "Capacity"])
            writer.writerow(["EENG4101", "Fundamentals of Programming", "Horne", "Monday 10:00 AM", 30])
            writer.writerow(["EENG3130", "Embedded Systems", "Smith", "Tuesday 2:00 PM", 25])
            writer.writerow(["EENG2001", "Circuit Analysis", "Horne", "Wednesday 9:00 AM", 35])
        print("Created modules.csv with sample data.")

    if not os.path.exists("attendance.csv"):
        with open("attendance.csv", "w", newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["StudentName", "ModuleCode", "Session", "Present"])
        print("Created attendance.csv.")


def load_academics():
    academics = []
    try:
        with open("academics.csv", "r") as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                academics.append(AcademicStaff(row[0], row[1], row[2]))
    except FileNotFoundError:
        pass
    return academics


def save_student(student):
    with open("students.csv", "a", newline='') as file:
        writer = csv.writer(file)
        if isinstance(student, Undergraduate):
            writer.writerow(["Undergrad", student.name, student.degree, student.grade,
                             student.year_of_study, student.year_in_industry])
        elif isinstance(student, Postgrad):
            writer.writerow(["Postgrad", student.name, student.degree, student.grade,
                             "N/A", "N/A", student.thesis_title])
        else:
            writer.writerow(["Base", student.name, student.degree, student.grade,
                             "N/A", "N/A", "N/A"])


def load_students():
    students = []
    try:
        with open("students.csv", "r") as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if row[0] == "Undergrad":
                    students.append(Undergraduate(row[1], row[2], int(row[3]),
                                                  int(row[4]), row[5] == 'True'))
                elif row[0] == "Postgrad":
                    students.append(Postgrad(row[1], row[2], int(row[3]), row[6]))
                else:
                    students.append(Student(row[1], row[2], int(row[3])))
    except FileNotFoundError:
        pass
    return students


def save_all_students(students):
    """Rewrite the entire students.csv file (used after edits or deletes)."""
    with open("students.csv", "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Type", "Name", "Degree", "Grade", "Year", "Industry", "Thesis"])
        for student in students:
            if isinstance(student, Undergraduate):
                writer.writerow(["Undergrad", student.name, student.degree, student.grade,
                                 student.year_of_study, student.year_in_industry])
            elif isinstance(student, Postgrad):
                writer.writerow(["Postgrad", student.name, student.degree, student.grade,
                                 "N/A", "N/A", student.thesis_title])
            else:
                writer.writerow(["Base", student.name, student.degree, student.grade,
                                 "N/A", "N/A", "N/A"])


def load_modules(academics):
    """Load modules from CSV and link them to their academics."""
    modules = []
    try:
        with open("modules.csv", "r") as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                module_code = row[0]
                name = row[1]
                academic_name = row[2]
                time_slot = row[3]
                capacity = int(row[4])
                # Find the academic by name
                academic = None
                for a in academics:
                    if a.name == academic_name:
                        academic = a
                        break
                if academic is not None:
                    modules.append(Module(module_code, name, academic, time_slot, capacity))
    except FileNotFoundError:
        pass
    return modules


def save_attendance(student_name, module_code, session_number, present):
    with open("attendance.csv", "a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow([student_name, module_code, session_number, present])


def load_attendance(students):
    """Read attendance.csv and populate each student's attendance dict."""
    try:
        with open("attendance.csv", "r") as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                student_name = row[0]
                module_code = row[1]
                present = row[3] == "True"
                for s in students:
                    if s.name == student_name:
                        if module_code not in s.attendance:
                            s.attendance[module_code] = []
                        s.attendance[module_code].append(present)
                        break
    except FileNotFoundError:
        pass


# ==========================================
# PART 3: Search & Statistics Functions
# ==========================================

def search_students(students, search_term):
    """Search students by name (case-insensitive partial match)."""
    results = []
    for s in students:
        if search_term.lower() in s.name.lower():
            results.append(s)
    return results


def filter_by_degree(students, degree):
    """Return all students on a given degree programme."""
    results = []
    for s in students:
        if s.degree == degree:
            results.append(s)
    return results


def filter_by_classification(students, classification):
    """Return all students with a given grade classification."""
    results = []
    for s in students:
        if s.get_classification() == classification:
            results.append(s)
    return results


def get_at_risk_students(students):
    """Return all students flagged as at risk."""
    results = []
    for s in students:
        if s.is_at_risk():
            results.append(s)
    return results


def calculate_degree_statistics(students):
    """Print grade stats broken down by degree programme."""
    degrees = ["ECE", "BIO", "MECH", "EEE", "COMP"]

    print(f"\n{'='*60}")
    print(f"  GRADE STATISTICS BY DEGREE")
    print(f"{'='*60}")

    for degree in degrees:
        degree_students = filter_by_degree(students, degree)
        if len(degree_students) == 0:
            print(f"\n  {degree}: No students enrolled.")
            continue

        grades = []
        for s in degree_students:
            grades.append(s.grade)

        total = 0
        for g in grades:
            total += g
        average = total / len(grades)

        highest = grades[0]
        lowest = grades[0]
        for g in grades:
            if g > highest:
                highest = g
            if g < lowest:
                lowest = g

        passing = 0
        for g in grades:
            if g >= 40:
                passing += 1
        pass_rate = (passing / len(grades)) * 100

        print(f"\n  {degree} ({len(degree_students)} students):")
        print(f"    Average Grade:  {average:.1f}%")
        print(f"    Highest Grade:  {highest}%")
        print(f"    Lowest Grade:   {lowest}%")
        print(f"    Pass Rate:      {pass_rate:.1f}%")

    print(f"\n{'='*60}")


def print_summary_dashboard(students, modules):
    """Print a high-level overview of the whole system."""
    total = len(students)
    undergrads = 0
    postgrads = 0
    for s in students:
        if isinstance(s, Undergraduate):
            undergrads += 1
        elif isinstance(s, Postgrad):
            postgrads += 1

    at_risk = len(get_at_risk_students(students))

    total_grade = 0
    for s in students:
        total_grade += s.grade
    avg_grade = total_grade / total if total > 0 else 0

    print(f"\n{'='*60}")
    print(f"  STUDENT DATA SYSTEM - DASHBOARD")
    print(f"{'='*60}")
    print(f"  Total Students:      {total}")
    print(f"    Undergraduates:    {undergrads}")
    print(f"    Postgraduates:     {postgrads}")
    print(f"    Other:             {total - undergrads - postgrads}")
    print(f"  Average Grade:       {avg_grade:.1f}%")
    print(f"  Students at Risk:    {at_risk}")
    print(f"  Total Modules:       {len(modules)}")
    print(f"{'='*60}")


# ==========================================
# PART 4: Main Execution & CLI
# ==========================================

def print_help():
    print("\nUsage: python sds2.py <command>")
    print("\nAvailable commands:")
    print("  add          - Add a new student (interactive)")
    print("  list         - List all students sorted by name")
    print("  academics    - List all academic staff")
    print("  modules      - List all modules with class details")
    print("  search       - Search for a student by name")
    print("  filter       - Filter students by degree")
    print("  stats        - Show grade statistics by degree")
    print("  atrisk       - Show students at risk")
    print("  report       - Print a full report for a student")
    print("  attendance   - Record attendance for a student")
    print("  edit         - Edit a student's grade")
    print("  delete       - Remove a student from the system")
    print("  dashboard    - Show system summary dashboard")
    print("  demo         - Run system demonstration")
    print("  help         - Show this help message")


def main():
    generate_fake_files()

    if len(sys.argv) < 2:
        print("Too few arguments.")
        print_help()
        sys.exit()

    mode = sys.argv[1].lower()

    # --- Add a student ---
    if mode == "add":
        print("\n--- Add New Student ---")
        name = input("Name: ")
        degree = input("Degree (ECE, BIO, MECH, EEE, COMP): ").upper()
        grade = int(input("Grade (0-100): "))

        student_type = input("Type (undergrad/postgrad/base): ").lower()

        if student_type == "undergrad":
            year = int(input("Year of study (1-4): "))
            yin = input("Year in industry? (yes/no): ").lower() == "yes"
            new_student = Undergraduate(name, degree, grade, year, yin)
        elif student_type == "postgrad":
            thesis = input("Thesis title: ")
            new_student = Postgrad(name, degree, grade, thesis)
        else:
            new_student = Student(name, degree, grade)

        save_student(new_student)
        cowsay.cow(f"Success! Saved {name} to the database.")

    # --- List all students ---
    elif mode == "list":
        print("\n--- Student Roster ---")
        students = load_students()
        for s in sorted(students, key=lambda s: s.name):
            classification = s.get_classification()
            risk = " ⚠️" if s.is_at_risk() else ""
            print(f"  {s} [{classification}]{risk}")
        print(f"\nTotal: {len(students)} students")

    # --- List academics ---
    elif mode == "academics":
        print("\n--- Academic Staff ---")
        academics = load_academics()
        for a in academics:
            print(f"  {a}")

    # --- List modules ---
    elif mode == "modules":
        academics = load_academics()
        modules = load_modules(academics)
        students = load_students()
        # Enrol students into their modules for the demo
        for mod in modules:
            for s in students:
                if s.degree in ["ECE", "EEE", "COMP"]:
                    s.enroll(mod)
        for mod in modules:
            mod.print_class_list()

    # --- Search for a student ---
    elif mode == "search":
        search_term = input("Search for student (name): ")
        students = load_students()
        results = search_students(students, search_term)
        if len(results) == 0:
            print(f"No students found matching '{search_term}'.")
        else:
            print(f"\n--- Search Results ({len(results)} found) ---")
            for s in results:
                print(f"  {s}")

    # --- Filter by degree ---
    elif mode == "filter":
        degree = input("Degree to filter by (ECE, BIO, MECH, EEE, COMP): ").upper()
        students = load_students()
        results = filter_by_degree(students, degree)
        if len(results) == 0:
            print(f"No students found on {degree}.")
        else:
            print(f"\n--- {degree} Students ({len(results)}) ---")
            for s in sorted(results, key=lambda s: s.grade, reverse=True):
                print(f"  {s} [{s.get_classification()}]")

    # --- Grade statistics ---
    elif mode == "stats":
        students = load_students()
        calculate_degree_statistics(students)

    # --- At risk students ---
    elif mode == "atrisk":
        students = load_students()
        at_risk = get_at_risk_students(students)
        if len(at_risk) == 0:
            print("No students are currently at risk. 🎉")
        else:
            print(f"\n--- Students at Risk ({len(at_risk)}) ---")
            for s in at_risk:
                print(f"  ⚠️ {s}")

    # --- Student report ---
    elif mode == "report":
        name = input("Student name: ")
        students = load_students()
        load_attendance(students)
        student = None
        for s in students:
            if s.name.lower() == name.lower():
                student = s
                break
        if student is None:
            print(f"Student '{name}' not found.")
        else:
            student.print_report()

    # --- Record attendance ---
    elif mode == "attendance":
        students = load_students()
        name = input("Student name: ")
        student = None
        for s in students:
            if s.name.lower() == name.lower():
                student = s
                break
        if student is None:
            print(f"Student '{name}' not found.")
        else:
            module_code = input("Module code: ").upper()
            session = input("Session number: ")
            present = input("Present? (yes/no): ").lower() == "yes"
            save_attendance(student.name, module_code, session, present)
            print(f"Recorded: {student.name} was {'present' if present else 'absent'} "
                  f"for {module_code} session {session}.")

    # --- Edit a student's grade ---
    elif mode == "edit":
        name = input("Student name to edit: ")
        students = load_students()
        found = False
        for s in students:
            if s.name.lower() == name.lower():
                print(f"Current grade for {s.name}: {s.grade}")
                new_grade = int(input("New grade (0-100): "))
                if 0 <= new_grade <= 100:
                    s.grade = new_grade
                    save_all_students(students)
                    print(f"Updated {s.name}'s grade to {new_grade}.")
                else:
                    print("Invalid grade. Must be between 0 and 100.")
                found = True
                break
        if not found:
            print(f"Student '{name}' not found.")

    # --- Delete a student ---
    elif mode == "delete":
        name = input("Student name to delete: ")
        students = load_students()
        new_students = []
        found = False
        for s in students:
            if s.name.lower() == name.lower():
                found = True
                confirm = input(f"Are you sure you want to delete {s.name}? (yes/no): ")
                if confirm.lower() == "yes":
                    print(f"Deleted {s.name}.")
                else:
                    print("Cancelled.")
                    new_students.append(s)
            else:
                new_students.append(s)
        if not found:
            print(f"Student '{name}' not found.")
        else:
            save_all_students(new_students)

    # --- Dashboard ---
    elif mode == "dashboard":
        academics = load_academics()
        students = load_students()
        modules = load_modules(academics)
        print_summary_dashboard(students, modules)

    # --- Demo ---
    elif mode == "demo":
        print("\n--- Running Full System Demonstration ---")
        academics = load_academics()
        students = load_students()
        modules = load_modules(academics)
        load_attendance(students)

        # Find our demo data
        dr_horne = None
        for a in academics:
            if a.name == "Horne":
                dr_horne = a
                break

        alice = None
        for s in students:
            if s.name == "Alice":
                alice = s
                break

        if dr_horne and alice:
            # Find or create the FoP module
            fop = None
            for m in modules:
                if m.module_code == "EENG4101":
                    fop = m
                    break
            if fop is None:
                fop = Module("EENG4101", "Fundamentals of Programming",
                             dr_horne, "Monday 10:00 AM")

            # Enrol Alice and show timetable
            alice.enroll(fop)
            alice.print_timetable()

            # Simulate some attendance
            for i in range(10):
                present = random.choice([True, True, True, False])  # 75% chance present
                alice.record_attendance(fop.module_code, present)
                save_attendance(alice.name, fop.module_code, i + 1, present)

            # Print her report
            alice.print_report()

            # Enrol a few more students for module stats
            for s in students:
                if s.degree == "ECE" and s.name != "Alice":
                    s.enroll(fop)

            fop.print_class_list()

            # Show degree stats
            calculate_degree_statistics(students)

            # Dashboard
            print_summary_dashboard(students, modules)

            # Show at-risk students
            at_risk = get_at_risk_students(students)
            if len(at_risk) > 0:
                print(f"\n⚠️  {len(at_risk)} student(s) at risk:")
                for s in at_risk:
                    print(f"  - {s.name} (Grade: {s.grade}, Classification: {s.get_classification()})")
        else:
            print("Required data missing for demo.")

    # --- Help ---
    elif mode == "help":
        print_help()

    else:
        print(f"Unknown command: '{mode}'")
        print_help()


if __name__ == "__main__":
    main()
