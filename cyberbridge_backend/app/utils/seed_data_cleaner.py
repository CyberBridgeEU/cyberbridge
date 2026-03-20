"""
Utility module for cleaning seed data by removing duplicates.

This module provides functions to deduplicate questions and objectives from framework data.
Use this when creating new framework seed files to ensure only unique data is stored.
"""

from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


def extract_unique_questions(
    framework_data: List[Dict[str, Any]],
    question_field: str = 'conformity_questions'
) -> List[str]:
    """
    Extract unique questions from framework data.

    Args:
        framework_data: List of framework items containing questions
        question_field: Name of the field containing questions (default: 'conformity_questions')

    Returns:
        List of unique questions in the order they first appear
    """
    seen_questions = set()
    unique_questions = []

    for item in framework_data:
        questions = item.get(question_field, [])

        # Handle both list and single string formats
        if isinstance(questions, str):
            questions = [questions]

        for question in questions:
            if question and question not in seen_questions:
                seen_questions.add(question)
                unique_questions.append(question)

    logger.info(f"Extracted {len(unique_questions)} unique questions from {question_field}")
    return unique_questions


def extract_unique_objectives(
    framework_data: List[Dict[str, Any]],
    identifier_field: str = 'objective_title'
) -> List[Dict[str, Any]]:
    """
    Extract unique objectives from framework data.

    Args:
        framework_data: List of framework items containing objectives
        identifier_field: Field name to use for identifying unique objectives

    Returns:
        List of unique objective items in the order they first appear
    """
    seen_objectives = {}
    unique_objectives = []

    for item in framework_data:
        identifier = item.get(identifier_field)

        if identifier and identifier not in seen_objectives:
            seen_objectives[identifier] = True
            unique_objectives.append(item)

    logger.info(f"Extracted {len(unique_objectives)} unique objectives")
    return unique_objectives


def generate_cleaned_framework_data(
    raw_data: List[Dict[str, Any]]
) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    """
    Generate cleaned framework data with unique questions and objectives.

    This is the main function to use when preparing seed file data.

    Args:
        raw_data: Raw framework data from Excel/source

    Returns:
        Tuple of (unique_conformity_questions, unique_audit_questions, unique_objectives)
    """
    logger.info("Cleaning framework data...")

    # Extract unique conformity questions
    unique_conformity_questions = extract_unique_questions(
        raw_data,
        question_field='conformity_questions'
    )

    # Extract unique audit questions (if present)
    unique_audit_questions = extract_unique_questions(
        raw_data,
        question_field='audit_question'
    )

    # Extract unique objectives
    unique_objectives = extract_unique_objectives(
        raw_data,
        identifier_field='objective_title'
    )

    logger.info(f"Cleaning complete: {len(unique_conformity_questions)} conformity questions, "
                f"{len(unique_audit_questions)} audit questions, {len(unique_objectives)} objectives")

    return unique_conformity_questions, unique_audit_questions, unique_objectives


def deduplicate_list(items: List[Any], preserve_order: bool = True) -> List[Any]:
    """
    Remove duplicates from a list while optionally preserving order.

    Args:
        items: List to deduplicate
        preserve_order: Whether to preserve the original order (default: True)

    Returns:
        List with duplicates removed
    """
    if preserve_order:
        seen = set()
        result = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
    else:
        return list(set(items))
