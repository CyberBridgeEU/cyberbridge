"""
Service for generating AI-powered compliance roadmaps for objectives.
Gathers context (assessment data, policies, evidence, CTI indicators, RAG)
and produces actionable step-by-step plans to reach compliance.
"""
import json
import logging
import re
import uuid
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import models
from app.services.llm_service import LLMService
from app.services.objectives_ai_service import gather_assessment_data

logger = logging.getLogger(__name__)

LLM_TIMEOUT = 120


def _parse_llm_json(text: str) -> Optional[dict]:
    """Try to extract and parse JSON from LLM response text."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    stripped = re.sub(r'```(?:json)?\s*', '', text).strip()
    if stripped != text:
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        try:
            start = stripped.index(start_char)
            end = stripped.rindex(end_char) + 1
            json_str = stripped[start:end]
            return json.loads(json_str)
        except (ValueError, json.JSONDecodeError):
            continue
    logger.warning(f"Could not parse JSON from LLM response: {text[:200]}")
    return None


class RoadmapService:
    def __init__(self, db: Session, current_user=None):
        self.db = db
        self.current_user = current_user

    # ── Public API ──────────────────────────────────────────────

    async def generate_roadmap(
        self, objective_id: uuid.UUID, framework_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Generate a compliance roadmap for a single objective."""
        context = self._gather_objective_context(objective_id, framework_id)
        if not context:
            return {"success": False, "error": "Objective not found"}

        prompt = self._build_roadmap_prompt(context)
        raw = await self._call_llm(prompt)
        if raw is None:
            return {"success": False, "error": "Failed to get LLM response"}

        roadmap = self._normalize_response(raw, context)
        return {"success": True, "roadmap": roadmap}

    async def generate_roadmap_bulk(
        self, framework_id: uuid.UUID, objective_ids: List[uuid.UUID]
    ) -> Dict[str, Any]:
        """Generate roadmaps for multiple objectives."""
        roadmaps = []
        for oid in objective_ids:
            result = await self.generate_roadmap(oid, framework_id)
            if result.get("success"):
                roadmaps.append(result["roadmap"])
        return {"success": True, "roadmaps": roadmaps, "total": len(roadmaps)}

    # ── Context gathering ───────────────────────────────────────

    def _gather_objective_context(
        self, objective_id: uuid.UUID, framework_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        objective = (
            self.db.query(models.Objectives)
            .filter(models.Objectives.id == objective_id)
            .first()
        )
        if not objective:
            return None

        # Chapter
        chapter = (
            self.db.query(models.Chapters)
            .filter(models.Chapters.id == objective.chapter_id)
            .first()
        )

        # Framework
        framework = (
            self.db.query(models.Framework)
            .filter(models.Framework.id == framework_id)
            .first()
        )

        # Compliance status label
        compliance_label = "Not Assessed"
        if objective.compliance_status_id:
            cs = (
                self.db.query(models.ComplianceStatuses)
                .filter(models.ComplianceStatuses.id == objective.compliance_status_id)
                .first()
            )
            if cs:
                compliance_label = cs.status_name

        # Linked policies via PolicyObjectives
        linked_policies = (
            self.db.query(
                models.Policies.id,
                models.Policies.title,
                models.Policies.body,
                models.PolicyStatuses.status.label("status_name"),
            )
            .join(
                models.PolicyObjectives,
                models.Policies.id == models.PolicyObjectives.policy_id,
            )
            .outerjoin(
                models.PolicyStatuses,
                models.Policies.status_id == models.PolicyStatuses.id,
            )
            .filter(models.PolicyObjectives.objective_id == objective_id)
            .all()
        )

        # Lightweight assessment data — only grab a few answered questions
        user_id = uuid.UUID(str(self.current_user.id)) if self.current_user else None
        answered_summary: list = []
        if user_id:
            try:
                assessment_data = gather_assessment_data(self.db, framework_id, user_id)
                answered_summary = [
                    {"question": a["question"][:80], "answer": a["answer"][:100]}
                    for a in assessment_data.get("assessments", [])
                    if a.get("answer") and a["answer"].strip()
                ][:3]  # Only top 3 to keep prompt small
            except Exception:
                pass

        # CTI indicators — just top 3
        cti_indicators: list = []
        org_id = getattr(self.current_user, "organisation_id", None) if self.current_user else None
        if org_id:
            try:
                cti_indicators = (
                    self.db.query(models.CtiIndicator)
                    .filter(models.CtiIndicator.organisation_id == org_id)
                    .order_by(models.CtiIndicator.severity.desc())
                    .limit(3)
                    .all()
                )
            except Exception:
                pass

        return {
            "objective": {
                "id": str(objective.id),
                "title": objective.title or "",
                "subchapter": objective.subchapter or "",
                "requirement_description": objective.requirement_description or "",
                "objective_utilities": objective.objective_utilities or "",
                "compliance_status": compliance_label,
                "has_evidence": bool(objective.evidence_filename),
                "evidence_filename": objective.evidence_filename or "",
                "applicable_operators": objective.applicable_operators or "",
            },
            "chapter_title": chapter.title if chapter else "",
            "framework_name": framework.name if framework else "",
            "policies": [
                {
                    "title": p.title,
                    "body": (p.body or "")[:200],
                    "status": p.status_name or "unknown",
                }
                for p in linked_policies
            ],
            "answered_summary": answered_summary,
            "cti_indicators": [
                {"name": ind.name, "severity": ind.severity}
                for ind in cti_indicators
            ],
        }

    # ── Prompt building ─────────────────────────────────────────

    def _build_roadmap_prompt(self, ctx: Dict[str, Any]) -> str:
        obj = ctx["objective"]

        # Keep requirement and guidance short
        requirement = (obj['requirement_description'] or '')[:200]
        guidance = (obj['objective_utilities'] or '')[:150]

        prompt = f"""You are a compliance expert. Create an actionable roadmap for this objective.

FRAMEWORK: {ctx['framework_name']}
OBJECTIVE: {obj['title']}
REQUIREMENT: {requirement}
GUIDANCE: {guidance}
STATUS: {obj['compliance_status']}
EVIDENCE: {'Yes' if obj['has_evidence'] else 'No'}
"""
        # Policies — keep compact
        policies = ctx.get("policies", [])
        if policies:
            prompt += "POLICIES: " + "; ".join(f"{p['title']} ({p['status']})" for p in policies[:3]) + "\n"

        # Assessment — very brief
        answered = ctx.get("answered_summary", [])
        if answered:
            prompt += "ASSESSMENT ANSWERS:\n"
            for a in answered:
                prompt += f"- Q: {a['question']} A: {a['answer']}\n"

        # CTI — one line
        cti = ctx.get("cti_indicators", [])
        if cti:
            prompt += "FINDINGS: " + "; ".join(f"{ind['name']} (sev:{ind['severity']})" for ind in cti) + "\n"

        prompt += """
Return ONLY valid JSON, max 5 action steps:
{"gap_summary":"what is missing","action_steps":[{"step_number":1,"title":"short title","description":"what to do","priority":"critical|high|medium|low","estimated_effort":"time estimate","category":"technical|policy|evidence|process|training","platform_action":"Upload evidence|Create policy|Run scan|null"}],"estimated_total_effort":"total time","quick_wins":["immediate actions"],"dependencies":["blocking items"],"risk_if_unaddressed":"consequence"}"""
        return prompt

    # ── LLM interaction ─────────────────────────────────────────

    def _get_effective_llm_settings(self) -> dict:
        global_settings = self.db.query(models.LLMSettings).first()
        if global_settings and global_settings.ai_enabled == False:
            return {"ai_enabled": False, "llm_provider": "llamacpp"}

        user_org_id = (
            getattr(self.current_user, "organisation_id", None)
            if self.current_user
            else None
        )
        if user_org_id:
            org_settings = (
                self.db.query(models.OrganizationLLMSettings)
                .filter(models.OrganizationLLMSettings.organisation_id == user_org_id)
                .first()
            )
            if org_settings and org_settings.is_enabled:
                return {
                    "ai_enabled": True,
                    "llm_provider": org_settings.llm_provider,
                    "qlon_url": org_settings.qlon_url,
                    "qlon_api_key": org_settings.qlon_api_key,
                    "qlon_use_tools": (
                        org_settings.qlon_use_tools
                        if org_settings.qlon_use_tools is not None
                        else True
                    ),
                }

        return {
            "ai_enabled": True,
            "llm_provider": (
                getattr(global_settings, "default_provider", "llamacpp") or "llamacpp"
            )
            if global_settings
            else "llamacpp",
        }

    async def _call_llm(self, prompt: str) -> Optional[dict]:
        try:
            effective = self._get_effective_llm_settings()
            if not effective.get("ai_enabled", True):
                logger.warning("AI is disabled")
                return None

            llm_service = LLMService(self.db)
            provider = effective.get("llm_provider", "llamacpp")

            if (
                provider == "qlon"
                and effective.get("qlon_url")
                and effective.get("qlon_api_key")
            ):
                response_text = await llm_service.generate_text_with_qlon(
                    prompt,
                    qlon_url=effective["qlon_url"],
                    qlon_api_key=effective["qlon_api_key"],
                    use_tools=effective.get("qlon_use_tools", True),
                    timeout=LLM_TIMEOUT,
                )
            else:
                if provider == "llamacpp":
                    llm_service.llm_backend = "llamacpp"
                response_text = await llm_service.generate_text(
                    prompt, timeout=LLM_TIMEOUT
                )

            return _parse_llm_json(response_text)
        except Exception as e:
            logger.error(f"Roadmap LLM call failed: {e}")
            return None

    # ── Response normalization ──────────────────────────────────

    def _normalize_response(
        self, raw: dict, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        obj = context["objective"]

        steps = []
        for step in raw.get("action_steps", [])[:5]:
            steps.append(
                {
                    "step_number": step.get("step_number", len(steps) + 1),
                    "title": str(step.get("title", "Action")),
                    "description": str(step.get("description", "")),
                    "priority": str(step.get("priority", "medium")).lower(),
                    "estimated_effort": str(step.get("estimated_effort", "Unknown")),
                    "category": str(step.get("category", "process")).lower(),
                    "platform_action": step.get("platform_action"),
                    "references": step.get("references", []),
                }
            )

        return {
            "objective_id": obj["id"],
            "objective_title": obj["title"],
            "current_status": obj["compliance_status"],
            "target_status": "compliant",
            "gap_summary": str(raw.get("gap_summary", "")),
            "action_steps": steps,
            "estimated_total_effort": str(
                raw.get("estimated_total_effort", "Unknown")
            ),
            "quick_wins": raw.get("quick_wins", []),
            "dependencies": raw.get("dependencies", []),
            "risk_if_unaddressed": str(raw.get("risk_if_unaddressed", "")),
        }

    def _is_production(self) -> bool:
        import os
        return os.getenv("CONTAINER_ENV") == "docker" or os.getenv("DB_HOST") is not None
