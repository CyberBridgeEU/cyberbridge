"""
Utility module for parsing Excel files and generating framework seed files.

This module handles:
- Excel file parsing and column detection
- Data deduplication and analysis
- Seed file generation
"""

import pandas as pd
import logging
from typing import Dict, List, Any, Tuple, Optional
from .seed_data_cleaner import extract_unique_questions, extract_unique_objectives
import json
import pprint

logger = logging.getLogger(__name__)


class ExcelFrameworkParser:
    """Parse Excel files and generate framework seed file data"""

    def __init__(self, file_path: str):
        """
        Initialize parser with Excel file path.

        Args:
            file_path: Path to the Excel file
        """
        self.file_path = file_path
        self.df = None
        self.column_mapping = {}

    def parse_excel(self) -> pd.DataFrame:
        """
        Parse Excel file and return DataFrame.

        Intelligently detects if the file has title/empty rows and handles them accordingly.

        Returns:
            pandas DataFrame with Excel data
        """
        try:
            # First, try reading the file normally
            df_initial = pd.read_excel(self.file_path)

            # Expected column keywords
            expected_keywords = ['category', 'subcategory', 'sub-category', 'objective', 'description', 'assessment']

            # Check first few rows to find where the actual column headers are
            header_row_index = None
            for row_idx in range(min(5, len(df_initial))):  # Check first 5 rows max
                row_values = df_initial.iloc[row_idx].tolist()
                row_str = [str(val).lower().strip() for val in row_values if pd.notna(val)]

                # Check if this row contains our expected column names
                keyword_matches = sum(1 for keyword in expected_keywords if any(keyword in row_val for row_val in row_str))

                if keyword_matches >= 3:  # If at least 3 expected keywords found
                    header_row_index = row_idx
                    logger.info(f"Detected headers in row {row_idx}")
                    break

            if header_row_index is not None:
                # Found header row embedded in the data, use it
                logger.info(f"Re-reading Excel with header at row {header_row_index}")

                # Get the column names from the detected header row
                new_columns = [str(val).strip() if pd.notna(val) else f"Unnamed_{i}" for i, val in enumerate(df_initial.iloc[header_row_index])]

                # Create new dataframe starting from row after header
                self.df = df_initial.iloc[header_row_index + 1:].copy()
                self.df.columns = new_columns
                self.df.reset_index(drop=True, inplace=True)

                logger.info(f"Re-parsed with detected columns: {new_columns[:5]}")
            else:
                # Normal Excel file with proper headers
                self.df = df_initial
                logger.info("Using default Excel headers")

            logger.info(f"Successfully parsed Excel file with {len(self.df)} rows and {len(self.df.columns)} columns")
            logger.info(f"Column names: {self.df.columns.tolist()[:5]}")
            return self.df
        except Exception as e:
            logger.error(f"Error parsing Excel file: {e}")
            raise

    def detect_columns(self) -> Dict[str, str]:
        """
        Auto-detect column names based on common patterns.

        Returns:
            Dictionary mapping field names to detected column names
        """
        if self.df is None:
            raise ValueError("Excel file not parsed yet. Call parse_excel() first.")

        columns = self.df.columns.tolist()
        column_mapping = {}

        logger.info(f"Excel columns found: {columns}")

        # Common column name patterns (case-insensitive)
        patterns = {
            'chapter_title': ['category'],
            'subchapter': ['subcategory', 'sub-category', 'sub category'],
            'objective_title': ['objective'],
            'requirement_description': ['description'],
            'conformity_questions': ['assessment']
        }

        for field, pattern_list in patterns.items():
            for col in columns:
                col_lower = str(col).lower().strip()
                if any(pattern in col_lower for pattern in pattern_list):
                    column_mapping[field] = col
                    logger.info(f"Matched field '{field}' to column '{col}'")
                    break

        self.column_mapping = column_mapping
        logger.info(f"Detected column mapping: {column_mapping}")
        return column_mapping

    def parse_framework_data(self, column_mapping: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Parse framework data from Excel using column mapping.

        Args:
            column_mapping: Optional custom column mapping. If not provided, uses auto-detected mapping.

        Returns:
            List of dictionaries containing framework data
        """
        if self.df is None:
            raise ValueError("Excel file not parsed yet. Call parse_excel() first.")

        if column_mapping:
            self.column_mapping = column_mapping
        elif not self.column_mapping:
            self.detect_columns()

        framework_data = []

        for idx, row in self.df.iterrows():
            item = {}

            # Extract chapter info
            if 'chapter_title' in self.column_mapping:
                item['chapter_title'] = str(row[self.column_mapping['chapter_title']]) if pd.notna(row[self.column_mapping['chapter_title']]) else ''

            if 'subchapter' in self.column_mapping:
                item['subchapter'] = str(row[self.column_mapping['subchapter']]) if pd.notna(row[self.column_mapping['subchapter']]) else None

            # Extract objective info
            if 'objective_title' in self.column_mapping:
                item['objective_title'] = str(row[self.column_mapping['objective_title']]) if pd.notna(row[self.column_mapping['objective_title']]) else ''

            if 'requirement_description' in self.column_mapping:
                item['requirement_description'] = str(row[self.column_mapping['requirement_description']]) if pd.notna(row[self.column_mapping['requirement_description']]) else None

            # Extract questions - only those starting with Q-
            if 'conformity_questions' in self.column_mapping:
                questions_text = str(row[self.column_mapping['conformity_questions']]) if pd.notna(row[self.column_mapping['conformity_questions']]) else ''
                # Split by newline and filter to only include questions starting with Q-
                all_questions = [q.strip() for q in questions_text.split('\n') if q.strip()] if questions_text else []
                filtered_questions = [q for q in all_questions if q.startswith('Q-')]
                item['conformity_questions'] = filtered_questions

                # Log first row for debugging
                if idx == 0 and all_questions:
                    logger.info(f"Sample questions from first row: {all_questions[:3]}")
                    logger.info(f"Filtered questions (Q- only): {filtered_questions[:3]}")

            framework_data.append(item)

        logger.info(f"Parsed {len(framework_data)} rows of framework data")
        return framework_data

    def analyze_data(self, framework_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze framework data and provide deduplication metrics.

        Args:
            framework_data: List of framework data dictionaries

        Returns:
            Dictionary containing analysis metrics
        """
        # Count raw data
        total_conformity_questions = sum(len(item.get('conformity_questions', [])) for item in framework_data)
        total_objectives = len(framework_data)

        # Extract unique data
        unique_conformity_questions = extract_unique_questions(framework_data, 'conformity_questions')
        unique_objectives = extract_unique_objectives(framework_data, 'objective_title')

        # Calculate reductions
        conformity_reduction = ((total_conformity_questions - len(unique_conformity_questions)) / total_conformity_questions * 100) if total_conformity_questions > 0 else 0
        objectives_reduction = ((total_objectives - len(unique_objectives)) / total_objectives * 100) if total_objectives > 0 else 0

        metrics = {
            'conformity_questions': {
                'total': total_conformity_questions,
                'unique': len(unique_conformity_questions),
                'reduction_percent': round(conformity_reduction, 1)
            },
            'audit_questions': {
                'total': 0,
                'unique': 0,
                'reduction_percent': 0
            },
            'objectives': {
                'total': total_objectives,
                'unique': len(unique_objectives),
                'reduction_percent': round(objectives_reduction, 1)
            }
        }

        logger.info(f"Analysis complete: {metrics}")
        return metrics

    @staticmethod
    def _format_python_data(data: Any, indent: int = 8) -> str:
        """
        Format Python data structures with proper Python syntax (None instead of null).

        Args:
            data: Data to format (list, dict, string, None, etc.)
            indent: Number of spaces for indentation

        Returns:
            Formatted string with Python syntax
        """
        # Use pprint to format, then adjust indentation
        formatted = pprint.pformat(data, width=120, compact=False)

        # Add proper indentation to each line
        indent_str = ' ' * indent
        lines = formatted.split('\n')
        indented_lines = [indent_str + line if i > 0 else line for i, line in enumerate(lines)]

        return '\n'.join(indented_lines)

    def generate_seed_file_content(
        self,
        framework_name: str,
        framework_description: str,
        framework_data: List[Dict[str, Any]],
        allowed_scope_types: Optional[List[str]] = None,
        scope_selection_mode: Optional[str] = "optional"
    ) -> str:
        """
        Generate Python seed file content.

        Args:
            framework_name: Name of the framework
            framework_description: Description of the framework
            framework_data: List of framework data dictionaries

        Returns:
            String containing Python seed file content
        """
        # Extract unique data
        unique_conformity_questions = extract_unique_questions(framework_data, 'conformity_questions')
        unique_objectives = extract_unique_objectives(framework_data, 'objective_title')

        # Generate class name from framework name - remove all special characters
        # Remove parentheses, brackets, commas and other special chars before processing
        clean_name = framework_name.replace('(', '').replace(')', '').replace('[', '').replace(']', '').replace(',', '')
        class_name = ''.join(word.capitalize() for word in clean_name.replace('-', ' ').replace('_', ' ').replace('.', ' ').split()) + 'Seed'

        # Generate seed file content - sanitize filename for Python module (replace spaces, dots, hyphens with underscores)
        sanitized_name = framework_name.lower()
        sanitized_name = sanitized_name.replace('(', '').replace(')', '').replace('[', '').replace(']', '').replace(',', '')
        sanitized_name = sanitized_name.replace(' ', '_').replace('-', '_').replace('.', '_')
        # Remove multiple consecutive underscores
        while '__' in sanitized_name:
            sanitized_name = sanitized_name.replace('__', '_')
        # Remove leading/trailing underscores
        sanitized_filename = sanitized_name.strip('_')
        seed_content = f'''# app/seeds/{sanitized_filename}_seed.py
import logging
from .base_seed import BaseSeed
from app.models import models

logger = logging.getLogger(__name__)


class {class_name}(BaseSeed):
    """Seed {framework_name} framework and its associated questions"""

    def __init__(self, db, organizations, assessment_types):
        super().__init__(db)
        self.organizations = organizations
        self.assessment_types = assessment_types

    def seed(self) -> dict:
        logger.info("Creating {framework_name} framework and questions...")

        # Get default organization
        default_org = list(self.organizations.values())[0]
        conformity_assessment_type = self.assessment_types["conformity"]

        # Create {framework_name} Framework
        {sanitized_filename}_framework, created = self.get_or_create(
            models.Framework,
            {{"name": "{framework_name}", "organisation_id": default_org.id}},
            {{
                "name": "{framework_name}",
                "description": "{framework_description}",
                "organisation_id": default_org.id,
                "allowed_scope_types": {repr(json.dumps(allowed_scope_types)) if allowed_scope_types else None},
                "scope_selection_mode": {repr(scope_selection_mode)}
            }}
        )

        # If framework already exists, skip question creation to prevent duplicates
        if not created:
            logger.info("{framework_name} framework already exists, skipping question creation to prevent duplicates")

            # Get existing questions for this framework
            existing_questions = self.db.query(models.Question).join(
                models.FrameworkQuestion,
                models.Question.id == models.FrameworkQuestion.question_id
            ).filter(
                models.FrameworkQuestion.framework_id == {sanitized_filename}_framework.id
            ).all()

            # Get existing objectives for this framework
            existing_objectives = self.db.query(models.Objectives).join(
                models.Chapters,
                models.Objectives.chapter_id == models.Chapters.id
            ).filter(
                models.Chapters.framework_id == {sanitized_filename}_framework.id
            ).all()

            logger.info(f"Found existing {framework_name} framework with {{len(existing_questions)}} questions and {{len(existing_objectives)}} objectives")

            return {{
                "framework": {sanitized_filename}_framework,
                "conformity_questions": existing_questions,
                "objectives": existing_objectives
            }}

        # Get unique questions and objectives
        unique_conformity_questions = self._get_unique_conformity_questions()
        unique_objectives_data = self._get_unique_objectives()

        # Create conformity questions
        conformity_questions = []
        question_order = 1

        for conf_q_text in unique_conformity_questions:
            # Always create new questions for each framework (no sharing across frameworks)
            question = models.Question(
                text=conf_q_text,
                description="{framework_name} conformity question",
                mandatory=True,
                assessment_type_id=conformity_assessment_type.id
            )
            self.db.add(question)
            self.db.flush()  # Get the question ID
            conformity_questions.append(question)

            # Create framework-question relationship
            framework_question = models.FrameworkQuestion(
                framework_id={sanitized_filename}_framework.id,
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
                        "framework_id": {sanitized_filename}_framework.id
                    }},
                    {{
                        "title": chapter_title,
                        "framework_id": {sanitized_filename}_framework.id
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
                    "requirement_description": item.get('requirement_description')
                }}
            )
            objectives_list.append(objective)

        self.db.commit()

        logger.info(f"Created {framework_name} framework with {{len(unique_conformity_questions)}} conformity questions and {{len(unique_objectives_data)}} objectives")

        return {{
            "framework": {sanitized_filename}_framework,
            "conformity_questions": conformity_questions,
            "objectives": objectives_list
        }}

    def _get_unique_conformity_questions(self):
        """Returns the list of unique conformity questions (pre-deduplicated)"""
        return {self._format_python_data(unique_conformity_questions, indent=8)}

    def _get_unique_objectives(self):
        """Returns the list of unique objectives (pre-deduplicated)"""
        return {self._format_python_data(unique_objectives, indent=8)}
'''

        return seed_content
