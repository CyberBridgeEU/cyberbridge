from typing import List, Dict
from ..base_framework_update import BaseFrameworkUpdate


class CRAUpdate1(BaseFrameworkUpdate):
    """
    CRA Framework Update #1

    This update adds:
    - 2 new questions to Chapter I
    - Updates 1 existing question text
    - Updates the objective_utilities for Subchapter 1.1.1
    """

    version = 1
    description = "Add new questions and update existing question text"
    framework_name = "cra"

    def get_new_questions(self) -> List[Dict]:
        """
        Add 2 new questions to Chapter I - General Provisions.
        """
        # Chapter I - General Provisions ID: 602f293e-1613-43b8-a584-dda5266bec72
        # Assessment type conformity ID: 55ca2fce-c560-46bb-9d38-fdc5e4121788
        return [
            {
                "chapter_id": "602f293e-1613-43b8-a584-dda5266bec72",
                "title": "General Inquiry",
                "question_text": "what's up doc",
                "assessment_type_id": "55ca2fce-c560-46bb-9d38-fdc5e4121788",
                "order": 100
            },
            {
                "chapter_id": "602f293e-1613-43b8-a584-dda5266bec72",
                "title": "Status Check",
                "question_text": "what is going on here?",
                "assessment_type_id": "55ca2fce-c560-46bb-9d38-fdc5e4121788",
                "order": 101
            }
        ]

    def get_new_chapters(self) -> List[Dict]:
        """
        No new chapters in this update.
        """
        return []

    def get_new_objectives(self) -> List[Dict]:
        """
        Add 1 new objective to Subchapter 1.2.5.
        Note: chapter_id must be fetched from the database at runtime.
        For this example update, we return an empty list to avoid errors.
        """
        return []

    def get_updated_objectives(self) -> List[Dict]:
        """
        No objective updates in this update.
        """
        return []

    def get_updated_questions(self) -> List[Dict]:
        """
        Update existing question to add 'test-' prefix.
        """
        # Question ID: 9988db9b-b9d1-43e6-a1f6-029eba489928
        return [
            {
                "question_id": "9988db9b-b9d1-43e6-a1f6-029eba489928",
                "text": "test- Have you undertaken an assessment of the cybersecurity risks associated with your product with digital elements?"
            }
        ]
