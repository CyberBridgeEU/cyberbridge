#!/usr/bin/env python3
"""
Script to generate cleaned seed files with only unique questions and objectives.
This is a one-time migration script to clean up existing seed files.
"""

import sys
sys.path.insert(0, '/Users/miaritisnestor/Documents/Code_Projects/python/cyberbridge_project/cyberbridge_backend')

from app.seeds.iso_27001_2022_seed import ISO270012022Seed
from app.seeds.nis2_directive_seed import NIS2DirectiveSeed
from app.utils.seed_data_cleaner import extract_unique_questions, extract_unique_objectives
import json

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


def generate_iso_cleaned_seed():
    """Generate cleaned ISO 27001 seed file"""
    print("Processing ISO 27001:2022...")

    mock_db = MockDB()
    mock_orgs = {"default": MockOrg()}
    mock_types = {
        "conformity": MockAssessmentType(),
        "audit": MockAssessmentType()
    }

    seeder = ISO270012022Seed(mock_db, mock_orgs, mock_types)
    iso_data = seeder._parse_iso_27001_2022_data()

    # Extract unique data
    unique_conformity_questions = extract_unique_questions(iso_data, 'conformity_questions')
    unique_audit_questions = extract_unique_questions(iso_data, 'audit_question')
    unique_objectives = extract_unique_objectives(iso_data, 'objective_title')

    print(f"✅ ISO 27001:2022: {len(unique_conformity_questions)} conformity questions, "
          f"{len(unique_audit_questions)} audit questions, {len(unique_objectives)} objectives")

    # Generate new seed file content
    seed_content = f'''# app/seeds/iso_27001_2022_seed.py
import logging
from .base_seed import BaseSeed
from app.models import models

logger = logging.getLogger(__name__)


class ISO270012022Seed(BaseSeed):
    """Seed ISO 27001 2022 framework and its associated questions"""

    def __init__(self, db, organizations, assessment_types):
        super().__init__(db)
        self.organizations = organizations
        self.assessment_types = assessment_types

    def seed(self) -> dict:
        logger.info("Creating ISO 27001 2022 framework and questions...")

        # Get default organization (assuming first one is default)
        default_org = list(self.organizations.values())[0]
        conformity_assessment_type = self.assessment_types["conformity"]
        audit_assessment_type = self.assessment_types["audit"]

        # Create ISO 27001 2022 Framework
        iso_27001_2022_framework, created = self.get_or_create(
            models.Framework,
            {{"name": "ISO 27001 2022", "organisation_id": default_org.id}},
            {{
                "name": "ISO 27001 2022",
                "description": "ISO/IEC 27001:2022 Information Security Management System compliance framework",
                "organisation_id": default_org.id
            }}
        )

        # Get unique questions and objectives
        unique_conformity_questions = self._get_unique_conformity_questions()
        unique_audit_questions = self._get_unique_audit_questions()
        unique_objectives_data = self._get_unique_objectives()

        # Create conformity questions
        conformity_questions = []
        question_order = 1

        for conf_q_text in unique_conformity_questions:
            # Always create new questions for each framework (no sharing across frameworks)
            question = models.Question(
                text=conf_q_text,
                description="ISO 27001 conformity question",
                mandatory=True,
                assessment_type_id=conformity_assessment_type.id
            )
            self.db.add(question)
            self.db.flush()  # Get the question ID
            conformity_questions.append(question)

            # Create framework-question relationship
            framework_question = models.FrameworkQuestion(
                framework_id=iso_27001_2022_framework.id,
                question_id=question.id,
                order=question_order
            )
            self.db.add(framework_question)

            question_order += 1

        # Create audit questions
        audit_questions = []
        audit_start_order = question_order

        for audit_q_text in unique_audit_questions:
            # Always create new questions for each framework (no sharing across frameworks)
            question = models.Question(
                text=audit_q_text,
                description="ISO 27001 audit question",
                mandatory=True,
                assessment_type_id=audit_assessment_type.id
            )
            self.db.add(question)
            self.db.flush()  # Get the question ID
            audit_questions.append(question)

            # Create framework-question relationship
            framework_question = models.FrameworkQuestion(
                framework_id=iso_27001_2022_framework.id,
                question_id=question.id,
                order=audit_start_order
            )
            self.db.add(framework_question)

            audit_start_order += 1

        # Create chapters and objectives
        chapters_dict = {{}}
        objectives_list = []

        for item in unique_objectives_data:
            chapter_title = item['chapter_title']

            # Create or get chapter
            if chapter_title not in chapters_dict:
                chapter, created = self.get_or_create(
                    models.Chapters,
                    {{
                        "title": chapter_title,
                        "framework_id": iso_27001_2022_framework.id
                    }},
                    {{
                        "title": chapter_title,
                        "framework_id": iso_27001_2022_framework.id
                    }}
                )
                chapters_dict[chapter_title] = chapter

            chapter = chapters_dict[chapter_title]

            # Create objective
            objective, created = self.get_or_create(
                models.Objectives,
                {{
                    "title": item['objective_title'],
                    "chapter_id": chapter.id
                }},
                {{
                    "title": item['objective_title'],
                    "subchapter": item.get('subchapter'),
                    "chapter_id": chapter.id,
                    "requirement_description": item.get('requirement_description'),
                    "objective_utilities": item.get('objective_utilities')
                }}
            )
            objectives_list.append(objective)

        self.db.commit()

        logger.info(f"Created ISO 27001 2022 framework with {{len(unique_conformity_questions)}} conformity questions, "
                    f"{{len(unique_audit_questions)}} audit questions, and {{len(unique_objectives_data)}} objectives")

        return {{
            "framework": iso_27001_2022_framework,
            "conformity_questions": conformity_questions,
            "audit_questions": audit_questions,
            "objectives": objectives_list
        }}

    def _get_unique_conformity_questions(self):
        """Returns the list of unique conformity questions (pre-deduplicated)"""
        return {json.dumps(unique_conformity_questions, indent=12)[12:]}

    def _get_unique_audit_questions(self):
        """Returns the list of unique audit questions (pre-deduplicated)"""
        return {json.dumps(unique_audit_questions, indent=12)[12:]}

    def _get_unique_objectives(self):
        """Returns the list of unique objectives (pre-deduplicated)"""
        return {json.dumps(unique_objectives, indent=12, ensure_ascii=False)[12:]}
'''

    # Write to new file
    output_path = '/Users/miaritisnestor/Documents/Code_Projects/python/cyberbridge_project/cyberbridge_backend/app/seeds/iso_27001_2022_seed_cleaned.py'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(seed_content)

    print(f"✅ Generated: {output_path}")
    return output_path


def generate_nis2_cleaned_seed():
    """Generate cleaned NIS2 Directive seed file"""
    print("\nProcessing NIS2 Directive...")

    mock_db = MockDB()
    mock_orgs = {"default": MockOrg()}
    mock_types = {
        "conformity": MockAssessmentType(),
        "audit": MockAssessmentType()
    }

    seeder = NIS2DirectiveSeed(mock_db, mock_orgs, mock_types)
    nis2_data = seeder._parse_nis2_directive_data()

    # Extract unique data
    unique_questions = extract_unique_questions(nis2_data, 'conformity_questions')
    unique_objectives = extract_unique_objectives(nis2_data, 'objective_title')

    print(f"✅ NIS2 Directive: {len(unique_questions)} questions, {len(unique_objectives)} objectives")

    # Generate new seed file content
    seed_content = f'''# app/seeds/nis2_directive_seed.py
import logging
from .base_seed import BaseSeed
from app.models import models

logger = logging.getLogger(__name__)


class NIS2DirectiveSeed(BaseSeed):
    """Seed NIS2 Directive framework and its associated questions"""

    def __init__(self, db, organizations, assessment_types):
        super().__init__(db)
        self.organizations = organizations
        self.assessment_types = assessment_types

    def seed(self) -> dict:
        logger.info("Creating NIS2 Directive framework and questions...")

        # Get default organization
        default_org = list(self.organizations.values())[0]
        conformity_assessment_type = self.assessment_types["conformity"]

        # Create NIS2 Directive Framework
        nis2_directive_framework, created = self.get_or_create(
            models.Framework,
            {{"name": "NIS2 Directive", "organisation_id": default_org.id}},
            {{
                "name": "NIS2 Directive",
                "description": "NIS2 Directive compliance framework for network and information systems security",
                "organisation_id": default_org.id
            }}
        )

        # Get unique questions and objectives
        unique_questions = self._get_unique_questions()
        unique_objectives_data = self._get_unique_objectives()

        # Create conformity questions
        conformity_questions = []
        question_order = 1

        for conf_q_text in unique_questions:
            # Always create new questions for each framework (no sharing across frameworks)
            question = models.Question(
                text=conf_q_text,
                description="NIS2 Directive conformity question",
                mandatory=True,
                assessment_type_id=conformity_assessment_type.id
            )
            self.db.add(question)
            self.db.flush()  # Get the question ID
            conformity_questions.append(question)

            # Create framework-question relationship
            framework_question = models.FrameworkQuestion(
                framework_id=nis2_directive_framework.id,
                question_id=question.id,
                order=question_order
            )
            self.db.add(framework_question)

            question_order += 1

        # Create chapters and objectives
        chapters_dict = {{}}
        objectives_list = []

        for item in unique_objectives_data:
            chapter_title = item['chapter_title']

            # Create or get chapter
            if chapter_title not in chapters_dict:
                chapter, created = self.get_or_create(
                    models.Chapters,
                    {{
                        "title": chapter_title,
                        "framework_id": nis2_directive_framework.id
                    }},
                    {{
                        "title": chapter_title,
                        "framework_id": nis2_directive_framework.id
                    }}
                )
                chapters_dict[chapter_title] = chapter

            chapter = chapters_dict[chapter_title]

            # Create objective
            objective, created = self.get_or_create(
                models.Objectives,
                {{
                    "title": item['objective_title'],
                    "chapter_id": chapter.id
                }},
                {{
                    "title": item['objective_title'],
                    "subchapter": item.get('subchapter'),
                    "chapter_id": chapter.id,
                    "requirement_description": item.get('requirement_description'),
                    "objective_utilities": item.get('objective_utilities')
                }}
            )
            objectives_list.append(objective)

        self.db.commit()

        logger.info(f"Created NIS2 Directive framework with {{len(unique_questions)}} conformity questions "
                    f"and {{len(unique_objectives_data)}} objectives")

        return {{
            "framework": nis2_directive_framework,
            "conformity_questions": conformity_questions,
            "objectives": objectives_list
        }}

    def _get_unique_questions(self):
        """Returns the list of unique conformity questions (pre-deduplicated)"""
        return {json.dumps(unique_questions, indent=12)[12:]}

    def _get_unique_objectives(self):
        """Returns the list of unique objectives (pre-deduplicated)"""
        return {json.dumps(unique_objectives, indent=12, ensure_ascii=False)[12:]}
'''

    # Write to new file
    output_path = '/Users/miaritisnestor/Documents/Code_Projects/python/cyberbridge_project/cyberbridge_backend/app/seeds/nis2_directive_seed_cleaned.py'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(seed_content)

    print(f"✅ Generated: {output_path}")
    return output_path


if __name__ == "__main__":
    print("=" * 60)
    print("Generating cleaned seed files with unique data only")
    print("=" * 60)
    print()

    try:
        iso_path = generate_iso_cleaned_seed()
        nis2_path = generate_nis2_cleaned_seed()

        print("\n" + "=" * 60)
        print("✅ Generation complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Review the generated files:")
        print(f"   - {iso_path}")
        print(f"   - {nis2_path}")
        print("2. If they look good, replace the original files")
        print("3. The deduplication logic is now removed from seed files")
        print("4. Use app/utils/seed_data_cleaner.py for future framework seed creation")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
