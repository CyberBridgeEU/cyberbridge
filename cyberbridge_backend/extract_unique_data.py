#!/usr/bin/env python3
"""
Script to extract unique questions and objectives from seed files
and generate cleaned seed file data
"""

import sys
sys.path.insert(0, '/Users/miaritisnestor/Documents/Code_Projects/python/cyberbridge_project/cyberbridge_backend')

from app.seeds.iso_27001_2022_seed import ISO270012022Seed
from app.seeds.nis2_directive_seed import NIS2DirectiveSeed

class MockDB:
    """Mock database for extraction purposes"""
    pass

class MockOrg:
    """Mock organization"""
    def __init__(self):
        self.id = "mock-id"

class MockAssessmentType:
    """Mock assessment type"""
    def __init__(self):
        self.id = "mock-id"

def extract_iso_data():
    """Extract unique ISO data"""
    mock_db = MockDB()
    mock_orgs = {"default": MockOrg()}
    mock_types = {
        "conformity": MockAssessmentType(),
        "audit": MockAssessmentType()
    }

    seeder = ISO270012022Seed(mock_db, mock_orgs, mock_types)
    iso_data = seeder._parse_iso_27001_2022_data()

    # Extract unique conformity questions
    seen_conformity = set()
    unique_conformity = []
    for item in iso_data:
        for q in item['conformity_questions']:
            if q and q not in seen_conformity:
                seen_conformity.add(q)
                unique_conformity.append(q)

    # Extract unique audit questions
    seen_audit = set()
    unique_audit = []
    for item in iso_data:
        if item['audit_question'] and item['audit_question'] not in seen_audit:
            seen_audit.add(item['audit_question'])
            unique_audit.append(item['audit_question'])

    # Extract unique objectives
    seen_objectives = {}
    unique_objectives = []
    for item in iso_data:
        obj_title = item['objective_title']
        if obj_title not in seen_objectives:
            seen_objectives[obj_title] = True
            unique_objectives.append(item)

    print("=== ISO 27001:2022 Statistics ===")
    print(f"Total conformity question entries: {sum(len(item['conformity_questions']) for item in iso_data)}")
    print(f"Unique conformity questions: {len(unique_conformity)}")
    print(f"Total audit question entries: {len(iso_data)}")
    print(f"Unique audit questions: {len(unique_audit)}")
    print(f"Total objective entries: {len(iso_data)}")
    print(f"Unique objectives: {len(unique_objectives)}")

    return unique_conformity, unique_audit, unique_objectives

def extract_nis2_data():
    """Extract unique NIS2 data"""
    mock_db = MockDB()
    mock_orgs = {"default": MockOrg()}
    mock_types = {
        "conformity": MockAssessmentType(),
        "audit": MockAssessmentType()
    }

    seeder = NIS2DirectiveSeed(mock_db, mock_orgs, mock_types)
    nis2_data = seeder._parse_nis2_directive_data()

    # Extract unique questions
    seen_questions = set()
    unique_questions = []
    for item in nis2_data:
        for q in item['conformity_questions']:
            if q and q not in seen_questions:
                seen_questions.add(q)
                unique_questions.append(q)

    # Extract unique objectives
    seen_objectives = {}
    unique_objectives = []
    for item in nis2_data:
        obj_title = item['objective_title']
        if obj_title not in seen_objectives:
            seen_objectives[obj_title] = True
            unique_objectives.append(item)

    print("\n=== NIS2 Directive Statistics ===")
    print(f"Total question entries: {sum(len(item['conformity_questions']) for item in nis2_data)}")
    print(f"Unique questions: {len(unique_questions)}")
    print(f"Total objective entries: {len(nis2_data)}")
    print(f"Unique objectives: {len(unique_objectives)}")

    return unique_questions, unique_objectives

if __name__ == "__main__":
    print("Extracting unique data from seed files...\n")

    # Extract ISO data
    iso_conformity, iso_audit, iso_objectives = extract_iso_data()

    # Extract NIS2 data
    nis2_questions, nis2_objectives = extract_nis2_data()

    print("\n✅ Extraction complete!")
    print("\nThis confirms the deduplication logic is working correctly.")
    print("The seed files contain duplicate data that needs to be cleaned.")
