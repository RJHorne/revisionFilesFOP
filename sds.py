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
