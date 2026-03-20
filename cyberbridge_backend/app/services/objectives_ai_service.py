"""
Service for AI-powered objectives analysis based on assessment answers.
Analyzes all assessment data including answers, evidence files, and policies
to suggest compliance statuses for objectives.
"""
import os
import uuid
import PyPDF2
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models import models
from app.services.llm_service import LLMService


def extract_pdf_text(file_path: str, max_chars: int = 2000) -> str:
    """Extract text from a PDF file, limited to max_chars."""
    try:
        if not os.path.exists(file_path):
            return f"[File not found: {os.path.basename(file_path)}]"

        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_parts = []
            total_chars = 0

            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if total_chars + len(page_text) > max_chars:
                    remaining = max_chars - total_chars
                    text_parts.append(page_text[:remaining])
                    break
                text_parts.append(page_text)
                total_chars += len(page_text)

            return ' '.join(text_parts)
    except Exception as e:
        return f"[Error reading PDF: {str(e)}]"


def extract_file_content(file_path: str, file_type: str, max_chars: int = 500) -> str:
    """Extract content from evidence files based on type with reduced character limit."""
    try:
        if not os.path.exists(file_path):
            return f"[File not accessible: {os.path.basename(file_path)}]"

        # Handle PDF files - reduced limit
        if file_type == 'application/pdf' or file_path.endswith('.pdf'):
            return extract_pdf_text(file_path, max_chars=max_chars)

        # Handle text files - reduced limit
        if file_type.startswith('text/') or file_path.endswith(('.txt', '.log', '.md', '.csv')):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read(max_chars)
            except UnicodeDecodeError:
                return f"[Binary file: {os.path.basename(file_path)}]"

        # For other files, just return metadata
        file_size = os.path.getsize(file_path)
        return f"[{file_type} file: {os.path.basename(file_path)}, Size: {file_size} bytes]"

    except Exception as e:
        return f"[Error processing file: {str(e)}]"


def gather_assessment_data(db: Session, framework_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, Any]:
    """
    Gather all assessment data for a specific framework and user.
    Returns structured data including answers, evidence, and policies.
    """

    # Get all assessments for this framework and user
    assessments = db.query(models.Assessment).filter(
        and_(
            models.Assessment.framework_id == framework_id,
            models.Assessment.user_id == user_id
        )
    ).all()

    if not assessments:
        return {
            "assessments": [],
            "total_answers": 0,
            "answered_questions": 0,
            "policies_linked": 0
        }

    assessment_ids = [a.id for a in assessments]

    # Get all answers with related data
    answers_data = (
        db.query(
            models.Answer.id,
            models.Answer.value,
            models.Answer.evidence_description,
            models.Answer.policy_id,
            models.Question.text.label('question_text'),
            models.Question.description.label('question_description'),
            models.Policies.title.label('policy_title'),
            models.Policies.body.label('policy_body')
        )
        .join(models.Question, models.Answer.question_id == models.Question.id)
        .outerjoin(models.Policies, models.Answer.policy_id == models.Policies.id)
        .filter(models.Answer.assessment_id.in_(assessment_ids))
        .all()
    )

    # Structure the data
    structured_answers = []
    answered_count = 0
    policies_set = set()

    for answer in answers_data:
        # Get evidence files for this answer
        evidence_files = db.query(models.Evidence).filter(
            models.Evidence.answer_id == answer.id
        ).all()

        # Extract evidence file content
        evidence_summaries = []
        for evidence in evidence_files:
            file_content = extract_file_content(evidence.filepath, evidence.file_type)
            evidence_summaries.append({
                "filename": evidence.filename,
                "type": evidence.file_type,
                "size": evidence.file_size,
                "content_summary": file_content
            })

        # Track if question is answered
        if answer.value and answer.value.strip():
            answered_count += 1

        # Track unique policies
        if answer.policy_id:
            policies_set.add(answer.policy_id)

        structured_answers.append({
            "question": answer.question_text,
            "question_description": answer.question_description,
            "answer": answer.value,
            "evidence_description": answer.evidence_description,
            "policy_title": answer.policy_title,
            "policy_body": answer.policy_body,
            "evidence_files": evidence_summaries
        })

    return {
        "assessments": structured_answers,
        "total_answers": len(answers_data),
        "answered_questions": answered_count,
        "policies_linked": len(policies_set)
    }


def build_objectives_analysis_prompt(
    db: Session,
    framework_id: uuid.UUID,
    user_id: uuid.UUID,
    objectives: List[Dict[str, Any]]
) -> str:
    """
    Build a comprehensive prompt for LLM to analyze objectives based on assessment data.
    """

    # Gather all assessment data
    assessment_data = gather_assessment_data(db, framework_id, user_id)

    # Get framework name
    framework = db.query(models.Framework).filter(models.Framework.id == framework_id).first()
    framework_name = framework.name if framework else "Unknown Framework"

    # Build the prompt
    prompt = f"""You are a cybersecurity compliance expert analyzing assessment data to determine objective compliance statuses.

FRAMEWORK: {framework_name}

ASSESSMENT DATA SUMMARY:
- Total Questions: {assessment_data['total_answers']}
- Answered Questions: {assessment_data['answered_questions']}
- Policies Linked: {assessment_data['policies_linked']}

DETAILED ASSESSMENT ANSWERS:
"""

    # Add each answer with all details
    for idx, answer in enumerate(assessment_data['assessments'], 1):
        if not answer['answer'] or not answer['answer'].strip():
            continue  # Skip unanswered questions

        prompt += f"\n--- Question {idx} ---\n"
        prompt += f"Question: {answer['question']}\n"
        if answer['question_description']:
            prompt += f"Description: {answer['question_description']}\n"
        prompt += f"Answer: {answer['answer']}\n"

        if answer['evidence_description']:
            prompt += f"Evidence Description: {answer['evidence_description']}\n"

        if answer['policy_title']:
            prompt += f"Linked Policy: {answer['policy_title']}\n"
            if answer['policy_body']:
                # Limit policy body to 200 chars
                policy_body = answer['policy_body'][:200]
                prompt += f"Policy Summary: {policy_body}...\n"

        if answer['evidence_files']:
            prompt += f"Evidence Files: {len(answer['evidence_files'])} file(s) - "
            file_names = [e['filename'] for e in answer['evidence_files'][:3]]  # Limit to 3 files
            prompt += f"{', '.join(file_names)}\n"

    # Add objectives to analyze
    prompt += f"\n\nOBJECTIVES TO ANALYZE ({len(objectives)}):\n"
    for idx, objective in enumerate(objectives, 1):
        prompt += f"\n{idx}. {objective['title']}\n"
        if objective.get('chapter'):
            prompt += f"   Chapter: {objective['chapter']}\n"
        if objective.get('subchapter'):
            prompt += f"   Subchapter: {objective['subchapter']}\n"
        if objective.get('requirement_description'):
            prompt += f"   Requirement: {objective['requirement_description']}\n"

    # Add instructions
    prompt += """

TASK:
Analyze all the assessment answers, evidence descriptions, evidence files, and linked policies above.
For each objective, determine:
1. Recommended Compliance Status (choose one):
   - "compliant": Sufficient evidence shows full compliance
   - "partially compliant": Some evidence exists but gaps remain
   - "not compliant": No or insufficient evidence
   - "not assessed": Cannot determine from available data
   - "in review": Evidence suggests compliance but needs verification
   - "not applicable": Objective doesn't apply based on context

2. Confidence Level (0-100%): How confident are you in this recommendation?

3. Supporting Evidence: Which questions/answers support this status?

4. Gaps Identified: What evidence is missing or needed?

5. Recommended Policies: Which policies should be linked to this objective?

6. Suggested Objective Body: A concise summary (2-3 sentences) of why this status was chosen.

IMPORTANT: Base your analysis ONLY on the evidence provided. Be conservative - if evidence is weak or missing, mark as "partially compliant" or "not assessed".

Return your analysis in JSON format:
{
  "objectives": [
    {
      "objective_id": "<objective ID>",
      "objective_title": "<objective title>",
      "recommended_status": "<status>",
      "confidence": <0-100>,
      "supporting_evidence": ["question 1 shows...", "question 5 demonstrates..."],
      "gaps": ["Missing evidence for...", "Need documentation of..."],
      "recommended_policies": ["Policy title 1", "Policy title 2"],
      "suggested_body": "Brief summary of compliance basis..."
    }
  ]
}
"""

    return prompt


def build_batch_prompt(
    assessment_summary: str,
    objectives_batch: List[Dict[str, Any]],
    framework_name: str
) -> str:
    """Build a prompt for analyzing a batch of objectives."""
    prompt = f"""You are a cybersecurity compliance expert. Based on the assessment summary below, analyze these objectives.

FRAMEWORK: {framework_name}

{assessment_summary}

OBJECTIVES TO ANALYZE ({len(objectives_batch)}):
"""

    for idx, objective in enumerate(objectives_batch, 1):
        prompt += f"\n{idx}. ID: {objective['id']}\n"
        prompt += f"   Title: {objective['title']}\n"
        if objective.get('chapter'):
            prompt += f"   Chapter: {objective['chapter']}\n"
        if objective.get('subchapter'):
            prompt += f"   Subchapter: {objective['subchapter']}\n"
        if objective.get('requirement_description'):
            prompt += f"   Requirement: {objective['requirement_description'][:300]}...\n"

    prompt += """

TASK:
For each objective, determine:
1. Recommended Status: compliant, partially compliant, not compliant, not assessed, in review, or not applicable
2. Confidence (0-100%)
3. Brief reasoning (1-2 sentences)

Return ONLY valid JSON:
{
  "objectives": [
    {
      "objective_id": "<id>",
      "recommended_status": "<status>",
      "confidence": <0-100>,
      "reasoning": "Brief explanation..."
    }
  ]
}
"""
    return prompt


def create_assessment_summary(db: Session, framework_id: uuid.UUID, user_id: uuid.UUID) -> str:
    """Create a concise summary of assessment data for context."""
    assessment_data = gather_assessment_data(db, framework_id, user_id)

    summary = f"""ASSESSMENT SUMMARY:
- Total Questions: {assessment_data['total_answers']}
- Answered: {assessment_data['answered_questions']}
- Policies Linked: {assessment_data['policies_linked']}

KEY ANSWERED QUESTIONS (showing up to 20):
"""

    # Include only answered questions, limit to 20
    answered_questions = [a for a in assessment_data['assessments'] if a['answer'] and a['answer'].strip()][:20]

    for idx, answer in enumerate(answered_questions, 1):
        summary += f"\n{idx}. Q: {answer['question'][:100]}...\n"
        summary += f"   A: {answer['answer']}\n"
        if answer['evidence_description']:
            summary += f"   Evidence: {answer['evidence_description'][:100]}...\n"
        if answer['policy_title']:
            summary += f"   Policy: {answer['policy_title']}\n"

    return summary


async def analyze_objectives_with_ai(
    db: Session,
    framework_id: uuid.UUID,
    user_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Simple keyword matching between answered questions and objectives.
    No LLM needed - instant results with match percentage.
    """
    import logging
    import re
    from difflib import SequenceMatcher
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Starting keyword-based matching for framework_id={framework_id}, user_id={user_id}")

        # Get ONLY answered questions for this framework
        assessment_data = gather_assessment_data(db, framework_id, user_id)
        answered_questions = [a for a in assessment_data['assessments'] if a['answer'] and a['answer'].strip()]

        logger.info(f"Found {len(answered_questions)} answered questions")

        if not answered_questions:
            return {
                "success": False,
                "error": "No answered questions found. Please complete some assessment questions first.",
                "objectives_count": 0,
                "suggestions": []
            }

        # Get all objectives with compliance statuses
        objectives = (
            db.query(models.Objectives)
            .join(models.Chapters, models.Objectives.chapter_id == models.Chapters.id)
            .filter(models.Chapters.framework_id == framework_id)
            .all()
        )
        logger.info(f"Found {len(objectives)} objectives")

        if not objectives:
            return {
                "success": False,
                "error": "No objectives found for this framework",
                "objectives_count": 0,
                "suggestions": []
            }

        # Get compliance statuses
        partially_compliant_status = db.query(models.ComplianceStatuses).filter(
            models.ComplianceStatuses.status_name == "partially compliant"
        ).first()

        # Build searchable text from all answered questions
        questions_text = " ".join([
            f"{q['question']} {q['answer']} {q.get('evidence_description', '')}"
            for q in answered_questions
        ]).lower()

        # Extract keywords from questions (remove common words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can'}
        question_keywords = set(re.findall(r'\b\w{4,}\b', questions_text))
        question_keywords = question_keywords - stop_words

        logger.info(f"Extracted {len(question_keywords)} keywords from answered questions")

        # Match each objective
        all_suggestions = []
        for obj in objectives:
            # Skip objectives that already have a status
            if obj.compliance_status_id:
                continue

            # Build objective text (subchapter + title only)
            objective_text = f"{obj.subchapter or ''} {obj.title or ''}".lower()
            objective_keywords = set(re.findall(r'\b\w{4,}\b', objective_text))
            objective_keywords = objective_keywords - stop_words

            # Calculate match percentage
            if not objective_keywords:
                match_percentage = 0
            else:
                matching_keywords = question_keywords & objective_keywords
                match_percentage = int((len(matching_keywords) / len(objective_keywords)) * 100)

            # Only suggest if match is > 30%
            if match_percentage >= 30:
                suggestion = {
                    "objective_id": str(obj.id),
                    "objective_title": obj.title or "",
                    "subchapter": obj.subchapter or "",
                    "recommended_status": "partially compliant",
                    "recommended_status_id": str(partially_compliant_status.id) if partially_compliant_status else None,
                    "confidence": match_percentage,
                    "supporting_evidence": [],
                    "gaps": [],
                    "recommended_policies": [],
                    "suggested_body": f"Matched {match_percentage}% based on keywords: {', '.join(list(matching_keywords)[:5])}"
                }
                all_suggestions.append(suggestion)

        logger.info(f"Found {len(all_suggestions)} matching objectives")

        # Get framework name
        framework = db.query(models.Framework).filter(models.Framework.id == framework_id).first()
        framework_name = framework.name if framework else "Unknown Framework"

        return {
            "success": True,
            "objectives_count": len(objectives),
            "framework_name": framework_name,
            "suggestions": all_suggestions,
            "total_matches": len(all_suggestions),
            "timestamp": str(uuid.uuid4())[:8]
        }

    except Exception as e:
        logger.error(f"Unexpected error in analyze_objectives_with_ai: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "objectives_count": 0,
            "suggestions": []
        }
