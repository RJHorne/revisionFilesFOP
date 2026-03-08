import sys
import csv
import os
import random

# --- External Libraries ---
import requests
import cowsay
from faker import Faker

# ==========================================
# PART 1: OOP Models (Classes & Inheritance)
# ==========================================

class Student:
    def __init__(self, name, degree, grade):
        if not name:
            raise ValueError("Missing name")
        if degree not in ["ECE", "BIO", "MECH", "EEE", "COMP"]:
            raise ValueError("Invalid degree")
        
        self.name = name
        self.degree = degree
        self.grade = grade
        self.modules = [] 

    def enroll(self, module):
        self.modules.append(module)
        module.add_student(self)

    def print_timetable(self):
        print(f"\n--- Timetable for {self.name} ---")
        if not self.modules:
            print("No modules enrolled.")
        for mod in sorted(self.modules, key=lambda m: m.time_slot):
            print(f"{mod.time_slot}: {mod.name} (Taught by: {mod.academic.title} {mod.academic.name})")
        print("-----------------------------------")
        
        # 1. Using requests to hit an API (From Lecture 7)
        try:
            # Search iTunes for a study song related to their degree
            url = f"https://itunes.apple.com/search?entity=song&limit=1&term={self.degree}+study"
            response = requests.get(url)
            song_data = response.json()
            
            if song_data["results"]:
                track = song_data["results"][0]["trackName"]
                artist = song_data["results"][0]["artistName"]
                print(f"🎵 Recommended Study Song: '{track}' by {artist}")
        except Exception:
            # If the computer is offline, just fail silently
            pass

    def __str__(self):
        return f"{self.name} studies {self.degree} (Grade: {self.grade})"

class Undergraduate(Student):
    def __init__(self, name, degree, grade, year_of_study, year_in_industry):
        super().__init__(name, degree, grade)
        self.year_of_study = year_of_study
        self.year_in_industry = year_in_industry
        
    def __str__(self):
        industry_text = " [Year in Industry]" if self.year_in_industry else ""
        return f"{super().__str__()} - Year {self.year_of_study}{industry_text}"

class Postgrad(Student):
    def __init__(self, name, degree, grade, thesis_title):
        super().__init__(name, degree, grade)
        self.thesis_title = thesis_title

    def __str__(self):
        return f"{super().__str__()} - Thesis: '{self.thesis_title}'"

class AcademicStaff:
    def __init__(self, title, name, subject):
        if not name:
            raise ValueError("Missing name")
        self.title = title
        self.name = name
        self.subject = subject

    def __str__(self):
        return f"{self.title} {self.name} ({self.subject})"

class Module:
    def __init__(self, module_code, name, academic, time_slot):
        self.module_code = module_code
        self.name = name
        self.academic = academic
        self.time_slot = time_slot
        self.enrolled_students = []

    def add_student(self, student):
        if student not in self.enrolled_students:
            self.enrolled_students.append(student)

    def __str__(self):
        return f"{self.module_code}: {self.name} at {self.time_slot}"


# ==========================================
# PART 2: File I/O & Fake Data Generation
# ==========================================

def generate_fake_files():
    # 2. Using Faker to supercharge our mock data 
    fake = Faker()
    degrees = ["ECE", "BIO", "MECH", "EEE", "COMP"]
    
    if not os.path.exists("academics.csv"):
        with open("academics.csv", "w", newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Title", "Name", "Subject"])
            writer.writerow(["Dr.", "Horne", "Biomedical Engineering"])
            writer.writerow(["Prof.", "Smith", "Engineering"])
            
            # Let's generate 3 random academics using Faker
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
                name = fake.first_name()
                degree = random.choice(degrees)
                grade = random.randint(40, 100)
                
                # Randomly decide if student is Undergrad or Postgrad
                student_type = random.choice(["Undergrad", "Postgrad"])
                
                if student_type == "Undergrad":
                    year = random.randint(1, 4)
                    yin = random.choice(["True", "False"])
                    writer.writerow(["Undergrad", name, degree, grade, year, yin, "N/A"])
                else:  # Postgrad
                    thesis = fake.catch_phrase()  # Generate a random thesis title
                    writer.writerow(["Postgrad", name, degree, grade, "N/A", "N/A", thesis])
        print("Created students.csv with bulk fake data.")

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
            writer.writerow(["Undergrad", student.name, student.degree, student.grade, student.year_of_study, student.year_in_industry])
        elif isinstance(student, Postgrad):
            writer.writerow(["Postgrad", student.name, student.degree, student.grade, "N/A", "N/A", student.thesis_title])
        else:
            writer.writerow(["Base", student.name, student.degree, student.grade, "N/A", "N/A", "N/A"])

def load_students():
    students = []
    try:
        with open("students.csv", "r") as file:
            reader = csv.reader(file)
            next(reader) 
            for row in reader:
                if row[0] == "Undergrad":
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

def main():
    generate_fake_files()
    
    # sys.argv checks for command line arguments (From Lecture 7)
    if len(sys.argv) < 2:
        print("Too few arguments. Use 'add', 'list', 'academics', or 'demo'.")
        sys.exit()
        
    mode = sys.argv[1].lower()
    
    if mode == "add":
        name = input("Name: ")
        degree = input("Degree (ECE, BIO, MECH, EEE, COMP): ")
        grade = int(input("Grade: "))
        
        new_student = Student(name, degree, grade)
        save_student(new_student)
        
        # 4. Cowsay callback from Lecture 7!
        cowsay.cow(f"Success! Saved {name} to the database.")
        
    elif mode == "list":
        print("\n--- Student Roster ---")
        students = load_students()
        for s in sorted(students, key=lambda s: s.name):
            print(s)
            
    elif mode == "academics":
        print("\n--- Academic Staff ---")
        academics = load_academics()
        for a in academics:
            print(a)
            
    elif mode == "demo":
        print("\n--- Running System Demonstration ---")
        academics = load_academics()
        students = load_students()
        
        dr_horne = next((a for a in academics if a.name == "Horne"), None)
        alice = next((s for s in students if s.name == "Alice"), None)
        
        if dr_horne and alice:
            fop_module = Module("EENG4101", "Fundamentals of Programming", dr_horne, "Monday 10:00 AM")
            alice.enroll(fop_module)
            alice.print_timetable()
        else:
            print("Required data missing for demo.")

if __name__ == "__main__":
    main()
