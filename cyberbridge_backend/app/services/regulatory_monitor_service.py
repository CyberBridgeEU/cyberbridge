import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from ..database.database import get_db
from ..repositories import regulatory_monitor_repository as repo
from .regulatory_web_search_service import RegulatoryWebSearchService
from .framework_snapshot_service import FrameworkSnapshotService
from ..models.models import (
    Framework, Chapters, Objectives, Question, FrameworkQuestion,
    FrameworkUpdates, RegulatoryChange
)
from sqlalchemy import and_

logger = logging.getLogger(__name__)

# Framework type detection mapping (same logic as FrameworkUpdateService)
FRAMEWORK_TYPE_KEYWORDS = {
    "cra": ["cra", "cyber resilience act"],
    "nis2_directive": ["nis", "nis2"],
    "iso_27001_2022": ["iso", "27001"],
    "gdpr": ["gdpr", "general data protection"],
    "dora_2022": ["dora", "digital operational resilience"],
    "nist_csf_2_0": ["nist", "cybersecurity framework"],
    "cmmc_2_0": ["cmmc"],
    "pci_dss_v4_0": ["pci", "payment card"],
    "soc_2": ["soc 2", "soc2"],
    "hipaa_privacy_rule": ["hipaa"],
    "cobit_2019": ["cobit"],
    "ccpa_california_consumer_privacy_act": ["ccpa", "california consumer privacy"],
    "ftc_safeguards": ["ftc", "safeguards"],
    "australia_energy_aescsf": ["aescsf", "australian energy"],
}


def detect_framework_type(framework_name: str) -> Optional[str]:
    """Detect framework type from framework name."""
    name_lower = framework_name.lower()
    for fw_type, keywords in FRAMEWORK_TYPE_KEYWORDS.items():
        if any(kw in name_lower for kw in keywords):
            return fw_type
    return None


class RegulatoryMonitorService:
    """
    Core orchestrator for the Regulatory Change Monitor.
    - run_web_scan(): background job that searches the web (no LLM)
    - run_llm_analysis(): on-demand LLM analysis triggered by admin
    """

    @staticmethod
    async def run_web_scan():
        """
        Background job: search the web for regulatory changes across all frameworks.
        Stores raw findings in regulatory_scan_results. No LLM involved.
        """
        db = next(get_db())
        try:
            settings = repo.get_settings(db)
            if not settings or not settings.enabled:
                logger.info("Regulatory monitor is disabled, skipping scan")
                return

            # Create scan run
            scan_run = repo.create_scan_run(db)
            db.commit()

            searxng_url = settings.searxng_url or "http://searxng:8080"
            search_service = RegulatoryWebSearchService(searxng_url=searxng_url)

            # Get all enabled sources grouped by framework
            sources = repo.get_sources(db, enabled_only=True)
            if not sources:
                logger.info("No regulatory sources configured, skipping scan")
                repo.update_scan_run(db, scan_run.id, status="completed", completed_at=datetime.utcnow())
                db.commit()
                return

            frameworks_scanned = set()
            total_new_findings = 0
            log_entries = []

            for source in sources:
                try:
                    log_entries.append(f"Fetching {source.source_name} ({source.source_type}) for {source.framework_type}")
                    results = await search_service.fetch_for_source(source)

                    for result in results:
                        content = result.get("content", "")
                        if not content:
                            continue

                        # Sanitize content to remove NUL bytes that PostgreSQL rejects
                        content = RegulatoryWebSearchService.sanitize_content(content)

                        content_hash = RegulatoryWebSearchService.compute_content_hash(content)

                        # Check if we've seen this exact content before
                        prev_hash = repo.get_previous_content_hash(
                            db, source.framework_type, source.source_name
                        )

                        if content_hash == prev_hash:
                            log_entries.append(f"  No changes detected for {source.source_name}")
                            continue

                        # Store new/changed finding
                        try:
                            repo.create_scan_result(db, {
                                "scan_run_id": scan_run.id,
                                "framework_type": source.framework_type,
                                "source_name": source.source_name,
                                "source_url": result.get("url", ""),
                                "raw_content": content,
                                "content_hash": content_hash,
                                "fetched_at": datetime.utcnow()
                            })
                            db.commit()

                            total_new_findings += 1
                            frameworks_scanned.add(source.framework_type)
                            log_entries.append(f"  New content found from {source.source_name}")
                        except Exception as store_err:
                            db.rollback()
                            log_entries.append(f"  Error storing result from {source.source_name}: {str(store_err)}")
                            logger.error(f"Error storing result from {source.source_name}: {store_err}")

                except Exception as e:
                    log_entries.append(f"  Error fetching {source.source_name}: {str(e)}")
                    logger.error(f"Error fetching source {source.source_name}: {e}")

            # Update scan run status
            repo.update_scan_run(
                db, scan_run.id,
                status="completed",
                completed_at=datetime.utcnow(),
                frameworks_scanned=len(frameworks_scanned),
                changes_found=total_new_findings,
                raw_log=json.dumps(log_entries)
            )

            # Update last_scan_at
            repo.update_settings(db, {"last_scan_at": datetime.utcnow()})
            db.commit()

            logger.info(
                f"Regulatory scan completed: {len(frameworks_scanned)} frameworks, "
                f"{total_new_findings} new findings"
            )

        except Exception as e:
            logger.error(f"Regulatory web scan failed: {e}")
            try:
                if scan_run:
                    repo.update_scan_run(
                        db, scan_run.id,
                        status="failed",
                        completed_at=datetime.utcnow(),
                        error_message=str(e)
                    )
                db.commit()
            except Exception:
                db.rollback()
        finally:
            db.close()

    @staticmethod
    def run_llm_analysis(
        db: Session,
        scan_run_id: uuid.UUID,
        framework_type: str,
        llm_service_func=None
    ) -> List[Dict]:
        """
        On-demand LLM analysis: compare current seed content vs raw web findings.
        Returns structured changes with confidence scores.

        llm_service_func: async callable(prompt: str) -> str
            If not provided, uses the default LLM integration.
        """
        # Load raw web findings for this run and framework
        raw_results = repo.get_scan_results(db, scan_run_id, framework_type)
        if not raw_results:
            return []

        # Get current framework content for comparison
        current_content = RegulatoryMonitorService._extract_framework_content(db, framework_type)
        if not current_content:
            logger.warning(f"No framework content found for type {framework_type}")
            return []

        # Build the LLM prompt — keep total prompt under ~3000 chars to fit local LLM context
        # Truncate current content
        current_content_trimmed = current_content[:1500] if len(current_content) > 1500 else current_content

        # Truncate raw findings — pick the most relevant sources, limit each
        max_findings_chars = 1500
        findings_parts = []
        chars_used = 0
        for r in raw_results:
            snippet = r.raw_content[:500] if r.raw_content else ""
            entry = f"Source: {r.source_name}\nURL: {r.source_url}\n{snippet}"
            if chars_used + len(entry) > max_findings_chars:
                break
            findings_parts.append(entry)
            chars_used += len(entry)
        raw_findings_text = "\n\n---\n\n".join(findings_parts) if findings_parts else "No findings available."

        prompt = f"""You are a regulatory compliance analyst. Compare the CURRENT framework content against the LATEST regulatory text. Identify discrepancies: additions, modifications, removals.

## SECTION A: Current Framework Content

{current_content_trimmed}

## SECTION B: Latest Regulatory Findings

{raw_findings_text}

## Instructions

Return a JSON array of change objects. Each object must have:
- change_type: "new_chapter", "new_objective", "update_objective", "new_question", "update_question", or "remove_objective"
- entity_identifier: subchapter number or chapter name
- proposed_value: object with the proposed state
- source_excerpt: short excerpt from regulatory text
- confidence: float 0.0-1.0
- reasoning: brief explanation

Return ONLY valid JSON. If no changes found, return [].
Be conservative — only flag genuine regulatory changes, not formatting differences."""

        # If no LLM function provided, try to use the system's AI integration
        if llm_service_func is None:
            # Store the prompt for manual processing and return empty
            # The actual LLM call will be made via the controller using the existing AI tools
            return [{
                "status": "prompt_ready",
                "prompt": prompt,
                "framework_type": framework_type,
                "scan_run_id": str(scan_run_id),
                "raw_results_count": len(raw_results)
            }]

        # Parse LLM response and store changes
        try:
            import asyncio
            llm_response = asyncio.get_event_loop().run_until_complete(llm_service_func(prompt))
            changes = RegulatoryMonitorService._parse_llm_changes(llm_response)
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return []

        # Store changes in database
        stored_changes = []
        for change in changes:
            stored = repo.create_change(db, {
                "scan_run_id": scan_run_id,
                "framework_type": framework_type,
                "change_type": change.get("change_type", "unknown"),
                "entity_identifier": change.get("entity_identifier"),
                "current_value": json.dumps(change.get("current_value")) if change.get("current_value") else None,
                "proposed_value": json.dumps(change.get("proposed_value")) if change.get("proposed_value") else None,
                "source_url": change.get("source_url"),
                "source_excerpt": change.get("source_excerpt"),
                "confidence": change.get("confidence", 0.5),
                "llm_reasoning": change.get("reasoning"),
                "status": "pending"
            })
            stored_changes.append({
                "id": str(stored.id),
                "change_type": stored.change_type,
                "entity_identifier": stored.entity_identifier,
                "confidence": stored.confidence,
                "status": stored.status
            })

        db.commit()
        return stored_changes

    @staticmethod
    def store_llm_changes(
        db: Session,
        scan_run_id: uuid.UUID,
        framework_type: str,
        llm_response: str
    ) -> List[Dict]:
        """Parse LLM response and store changes. Called by the controller after LLM completes."""
        changes = RegulatoryMonitorService._parse_llm_changes(llm_response)

        stored_changes = []
        for change in changes:
            stored = repo.create_change(db, {
                "scan_run_id": scan_run_id,
                "framework_type": framework_type,
                "change_type": change.get("change_type", "unknown"),
                "entity_identifier": change.get("entity_identifier"),
                "current_value": json.dumps(change.get("current_value")) if change.get("current_value") else None,
                "proposed_value": json.dumps(change.get("proposed_value")) if change.get("proposed_value") else None,
                "source_url": change.get("source_url"),
                "source_excerpt": change.get("source_excerpt"),
                "confidence": change.get("confidence", 0.5),
                "llm_reasoning": change.get("reasoning"),
                "status": "pending"
            })
            stored_changes.append({
                "id": str(stored.id),
                "change_type": stored.change_type,
                "entity_identifier": stored.entity_identifier,
                "confidence": stored.confidence,
                "status": stored.status
            })

        db.flush()
        return stored_changes

    @staticmethod
    def apply_approved_changes(
        db: Session,
        change_ids: List[uuid.UUID],
        framework_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Dict:
        """Apply approved regulatory changes to an org's framework DB."""
        framework = db.query(Framework).filter(Framework.id == framework_id).first()
        if not framework:
            raise ValueError(f"Framework with ID {framework_id} not found")

        # Get approved changes
        changes = []
        for cid in change_ids:
            change = repo.get_change(db, cid)
            if change and change.status == "approved":
                changes.append(change)

        if not changes:
            raise ValueError("No approved changes found to apply")

        # Create pre-update snapshot
        # Use version 10000+ for regulatory monitor updates to avoid collisions with seed update versions (1, 2, 3...)
        from sqlalchemy import func as sa_func
        max_reg_version = db.query(sa_func.max(FrameworkUpdates.version)).filter(
            FrameworkUpdates.framework_id == framework_id,
            FrameworkUpdates.source == "regulatory_monitor"
        ).scalar() or 9999
        max_version = max_reg_version + 1

        snapshot = FrameworkSnapshotService.create_snapshot(
            db, framework_id, max_version, "pre_update", user_id
        )

        counts = {
            "new_chapters": 0,
            "new_objectives": 0,
            "updated_objectives": 0,
            "new_questions": 0,
            "updated_questions": 0
        }

        for change in changes:
            proposed = json.loads(change.proposed_value) if change.proposed_value else {}

            if change.change_type == "new_chapter":
                new_chapter = Chapters(
                    id=uuid.uuid4(),
                    title=proposed.get("title", proposed.get("name", "")),
                    framework_id=framework_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_chapter)
                counts["new_chapters"] += 1

            elif change.change_type == "new_objective":
                chapter_id = proposed.get("chapter_id")
                if not chapter_id:
                    # Try to find chapter by name
                    chapter_name = proposed.get("chapter_name")
                    if chapter_name:
                        chapter = db.query(Chapters).filter(
                            and_(Chapters.framework_id == framework_id, Chapters.title.ilike(f"%{chapter_name}%"))
                        ).first()
                        chapter_id = str(chapter.id) if chapter else None

                if chapter_id:
                    new_obj = Objectives(
                        id=uuid.uuid4(),
                        title=proposed.get("title", ""),
                        subchapter=proposed.get("subchapter"),
                        chapter_id=uuid.UUID(chapter_id),
                        requirement_description=proposed.get("requirement_description"),
                        objective_utilities=proposed.get("objective_utilities"),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(new_obj)
                    counts["new_objectives"] += 1

            elif change.change_type == "update_objective":
                subchapter = change.entity_identifier
                existing = db.query(Objectives).join(Chapters).filter(
                    and_(
                        Objectives.subchapter == subchapter,
                        Chapters.framework_id == framework_id
                    )
                ).first()

                if existing:
                    if proposed.get("title"):
                        existing.title = proposed["title"]
                    if proposed.get("requirement_description"):
                        existing.requirement_description = proposed["requirement_description"]
                    if proposed.get("objective_utilities"):
                        existing.objective_utilities = proposed["objective_utilities"]
                    existing.updated_at = datetime.utcnow()
                    counts["updated_objectives"] += 1

            elif change.change_type == "new_question":
                new_q = Question(
                    id=uuid.uuid4(),
                    text=proposed.get("question_text", proposed.get("text", "")),
                    description=proposed.get("title", proposed.get("description", "")),
                    mandatory=proposed.get("mandatory", False),
                    assessment_type_id=uuid.UUID(proposed["assessment_type_id"]) if proposed.get("assessment_type_id") else None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_q)
                db.flush()

                fq = FrameworkQuestion(
                    framework_id=framework_id,
                    question_id=new_q.id,
                    order=proposed.get("order", 0)
                )
                db.add(fq)
                counts["new_questions"] += 1

            elif change.change_type == "update_question":
                q_id = proposed.get("question_id") or change.entity_identifier
                if q_id:
                    existing_q = db.query(Question).filter(Question.id == uuid.UUID(q_id)).first()
                    if existing_q:
                        if proposed.get("text"):
                            existing_q.text = proposed["text"]
                        if proposed.get("description"):
                            existing_q.description = proposed["description"]
                        existing_q.updated_at = datetime.utcnow()
                        counts["updated_questions"] += 1

            # Mark change as applied
            change.status = "applied"
            change.updated_at = datetime.utcnow()

        # Record in framework_updates
        update_record = FrameworkUpdates(
            id=uuid.uuid4(),
            framework_id=framework_id,
            version=max_version,
            framework_name=detect_framework_type(framework.name) or "unknown",
            description=f"Regulatory monitor: {sum(counts.values())} changes applied",
            status="applied",
            applied_by=user_id,
            applied_at=datetime.utcnow(),
            snapshot_id=snapshot.id,
            source="regulatory_monitor",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(update_record)
        db.commit()

        return {
            "success": True,
            "message": f"Applied {sum(counts.values())} regulatory changes",
            "changes": counts,
            "update_id": str(update_record.id),
            "snapshot_id": str(snapshot.id)
        }

    @staticmethod
    def _extract_framework_content(db: Session, framework_type: str) -> Optional[str]:
        """Extract current framework content as text for LLM comparison."""
        # Find frameworks of this type across all orgs
        frameworks = db.query(Framework).all()
        target_fw = None
        for fw in frameworks:
            detected = detect_framework_type(fw.name)
            if detected == framework_type:
                target_fw = fw
                break

        if not target_fw:
            return None

        chapters = db.query(Chapters).filter(
            Chapters.framework_id == target_fw.id
        ).order_by(Chapters.title).all()

        content_parts = [f"Framework: {target_fw.name}\n"]

        for chapter in chapters:
            content_parts.append(f"\n## Chapter: {chapter.title}")

            objectives = db.query(Objectives).filter(
                Objectives.chapter_id == chapter.id
            ).order_by(Objectives.subchapter).all()

            for obj in objectives:
                content_parts.append(
                    f"\n### {obj.subchapter or 'N/A'}: {obj.title}\n"
                    f"Requirement: {obj.requirement_description or 'N/A'}\n"
                    f"Utilities: {obj.objective_utilities or 'N/A'}"
                )

        return "\n".join(content_parts)

    @staticmethod
    def _parse_llm_changes(llm_response: str) -> List[Dict]:
        """Parse LLM JSON response into a list of change dicts."""
        try:
            # Try to extract JSON array from response
            text = llm_response.strip()

            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            # Find the JSON array
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])

            return []
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return []
