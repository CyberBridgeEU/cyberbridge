from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime


class BaseFrameworkUpdate(ABC):
    """
    Abstract base class for all framework update files.
    Each update file must inherit from this class and implement all abstract methods.
    """

    # These must be set in child classes
    version: int
    description: str
    framework_name: str  # 'cra', 'iso27001', or 'nis2'

    def __init__(self):
        if not hasattr(self, 'version'):
            raise NotImplementedError("Update class must define 'version' attribute")
        if not hasattr(self, 'description'):
            raise NotImplementedError("Update class must define 'description' attribute")
        if not hasattr(self, 'framework_name'):
            raise NotImplementedError("Update class must define 'framework_name' attribute")

    @abstractmethod
    def get_new_questions(self) -> List[Dict]:
        """
        Returns a list of new questions to add to the framework.

        Each question dict should contain:
        - chapter_id: int - ID of the chapter this question belongs to
        - title: str - Question title
        - question_text: str - The actual question content
        - assessment_type_id: int - Type of assessment (1=Initial, 2=Gap Analysis, etc.)
        - order: int (optional) - Display order within the chapter

        Example:
        [
            {
                "chapter_id": 5,
                "title": "Data Encryption",
                "question_text": "Does the organization encrypt data at rest?",
                "assessment_type_id": 1,
                "order": 10
            }
        ]
        """
        pass

    @abstractmethod
    def get_new_chapters(self) -> List[Dict]:
        """
        Returns a list of new chapters to add to the framework.

        Each chapter dict should contain:
        - name: str - Chapter name
        - description: str - Chapter description
        - chapter_number: str - Chapter number/identifier
        - order: int - Display order

        Example:
        [
            {
                "name": "Supply Chain Security",
                "description": "Requirements for managing supply chain security risks",
                "chapter_number": "8",
                "order": 8
            }
        ]
        """
        pass

    @abstractmethod
    def get_new_objectives(self) -> List[Dict]:
        """
        Returns a list of new objectives to add to the framework.

        Each objective dict should contain:
        - chapter_id: int - Parent chapter ID
        - subchapter: str - Subchapter identifier (e.g., "3.2.1")
        - title: str - Objective title
        - requirement_description: str - What the requirement mandates
        - objective_utilities: str - Why this objective matters
        - compliance_status_id: int (optional) - Initial compliance status

        Example:
        [
            {
                "chapter_id": 4,
                "subchapter": "4.3.5",
                "title": "Incident Response Training",
                "requirement_description": "Staff must receive incident response training annually",
                "objective_utilities": "Ensures rapid and effective response to security incidents"
            }
        ]
        """
        pass

    @abstractmethod
    def get_updated_objectives(self) -> List[Dict]:
        """
        Returns a list of existing objectives to update.

        Each objective dict should contain:
        - subchapter: str - Identifies which objective to update (unique identifier)
        - Any fields to update (title, requirement_description, objective_utilities, etc.)

        Example:
        [
            {
                "subchapter": "3.2.1",
                "requirement_description": "Updated requirement text...",
                "objective_utilities": "Updated utility description..."
            }
        ]
        """
        pass

    def get_updated_questions(self) -> List[Dict]:
        """
        Returns a list of existing questions to update.

        Each question dict should contain:
        - question_id: str - UUID of the question to update
        - Any fields to update (text, description, mandatory, etc.)

        Example:
        [
            {
                "question_id": "9988db9b-b9d1-43e6-a1f6-029eba489928",
                "text": "Updated question text?",
                "description": "Updated description"
            }
        ]

        Note: This method is optional and defaults to returning an empty list.
        """
        return []

    def get_metadata(self) -> Dict:
        """
        Returns metadata about this update.
        """
        return {
            "version": self.version,
            "description": self.description,
            "framework_name": self.framework_name,
            "created_at": datetime.utcnow().isoformat()
        }
