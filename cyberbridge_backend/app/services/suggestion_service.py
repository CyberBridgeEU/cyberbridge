import json
import logging
import re
import uuid as _uuid
from typing import List, Dict, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.constants.suggestion_rules import (
    ASSET_TYPE_TO_RISK_KEYWORDS,
    CIA_RISK_WEIGHTING,
    RISK_CATEGORY_TO_CONTROL_PREFIX,
    CONTROL_PREFIX_TO_POLICY_KEYWORDS,
    POLICY_TO_OBJECTIVE_KEYWORDS,
)
from app.constants.assessment_scan_rules import (
    QUESTION_KEYWORD_TO_SCANNERS,
    SEVERITY_ORDER,
    CAPABILITY_KEYWORDS,
    ABSENCE_KEYWORDS,
)
from app.services.llm_service import LLMService
from app.models import models

logger = logging.getLogger(__name__)

MAX_SUGGESTIONS = 15
MAX_LLM_ITEMS = 15
MAX_LLM_DESC_CHARS = 60
LLM_TIMEOUT = 300


def _keyword_score(text: str, keywords: List[str]) -> int:
    """Score how many keywords match in text. Returns 0-100."""
    if not text or not keywords:
        return 0
    text_lower = text.lower()
    matches = sum(1 for kw in keywords if kw.lower() in text_lower)
    if not matches:
        return 0
    # Normalize: max score when half or more keywords match
    ratio = min(matches / max(len(keywords) * 0.5, 1), 1.0)
    return max(5, min(int(ratio * 100), 100))


def _parse_llm_json(text: str) -> Optional[dict]:
    """Try to extract and parse JSON from LLM response text."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    stripped = re.sub(r'```(?:json)?\s*', '', text).strip()
    if stripped != text:
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
    # Try to find JSON in the text between { and } or [ and ]
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


def _truncate(text: Optional[str], max_chars: int = MAX_LLM_DESC_CHARS) -> str:
    """Truncate text for LLM prompts."""
    if not text:
        return ""
    return text[:max_chars] + ("..." if len(text) > max_chars else "")


class SuggestionService:
    def __init__(self, db: Session, current_user=None):
        self.db = db
        self.current_user = current_user

    # ========== ASSET → RISK ==========

    def suggest_risks_for_asset_rules(
        self,
        asset_name: str,
        asset_type_name: str,
        confidentiality: Optional[str],
        integrity: Optional[str],
        availability: Optional[str],
        description: Optional[str],
        available_risks: List[dict],
    ) -> List[dict]:
        """Rule-based: score available risks against asset context."""
        # Collect keywords from asset type
        keywords: List[str] = []
        asset_type_lower = (asset_type_name or "").lower()
        for type_key, type_keywords in ASSET_TYPE_TO_RISK_KEYWORDS.items():
            if type_key in asset_type_lower:
                keywords.extend(type_keywords)

        # Boost from CIA ratings
        for cia_dim, cia_val in [("confidentiality", confidentiality), ("integrity", integrity), ("availability", availability)]:
            if cia_val and cia_val.lower() in CIA_RISK_WEIGHTING.get(cia_dim, {}):
                keywords.extend(CIA_RISK_WEIGHTING[cia_dim][cia_val.lower()])

        if not keywords:
            # Fallback: use asset name and description words
            fallback_text = f"{asset_name} {asset_type_name} {description or ''}"
            keywords = [w for w in re.split(r'\W+', fallback_text.lower()) if len(w) > 3]

        scored = []
        for risk in available_risks:
            search_text = f"{risk.get('risk_category_name', '')} {risk.get('risk_category_description', '')} {risk.get('risk_potential_impact', '')} {risk.get('risk_control', '')}"
            score = _keyword_score(search_text, keywords)
            if score > 0:
                scored.append({
                    "item_id": risk["id"],
                    "display_name": f"{risk.get('risk_code', '')}: {risk.get('risk_category_name', '')}" if risk.get('risk_code') else risk.get('risk_category_name', 'Unknown'),
                    "confidence": score,
                    "reasoning": f"Matches asset type '{asset_type_name}' keywords",
                })

        scored.sort(key=lambda x: x["confidence"], reverse=True)
        return scored[:MAX_SUGGESTIONS]

    async def suggest_risks_for_asset_llm(
        self,
        asset_name: str,
        asset_type_name: str,
        confidentiality: Optional[str],
        integrity: Optional[str],
        availability: Optional[str],
        description: Optional[str],
        available_risks: List[dict],
    ) -> List[dict]:
        """LLM-based: send asset context + available risks, parse JSON."""
        truncated_risks = [
            {"id": r["id"], "name": _truncate(r.get("risk_category_name", ""), 60), "desc": _truncate(r.get("risk_category_description"))}
            for r in available_risks[:MAX_LLM_ITEMS]
        ]

        prompt = f"""You are a cybersecurity risk analyst. Given the following asset, suggest which risks from the available list are most relevant.

ASSET:
- Name: {asset_name}
- Type: {asset_type_name}
- Confidentiality: {confidentiality or 'N/A'}
- Integrity: {integrity or 'N/A'}
- Availability: {availability or 'N/A'}
- Description: {_truncate(description, 200)}

AVAILABLE RISKS:
{json.dumps(truncated_risks, indent=1)}

Return a JSON array of the most relevant risks (max {MAX_SUGGESTIONS}). No markdown, no code fences, just raw JSON:
[{{"item_id": "uuid", "display_name": "risk name", "confidence": 85, "reasoning": "brief reason"}}]

Only include risks with genuine relevance. Confidence should be 0-100."""

        return await self._call_llm(prompt)

    # ========== RISK → CONTROL ==========

    def suggest_controls_for_risk_rules(
        self,
        risk_name: str,
        risk_description: Optional[str],
        risk_impact: Optional[str],
        risk_control: Optional[str],
        available_controls: List[dict],
    ) -> List[dict]:
        """Rule-based: match risk keywords to control prefixes and descriptions."""
        search_text = f"{risk_name} {risk_description or ''} {risk_impact or ''} {risk_control or ''}"
        search_lower = search_text.lower()

        # Collect matching control prefixes
        matching_prefixes: List[str] = []
        for keyword, prefixes in RISK_CATEGORY_TO_CONTROL_PREFIX.items():
            if keyword in search_lower:
                matching_prefixes.extend(prefixes)

        # Also collect description keywords from policy mapping
        desc_keywords: List[str] = []
        for keyword, policy_kws in RISK_CATEGORY_TO_CONTROL_PREFIX.items():
            if keyword in search_lower:
                desc_keywords.append(keyword)

        scored = []
        for control in available_controls:
            code = (control.get("code") or "").upper()
            name = control.get("name", "")
            desc = control.get("description", "")
            control_text = f"{code} {name} {desc}"

            score = 0
            # Score from prefix match
            prefix_match = any(code.startswith(p) for p in matching_prefixes)
            if prefix_match:
                score += 60

            # Score from keyword match in name/description
            kw_score = _keyword_score(control_text, desc_keywords)
            score = min(score + kw_score // 2, 100)

            if score > 0:
                display = f"{code}: {name}" if code else name
                scored.append({
                    "item_id": control["id"],
                    "display_name": display,
                    "confidence": score,
                    "reasoning": f"Control {'prefix' if prefix_match else 'keywords'} match risk category",
                })

        scored.sort(key=lambda x: x["confidence"], reverse=True)
        return scored[:MAX_SUGGESTIONS]

    async def suggest_controls_for_risk_llm(
        self,
        risk_name: str,
        risk_description: Optional[str],
        risk_impact: Optional[str],
        risk_control: Optional[str],
        available_controls: List[dict],
    ) -> List[dict]:
        """LLM-based: send risk context + available controls."""
        truncated = [
            {"id": c["id"], "code": c.get("code", ""), "name": c.get("name", ""), "desc": _truncate(c.get("description"))}
            for c in available_controls[:MAX_LLM_ITEMS]
        ]

        prompt = f"""You are a cybersecurity controls advisor. Given the following risk, suggest which controls from the available list would best mitigate it.

RISK:
- Name: {risk_name}
- Description: {_truncate(risk_description, 200)}
- Potential Impact: {_truncate(risk_impact, 200)}
- Suggested Control: {_truncate(risk_control, 200)}

AVAILABLE CONTROLS:
{json.dumps(truncated, indent=1)}

Return a JSON array of the most relevant controls (max {MAX_SUGGESTIONS}). No markdown, no code fences, just raw JSON:
[{{"item_id": "uuid", "display_name": "control name", "confidence": 85, "reasoning": "brief reason"}}]

Only include controls with genuine relevance. Confidence should be 0-100."""

        return await self._call_llm(prompt)

    # ========== CONTROL → POLICY ==========

    def suggest_policies_for_control_rules(
        self,
        control_code: Optional[str],
        control_name: str,
        control_description: Optional[str],
        available_policies: List[dict],
    ) -> List[dict]:
        """Rule-based: extract control prefix, lookup policy keywords, score policies."""
        # Extract prefix from control code (e.g., "IAM-1" → "IAM")
        prefix = ""
        if control_code:
            match = re.match(r'^([A-Za-z]+)', control_code)
            if match:
                prefix = match.group(1).upper()

        # Collect policy keywords from prefix mapping
        policy_keywords: List[str] = []
        if prefix and prefix in CONTROL_PREFIX_TO_POLICY_KEYWORDS:
            policy_keywords.extend(CONTROL_PREFIX_TO_POLICY_KEYWORDS[prefix])

        # Also try matching control name/description to broader keywords
        control_text = f"{control_name} {control_description or ''}".lower()
        for kw_category, kw_list in CONTROL_PREFIX_TO_POLICY_KEYWORDS.items():
            for kw in kw_list:
                if kw.lower() in control_text:
                    policy_keywords.extend(kw_list)
                    break

        if not policy_keywords:
            # Fallback: use words from control name
            policy_keywords = [w for w in re.split(r'\W+', control_text) if len(w) > 3]

        scored = []
        for policy in available_policies:
            search_text = f"{policy.get('title', '')} {policy.get('body', '') or ''}"
            score = _keyword_score(search_text, policy_keywords)
            if score > 0:
                display = f"{policy.get('policy_code', '')}: {policy.get('title', '')}" if policy.get('policy_code') else policy.get('title', 'Unknown')
                scored.append({
                    "item_id": policy["id"],
                    "display_name": display,
                    "confidence": score,
                    "reasoning": f"Policy keywords match control {'prefix ' + prefix if prefix else 'description'}",
                })

        scored.sort(key=lambda x: x["confidence"], reverse=True)
        return scored[:MAX_SUGGESTIONS]

    async def suggest_policies_for_control_llm(
        self,
        control_code: Optional[str],
        control_name: str,
        control_description: Optional[str],
        available_policies: List[dict],
    ) -> List[dict]:
        """LLM-based: send control context + available policies."""
        truncated = [
            {"id": p["id"], "code": p.get("policy_code", ""), "title": p.get("title", ""), "desc": _truncate(p.get("body"))}
            for p in available_policies[:MAX_LLM_ITEMS]
        ]

        prompt = f"""You are a GRC policy advisor. Given the following security control, suggest which policies from the available list should govern this control.

CONTROL:
- Code: {control_code or 'N/A'}
- Name: {control_name}
- Description: {_truncate(control_description, 200)}

AVAILABLE POLICIES:
{json.dumps(truncated, indent=1)}

Return a JSON array of the most relevant policies (max {MAX_SUGGESTIONS}). No markdown, no code fences, just raw JSON:
[{{"item_id": "uuid", "display_name": "policy name", "confidence": 85, "reasoning": "brief reason"}}]

Only include policies with genuine relevance. Confidence should be 0-100."""

        return await self._call_llm(prompt)

    # ========== POLICY → OBJECTIVE ==========

    def suggest_objectives_for_policy_rules(
        self,
        policy_title: str,
        policy_body: Optional[str],
        available_objectives: List[dict],
    ) -> List[dict]:
        """Rule-based: keyword match policy title/body to objective title/description."""
        policy_text = f"{policy_title} {policy_body or ''}".lower()

        # Collect objective keywords from policy keyword clusters
        obj_keywords: List[str] = []
        for cluster_key, obj_kws in POLICY_TO_OBJECTIVE_KEYWORDS.items():
            if cluster_key in policy_text:
                obj_keywords.extend(obj_kws)

        if not obj_keywords:
            # Fallback: use significant words from policy title
            obj_keywords = [w for w in re.split(r'\W+', policy_text) if len(w) > 3]

        scored = []
        for obj in available_objectives:
            search_text = f"{obj.get('title', '')} {obj.get('requirement_description', '') or ''}"
            score = _keyword_score(search_text, obj_keywords)
            if score > 0:
                scored.append({
                    "item_id": obj["id"],
                    "display_name": obj.get("title", "Unknown"),
                    "confidence": score,
                    "reasoning": f"Objective keywords match policy theme",
                })

        scored.sort(key=lambda x: x["confidence"], reverse=True)
        return scored[:MAX_SUGGESTIONS]

    async def suggest_objectives_for_policy_llm(
        self,
        policy_title: str,
        policy_body: Optional[str],
        available_objectives: List[dict],
    ) -> List[dict]:
        """LLM-based: send policy context + available objectives."""
        truncated = [
            {"id": o["id"], "title": o.get("title", ""), "desc": _truncate(o.get("requirement_description"))}
            for o in available_objectives[:MAX_LLM_ITEMS]
        ]

        prompt = f"""You are a compliance advisor. Given the following policy, suggest which compliance objectives from the available list this policy should address.

POLICY:
- Title: {policy_title}
- Body: {_truncate(policy_body, 300)}

AVAILABLE OBJECTIVES:
{json.dumps(truncated, indent=1)}

Return a JSON array of the most relevant objectives (max {MAX_SUGGESTIONS}). No markdown, no code fences, just raw JSON:
[{{"item_id": "uuid", "display_name": "objective title", "confidence": 85, "reasoning": "brief reason"}}]

Only include objectives with genuine relevance. Confidence should be 0-100."""

        return await self._call_llm(prompt)

    # ========== ASSESSMENT ANSWERS FROM SCANS ==========

    def suggest_answers_from_scans_rules(
        self,
        unanswered_questions: List[dict],
        findings_summary: dict,
        all_findings: List[dict],
    ) -> List[dict]:
        """Rule-based: match question keywords to scanner findings and suggest answers."""
        if not all_findings:
            return []

        # Build per-scanner finding lists
        findings_by_scanner: Dict[str, List[dict]] = {}
        for f in all_findings:
            st = f.get("scanner_type", "")
            findings_by_scanner.setdefault(st, []).append(f)

        by_scanner = findings_summary.get("by_scanner", {})
        by_severity = findings_summary.get("by_severity", {})

        suggestions = []
        for q in unanswered_questions:
            q_id = str(q.get("question_id", ""))
            q_text = (q.get("question_text", "") or "").lower()
            if not q_text:
                continue

            # Find relevant scanners for this question
            relevant_scanners = set()
            for keyword, scanners in QUESTION_KEYWORD_TO_SCANNERS.items():
                if keyword in q_text:
                    relevant_scanners.update(scanners)

            if not relevant_scanners:
                continue

            # Gather findings from relevant scanners
            relevant_findings = []
            for scanner in relevant_scanners:
                relevant_findings.extend(findings_by_scanner.get(scanner, []))

            if not relevant_findings:
                continue

            # Count severities in relevant findings
            unremediated = [f for f in relevant_findings if not f.get("is_remediated")]
            sev_counts: Dict[str, int] = {}
            for f in unremediated:
                sev = (f.get("normalized_severity") or "unknown").lower()
                sev_counts[sev] = sev_counts.get(sev, 0) + 1

            critical_high = sev_counts.get("critical", 0) + sev_counts.get("high", 0)
            total_unremediated = len(unremediated)
            scanner_names = ", ".join(sorted(relevant_scanners & set(findings_by_scanner.keys())))

            # Determine answer based on question framing
            is_absence_question = any(kw in q_text for kw in ["without", "free from", "no known", "absence"])
            is_capability_question = any(kw in q_text for kw in ["do you", "is there", "have you", "are there", "implemented", "in place"])

            if is_absence_question:
                # Question asks about absence of vulns
                if critical_high > 0:
                    answer = "no"
                    confidence = min(90, 60 + critical_high * 5)
                    reasoning = f"{critical_high} critical/high severity unremediated findings detected"
                elif total_unremediated > 0:
                    answer = "partially"
                    confidence = 65
                    reasoning = f"{total_unremediated} unremediated findings (no critical/high) detected"
                else:
                    answer = "yes"
                    confidence = 70
                    reasoning = f"All {len(relevant_findings)} findings from {scanner_names} are remediated"
            elif is_capability_question:
                # Question asks about having a capability - scans existing = capability exists
                answer = "yes"
                confidence = 75
                reasoning = f"Scan activity detected from {scanner_names} ({len(relevant_findings)} findings)"
            else:
                # Neutral question - base on finding health
                if critical_high > 0:
                    answer = "partially"
                    confidence = 60
                    reasoning = f"{critical_high} critical/high findings still unremediated"
                else:
                    answer = "yes"
                    confidence = 65
                    reasoning = f"Scans from {scanner_names} show manageable findings"

            # Build evidence description
            evidence_parts = [f"Based on {len(relevant_findings)} findings from {scanner_names} scans."]
            if sev_counts:
                sev_str = ", ".join(f"{count} {sev}" for sev, count in sorted(sev_counts.items(), key=lambda x: SEVERITY_ORDER.get(x[0], 5)))
                evidence_parts.append(f"Unremediated: {sev_str}.")
            if len(relevant_findings) > total_unremediated:
                evidence_parts.append(f"{len(relevant_findings) - total_unremediated} findings already remediated.")

            suggestions.append({
                "question_id": q_id,
                "question_text": q.get("question_text", ""),
                "question_number": q.get("min_order", 0),
                "suggested_answer": answer,
                "evidence_description": " ".join(evidence_parts),
                "confidence": confidence,
                "reasoning": reasoning,
            })

        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions[:MAX_SUGGESTIONS]

    async def suggest_answers_from_scans_llm(
        self,
        unanswered_questions: List[dict],
        findings_summary: dict,
        all_findings: List[dict],
    ) -> List[dict]:
        """LLM-based: use scan findings to suggest assessment answers."""
        if not all_findings:
            return []

        # Build summary text
        by_scanner = findings_summary.get("by_scanner", {})
        by_severity = findings_summary.get("by_severity", {})
        total = findings_summary.get("total", 0)
        remediated = findings_summary.get("remediated", 0)

        summary_text = f"Total findings: {total}, Remediated: {remediated}\n"
        summary_text += f"By scanner: {json.dumps(by_scanner)}\n"
        summary_text += f"By severity: {json.dumps(by_severity)}\n"

        # Sample top 50 findings for the prompt
        sample_findings = []
        for f in all_findings[:50]:
            sample_findings.append({
                "scanner": f.get("scanner_type", ""),
                "title": _truncate(f.get("title", ""), 80),
                "severity": f.get("normalized_severity", ""),
                "remediated": f.get("is_remediated", False),
                "id_or_cve": _truncate(f.get("identifier", ""), 30),
            })

        # Build questions list
        questions_for_prompt = []
        for q in unanswered_questions[:30]:  # Cap at 30 questions for prompt size
            questions_for_prompt.append({
                "id": str(q.get("question_id", "")),
                "text": _truncate(q.get("question_text", ""), 200),
            })

        prompt = f"""You are a cybersecurity compliance assessor. Given scan findings from security tools, suggest answers to unanswered assessment questions.

SCAN FINDINGS SUMMARY:
{summary_text}

SAMPLE FINDINGS (top {len(sample_findings)}):
{json.dumps(sample_findings, indent=1)}

UNANSWERED QUESTIONS:
{json.dumps(questions_for_prompt, indent=1)}

For each question that scan data can meaningfully answer, return a JSON array:
[{{"question_id": "uuid", "question_text": "the question", "suggested_answer": "yes|no|partially|n/a", "evidence_description": "specific evidence from scan data", "confidence": 0-100, "reasoning": "brief explanation"}}]

IMPORTANT RULES:
- Only suggest answers where scan findings provide real evidence
- Skip governance, training, organizational, or policy questions that scans cannot answer
- "yes" = scans confirm the capability/practice exists
- "no" = scans show clear deficiency or vulnerability
- "partially" = mixed evidence (some good, some concerning)
- "n/a" = question is not applicable based on scan scope
- evidence_description should cite specific scan counts, severities, or finding types
- Confidence should reflect how directly scans can answer the question (technical questions = higher, process questions = lower)

Return ONLY the JSON array, no markdown, no code fences."""

        # Build question_id -> min_order lookup for enrichment
        order_lookup = {str(q.get("question_id", "")): q.get("min_order", 0) for q in unanswered_questions}
        return await self._call_llm_for_answers(prompt, order_lookup)

    # ========== ASSESSMENT ANSWERS FROM ALL SOURCES ==========

    def _gather_all_platform_data(self, framework_id, org_id, user_id) -> dict:
        """Collect all platform data for comprehensive AI answer suggestion."""
        from app.repositories import scan_finding_repository

        platform_data: Dict[str, any] = {}

        # 1. Scan findings — top 30
        try:
            findings, stats = scan_finding_repository.get_findings_for_suggestion(self.db, org_id)
            sample = []
            for f in findings[:30]:
                sample.append({
                    "scanner": f.get("scanner_type", ""),
                    "title": _truncate(f.get("title", ""), 80),
                    "severity": f.get("normalized_severity", ""),
                    "remediated": f.get("is_remediated", False),
                })
            platform_data["scan_findings"] = sample
            platform_data["scan_stats"] = stats
        except Exception as e:
            logger.warning(f"Could not gather scan findings: {e}")
            platform_data["scan_findings"] = []
            platform_data["scan_stats"] = {}

        # 2. Approved policies for framework — max 15
        try:
            approved_status = self.db.query(models.PolicyStatuses).filter(
                models.PolicyStatuses.status == "Approved"
            ).first()
            if approved_status and framework_id:
                policies = (
                    self.db.query(models.Policies)
                    .join(models.PolicyFrameworks, models.PolicyFrameworks.policy_id == models.Policies.id)
                    .filter(
                        models.PolicyFrameworks.framework_id == framework_id,
                        models.Policies.status_id == approved_status.id,
                        models.Policies.organisation_id == org_id,
                    )
                    .limit(15)
                    .all()
                )
                platform_data["policies"] = [
                    {"code": p.policy_code, "title": p.title, "body": _truncate(p.body, 300)}
                    for p in policies
                ]
            else:
                platform_data["policies"] = []
        except Exception as e:
            logger.warning(f"Could not gather policies: {e}")
            platform_data["policies"] = []

        # 3. Objectives for framework — max 20
        try:
            if framework_id:
                chapters = self.db.query(models.Chapters).filter(
                    models.Chapters.framework_id == framework_id
                ).all()
                chapter_ids = [c.id for c in chapters]
                chapter_map = {c.id: c.title for c in chapters}
                if chapter_ids:
                    objectives = (
                        self.db.query(models.Objectives, models.ComplianceStatuses.status_name)
                        .outerjoin(models.ComplianceStatuses, models.Objectives.compliance_status_id == models.ComplianceStatuses.id)
                        .filter(models.Objectives.chapter_id.in_(chapter_ids))
                        .limit(20)
                        .all()
                    )
                    platform_data["objectives"] = [
                        {
                            "chapter": chapter_map.get(obj.chapter_id, ""),
                            "title": _truncate(obj.title, 100),
                            "status": status_name or "not assessed",
                            "requirement": _truncate(obj.requirement_description, 200),
                        }
                        for obj, status_name in objectives
                    ]
                else:
                    platform_data["objectives"] = []
            else:
                platform_data["objectives"] = []
        except Exception as e:
            logger.warning(f"Could not gather objectives: {e}")
            platform_data["objectives"] = []

        # 4. Answered evidence from assessments — max 10
        try:
            evidence_rows = (
                self.db.query(
                    models.Question.text.label("question_text"),
                    models.Answer.value.label("answer_value"),
                    models.Answer.evidence_description,
                    func.string_agg(models.Evidence.filename, ', ').label("file_names"),
                )
                .join(models.Answer, models.Answer.question_id == models.Question.id)
                .outerjoin(models.Evidence, models.Evidence.answer_id == models.Answer.id)
                .join(models.Assessment, models.Assessment.id == models.Answer.assessment_id)
                .filter(
                    models.Assessment.framework_id == framework_id,
                    models.Answer.value.isnot(None),
                    models.Answer.value != "",
                )
                .group_by(models.Question.text, models.Answer.value, models.Answer.evidence_description)
                .limit(10)
                .all()
            )
            platform_data["answered_evidence"] = [
                {
                    "question": _truncate(row.question_text, 100),
                    "answer": row.answer_value,
                    "evidence_desc": _truncate(row.evidence_description, 200),
                    "files": _truncate(row.file_names, 100) if row.file_names else "",
                }
                for row in evidence_rows
            ]
        except Exception as e:
            logger.warning(f"Could not gather answered evidence: {e}")
            platform_data["answered_evidence"] = []

        # 5. Evidence library — max 10 approved
        try:
            lib_items = (
                self.db.query(models.EvidenceLibraryItem)
                .filter(
                    models.EvidenceLibraryItem.organisation_id == org_id,
                    models.EvidenceLibraryItem.status == "Approved",
                )
                .limit(10)
                .all()
            )
            platform_data["evidence_library"] = [
                {"name": item.name, "description": _truncate(item.description, 100), "type": item.evidence_type}
                for item in lib_items
            ]
        except Exception as e:
            logger.warning(f"Could not gather evidence library: {e}")
            platform_data["evidence_library"] = []

        # 6. Organisation domain
        try:
            org = self.db.query(models.Organisations).filter(models.Organisations.id == org_id).first()
            platform_data["org_domain"] = org.domain if org and org.domain else ""
        except Exception as e:
            logger.warning(f"Could not gather org domain: {e}")
            platform_data["org_domain"] = ""

        # 7. Latest Compliance Advisor analysis
        try:
            from app.repositories import scanner_history_repository
            latest_rows = scanner_history_repository.get_scanner_history_by_scanner_type(
                self.db, "compliance_advisor", organisation_id=org_id, limit=1
            )
            if latest_rows:
                row = latest_rows[0]
                try:
                    parsed = json.loads(row.results) if isinstance(row.results, str) else row.results
                except (json.JSONDecodeError, TypeError):
                    parsed = {}
                recs = parsed.get("recommendations", [])
                platform_data["compliance_advisor"] = {
                    "company_summary": parsed.get("company_summary", ""),
                    "recommendations": [
                        {"framework": r.get("framework_name", ""), "relevance": r.get("relevance", ""), "reasoning": r.get("reasoning", "")}
                        for r in recs[:5]
                    ],
                    "analyzed_url": row.scan_target or "",
                }
            else:
                platform_data["compliance_advisor"] = None
        except Exception as e:
            logger.warning(f"Could not gather compliance advisor data: {e}")
            platform_data["compliance_advisor"] = None

        return platform_data

    def _build_compact_platform_context(self, platform_data: dict) -> str:
        """Build a compact platform context string for LLM prompts, minimizing token count."""
        sections = []

        scan_findings = platform_data.get("scan_findings", [])
        scan_stats = platform_data.get("scan_stats", {})
        if scan_stats.get("total"):
            sections.append(
                f"SCANS: {scan_stats.get('total',0)} findings, {scan_stats.get('remediated',0)} fixed. "
                f"Severity: {json.dumps(scan_stats.get('by_severity',{}),separators=(',',':'))}. "
                f"Top: {json.dumps([{'t':f['title'],'s':f['severity'],'r':f['remediated']} for f in scan_findings[:8]],separators=(',',':'))}"
            )

        policies = platform_data.get("policies", [])
        if policies:
            compact = [{"c": p.get("code",""), "t": p["title"]} for p in policies[:10]]
            sections.append(f"POLICIES({len(policies)}): {json.dumps(compact,separators=(',',':'))}")

        objectives = platform_data.get("objectives", [])
        if objectives:
            compact = [{"t": o["title"], "s": o.get("status","")} for o in objectives[:10]]
            sections.append(f"OBJECTIVES({len(objectives)}): {json.dumps(compact,separators=(',',':'))}")

        answered_evidence = platform_data.get("answered_evidence", [])
        if answered_evidence:
            compact = [{"q": _truncate(e["question"],60), "a": e["answer"]} for e in answered_evidence[:8]]
            sections.append(f"EVIDENCE({len(answered_evidence)}): {json.dumps(compact,separators=(',',':'))}")

        evidence_library = platform_data.get("evidence_library", [])
        if evidence_library:
            compact = [{"n": e["name"], "t": e["type"]} for e in evidence_library[:8]]
            sections.append(f"LIBRARY({len(evidence_library)}): {json.dumps(compact,separators=(',',':'))}")

        compliance_advisor = platform_data.get("compliance_advisor")
        if compliance_advisor and compliance_advisor.get("company_summary"):
            sections.append(f"ADVISOR: {_truncate(compliance_advisor['company_summary'], 200)}")

        org_domain = platform_data.get("org_domain", "")
        if org_domain:
            sections.append(f"DOMAIN: {org_domain}")

        return "\n".join(sections)

    async def suggest_answers_from_all_sources_llm(
        self,
        unanswered_questions: List[dict],
        platform_data: dict,
    ) -> List[dict]:
        """LLM-based: use all platform data to suggest assessment answers."""
        if not unanswered_questions:
            return []

        platform_context = self._build_compact_platform_context(platform_data)

        # Build question_id -> min_order lookup
        order_lookup = {str(q.get("question_id", "")): q.get("min_order", 0) for q in unanswered_questions}

        # Single-question fast path
        if len(unanswered_questions) == 1:
            q = unanswered_questions[0]
            qid = str(q.get("question_id", ""))
            qtext = _truncate(q.get("question_text", ""), 200)

            prompt = f"""Given the platform data, answer this compliance question.

{platform_context}

QUESTION: {qtext}

Return a single JSON object (no markdown):
{{"question_id":"{qid}","question_text":"{qtext}","suggested_answer":"yes|no|partially|n/a","evidence_description":"cite sources","confidence":0-100,"reasoning":"brief"}}

Rules: "yes"=confirmed, "no"=deficiency, "partially"=mixed, "n/a"=not applicable. Cite specific sources. Cap confidence at 65 if only one source. Return [] if no data is relevant."""

            try:
                return await self._call_llm_for_answers(prompt, order_lookup)
            except Exception as e:
                logger.warning(f"Single-question LLM call failed: {e}")
                return []

        # Multi-question: batch in groups of 10
        batch_size = 10
        all_suggestions = []
        total_batches = (len(unanswered_questions) + batch_size - 1) // batch_size

        for batch_idx in range(total_batches):
            start = batch_idx * batch_size
            end = start + batch_size
            batch = unanswered_questions[start:end]

            questions_for_prompt = [
                {"id": str(q.get("question_id", "")), "text": _truncate(q.get("question_text", ""), 200)}
                for q in batch
            ]

            prompt = f"""You are a cybersecurity compliance assessor. Analyze the platform data to suggest answers.

{platform_context}

QUESTIONS (batch {batch_idx + 1}/{total_batches}):
{json.dumps(questions_for_prompt,separators=(',',':'))}

Return a JSON array:
[{{"question_id":"uuid","question_text":"text","suggested_answer":"yes|no|partially|n/a","evidence_description":"cite sources","confidence":0-100,"reasoning":"brief"}}]

Rules: Cross-reference sources. Cap confidence at 65 if only one source. Skip irrelevant questions. Cite specific data (e.g. "policy POL-001", "3 scan findings").
Return ONLY JSON, no markdown."""

            try:
                batch_results = await self._call_llm_for_answers(prompt, order_lookup)
                all_suggestions.extend(batch_results)
            except Exception as e:
                logger.warning(f"Batch {batch_idx + 1}/{total_batches} failed: {e}")
                continue

        all_suggestions.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return all_suggestions

    async def _call_llm_for_answers(self, prompt: str, order_lookup: Dict[str, int] = None) -> List[dict]:
        """Call LLM and parse response into answer suggestion list."""
        try:
            effective_settings = self._get_effective_llm_settings()
            if not effective_settings.get("ai_enabled", True):
                raise Exception("AI is disabled")

            llm_service = LLMService(self.db)
            effective_provider = effective_settings.get("llm_provider", "llamacpp")

            if effective_provider == "qlon" and effective_settings.get("qlon_url") and effective_settings.get("qlon_api_key"):
                response_text = await llm_service.generate_text_with_qlon(
                    prompt,
                    qlon_url=effective_settings["qlon_url"],
                    qlon_api_key=effective_settings["qlon_api_key"],
                    use_tools=effective_settings.get("qlon_use_tools", True),
                    timeout=LLM_TIMEOUT,
                )
            else:
                if effective_provider == "llamacpp":
                    llm_service.llm_backend = "llamacpp"
                response_text = await llm_service.generate_text(prompt, timeout=LLM_TIMEOUT)

            result = _parse_llm_json(response_text)

            if isinstance(result, list):
                suggestions = result
            elif isinstance(result, dict) and "suggestions" in result:
                suggestions = result["suggestions"]
            else:
                logger.warning("LLM returned unexpected format for answer suggestions")
                return []

            # Validate and normalize
            valid_answers = {"yes", "no", "partially", "n/a"}
            valid = []
            for item in suggestions[:MAX_SUGGESTIONS]:
                if not isinstance(item, dict) or "question_id" not in item:
                    continue
                answer = str(item.get("suggested_answer", "")).lower().strip()
                if answer not in valid_answers:
                    answer = "partially"  # safe fallback
                qid = str(item["question_id"])
                valid.append({
                    "question_id": qid,
                    "question_text": str(item.get("question_text", "")),
                    "question_number": (order_lookup or {}).get(qid, 0),
                    "suggested_answer": answer,
                    "evidence_description": str(item.get("evidence_description", "AI-suggested based on scan data")),
                    "confidence": max(0, min(int(item.get("confidence", 50)), 100)),
                    "reasoning": str(item.get("reasoning", "AI suggested")),
                })
            return valid

        except Exception as e:
            logger.error(f"LLM answer suggestion failed: {str(e)}")
            raise

    # ========== Shared LLM helper ==========

    def _get_effective_llm_settings(self) -> dict:
        """Get effective LLM settings for the current user's organization."""
        global_settings = self.db.query(models.LLMSettings).first()
        if global_settings and global_settings.ai_enabled == False:
            return {"ai_enabled": False, "llm_provider": "llamacpp"}

        user_org_id = getattr(self.current_user, 'organisation_id', None) if self.current_user else None
        if user_org_id:
            org_settings = self.db.query(models.OrganizationLLMSettings).filter(
                models.OrganizationLLMSettings.organisation_id == user_org_id
            ).first()
            if org_settings and org_settings.is_enabled:
                return {
                    "ai_enabled": True,
                    "llm_provider": org_settings.llm_provider,
                    "qlon_url": org_settings.qlon_url,
                    "qlon_api_key": org_settings.qlon_api_key,
                    "qlon_use_tools": org_settings.qlon_use_tools if org_settings.qlon_use_tools is not None else True,
                }

        return {
            "ai_enabled": True,
            "llm_provider": getattr(global_settings, 'default_provider', 'llamacpp') or 'llamacpp' if global_settings else 'llamacpp',
        }

    async def _call_llm(self, prompt: str) -> List[dict]:
        """Call LLM and parse response into suggestion list."""
        try:
            effective_settings = self._get_effective_llm_settings()
            if not effective_settings.get("ai_enabled", True):
                raise Exception("AI is disabled")

            llm_service = LLMService(self.db)
            effective_provider = effective_settings.get("llm_provider", "llamacpp")

            if effective_provider == "qlon" and effective_settings.get("qlon_url") and effective_settings.get("qlon_api_key"):
                response_text = await llm_service.generate_text_with_qlon(
                    prompt,
                    qlon_url=effective_settings["qlon_url"],
                    qlon_api_key=effective_settings["qlon_api_key"],
                    use_tools=effective_settings.get("qlon_use_tools", True),
                    timeout=LLM_TIMEOUT,
                )
            else:
                if effective_provider == "llamacpp":
                    llm_service.llm_backend = "llamacpp"
                response_text = await llm_service.generate_text(prompt, timeout=LLM_TIMEOUT)
            result = _parse_llm_json(response_text)

            if isinstance(result, list):
                suggestions = result
            elif isinstance(result, dict) and "suggestions" in result:
                suggestions = result["suggestions"]
            else:
                logger.warning("LLM returned unexpected format")
                return []

            # Validate and normalize
            valid = []
            for item in suggestions[:MAX_SUGGESTIONS]:
                if isinstance(item, dict) and "item_id" in item:
                    valid.append({
                        "item_id": str(item["item_id"]),
                        "display_name": str(item.get("display_name", "Unknown")),
                        "confidence": max(0, min(int(item.get("confidence", 50)), 100)),
                        "reasoning": str(item.get("reasoning", "AI suggested")),
                    })
            return valid

        except Exception as e:
            logger.error(f"LLM suggestion failed: {str(e)}")
            raise
